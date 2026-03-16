---
phase: 2
slug: semantic-search-response
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual CLI integration (no test framework — LLM API + DB required) |
| **Config file** | none |
| **Quick run command** | `python src/search.py "Qual o tema principal?" document.pdf` |
| **Full suite command** | Run on-topic + off-topic questions manually |
| **Estimated runtime** | ~10 seconds (depends on LLM API latency) |

---

## Sampling Rate

- **After every task commit:** Run `python src/search.py "Qual o tema principal?" document.pdf`
- **After every plan wave:** Run both on-topic and off-topic questions, verify responses
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | RETR-01 | integration | `python src/search.py "test question"` | N/A | ⬜ pending |
| 02-01-02 | 01 | 1 | RETR-02 | integration | `python src/search.py "test question"` | N/A | ⬜ pending |
| 02-01-03 | 01 | 1 | RETR-03 | integration | `python src/search.py "Qual o tema principal?"` | N/A | ⬜ pending |
| 02-01-04 | 01 | 1 | RESP-01 | integration | `python src/search.py "Qual o tema principal?"` | N/A | ⬜ pending |
| 02-01-05 | 01 | 1 | RESP-02 | manual | Ask on-topic question, verify answer references PDF | N/A | ⬜ pending |
| 02-01-06 | 01 | 1 | RESP-03 | manual | `python src/search.py "Qual a capital da Franca?"` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- No test framework needed — validation is via CLI integration tests
- Verification requires LLM API access and running PostgreSQL with ingested data

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LLM answers from context only | RESP-02 | Requires human judgment to verify answer quality | Ask an on-topic question about the PDF, verify response references document content |
| Portuguese refusal for off-topic | RESP-03 | Requires human verification of refusal message | Ask "Qual a capital da Franca?" — expect "Não tenho informações necessárias para responder sua pergunta." |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
