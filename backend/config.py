"""Configuration settings for AssetBrain backend."""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CORPUS_DIR = DATA_DIR / "corpus"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "chromadb").mkdir(parents=True, exist_ok=True)

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# ChromaDB Configuration
CHROMA_PERSIST_DIR = str(DATA_DIR / "chromadb")
CHROMA_COLLECTION_NAME = "assetbrain_docs"

# Knowledge Graph
GRAPH_PATH = DATA_DIR / "graph.json"

# Query log
QUERY_LOG_PATH = DATA_DIR / "query_log.json"

# Ingestion settings
CHUNK_SIZE = 800  # approximate tokens
CHUNK_OVERLAP = 100

# Rate limiting for Gemini API
# Free tier limit: 15 RPM, so we need at least 4 seconds between requests
MIN_REQUEST_INTERVAL = 6.0  # seconds between requests (conservative for free tier)
MAX_RETRIES = 5
INITIAL_BACKOFF = 15.0  # seconds - start higher for rate limits
MAX_BACKOFF = 120.0  # seconds

# Document types
DOC_TYPES = {
    ".pdf": "pdf",
    ".txt": "text",
    ".csv": "csv",
    ".xlsx": "excel",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

# Entity extraction patterns
EQUIPMENT_TAG_PATTERN = r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b'

# Known entities (loaded from entities.json at runtime)
ENTITIES_PATH = DATA_DIR / "entities.json"
COMPLIANCE_RULES_PATH = DATA_DIR / "compliance_rules.json"
