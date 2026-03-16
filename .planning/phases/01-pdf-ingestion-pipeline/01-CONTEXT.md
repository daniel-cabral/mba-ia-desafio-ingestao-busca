# Phase 1: PDF Ingestion Pipeline - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Load a PDF file, split it into chunks, generate embeddings, and store them in PostgreSQL/pgVector. This is a one-time data preparation step run via CLI. The search, chat loop, and multi-provider support are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Re-ingestion behavior
- Clear existing collection and re-create from scratch on every run
- Prompt user for confirmation before clearing: "Collection exists. Clear and re-ingest? (y/n)"
- No --force flag — always ask (this is a manual tool)
- Simple "Done" message after completion, no detailed summary of changes

### Progress & output
- Rich progress bar (using `rich` library) during chunk processing
- Progress bar displays: PDF filename, chunk count (e.g. 12/38), elapsed time
- Simple "Done" message when ingestion finishes — no stats summary

### Error handling
- Validate environment variables upfront before starting any work (OPENAI_API_KEY, DATABASE_URL)
- If PDF file doesn't exist or is invalid: clear error message + exit with non-zero code
- If database is unreachable: retry 3 times with delay, then fail with clear message ("Is Docker running?")
- Errors use rich formatting — red panels with error icon, consistent with progress bar style

### Collection naming
- Auto-generate collection name from PDF filename (e.g. `document_pdf` from `document.pdf`)
- PG_VECTOR_COLLECTION_NAME env var available as optional override (Claude's discretion on implementation)
- Chat.py will receive PDF name as CLI argument to find the right collection (consistency across ingest/search)

### Claude's Discretion
- Exact rich progress bar layout and styling
- Retry timing/backoff strategy for DB connection
- How collection name is sanitized from PDF filename
- Whether PG_VECTOR_COLLECTION_NAME env var is kept as override or removed

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ingest.py`: Stub with `ingest_pdf()` function and `PDF_PATH` env var loading via dotenv
- `docker-compose.yml`: PostgreSQL 17 + pgVector fully configured with healthcheck and auto-bootstrap of vector extension
- `.env.example`: Template with OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, DATABASE_URL, PG_VECTOR_COLLECTION_NAME, PDF_PATH
- `requirements.txt`: All dependencies pinned (langchain 0.3.27, langchain-postgres 0.0.15, pypdf 6.0.0, rich not yet added)

### Established Patterns
- Environment variables loaded via `python-dotenv` (`load_dotenv()`)
- Connection string format: `postgresql+psycopg://postgres:postgres@localhost:5432/rag`
- Use `langchain_postgres.PGVector` (NOT deprecated `langchain_community.vectorstores.PGVector`)

### Integration Points
- `src/search.py` will import from the same pgVector collection — collection naming must be consistent
- `src/chat.py` will pass PDF name as argument — ingest.py sets the pattern for CLI argument handling
- `rich` library needs to be added to requirements.txt

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Assignment constrains chunk size (1000), overlap (150), and embedding model (text-embedding-3-small for OpenAI).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-pdf-ingestion-pipeline*
*Context gathered: 2026-03-08*
