
# Medical RAG System for CIM-10 Coding

A retrieval-augmented generation system that suggests CIM-10 medical codes from clinical descriptions, using the CoCoA reference document.

**Time investment:** half a day for MVP  
**Current status:** Functional prototype

---

## What It Does

Input: "dyspnée à l'effort"  
Output:
- Relevant CIM-10 codes (like : R06.0, J44.1, etc.)
- Clinical explanations
- CoCoA coding rules (exclusions, inclusions, instructions)
- Confidence scores

Basically a smart search for medical codes that understands clinical context.


---

## Screenshots

See the [application walkthrough](docs/screenshots.md) for UI screenshots and usage examples.

---

## Architecture

```
src/
├── domain/          # Business entities (codes, chunks, suggestions)
├── application/     # Core logic (retrieval, query processing, RAG)
├── infrastructure/  # External services (OpenAI, ChromaDB, PDF)
└── api/             # FastAPI REST endpoints
```

Loosely based on hexagonal architecture. Not pure DDD, Lacks : 
- Aggregates: grouping related domain objects with consistency rules.

- Value Objects: small, immutable data types with domain meaning.

- Domain Services: pure business logic separate from infrastructure.

---

## How It Works

### 1. PDF Processing
The CoCoA PDF has 1040 pages. It is split into:
- Pages 1-30: General coding rules (1 big chunk)
- Pages 31+: Individual codes (about 17,500 chunks)

Each code chunk contains: code ID, label, exclusions, inclusions, P-R-A priority, instructions.

**Chunking strategy:** Keep each code self-contained. Small chunks for a theoritical better retrieval precision.

**Known issue:** 100 chunks (~0.5%) failed to embed due to token limits. Acceptable loss for now.

### 2. Vector Store
ChromaDB stores 17,411 document chunks with:
- Text content
- 1536-dimensional embeddings
- Metadata (code, label, chapter, priority, flags)

**Why ChromaDB:** No server setup, persistent storage, fast enough for 17k docs. Would need Pinecone/Weaviate for 100k+ scale.

### 3. Hybrid Retrieval
Two search methods combined:

**Semantic search (70%):** Query → embedding → cosine similarity. Good for synonyms and context.

**Keyword search (30%):** BM25 algorithm. Good for exact matches and specific terms.

Results merged by weighted score.

**Why both:** Semantic alone misses exact code matches. Keyword alone can't handle "dyspnée" → "insuffisance respiratoire". Together they work.

### 4. LLM Re-ranking
Top 10 hybrid results → GPT-4o-mini re-ranks to top 5.

**Why:** Vector similarity ≠ clinical relevance. LLM understands CoCoA exclusion rules and catches edge cases.

### 5. Explanation Generation
Re-ranked codes + original query → GPT-4o-mini → structured explanations.

Includes fallback: if LLM fails, return codes with generic explanations. System stays functional.

---

## File Breakdown

### Domain Layer
`domain/entities.py` - Data structures only. No logic.
- `CIMCode`: Medical code representation
- `DocumentChunk`: Piece of CoCoA doc
- `CodeSuggestion`: Single suggestion with explanation
- `QueryResult`: Complete response

### Application Layer
`application/query_processor.py` - Query cleanup and expansion
- Normalize text (lowercase, strip chars)
- Extract mentioned codes
- Add synonyms (dyspnée → essoufflement, difficulté respiratoire)

`application/retriever.py` - All retrieval logic
- `retrieve_semantic()`: Vector search
- `retrieve_keyword()`: BM25 search  
- `retrieve_hybrid()`: Merge both with weights

BM25 index built on first use (~2 seconds).

`application/rag_pipeline.py` - Main orchestrator
1. Process query
2. Retrieve candidates
3. Re-rank with LLM
4. Generate explanations
5. Return result

### Infrastructure Layer
`infrastructure/pdf_processor.py` - PDF parsing
- PyMuPDF for text extraction
- Regex for code detection
- Two-pass: line-based first, block-based fallback for complex layouts

Line parsing is fast but fragile. Block parsing handles multi-column but slower. Used both.

`infrastructure/embeddings.py` - OpenAI embedding wrapper
- text-embedding-3-small (1536 dims)
- Batch size: 100 texts per call
- Truncates >30k chars
- Returns zeros on failure (needs improvement)

`infrastructure/vector_store.py` - ChromaDB wrapper
- Handles duplicate IDs
- Cleans metadata for ChromaDB
- Skips zero embeddings
- Search and lookup methods

`infrastructure/llm_client.py` - GPT-4o-mini integration
- JSON mode for new models, text parsing for old
- Re-ranking and explanation generation
- Extracts JSON from markdown if needed
- Graceful error handling

`infrastructure/auth.py` - JWT auth
- Hashed passwords
- Users: admin/admin123
- 60-minute token expiry

### API Layer
`api/main.py` - FastAPI setup with CORS

`api/routes.py` - Endpoints
- `POST /suggest-codes`: Main query (auth required)
- `POST /lookup-code`: Direct lookup (auth required)
- `GET /health`: Status check (public)

`api/auth_routes.py` - Auth
- `POST /login`: Get JWT
- `POST /logout`: Client-side

`api/schema.py` - Pydantic models for validation

---

## Setup

### Installation
```bash
cd medical-rag-system
python -m venv venv
source venv/Scripts/Activate #for Windows.

pip install -r requirements.txt

```
- Create data folder at the root and place the pdf inside
- Create .env file with correct env variables

### Build Vector Store (One-Time)
```bash
python scripts/build_vector_store.py
```
Takes few minutes. Creates `data/chroma_db/` with 17k embeddings.  
Cost: about $0.50 in OpenAI calls.

### Run
```bash
python -m src.api.main
```
then

```bash
streamlit run app.py
```
Runs on http://localhost:8501

### Test
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Query (use token from login)
curl -X POST http://localhost:8000/api/v1/suggest-codes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query":"dyspnee a effort","top_k":3}'
```

---

## Design Decisions

### Hybrid Search
Combined semantic + keyword because:
- Pure semantic misses exact matches
- Pure keyword struggles with synonyms
- Medical coding needs both
- 70/30 weight found through testing

Trade-off: More complexity, BM25 adds startup time.

### LLM Re-ranking
Re-rank top 10 → top 5 because:
- Vector similarity ≠ clinical correctness
- CoCoA has complex exclusion rules
- LLM reasons about context better
- Small cost for quality gain

Trade-off: 5-10s latency, costs money.

### No Caching for now

To be added later

### ChromaDB vs Faiss
- ChromaDB: managed, persistent, easy metadata filtering  
- FAISS: pure in-memory, fast for large datasets, but no built-in metadata  
- ChromaDB integrates well with Python and RAG pipelines  
- FAISS requires more custom code for persistence and updates  

Trade-off: ChromaDB slightly slower than FAISS for huge corpus, but simpler in my case and with built in metadata support.

### No Evaluation Metrics for now
Skipped formal eval because:
- No ground truth dataset
- Time constraints : half a day working mvp
- Manual testing showed decent results

Trade-off: No quantitative quality measure.

---

## Known Issues

1. **Performance:** 15-20s per query (mostly LLM), no rate limiting
2. **Cost:** ~$0.003 per query
3. **Error Handling:** Silent failures in embedding generation
4. **Testing:** No automated tests
5. **Monitoring:** No metrics or logging
6. **Scalability:** Global state in routes, no pooling. Critical.
7. **BM25:** Built on first request (2-3s delay)
8. **Embeddings:** 100 chunks have zeros
9. **No Cache:** Every query hits OpenAI

---

## Improvements Needed

### Critical (Before Production)
- Fix auth: proper bcrypt with hashing (Fixed)
- Add logging: replace all `print()`
- Error handling: retry logic, no silent fails
- Tests: at least unit tests
- Rate limiting: prevent abuse
- Monitoring: track times, errors, costs

### Important (Performance)
- Caching: Redis for repeated queries. (To be fixed)
- Async LLM: parallel re-rank + suggestions
- Preload BM25: build at startup
- Connection pooling: ChromaDB and OpenAI
- Evaluation: test set, measure P@5/R@5

### Nice to Have
- Response streaming
- Request deduplication
- Fine-tune embeddings on medical data
- Multi-language support
- User feedback loop

### Architecture
- Complete hexagonal pattern
- Proper DDD (value objects, services)
- Event sourcing for analytics
- CQRS for read/write separation

---

## Performance

**Query time breakdown:**
- Retrieval: 1-2s
- Re-ranking: 5-10s
- Explanations: 5-10s
- Total: 15-20s

**Bottleneck:** Sequential LLM calls. Could be less with async.

**Cost per 1000 queries:**
- Re-ranking: $1.50
- Explanations: $1.50
- Total: ~$3

**Storage:**
- Vector store: 0.5GB
- PDF: 7MB

---

## Stack

- Python 3.10
- FastAPI
- Streamlit
- ChromaDB
- OpenAI GPT-4o-mini
- OpenAI text-embedding-3-small
- PyMuPDF
- rank-bm25
- JWT (python-jose)
- Pydantic

---

## Notes

Built for within a half day timeframe.
The code works but isn't production-ready. It's a proof of concept.


