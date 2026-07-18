"""RAG Copilot with graph-augmented retrieval for AssetBrain."""

import time
import json
from typing import Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings

from .config import (
    CHROMA_PERSIST_DIR,
    GRAPH_PATH,
)
from .llm_client import GeminiClient
from .ingest import KnowledgeGraph


class RAGCopilot:
    """Graph-augmented RAG copilot for industrial knowledge queries."""

    def __init__(self):
        # Initialize LLM client
        self.llm = GeminiClient()

        # Initialize ChromaDB with helpful error
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        try:
            self.collection = self.chroma_client.get_collection("assetbrain_docs")
        except Exception as e:
            raise RuntimeError(
                f"ChromaDB collection 'assetbrain_docs' not found. "
                f"Run ingestion first: POST /api/ingest. Original error: {e}"
            )

        # Load knowledge graph with helpful error
        try:
            self.kg = KnowledgeGraph.load()
        except Exception as e:
            raise RuntimeError(
                f"Failed to load knowledge graph from {GRAPH_PATH}. "
                f"Run ingestion first: POST /api/ingest. Original error: {e}"
            )

    def _extract_entities_from_query(self, query: str) -> list[str]:
        """Extract equipment tags and entity references from query."""
        entities = []

        # Pattern match for equipment tags (e.g., P-101A, V-310, E-205)
        import re
        equipment_pattern = r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b'
        matches = re.findall(equipment_pattern, query.upper())
        entities.extend(matches)

        # Check for personnel names mentioned in the knowledge graph
        for node in self.kg.graph.nodes(data=True):
            node_id, data = node
            if data.get('node_type') == 'personnel':
                name = data.get('name', '')
                if name.lower() in query.lower():
                    entities.append(node_id)

        # Check for failure modes
        failure_keywords = ['seal', 'failure', 'leak', 'corrosion', 'vibration', 'fouling', 'degradation']
        for keyword in failure_keywords:
            if keyword in query.lower():
                # Find matching failure mode nodes
                for node in self.kg.graph.nodes(data=True):
                    node_id, data = node
                    if data.get('node_type') == 'failure_mode':
                        if keyword in node_id.lower():
                            entities.append(node_id)

        return list(set(entities))

    def _get_graph_context(self, entities: list[str], hops: int = 1) -> dict:
        """Get graph neighborhood context for extracted entities."""
        context = {
            "related_documents": set(),
            "related_equipment": set(),
            "related_failures": set(),
            "related_personnel": set(),
            "edges": []
        }

        for entity in entities:
            neighbors = self.kg.get_neighbors(entity, hops=hops)

            for node in neighbors.get("nodes", []):
                node_type = node.get("node_type", "")
                node_id = node.get("id", "")

                if node_type == "document":
                    context["related_documents"].add(node_id)
                elif node_type == "equipment":
                    context["related_equipment"].add(node_id)
                elif node_type == "failure_mode":
                    context["related_failures"].add(node_id)
                elif node_type == "personnel":
                    context["related_personnel"].add(node_id)

            context["edges"].extend(neighbors.get("edges", []))

        # Convert sets to lists for JSON serialization
        context["related_documents"] = list(context["related_documents"])
        context["related_equipment"] = list(context["related_equipment"])
        context["related_failures"] = list(context["related_failures"])
        context["related_personnel"] = list(context["related_personnel"])

        return context

    def _retrieve_chunks(self, query: str, top_k: int = 8, graph_docs: list[str] = None) -> list[dict]:
        """Retrieve relevant chunks using vector similarity + graph boosting."""
        # Query ChromaDB using its built-in embedding (same as used during ingestion)
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k * 2,  # Get more to allow graph boosting
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            chunk = {
                "id": doc_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
                "graph_boosted": False
            }

            # Boost score if document is in graph context
            if graph_docs:
                doc_name = chunk["metadata"].get("source", "").split("/")[-1]
                base_doc = doc_id.split("#")[0]  # Remove chunk suffix
                if base_doc in graph_docs or doc_name in graph_docs:
                    chunk["distance"] *= 0.7  # Boost by reducing distance
                    chunk["graph_boosted"] = True

            chunks.append(chunk)

        # Sort by distance (lower is better) and take top_k
        chunks.sort(key=lambda x: x["distance"])
        return chunks[:top_k]

    def _format_context(self, chunks: list[dict], graph_context: dict) -> str:
        """Format retrieved chunks and graph context for the LLM."""
        context_parts = []

        # Add graph context summary
        if graph_context["related_equipment"]:
            context_parts.append(f"Related Equipment: {', '.join(graph_context['related_equipment'])}")
        if graph_context["related_failures"]:
            context_parts.append(f"Related Failure Modes: {', '.join(graph_context['related_failures'])}")
        if graph_context["related_documents"]:
            context_parts.append(f"Graph-linked Documents: {', '.join(graph_context['related_documents'][:5])}")

        context_parts.append("\n--- Retrieved Document Excerpts ---\n")

        # Add chunk contents
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", chunk["id"])
            source_name = Path(source).name if source else chunk["id"]
            boost_marker = " [GRAPH-LINKED]" if chunk.get("graph_boosted") else ""

            context_parts.append(f"[Source {i}: {source_name}{boost_marker}]")
            context_parts.append(chunk["text"])
            context_parts.append("")

        return "\n".join(context_parts)

    def _generate_answer(self, query: str, context: str, graph_entities: list[str]) -> dict:
        """Generate answer using LLM with context."""

        system_context = """You are AssetBrain, an industrial knowledge assistant for Vantara Petrochem Unit 3.
Your role is to answer questions about equipment, maintenance, incidents, and compliance using the provided context.

Guidelines:
1. Base your answer ONLY on the provided context. Do not make up information.
2. Cite specific sources using [Source N] format when referencing information.
3. If the context doesn't contain enough information, say so clearly.
4. For pattern analysis questions, synthesize information across multiple sources.
5. Be specific about equipment tags, dates, personnel, and findings.
6. If you identify a potential safety or compliance issue, highlight it clearly.

When analyzing patterns or correlations:
- Look for temporal relationships (dates, sequences)
- Look for equipment relationships (same system, same type)
- Look for causal relationships (root causes, contributing factors)
- Cross-reference work orders, incidents, and inspection findings"""

        prompt = f"""{system_context}

Context:
{context}

Question: {query}

Provide a comprehensive answer based on the context above. Include:
1. Direct answer to the question
2. Supporting evidence with source citations [Source N]
3. Any patterns or correlations you notice across sources
4. Relevant recommendations if applicable

Also provide:
- A confidence level (HIGH, MEDIUM, LOW) based on how well the context supports your answer
- A brief reason for your confidence level"""

        response = self.llm.generate(prompt=prompt)

        # Parse the response to extract structured components
        return self._parse_response(response, graph_entities)

    def _parse_response(self, response: str, graph_entities: list[str]) -> dict:
        """Parse LLM response into structured format."""
        # Extract confidence if mentioned
        confidence = "MEDIUM"
        confidence_reason = "Based on available context"

        lines = response.split("\n")
        answer_lines = []

        for line in lines:
            line_lower = line.lower()
            if "confidence:" in line_lower or "confidence level:" in line_lower:
                if "high" in line_lower:
                    confidence = "HIGH"
                elif "low" in line_lower:
                    confidence = "LOW"
                else:
                    confidence = "MEDIUM"
                # Try to extract reason
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        confidence_reason = parts[1].strip()
            elif "reason:" in line_lower or "confidence reason:" in line_lower:
                if ":" in line:
                    confidence_reason = line.split(":", 1)[1].strip()
            else:
                answer_lines.append(line)

        # Extract citations
        import re
        citations = list(set(re.findall(r'\[Source (\d+)[^\]]*\]', response)))

        return {
            "answer": "\n".join(answer_lines).strip(),
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "citations_found": citations,
            "graph_entities_used": graph_entities,
        }

    def query(self, query: str, top_k: int = 8) -> dict:
        """Execute a RAG query with graph augmentation."""
        start_time = time.time()

        # Step 1: Extract entities from query
        entities = self._extract_entities_from_query(query)

        # Step 2: Get graph context for entities
        graph_context = self._get_graph_context(entities, hops=1)

        # Step 3: Retrieve relevant chunks with graph boosting
        chunks = self._retrieve_chunks(
            query,
            top_k=top_k,
            graph_docs=graph_context["related_documents"]
        )

        # Step 4: Format context
        context = self._format_context(chunks, graph_context)

        # Step 5: Generate answer
        result = self._generate_answer(query, context, entities)

        # Step 6: Build citations list with source details
        citations = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", chunk["id"])
            citations.append({
                "index": i,
                "source": Path(source).name if source else chunk["id"],
                "full_path": source,
                "graph_boosted": chunk.get("graph_boosted", False),
                "relevance_score": 1 - chunk["distance"],  # Convert distance to similarity
            })

        latency_ms = (time.time() - start_time) * 1000

        return {
            "answer": result["answer"],
            "citations": citations,
            "confidence": result["confidence"],
            "confidence_reason": result["confidence_reason"],
            "latency_ms": round(latency_ms, 2),
            "graph_entities_used": result["graph_entities_used"],
            "graph_context": {
                "related_equipment": graph_context["related_equipment"],
                "related_documents": graph_context["related_documents"][:5],
            }
        }


# Singleton instance
_copilot_instance: Optional[RAGCopilot] = None


def get_copilot() -> RAGCopilot:
    """Get or create the copilot singleton."""
    global _copilot_instance
    if _copilot_instance is None:
        _copilot_instance = RAGCopilot()
    return _copilot_instance


def query_with_rag(query: str, top_k: int = 8) -> dict:
    """Convenience function for querying the copilot."""
    copilot = get_copilot()
    return copilot.query(query, top_k=top_k)
