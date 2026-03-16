# Phase 2: Semantic Search & Response - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Retrieve relevant chunks from pgVector using the same embedding model from ingestion, inject them into the assignment-specified prompt template, and send to the configured LLM to get a context-grounded answer. The interactive chat loop and rich formatting are Phase 3. Multi-provider flexibility is Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Score filtering
- No filtering — always use all top 10 chunks regardless of similarity scores
- Scores are retrieved per requirement (similarity_search_with_score) but discarded — only text content is passed forward
- Always send chunks to the LLM even for off-topic questions — trust the prompt template's refusal rule
- Hardcoded k=10, no env var override

### Context formatting
- Plain concatenation of chunks with double newline separator
- No numbering, no page metadata, no divider lines
- No deduplication — keep all 10 chunks as-is (150-char overlap is negligible)
- Ordered by similarity score (most relevant first) — default pgVector behavior

### Return shape
- search_prompt() returns a LangChain chain object (RetrievalQA or similar)
- chat.py invokes via chain.invoke({"query": question}) pattern
- search_prompt() handles initialization errors internally (env validation, DB connection test) and returns None on failure — consistent with ingest.py's error handling pattern
- search.py is independently runnable: `python src/search.py "question" [pdf_path]`
- Standalone mode accepts PDF name argument to find the right collection via get_collection_name(), defaults to document.pdf — matches ingest.py CLI pattern

### Claude's Discretion
- Whether to use LangChain RetrievalQA chain or a custom chain with PromptTemplate + LLM
- How to share utility functions between ingest.py and search.py (import vs shared module)
- LLM instantiation pattern (get_llm() function mirroring get_embeddings())
- Exact error messages for search-specific failures

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ingest.py`: `get_provider()`, `get_embeddings()`, `validate_env()`, `get_collection_name()`, `test_db_connection()` — all reusable for search
- `src/search.py`: PROMPT_TEMPLATE already defined with Portuguese rules and refusal examples, stub `search_prompt()` function
- `src/chat.py`: Already imports `search_prompt` from search and checks for None return
- Rich console pattern established in ingest.py (`Console(force_terminal=True)`, Panel for errors)

### Established Patterns
- Provider selection via `LLM_PROVIDER` env var with get_provider()
- Embedding model creation via get_embeddings() with per-provider branching
- LLM model env vars already defined: `OPENAI_LLM_MODEL`, `GOOGLE_LLM_MODEL`, `LMSTUDIO_LLM_MODEL`
- DB connection string from `DATABASE_URL` env var
- Collection naming from PDF filename via get_collection_name()
- Windows UTF-8 handling at module top

### Integration Points
- PGVector store connection must use same collection_name as ingest.py
- chat.py expects `search_prompt()` to return a chain or None
- .env.example already has all LLM model env vars configured

</code_context>

<specifics>
## Specific Ideas

No specific requirements — assignment constrains the prompt template (already in search.py), chunk count (k=10), and embedding model. Implementation follows established patterns from ingest.py.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-semantic-search-response*
*Context gathered: 2026-03-10*
