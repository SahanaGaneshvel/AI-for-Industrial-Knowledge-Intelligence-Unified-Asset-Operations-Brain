# AssetBrain Demo Guide

## Pre-Demo Setup (5 minutes)

### 1. Environment Check
```bash
# Verify backend health
python scripts/test_backend.py

# Should show:
# ✓ Module Imports: PASS
# ✓ Data Files: PASS
# ✓ ChromaDB: PASS (29 chunks)
# ✓ Knowledge Graph: PASS (135 nodes, 641 edges)
# ✓ API Key: PASS
```

### 2. Start Services
```bash
# Terminal 1: Start backend
python scripts\start_backend.bat
# OR: uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start frontend
python scripts\start_frontend.bat
# OR: cd frontend && npm run dev
```

### 3. Verify URLs
- Backend API: http://localhost:8000/api/health
- Frontend UI: http://localhost:5173

---

## Demo Script (10-12 minutes)

### **Opening (30 seconds)**
"AssetBrain is an intelligent knowledge platform for industrial operations. It ingests maintenance records, incident reports, and procedures to automatically discover patterns, answer questions, and detect compliance gaps."

---

### **PART 1: Cross-Document Pattern Discovery (4 minutes)**

**Navigate to:** Copilot View (main page)

**Demo Question 1: The Flagship Question**
```
What is the recurring failure mode on P-101A and what pattern precedes it?
```

**While it processes (~15-20s), explain:**
- "The copilot is searching across 27 documents in the corpus"
- "It's using graph-augmented retrieval - first finding entities mentioned in the question (P-101A), then boosting documents connected to those entities in the knowledge graph"
- "The answer requires synthesizing evidence from 7+ different sources"

**When answer appears, highlight:**
1. **Answer Synthesis**:
   - "Notice it identified 4 mechanical seal failures between March 2023 and April 2024"
   - "It discovered the pattern: lubricant change to EconoLube Standard 320"
   - "This correlation wasn't stated in any single document - it had to connect work orders, incident reports, AND the lubrication standard"

2. **Source Citations** (scroll down):
   - "7 sources cited: work orders, incident reports, and LUB-STD-001.pdf"
   - "Some are marked 'Graph-Linked' - these were prioritized because the knowledge graph shows they're connected to P-101A"

3. **Confidence & Graph Context**:
   - "HIGH confidence because multiple sources corroborate"
   - "Graph entities used: P-101A and several failure mode nodes"

**Key Insight to Emphasize:**
> "No single document says 'EconoLube causes seal failures on P-101A.' The copilot had to notice that lubricant changes in work orders occurred 2 months before seal failures, then find the lubrication standard warning about incompatibility. This is true cross-document reasoning."

---

### **PART 2: Compliance Gap Detection (3 minutes)**

**Navigate to:** Compliance View

**Click:** "Run Scan" button

**While it scans (~90s), explain:**
- "We've defined 10 regulatory compliance rules based on Indian standards (OISD, IS, PESO)"
- "The system is searching the corpus for evidence of compliance or violations"
- "It uses LLM-as-judge to assess each rule"

**When results appear, highlight:**

1. **Summary Dashboard**:
   - "3 non-compliant rules found"
   - "2 critical gaps, 1 high-risk gap"

2. **Gap 1: CR-003 - LOTO Zero Energy Verification (CRITICAL)**
   - "The LOTO procedure SOP-LOTO-001 is missing the zero energy verification step"
   - "Regulatory requirement: IS 14489:2018 Clause 6.2.3"
   - "Risk: Workers could be injured if equipment unexpectedly starts"

3. **Gap 2: CR-006 - Approved Lubricants (CRITICAL)**
   - "This ties back to our first demo!"
   - "EconoLube Standard 320 was used but is NOT approved per the lubrication standard"
   - "The compliance scanner independently discovered the same pattern the copilot found"

4. **Gap 3: CR-009 - Recurring Failure RCA (HIGH)**
   - "P-101A has >3 failures in 18 months, triggering requirement for formal Root Cause Analysis"
   - "No RCA documentation found in corpus"

**Key Insight:**
> "Notice how the compliance gaps connect to the operational patterns. The unapproved lubricant (compliance gap) is causing recurring failures (another compliance gap) on P-101A. The system is finding these connections automatically."

---

### **PART 3: Knowledge Graph Exploration (2 minutes)**

**Navigate to:** Knowledge Graph View

**Show Stats:**
- "135 nodes total: 27 documents, 12 equipment tags, 8 personnel, failure modes, etc."
- "641 edges connecting everything"

**Search for:** `P-101A`

**Click "Search"**

**When results appear, highlight:**
1. **Connected Nodes**:
   - "11 documents mention P-101A"
   - "Connected to personnel: Priya Sharma, Rajesh Kumar (technicians who worked on it)"
   - "Connected to failure modes: mechanical seal failure, catastrophic seal failure"

2. **Edges**:
   - "MENTIONS relationships to all work orders and incidents"
   - "FAILED_WITH relationships to failure modes"
   - "PERFORMED_BY relationships to personnel"

**Try another search:** `V-310`

**Highlight:**
- "V-310 appears in inspection reports and the P&ID diagram"
- "This is the vessel with the unresolved CUI finding (Compliance Gap #2)"

**Key Insight:**
> "The graph lets us navigate the knowledge network. Click any node to explore further - it's like a LinkedIn for industrial assets and events."

---

### **PART 4: Data Ingestion (1 minute - optional)**

**Navigate to:** Data Ingestion View

**Explain quickly:**
- "27 documents already ingested"
- "Can upload new documents - they'll be automatically processed, entities extracted, graph updated"
- "LLM extractions are cached by file hash - re-ingestion is fast"

**Process Overview:**
- Extract text (PDFs, CSVs, images via OCR)
- Gemini extracts entities, equipment tags, personnel
- Chunk into 800 tokens with 100 overlap
- Store in ChromaDB vector store
- Update knowledge graph

---

### **Closing (1 minute)**

**Summary:**
"In 10 minutes we've seen:
1. **Cross-document pattern discovery** - finding a lubricant incompatibility that no single document stated
2. **Automated compliance detection** - identifying 3 regulatory gaps with evidence and recommendations
3. **Knowledge graph navigation** - exploring the entity relationship network

This prototype demonstrates how graph-augmented RAG can go beyond simple search to synthesize insights, detect patterns, and ensure compliance across thousands of industrial documents."

**Technical Highlights:**
- "Graph-augmented retrieval: combines vector search + knowledge graph traversal"
- "Planted evidence chains: the P-101A pattern required synthesizing 7+ sources"
- "LLM caching & rate limiting: works with Gemini free tier (15 RPM)"

**Questions?**

---

## Troubleshooting

### Backend Issues
- **"GEMINI_API_KEY not set"**: Set with `set GEMINI_API_KEY=your-key`
- **Rate limit errors**: Increase `MIN_REQUEST_INTERVAL` in `backend/config.py`
- **ChromaDB errors**: Delete `data/chromadb` and re-run ingestion

### Frontend Issues
- **"Cannot connect to API"**: Ensure backend is running on port 8000
- **Blank screen**: Check browser console for errors, ensure `npm install` completed

### Demo Failures
- **Copilot not finding pattern**: Check that ingestion completed (29 chunks in ChromaDB)
- **Compliance scan finds no gaps**: Verify `data/compliance_rules.json` exists
- **Graph search returns nothing**: Ensure `data/graph.json` exists with 135 nodes

---

## Quick Validation Commands

```bash
# Check ChromaDB
python -c "import chromadb; c = chromadb.PersistentClient(path='data/chromadb'); print(c.get_collection('assetbrain_docs').count())"
# Should output: 29

# Check Knowledge Graph
python -c "from backend.ingest import KnowledgeGraph; kg = KnowledgeGraph.load(); print(f'{kg.graph.number_of_nodes()} nodes, {kg.graph.number_of_edges()} edges')"
# Should output: 135 nodes, 641 edges

# Test Copilot Query
python -c "from backend.copilot import query_with_rag; r = query_with_rag('What equipment has seal failures?'); print(r['answer'][:200])"
```

---

## Time Estimates

| Activity | Time |
|----------|------|
| Setup & start services | 5 min |
| Copilot demo | 4 min |
| Compliance demo | 3 min |
| Graph demo | 2 min |
| Q&A | 3 min |
| **Total** | **15-17 min** |

Adjust based on audience technical depth and questions.
