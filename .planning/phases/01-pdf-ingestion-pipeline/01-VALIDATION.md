---
phase: 1
slug: pdf-ingestion-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual verification + psql queries |
| **Config file** | none — no test framework in requirements.txt |
| **Quick run command** | `python src/ingest.py document.pdf` |
| **Full suite command** | `python src/ingest.py document.pdf && docker exec postgres_rag psql -U postgres -d rag -c "SELECT count(*) FROM langchain_pg_embedding;"` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python src/ingest.py document.pdf`
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must complete successfully
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INGE-01 | manual | `python src/ingest.py document.pdf` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | INGE-02 | manual | `python src/ingest.py document.pdf` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | INGE-03 | manual | `python src/ingest.py document.pdf` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | INGE-04 | manual | `docker exec postgres_rag psql -U postgres -d rag -c "SELECT count(*) FROM langchain_pg_embedding;"` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | INGE-05 | visual | `python src/ingest.py document.pdf` (observe progress bar) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] No test framework needed — validation is via running the script and checking DB state
- [ ] Docker must be running with PostgreSQL + pgVector

*Existing infrastructure (Docker + psql) covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PDF loaded and chunked | INGE-01, INGE-02 | Output visible in progress bar | Run ingest, observe chunk count matches expected |
| Embeddings stored in pgVector | INGE-03, INGE-04 | Requires DB query | `docker exec postgres_rag psql -U postgres -d rag -c "SELECT count(*) FROM langchain_pg_embedding;"` |
| Rich progress bar displays | INGE-05 | Visual verification | Run ingest, observe progress bar with filename, count, time |
| Re-ingestion with confirmation | INGE-01 | Interactive prompt | Run ingest twice, verify confirmation prompt appears |
| Default PDF path | INGE-01 | CLI behavior | Run `python src/ingest.py` without arguments |

---

## Validation Sign-Off

- [ ] All tasks have manual verification commands
- [ ] Sampling continuity: manual checks after each task
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
