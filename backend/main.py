"""FastAPI application for AssetBrain backend."""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .config import (
    GEMINI_API_KEY,
    CORPUS_DIR,
    DATA_DIR,
    GRAPH_PATH,
    CHROMA_PERSIST_DIR,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("assetbrain")

# Startup status tracking
startup_status = {
    "api_key": False,
    "graph": False,
    "chromadb": False,
    "ready": False,
    "errors": []
}


def check_startup_dependencies():
    """Check all required dependencies at startup and log status."""
    global startup_status
    startup_status["errors"] = []

    # Check API key - FATAL if not set
    if GEMINI_API_KEY:
        startup_status["api_key"] = True
        logger.info("✓ GEMINI_API_KEY is set")
    else:
        startup_status["api_key"] = False
        error_msg = "FATAL: GEMINI_API_KEY environment variable not set. Set it with: set GEMINI_API_KEY=your-key"
        startup_status["errors"].append(error_msg)
        logger.critical(f"✗ {error_msg}")
        logger.critical("Server cannot start without GEMINI_API_KEY. Exiting.")
        sys.exit(1)

    # Check graph.json
    if GRAPH_PATH.exists():
        try:
            with open(GRAPH_PATH, "r") as f:
                graph_data = json.load(f)
            node_count = len(graph_data.get("nodes", []))
            edge_count = len(graph_data.get("edges", []))
            startup_status["graph"] = True
            logger.info(f"✓ graph.json loaded ({node_count} nodes, {edge_count} edges)")
        except Exception as e:
            startup_status["graph"] = False
            error_msg = f"graph.json exists but failed to load: {e}"
            startup_status["errors"].append(error_msg)
            logger.error(f"✗ {error_msg}")
    else:
        startup_status["graph"] = False
        error_msg = f"graph.json not found at {GRAPH_PATH} - run ingestion first"
        startup_status["errors"].append(error_msg)
        logger.warning(f"✗ {error_msg}")

    # Check ChromaDB - just verify directory structure (avoid creating client conflicts)
    chroma_path = Path(CHROMA_PERSIST_DIR)
    sqlite_file = chroma_path / "chroma.sqlite3"
    if sqlite_file.exists():
        startup_status["chromadb"] = True
        logger.info(f"✓ ChromaDB directory ready at {chroma_path}")
    else:
        startup_status["chromadb"] = False
        error_msg = "ChromaDB not initialized - run ingestion first"
        startup_status["errors"].append(error_msg)
        logger.warning(f"✗ {error_msg}")

    # Overall readiness
    startup_status["ready"] = all([
        startup_status["api_key"],
        startup_status["graph"],
        startup_status["chromadb"]
    ])

    if startup_status["ready"]:
        logger.info("✓ AssetBrain is fully ready for queries")
    else:
        logger.warning(f"⚠ AssetBrain started with issues: {len(startup_status['errors'])} problem(s)")
        for err in startup_status["errors"]:
            logger.warning(f"  - {err}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("AssetBrain API Starting...")
    logger.info("=" * 60)
    check_startup_dependencies()
    logger.info("=" * 60)
    yield
    # Shutdown
    logger.info("AssetBrain API shutting down...")

app = FastAPI(
    title="AssetBrain API",
    description="Unified Industrial Knowledge Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 8


class QueryResponse(BaseModel):
    answer: str
    citations: list
    confidence: str
    confidence_reason: str
    latency_ms: float
    graph_entities_used: list


class IngestResponse(BaseModel):
    status: str
    documents_processed: int
    documents_cached: int
    errors: int


class UploadResponse(BaseModel):
    status: str
    doc_id: str
    extracted_entities: dict
    new_graph_edges: int


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint with detailed status."""
    return {
        "status": "ready" if startup_status["ready"] else "degraded",
        "components": {
            "api_key": startup_status["api_key"],
            "graph": startup_status["graph"],
            "chromadb": startup_status["chromadb"],
        },
        "errors": startup_status["errors"] if not startup_status["ready"] else [],
        "timestamp": datetime.utcnow().isoformat(),
    }


# Ingestion endpoints
@app.post("/api/ingest", response_model=IngestResponse)
async def run_ingestion(force: bool = Query(False, description="Force re-ingestion of all documents")):
    """Run full corpus ingestion."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    try:
        from .ingest import run_full_ingestion
        result = run_full_ingestion(force=force)
        return IngestResponse(
            status="completed",
            documents_processed=result["processed"],
            documents_cached=result["cached"],
            errors=result["errors"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/file")
async def ingest_single_file(file: UploadFile = File(...)):
    """Ingest a single uploaded file."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    # Save uploaded file to corpus
    try:
        # Determine subdirectory based on filename
        filename = file.filename
        if filename.lower().startswith("wo-"):
            subdir = "work_orders"
        elif filename.lower().startswith("inc-"):
            subdir = "incident_reports"
        elif filename.lower().startswith("ins-"):
            subdir = "inspection_reports"
        elif filename.lower().startswith("sop-"):
            subdir = "sops"
        else:
            subdir = "uploads"

        target_dir = CORPUS_DIR / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        # Save file
        with open(target_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Ingest the file
        from .ingest import get_ingester
        ingester = get_ingester()
        result = ingester.ingest_single_file(target_path)

        return {
            "status": "success",
            "doc_id": result["doc_id"],
            "extracted_entities": result.get("extraction", {}),
            "chunks_created": result.get("chunks", 0),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Query endpoint
@app.post("/api/query")
async def query_copilot(request: QueryRequest):
    """Query the RAG copilot."""
    # Check prerequisites with clear error messages
    if not startup_status["api_key"]:
        logger.error("Query rejected: GEMINI_API_KEY not set")
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY not configured. Set the environment variable and restart the server."
        )

    if not startup_status["chromadb"]:
        logger.error("Query rejected: ChromaDB collection not available")
        raise HTTPException(
            status_code=503,
            detail="ChromaDB collection 'assetbrain_docs' not found. Run ingestion first: POST /api/ingest"
        )

    if not startup_status["graph"]:
        logger.error("Query rejected: Knowledge graph not available")
        raise HTTPException(
            status_code=503,
            detail="Knowledge graph (graph.json) not found. Run ingestion first: POST /api/ingest"
        )

    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        from .copilot import query_with_rag
        result = query_with_rag(request.query, top_k=request.top_k)
        logger.info(f"Query completed successfully (confidence: {result.get('confidence', 'N/A')})")
        return result
    except ImportError as e:
        logger.error(f"Copilot import error: {e}")
        raise HTTPException(status_code=501, detail=f"Copilot module error: {e}")
    except Exception as e:
        # Log the full exception for debugging
        logger.exception(f"Query failed with exception: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# Graph endpoints
@app.get("/api/graph")
async def get_graph():
    """Get the full knowledge graph."""
    if not GRAPH_PATH.exists():
        return {"nodes": [], "edges": []}

    try:
        with open(GRAPH_PATH, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/node/{node_id}")
async def get_node_neighbors(node_id: str, hops: int = Query(1, ge=1, le=3)):
    """Get a node and its neighbors."""
    try:
        from .ingest import KnowledgeGraph
        kg = KnowledgeGraph.load()
        return kg.get_neighbors(node_id, hops=hops)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/stats")
async def get_graph_stats():
    """Get graph statistics."""
    try:
        from .ingest import KnowledgeGraph

        # Load graph directly
        kg = KnowledgeGraph.load()

        # Get ChromaDB chunk count - use the copilot's collection to avoid client conflicts
        chunks_indexed = 0
        try:
            from .copilot import get_copilot
            copilot = get_copilot()
            chunks_indexed = copilot.collection.count()
        except Exception:
            # If copilot not initialized, try direct access
            try:
                import chromadb
                from chromadb.config import Settings
                client = chromadb.PersistentClient(
                    path=str(CHROMA_PERSIST_DIR),
                    settings=Settings(anonymized_telemetry=False),
                )
                collection = client.get_collection("assetbrain_docs")
                chunks_indexed = collection.count()
            except Exception:
                pass

        return {
            "documents_processed": kg.get_node_summary().get("document", 0),
            "chunks_indexed": chunks_indexed,
            "graph_nodes": kg.get_node_summary(),
            "graph_edges": kg.get_edge_summary(),
        }
    except Exception as e:
        logger.exception(f"Graph stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Document serving
@app.get("/api/doc/{doc_id:path}")
async def get_document(doc_id: str):
    """Serve a document file."""
    # Convert doc_id back to path
    file_path = CORPUS_DIR / doc_id

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )


# Compliance endpoints (placeholder - will be implemented in Milestone 4)
@app.get("/api/compliance/scan")
async def run_compliance_scan():
    """Run compliance gap detection."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    try:
        from .compliance import run_compliance_scan
        return run_compliance_scan()
    except ImportError:
        raise HTTPException(status_code=501, detail="Compliance scanner not yet implemented")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance/report")
async def get_compliance_report():
    """Get the last compliance scan report."""
    report_path = DATA_DIR / "compliance_report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="No compliance report available. Run a scan first.")

    try:
        with open(report_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Benchmark endpoints (placeholder - will be implemented in Milestone 5)
@app.post("/api/benchmark/run")
async def run_benchmark():
    """Run the evaluation benchmark."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    try:
        from .benchmark import run_benchmark
        return run_benchmark()
    except ImportError:
        raise HTTPException(status_code=501, detail="Benchmark not yet implemented")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Entities endpoint
@app.get("/api/entities")
async def get_entities():
    """Get the known entities list."""
    entities_path = DATA_DIR / "entities.json"
    if not entities_path.exists():
        raise HTTPException(status_code=404, detail="Entities file not found")

    try:
        with open(entities_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
