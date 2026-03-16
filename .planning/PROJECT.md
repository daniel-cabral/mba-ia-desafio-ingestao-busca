# PDF Semantic Search (RAG Pipeline)

## What This Is

A CLI-based RAG (Retrieval-Augmented Generation) application that ingests a PDF document into PostgreSQL with pgVector and lets users ask questions via terminal, receiving answers grounded strictly in the PDF's content. Built as a university assignment (MBA IA — Full Cycle) using Python and LangChain.

## Core Value

Users can ask natural language questions about a PDF and get accurate answers based exclusively on the document's content — never hallucinated or invented information.

## Requirements

### Validated

- ✓ Project structure (src/ingest.py, src/search.py, src/chat.py) — existing
- ✓ Docker Compose for PostgreSQL 17 + pgVector — existing
- ✓ Prompt template with strict context-only rules — existing
- ✓ requirements.txt with all dependencies pinned — existing

### Active

- [ ] PDF ingestion: load PDF, split into 1000-char chunks with 150 overlap, embed and store in pgVector
- [ ] Semantic search: vectorize question, retrieve top 10 similar chunks via similarity_search_with_score
- [ ] LLM response: construct prompt with retrieved context, call LLM, return answer
- [ ] CLI chat loop: interactive terminal for continuous Q&A
- [ ] Dual provider support: OpenAI (text-embedding-3-small + gpt-5-nano) and Gemini (embedding-001 + gemini-2.5-flash-lite), switchable via env var
- [ ] Accept any PDF path as CLI argument (not just hardcoded document.pdf)
- [ ] Refuse out-of-context questions with standard message

### Out of Scope

- Web UI — assignment requires CLI only
- Multi-document search — single PDF at a time
- Conversation memory — each question is independent
- Authentication/authorization — local tool only
- Deployment/production hosting — runs locally with Docker

## Context

- University assignment for MBA IA (Full Cycle DevOps)
- Existing scaffold: stub functions in all 3 scripts, prompt template already defined in search.py
- PostgreSQL 17 + pgVector runs via docker-compose.yml with auto-bootstrap of vector extension
- The included document.pdf is the reference test document
- All instructions are in Portuguese (Brazilian)
- The assignment specifies exact chunk size (1000), overlap (150), k value (10), and prompt template

## Constraints

- **Tech stack**: Python + LangChain + PostgreSQL/pgVector — assignment requirement
- **Project structure**: Must follow src/ingest.py, src/search.py, src/chat.py — assignment requirement
- **Prompt template**: Must use the exact template defined in instructions — assignment requirement
- **Chunking**: 1000 chars, 150 overlap — assignment requirement
- **Retrieval**: k=10 similarity search — assignment requirement
- **Models (OpenAI)**: text-embedding-3-small + gpt-5-nano — assignment requirement
- **Models (Gemini)**: models/embedding-001 + gemini-2.5-flash-lite — assignment requirement

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Support both OpenAI and Gemini | User wants flexibility between providers | — Pending |
| Accept PDF path as argument | More flexible than hardcoded path | — Pending |
| Build on existing scaffold | Preserve template repo structure, fill in stubs | — Pending |

---
*Last updated: 2026-03-08 after initialization*
