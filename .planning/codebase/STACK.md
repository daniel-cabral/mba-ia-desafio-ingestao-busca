# Technology Stack

**Analysis Date:** 2026-03-08

## Languages

**Primary:**
- Python 3 - All application code (`src/ingest.py`, `src/search.py`, `src/chat.py`)

**Secondary:**
- SQL - Database bootstrap via Docker Compose (`docker-compose.yml` bootstrap_vector_ext service)

## Runtime

**Environment:**
- Python 3 (no `.python-version` file; version not pinned)
- Virtual environment recommended (`python3 -m venv venv`)

**Package Manager:**
- pip with `requirements.txt` (pinned versions, no lockfile)
- Lockfile: missing (only `requirements.txt` with `==` pins)

## Frameworks

**Core:**
- LangChain 0.3.27 - Orchestration framework for RAG pipeline
- LangChain Core 0.3.74 - Core abstractions
- LangChain Community 0.3.27 - Community integrations (PDF loader)
- LangChain Text Splitters 0.3.9 - Document chunking (RecursiveCharacterTextSplitter)

**LLM Providers:**
- LangChain OpenAI 0.3.30 - OpenAI embeddings and LLM (text-embedding-3-small, gpt-5-nano)
- LangChain Google GenAI 2.1.9 - Google Gemini embeddings and LLM (models/embedding-001, gemini-2.5-flash-lite)

**Database/Vector Store:**
- LangChain Postgres 0.0.15 - PGVector integration for vector storage and similarity search

**Testing:**
- Not detected - no test framework in `requirements.txt`

**Build/Dev:**
- Docker & Docker Compose - PostgreSQL with pgvector (`docker-compose.yml`)
- python-dotenv 1.1.1 - Environment variable loading

## Key Dependencies

**Critical:**
- `langchain==0.3.27` - Core RAG orchestration framework
- `langchain-postgres==0.0.15` - PGVector vector store integration
- `langchain-openai==0.3.30` - OpenAI embeddings + LLM provider
- `langchain-google-genai==2.1.9` - Google Gemini embeddings + LLM provider
- `openai==1.102.0` - OpenAI Python SDK (underlying client)
- `pgvector==0.3.6` - pgvector Python extension support
- `pypdf==6.0.0` - PDF parsing (used by LangChain's PyPDFLoader)

**Infrastructure:**
- `psycopg==3.2.9` + `psycopg-binary==3.2.9` - PostgreSQL async driver (psycopg3)
- `psycopg2-binary==2.9.10` - PostgreSQL driver (psycopg2, legacy)
- `psycopg-pool==3.2.6` - Connection pooling for psycopg3
- `SQLAlchemy==2.0.43` - SQL toolkit (used by langchain-postgres under the hood)
- `asyncpg==0.30.0` - Async PostgreSQL driver
- `pydantic==2.11.7` - Data validation (used by LangChain internals)
- `pydantic-settings==2.10.1` - Settings management
- `tiktoken==0.11.0` - OpenAI tokenizer for text splitting
- `numpy==2.3.2` - Numerical operations for vector math

**Networking/HTTP:**
- `httpx==0.28.1` - Async HTTP client (used by OpenAI SDK)
- `aiohttp==3.12.15` - Async HTTP (used by Google GenAI SDK)
- `requests==2.32.5` - HTTP client
- `grpcio==1.74.0` - gRPC (used by Google AI SDK)

**Google AI Stack:**
- `google-ai-generativelanguage==0.6.18` - Google AI API bindings
- `google-api-core==2.25.1` - Google API core
- `google-auth==2.40.3` - Google authentication

## Configuration

**Environment:**
- `.env.example` defines required variables (never read `.env` contents)
- Loaded via `python-dotenv` in application code (`load_dotenv()` in `src/ingest.py`)
- Required env vars: `GOOGLE_API_KEY`, `GOOGLE_EMBEDDING_MODEL`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `DATABASE_URL`, `PG_VECTOR_COLLECTION_NAME`, `PDF_PATH`

**Build:**
- `docker-compose.yml` - PostgreSQL 17 with pgvector extension
- `requirements.txt` - All Python dependencies pinned

## Platform Requirements

**Development:**
- Python 3 with venv
- Docker & Docker Compose (for PostgreSQL + pgvector)
- API key for either OpenAI or Google Gemini

**Production:**
- PostgreSQL 17 with pgvector extension
- Python runtime with all dependencies from `requirements.txt`

---

*Stack analysis: 2026-03-08*
