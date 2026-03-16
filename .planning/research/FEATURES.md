# Feature Landscape

**Domain:** RAG Pipeline / PDF Semantic Search CLI (University Assignment)
**Researched:** 2026-03-08

## Context

This is a university assignment (MBA IA -- Full Cycle) with a fixed specification. The assignment dictates exact technology choices, file structure, chunking parameters, prompt template, and models. "Table stakes" here means "what the assignment requires to pass" and "differentiators" means "what earns a higher grade or demonstrates deeper understanding without violating constraints."

## Table Stakes

Features the assignment explicitly requires. Missing any of these = incomplete submission.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| PDF ingestion via PyPDFLoader | Assignment requirement (explicit import specified) | Low | LangChain community loader, straightforward API |
| Chunk splitting (1000 chars, 150 overlap) | Assignment specifies exact parameters | Low | RecursiveCharacterTextSplitter with fixed config |
| Embedding generation | Core of the RAG pipeline | Low | OpenAIEmbeddings or GoogleGenerativeAIEmbeddings, one-liner with LangChain |
| pgVector storage via PGVector | Assignment specifies PostgreSQL + pgVector | Medium | langchain_postgres.PGVector handles schema creation; connection string setup needs care |
| Similarity search (k=10) with scores | Assignment specifies `similarity_search_with_score(query, k=10)` | Low | Single method call on the vector store |
| Prompt construction with exact template | Assignment provides the exact prompt template in Portuguese | Low | Template already exists in search.py, just needs context injection |
| LLM call for answer generation | Core RAG retrieval-then-generate step | Low | LangChain chain or direct invoke with prompt |
| Out-of-context refusal | Assignment requires standard refusal message (built into prompt template) | Low | Handled by the prompt rules; no code needed beyond the prompt |
| Interactive CLI chat loop | Assignment says "simular um chat no terminal" | Low | while-True loop with input(), print response, repeat |
| OpenAI provider (text-embedding-3-small + gpt-4.1-nano) | Assignment requirement | Low | Standard LangChain OpenAI integration |
| Docker Compose for PostgreSQL | Assignment provides docker-compose.yml (already exists) | Low | Already done in scaffold |
| .env for API keys | Assignment mentions .env.example | Low | python-dotenv already in requirements |

## Differentiators

Features NOT required by the assignment but that demonstrate competence, earn better grades, or make the tool genuinely useful. None of these should violate the assignment constraints.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dual provider support (OpenAI + Gemini) | Shows flexibility; assignment lists both as options | Medium | Requires env-var-based switching for both embeddings and LLM; must ensure embeddings from one provider are not mixed with another's vector store |
| Accept PDF path as CLI argument | More flexible than hardcoded `document.pdf` | Low | `sys.argv[1]` or argparse; falls back to env var PDF_PATH or default |
| Ingestion progress feedback | User sees chunks being processed instead of silent wait | Low | tqdm is already in requirements.txt; wrap chunk loop |
| Clear error messages for missing config | User knows immediately if API key or DB is missing | Low | Check env vars at startup, print actionable error |
| Collection name from PDF filename | Avoids overwriting vectors when ingesting different PDFs | Low | Derive collection name from PDF basename |
| Re-ingestion guard | Skip ingestion if PDF already loaded (same collection exists) | Medium | Check if collection exists and has documents; prompt user to confirm overwrite |
| Relevance score display | Show similarity scores alongside answers so user can gauge confidence | Low | Data already returned by `similarity_search_with_score`; just format and print |
| Source chunk display | Show which chunks contributed to the answer | Low | Print the page numbers or chunk indices used for context |
| Graceful shutdown | Handle Ctrl+C cleanly in chat loop | Low | try/except KeyboardInterrupt with goodbye message |
| README with clear execution instructions | Assignment deliverable requires README with "instrucoes claras" | Low | Document setup, env vars, and run commands |

## Anti-Features

Features to explicitly NOT build. Either they violate assignment constraints, add unnecessary complexity, or distract from the core deliverable.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Web UI / API server | Assignment explicitly requires CLI only | Keep it terminal-based with input()/print() |
| Multi-document search | Out of scope per PROJECT.md; complicates vector store management | Single PDF per ingestion run |
| Conversation memory / chat history | Assignment treats each question independently; adding memory changes the prompt behavior | Each question is stateless; no message history |
| Custom embedding models / fine-tuning | Assignment specifies exact models | Use text-embedding-3-small (OpenAI) or embedding-001 (Gemini) as-is |
| Authentication / user management | Local tool, no users | None needed |
| Async / streaming responses | Over-engineering for a CLI assignment | Synchronous calls are fine; simpler to debug |
| Custom vector similarity algorithms | pgVector handles this; assignment uses default cosine similarity | Use PGVector defaults |
| Chunking strategy experimentation | Assignment specifies exact params (1000/150) | Use RecursiveCharacterTextSplitter with fixed values |
| Deployment / CI/CD | Assignment is local-only; deliverable is a GitHub repo | Just ensure `docker compose up` + `python src/*.py` works |
| LangSmith tracing / observability | Adds complexity and external dependency for no assignment benefit | Skip tracing config; langsmith is a transitive dep but does not need to be configured |
| Prompt engineering beyond template | Assignment provides the exact prompt; changing it risks deviating from requirements | Use the provided template verbatim |

## Feature Dependencies

```
Docker Compose (PostgreSQL + pgVector)
  --> PDF Ingestion (needs DB to store vectors)
    --> Semantic Search (needs stored vectors to query)
      --> LLM Response Generation (needs search results as context)
        --> CLI Chat Loop (needs the full chain to function)

Provider Selection (env var)
  --> Embedding Model Selection
  --> LLM Model Selection
  (Both must use same provider to avoid dimension mismatch in vectors)
```

Key dependency insight: **Embedding provider and LLM provider must match per session.** You cannot embed with OpenAI and query with Gemini because the vector dimensions and representations differ. The vector store collection should be provider-specific.

## MVP Recommendation

The assignment IS the MVP. Prioritize in this order:

1. **PDF ingestion with OpenAI embeddings** -- get vectors into pgVector first (validates the full storage pipeline)
2. **Semantic search** -- query those vectors and confirm relevant chunks come back
3. **LLM response with prompt template** -- wire up the chain from search results to LLM answer
4. **CLI chat loop** -- wrap everything in the interactive terminal experience
5. **Gemini provider support** -- add as second provider once OpenAI path works end-to-end
6. **Polish** -- CLI argument for PDF path, progress feedback, error messages, README

Defer: Re-ingestion guard, relevance score display, source chunk display. These are nice-to-have but not graded.

## Sources

- Assignment instructions: `docs/instrucoes.md` (primary source of truth for all requirements)
- Project context: `.planning/PROJECT.md`
- Existing scaffold: `src/ingest.py`, `src/search.py`, `src/chat.py`
- LangChain documentation (for API patterns referenced in assignment imports)
