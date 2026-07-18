# AssetBrain — Unified Industrial Knowledge Intelligence Platform

A hackathon prototype demonstrating graph-augmented RAG (Retrieval-Augmented Generation) for industrial plant operations, maintenance, and compliance.

## Overview

AssetBrain ingests industrial documents (work orders, incident reports, inspection reports, SOPs) and builds a knowledge graph to enable:
- **Intelligent Q&A Copilot**: Ask questions about equipment, failures, and patterns
- **Compliance Gap Detection**: Automated regulatory compliance assessment
- **Cross-Document Pattern Discovery**: Synthesize insights across multiple sources
- **Knowledge Graph Exploration**: Navigate entity relationships

## Key Features

### 1. Graph-Augmented RAG
- ChromaDB vector store for semantic search
- NetworkX knowledge graph for entity relationships
- Graph-boosted retrieval prioritizes documents connected to query entities
- LLM-powered answer synthesis with source citations

### 2. Planted Demo Scenarios
Three compliance gaps are intentionally planted in the synthetic corpus:

**GAP 1: P-101A Seal Failures & Incompatible Lubricant**
- Pattern: 4 mechanical seal failures on P-101A (March 2023 - April 2024)
- Root cause: EconoLube Standard 320 is incompatible with FFKM seals
- Evidence distributed across 7+ documents requiring synthesis
- Violates CR-006 (Approved Lubricants) and CR-009 (Recurring Failure RCA)

**GAP 2: V-310 CUI Finding Unresolved**
- Critical CUI inspection finding (15% wall loss) on V-310
- Engineering assessment required within 30 days (per OISD-STD-119)
- No follow-up work orders exist
- Violates CR-002 (Wall Thickness Trending) and CR-010 (Timely Remediation)

**GAP 3: LOTO Procedure Missing Zero Energy Verification**
- SOP-LOTO-001 lacks step to verify zero energy state
- Required by IS 14489:2018 Clause 6.2.3
- Violates CR-003 (LOTO Zero Energy Verification)

### 3. Synthetic Corpus
27 documents in `data/corpus/`:
- 5 detailed work order TXT files
- 8 inspection report PDFs
- 6 SOP PDFs
- 5 incident report TXT files
- 1 P&ID diagram (PNG with vision extraction)
- 1 maintenance work orders CSV
- 1 lubrication standard PDF

Entities:
- 12 equipment tags (P-101A, V-310, E-205, etc.)
- 8 personnel (Priya Sharma, Rajesh Kumar, etc.)
- 6 failure modes
- 10 regulatory references

## Architecture

### Backend (FastAPI + Python)
```
backend/
├── main.py              # FastAPI app with REST endpoints
├── config.py            # Configuration and rate limiting
├── llm_client.py        # Gemini API wrapper with caching
├── ingest.py            # Document ingestion & knowledge graph
├── copilot.py           # RAG copilot with graph augmentation
└── compliance.py        # Compliance gap detector
```

### Frontend (React + Vite + Tailwind)
```
frontend/
├── src/
│   ├── views/
│   │   ├── CopilotView.jsx      # Q&A interface
│   │   ├── ComplianceView.jsx   # Compliance dashboard
│   │   ├── GraphView.jsx        # Graph explorer
│   │   └── IngestionView.jsx    # Data upload
│   ├── services/api.js          # API client
│   └── App.jsx                  # Main app & routing
└── package.json
```

### Data Layer
```
data/
├── corpus/                      # Source documents
│   ├── work_orders/
│   ├── incident_reports/
│   ├── inspection_reports/
│   ├── sops/
│   ├── diagrams/
│   └── standards/
├── chromadb/                    # Vector store (persistent)
├── cache/                       # LLM extraction cache
├── graph.json                   # Knowledge graph export
├── entities.json                # Master entity list
├── compliance_rules.json        # Regulatory rules
└── benchmark.json               # Evaluation Q&A pairs
```

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key (free tier works)

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export GEMINI_API_KEY="your-key-here"  # Linux/Mac
set GEMINI_API_KEY=your-key-here       # Windows

# Run ingestion (one-time, ~2 minutes with rate limiting)
python -m backend.ingest

# Start API server
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

## API Endpoints

### Copilot
- `POST /api/query` - Ask a question
  ```json
  {
    "query": "What is the recurring failure mode on P-101A?",
    "top_k": 10
  }
  ```

### Compliance
- `GET /api/compliance/scan` - Run compliance scan
- `GET /api/compliance/report` - Get latest report

### Knowledge Graph
- `GET /api/graph` - Get full graph
- `GET /api/graph/node/{node_id}?hops=1` - Get node neighbors
- `GET /api/graph/stats` - Graph statistics

### Ingestion
- `POST /api/ingest?force=false` - Full corpus ingestion
- `POST /api/ingest/file` - Upload single file

## Demo Script

### 1. Show Copilot Pattern Discovery
**Query:** "What is the recurring failure mode on P-101A and what pattern precedes it?"

**Expected Result:**
- Identifies mechanical seal failures (4 occurrences)
- Discovers EconoLube lubricant change pattern
- Cites 7+ sources including WO-2024-001, INC-2023-008, LUB-STD-001.pdf
- HIGH confidence with synthesis across documents

### 2. Show Compliance Gap Detection
**Action:** Navigate to Compliance view, click "Run Scan"

**Expected Result:**
- 3 critical/high gaps identified:
  - CR-003: LOTO missing zero energy verification (CRITICAL)
  - CR-006: Unapproved lubricant usage (CRITICAL)
  - CR-009: P-101A missing formal RCA (HIGH)
- Detailed evidence and recommended actions

### 3. Show Knowledge Graph
**Action:** Navigate to Graph view, search for "P-101A"

**Expected Result:**
- Shows 10+ connected nodes
- Documents: WO-2024-001, INC-2024-001, maintenance_work_orders.csv
- Personnel: Priya Sharma, Rajesh Kumar
- Failure modes: mechanical seal failure
- Edge types: MENTIONS, PERFORMED_BY, FAILED_WITH

## Technical Highlights

### Rate Limiting & Caching
- Gemini free tier: 15 RPM
- Conservative 6s interval between requests
- File-hash based LLM extraction cache
- Exponential backoff with jitter for 429 errors

### Graph-Augmented Retrieval
1. Extract entities from query (equipment tags, personnel, failure modes)
2. Get 1-hop graph neighborhood for each entity
3. Vector search with ChromaDB
4. Boost scores for chunks from graph-connected documents
5. Inject graph context into LLM prompt

### Compliance Detection
- LLM-as-judge pattern for rule assessment
- Targeted searches for each rule type
- Evidence extraction and risk classification
- JSON-structured findings

## Performance

- **Ingestion**: ~2 minutes for 27 documents (with caching)
- **Query latency**: 15-20s (includes LLM generation)
- **Compliance scan**: ~90s for 5 rules
- **Graph operations**: <100ms

## Limitations & Future Work

**Current Limitations:**
- Single-tenant (no user auth)
- Gemini free tier rate limits
- No real-time updates
- Static graph visualization (no D3.js rendering)

**Future Enhancements:**
- Multi-modal RAG (images, tables)
- Temporal reasoning (time-series analysis)
- Predictive maintenance alerts
- Multi-agent workflow orchestration
- Graph neural networks for link prediction

## License

MIT License - Hackathon prototype, not for production use.

## Credits

Built with:
- **Gemini 2.5 Flash** for LLM reasoning
- **ChromaDB** for vector storage
- **NetworkX** for knowledge graphs
- **FastAPI** for backend
- **React + Vite + Tailwind** for frontend
- **Reportlab** for PDF generation
