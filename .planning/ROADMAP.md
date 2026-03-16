# Roadmap: PDF Semantic Search (RAG Pipeline)

## Overview

This project implements a CLI-based RAG pipeline that ingests a PDF into PostgreSQL/pgVector and answers natural language questions grounded in the document's content. The roadmap follows the natural data flow: first get data into the vector store, then build search and response on top of it, then wrap it in an interactive CLI, then add multi-provider flexibility, and finally add documentation for the educational context.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: PDF Ingestion Pipeline** - Load, chunk, embed, and store PDF content in pgVector
- [ ] **Phase 2: Semantic Search & Response** - Retrieve relevant chunks and generate context-grounded answers
- [ ] **Phase 3: Interactive Chat CLI** - Terminal-based Q&A loop with rich formatting
- [ ] **Phase 4: Multi-Provider Support** - OpenAI, Gemini, and LM Studio as switchable providers
- [ ] **Phase 5: Documentation & Polish** - Educational comments, learning guide, and README

## Phase Details

### Phase 1: PDF Ingestion Pipeline
**Goal**: Users can ingest any PDF into the vector store with a single command
**Depends on**: Nothing (first phase)
**Requirements**: INGE-01, INGE-02, INGE-03, INGE-04, INGE-05
**Success Criteria** (what must be TRUE):
  1. User can run `python src/ingest.py document.pdf` and see chunks being processed with a progress indicator
  2. User can run `python src/ingest.py` with no argument and it defaults to `document.pdf`
  3. After ingestion completes, chunks exist in the PostgreSQL pgVector table (verifiable via psql query)
  4. Running ingestion a second time works without errors (idempotent or re-creates cleanly)
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Implement ingest.py with tests (core pipeline + unit tests)
- [ ] 01-02-PLAN.md — Integration verification and human UX review

### Phase 2: Semantic Search & Response
**Goal**: Users can ask a question and receive an answer grounded exclusively in the ingested PDF content
**Depends on**: Phase 1
**Requirements**: RETR-01, RETR-02, RETR-03, RESP-01, RESP-02, RESP-03
**Success Criteria** (what must be TRUE):
  1. User can call the search function with a question string and get back relevant chunks from the PDF
  2. The system constructs a prompt using the exact assignment-specified template with retrieved context injected
  3. The LLM returns an answer that references information from the PDF
  4. When asked a question unrelated to the PDF content, the system returns the standard refusal message in Portuguese
**Plans**: 1 plan

Plans:
- [ ] 02-01-PLAN.md — Implement RAG search chain (get_llm, search_prompt, standalone CLI)

### Phase 3: Interactive Chat CLI
**Goal**: Users can have a continuous Q&A session about the PDF in a polished terminal interface
**Depends on**: Phase 2
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04
**Success Criteria** (what must be TRUE):
  1. User can start the chat with `python src/chat.py` and enter questions in a loop, receiving answers after each one
  2. The terminal output uses colors, panels, and styled text (rich library) making it easy to distinguish questions from answers
  3. Pressing Ctrl+C exits gracefully with a friendly goodbye message instead of a traceback
  4. If the database is unreachable or env vars are missing, the user sees a clear error message explaining what to fix
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Multi-Provider Support
**Goal**: Users can choose between OpenAI, Gemini, or LM Studio as their LLM and embedding provider
**Depends on**: Phase 3
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05
**Success Criteria** (what must be TRUE):
  1. User can set `LLM_PROVIDER=openai` and the full pipeline (ingest + search + chat) works with text-embedding-3-small and gpt-5-nano
  2. User can set `LLM_PROVIDER=gemini` and the full pipeline works with embedding-001 and gemini-2.5-flash-lite
  3. User can set `LLM_PROVIDER=lmstudio` and the full pipeline works with user-chosen models via a configurable OpenAI-compatible base URL
  4. User can switch providers by changing the env var and re-ingesting, and the system handles this correctly
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: Documentation & Polish
**Goal**: The codebase serves as a learning resource with clear documentation for the university assignment
**Depends on**: Phase 4
**Requirements**: DOCS-01, DOCS-02, DOCS-03
**Success Criteria** (what must be TRUE):
  1. Each Python file contains inline comments explaining RAG concepts, LangChain usage, and design choices at key points
  2. A docs/GUIDE.md file exists that walks through the architecture and explains each component in educational detail
  3. README.md contains clear step-by-step execution instructions (setup, ingest, chat) that a new user can follow
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. PDF Ingestion Pipeline | 0/2 | Planning complete | - |
| 2. Semantic Search & Response | 0/1 | Planning complete | - |
| 3. Interactive Chat CLI | 0/? | Not started | - |
| 4. Multi-Provider Support | 0/? | Not started | - |
| 5. Documentation & Polish | 0/? | Not started | - |
