# Phase 1: PDF Ingestion Pipeline - Research

**Researched:** 2026-03-08
**Domain:** PDF processing, text chunking, vector embeddings, PostgreSQL/pgVector storage
**Confidence:** HIGH

## Summary

This phase implements a CLI tool that loads a PDF, splits it into text chunks, generates embeddings via OpenAI, and stores them in PostgreSQL with pgVector. The stack is fully constrained by CONTEXT.md and the existing project: LangChain 0.3.27, langchain-postgres 0.0.15, pypdf 6.0.0, and rich for progress display. The database infrastructure (Docker + pgVector) is already configured.

The critical integration point is `langchain_postgres.PGVector` -- the newer package (not the deprecated `langchain_community` version). It requires `psycopg3` connection strings (`postgresql+psycopg://` not `postgresql+psycopg2://`). Tables are auto-created on instantiation. Re-ingestion is handled by the `delete_collection()` method or the `pre_delete_collection=True` constructor parameter.

**Primary recommendation:** Use `PGVector` constructor with `pre_delete_collection=True` for re-ingestion, `PyPDFLoader` for PDF loading, `RecursiveCharacterTextSplitter` for chunking, and `rich.progress.track()` for the progress bar. Process chunks in batches through `add_documents()` to enable progress tracking.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Re-ingestion: Clear existing collection and re-create from scratch on every run
- Prompt user for confirmation before clearing: "Collection exists. Clear and re-ingest? (y/n)"
- No --force flag -- always ask (this is a manual tool)
- Simple "Done" message after completion, no detailed summary
- Rich progress bar during chunk processing showing: PDF filename, chunk count (e.g. 12/38), elapsed time
- Validate environment variables upfront (OPENAI_API_KEY, DATABASE_URL)
- PDF not found/invalid: clear error message + exit non-zero
- DB unreachable: retry 3 times with delay, then fail with message ("Is Docker running?")
- Errors use rich formatting -- red panels with error icon
- Auto-generate collection name from PDF filename (e.g. `document_pdf` from `document.pdf`)
- PG_VECTOR_COLLECTION_NAME env var as optional override

### Claude's Discretion
- Exact rich progress bar layout and styling
- Retry timing/backoff strategy for DB connection
- How collection name is sanitized from PDF filename
- Whether PG_VECTOR_COLLECTION_NAME env var is kept as override or removed

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INGE-01 | CLI: `python src/ingest.py <path>`, defaults to `document.pdf` | sys.argv parsing, dotenv for PDF_PATH fallback |
| INGE-02 | Split chunks: 1000 chars, 150 overlap, RecursiveCharacterTextSplitter | langchain-text-splitters 0.3.9 already in requirements |
| INGE-03 | Embed chunks with configured provider (OpenAI text-embedding-3-small) | langchain-openai 0.3.30 OpenAIEmbeddings |
| INGE-04 | Store in PostgreSQL pgVector via langchain-postgres PGVector | langchain-postgres 0.0.15 PGVector class |
| INGE-05 | Progress feedback via rich progress bar | rich library (needs adding to requirements.txt) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-postgres | 0.0.15 | PGVector store for embeddings | Official LangChain postgres integration, replaces deprecated langchain_community version |
| langchain-openai | 0.3.30 | OpenAI embeddings (text-embedding-3-small) | Standard LangChain OpenAI integration |
| langchain-text-splitters | 0.3.9 | RecursiveCharacterTextSplitter | Standard LangChain text splitting |
| pypdf | 6.0.0 | PDF text extraction | Used by LangChain's PyPDFLoader |
| langchain-community | 0.3.27 | PyPDFLoader document loader | Hosts PDF document loaders |
| rich | 14.x (latest) | Progress bars, error panels, terminal formatting | User decision for progress/error display |
| python-dotenv | 1.1.1 | Load .env file | Already established in project |
| psycopg | 3.2.9 | PostgreSQL driver (psycopg3) | Required by langchain-postgres (not psycopg2) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tenacity | 9.1.2 | Retry logic for DB connection | Already in requirements, use for DB retry |
| SQLAlchemy | 2.0.43 | ORM layer used by langchain-postgres | Already installed, implicit dependency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| langchain-postgres PGVector | langchain_community PGVector | community version is DEPRECATED -- do not use |
| PyPDFLoader | pymupdf, pdfplumber | pypdf already pinned, PyPDFLoader is simplest |
| rich | tqdm | User decided rich; tqdm already installed but not for this |

**Installation (add to requirements.txt):**
```bash
pip install rich
```

## Architecture Patterns

### Recommended Project Structure
```
src/
    ingest.py           # Main ingestion script (CLI entry point)
```

No additional files needed for Phase 1 -- everything lives in `ingest.py` as a single-file script.

### Pattern 1: PDF Loading + Chunking Pipeline
**What:** Load PDF pages as LangChain Documents, then split into chunks
**When to use:** Always -- this is the standard LangChain document processing pattern

```python
# Source: LangChain docs + langchain-postgres examples
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = PyPDFLoader(pdf_path)
documents = loader.load()  # Returns List[Document], one per page

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
)
chunks = text_splitter.split_documents(documents)  # Returns List[Document]
```

### Pattern 2: PGVector Store Initialization + Collection Management
**What:** Create PGVector instance, handle re-ingestion by deleting existing collection
**When to use:** Every ingestion run

```python
# Source: langchain-postgres GitHub examples/vectorstore.ipynb
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
connection = "postgresql+psycopg://postgres:postgres@localhost:5432/rag"

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
    pre_delete_collection=True,  # Clears collection on init
)
```

**For checking if collection exists before prompting user:**
```python
# Create without pre_delete to check first
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
    pre_delete_collection=False,
)
# Then manually delete if user confirms
vector_store.delete_collection()
# Re-create the store (tables auto-created)
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)
```

### Pattern 3: Batch Document Addition with Progress
**What:** Add documents in batches to enable progress tracking
**When to use:** During chunk embedding + storage

```python
from rich.progress import track

# Add chunks in small batches to show progress
batch_size = 10
for i in track(range(0, len(chunks), batch_size), description=f"[cyan]{pdf_name}"):
    batch = chunks[i:i + batch_size]
    vector_store.add_documents(batch)
```

### Pattern 4: Rich Error Panels
**What:** Consistent error display using rich panels
**When to use:** All error conditions

```python
from rich.console import Console
from rich.panel import Panel

console = Console()
console.print(Panel(
    "[red]PDF file not found: document.pdf[/red]",
    title="[red]Error[/red]",
    border_style="red",
))
```

### Pattern 5: Collection Name from PDF Filename
**What:** Sanitize PDF filename into a valid collection name
**When to use:** Auto-generating collection name

```python
import re
from pathlib import Path

def collection_name_from_pdf(pdf_path: str) -> str:
    """Convert 'path/to/my-file.pdf' -> 'my_file_pdf'"""
    name = Path(pdf_path).name  # 'my-file.pdf'
    # Replace non-alphanumeric with underscore, collapse multiples
    sanitized = re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_').lower()
    return sanitized
```

### Anti-Patterns to Avoid
- **Using langchain_community.vectorstores.PGVector:** DEPRECATED. Always use `langchain_postgres.PGVector`
- **Using psycopg2 connection string:** Must use `postgresql+psycopg://` (psycopg3), not `postgresql+psycopg2://`
- **Loading all pages then joining text:** Use `split_documents()` not `split_text()` -- preserves page metadata
- **Embedding all chunks at once without progress:** Users need visual feedback; batch and track
- **Hardcoding collection name:** Must derive from PDF filename for multi-PDF support across phases

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction | Custom PDF parser | `PyPDFLoader` | Handles encoding, page boundaries, metadata |
| Text chunking | Custom chunk logic | `RecursiveCharacterTextSplitter` | Smart separator hierarchy (paragraph > line > sentence > word) |
| Vector storage | Raw SQL inserts | `PGVector` class | Handles table creation, indexing, collection management |
| Retry logic | Custom retry loops | `tenacity` library | Already in requirements, handles backoff patterns |
| Progress display | print statements | `rich` library | Handles terminal width, colors, elapsed time |
| Embedding API calls | Raw HTTP to OpenAI | `OpenAIEmbeddings` | Handles batching, rate limits, token counting |

**Key insight:** LangChain provides the entire pipeline from PDF to vector store. The implementation code should be glue between LangChain components + CLI/UX logic, not custom data processing.

## Common Pitfalls

### Pitfall 1: Wrong PGVector Import
**What goes wrong:** Using `from langchain_community.vectorstores import PGVector` instead of `from langchain_postgres import PGVector`
**Why it happens:** Old tutorials reference the community package
**How to avoid:** Always import from `langchain_postgres`
**Warning signs:** Deprecation warnings in console output

### Pitfall 2: psycopg2 vs psycopg3 Connection String
**What goes wrong:** Using `postgresql+psycopg2://` causes connection failures with langchain-postgres
**Why it happens:** psycopg2 was the standard for years
**How to avoid:** Always use `postgresql+psycopg://` (no "2" suffix)
**Warning signs:** SQLAlchemy connection errors mentioning driver

### Pitfall 3: Embedding Dimension Mismatch
**What goes wrong:** Re-ingesting with a different embedding model creates dimension conflicts
**Why it happens:** pgVector columns have fixed dimensions; text-embedding-3-small = 1536 dims
**How to avoid:** `pre_delete_collection=True` or `drop_tables()` before re-ingestion
**Warning signs:** PostgreSQL errors about vector dimension mismatch

### Pitfall 4: Missing Vector Extension
**What goes wrong:** PGVector fails because the `vector` extension isn't created
**Why it happens:** Extension must be explicitly created in PostgreSQL
**How to avoid:** Docker compose already handles this via `bootstrap_vector_ext` service
**Warning signs:** SQL error "type vector does not exist"

### Pitfall 5: Not Validating Environment Before Work
**What goes wrong:** Script starts processing, embeds chunks, then fails on DB write
**Why it happens:** Lazy validation -- errors surface late
**How to avoid:** Check OPENAI_API_KEY and DATABASE_URL existence at startup, test DB connection before processing
**Warning signs:** Wasted API calls (costs money) before failure

### Pitfall 6: Large PDF Memory Usage
**What goes wrong:** Loading a very large PDF into memory causes OOM
**Why it happens:** `loader.load()` loads all pages at once
**How to avoid:** For this assignment scope, `load()` is fine (single PDF, reasonable size). `lazy_load()` available if needed.
**Warning signs:** Memory errors on very large PDFs

## Code Examples

### Complete Ingestion Flow (Skeleton)
```python
# Source: Synthesized from langchain-postgres examples + project requirements
import sys
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

load_dotenv()
console = Console()

def get_pdf_path() -> str:
    """Get PDF path from CLI arg or default to 'document.pdf'."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return "document.pdf"

def get_collection_name(pdf_path: str) -> str:
    """Derive collection name from PDF filename."""
    env_name = os.getenv("PG_VECTOR_COLLECTION_NAME")
    if env_name:
        return env_name
    name = Path(pdf_path).name
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_').lower()

def validate_env():
    """Validate required environment variables."""
    missing = []
    if not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if not os.getenv("DATABASE_URL"):
        missing.append("DATABASE_URL")
    if missing:
        console.print(Panel(
            f"[red]Missing environment variables: {', '.join(missing)}[/red]",
            title="[red]Error[/red]",
            border_style="red",
        ))
        sys.exit(1)

def ingest_pdf():
    validate_env()

    pdf_path = get_pdf_path()
    if not Path(pdf_path).exists():
        console.print(Panel(
            f"[red]PDF file not found: {pdf_path}[/red]",
            title="[red]Error[/red]",
            border_style="red",
        ))
        sys.exit(1)

    collection_name = get_collection_name(pdf_path)
    connection = os.getenv("DATABASE_URL")

    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))

    # Load and split PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = text_splitter.split_documents(documents)

    # Create vector store (with collection check + user confirmation)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )

    # Add documents with progress
    batch_size = 10
    for i in track(range(0, len(chunks), batch_size),
                   description=f"Processing {Path(pdf_path).name}"):
        batch = chunks[i:i + batch_size]
        vector_store.add_documents(batch)

    console.print("[green]Done[/green]")
```

### DB Connection Retry with Tenacity
```python
# Source: tenacity docs + project requirements
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(OperationalError),
)
def test_db_connection(connection_string: str):
    """Test database connectivity with retries."""
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
```

### Rich Progress with Custom Display
```python
# Source: rich docs
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn,
    MofNCompleteColumn, TimeElapsedColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    MofNCompleteColumn(),
    TimeElapsedColumn(),
) as progress:
    task = progress.add_task(f"Processing {pdf_name}", total=len(chunks))
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        vector_store.add_documents(batch)
        progress.update(task, advance=len(batch))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `langchain_community.vectorstores.PGVector` | `langchain_postgres.PGVector` | 2024 | Must use new import path |
| `psycopg2` driver | `psycopg` (v3) | 2024 | Connection string changes |
| `use_jsonb=False` | `use_jsonb=True` (required) | langchain-postgres 0.0.12+ | False is no longer supported |
| Manual vector extension | Docker bootstrap service | Project setup | Already handled |

**Deprecated/outdated:**
- `langchain_community.vectorstores.pgvector.PGVector`: Deprecated, use `langchain_postgres.PGVector`
- `psycopg2` connection strings: Not compatible with langchain-postgres
- `use_jsonb=False`: No longer supported in langchain-postgres

## Open Questions

1. **Collection existence check via PGVector API**
   - What we know: `delete_collection()` and `pre_delete_collection` exist
   - What's unclear: Whether there's a clean API to check if a collection exists without creating it (for the user confirmation prompt)
   - Recommendation: Try creating with `pre_delete_collection=False`, catch any error, or query the collection table directly via SQLAlchemy. The implementation should test this at dev time.

2. **Batch size for add_documents**
   - What we know: `add_documents()` accepts a list of Documents
   - What's unclear: Optimal batch size for progress granularity vs. API efficiency
   - Recommendation: Start with batch_size=10, adjustable. This gives ~4 progress updates for a 38-chunk document.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (standard Python, needs install) |
| Config file | none -- Wave 0 |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INGE-01 | CLI arg parsing, default to document.pdf | unit | `python -m pytest tests/test_ingest.py::test_cli_args -x` | No -- Wave 0 |
| INGE-02 | Chunk size=1000, overlap=150 | unit | `python -m pytest tests/test_ingest.py::test_chunking -x` | No -- Wave 0 |
| INGE-03 | Embedding generation (mocked) | unit | `python -m pytest tests/test_ingest.py::test_embeddings -x` | No -- Wave 0 |
| INGE-04 | PGVector storage (integration) | integration | `python -m pytest tests/test_ingest.py::test_pgvector_store -x` | No -- Wave 0 |
| INGE-05 | Progress bar displays | manual-only | Manual: run ingest and visually confirm progress bar | N/A |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_ingest.py` -- unit tests for CLI parsing, chunking params, env validation
- [ ] `tests/conftest.py` -- shared fixtures (mock embeddings, test PDF)
- [ ] Framework install: `pip install pytest` and add to requirements.txt
- [ ] Test PDF fixture: small test PDF for unit tests

## Sources

### Primary (HIGH confidence)
- [langchain-postgres GitHub vectorstores.py](https://github.com/langchain-ai/langchain-postgres/blob/main/langchain_postgres/vectorstores.py) -- PGVector constructor, methods, parameters
- [langchain-postgres examples/vectorstore.ipynb](https://github.com/langchain-ai/langchain-postgres/blob/main/examples/vectorstore.ipynb) -- Working usage examples
- [Rich Progress docs](https://rich.readthedocs.io/en/latest/progress.html) -- Progress bar API and customization
- Project files: `requirements.txt`, `docker-compose.yml`, `.env.example`, `src/ingest.py`

### Secondary (MEDIUM confidence)
- [LangChain PyPDFLoader docs](https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.pdf.PyPDFLoader.html) -- PDF loading API
- [LangChain RecursiveCharacterTextSplitter tutorial](https://langchain-opentutorial.gitbook.io/langchain-opentutorial/07-textsplitter/02-recursivecharactertextsplitter) -- Chunking patterns

### Tertiary (LOW confidence)
- None -- all findings verified against official sources or project code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already pinned in requirements.txt, versions known
- Architecture: HIGH -- LangChain patterns are well-documented, project structure is simple
- Pitfalls: HIGH -- common issues well-documented across multiple sources
- Validation: MEDIUM -- no existing test infrastructure; pytest is standard but needs setup

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (stable stack, all versions pinned)
