# Architecture

**Analysis Date:** 2026-03-08

## Pattern Overview

**Overall:** RAG (Retrieval-Augmented Generation) Pipeline - CLI Application

**Key Characteristics:**
- Three-script pipeline: ingest, search, chat
- PDF document ingestion into PostgreSQL with pgVector for vector storage
- Semantic search over embedded document chunks, with LLM-powered answer generation
- CLI-based interactive chat interface
- Currently a scaffold/skeleton -- all core functions are stub `pass` implementations

## Layers

**Ingestion Layer:**
- Purpose: Read a PDF file, split into chunks, generate embeddings, store vectors in PostgreSQL/pgVector
- Location: `src/ingest.py`
- Contains: PDF loading, text splitting, embedding generation, vector storage
- Depends on: LangChain (PyPDFLoader, RecursiveCharacterTextSplitter, PGVector), embedding provider (OpenAI or Google), PostgreSQL
- Used by: Executed standalone as a one-time data preparation step

**Search/Retrieval Layer:**
- Purpose: Accept a user question, vectorize it, perform similarity search against stored embeddings, construct a prompt with retrieved context, and call an LLM
- Location: `src/search.py`
- Contains: Prompt template (`PROMPT_TEMPLATE`), search function (`search_prompt`)
- Depends on: LangChain PGVector (similarity_search_with_score), embedding provider, LLM provider (OpenAI or Google)
- Used by: `src/chat.py`

**Chat/Presentation Layer:**
- Purpose: CLI loop that accepts user questions and displays LLM-generated answers
- Location: `src/chat.py`
- Contains: Main interactive loop, imports `search_prompt` from search module
- Depends on: `src/search.py`
- Used by: End user via terminal

## Data Flow

**Ingestion Flow (offline, one-time):**

1. User runs `python src/ingest.py`
2. PDF at path specified by `PDF_PATH` env var is loaded (expected: LangChain `PyPDFLoader`)
3. Document is split into chunks of 1000 characters with 150 overlap (expected: `RecursiveCharacterTextSplitter`)
4. Each chunk is converted to an embedding vector via OpenAI (`text-embedding-3-small`) or Google (`models/embedding-001`)
5. Vectors are stored in PostgreSQL with pgVector extension via `langchain_postgres.PGVector`

**Query Flow (interactive):**

1. User runs `python src/chat.py` and enters a question
2. `chat.py` calls `search_prompt()` from `src/search.py`
3. Question is vectorized using same embedding model as ingestion
4. Similarity search retrieves top 10 results (`k=10`) from pgVector
5. Retrieved context is injected into `PROMPT_TEMPLATE` along with user question
6. Prompt is sent to LLM (OpenAI `gpt-5-nano` or Google `gemini-2.5-flash-lite`)
7. LLM response is displayed to the user in the terminal

**State Management:**
- All persistent state lives in PostgreSQL with pgVector extension
- No application-level caching or session state
- Environment variables provide all configuration (loaded via `python-dotenv`)

## Key Abstractions

**PROMPT_TEMPLATE:**
- Purpose: Structured prompt that constrains the LLM to answer only from provided context
- Location: `src/search.py` (lines 1-26)
- Pattern: Template string with `{contexto}` and `{pergunta}` placeholders
- Language: Portuguese (Brazilian)

**PGVector (expected):**
- Purpose: Vector store abstraction from LangChain for storing and querying embeddings
- Package: `langchain_postgres.PGVector`
- Pattern: Handles embedding storage and similarity search via `similarity_search_with_score(query, k=10)`

## Entry Points

**`src/ingest.py`:**
- Location: `src/ingest.py`
- Triggers: Manual execution via `python src/ingest.py`
- Responsibilities: Load PDF, chunk text, generate embeddings, store in database
- Current state: Stub - `ingest_pdf()` is `pass`

**`src/chat.py`:**
- Location: `src/chat.py`
- Triggers: Manual execution via `python src/chat.py`
- Responsibilities: Interactive CLI loop for question-answering
- Current state: Stub - `main()` calls `search_prompt()` then `pass`

**`src/search.py`:**
- Location: `src/search.py`
- Triggers: Imported by `src/chat.py`
- Responsibilities: Semantic search and LLM prompt construction
- Current state: Stub - `search_prompt()` is `pass`; prompt template is defined

## Error Handling

**Strategy:** Minimal - only a null check exists in `src/chat.py` for when `search_prompt()` returns falsy

**Patterns:**
- `src/chat.py` checks if `chain` (result of `search_prompt()`) is falsy and prints an error message
- No try/except blocks anywhere in current code
- No structured error handling or logging

## Cross-Cutting Concerns

**Configuration:** Environment variables loaded via `python-dotenv` (`load_dotenv()`) in `src/ingest.py`. Required vars: `PDF_PATH`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, plus API keys for chosen provider (see `.env.example`).

**Logging:** None. Uses `print()` for user-facing output only.

**Validation:** None implemented.

**Authentication:** API keys for OpenAI or Google stored in `.env` file (not committed).

## Infrastructure

**Database:**
- PostgreSQL 17 with pgVector extension
- Runs via Docker Compose (`docker-compose.yml`)
- Bootstrap service auto-creates the `vector` extension
- Default credentials: `postgres/postgres`, database `rag`, port `5432`
- Data persisted via Docker volume `postgres_data`

---

*Architecture analysis: 2026-03-08*
