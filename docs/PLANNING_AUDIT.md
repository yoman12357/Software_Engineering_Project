# Planning Audit — CyberSRS

**Version:** 0.1.0
**Date:** 2026-08-07
**Auditor:** Senior software architect / cybersecurity reviewer / RAG engineer / ML engineer / quality auditor
**Scope:** Complete planning foundation — README, AGENTS.md, all `docs/*.md`, all `docs/adr/*.md`
**Status:** Audit complete; corrections applied where noted

---

## 1. Executive Summary

CyberSRS is a well-structured, unusually mature Phase-0 planning repository for a single-student project. The canonical planning set (the versioned `0.1.0-draft` documents) is internally consistent across the most important dimensions: the fixed project invariants (single 4B Qwen model, 2×2 evaluation design, RAG ≠ fine-tuning split, local-first, JSON-first) are respected in every relevant document; the security foundations (15-threat STRIDE model, SEC-001–SEC-050, threat→mitigation→requirement traceability) are comprehensive; and the roadmap is correctly ordered with the non-AI skeleton and a mocked end-to-end flow before any real LLM work.

The audit found **no critical issues** in the canonical planning set and **one major documentation-completeness issue** (the master requirements catalogue does not contain SEC-008–SEC-050). All other findings are minor consistency notes or already-resolved-open decisions.

**Readiness rating: 87 / 100**

The repository is **ready for coding**. Phase 1A (non-AI backend foundation) may begin. No remaining planning issue blocks implementation.

---

## 2. Readiness Rating

| Dimension                                 | Score (0–10) | Notes                                                                                                |
| ----------------------------------------- | ------------ | ---------------------------------------------------------------------------------------------------- |
| Scope consistency (PRD ↔ SCOPE ↔ ROADMAP) | 9            | Canonical docs agree on 8 categories (CAT-01–CAT-08)                                                 |
| Requirement quality                       | 8            | 81 IDs in catalogue + 43 SEC IDs in SECURITY_REQUIREMENTS.md; SEC-008+ missing from master catalogue |
| Architecture consistency                  | 9            | Modular monolith, provider abstraction, JSON-first, deterministic/generative separation all defined  |
| Workflow consistency                      | 9            | Full workflow incl. error paths, unsupported-domain path, no manual domain selection                 |
| RAG design quality                        | 9            | Provenance, hashes, metadata, chunking, citations, stale-doc strategy, prompt-injection defence      |
| Fine-tuning quality                       | 9            | Distinct task categories, splits, leakage prevention, human review, rollback criteria                |
| Evaluation quality                        | 9            | Fixed set, 4 configurations, automated + human metrics, reproducible                                 |
| Security quality                          | 9            | Threat model, mitigations, requirement mapping, hard prohibitions                                    |
| Roadmap quality                           | 8            | Correct ordering; a few gate/backlog alignment notes                                                 |
| Academic feasibility                      | 8            | Ambitious but achievable; dataset size is the nearest constraint                                     |
| **Total**                                 | **87 / 100** |                                                                                                      |

---

## 3. Critical Issues

**None found in the canonical planning documents.**

---

## 4. Major Issues

### MAJ-01 — Master requirements catalogue omits SEC-008 through SEC-050

- `docs/SECURITY_REQUIREMENTS.md` defines SEC-008–SEC-050 (43 requirements, each testable, phased, threat-linked).
- `docs/REQUIREMENTS_CATALOG.md` contains only SEC-001–SEC-007 and claims a total of 81 requirements.
- The catalogue is defined as the "traceable master catalogue" and its verification section claims all PRD requirements are represented.
- **Fix applied:** Added a cross-reference note in `docs/REQUIREMENTS_CATALOG.md` stating that SEC-008–SEC-050 are maintained in `docs/SECURITY_REQUIREMENTS.md` and are considered part of the master set. The catalogue's scope note now records the true total (81 + 43 security requirements).
- **Preferred long-term fix (Phase 5 when SEC work starts):** either import all 43 rows into the catalogue or convert the catalogue to point to SECURITY_REQUIREMENTS.md as the authoritative source for SEC IDs.

### MAJ-02 — Stale document snapshots observed during audit

- During review, both an older, shorter snapshot and the canonical `0.1.0-draft` version of the same paths were observed (e.g., PRD, THREAT_MODEL, ROADMAP, RAG_DESIGN, FINETUNING_PLAN). The older snapshots reference a 12-category PRD, simple T-01–T-08 threats, 70/15/15 splits, and alternative roadmap phases.
- **Assessment:** The canonical `0.1.0-draft` documents are internally consistent with each other and with AGENTS.md/README. The stale snapshots are not in the current working tree after audit verification.
- **Action:** No file change required. Any future commit that reintroduces non-versioned duplicate content should be rejected in review.

---

## 5. Minor Issues

| ID     | Issue                                                                                                                                                                          | Recommendation                                                                                                                                   | Status   |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| MIN-01 | PRD success criterion SC-5 mentions "16 GB RAM, no GPU" while SCOPE §1.2 and PRD §19 state minimum ≥ 8 GB RAM.                                                                 | Treat 8 GB as minimum and 16 GB as the recommended/comfortable target; align SC-5 wording when PRD is next revised.                              | Recorded |
| MIN-02 | ROADMAP Phase 1 does not explicitly enumerate the mocked end-to-end flow; the flow exists only in IMPLEMENTATION_BACKLOG Epics 1–2.                                            | Leave as-is: IMPLEMENTATION_BACKLOG is the task-level source of truth; ROADMAP Phase 1 gate wording "no LLM calls, no generation" is compatible. | Recorded |
| MIN-03 | README phase-status list does not show the incremental baseline evaluations (C1 at Phase 3, C2 at Phase 4) that EVALUATION_PLAN §7 defines.                                    | Update README phase bullets when starting Phase 3 to mention "record C1 baseline".                                                               | Recorded |
| MIN-04 | The two duplicate file-versioning issue (MAJ-02) makes count-based auditing (e.g., "81 requirements") fragile.                                                                 | Add a documented requirement that all planning docs carry a `Version:` header; deprecate any un-versioned copy.                                  | Recorded |
| MIN-05 | UDEC-012 (chunk size) and UDEC-008 (chunking strategy) overlap in scope.                                                                                                       | Keep both, but note in DECISIONS.md that UDEC-008 is a superset decision resolved during Phase 4 experiments; UDEC-012 is its parameter.         | Recorded |
| MIN-06 | Chronological inconsistency: repository timestamps show documents dated 2026-08-07 authored in a single session; acceptable for Phase 0 but should be reviewed once per phase. | Add a "reviewed at phase gate" note to each document header as phases complete.                                                                  | Recorded |

---

## 6. Contradictions

| #      | Documents                                                               | Statement A                                           | Statement B                                                                   | Verdict                                                                                                                                                                                                                                                        |
| ------ | ----------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CON-01 | PRD SC-5 / SCOPE §1.2                                                   | "16 GB RAM, no GPU"                                   | "≥ 8 GB RAM, GPU recommended"                                                 | Minor wording conflict; interpret as minimum vs recommended (see MIN-01).                                                                                                                                                                                      |
| CON-02 | REQUIREMENTS_CATALOG §7/§10 vs SECURITY_REQUIREMENTS                    | "Total: 81"                                           | 43 additional SEC-008–SEC-050 defined                                         | Resolved via MAJ-01 fix (cross-reference note).                                                                                                                                                                                                                |
| CON-03 | PRD §23 item 9                                                          | "A QLoRA fine-tuned adapter exists" as MVP acceptance | FINETUNING_PLAN rollback criteria allow a null result (adapter not improving) | Intent: the fine-tuning _experiment and evaluation_ must exist; the adapter may be rolled back. Recommendation: reword PRD §23 item 9 to "A QLoRA fine-tuning run is performed and the result documented (adapter may be rolled back if it does not improve)". |
| CON-04 | KNOWLEDGE_BASE_PLAN §3 (14 docs) vs §3 in detailed version (15–25 docs) | 14 planned documents                                  | 15–25 estimated                                                               | Estimates, not contradictions; ranges are acceptable.                                                                                                                                                                                                          |

No other material contradictions found across the canonical set.

---

## 7. Missing Decisions

12 decisions are deliberately deferred in `docs/DECISIONS.md` (UDEC-001 … UDEC-012). **None blocks Phase 1A.**

| ID       | Decision                            | Needed by phase | Blocking Phase 1A?          |
| -------- | ----------------------------------- | --------------- | --------------------------- |
| UDEC-001 | Embedding model                     | 4               | No                          |
| UDEC-002 | PDF library                         | 6               | No                          |
| UDEC-003 | Adapter loading path (Ollama vs HF) | 8               | No                          |
| UDEC-004 | Fine-tuning comparison metrics      | 9               | No                          |
| UDEC-005 | React state management              | 1 (frontend)    | No (backend milestone only) |
| UDEC-006 | Prompt-engineering approach         | 2               | No                          |
| UDEC-007 | Sync vs async SRS generation        | 3               | No                          |
| UDEC-008 | Chunking strategy                   | 4               | No                          |
| UDEC-009 | Docker support                      | 10              | No                          |
| UDEC-010 | Project licence                     | 10              | No                          |
| UDEC-011 | PDF parser library                  | 4               | No                          |
| UDEC-012 | Optimal chunk size                  | 4               | No                          |

---

## 8. Scope Risks

| Risk                                                     | Assessment                                                                              | Mitigation                                                                                                                                                                       |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dataset creation effort (390–550 hand-reviewed examples) | **Highest schedule risk.** ~80–110 hours of human curation on top of application build. | Backlog T-140 is scheduled in Phase 7, after the core app; dataset card documents limits; PROMPT/PROMPT_AND_OUTPUT allows RAG-assisted draft generation to accelerate authoring. |
| Eight-category domain inference quality with a 4B model  | Medium.                                                                                 | Clarification loop + schema validation + retry; unsupported-domain path defined.                                                                                                 |
| 10-minute generation target on CPU-only hardware         | Medium; 7+ sectioned LLM calls on a 4B model may exceed this.                           | NFR-020 is "Should"; latency is measured, not gated; async status endpoint allows long runs.                                                                                     |
| Knowledge-base licensing (ISO 27001/27002)               | KB-Q2 unresolved; plan allows omission.                                                 | OWASP/NIST/MITRE/CIS provide sufficient MVP coverage without ISO.                                                                                                                |

---

## 9. Security Risks

| Risk                                                 | Assessment                 | Mitigation (documented)                                                                      |
| ---------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------- |
| Prompt injection via description/answers             | High threat, well-covered. | SEC-012, SEC-018, SEC-020; delimited `<retrieved_context>`; schema validation as final gate. |
| RAG knowledge-base poisoning                         | High threat, well-covered. | SEC-013–SEC-017, SEC-021–SEC-022, SEC-037; source manifest + hashes; operator approval.      |
| Unsafe generated content (exploit-like requirements) | High threat, well-covered. | SEC-004, SEC-025; safety guardrails; disclaimer; user-review workflow.                       |
| Model/adapter tampering                              | Covered.                   | SEC-035, SEC-036 (hash verification).                                                        |
| PDF injection                                        | Covered.                   | SEC-044, SEC-045; JSON-only rendering.                                                       |
| Log leakage of sensitive project text                | Covered.                   | SEC-031, SEC-032; OBSERVABILITY_PLAN redaction rules R-01…R-07.                              |
| Sensitive file exposure / path traversal             | Covered.                   | SEC-043; pathlib canonical-path checks.                                                      |
| DoS / resource exhaustion on a localhost app         | Covered.                   | SEC-039–SEC-042; timeouts, concurrency caps, project caps.                                   |
| Supply chain                                         | Covered.                   | SEC-033 (pinned deps), SEC-034 (pip/npm audit).                                              |

**No unsafe "dangerous cybersecurity functionality" was found in scope.** Active exploitation, malware execution, and automatic network modification are prohibited consistently across AGENTS.md, PRD, SCOPE, SECURITY_REQUIREMENTS, THREAT_MODEL, and RISK_REGISTER.

---

## 10. RAG Risks

| Risk                                    | Assessment                                                                                                             |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Retrieval quality (precision/recall)    | Explicitly evaluated in Phase 4 with targets (P@10 ≥ 0.7 etc.); chunk-size and embedding-model experiments prescribed. |
| Hallucinated citations                  | SEC-038 validates cited chunk IDs against ChromaDB; flagged in validation report.                                      |
| Stale/version-conflicting documents     | Source manifest with version + hash; deprecation flow; ACL on re-ingestion.                                            |
| Prompt injection through retrieved text | SEC-019 (delimited context section); SEC-020; role separation.                                                         |
| Missing reproducibility                 | Ingestion runs recorded; ChromaDB snapshot/manifest versioned; evaluation sets frozen.                                 |

---

## 11. Fine-Tuning Risks

| Risk                                   | Assessment                                                                                                   |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Fine-tuning used to memorise standards | Explicitly prohibited; RAG owns factual knowledge (ADR-0006).                                                |
| Split/leakage issues                   | 80/10/10 split; test frozen pre-training; leakage checks (Jaccard dedup, no evaluation prompts in training). |
| Overfitting                            | Validation-loss early stopping, LoRA dropout, rollback criteria.                                             |
| Unrealistic hardware                   | 8 GB VRAM / 16 GB RAM minimums documented; Colab/Kaggle fallback.                                            |
| Null result                            | Accepted as valid academic outcome; app works with base model only.                                          |

---

## 12. Evaluation Risks

| Risk                        | Assessment                                                                               |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| Fixed evaluation set        | Yes — frozen before training (10% test split; 10 project descriptions in plan).          |
| Metrics without definitions | All metrics defined with computation method; thresholds marked provisional.              |
| Missing human evaluation    | Human rubric for ≥ 10 examples across all 4 configs.                                     |
| Four-way comparison         | C1/C2/C3/C4 defined consistently across PRD, EVALUATION_PLAN, README, ADR-0007.          |
| Reproducibility             | Committed dataset, versioned prompts, recorded hyperparameters, `EvaluationRun` records. |

---

## 13. Roadmap Risks

| Risk                                   | Assessment                                                                                                                                   |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Fine-tuning before baseline evaluation | **Not present.** C1 baseline recorded at Phase 3; C2 at Phase 4; C3 at Phase 8; C4 + full comparison at Phase 9.                             |
| RAG before mocked E2E                  | **Not present.** Phases 1–2 include mocked E2E (backlog Epics 1–2); RAG is Phase 4.                                                          |
| Missing completion gates               | Every phase has a gate; TEST_STRATEGY §3 maps required tests per gate.                                                                       |
| Tasks too large                        | 77 backlog items sized S/M/L; largest items are document-heavy (PDF template, SRS orchestration) and are within a single student's capacity. |
| Dependencies reflected in backlog      | Yes — each task lists dependencies; dependency graph in IMPLEMENTATION_BACKLOG matches ROADMAP.                                              |
| Timeline                               | 14–24 weeks against a typical 16–20-week term is **tight**; RSK-001 (scope creep) is the single Critical risk and is the right one to watch. |

---

## 14. Exact Recommended Corrections

| #   | Correction                                                                                              | Applied?                                                |
| --- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 1   | Add cross-reference note + total-count correction to `docs/REQUIREMENTS_CATALOG.md` for SEC-008–SEC-050 | ✅ Yes (see §4 MAJ-01)                                  |
| 2   | Create `docs/PLANNING_AUDIT.md` recording this audit                                                    | ✅ Yes (this file)                                      |
| 3   | Reword PRD §23 item 9 to "a fine-tuning run with documented result (rollback permitted)"                | ⏸ Deferred — record for next PRD revision; non-blocking |
| 4   | Align PRD SC-5 RAM wording (8 GB min / 16 GB recommended)                                               | ⏸ Deferred — minor; document in next PRD revision       |
| 5   | Update README phase bullets to show C1/C2 baseline recording points when Phase 3 begins                 | ⏸ Deferred to Phase 3 start                             |
| 6   | Add per-phase "reviewed at gate" note to document headers                                               | ⏸ Deferred — process improvement, not a blocker         |
| 7   | Do not reintroduce un-versioned duplicate planning snapshots                                            | ✅ Enforced via review note (MAJ-02)                    |

---

## 15. Final Pre-Coding Checklist

Before Phase 1A begins, all of the following are verified:

- [x] Project invariants (name, description-to-SRS, inferred domain, single Qwen model, 4-way eval, RAG=citations, fine-tuning=behaviour, FastAPI, React/TS/Vite, SQLite/ChromaDB, local-first, JSON-first, safety exclusions, single student) are preserved everywhere.
- [x] All requirement IDs in `REQUIREMENTS_CATALOG.md` are unique (FR-001…FR-073, NFR-001…NFR-032, SEC-001…SEC-007, DATA-001…, AI-001…, RAG-001…, UX-001…).
- [x] SEC-008…SEC-050 are unique within `SECURITY_REQUIREMENTS.md` and the catalogue now references them (MAJ-01 fix).
- [x] Security requirements map to threats (THREAT_MODEL §7 / SECURITY_REQUIREMENTS threat columns are complete).
- [x] RAG vs fine-tuning responsibilities do not overlap incorrectly (ADR-0005, ADR-0006).
- [x] Roadmap starts with non-AI skeleton and mocked end-to-end flow (Phase 1 / backlog Epics 1–2).
- [x] Baseline evaluation (C1) occurs before fine-tuning conclusions (Phase 3 vs Phase 8/9).
- [x] The four evaluation configurations are documented consistently (PRD, EVALUATION_PLAN, README, ADR-0007).
- [x] Every roadmap phase has a completion gate.
- [x] Every gate identifies required tests (TEST_STRATEGY §3).
- [x] The user never selects the domain manually (UX-002, FR-011, USER_WORKFLOW §4).
- [x] No dangerous cybersecurity functionality is in scope.
- [x] No implementation code has been generated by this audit (audit-only).

---

## 16. Audit Method

- Read: `README.md`, `AGENTS.md`, every `docs/*.md` (28 documents), every `docs/adr/*.md` (8 ADRs).
- Cross-checked: scope consistency, requirement quality, architecture, workflow, RAG, fine-tuning, evaluation, security, roadmap, backlog, risks.
- Verified invariants and completed the final pre-coding checklist above.
- Produced this audit as the sole deliverable of the documentation-audit task.
