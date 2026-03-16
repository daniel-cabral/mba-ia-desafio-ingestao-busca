# Testing Patterns

**Analysis Date:** 2026-03-08

## Test Framework

**Runner:**
- No test framework is configured
- No test files exist anywhere in the project
- No `pytest`, `unittest`, or any test runner in `requirements.txt`

**Recommendation:** Add `pytest` as the test runner. It is the de facto standard for Python projects using LangChain and Pydantic.

**Suggested setup:**
```bash
pip install pytest pytest-cov pytest-asyncio
```

**Suggested config (add to `pyproject.toml`):**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

## Test File Organization

**Current state:** No test files exist.

**Recommended structure:**
```
tests/
├── conftest.py          # Shared fixtures (db connection, mock LLM)
├── test_ingest.py       # Tests for src/ingest.py
├── test_search.py       # Tests for src/search.py
└── test_chat.py         # Tests for src/chat.py
```

**Naming convention to follow:**
- Test files: `test_<module>.py`
- Test functions: `test_<behavior_description>()`
- Fixtures: descriptive `snake_case` names

## Test Structure

**Recommended pattern for this codebase:**
```python
# tests/test_ingest.py
import pytest
from unittest.mock import patch, MagicMock

class TestIngestPdf:
    """Tests for the PDF ingestion pipeline."""

    def test_ingest_pdf_reads_file(self, tmp_path):
        """Verify that ingest_pdf reads the PDF from the configured path."""
        # Arrange
        pdf_path = tmp_path / "test.pdf"
        # ... create test PDF ...

        # Act
        with patch.dict("os.environ", {"PDF_PATH": str(pdf_path)}):
            result = ingest_pdf()

        # Assert
        assert result is not None
```

## Mocking

**What will need mocking (based on dependencies in `requirements.txt`):**
- LLM API calls: `langchain-google-genai`, `langchain-openai` (use `unittest.mock.patch`)
- Database connections: `langchain-postgres`, `psycopg`, `SQLAlchemy`
- PDF reading: `pypdf`
- Environment variables: `unittest.mock.patch.dict("os.environ", {...})`

**Recommended mocking approach:**
```python
from unittest.mock import patch, MagicMock

@patch("ingest.some_llm_client")
def test_with_mocked_llm(mock_client):
    mock_client.return_value = MagicMock()
    mock_client.return_value.embed.return_value = [0.1, 0.2, 0.3]
    # ...
```

**What to mock:**
- All external API calls (OpenAI, Google AI)
- Database connections and queries
- File system reads for PDF (use `tmp_path` fixture instead)

**What NOT to mock:**
- Prompt template formatting logic in `src/search.py`
- Pure data transformation functions
- LangChain chain construction (test integration with mocked endpoints)

## Fixtures and Factories

**Recommended fixtures for `tests/conftest.py`:**
```python
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_embeddings():
    """Mock embedding model that returns fixed vectors."""
    mock = MagicMock()
    mock.embed_documents.return_value = [[0.1] * 384]
    mock.embed_query.return_value = [0.1] * 384
    return mock

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal test PDF."""
    # Use pypdf or a fixture file
    pass

@pytest.fixture
def mock_vector_store():
    """Mock pgvector store."""
    mock = MagicMock()
    mock.similarity_search.return_value = []
    return mock
```

## Coverage

**Requirements:** None enforced (no coverage tool configured)

**Recommended setup:**
```bash
pytest --cov=src --cov-report=term-missing
```

**Target:** Aim for at least 80% coverage on implemented (non-stub) code.

## Test Types

**Unit Tests:**
- Test individual functions in isolation: `ingest_pdf()`, `search_prompt()`, `main()`
- Mock all external dependencies
- Focus on prompt template correctness in `src/search.py`

**Integration Tests:**
- Test the full chain: PDF ingestion -> vector store -> search -> chat response
- Requires running PostgreSQL with pgvector (use `docker-compose.yml`)
- Mark with `@pytest.mark.integration` to allow skipping in CI

**E2E Tests:**
- Not applicable yet (no web interface or API endpoints)

## Run Commands

**Recommended (once pytest is added):**
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov=src               # With coverage
pytest -k "test_ingest"        # Run specific tests
pytest -m "not integration"    # Skip integration tests
```

## Common Patterns

**Async Testing:**
- Not needed currently (no async code in `src/`)
- If async is added, use `pytest-asyncio`:
```python
import pytest

@pytest.mark.asyncio
async def test_async_search():
    result = await async_search("query")
    assert result is not None
```

**Error Testing:**
```python
def test_search_prompt_without_question():
    """search_prompt called with no question returns None or handles gracefully."""
    result = search_prompt(question=None)
    assert result is None or result == ""
```

**Environment Variable Testing:**
```python
from unittest.mock import patch

def test_ingest_pdf_missing_env():
    """ingest_pdf raises error when PDF_PATH is not set."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            ingest_pdf()
```

---

*Testing analysis: 2026-03-08*
