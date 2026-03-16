# Architecture Patterns

**Domain:** RAG Pipeline / PDF Semantic Search CLI
**Researched:** 2026-03-08

## Recommended Architecture

This project follows the canonical **Indexing + Retrieval** two-phase RAG pattern, mapped directly onto the three-file structure required by the assignment.

```
Phase 1: INDEXING (ingest.py)                    Phase 2: QUERY (search.py + chat.py)

PDF File                                         User Question (CLI)
  |                                                |
  v                                                v
PyPDFLoader                                      Embeddings Model
  |                                              (same model used in indexing)
  v                                                |
RecursiveCharacterTextSplitter                     v
(1000 chars, 150 overlap)                        PGVector.similarity_search_with_score(k=10)
  |                                                |
  v                                                v
Embeddings Model                                 Retrieved Document chunks
(text-embedding-3-small or embedding-001)          |
  |                                                v
  v                                              Prompt Template (CONTEXTO + REGRAS + PERGUNTA)
PGVector.from_documents()                          |
  |                                                v
  v                                              LLM (gpt-4.1-nano or gemini-2.5-flash-lite)
PostgreSQL 17 + pgVector extension                 |
(Docker container)                                 v
                                                 Answer (printed to terminal)
```

### Component Boundaries

| Component | File | Responsibility | Communicates With |
|-----------|------|---------------|-------------------|
| **PDF Loader** | `ingest.py` | Load PDF pages as LangChain Documents | Text Splitter |
| **Text Splitter** | `ingest.py` | Split documents into 1000-char chunks with 150 overlap | Vector Store |
| **Embedding Model** | `ingest.py` + `search.py` | Convert text to vector representations | Vector Store (write), Similarity Search (read) |
| **Vector Store (PGVector)** | `ingest.py` + `search.py` | Store and retrieve embeddings in PostgreSQL | PostgreSQL via psycopg/SQLAlchemy |
| **PostgreSQL + pgVector** | `docker-compose.yml` | Persistent vector storage with similarity search operators | Vector Store component via TCP :5432 |
| **Retriever** | `search.py` | Query vector store, format prompt with context | LLM |
| **Prompt Template** | `search.py` | Combine retrieved context + user question into structured prompt | LLM |
| **LLM** | `search.py` | Generate answer from prompt | Chat Loop |
| **Chat Loop** | `chat.py` | Interactive CLI, send questions, display answers | Retriever + LLM chain |

### Data Flow

**Indexing flow (run once per PDF):**

1. `ingest.py` receives PDF path (from env var or CLI argument)
2. `PyPDFLoader(pdf_path).load()` returns list of `Document` objects (one per page)
3. `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(docs)` produces smaller chunks
4. `PGVector.from_documents(chunks, embedding_model, connection=CONNECTION_STRING, collection_name="...")` embeds all chunks and inserts them into PostgreSQL

**Query flow (runs per question):**

1. `chat.py` captures user input in a loop
2. Calls `search.py`'s chain with the question
3. `search.py` creates a `PGVector` instance pointing to the existing collection
4. `vector_store.similarity_search_with_score(question, k=10)` vectorizes the question and retrieves top 10 chunks
5. Retrieved chunks are concatenated into the `{contexto}` field of the prompt template
6. Complete prompt is sent to LLM via `ChatOpenAI` or `ChatGoogleGenerativeAI`
7. LLM response is returned and printed

## Patterns to Follow

### Pattern 1: Provider Abstraction via Environment Variables

**What:** Use a single env var (e.g., `LLM_PROVIDER=openai|gemini`) to switch between providers. Initialize the correct embedding model and chat model based on this value.

**When:** Always -- this is a core requirement.

**Example:**

```python
import os

def get_embeddings():
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    else:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4.1-nano")
```

**Why:** Keeps provider logic centralized. Both `ingest.py` and `search.py` call the same factory functions, guaranteeing embedding model consistency.

### Pattern 2: Connection String from Environment

**What:** Build the PostgreSQL connection string from env vars or use a sensible default matching docker-compose.yml.

**Example:**

```python
CONNECTION_STRING = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/rag"
)
```

**Why:** The `langchain-postgres` PGVector class expects a SQLAlchemy-style connection string with the `psycopg` driver (psycopg3, not psycopg2). The `+psycopg` suffix is critical -- using `+psycopg2` will also work since psycopg2-binary is in requirements, but `psycopg` (v3) is the modern default for `langchain-postgres`.

### Pattern 3: Separate Indexing from Querying

**What:** `ingest.py` uses `PGVector.from_documents()` (creates collection + inserts). `search.py` instantiates `PGVector(...)` pointing to the existing collection (read-only).

**Why:** Indexing is a one-time batch operation. Querying is repeated. Separating them prevents accidental re-indexing and keeps the query path fast.

### Pattern 4: Manual Retrieval + Prompt Construction (not using RetrievalQA chain)

**What:** For this assignment, build the chain manually: call `similarity_search_with_score`, concatenate results, format prompt template, call LLM. Do NOT use LangChain's `RetrievalQA` or `create_retrieval_chain` abstractions.

**Why:** The assignment specifies exact control over k=10, the exact prompt template, and `similarity_search_with_score` (not just `similarity_search`). Using high-level chains would obscure these requirements and make it harder to match the exact specification. Manual construction is simpler and more transparent for this scope.

```python
# search.py approach
def search_prompt(question=None):
    embeddings = get_embeddings()
    vector_store = PGVector(
        embeddings=embeddings,
        connection=CONNECTION_STRING,
        collection_name="pdf_chunks",
    )

    if question is None:
        # Return a callable for the chat loop
        llm = get_llm()
        def ask(q):
            results = vector_store.similarity_search_with_score(q, k=10)
            contexto = "\n\n".join([doc.page_content for doc, score in results])
            prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=q)
            response = llm.invoke(prompt)
            return response.content
        return ask
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Mismatched Embedding Models Between Indexing and Querying

**What:** Using OpenAI embeddings for ingestion but Gemini embeddings for search (or vice versa).

**Why bad:** Vectors from different embedding models are completely incompatible. Similarity search will return garbage results. The collection must be re-ingested when switching providers.

**Instead:** Use the same `get_embeddings()` factory in both files. When switching providers, re-run `ingest.py` to re-embed the PDF.

### Anti-Pattern 2: Using `psycopg2` Driver with `langchain-postgres`

**What:** Connection string `postgresql+psycopg2://...` with the `langchain_postgres.PGVector` class.

**Why bad:** `langchain-postgres` (the newer package, v0.0.15 in requirements) is built on psycopg3 (the `psycopg` package). While it may accept psycopg2 connections, the documented and tested path is `postgresql+psycopg://...`. Note: the older `langchain_community.vectorstores.PGVector` used psycopg2, but that class is deprecated.

**Instead:** Use `postgresql+psycopg://postgres:postgres@localhost:5432/rag`.

### Anti-Pattern 3: Storing Scores but Never Using Them

**What:** Calling `similarity_search_with_score` but ignoring the scores.

**Why bad:** The assignment specifies `similarity_search_with_score` -- scores could be logged or used for relevance filtering. At minimum, acknowledge them in the implementation even if not displayed.

**Instead:** Use the scored variant as required. Consider logging scores for debugging.

### Anti-Pattern 4: Re-creating the Vector Extension in Python

**What:** Running `CREATE EXTENSION IF NOT EXISTS vector` inside `ingest.py`.

**Why bad:** The docker-compose.yml already has a `bootstrap_vector_ext` service that handles this. Duplicating it adds unnecessary complexity and a potential race condition.

**Instead:** Trust the Docker Compose bootstrap. Document in README that `docker compose up -d` must run before `ingest.py`.

## Key Architecture Decisions

### langchain-postgres vs langchain-community PGVector

The project uses `langchain-postgres==0.0.15` (the dedicated package), NOT the older `langchain_community.vectorstores.PGVector`. This is the correct choice:

- `langchain-postgres` is the actively maintained package
- `langchain_community` PGVector is deprecated and will be removed
- Import path: `from langchain_postgres import PGVector`
- Requires psycopg3 (`psycopg` package, already in requirements)

### Collection Name Strategy

Use a fixed collection name (e.g., `"pdf_chunks"`) since the assignment is single-document. Both `ingest.py` and `search.py` must use the same collection name. Consider making it a shared constant or env var.

### No LangChain Expression Language (LCEL) Needed

For this scope, plain function calls are clearer than LCEL pipe syntax (`chain = retriever | prompt | llm`). The assignment is simple enough that LCEL adds abstraction without benefit.

## Suggested Build Order

Based on component dependencies:

```
1. Docker/Database (already done)
   - docker-compose.yml exists and works
   - pgVector extension auto-bootstraps

2. Provider Configuration (shared module or inline)
   - get_embeddings() factory
   - get_llm() factory
   - CONNECTION_STRING constant
   - .env file with API keys

3. ingest.py (depends on: provider config, database)
   - PDF loading
   - Text splitting
   - Embedding + storage in PGVector

4. search.py (depends on: provider config, database, ingested data)
   - PGVector connection to existing collection
   - similarity_search_with_score
   - Prompt template formatting
   - LLM invocation
   - Return callable chain

5. chat.py (depends on: search.py)
   - Interactive input loop
   - Call search chain
   - Display responses
   - Handle exit gracefully
```

**Critical dependency:** `ingest.py` MUST run successfully before `search.py` can work. The collection must exist with data. This is a sequential, not parallel, build path.

**Shared code consideration:** The provider factories (`get_embeddings`, `get_llm`, `CONNECTION_STRING`) are needed by both `ingest.py` and `search.py`. Options:
1. **Duplicate the code** in both files (simplest, acceptable for 3-file assignment)
2. **Import from a shared location** -- but the assignment structure only specifies 3 files. A helper could be added, but keep it minimal.

Recommendation: Put shared config in `search.py` and import from it in `ingest.py`, since `chat.py` already imports from `search.py`. This keeps the dependency tree clean: `chat.py -> search.py <- ingest.py`.

## Scalability Considerations

Not a primary concern for this assignment (single PDF, local CLI), but noted for completeness:

| Concern | Current Scale | If Scaled |
|---------|--------------|-----------|
| PDF size | Single document, ~dozens of pages | Use batch insertion, consider async embedding calls |
| Query latency | Acceptable for CLI | Add HNSW index on pgVector for approximate nearest neighbor |
| Concurrent users | Single user | Connection pooling via psycopg pool |
| Multiple documents | Out of scope | Add document_id metadata, filter by document in search |

## Sources

- Project scaffold files (ingest.py, search.py, chat.py stubs)
- Assignment instructions (docs/instrucoes.md)
- requirements.txt (pinned dependency versions)
- docker-compose.yml (database configuration)
- LangChain documentation for langchain-postgres, langchain-openai, langchain-google-genai (training data, MEDIUM confidence)
- pgVector documentation (training data, HIGH confidence -- stable, well-known project)
