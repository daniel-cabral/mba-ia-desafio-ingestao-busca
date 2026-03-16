# Codebase Structure

**Analysis Date:** 2026-03-08

## Directory Layout

```
mba-ia-desafio-ingestao-busca/
├── src/
│   ├── ingest.py           # PDF ingestion script (stub)
│   ├── search.py           # Semantic search + prompt template
│   └── chat.py             # CLI chat interface (stub)
├── docs/
│   └── instrucoes.md       # Challenge instructions (Portuguese)
├── .planning/
│   └── codebase/           # Architecture/analysis docs
├── docker-compose.yml      # PostgreSQL + pgVector setup
├── requirements.txt        # Python dependencies (pinned)
├── .env.example            # Environment variable template
├── .gitignore              # Ignores .env, venv, __pycache__
├── document.pdf            # Source PDF for ingestion
└── README.md               # Project README (sparse)
```

## Directory Purposes

**`src/`:**
- Purpose: All application source code
- Contains: Three Python scripts forming the RAG pipeline
- Key files: `ingest.py`, `search.py`, `chat.py`

**`docs/`:**
- Purpose: Project documentation and challenge instructions
- Contains: `instrucoes.md` with full challenge requirements
- Not committed to git yet (shown as untracked)

**`.planning/codebase/`:**
- Purpose: Codebase analysis documents for planning
- Contains: Architecture and structure documentation
- Generated: Yes (by analysis tooling)

## Key File Locations

**Entry Points:**
- `src/ingest.py`: Run to ingest the PDF into the vector database
- `src/chat.py`: Run to start the interactive CLI chat

**Configuration:**
- `docker-compose.yml`: PostgreSQL + pgVector container setup
- `.env.example`: Template for required environment variables
- `requirements.txt`: Pinned Python dependencies

**Core Logic:**
- `src/search.py`: Contains `PROMPT_TEMPLATE` and `search_prompt()` function
- `src/ingest.py`: Contains `ingest_pdf()` function
- `src/chat.py`: Contains `main()` function with CLI loop

**Source Document:**
- `document.pdf`: The PDF file to be ingested (175KB)

**Testing:**
- No test files exist. No test framework is configured.

## Naming Conventions

**Files:**
- snake_case Python files: `ingest.py`, `search.py`, `chat.py`
- All source files are flat in `src/` (no subdirectories, no `__init__.py`)

**Functions:**
- snake_case: `ingest_pdf()`, `search_prompt()`, `main()`

**Variables:**
- UPPER_SNAKE_CASE for constants and env vars: `PDF_PATH`, `PROMPT_TEMPLATE`, `DATABASE_URL`

**Directories:**
- lowercase: `src/`, `docs/`

## Where to Add New Code

**New Feature (e.g., a utility or helper):**
- Primary code: `src/` (add a new `.py` file at `src/` level)
- There is no package structure (`__init__.py`) -- modules import each other directly (e.g., `from search import search_prompt`)

**Extending Ingestion:**
- Add logic inside `ingest_pdf()` in `src/ingest.py`
- Use LangChain loaders and splitters per `docs/instrucoes.md`

**Extending Search/Chat:**
- Search logic goes in `search_prompt()` in `src/search.py`
- Chat loop logic goes in `main()` in `src/chat.py`

**New Dependencies:**
- Add to `requirements.txt` (pinned versions)

**Tests:**
- No test infrastructure exists. If adding tests, create `tests/` at root or co-locate as `src/test_*.py`

## Special Directories

**`venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `python -m venv venv`)
- Committed: No (in `.gitignore`)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python runtime)
- Committed: No (in `.gitignore`)

## Import Pattern

Scripts import each other using direct module names (not package-relative imports). This means scripts must be run from the `src/` directory or `src/` must be on `PYTHONPATH`.

Example from `src/chat.py`:
```python
from search import search_prompt
```

This is a flat module structure -- there is no Python package with `__init__.py`.

## Execution Order

Per challenge requirements:
1. `docker compose up -d` -- start PostgreSQL with pgVector
2. `python src/ingest.py` -- ingest the PDF into the vector store
3. `python src/chat.py` -- start the interactive chat CLI

---

*Structure analysis: 2026-03-08*
