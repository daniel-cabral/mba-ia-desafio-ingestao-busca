# Phase 2: Semantic Search & Response - Research

**Researched:** 2026-03-10
**Domain:** LangChain RAG pipeline (retrieval + response generation)
**Confidence:** HIGH

## Summary

Phase 2 implements the core RAG loop: vectorize a user question using the same embedding model from ingestion, retrieve the top 10 similar chunks from pgVector, inject them into the assignment-specified Portuguese prompt template (already defined in `src/search.py`), and send to the configured LLM. The existing codebase has all utility functions needed (`get_provider()`, `get_embeddings()`, `validate_env()`, `get_collection_name()`, `test_db_connection()`) in `src/ingest.py`, plus the `PROMPT_TEMPLATE` and stub `search_prompt()` in `src/search.py`, and the consumer `src/chat.py` that expects `search_prompt()` to return a chain or None.

The key technical decision is how to build the chain. `RetrievalQA` is deprecated since LangChain 0.1.17. The modern replacement is `create_retrieval_chain` + `create_stuff_documents_chain`, but these expect `{context}` and `{input}` variable names while the assignment template uses `{contexto}` and `{pergunta}`. The cleanest approach is a simple LCEL chain that manually retrieves chunks, formats them into the existing template, and calls the LLM -- avoiding framework assumptions and keeping the assignment template untouched.

**Primary recommendation:** Build a simple LCEL pipeline using `PromptTemplate` + LLM with manual retrieval via `vector_store.similarity_search_with_score()`, keeping full control over the assignment-specified template variables `{contexto}` and `{pergunta}`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Score filtering:** No filtering -- always use all top 10 chunks regardless of similarity scores. Scores are retrieved (similarity_search_with_score) but discarded -- only text content is passed forward. Always send chunks to the LLM even for off-topic questions. Hardcoded k=10, no env var override.
- **Context formatting:** Plain concatenation of chunks with double newline separator. No numbering, no page metadata, no divider lines. No deduplication. Ordered by similarity score (most relevant first).
- **Return shape:** `search_prompt()` returns a LangChain chain object (RetrievalQA or similar). `chat.py` invokes via `chain.invoke({"query": question})` pattern. `search_prompt()` handles initialization errors internally and returns None on failure. `search.py` is independently runnable: `python src/search.py "question" [pdf_path]`. Standalone mode accepts PDF name argument to find the right collection via `get_collection_name()`, defaults to `document.pdf`.

### Claude's Discretion
- Whether to use LangChain RetrievalQA chain or a custom chain with PromptTemplate + LLM
- How to share utility functions between ingest.py and search.py (import vs shared module)
- LLM instantiation pattern (get_llm() function mirroring get_embeddings())
- Exact error messages for search-specific failures

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RETR-01 | User question is vectorized using the same embedding model used during ingestion | Reuse `get_embeddings()` from ingest.py; PGVector store initialized with same embeddings handles vectorization automatically |
| RETR-02 | Top 10 most similar chunks are retrieved via similarity_search_with_score (k=10) | PGVector `similarity_search_with_score(query, k=10)` returns list of (Document, score) tuples |
| RETR-03 | Retrieved context is injected into the exact prompt template defined in the assignment | PROMPT_TEMPLATE already exists in search.py with `{contexto}` and `{pergunta}` variables; use PromptTemplate with these vars |
| RESP-01 | Prompt with context and question is sent to configured LLM | `get_llm()` function creates ChatOpenAI/ChatGoogleGenerativeAI per provider; chain pipes prompt to LLM |
| RESP-02 | LLM responds based only on provided context | Enforced by PROMPT_TEMPLATE's REGRAS section (rules) |
| RESP-03 | Out-of-context questions receive standard refusal message in Portuguese | PROMPT_TEMPLATE includes refusal rule and examples; LLM should follow instructions |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain | 0.3.27 | Chain orchestration, PromptTemplate | Core framework |
| langchain-core | 0.3.74 | PromptTemplate, StrOutputParser, RunnableLambda | LCEL primitives |
| langchain-postgres | 0.0.15 | PGVector vector store with as_retriever() | pgVector integration |
| langchain-openai | 0.3.30 | ChatOpenAI for OpenAI/LMStudio LLM | OpenAI chat models |
| langchain-google-genai | 2.1.9 | ChatGoogleGenerativeAI for Gemini LLM | Google Gemini models |
| python-dotenv | 1.1.1 | Load .env file | Environment management |
| rich | 14.0.0 | Console output, error panels | Already used in ingest.py |

### No New Dependencies Needed
All required packages are already in requirements.txt. No additional installs.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom LCEL chain | RetrievalQA.from_chain_type | RetrievalQA is deprecated since 0.1.17; still works in 0.3.x but may be removed |
| Custom LCEL chain | create_retrieval_chain | Expects `{context}`/`{input}` vars, clashes with Portuguese template `{contexto}`/`{pergunta}` |
| Manual retrieval + format | as_retriever() in chain | Less control over score retrieval and context formatting |

**Recommendation:** Use a custom LCEL chain with manual retrieval. This avoids deprecated APIs, preserves the assignment template variables, and keeps the code simple and educational.

## Architecture Patterns

### Recommended Project Structure
```
src/
    ingest.py       # Existing -- imports shared by search.py
    search.py       # PROMPT_TEMPLATE + search_prompt() + get_llm() + standalone CLI
    chat.py         # Existing -- calls search_prompt() and invokes chain
```

### Pattern 1: Import Shared Utilities from ingest.py
**What:** Import `get_provider`, `get_embeddings`, `validate_env`, `get_collection_name`, `test_db_connection` directly from `ingest`
**When to use:** When functions are stable and well-defined (they are)
**Example:**
```python
from ingest import (
    get_provider,
    get_embeddings,
    validate_env,
    get_collection_name,
    test_db_connection,
    console,
)
```
**Rationale:** These are all pure utility functions with no side effects at import time. The `ingest_pdf()` function only runs under `if __name__ == "__main__"`. A shared module would be premature -- there are only two consumers.

### Pattern 2: get_llm() Mirroring get_embeddings()
**What:** A provider-branching factory function that creates the appropriate LLM chat model
**When to use:** Always -- follows established pattern from ingest.py
**Example:**
```python
def get_llm(provider: str):
    """Create the LLM chat model for the configured provider."""
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        model = os.getenv("OPENAI_LLM_MODEL", "gpt-5-nano")
        return ChatOpenAI(model=model)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash-lite")
        return ChatGoogleGenerativeAI(model=model)
    elif provider == "lmstudio":
        from langchain_openai import ChatOpenAI
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        model = os.getenv("LMSTUDIO_LLM_MODEL", "local-model")
        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key="lm-studio",
        )
```

### Pattern 3: Custom LCEL Chain with Manual Retrieval
**What:** Build the chain as a RunnableLambda that retrieves, formats, prompts, and parses
**When to use:** When the prompt template has non-standard variable names or you need fine control
**Example:**
```python
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["contexto", "pergunta"],
)

# The chain function
def _run_chain(inputs: dict, vector_store, llm) -> str:
    query = inputs.get("query", "")
    # RETR-02: retrieve top 10 with scores
    results = vector_store.similarity_search_with_score(query, k=10)
    # Context formatting: plain concatenation, double newline
    contexto = "\n\n".join(doc.page_content for doc, _score in results)
    # RETR-03: inject into assignment template
    formatted = prompt.format(contexto=contexto, pergunta=query)
    # RESP-01: send to LLM
    response = llm.invoke(formatted)
    return response.content
```

### Pattern 4: Wrapping as Invocable Chain
**What:** Return an object that supports `.invoke({"query": question})` as chat.py expects
**When to use:** To satisfy the contract with chat.py
**Example:**
```python
from langchain_core.runnables import RunnableLambda

def search_prompt(question=None):
    # ... initialization, env validation, DB test ...
    # Build the chain
    chain = RunnableLambda(lambda inputs: _run_chain(inputs, vector_store, llm))

    # If called with a question directly (standalone mode), run it
    if question:
        result = chain.invoke({"query": question})
        console.print(result)
        return None  # Don't return chain in standalone mode

    return chain  # Return chain for chat.py to use
```

### Pattern 5: Standalone CLI Mode
**What:** `python src/search.py "question" [pdf_path]` runs a single query
**When to use:** For testing and standalone usage, matching ingest.py CLI pattern
**Example:**
```python
if __name__ == "__main__":
    pdf_name = sys.argv[2] if len(sys.argv) > 2 else "document.pdf"
    question = sys.argv[1] if len(sys.argv) > 1 else None
    if not question:
        console.print("Usage: python src/search.py \"question\" [pdf_path]")
        sys.exit(1)
    search_prompt(question=question)
```

### Anti-Patterns to Avoid
- **Using RetrievalQA:** Deprecated since 0.1.17; will break in a future LangChain update
- **Renaming template variables:** The assignment specifies exact template -- do not change `{contexto}` to `{context}`
- **Filtering by score:** Decision is locked -- always pass all 10 chunks to LLM
- **Building a shared utils module:** Premature abstraction with only 2 consumers; direct import is simpler
- **Using sys.exit() inside search_prompt():** chat.py checks for None return -- raise/catch internally and return None

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Embedding vectorization | Custom embedding code | PGVector's similarity_search handles vectorization | Already vectorizes the query internally |
| Similarity search | Raw SQL cosine distance | PGVector.similarity_search_with_score() | Handles index, distance calc, returns Documents |
| LLM API calls | Raw HTTP to OpenAI/Gemini | ChatOpenAI / ChatGoogleGenerativeAI | Handles auth, retries, parsing, streaming |
| Prompt formatting | f-string with manual escaping | PromptTemplate.format() | Validates variables, handles edge cases |

**Key insight:** LangChain already wraps every API call this pipeline needs. The only "custom" part is the glue between retrieval and prompting, which is intentionally simple.

## Common Pitfalls

### Pitfall 1: Collection Name Mismatch
**What goes wrong:** Search fails to find any chunks because it uses a different collection name than ingestion
**Why it happens:** Different PDF path handling or hardcoded names
**How to avoid:** Import and use the exact same `get_collection_name()` from ingest.py with the same PDF path logic
**Warning signs:** Empty results from similarity search

### Pitfall 2: Connection String Format
**What goes wrong:** PGVector fails with psycopg2 vs psycopg3 mismatch
**Why it happens:** langchain-postgres 0.0.15 requires psycopg3 format (`postgresql+psycopg://`)
**How to avoid:** Use same DATABASE_URL env var as ingest.py -- it already works
**Warning signs:** SQLAlchemy connection errors mentioning psycopg

### Pitfall 3: Import Path for src/ Modules
**What goes wrong:** `from ingest import ...` fails when running from project root
**Why it happens:** Python path doesn't include `src/` directory
**How to avoid:** Run with `python src/search.py` (same directory as ingest.py), or use relative import. Since chat.py already does `from search import search_prompt`, the pattern is established -- scripts run from within `src/` or the directory is on the path.
**Warning signs:** ModuleNotFoundError for ingest

### Pitfall 4: LLM Model Names May Not Exist Yet
**What goes wrong:** API rejects model name (gpt-5-nano, gemini-2.5-flash-lite)
**Why it happens:** These are specified in .env.example but model availability depends on provider/API access
**How to avoid:** Use env vars for model names (already configured in .env.example), so users can override. This is already noted as a STATE.md research concern for Phase 4.
**Warning signs:** 404 or model-not-found API errors

### Pitfall 5: PromptTemplate Brace Escaping
**What goes wrong:** PromptTemplate raises error on curly braces in template text
**Why it happens:** Template string may contain literal `{` or `}` that aren't variables
**How to avoid:** The existing PROMPT_TEMPLATE only has `{contexto}` and `{pergunta}` -- no literal braces. Just pass these as `input_variables`.
**Warning signs:** KeyError or validation error from PromptTemplate

### Pitfall 6: ChatModel Returns AIMessage, Not String
**What goes wrong:** Chain returns an AIMessage object instead of a string
**Why it happens:** ChatOpenAI/ChatGoogleGenerativeAI return AIMessage; need `.content` property
**How to avoid:** Either access `.content` on the response, or pipe through `StrOutputParser()` in the LCEL chain
**Warning signs:** Output shows `AIMessage(content="...")` instead of just the text

## Code Examples

### Complete search_prompt() Implementation Pattern
```python
# Source: Verified against LangChain 0.3.x API docs
import os
import sys
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_postgres import PGVector

from ingest import (
    get_provider, get_embeddings, validate_env,
    get_collection_name, test_db_connection, console,
)

PROMPT_TEMPLATE = """..."""  # Already defined

def get_llm(provider: str):
    """Create the LLM chat model for the configured provider."""
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        model = os.getenv("OPENAI_LLM_MODEL", "gpt-5-nano")
        return ChatOpenAI(model=model)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash-lite")
        return ChatGoogleGenerativeAI(model=model)
    elif provider == "lmstudio":
        from langchain_openai import ChatOpenAI
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        model = os.getenv("LMSTUDIO_LLM_MODEL", "local-model")
        return ChatOpenAI(model=model, base_url=base_url, api_key="lm-studio")

def search_prompt(question=None):
    """Build and optionally run the RAG search chain."""
    try:
        load_dotenv()
        provider = get_provider()
        validate_env(provider)

        connection_string = os.environ["DATABASE_URL"]
        test_db_connection(connection_string)

        # Determine PDF path for collection name
        pdf_path = sys.argv[2] if len(sys.argv) > 2 else "document.pdf"
        collection_name = get_collection_name(pdf_path)

        embeddings = get_embeddings(provider)
        llm = get_llm(provider)

        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=connection_string,
            use_jsonb=True,
        )

        prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["contexto", "pergunta"],
        )

        def _run(inputs: dict) -> str:
            query = inputs.get("query", "")
            results = vector_store.similarity_search_with_score(query, k=10)
            contexto = "\n\n".join(doc.page_content for doc, _score in results)
            formatted = prompt.format(contexto=contexto, pergunta=query)
            response = llm.invoke(formatted)
            return response.content

        chain = RunnableLambda(_run)

        if question:
            result = chain.invoke({"query": question})
            console.print(result)
            return None

        return chain
    except Exception as e:
        console.print(Panel(str(e), title="[red]Error[/red]", border_style="red"))
        return None
```

### Invoking from chat.py (already implemented)
```python
chain = search_prompt()
if chain:
    result = chain.invoke({"query": "Qual o tema principal do documento?"})
    print(result)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| RetrievalQA.from_chain_type() | create_retrieval_chain() or LCEL | LangChain 0.1.17 (2024) | RetrievalQA deprecated, still functional in 0.3.x |
| StuffDocumentsChain class | create_stuff_documents_chain() function | LangChain 0.2.x | Class-based chains replaced by function constructors |
| LLMChain + PromptTemplate | LCEL pipe operator (prompt \| llm \| parser) | LangChain 0.2.x | More composable, streamable |

**Deprecated/outdated:**
- `RetrievalQA`: Deprecated since 0.1.17, will be removed in 0.3.0+. Still works but emits deprecation warnings.
- `LLMChain`: Replaced by LCEL pipe patterns.

## Open Questions

1. **validate_env() calls sys.exit() on failure**
   - What we know: search_prompt() should return None on failure, not exit
   - What's unclear: Whether to duplicate validate_env() or wrap with try/except
   - Recommendation: Wrap the entire init block in try/except and catch SystemExit, converting to None return. This preserves ingest.py's function unchanged.

2. **PGVector store initialization without pre_delete_collection**
   - What we know: ingest.py uses `pre_delete_collection=True` for fresh ingestion
   - What's unclear: Whether PGVector constructor needs explicit `pre_delete_collection=False` for read-only use
   - Recommendation: Simply omit the parameter (defaults to False). Verified: PGVector constructor defaults to not deleting.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual validation (no test framework installed) |
| Config file | none -- see Wave 0 |
| Quick run command | `python src/search.py "Qual o tema principal?" document.pdf` |
| Full suite command | Manual: run search with on-topic and off-topic questions |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RETR-01 | Question vectorized with same embedding model | integration | `python src/search.py "test question"` | N/A -- verified by successful retrieval |
| RETR-02 | Top 10 chunks retrieved with scores | integration | `python src/search.py "test question"` | N/A -- add print of chunk count for verification |
| RETR-03 | Context injected into assignment template | integration | `python src/search.py "Qual o tema principal?"` | N/A -- verified by LLM receiving correct prompt |
| RESP-01 | Prompt sent to configured LLM | integration | `python src/search.py "Qual o tema principal?"` | N/A -- verified by receiving response |
| RESP-02 | LLM responds based on context only | manual | Ask on-topic question, verify answer references PDF content | N/A |
| RESP-03 | Off-topic gets Portuguese refusal | manual | `python src/search.py "Qual a capital da Franca?"` | N/A |

### Sampling Rate
- **Per task commit:** `python src/search.py "Qual o tema principal?" document.pdf`
- **Per wave merge:** Run both on-topic and off-topic questions, verify responses
- **Phase gate:** All 6 requirements verified manually before completion

### Wave 0 Gaps
- No test framework needed -- this phase is validated via CLI integration tests (running the script with questions)
- Verification is inherently manual since it requires LLM API access and a running PostgreSQL with ingested data

## Sources

### Primary (HIGH confidence)
- [LangChain RetrievalQA API Reference](https://api.python.langchain.com/en/latest/chains/langchain.chains.retrieval_qa.base.RetrievalQA.html) - Deprecation notice, replacement guidance
- [LangChain create_retrieval_chain](https://api.python.langchain.com/en/latest/chains/langchain.chains.retrieval.create_retrieval_chain.html) - Modern replacement API
- [LangChain create_stuff_documents_chain](https://api.python.langchain.com/en/latest/chains/langchain.chains.combine_documents.stuff.create_stuff_documents_chain.html) - document_variable_name parameter
- [langchain-postgres PGVector](https://python.langchain.com/api_reference/postgres/vectorstores/langchain_postgres.vectorstores.PGVector.html) - similarity_search_with_score API
- [ChatGoogleGenerativeAI](https://python.langchain.com/api_reference/google_genai/chat_models/langchain_google_genai.chat_models.ChatGoogleGenerativeAI.html) - Model parameter usage

### Secondary (MEDIUM confidence)
- [LangChain PGVector Integration Guide](https://python.langchain.com/docs/integrations/vectorstores/pgvector/) - as_retriever() patterns
- [LangChain PromptTemplate](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.prompt.PromptTemplate.html) - Template variable handling

### Tertiary (LOW confidence)
- Model name availability (gpt-5-nano, gemini-2.5-flash-lite) -- flagged for Phase 4 validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed and used in Phase 1; versions confirmed from requirements.txt
- Architecture: HIGH - Pattern directly extends ingest.py's established patterns; LCEL is well-documented
- Pitfalls: HIGH - Based on direct code analysis and API documentation review

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable -- LangChain 0.3.x is current stable line)
