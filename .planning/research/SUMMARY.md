# Research Summary: PDF Semantic Search (RAG Pipeline)

**Domain:** RAG (Retrieval-Augmented Generation) CLI application
**Researched:** 2026-03-08
**Overall confidence:** MEDIUM-HIGH (stack is assignment-constrained and well-known; web verification was unavailable)

## Executive Summary

This is a straightforward RAG pipeline with a constrained tech stack (Python, LangChain 0.3.x, PostgreSQL 17 with pgVector). The assignment prescribes specific chunking parameters (1000 chars, 150 overlap), retrieval settings (k=10), models (OpenAI text-embedding-3-small + gpt-4.1-nano, Gemini embedding-001 + gemini-2.5-flash-lite), and project structure (ingest.py, search.py, chat.py).

The scaffold already exists with stub functions, docker-compose is configured, and requirements.txt has all dependencies pinned. The implementation work is filling in three Python files with well-established LangChain patterns. The main technical risk is using the correct langchain-postgres API (not the deprecated community version) and getting the psycopg3 connection string format right.

The dual-provider requirement (OpenAI vs Gemini) adds a small layer of complexity: embeddings are not interchangeable between providers because vector dimensions differ. The system must either use separate collections per provider or require re-ingestion when switching providers.

The prompt template is already defined in search.py in Portuguese, enforcing context-only answers. The architecture is simple: load PDF, chunk it, embed chunks into pgVector, then at query time embed the question, retrieve top-10 similar chunks, format them into the prompt, and call the LLM.

## Key Findings

**Stack:** LangChain 0.3.27 + langchain-postgres 0.0.15 + psycopg3 + pypdf. All pinned in requirements.txt.
**Architecture:** Three-file pipeline (ingest -> search -> chat). No complex chains needed; manual retrieve-then-prompt is cleanest.
**Critical pitfall:** Using the deprecated `langchain_community.vectorstores.PGVector` instead of `langchain_postgres.PGVector`, or using psycopg2 connection strings with langchain-postgres.

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Phase 1: PDF Ingestion** - Implement ingest.py
   - Addresses: PDF loading, text splitting, embedding, pgVector storage
   - Avoids: Mixing providers in same collection
   - This must come first because search depends on having data in the vector store

2. **Phase 2: Search & Retrieval** - Implement search.py
   - Addresses: Query embedding, similarity search, prompt formatting, LLM call
   - Depends on: Phase 1 (needs ingested data to test)

3. **Phase 3: Chat CLI** - Implement chat.py
   - Addresses: Interactive loop, user input, display answers
   - Depends on: Phase 2 (needs working search_prompt function)

4. **Phase 4: Dual Provider Support** - Add Gemini as alternative
   - Addresses: Provider switching via env var
   - Can be woven into earlier phases or done as a final pass

**Phase ordering rationale:**
- Strictly sequential dependency: ingest -> search -> chat
- Each phase is independently testable
- Dual provider support can be integrated at any point but is cleanest as a cross-cutting concern applied after the OpenAI path works

**Research flags for phases:**
- Phase 1: Verify langchain-postgres table creation behavior (does it auto-create? does it need explicit setup?)
- Phase 4: Verify gpt-4.1-nano and gemini-2.5-flash-lite model availability (newer model names)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions pinned in requirements.txt; LangChain 0.3.x patterns well-known |
| Features | HIGH | Assignment specifies exact requirements; no ambiguity |
| Architecture | HIGH | Three-file structure is prescribed; RAG pattern is standard |
| Pitfalls | MEDIUM | Based on training data patterns; could not verify against latest docs |

## Gaps to Address

- Could not verify latest langchain-postgres 0.0.15 API changes via official docs (web tools were restricted)
- Model names gpt-4.1-nano and gemini-2.5-flash-lite should be verified at implementation time
- Gemini embedding-001 dimension count (768d) should be confirmed
