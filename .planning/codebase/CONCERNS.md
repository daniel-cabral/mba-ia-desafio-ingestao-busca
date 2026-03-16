# Codebase Concerns

**Analysis Date:** 2026-03-08

## Tech Debt

**All core functions are stub implementations (pass):**
- Issue: The three main source files contain only stub/placeholder functions with `pass` bodies. None of the required functionality (PDF ingestion, vector search, chat CLI) is implemented.
- Files: `src/ingest.py`, `src/search.py`, `src/chat.py`
- Impact: The application does nothing. The entire assignment (PDF ingestion, embedding storage, semantic search, CLI chat) remains unbuilt.
- Fix approach: Implement each module per the assignment requirements in `docs/instrucoes.md`. See detailed gaps below.

**No project tooling or virtual environment management:**
- Issue: No `pyproject.toml`, `setup.py`, or `setup.cfg` exists. The project relies solely on a flat `requirements.txt` with pinned transitive dependencies (75 packages), making it hard to distinguish direct vs transitive deps.
- Files: `requirements.txt`
- Impact: Dependency management is fragile. Upgrading one package requires manually resolving the entire dependency tree. No way to distinguish the ~10 direct dependencies from 65 transitive ones.
- Fix approach: Create a `pyproject.toml` or at minimum a separate `requirements-direct.txt` listing only direct dependencies (langchain, langchain-postgres, langchain-openai, langchain-google-genai, pypdf, python-dotenv, pgvector, psycopg2-binary).

**README is empty placeholder:**
- Issue: README contains only the project title and a placeholder line. No setup instructions, usage guide, or architecture description.
- Files: `README.md`
- Impact: Assignment requires "README com instrucoes claras de execucao do projeto." This is an incomplete deliverable.
- Fix approach: Document prerequisites (Docker, Python 3.x, venv), setup steps, env var configuration, and execution order.

## Known Bugs

**`search_prompt()` returns None implicitly:**
- Symptoms: `chat.py` calls `search_prompt()` which always returns `None` (stub). The `if not chain` guard catches this and prints an error, but the function signature accepts `question=None` as a parameter that is never used.
- Files: `src/search.py` (line 28-29), `src/chat.py` (line 4-7)
- Trigger: Running `python src/chat.py` always prints the error message and exits.
- Workaround: None -- implementation is required.

**`ingest_pdf()` silently does nothing:**
- Symptoms: Running `python src/ingest.py` exits with code 0 but performs no ingestion.
- Files: `src/ingest.py` (line 8-9)
- Trigger: Running the ingest script.
- Workaround: None -- implementation is required.

## Security Considerations

**Hardcoded database credentials in docker-compose.yml:**
- Risk: PostgreSQL user/password (`postgres`/`postgres`) are hardcoded in the compose file. If this pattern carries into the application code, credentials could leak.
- Files: `docker-compose.yml` (lines 5-7)
- Current mitigation: `.env` is in `.gitignore`, and `.env.example` uses empty values for `DATABASE_URL`. The compose file itself is committed with default credentials.
- Recommendations: For a course assignment this is acceptable, but the `DATABASE_URL` in `.env` should use these credentials, and the compose file should reference environment variables or a `.env` file rather than hardcoding.

**Hardcoded password in bootstrap service command:**
- Risk: The `bootstrap_vector_ext` service has `PGPASSWORD=postgres` directly in the command string.
- Files: `docker-compose.yml` (line 27)
- Current mitigation: None.
- Recommendations: Use environment variables or a `.pgpass` approach instead.

**No input sanitization planned for CLI:**
- Risk: The chat CLI will accept raw user input to construct prompts. While this is a local CLI tool (not web-facing), prompt injection could cause the LLM to ignore context restrictions.
- Files: `src/search.py` (prompt template), `src/chat.py`
- Current mitigation: The prompt template in `src/search.py` includes strong grounding rules ("Responda somente com base no CONTEXTO").
- Recommendations: Consider basic input length limits and sanitization when implementing the CLI loop.

## Performance Bottlenecks

**No connection pooling configured:**
- Problem: When implementing the database interactions, there is no connection pool setup. Each query could open a new connection.
- Files: `src/ingest.py`, `src/search.py`
- Cause: Implementation not yet written, but `requirements.txt` includes `psycopg-pool` which should be used.
- Improvement path: Use `langchain_postgres.PGVector` which handles connection pooling internally, or explicitly configure `psycopg_pool.ConnectionPool`.

**Full PDF re-ingestion on every run:**
- Problem: The `ingest.py` stub has no mechanism to detect whether the PDF has already been ingested.
- Files: `src/ingest.py`
- Cause: No idempotency check planned.
- Improvement path: Implement a check (e.g., hash the PDF, store metadata) to skip re-ingestion if the document is unchanged. Alternatively, clear and re-create the collection on each run.

## Fragile Areas

**Environment variable loading with no validation:**
- Files: `src/ingest.py` (lines 1-6)
- Why fragile: `PDF_PATH = os.getenv("PDF_PATH")` returns `None` if not set. No validation or error message. The same pattern will likely be repeated for `DATABASE_URL`, `OPENAI_API_KEY`, etc.
- Safe modification: Add validation immediately after loading env vars. Raise clear errors if required variables are missing.
- Test coverage: No tests exist.

**Import path assumes execution from project root:**
- Files: `src/chat.py` (line 1: `from search import search_prompt`)
- Why fragile: This relative import works only if `python` is run from the `src/` directory or `src/` is on `PYTHONPATH`. Running `python src/chat.py` from the project root will fail with `ModuleNotFoundError`.
- Safe modification: Use relative imports (`from .search import search_prompt`) with a package `__init__.py`, or adjust `sys.path` in `chat.py`.
- Test coverage: No tests exist.

**No `__init__.py` in `src/`:**
- Files: `src/` directory
- Why fragile: Without `__init__.py`, `src/` is not a proper Python package. Imports between modules are fragile and depend on the working directory.
- Safe modification: Add `src/__init__.py` or restructure to use proper package imports.
- Test coverage: No tests exist.

## Scaling Limits

**Single PDF design:**
- Current capacity: The architecture assumes a single `document.pdf` file.
- Limit: No support for multiple documents or incremental ingestion.
- Scaling path: Accept a directory of PDFs, track ingested documents, support adding new documents without re-processing existing ones.

**In-memory chunk processing:**
- Current capacity: Entire PDF is loaded and chunked in memory.
- Limit: Very large PDFs (hundreds of MB) could exhaust memory.
- Scaling path: Use streaming/chunked PDF reading if needed, though for the assignment scope this is unlikely to be an issue.

## Dependencies at Risk

**langchain-postgres v0.0.15 (pre-release):**
- Risk: Version `0.0.15` indicates early/unstable release. API may change significantly.
- Impact: Upgrading could break ingestion and search code.
- Migration plan: Pin the version (already done in `requirements.txt`) and monitor for stable releases.

**Dual embedding provider dependencies:**
- Risk: Both `langchain-openai` and `langchain-google-genai` are included, but `.env.example` has keys for both providers. It is unclear which provider the implementation should use.
- Impact: Confusion during implementation; unused dependencies bloat the project.
- Migration plan: Choose one provider (per assignment instructions, either OpenAI or Gemini) and remove the unused dependency, or support both with a configuration switch.

## Missing Critical Features

**PDF ingestion pipeline:**
- Problem: `src/ingest.py` has no implementation. Must load PDF with `PyPDFLoader`, split with `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)`, generate embeddings, and store in PGVector.
- Blocks: No data in the database means search and chat cannot function.

**Semantic search:**
- Problem: `src/search.py` has only a prompt template but no search implementation. Must connect to PGVector, run `similarity_search_with_score(query, k=10)`, format results into the prompt template, and call the LLM.
- Blocks: Chat cannot produce answers without search.

**CLI chat loop:**
- Problem: `src/chat.py` has no interactive loop. Must implement a REPL that accepts user questions, calls `search_prompt()`, and displays answers.
- Blocks: No user interaction possible.

## Test Coverage Gaps

**No tests exist anywhere in the codebase:**
- What's not tested: Everything -- ingestion, search, chat, prompt formatting, environment loading.
- Files: No test files found (`*test*`, `*spec*`).
- Risk: Any implementation bugs will go unnoticed. Refactoring is risky without regression protection.
- Priority: Medium (assignment does not explicitly require tests, but they would catch integration issues with PGVector and LLM APIs).

---

*Concerns audit: 2026-03-08*
