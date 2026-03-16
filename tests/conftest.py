import os
from unittest.mock import patch

import pytest
from pypdf import PdfWriter


@pytest.fixture
def mock_env():
    """Patch environment with required variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-key",
        "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/rag",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def tmp_pdf(tmp_path):
    """Create a minimal valid PDF file for testing."""
    pdf_path = tmp_path / "test_document.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    # Add text annotation as a simple way to include content
    page = writer.pages[0]
    page.merge_page(page)  # ensure page is valid
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return str(pdf_path)
