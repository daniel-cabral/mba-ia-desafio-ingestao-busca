# Domain Pitfalls

**Domain:** RAG Pipeline — PDF Semantic Search CLI (LangChain + pgVector)
**Researched:** 2026-03-08
**Confidence:** MEDIUM (based on extensive domain knowledge; web verification unavailable)

---

## Critical Pitfalls

Mistakes that cause broken functionality, silent data corruption, or require rework.

### Pitfall 1: Embedding Dimension Mismatch Between Providers

**What goes wrong:** OpenAI `text-embedding-3-small` produces 1536-dimensional vectors. Google `models/embedding-001` produces 768-dimensional vectors. If you ingest a PDF with one provider and then switch to the other for search, the vector dimensions will not match and pgVector will either error out or return nonsensical similarity scores.

**Why it happens:** The project requires dual provider support (OpenAI and Gemini) switchable via env var. Developers often store vectors without tracking which embedding model produced them, then switch providers and wonder why search returns garbage.

**Consequences:** Silent retrieval failure -- queries return irrelevant chunks with no error message. Or hard crash if pgVector column dimension is fixed.

**Prevention:**
- Store the embedding provider name alongside the collection in pgVector. Use different `collection_name` values per provider (e.g., `"pdf_openai"` vs `"pdf_gemini"`).
- Alternatively, re-ingest the PDF whenever the provider changes. Since this is single-PDF, re-ingestion is cheap.
- Document clearly: switching `LLM_PROVIDER` env var requires re-running `ingest.py`.

**Detection:** Query returns chunks that have no semantic relation to the question. Or `ValueError` about dimension mismatch from pgVector.

**Phase:** Ingestion implementation (Phase 1). Must be designed correctly from the start.

---

### Pitfall 2: Using Deprecated `langchain_community.vectorstores.PGVector` Instead of `langchain_postgres.PGVector`

**What goes wrong:** The project includes `langchain-postgres==0.0.15` in requirements.txt, which is the correct modern package. However, many tutorials and examples online still reference `from langchain_community.vectorstores import PGVector`, which is the deprecated path. The old class uses a different connection string format (`postgresql+psycopg2://`) and has different APIs.

**Why it happens:** Most search results and tutorials predate the `langchain-postgres` package extraction. Developers copy-paste from outdated examples.

**Consequences:** Import errors, connection failures, or subtle behavioral differences. The old class and new class handle `collection_name`, connection strings, and document metadata differently.

**Prevention:**
- Use `from langchain_postgres import PGVector` (from `langchain-postgres` package).
- Use `psycopg` (v3) connection strings: `postgresql+psycopg://user:pass@host:port/db` -- note `psycopg` not `psycopg2`.
- The requirements already include both `psycopg` and `psycopg2-binary`. Use `psycopg` (v3) for the new package.

**Detection:** `DeprecationWarning` in console output. Connection errors mentioning driver mismatch.

**Phase:** Ingestion implementation (Phase 1). First line of code that touches pgVector.

---

### Pitfall 3: Not Creating the pgVector Extension Before First Use

**What goes wrong:** The `vector` extension must exist in PostgreSQL before LangChain can create embedding tables. Without it, table creation fails with `type "vector" does not exist`.

**Why it happens:** Developers start Postgres but forget the extension. Or the bootstrap container in docker-compose fails silently.

**Consequences:** Hard crash on first ingestion attempt.

**Prevention:** The current `docker-compose.yml` has a `bootstrap_vector_ext` service that creates the extension, which is good. However:
- The bootstrap service uses `restart: "no"` and depends on Postgres health check. If Postgres takes longer than expected to become healthy, bootstrap might not run.
- Add a defensive `CREATE EXTENSION IF NOT EXISTS vector;` in the Python ingestion code as well, via direct SQL before PGVector initialization.
- Verify the extension exists before proceeding: `SELECT * FROM pg_extension WHERE extname = 'vector';`

**Detection:** `UndefinedObject: type "vector" does not exist` error on first run.

**Phase:** Infrastructure/Setup (Phase 0). Verify before any ingestion code runs.

---

### Pitfall 4: PDF Text Extraction Producing Garbage from Scanned/Image PDFs

**What goes wrong:** `pypdf` (in requirements) extracts text from text-based PDFs only. If `document.pdf` is a scanned document (images of text), pypdf extracts empty strings or garbled characters. The chunks will contain no meaningful text, and the entire RAG pipeline silently produces useless results.

**Why it happens:** Developers assume all PDFs contain extractable text. Many academic/university documents are scans.

**Consequences:** Empty or near-empty chunks get embedded. Similarity search returns them (they are the only chunks available), and the LLM gets empty context, producing "Nao tenho informacoes" for every question.

**Prevention:**
- After extraction, validate that chunks contain meaningful text (not just whitespace/special characters).
- Log chunk count and average chunk length during ingestion. If average length is suspiciously low (< 50 chars), warn the user.
- For this assignment, verify `document.pdf` is text-based early.

**Detection:** Ingestion completes but produces very few chunks or chunks with < 50 characters average. All search queries return the out-of-context response.

**Phase:** Ingestion implementation (Phase 1). Add validation after text extraction.

---

### Pitfall 5: Connection String Format Wrong for `langchain-postgres`

**What goes wrong:** `langchain-postgres` 0.0.x requires a specific connection string format. Common mistakes:
- Using `postgresql://` instead of `postgresql+psycopg://` (missing driver specification).
- Using `psycopg2` driver with the new `langchain-postgres` package (it requires `psycopg` v3).
- Hardcoding connection string instead of reading from env, leading to failures when Docker host differs.

**Why it happens:** PostgreSQL connection strings vary by driver, and LangChain docs have historically been inconsistent about which format to use.

**Consequences:** `sqlalchemy.exc.NoSuchModuleError` or `ModuleNotFoundError` on startup. Or silent fallback to wrong driver.

**Prevention:**
- Connection string must be: `postgresql+psycopg://postgres:postgres@localhost:5432/rag`
- Store in `.env` file and load via `python-dotenv` (already in requirements).
- Test connection independently before passing to PGVector.

**Detection:** SQLAlchemy errors about missing dialect or driver on first run.

**Phase:** Ingestion implementation (Phase 1). First thing to configure correctly.

---

## Moderate Pitfalls

### Pitfall 6: Re-Ingesting Without Clearing Previous Embeddings

**What goes wrong:** Running `ingest.py` multiple times on the same PDF creates duplicate chunks in pgVector. Similarity search then returns the same passage multiple times (counted as different records), wasting the k=10 retrieval budget on duplicates.

**Why it happens:** `PGVector.from_documents()` appends by default. No built-in deduplication.

**Prevention:**
- Before ingestion, drop or clear the existing collection: use `PGVector.delete_collection()` or equivalent.
- Or use a deterministic collection name tied to the PDF filename, and drop-and-recreate on each ingestion.
- Log the number of chunks inserted so the user can verify.

**Detection:** Similarity search returns the same text passage multiple times with identical scores.

**Phase:** Ingestion implementation (Phase 1).

---

### Pitfall 7: Chunk Size in Characters vs. Tokens Confusion

**What goes wrong:** The assignment specifies `chunk_size=1000` and `chunk_overlap=150`. LangChain's `RecursiveCharacterTextSplitter` measures in **characters** by default. Some developers confuse this with tokens (1000 tokens is roughly 4000 characters), leading to chunks that are either too large or too small.

**Why it happens:** LLM context is measured in tokens, but the splitter default is characters. The naming is ambiguous.

**Consequences:** If using token-based splitting when character-based is expected (or vice versa), chunk sizes will be wrong. Too-large chunks waste context window; too-small chunks lose semantic coherence.

**Prevention:**
- Use `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)` -- this is character-based by default, which matches the assignment specification.
- Do NOT use `from_tiktoken_encoder()` or set `length_function` to a token counter.
- Verify by printing `len(chunks[0].page_content)` -- should be close to 1000.

**Detection:** First chunk length is wildly different from 1000.

**Phase:** Ingestion implementation (Phase 1).

---

### Pitfall 8: Prompt Template Variable Name Mismatch

**What goes wrong:** The existing prompt template in `search.py` uses `{contexto}` and `{pergunta}` (Portuguese). LangChain's `PromptTemplate` or `ChatPromptTemplate` expects exact variable name matches with the input keys. If the retrieval chain passes `context` and `question` (English) instead, the template renders with empty variables.

**Why it happens:** LangChain tutorials use English variable names. The assignment uses Portuguese. Copy-pasting chain setup code without adapting variable names.

**Consequences:** The LLM receives a prompt with empty `CONTEXTO` and `PERGUNTA DO USUARIO` sections. It will always respond with the out-of-context message, or hallucinate.

**Prevention:**
- When constructing the chain, explicitly map: retriever output to `contexto`, user question to `pergunta`.
- Test with a hardcoded question and print the formatted prompt before sending to LLM.
- Use `PromptTemplate(input_variables=["contexto", "pergunta"], template=PROMPT_TEMPLATE)` to get early validation.

**Detection:** LLM always returns the "Nao tenho informacoes" message even for questions clearly answered in the PDF.

**Phase:** Search/Chain implementation (Phase 2).

---

### Pitfall 9: Not Handling the `similarity_search_with_score` Return Format

**What goes wrong:** The assignment requires `similarity_search_with_score` which returns `List[Tuple[Document, float]]`, not `List[Document]`. If you feed this directly into a chain expecting documents, it will fail or produce garbled context.

**Why it happens:** `similarity_search()` and `similarity_search_with_score()` have different return types. Developers use the wrong one or don't unpack tuples.

**Consequences:** TypeError or the context fed to the LLM contains tuple representations like `(Document(...), 0.85)` instead of clean text.

**Prevention:**
- Unpack results: `docs = [doc for doc, score in results]`
- Or use the retriever interface (`as_retriever(search_kwargs={"k": 10})`) which handles this automatically -- but then you lose access to scores.
- If scores are needed for display, unpack explicitly and format context from documents only.

**Detection:** Context contains Python object representations instead of clean text. Or `TypeError: expected str, got tuple`.

**Phase:** Search implementation (Phase 2).

---

### Pitfall 10: Gemini API Key and Model Name Format Differences

**What goes wrong:** OpenAI uses `OPENAI_API_KEY` env var (auto-detected by LangChain). Gemini uses `GOOGLE_API_KEY` and has different model name formats. The LangChain wrappers for each provider have different initialization patterns:
- OpenAI: `ChatOpenAI(model="gpt-4.1-nano")`
- Gemini: `ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")`
- OpenAI embeddings: `OpenAIEmbeddings(model="text-embedding-3-small")`
- Gemini embeddings: `GoogleGenerativeAIEmbeddings(model="models/embedding-001")`

Note the `models/` prefix required for Gemini embeddings but not for the chat model.

**Why it happens:** Each provider has its own conventions. Easy to forget the `models/` prefix or use the wrong env var name.

**Consequences:** Authentication errors or model-not-found errors that are cryptic.

**Prevention:**
- Create a provider abstraction: a function that returns `(embeddings, llm)` tuple based on env var.
- Validate the API key env var exists before initializing.
- Use the exact model strings from the assignment spec.

**Detection:** `AuthenticationError` or `NotFoundError` on first API call.

**Phase:** Search/Chain implementation (Phase 2). Provider switching logic.

---

## Minor Pitfalls

### Pitfall 11: Docker Postgres Not Running When Scripts Execute

**What goes wrong:** Running `python src/ingest.py` without first starting Docker Compose. Connection refused.

**Prevention:** Add a connection test at the start of `ingest.py` with a clear error message: "PostgreSQL is not running. Start it with: docker-compose up -d"

**Phase:** Setup/Documentation (Phase 0).

---

### Pitfall 12: `.env` File Missing or Not Loaded

**What goes wrong:** API keys and database URL not available. Scripts fail with `None` values.

**Prevention:** Validate all required env vars at startup. Print which vars are missing. Provide a `.env.example` file.

**Phase:** Setup (Phase 0).

---

### Pitfall 13: Chat Loop Not Handling Exit Gracefully

**What goes wrong:** `chat.py` interactive loop does not handle Ctrl+C, "exit", or "sair" commands. User gets stuck or sees ugly traceback.

**Prevention:** Wrap the loop in try/except for `KeyboardInterrupt` and `EOFError`. Check for exit keywords.

**Phase:** Chat implementation (Phase 3).

---

### Pitfall 14: Large PDF Causes Slow Ingestion Without Feedback

**What goes wrong:** Embedding API calls for hundreds of chunks take minutes. User thinks the script is frozen.

**Prevention:** Print progress: "Embedding chunk X of Y..." or use `tqdm` (already in requirements).

**Phase:** Ingestion implementation (Phase 1).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 0: Setup | Extension not created, Docker not running, env vars missing | Defensive checks, clear error messages |
| Phase 1: Ingestion | Dimension mismatch across providers, duplicate chunks on re-run, wrong PGVector import, connection string format | Use `langchain_postgres`, clear collection before re-ingest, provider-scoped collections |
| Phase 2: Search/Chain | Prompt variable names (Portuguese vs English), `similarity_search_with_score` tuple handling, Gemini model name format | Explicit variable mapping, tuple unpacking, provider abstraction |
| Phase 3: Chat Loop | No graceful exit, no user feedback | KeyboardInterrupt handling, progress messages |
| Cross-cutting | Switching providers without re-ingesting | Document the requirement, warn user, or auto-re-ingest |

## Sources

- LangChain documentation for `langchain-postgres` package (training data, MEDIUM confidence)
- pgVector PostgreSQL extension documentation (training data, MEDIUM confidence)
- OpenAI and Google embedding model specifications (training data, MEDIUM confidence)
- Direct inspection of project `requirements.txt`, `docker-compose.yml`, and stub source files (HIGH confidence)

**Note:** Web search and Context7 were unavailable during this research session. All findings are based on domain expertise with LangChain, pgVector, and RAG pipelines. Confidence is MEDIUM overall -- the pitfalls described are well-established in the community but specific version behaviors of `langchain-postgres==0.0.15` should be verified against current documentation.
