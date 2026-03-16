# Technology Stack

**Project:** PDF Semantic Search (RAG Pipeline)
**Researched:** 2026-03-08
**Constraints:** Stack is assignment-mandated (Python, LangChain, PostgreSQL/pgVector). Research focuses on best practices within those constraints.

## Recommended Stack

All versions below match the project's existing `requirements.txt` pins. These are confirmed recent releases.

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.11+ | Runtime | Required by assignment; 3.11+ for best asyncio and typing support |
| LangChain | 0.3.27 | Orchestration framework | Assignment requirement. v0.3.x is the current stable line with clean module separation |
| langchain-core | 0.3.74 | Base abstractions (LLMs, embeddings, prompts) | Required peer dependency of langchain 0.3.x |
| langchain-text-splitters | 0.3.9 | Document chunking | Separated package for text splitting; use `RecursiveCharacterTextSplitter` |

### Database & Vector Store

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PostgreSQL | 17 | Relational + vector DB | Assignment requirement; pgvector image `pgvector/pgvector:pg17` already in docker-compose |
| pgvector (extension) | latest (bundled) | Vector similarity search in PostgreSQL | The standard for PostgreSQL vector search; HNSW indexing for fast ANN |
| langchain-postgres | 0.0.15 | LangChain <-> pgVector integration | The **official** LangChain integration for PostgreSQL vectors. Uses `PGVector` class |
| psycopg | 3.2.9 | PostgreSQL driver (async-capable) | langchain-postgres uses psycopg3 (not psycopg2) for connection pooling and async |
| psycopg-binary | 3.2.9 | Pre-compiled psycopg binaries | Avoids needing libpq-dev at install time |
| SQLAlchemy | 2.0.43 | ORM / connection management | Used internally by langchain-postgres for table management |

### LLM Providers

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| langchain-openai | 0.3.30 | OpenAI embeddings + chat models | Provides `OpenAIEmbeddings` and `ChatOpenAI` wrappers |
| langchain-google-genai | 2.1.9 | Google Gemini embeddings + chat models | Provides `GoogleGenerativeAIEmbeddings` and `ChatGoogleGenerativeAI` |
| openai | 1.102.0 | OpenAI Python SDK (underlying) | Used by langchain-openai internally |

### PDF Processing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pypdf | 6.0.0 | PDF text extraction | LangChain's `PyPDFLoader` uses this. Lightweight, pure Python, handles most PDFs well |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.1.1 | Load `.env` files | Always -- for API keys and DB connection strings |
| tiktoken | 0.11.0 | OpenAI tokenizer | Used by langchain-openai for token counting |
| pydantic | 2.11.7 | Data validation | Used throughout LangChain 0.3.x (Pydantic v2 required) |
| pydantic-settings | 2.10.1 | Settings management | Optional but useful for typed config |

## Key Implementation Details

### Connection String Format (langchain-postgres)

langchain-postgres 0.0.x uses **psycopg3** connection strings, NOT SQLAlchemy URLs:

```python
# CORRECT -- psycopg3 format
connection = "postgresql+psycopg://postgres:postgres@localhost:5432/rag"

# WRONG -- old psycopg2 format (will fail with langchain-postgres)
# connection = "postgresql+psycopg2://postgres:postgres@localhost:5432/rag"
```

**Confidence:** HIGH -- this is the single most common mistake with langchain-postgres. The `+psycopg` dialect (not `+psycopg2`) is required.

### PGVector Class Usage

```python
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings

vector_store = PGVector(
    embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="pdf_chunks",
    connection=connection,
    use_jsonb=True,  # recommended for metadata filtering
)
```

**Important:** langchain-postgres uses `PGVector` (not `PGVectorStore`). The class handles table creation automatically.

### Document Loading (PyPDFLoader)

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader(pdf_path)
documents = loader.load()  # returns List[Document], one per page
```

### Text Splitting

The assignment specifies 1000-char chunks with 150 overlap. Use `RecursiveCharacterTextSplitter`:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    length_function=len,  # character count, not tokens
)
chunks = splitter.split_documents(documents)
```

**Why `RecursiveCharacterTextSplitter` over `CharacterTextSplitter`:** Recursive splits on paragraph/sentence/word boundaries in order, producing more semantically coherent chunks. `CharacterTextSplitter` only splits on a single separator (default `\n\n`) and can produce oversized chunks when the separator is absent. Always prefer Recursive.

### Retrieval

```python
results = vector_store.similarity_search_with_score(query, k=10)
```

Returns `List[Tuple[Document, float]]` -- documents with their distance scores.

### Prompt Chain

```python
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

prompt = PromptTemplate(
    input_variables=["contexto", "pergunta"],
    template=PROMPT_TEMPLATE,
)

llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)

# Manual chain: retrieve -> format -> call LLM
# For this assignment, a simple retrieve-then-prompt approach is cleaner
# than using LCEL chains, since the flow is straightforward
```

### Dual Provider Pattern

```python
import os

provider = os.getenv("LLM_PROVIDER", "openai")

if provider == "openai":
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)
elif provider == "gemini":
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
```

**Critical:** You cannot mix embedding providers. If you ingest with OpenAI embeddings, you must search with OpenAI embeddings. The vector dimensions differ (text-embedding-3-small = 1536d, embedding-001 = 768d). Use separate collection names per provider or re-ingest when switching.

## Embedding Model Details

| Model | Provider | Dimensions | Max Tokens | Cost | Notes |
|-------|----------|------------|------------|------|-------|
| text-embedding-3-small | OpenAI | 1536 | 8191 | $0.02/1M tokens | Best cost/quality ratio for RAG |
| models/embedding-001 | Google | 768 | 2048 | Free tier available | Good for budget-conscious usage |

**Confidence:** HIGH for OpenAI dimensions/specs. MEDIUM for Gemini embedding-001 (Google has released newer models; embedding-001 may be legacy but is what the assignment specifies).

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| PDF loader | PyPDFLoader | UnstructuredPDFLoader | Unstructured adds heavy dependencies (poppler, tesseract); PyPDF handles text-based PDFs fine |
| Text splitter | RecursiveCharacterTextSplitter | CharacterTextSplitter | CharacterTextSplitter produces poor chunk boundaries; Recursive is strictly better |
| Vector store | langchain-postgres (PGVector) | Chroma, FAISS | Assignment requires PostgreSQL/pgVector |
| PG driver | psycopg3 | psycopg2 | langchain-postgres requires psycopg3; psycopg2 is legacy |
| Chain style | Manual retrieve + prompt | LCEL RetrievalQA chain | For this simple flow, manual composition is clearer and easier to debug |

## What NOT to Use

| Technology | Why Avoid |
|------------|-----------|
| `langchain_community.vectorstores.PGVector` | **Deprecated.** The community PGVector is the OLD integration. Use `langchain_postgres.PGVector` instead |
| `psycopg2` connection strings | langchain-postgres requires psycopg3 (`+psycopg` dialect). psycopg2 strings will fail silently or throw cryptic errors |
| `RetrievalQA` chain | Deprecated in LangChain 0.3.x. If you want chains, use LCEL. But for this project, manual composition is simplest |
| `ConversationalRetrievalChain` | Deprecated, and the project has no conversation memory requirement |
| `load_qa_chain` | Legacy pattern. Use prompt templates directly |
| tiktoken for chunk sizing | Assignment specifies character count (1000 chars), not token count |

## Installation

Already handled by `requirements.txt`. To install:

```bash
pip install -r requirements.txt
```

## Environment Variables Required

```env
# Provider selection
LLM_PROVIDER=openai  # or "gemini"

# OpenAI
OPENAI_API_KEY=sk-...

# Gemini (if using)
GOOGLE_API_KEY=...

# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag

# PDF
PDF_PATH=document.pdf
```

## Sources

- requirements.txt in project (pinned versions confirmed recent)
- LangChain 0.3.x documentation (training data, MEDIUM confidence)
- langchain-postgres package documentation (training data, MEDIUM confidence)
- pgvector PostgreSQL extension documentation (training data, HIGH confidence -- stable project)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Core LangChain 0.3.x patterns | HIGH | Well-established, versions confirmed in requirements.txt |
| langchain-postgres connection format | HIGH | psycopg3 requirement is well-documented and a known migration point |
| PyPDFLoader usage | HIGH | Stable API, widely used |
| RecursiveCharacterTextSplitter | HIGH | Standard recommendation, unchanged for years |
| Embedding dimensions | HIGH (OpenAI), MEDIUM (Gemini) | OpenAI is well-documented; Gemini embedding-001 may have evolved |
| Deprecated API warnings | MEDIUM | Based on LangChain 0.3.x migration patterns; verify if `langchain_community.vectorstores.PGVector` import still works as fallback |
| gpt-4.1-nano model name | MEDIUM | This is a newer model; verify it exists in your OpenAI account |
| gemini-2.5-flash-lite model name | MEDIUM | Newer Gemini model; verify availability |
