"""PDF ingestion pipeline for RAG system.

Loads a PDF, splits it into chunks, generates embeddings, and stores them
in PostgreSQL/pgVector for later retrieval.

Usage:
    python src/ingest.py [pdf_path]

If no pdf_path is provided, defaults to 'document.pdf'.
"""

import io
import os
import re
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows for Rich unicode characters (spinners, braille)
if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

console = Console(force_terminal=True)

_ERROR_TITLE = "[red]Error[/red]"


def get_pdf_path() -> str:
    """Get PDF path from CLI argument or default to 'document.pdf'."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return "document.pdf"


def get_collection_name(pdf_path: str) -> str:
    """Generate a collection name from the PDF filename.

    Uses PG_VECTOR_COLLECTION_NAME env var as override if set.
    Otherwise, sanitizes the filename: replaces non-alphanumeric chars
    with underscores, strips leading/trailing underscores, lowercases.
    """
    env_name = os.environ.get("PG_VECTOR_COLLECTION_NAME", "").strip()
    if env_name:
        return env_name

    filename = Path(pdf_path).name
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", filename)
    sanitized = sanitized.strip("_").lower()
    return sanitized


def get_provider() -> str:
    """Get the configured LLM provider.

    Reads LLM_PROVIDER env var. Defaults to 'openai'.
    Valid values: openai, gemini, lmstudio.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    valid = ("openai", "gemini", "lmstudio")
    if provider not in valid:
        console.print(
            Panel(
                f"Invalid LLM_PROVIDER='{provider}'. Must be one of: {', '.join(valid)}",
                title=_ERROR_TITLE,
                border_style="red",
            )
        )
        sys.exit(1)
    return provider


def get_embeddings(provider: str):
    """Create the embedding model for the configured provider.

    Returns a LangChain embeddings instance for the given provider.
    """
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        return OpenAIEmbeddings(model=model)
    elif provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        model = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001")
        return GoogleGenerativeAIEmbeddings(model=model)
    elif provider == "lmstudio":
        from langchain_openai import OpenAIEmbeddings

        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        model = os.getenv("LMSTUDIO_EMBEDDING_MODEL", "embedding-model")
        return OpenAIEmbeddings(
            model=model,
            openai_api_base=base_url,
            openai_api_key="lm-studio",
        )


def validate_env(provider: str) -> None:
    """Validate that required environment variables are set for the given provider.

    Exits with a rich error panel if required vars are missing.
    """
    missing = []
    if not os.environ.get("DATABASE_URL"):
        missing.append("DATABASE_URL")

    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    elif provider == "gemini" and not os.environ.get("GOOGLE_API_KEY"):
        missing.append("GOOGLE_API_KEY")
    # lmstudio doesn't need an API key

    if missing:
        console.print(
            Panel(
                f"Missing required environment variables for provider '{provider}':\n"
                + "\n".join(f"  - {var}" for var in missing),
                title=_ERROR_TITLE,
                border_style="red",
            )
        )
        sys.exit(1)


def create_text_splitter() -> RecursiveCharacterTextSplitter:
    """Create a text splitter with the configured chunk parameters."""
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(OperationalError),
)
def _test_db_connection_inner(connection_string: str) -> None:
    """Test database connectivity (inner function with retry decorator)."""
    engine = create_engine(connection_string)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def test_db_connection(connection_string: str) -> None:
    """Test database connectivity with 3 retries.

    On final failure, prints a rich error panel suggesting Docker may not be running.
    """
    try:
        _test_db_connection_inner(connection_string)
    except OperationalError:
        console.print(
            Panel(
                "Could not connect to database. Is Docker running?",
                title=_ERROR_TITLE,
                border_style="red",
            )
        )
        sys.exit(1)


def check_collection_exists(connection_string: str, collection_name: str) -> bool:
    """Check if a pgVector collection already exists in the database."""
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM langchain_pg_collection "
                    "WHERE name = :name"
                ),
                {"name": collection_name},
            )
            count = result.scalar()
            return count is not None and count > 0
    except Exception:
        return False


def ingest_pdf() -> None:
    """Main ingestion flow: load PDF, chunk, embed, store in pgVector."""
    load_dotenv()
    provider = get_provider()
    validate_env(provider)

    pdf_path = get_pdf_path()

    # Validate PDF exists
    if not Path(pdf_path).exists():
        console.print(
            Panel(
                f"PDF file not found: {pdf_path}",
                title=_ERROR_TITLE,
                border_style="red",
            )
        )
        sys.exit(1)

    connection_string = os.environ["DATABASE_URL"]

    # Test DB connection (retries 3 times)
    test_db_connection(connection_string)

    collection_name = get_collection_name(pdf_path)

    # Check for existing collection
    if check_collection_exists(connection_string, collection_name):
        answer = input(
            f"Collection '{collection_name}' exists. Clear and re-ingest? (y/n): "
        )
        if answer.strip().lower() != "y":
            console.print("Aborted.")
            sys.exit(0)

    # Load PDF
    documents = PyPDFLoader(pdf_path).load()

    # Split into chunks
    splitter = create_text_splitter()
    chunks = splitter.split_documents(documents)

    # Create embeddings for the configured provider
    embeddings = get_embeddings(provider)

    # Create vector store (pre_delete_collection=True since user confirmed or it's new)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection_string,
        use_jsonb=True,
        pre_delete_collection=True,
    )

    # Add documents with progress bar
    # Smaller batches + delay to stay within free-tier API rate limits
    batch_size = 5
    rate_limit_delay = int(os.getenv("INGEST_BATCH_DELAY", "4"))
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(
            f"Processing {Path(pdf_path).name}",
            total=len(chunks),
        )
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            vector_store.add_documents(batch)
            progress.advance(task, len(batch))
            # Delay between batches to respect API rate limits
            if i + batch_size < len(chunks):
                time.sleep(rate_limit_delay)

    console.print("[green]Done[/green]")


if __name__ == "__main__":
    ingest_pdf()
