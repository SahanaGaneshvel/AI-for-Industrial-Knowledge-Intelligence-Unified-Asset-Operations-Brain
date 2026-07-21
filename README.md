# AssetBrain — Unified Industrial Knowledge Intelligence Platform

A graph-augmented RAG (Retrieval-Augmented Generation) platform for industrial plant operations, maintenance, and compliance. Built for the hackathon to demonstrate intelligent cross-document pattern discovery and automated compliance gap detection.

## Overview

AssetBrain ingests industrial documents (work orders, incident reports, inspection reports, SOPs, P&ID diagrams) and builds a knowledge graph to enable:

- **Intelligent Q&A Copilot**: Ask natural language questions about equipment, failures, maintenance patterns, and compliance
- **Compliance Gap Detection**: Automated assessment against 10 regulatory rules with LLM-as-judge pattern
- **Cross-Document Pattern Discovery**: Synthesize insights that require correlating information across multiple sources
- **Knowledge Graph Exploration**: Navigate entity relationships between documents, equipment, personnel, and failure modes
- **Live Document Upload**: Add new documents to the knowledge base in real-time

## Technology Stack

| Component | Technology |
|-----------|------------|
| **LLM** | Google Gemini 2.5 Flash |
| **Vector Store** | ChromaDB (persistent) |
| **Knowledge Graph** | NetworkX (DiGraph) |
| **Backend** | FastAPI + Python 3.10+ |
| **Frontend** | React 18 + Vite + Tailwind CSS |
| **PDF Parsing** | pypdf |
| **Vision/P&ID** | Gemini Vision API |

## Key Features

### 1. Graph-Augmented RAG Pipeline

The copilot uses a sophisticated retrieval pipeline:

1. **Entity Extraction**: Identifies equipment tags (P-101A, V-310), personnel names, and failure modes from the query
2. **Graph Context**: Retrieves 1-hop neighborhood from knowledge graph for each entity
3. **Vector Search**: Semantic search via ChromaDB with graph-boosted scoring
4. **Context Assembly**: Combines graph relationships with retrieved chunks
5. **LLM Synthesis**: Generates answer with source citations and confidence scoring

### 2. Compliance Scanner

Automated regulatory compliance assessment:

- **10 Regulatory Rules**: Based on OISD standards, IS codes, Factories Act, PESO Rules
- **LLM-as-Judge**: Each rule assessed by prompting LLM with relevant document context
- **Specialized Checks**: Targeted retrieval for known gap patterns (CR-002, CR-003, CR-006, CR-009, CR-010)
- **Generic Checker**: Falls back to keyword-based retrieval for rules without specialized logic
- **Risk Classification**: CRITICAL, HIGH, MEDIUM, LOW with evidence and recommendations

### 3. Knowledge Graph

NetworkX-based entity relationship graph:

- **Node Types**: document, equipment, personnel, failure_mode, regulatory
- **Edge Types**: MENTIONS, INVOLVES, DESCRIBES, FAILED_WITH, GOVERNED_BY, PERFORMED_BY, REFERENCES
- **Operations**: 1-3 hop neighbor traversal, node statistics, relationship exploration

### 4. Document Ingestion

Multi-format document processing:

- **PDF**: Text extraction via pypdf
- **TXT/CSV**: Direct parsing with pandas
- **Images (PNG/JPG)**: Vision extraction via Gemini for P&ID diagrams
- **LLM Entity Extraction**: Equipment tags, personnel, dates, failure modes, regulatory refs
- **Chunking**: 800-token chunks with 100-token overlap
- **Caching**: SHA256 file-hash based extraction cache

### 5. Mobile-Responsive Frontend

React SPA with 4 main views:

- **Copilot View**: Q&A interface with example questions, confidence display, source citations
- **Compliance View**: Dashboard with summary stats, gap details, evidence, recommendations
- **Graph View**: Node search, neighbor exploration, statistics
- **Ingestion View**: File upload, full corpus re-indexing

## Planted Demo Scenarios

Three compliance gaps are intentionally planted in the synthetic corpus:

### GAP 1: P-101A Seal Failures & Incompatible Lubricant (CRITICAL)
- **Pattern**: 4 mechanical seal failures on P-101A (March 2023 - April 2024)
- **Root Cause**: EconoLube Standard 320 is incompatible with FFKM seals per LUB-STD-001
- **Evidence**: Distributed across 7+ documents (WO-2023-001, WO-2023-003, WO-2023-013, WO-2024-001, WO-2024-006, INC-2023-008, LUB-STD-001.pdf)
- **Violates**: CR-006 (Approved Lubricants) and CR-009 (Recurring Failure RCA)
- **Discovery**: Requires synthesizing lubricant change records + seal failures + incompatibility warning

### GAP 2: V-310 CUI Finding Unresolved (CRITICAL)
- **Issue**: 15% wall loss due to CUI on V-310 pressure vessel (August 2023)
- **Requirement**: Engineering assessment within 30 days per OISD-STD-119
- **Evidence**: INS-2023-V310-001.pdf documents finding, no follow-up work orders exist
- **Violates**: CR-002 (Wall Thickness Trending) and CR-010 (Timely Remediation)

### GAP 3: LOTO Procedure Missing Zero Energy Verification (CRITICAL)
- **Deficiency**: SOP-LOTO-001 lacks step to verify zero energy state by attempting startup
- **Requirement**: IS 14489:2018 Clause 6.2.3 mandates this verification
- **Violates**: CR-003 (LOTO Zero Energy Verification)

## Synthetic Corpus

**27 documents** in `data/corpus/`:

| Category | Count | Format | Examples |
|----------|-------|--------|----------|
| Work Orders | 5 | TXT | WO-2023-001.txt, WO-2024-006.txt |
| Incident Reports | 5 | TXT | INC-2023-008.txt, INC-2024-001.txt |
| Inspection Reports | 8 | PDF | INS-2023-V310-001.pdf, INS-2024-P101A-VIB-001.pdf |
| SOPs | 6 | PDF | SOP-LOTO-001.pdf, SOP-PUMP-001.pdf |
| Standards | 1 | PDF | LUB-STD-001.pdf |
| P&ID Diagrams | 1 | PNG | CDU-PID-001.png |
| CSV Data | 1 | CSV | maintenance_work_orders.csv (19 records) |

**Entities** (`data/entities.json`):
- 12 equipment tags (P-101A, P-101B, V-310, E-205, C-102, T-401, T-402, H-501, D-601, FV-1001, PSV-301, AG-701)
- 8 personnel with certifications
- 6 failure modes
- 2 lubricants (VantaLube Premium 320, EconoLube Standard 320)

## Architecture

### Backend Structure
```
backend/
├── main.py              # FastAPI app with 12 REST endpoints
├── config.py            # Configuration, paths, rate limiting (6s interval)
├── llm_client.py        # Gemini API wrapper with caching & exponential backoff
├── ingest.py            # Document ingestion, entity extraction, KnowledgeGraph class
├── copilot.py           # RAGCopilot with graph-augmented retrieval
└── compliance.py        # ComplianceScanner with 10-rule assessment
```

### Frontend Structure
```
frontend/
├── src/
│   ├── App.jsx                  # Router, navigation with mobile hamburger menu
│   ├── services/api.js          # Axios API client
│   └── views/
│       ├── CopilotView.jsx      # Q&A with example questions, citations
│       ├── ComplianceView.jsx   # Dashboard with gaps & evidence
│       ├── GraphView.jsx        # Node search & statistics
│       └── IngestionView.jsx    # File upload & re-index
├── package.json
├── vite.config.js
└── tailwind.config.js
```

### Data Layer
```
data/
├── corpus/                      # Source documents (27 files)
│   ├── work_orders/            # 5 TXT files
│   ├── incident_reports/       # 5 TXT files
│   ├── inspection_reports/     # 8 PDF files
│   ├── sops/                   # 6 PDF files
│   ├── standards/              # 1 PDF file
│   └── diagrams/               # 1 PNG file
├── chromadb/                    # Vector store (persistent, ~29 chunks)
├── cache/                       # LLM extraction cache (by file hash)
├── graph.json                   # Knowledge graph (135 nodes, 641 edges)
├── entities.json                # Master entity definitions
├── compliance_rules.json        # 10 regulatory rules
├── compliance_report.json       # Latest scan results
└── benchmark.json               # 12 evaluation Q&A pairs
```

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key ([Get free key](https://ai.google.dev/))

### Backend Setup
```bash
# Clone repository
git clone https://github.com/your-repo/assetbrain.git
cd assetbrain

# Install Python dependencies
pip install -r requirements.txt

# Set API key (required - server will not start without it)
set GEMINI_API_KEY=your-key-here       # Windows
export GEMINI_API_KEY="your-key-here"  # Linux/Mac

# Start API server
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

### First-Time Ingestion
If `data/chromadb/` is empty, run ingestion:
```bash
# Option 1: Via API (after server is running)
curl -X POST "http://localhost:8000/api/ingest?force=false"

# Option 2: Direct Python
python -m backend.ingest
```

## API Reference

### Health & Status
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health with component status |
| `/api/entities` | GET | Master entity list |

### Copilot
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Ask a question |

**Request:**
```json
{
  "query": "What is the recurring failure mode on P-101A?",
  "top_k": 10
}
```

**Response:**
```json
{
  "answer": "P-101A has experienced 4 recurring mechanical seal failures...",
  "citations": [{"index": 1, "source": "WO-2024-001.txt", "relevance_score": 0.87, "graph_boosted": true}],
  "confidence": "HIGH",
  "confidence_reason": "Multiple corroborating sources with clear pattern",
  "latency_ms": 15234.5,
  "graph_entities_used": ["P-101A", "FM:mechanical seal failure"],
  "graph_context": {"related_equipment": ["P-101A"], "related_documents": ["WO-2024-001.txt"]}
}
```

### Compliance
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/compliance/scan` | GET | Run fresh compliance scan (~90s) |
| `/api/compliance/report` | GET | Get latest cached report |

### Knowledge Graph
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/graph` | GET | Full graph (nodes + edges) |
| `/api/graph/stats` | GET | Node/edge counts by type |
| `/api/graph/node/{id}?hops=1` | GET | Node neighbors (1-3 hops) |

### Ingestion
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ingest?force=false` | POST | Full corpus ingestion |
| `/api/ingest/file` | POST | Upload single file (multipart/form-data) |
| `/api/doc/{doc_id}` | GET | Download document |

## Demo Script

### 1. Copilot Pattern Discovery (Flagship Demo)
**Query:** "What is the recurring failure mode on P-101A and what pattern precedes it?"

**Expected:**
- Identifies 4 mechanical seal failures
- Discovers EconoLube lubricant change correlation
- Cites 5+ sources including LUB-STD-001.pdf
- HIGH confidence with cross-document synthesis

### 2. Compliance Gap Detection
**Action:** Navigate to Compliance → Click "Run Scan"

**Expected:**
- 6 gaps identified (CR-001, CR-002, CR-003, CR-005, CR-006, CR-009)
- CRITICAL: CR-002 (V-310 wall loss), CR-003 (LOTO), CR-006 (lubricant)
- Detailed evidence and recommended actions

### 3. Knowledge Graph Exploration
**Action:** Navigate to Graph → Search "P-101A"

**Expected:**
- 10+ connected nodes
- Documents: WO-2024-001, INC-2024-001, maintenance_work_orders.csv
- Personnel: Priya Sharma, Rajesh Kumar
- Failure modes: mechanical seal failure, elastomer degradation

### 4. Live Document Upload
**Action:** Navigate to Ingestion → Upload a .txt work order

**Expected:**
- Document processed and chunked
- Entities extracted
- Graph updated with new relationships

## Performance Metrics

| Metric | Value |
|--------|-------|
| **Corpus Size** | 27 documents |
| **ChromaDB Chunks** | 29 |
| **Graph Nodes** | 135 (27 docs, 12 equipment, 8 personnel, 78 failure modes, 10 regulatory) |
| **Graph Edges** | 641 |
| **Ingestion Time** | ~2 minutes (with caching) |
| **Query Latency** | 15-25s (includes LLM generation) |
| **Compliance Scan** | ~90s for 10 rules |
| **Graph Operations** | <100ms |

## Technical Highlights

### Rate Limiting & Caching
- Gemini free tier: 15 RPM (requests per minute)
- Conservative 6-second interval between API calls
- SHA256 file-hash based extraction cache
- Exponential backoff (15s → 120s) with jitter for 429 errors

### Graph-Augmented Retrieval Algorithm
1. Extract entities from query using regex + knowledge graph lookup
2. Get 1-hop neighborhood for each entity from NetworkX graph
3. Query ChromaDB with semantic search (top_k * 2)
4. Boost scores for chunks from graph-connected documents (0.7x distance)
5. Inject graph context (related equipment, documents) into LLM prompt
6. Generate answer with confidence assessment

### Compliance Detection
- LLM-as-judge pattern: prompt LLM with rule + document context
- Specialized checks for planted gaps (CR-002, CR-003, CR-006, CR-009, CR-010)
- Generic checker: keyword-based retrieval for other rules
- Structured JSON output: status, confidence, evidence, risk_level, recommendation

## Configuration

Key settings in `backend/config.py`:

```python
GEMINI_MODEL = "gemini-2.5-flash"
CHUNK_SIZE = 800          # tokens per chunk
CHUNK_OVERLAP = 100       # overlap between chunks
MIN_REQUEST_INTERVAL = 6.0  # seconds between API calls
MAX_RETRIES = 5
INITIAL_BACKOFF = 15.0    # seconds
MAX_BACKOFF = 120.0       # seconds
```

## Limitations & Future Work

**Current Limitations:**
- Single-tenant (no authentication)
- Gemini free tier rate limits
- Static graph visualization (no D3.js/force-directed)
- No real-time document updates
- English only

**Future Enhancements:**
- Multi-modal RAG (tables, flowcharts)
- Temporal reasoning (time-series failure analysis)
- Predictive maintenance alerts
- Graph neural networks for link prediction
- Multi-agent workflow orchestration
- Interactive graph visualization

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GEMINI_API_KEY not set" | Set environment variable: `set GEMINI_API_KEY=your-key` |
| "ChromaDB collection not found" | Run ingestion: `POST /api/ingest` |
| "graph.json not found" | Run ingestion: `python -m backend.ingest` |
| 429 Rate Limit Error | Wait 60s, reduce query frequency |
| Slow queries | Normal for free tier; uses caching for repeated queries |

## License

MIT License - Hackathon prototype, not for production use.

## Credits

Built with:
- **Google Gemini 2.5 Flash** - LLM reasoning and vision
- **ChromaDB** - Vector storage and semantic search
- **NetworkX** - Knowledge graph operations
- **FastAPI** - Backend REST API
- **React + Vite + Tailwind** - Frontend UI
- **pypdf** - PDF text extraction
- **pandas** - CSV/data processing
