# External Integrations

**Analysis Date:** 2026-03-08

## APIs & External Services

**LLM Providers (choose one):**

- **OpenAI** - Embeddings and chat completion for RAG responses
  - SDK/Client: `openai==1.102.0` via `langchain-openai==0.3.30`
  - Embeddings model: `text-embedding-3-small` (configured via `OPENAI_EMBEDDING_MODEL` env var)
  - LLM model: `gpt-5-nano` (per project instructions in `docs/instrucoes.md`)
  - Auth: `OPENAI_API_KEY` env var
  - LangChain class: `from langchain_openai import OpenAIEmbeddings`

- **Google Gemini** - Alternative embeddings and chat completion
  - SDK/Client: `google-ai-generativelanguage==0.6.18` via `langchain-google-genai==2.1.9`
  - Embeddings model: `models/embedding-001` (configured via `GOOGLE_EMBEDDING_MODEL` env var)
  - LLM model: `gemini-2.5-flash-lite` (per project instructions in `docs/instrucoes.md`)
  - Auth: `GOOGLE_API_KEY` env var
  - LangChain class: `from langchain_google_genai import GoogleGenerativeAIEmbeddings`

**LangSmith (optional):**
- LangSmith 0.4.20 is included in dependencies for LangChain tracing/observability
  - SDK/Client: `langsmith==0.4.20`
  - No env vars configured in `.env.example` for this

## Data Storage

**Databases:**
- PostgreSQL 17 with pgvector extension
  - Image: `pgvector/pgvector:pg17` (via `docker-compose.yml`)
  - Connection: `DATABASE_URL` env var
  - Default Docker credentials: user `postgres`, password `postgres`, database `rag` (in `docker-compose.yml`)
  - Port: 5432 (mapped to host)
  - Client: `langchain-postgres` PGVector class (`from langchain_postgres import PGVector`)
  - Underlying ORM: SQLAlchemy 2.0.43
  - Drivers: `psycopg==3.2.9`, `psycopg2-binary==2.9.10`, `asyncpg==0.30.0`
  - Vector extension bootstrap: Automatic via `bootstrap_vector_ext` Docker service (`CREATE EXTENSION IF NOT EXISTS vector`)
  - Collection name: `PG_VECTOR_COLLECTION_NAME` env var
  - Volume: `postgres_data` (persistent Docker volume)

**File Storage:**
- Local filesystem only
  - PDF input: `document.pdf` at project root
  - Path configured via `PDF_PATH` env var

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- Not applicable (CLI application, no user auth)
- API keys for LLM providers stored in env vars

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Console output only (print statements in `src/chat.py`)

## CI/CD & Deployment

**Hosting:**
- Local execution (CLI application)

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars (from `.env.example`):**
- `GOOGLE_API_KEY` - Google Gemini API authentication
- `GOOGLE_EMBEDDING_MODEL` - Google embedding model name (default: `models/embedding-001`)
- `OPENAI_API_KEY` - OpenAI API authentication
- `OPENAI_EMBEDDING_MODEL` - OpenAI embedding model name (default: `text-embedding-3-small`)
- `DATABASE_URL` - PostgreSQL connection string
- `PG_VECTOR_COLLECTION_NAME` - Name for the pgvector collection
- `PDF_PATH` - Path to the PDF file to ingest

**Secrets location:**
- `.env` file (gitignored, `.env.example` provided as template)

## Document Processing

**PDF Ingestion Pipeline (to be implemented in `src/ingest.py`):**
- Loader: `from langchain_community.document_loaders import PyPDFLoader`
- Splitter: `RecursiveCharacterTextSplitter` with chunk_size=1000, chunk_overlap=150
- Vector store: PGVector with similarity search (k=10)
- Input file: `document.pdf` (project root)

## Webhooks & Callbacks

**Incoming:**
- None (CLI application)

**Outgoing:**
- None

---

*Integration audit: 2026-03-08*
