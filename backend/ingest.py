"""Document ingestion pipeline with extraction, chunking, and graph building."""

import json
import hashlib
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
import pandas as pd
from pypdf import PdfReader
import networkx as nx

from .config import (
    CORPUS_DIR,
    CACHE_DIR,
    DATA_DIR,
    GRAPH_PATH,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    DOC_TYPES,
    EQUIPMENT_TAG_PATTERN,
    ENTITIES_PATH,
)


def get_file_hash(file_path: Path) -> str:
    """Generate SHA256 hash of file contents for cache keying."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_extraction_cache_path(file_hash: str) -> Path:
    """Get cache file path for extraction results."""
    cache_dir = CACHE_DIR / "extractions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{file_hash}.json"


def load_cached_extraction(file_hash: str) -> Optional[Dict]:
    """Load cached extraction if available."""
    cache_path = get_extraction_cache_path(file_hash)
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_extraction_cache(file_hash: str, extraction: Dict) -> None:
    """Save extraction results to cache."""
    cache_path = get_extraction_cache_path(file_hash)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(extraction, f, indent=2)
    except IOError as e:
        print(f"Warning: Failed to cache extraction: {e}")


def load_known_entities() -> Dict[str, Set[str]]:
    """Load known entities from entities.json for pattern matching."""
    entities = {
        "equipment_tags": set(),
        "personnel_names": set(),
        "personnel_ids": set(),
        "failure_modes": set(),
        "regulatory_refs": set(),
        "lubricants": set(),
    }

    if ENTITIES_PATH.exists():
        try:
            with open(ENTITIES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            for eq in data.get("equipment", []):
                entities["equipment_tags"].add(eq.get("tag", ""))

            for person in data.get("personnel", []):
                entities["personnel_names"].add(person.get("name", ""))
                entities["personnel_ids"].add(person.get("id", ""))

            for fm in data.get("failure_modes", []):
                entities["failure_modes"].add(fm.get("name", ""))

            for reg in data.get("regulatory_references", []):
                entities["regulatory_refs"].add(reg.get("code", ""))

            for lub in data.get("lubricants", []):
                entities["lubricants"].add(lub.get("name", ""))

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load entities.json: {e}")

    return entities


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text content from PDF file."""
    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"Error extracting PDF {file_path}: {e}")
        return ""


def extract_text_from_txt(file_path: Path) -> str:
    """Read text file content."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text file {file_path}: {e}")
        return ""


def extract_text_from_csv(file_path: Path) -> str:
    """Convert CSV to text representation."""
    try:
        df = pd.read_csv(file_path)
        # Convert to readable text format
        text_parts = []
        for idx, row in df.iterrows():
            row_text = " | ".join(f"{col}: {val}" for col, val in row.items() if pd.notna(val))
            text_parts.append(row_text)
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        return ""


def extract_image_content(file_path: Path) -> str:
    """Extract content from image using Gemini Vision."""
    from .llm_client import get_llm_client

    try:
        with open(file_path, "rb") as f:
            image_data = f.read()

        # Determine MIME type
        suffix = file_path.suffix.lower()
        mime_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }.get(suffix, "image/png")

        prompt = """Analyze this industrial P&ID (Piping and Instrumentation Diagram) or technical diagram.

Extract ALL equipment tags visible in the diagram. Equipment tags typically follow patterns like:
- P-101A (pumps)
- E-205 (exchangers)
- V-310 (vessels)
- T-401 (tanks)
- C-102 (compressors)
- H-501 (heaters)
- D-601 (columns)
- FV-1001 (valves)
- PSV-301 (safety valves)
- AG-701 (air coolers)

Also identify:
- Process flow connections between equipment
- Any text labels or descriptions

Return a JSON object with this structure:
{
    "equipment_tags": ["P-101A", "E-205", ...],
    "connections": [{"from": "T-401", "to": "P-101A", "description": "feed line"}, ...],
    "labels": ["any text labels found"],
    "diagram_type": "P&ID" or "other",
    "summary": "brief description of what this diagram shows"
}"""

        client = get_llm_client()
        result = client.extract_json(
            prompt=prompt,
            image_data=image_data,
            image_mime_type=mime_type,
            use_cache=True,
        )

        # Convert to text for embedding
        text_parts = [f"Diagram: {result.get('summary', 'Industrial diagram')}"]
        text_parts.append(f"Equipment tags: {', '.join(result.get('equipment_tags', []))}")

        for conn in result.get("connections", []):
            text_parts.append(f"Connection: {conn.get('from')} -> {conn.get('to')} ({conn.get('description', '')})")

        return "\n".join(text_parts)

    except Exception as e:
        print(f"Error extracting image content {file_path}: {e}")
        return f"Image file: {file_path.name}"


def get_document_content(file_path: Path) -> str:
    """Get text content from document based on file type."""
    suffix = file_path.suffix.lower()
    doc_type = DOC_TYPES.get(suffix)

    if doc_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif doc_type == "text":
        return extract_text_from_txt(file_path)
    elif doc_type == "csv":
        return extract_text_from_csv(file_path)
    elif doc_type == "image":
        return extract_image_content(file_path)
    else:
        print(f"Unknown document type: {suffix}")
        return ""


def extract_entities_with_llm(content: str, file_path: Path, known_entities: Dict[str, Set[str]]) -> Dict:
    """Use LLM to extract structured entities from document content."""
    from .llm_client import get_llm_client

    # Build known entities hint
    known_tags = ", ".join(sorted(known_entities["equipment_tags"]))
    known_people = ", ".join(sorted(known_entities["personnel_names"]))

    prompt = f"""Analyze this industrial document and extract structured information.

KNOWN EQUIPMENT TAGS (look for these): {known_tags}
KNOWN PERSONNEL: {known_people}

Document content:
---
{content[:8000]}
---

Extract and return a JSON object with EXACTLY this structure:
{{
    "equipment_tags": ["list of equipment tags mentioned, e.g., P-101A, V-310"],
    "personnel": ["list of person names mentioned"],
    "dates": ["list of dates in YYYY-MM-DD format if possible"],
    "failure_modes": ["list of failure modes mentioned, e.g., seal leak, bearing failure"],
    "regulatory_refs": ["list of regulatory references, e.g., OISD-STD-119, IS 14489"],
    "parameters": {{"key measurements or values mentioned": "value"}},
    "doc_type": "one of: maintenance_work_order, inspection_report, incident_report, sop, standard, pid_diagram, other",
    "summary": "2-3 sentence summary of document content"
}}

Be thorough - extract ALL equipment tags and entities mentioned."""

    try:
        client = get_llm_client()
        result = client.extract_json(prompt=prompt, use_cache=True)

        # Ensure all expected fields exist
        default_result = {
            "equipment_tags": [],
            "personnel": [],
            "dates": [],
            "failure_modes": [],
            "regulatory_refs": [],
            "parameters": {},
            "doc_type": "other",
            "summary": "",
        }

        for key in default_result:
            if key not in result:
                result[key] = default_result[key]

        return result

    except Exception as e:
        print(f"LLM extraction failed for {file_path}: {e}")
        # Fall back to regex extraction
        return extract_entities_regex(content, known_entities)


def extract_entities_regex(content: str, known_entities: Dict[str, Set[str]]) -> Dict:
    """Fallback regex-based entity extraction."""
    result = {
        "equipment_tags": [],
        "personnel": [],
        "dates": [],
        "failure_modes": [],
        "regulatory_refs": [],
        "parameters": {},
        "doc_type": "other",
        "summary": content[:200] + "..." if len(content) > 200 else content,
    }

    # Extract equipment tags
    tag_pattern = re.compile(EQUIPMENT_TAG_PATTERN)
    found_tags = set(tag_pattern.findall(content))
    # Filter to known tags
    result["equipment_tags"] = list(found_tags & known_entities["equipment_tags"])

    # Extract dates
    date_pattern = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
    result["dates"] = list(set(date_pattern.findall(content)))

    # Extract known personnel
    for name in known_entities["personnel_names"]:
        if name in content:
            result["personnel"].append(name)

    # Extract known failure modes
    content_lower = content.lower()
    for fm in known_entities["failure_modes"]:
        if fm.lower() in content_lower:
            result["failure_modes"].append(fm)

    # Extract regulatory refs
    for ref in known_entities["regulatory_refs"]:
        if ref in content:
            result["regulatory_refs"].append(ref)

    return result


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []

    # Simple word-based chunking (approximate token count)
    words = text.split()
    chunks = []

    # Approximate: 1 token ≈ 0.75 words
    words_per_chunk = int(chunk_size * 0.75)
    overlap_words = int(overlap * 0.75)

    i = 0
    while i < len(words):
        chunk_words = words[i:i + words_per_chunk]
        chunks.append(" ".join(chunk_words))
        i += words_per_chunk - overlap_words

        if i + words_per_chunk >= len(words) and i < len(words):
            # Last chunk - include remaining
            chunks.append(" ".join(words[i:]))
            break

    return chunks if chunks else [text]


def infer_doc_type(file_path: Path) -> str:
    """Infer document type from file path and name."""
    path_str = str(file_path).lower()
    name = file_path.stem.lower()

    if "work_order" in path_str or name.startswith("wo-"):
        return "maintenance_work_order"
    elif "inspection" in path_str or name.startswith("ins-"):
        return "inspection_report"
    elif "incident" in path_str or name.startswith("inc-"):
        return "incident_report"
    elif "sop" in path_str or name.startswith("sop-"):
        return "sop"
    elif "standard" in path_str or name.startswith("lub-std"):
        return "standard"
    elif "diagram" in path_str or "pid" in name:
        return "pid_diagram"
    elif file_path.suffix.lower() == ".csv":
        return "maintenance_work_order"
    else:
        return "other"


class KnowledgeGraph:
    """NetworkX-based knowledge graph for industrial entities."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_document(self, doc_id: str, doc_type: str, source_path: str, summary: str):
        """Add document node."""
        self.graph.add_node(
            doc_id,
            node_type="document",
            doc_type=doc_type,
            source_path=source_path,
            summary=summary,
        )

    def add_equipment(self, tag: str, metadata: Dict = None):
        """Add or update equipment node."""
        if not self.graph.has_node(tag):
            self.graph.add_node(
                tag,
                node_type="equipment",
                **(metadata or {})
            )

    def add_personnel(self, name: str, metadata: Dict = None):
        """Add or update personnel node."""
        node_id = f"PERSON:{name}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                node_type="personnel",
                name=name,
                **(metadata or {})
            )
        return node_id

    def add_failure_mode(self, name: str):
        """Add failure mode node."""
        node_id = f"FM:{name}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, node_type="failure_mode", name=name)
        return node_id

    def add_regulatory_ref(self, code: str):
        """Add regulatory reference node."""
        node_id = f"REG:{code}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, node_type="regulatory", code=code)
        return node_id

    def add_edge(self, source: str, target: str, edge_type: str, **attrs):
        """Add edge between nodes."""
        if self.graph.has_node(source) and self.graph.has_node(target):
            self.graph.add_edge(source, target, edge_type=edge_type, **attrs)

    def save(self, path: Path = GRAPH_PATH):
        """Save graph to JSON."""
        data = nx.node_link_data(self.graph)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Graph saved: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    @classmethod
    def load(cls, path: Path = GRAPH_PATH) -> "KnowledgeGraph":
        """Load graph from JSON."""
        kg = cls()
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            kg.graph = nx.node_link_graph(data)
        return kg

    def get_node_summary(self) -> Dict[str, int]:
        """Get count of nodes by type."""
        counts = {}
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def get_edge_summary(self) -> Dict[str, int]:
        """Get count of edges by type."""
        counts = {}
        for u, v, data in self.graph.edges(data=True):
            edge_type = data.get("edge_type", "unknown")
            counts[edge_type] = counts.get(edge_type, 0) + 1
        return counts

    def get_neighbors(self, node_id: str, hops: int = 1) -> Dict:
        """Get node neighborhood up to n hops."""
        if not self.graph.has_node(node_id):
            return {"node": node_id, "found": False}

        neighbors = {"node": node_id, "found": True, "data": dict(self.graph.nodes[node_id]), "edges": []}

        visited = {node_id}
        current_level = {node_id}

        for hop in range(hops):
            next_level = set()
            for node in current_level:
                # Outgoing edges
                for _, target, data in self.graph.out_edges(node, data=True):
                    if target not in visited:
                        next_level.add(target)
                        neighbors["edges"].append({
                            "source": node,
                            "target": target,
                            "type": data.get("edge_type"),
                            "target_data": dict(self.graph.nodes[target]),
                        })
                # Incoming edges
                for source, _, data in self.graph.in_edges(node, data=True):
                    if source not in visited:
                        next_level.add(source)
                        neighbors["edges"].append({
                            "source": source,
                            "target": node,
                            "type": data.get("edge_type"),
                            "source_data": dict(self.graph.nodes[source]),
                        })
            visited.update(next_level)
            current_level = next_level

        return neighbors


class DocumentIngester:
    """Main ingestion orchestrator."""

    def __init__(self):
        self.known_entities = load_known_entities()
        self.graph = KnowledgeGraph()
        self._init_chromadb()
        self._load_existing_graph()
        self._processed_docs: Set[str] = set()
        self._load_processed_docs()

    def _init_chromadb(self):
        """Initialize ChromaDB client and collection."""
        import chromadb
        from chromadb.config import Settings

        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _load_existing_graph(self):
        """Load existing graph if available."""
        if GRAPH_PATH.exists():
            self.graph = KnowledgeGraph.load(GRAPH_PATH)

    def _load_processed_docs(self):
        """Load set of already processed document IDs."""
        processed_path = CACHE_DIR / "processed_docs.json"
        if processed_path.exists():
            try:
                with open(processed_path, "r") as f:
                    self._processed_docs = set(json.load(f))
            except (json.JSONDecodeError, IOError):
                self._processed_docs = set()

    def _save_processed_docs(self):
        """Save set of processed document IDs."""
        processed_path = CACHE_DIR / "processed_docs.json"
        with open(processed_path, "w") as f:
            json.dump(list(self._processed_docs), f)

    def _generate_doc_id(self, file_path: Path) -> str:
        """Generate unique document ID from file path."""
        rel_path = file_path.relative_to(CORPUS_DIR)
        return str(rel_path).replace("\\", "/").replace(" ", "_")

    def ingest_file(self, file_path: Path, force: bool = False) -> Dict:
        """Ingest a single file."""
        doc_id = self._generate_doc_id(file_path)
        file_hash = get_file_hash(file_path)

        # Check if already processed (unless forced)
        if not force and doc_id in self._processed_docs:
            cached = load_cached_extraction(file_hash)
            if cached:
                return {"doc_id": doc_id, "status": "cached", "extraction": cached}

        print(f"Processing: {doc_id}")

        # Check extraction cache by file hash
        extraction = load_cached_extraction(file_hash)

        if extraction is None:
            # Extract content
            content = get_document_content(file_path)
            if not content:
                return {"doc_id": doc_id, "status": "error", "message": "Could not extract content"}

            # Extract entities with LLM
            extraction = extract_entities_with_llm(content, file_path, self.known_entities)
            extraction["content"] = content
            extraction["file_hash"] = file_hash
            extraction["source_path"] = str(file_path)

            # Override doc_type with inferred if LLM didn't get it right
            inferred_type = infer_doc_type(file_path)
            if extraction.get("doc_type") == "other":
                extraction["doc_type"] = inferred_type

            # Cache extraction
            save_extraction_cache(file_hash, extraction)
        else:
            content = extraction.get("content", "")

        # Chunk and store in ChromaDB
        chunks = chunk_text(content)
        if chunks:
            chunk_ids = [f"{doc_id}#chunk{i}" for i in range(len(chunks))]

            # Prepare metadata for each chunk
            metadatas = []
            for i in range(len(chunks)):
                metadatas.append({
                    "doc_id": doc_id,
                    "doc_type": extraction.get("doc_type", "other"),
                    "equipment_tags": ",".join(extraction.get("equipment_tags", [])),
                    "source_path": str(file_path),
                    "chunk_index": i,
                })

            # Upsert to ChromaDB
            self.collection.upsert(
                ids=chunk_ids,
                documents=chunks,
                metadatas=metadatas,
            )

        # Update knowledge graph
        self._update_graph(doc_id, extraction, file_path)

        # Mark as processed
        self._processed_docs.add(doc_id)

        return {"doc_id": doc_id, "status": "ingested", "extraction": extraction, "chunks": len(chunks)}

    def _update_graph(self, doc_id: str, extraction: Dict, file_path: Path):
        """Update knowledge graph with extracted entities."""
        doc_type = extraction.get("doc_type", "other")
        summary = extraction.get("summary", "")

        # Add document node
        self.graph.add_document(doc_id, doc_type, str(file_path), summary)

        # Add equipment and edges
        for tag in extraction.get("equipment_tags", []):
            self.graph.add_equipment(tag)
            self.graph.add_edge(doc_id, tag, "MENTIONS")

        # Add personnel and edges
        for name in extraction.get("personnel", []):
            person_id = self.graph.add_personnel(name)
            self.graph.add_edge(doc_id, person_id, "INVOLVES")

            # If it's a work order, add PERFORMED_BY edge to equipment
            if doc_type == "maintenance_work_order":
                for tag in extraction.get("equipment_tags", []):
                    self.graph.add_edge(person_id, tag, "PERFORMED_BY")

        # Add failure modes and edges
        for fm in extraction.get("failure_modes", []):
            fm_id = self.graph.add_failure_mode(fm)
            self.graph.add_edge(doc_id, fm_id, "DESCRIBES")

            # Connect failure mode to equipment
            for tag in extraction.get("equipment_tags", []):
                self.graph.add_edge(tag, fm_id, "FAILED_WITH")

        # Add regulatory refs and edges
        for ref in extraction.get("regulatory_refs", []):
            ref_id = self.graph.add_regulatory_ref(ref)
            self.graph.add_edge(doc_id, ref_id, "REFERENCES")

            # Connect to equipment if inspection/compliance doc
            if doc_type in ["inspection_report", "sop", "standard"]:
                for tag in extraction.get("equipment_tags", []):
                    self.graph.add_edge(tag, ref_id, "GOVERNED_BY")

    def ingest_corpus(self, force: bool = False) -> Dict:
        """Ingest all documents in the corpus directory."""
        results = {
            "processed": 0,
            "cached": 0,
            "errors": 0,
            "documents": [],
        }

        # Find all documents
        for file_path in CORPUS_DIR.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in DOC_TYPES:
                try:
                    result = self.ingest_file(file_path, force=force)
                    results["documents"].append(result)

                    if result["status"] == "ingested":
                        results["processed"] += 1
                    elif result["status"] == "cached":
                        results["cached"] += 1
                    else:
                        results["errors"] += 1

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    results["errors"] += 1
                    results["documents"].append({
                        "doc_id": str(file_path),
                        "status": "error",
                        "message": str(e),
                    })

        # Save graph and processed docs list
        self.graph.save()
        self._save_processed_docs()

        # Print summary
        print(f"\n=== Ingestion Complete ===")
        print(f"Processed: {results['processed']}")
        print(f"Cached: {results['cached']}")
        print(f"Errors: {results['errors']}")
        print(f"\nGraph Summary:")
        print(f"  Nodes by type: {self.graph.get_node_summary()}")
        print(f"  Edges by type: {self.graph.get_edge_summary()}")
        print(f"\nChromaDB: {self.collection.count()} chunks indexed")

        return results

    def ingest_single_file(self, file_path: Path) -> Dict:
        """Ingest a single uploaded file."""
        result = self.ingest_file(file_path, force=True)
        self.graph.save()
        self._save_processed_docs()
        return result

    def get_stats(self) -> Dict:
        """Get current ingestion statistics."""
        return {
            "documents_processed": len(self._processed_docs),
            "chunks_indexed": self.collection.count(),
            "graph_nodes": self.graph.get_node_summary(),
            "graph_edges": self.graph.get_edge_summary(),
        }


# Module-level instance
_ingester: Optional[DocumentIngester] = None


def get_ingester() -> DocumentIngester:
    """Get or create the ingester singleton."""
    global _ingester
    if _ingester is None:
        _ingester = DocumentIngester()
    return _ingester


def run_full_ingestion(force: bool = False) -> Dict:
    """Run full corpus ingestion."""
    ingester = get_ingester()
    return ingester.ingest_corpus(force=force)


if __name__ == "__main__":
    # Run ingestion when executed directly
    import sys
    force = "--force" in sys.argv
    run_full_ingestion(force=force)
