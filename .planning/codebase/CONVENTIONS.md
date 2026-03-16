# Coding Conventions

**Analysis Date:** 2026-03-08

## Language

**Primary:** Python (no version pinned; dependencies suggest Python 3.10+)

## Naming Patterns

**Files:**
- Use lowercase `snake_case` for Python modules: `ingest.py`, `search.py`, `chat.py`
- All source files live flat inside `src/` with no sub-packages

**Functions:**
- Use `snake_case`: `ingest_pdf()`, `search_prompt()`, `main()`
- Short, descriptive verbs: `ingest_pdf`, `search_prompt`

**Variables:**
- Use `UPPER_SNAKE_CASE` for module-level constants and env-derived config: `PDF_PATH`, `PROMPT_TEMPLATE`
- Use `snake_case` for local variables

**Types:**
- No type annotations are used anywhere in the current codebase
- Pydantic is in `requirements.txt` but not yet imported

## Code Style

**Formatting:**
- No formatter configured (no `black`, `ruff`, `autopep8`, or `pyproject.toml` present)
- Recommendation: Add `pyproject.toml` with `[tool.black]` or `[tool.ruff]` configuration

**Linting:**
- No linter configured (no `.flake8`, `.pylintrc`, `ruff.toml`, or linting entries in any config)
- Recommendation: Add `ruff` for linting and formatting

**Indentation:**
- 4 spaces (Python standard)

## Import Organization

**Order observed in `src/ingest.py`:**
1. Standard library imports (`os`)
2. Third-party imports (`from dotenv import load_dotenv`)

**Order observed in `src/chat.py`:**
1. Local imports (`from search import search_prompt`)

**Path Aliases:**
- None. Imports use direct module names (no package structure, no `__init__.py`)

**Guidance for new code:**
1. Standard library imports first
2. Third-party imports second (blank line separator)
3. Local imports third (blank line separator)
4. Use `from module import name` style for specific imports

## Environment Configuration

**Pattern:** Use `python-dotenv` to load `.env` at module level.
```python
# Pattern from src/ingest.py
from dotenv import load_dotenv
load_dotenv()
PDF_PATH = os.getenv("PDF_PATH")
```

**Required env vars** (from `.env.example`):
- `GOOGLE_API_KEY` - Google AI API key
- `GOOGLE_EMBEDDING_MODEL` - defaults to `models/embedding-001`
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_EMBEDDING_MODEL` - defaults to `text-embedding-3-small`
- `DATABASE_URL` - PostgreSQL connection string
- `PG_VECTOR_COLLECTION_NAME` - pgvector collection name
- `PDF_PATH` - path to the PDF document for ingestion

## Error Handling

**Current pattern:** Minimal. Only `src/chat.py` has a basic falsy check:
```python
# src/chat.py lines 6-8
if not chain:
    print("Nao foi possivel iniciar o chat. Verifique os erros de inicializacao.")
    return
```

**Guidance for new code:**
- Use explicit `if not result` checks for None/empty returns
- Print user-facing error messages in Portuguese (project language is pt-BR)
- Use `try/except` for external service calls (LLM APIs, database)

## Logging

**Framework:** None configured. Uses `print()` for output.

**Guidance:**
- Currently `print()` is acceptable given project scope
- If logging is added, use Python's built-in `logging` module

## Comments

**Language:** Portuguese (pt-BR) is used for all user-facing strings and the prompt template in `src/search.py`

**JSDoc/Docstrings:**
- No docstrings present on any functions
- Recommendation: Add docstrings to all public functions

## Function Design

**Size:** Functions are stubs (`pass`), so no patterns established yet

**Parameters:**
- Use keyword arguments with defaults: `search_prompt(question=None)` in `src/search.py`

**Return Values:**
- Functions currently return `None` (stubs with `pass`)

## Module Design

**Exports:**
- No `__init__.py` files; `src/` is not a Python package
- Modules import each other directly by name: `from search import search_prompt`

**Entry Points:**
- Each module uses `if __name__ == "__main__":` guard pattern
- `src/ingest.py`: Runs `ingest_pdf()` for PDF ingestion
- `src/chat.py`: Runs `main()` for interactive chat

**Barrel Files:**
- Not used

## Prompt Engineering

**Pattern in `src/search.py`:**
- Define prompt templates as module-level string constants using `UPPER_SNAKE_CASE`
- Use Python f-string-style placeholders with curly braces: `{contexto}`, `{pergunta}`
- Template constant: `PROMPT_TEMPLATE` at top of module

---

*Convention analysis: 2026-03-08*
