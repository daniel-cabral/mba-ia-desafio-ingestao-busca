# Requirements: PDF Semantic Search (RAG Pipeline)

**Defined:** 2026-03-08
**Core Value:** Users can ask natural language questions about a PDF and get accurate answers based exclusively on the document's content

## v1 Requirements

### Ingestion

- [x] **INGE-01**: User can ingest a PDF by running `python src/ingest.py <path_to_pdf>` (defaults to `document.pdf` if no argument)
- [x] **INGE-02**: PDF is split into chunks of 1000 characters with 150-character overlap using RecursiveCharacterTextSplitter
- [x] **INGE-03**: Each chunk is converted to an embedding vector using the configured provider
- [x] **INGE-04**: Vectors are stored in PostgreSQL with pgVector extension via langchain-postgres PGVector
- [x] **INGE-05**: Ingestion shows progress feedback via tqdm or rich progress bar

### Retrieval

- [ ] **RETR-01**: User question is vectorized using the same embedding model used during ingestion
- [ ] **RETR-02**: Top 10 most similar chunks are retrieved via similarity_search_with_score (k=10)
- [ ] **RETR-03**: Retrieved context is injected into the exact prompt template defined in the assignment

### Response

- [ ] **RESP-01**: Prompt with context and question is sent to configured LLM
- [ ] **RESP-02**: LLM responds based only on provided context
- [ ] **RESP-03**: Out-of-context questions receive standard refusal message in Portuguese

### CLI Interface

- [ ] **CLI-01**: Interactive chat loop that accepts questions and displays answers
- [ ] **CLI-02**: Rich terminal formatting — colors, panels, styled text using `rich` library
- [ ] **CLI-03**: Graceful exit on Ctrl+C with friendly goodbye message
- [ ] **CLI-04**: Clear error messages on startup failures (missing DB, missing env vars)

### Provider Support

- [ ] **PROV-01**: OpenAI provider works end-to-end (text-embedding-3-small + gpt-5-nano)
- [ ] **PROV-02**: Gemini provider works end-to-end (models/embedding-001 + gemini-2.5-flash-lite)
- [ ] **PROV-03**: LM Studio provider works end-to-end (user-chosen models via OpenAI-compatible API at configurable base URL)
- [ ] **PROV-04**: Provider is selected via environment variable (LLM_PROVIDER=openai|gemini|lmstudio)
- [ ] **PROV-05**: Switching providers requires re-ingestion (different embedding dimensions)

### Documentation

- [ ] **DOCS-01**: Code contains educational inline comments explaining RAG concepts, LangChain usage, and design choices
- [ ] **DOCS-02**: Learning guide at docs/GUIDE.md walks through the architecture and explains each component
- [ ] **DOCS-03**: README.md with clear execution instructions

## v2 Requirements

### Enhanced Features

- **ENH-01**: Conversation memory (multi-turn context)
- **ENH-02**: Multi-document search (multiple PDFs)
- **ENH-03**: Web UI interface

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web UI | Assignment requires CLI only; rich terminal is sufficient |
| Conversation memory | Each question is independent per assignment spec |
| Multi-document search | Single PDF at a time per assignment spec |
| Authentication | Local tool only |
| Production deployment | Runs locally with Docker |
| Custom prompt template | Assignment specifies exact template |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGE-01 | Phase 1 | Complete |
| INGE-02 | Phase 1 | Complete |
| INGE-03 | Phase 1 | Complete |
| INGE-04 | Phase 1 | Complete |
| INGE-05 | Phase 1 | Complete |
| RETR-01 | Phase 2 | Pending |
| RETR-02 | Phase 2 | Pending |
| RETR-03 | Phase 2 | Pending |
| RESP-01 | Phase 2 | Pending |
| RESP-02 | Phase 2 | Pending |
| RESP-03 | Phase 2 | Pending |
| CLI-01 | Phase 3 | Pending |
| CLI-02 | Phase 3 | Pending |
| CLI-03 | Phase 3 | Pending |
| CLI-04 | Phase 3 | Pending |
| PROV-01 | Phase 4 | Pending |
| PROV-02 | Phase 4 | Pending |
| PROV-03 | Phase 4 | Pending |
| PROV-04 | Phase 4 | Pending |
| PROV-05 | Phase 4 | Pending |
| DOCS-01 | Phase 5 | Pending |
| DOCS-02 | Phase 5 | Pending |
| DOCS-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 after roadmap creation*
