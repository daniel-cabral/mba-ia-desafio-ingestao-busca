import os
import sys
from unittest.mock import patch

import pytest

from src.ingest import get_pdf_path, get_collection_name, get_provider, validate_env, create_text_splitter


class TestGetPdfPath:
    """Tests for CLI argument parsing (INGE-01)."""

    def test_get_pdf_path_with_arg(self):
        """When a CLI argument is provided, use it as the PDF path."""
        with patch.object(sys, "argv", ["ingest.py", "custom.pdf"]):
            assert get_pdf_path() == "custom.pdf"

    def test_get_pdf_path_default(self):
        """When no CLI argument is provided, default to document.pdf."""
        with patch.object(sys, "argv", ["ingest.py"]):
            assert get_pdf_path() == "document.pdf"


class TestGetCollectionName:
    """Tests for collection name generation (INGE-04)."""

    def test_get_collection_name_from_filename(self):
        """Sanitize PDF filename into a valid collection name."""
        assert get_collection_name("path/to/my-file.pdf") == "my_file_pdf"

    def test_get_collection_name_env_override(self):
        """PG_VECTOR_COLLECTION_NAME env var overrides filename-based name."""
        with patch.dict(os.environ, {"PG_VECTOR_COLLECTION_NAME": "custom_name"}):
            assert get_collection_name("anything.pdf") == "custom_name"


class TestGetProvider:
    """Tests for provider selection (PROV-04)."""

    def test_default_provider(self):
        """Default provider is openai."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_provider() == "openai"

    def test_gemini_provider(self):
        """Can select gemini provider."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini"}):
            assert get_provider() == "gemini"

    def test_lmstudio_provider(self):
        """Can select lmstudio provider."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "lmstudio"}):
            assert get_provider() == "lmstudio"

    def test_invalid_provider(self):
        """Invalid provider exits with error."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
            with pytest.raises(SystemExit):
                get_provider()


class TestValidateEnv:
    """Tests for environment variable validation."""

    def test_validate_env_missing_db(self):
        """Exit with error when DATABASE_URL is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                validate_env("openai")

    def test_validate_env_openai_missing_key(self):
        """Exit with error when OPENAI_API_KEY is missing for openai provider."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg://localhost/rag"}, clear=True):
            with pytest.raises(SystemExit):
                validate_env("openai")

    def test_validate_env_openai_success(self, mock_env):
        """No exception when all required env vars are present for openai."""
        validate_env("openai")  # Should not raise

    def test_validate_env_gemini_missing_key(self):
        """Exit with error when GOOGLE_API_KEY is missing for gemini provider."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg://localhost/rag"}, clear=True):
            with pytest.raises(SystemExit):
                validate_env("gemini")

    def test_validate_env_gemini_success(self):
        """No exception when all required env vars are present for gemini."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg://localhost/rag", "GOOGLE_API_KEY": "test-key"}):
            validate_env("gemini")  # Should not raise

    def test_validate_env_lmstudio_no_key_needed(self):
        """LM Studio doesn't require an API key."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg://localhost/rag"}, clear=True):
            validate_env("lmstudio")  # Should not raise


class TestChunkingParams:
    """Tests for chunking configuration (INGE-02)."""

    def test_chunking_params(self):
        """Text splitter uses chunk_size=1000 and chunk_overlap=150."""
        splitter = create_text_splitter()
        assert splitter._chunk_size == 1000
        assert splitter._chunk_overlap == 150
