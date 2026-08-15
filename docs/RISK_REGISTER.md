# Risk Register — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

---

## Risk Rating Scale

| Probability | Impact | Rating |
|---|---|---|
| High × High | — | **Critical** |
| High × Medium or Medium × High | — | **High** |
| Medium × Medium | — | **Medium** |
| Low × Medium or Medium × Low | — | **Low** |
| Low × Low | — | **Negligible** |

---

## Risk Table

| ID | Risk | Probability | Impact | Rating | Owner | Mitigation | Trigger | Contingency |
|---|---|---|---|---|---|---|---|---|
| RSK-001 | **Scope creep** — New features or documents are added beyond what is achievable by one student in the available time. | High | High | Critical | Student | Strict adherence to SCOPE.md; defer all post-MVP features; roadmap completion gates; refuse unplanned work. | A task takes 3× longer than expected, or new requirements appear mid-phase. | Cut the lowest-priority features (e.g., version history, quality score). Prioritise core workflow and evaluation. |
| RSK-002 | **GPU memory limitations** — Available GPU has insufficient VRAM for QLoRA training of Qwen3-4B. | Medium | High | High | Student | Plan for 4-bit quantisation (QLoRA); test on consumer GPU early; document minimum hardware. | Training script crashes with OOM error. | Reduce batch size, LoRA rank, or sequence length. Use gradient checkpointing. As a last resort, use a cloud GPU instance for training only. |
| RSK-003 | **Slow inference on CPU** — Qwen3-4B inference on CPU-only hardware is too slow for usable demo. | Medium | Medium | Medium | Student | Set realistic timeouts (120 s per call); implement progress indicators; recommend GPU in documentation. | Single section generation takes > 60 seconds. | Use Ollama quantisation (Q4_K_M); reduce prompt length; accept slower demo with progress indicators. |
| RSK-004 | **Poor JSON compliance** — Qwen3-4B frequently produces invalid JSON, causing excessive retries and failures. | Medium | High | High | Student | Detailed prompt templates with schema and examples; corrective-prompt retry logic; fine-tuning specifically targets JSON compliance. | > 30% of generation calls fail schema validation on first attempt. | Simplify JSON schemas (fewer required fields); increase max retries; use post-processing JSON repair library; focus fine-tuning on JSON compliance. |
| RSK-005 | **Poor retrieval quality** — ChromaDB returns irrelevant chunks, degrading SRS quality instead of improving it. | Medium | Medium | Medium | Student | Experiment with chunk sizes, embedding models, and relevance thresholds; evaluate retrieval precision during Phase 4. | Retrieval precision@10 < 0.3. | Adjust chunking strategy; try different embedding model; increase relevance threshold; add category-based metadata filtering. |
| RSK-006 | **Weak citations** — Generated requirements cite sources but the citations do not actually support the requirements. | Medium | Medium | Medium | Student | Citation validation (SEC-038); human evaluation of citation support; prompt engineering to improve citation accuracy. | Citation support score < 0.5. | Improve prompts with citation examples; increase retrieval quality; accept lower citation coverage and document as a limitation. |
| RSK-007 | **Dataset quality** — Training examples are too few, too homogeneous, or contain errors, limiting fine-tuning effectiveness. | High | Medium | High | Student | Target 390–550 examples across 13 categories; schema-validate all examples; human-review every example; diverse project types. | Fine-tuned model shows < 5% improvement over base model. | Increase dataset size; focus on the categories with weakest base-model performance; accept limited improvement and document honestly. |
| RSK-008 | **Data leakage** — Test examples accidentally appear in the training set, inflating evaluation metrics. | Low | High | Medium | Student | Strict train/val/test split before training; automated deduplication check; evaluation script verifies no overlap. | Automated check finds overlap between train and test sets. | Re-split data; re-train; re-evaluate. |
| RSK-009 | **Overfitting** — Fine-tuned model memorises training examples and generalises poorly. | Medium | Medium | Medium | Student | Monitor validation loss; early stopping; LoRA dropout; check for verbatim reproduction of training examples. | Validation loss increases for 2+ epochs while training loss decreases. | Stop training at best checkpoint; reduce epochs; increase dropout; check dataset diversity. |
| RSK-010 | **Insufficient evaluation time** — Not enough time to run full four-way evaluation before the project deadline. | Medium | High | High | Student | Start evaluation infrastructure in Phase 3 (record C1 baseline early); automate as much evaluation as possible; fix evaluation set before training. | 2 weeks before deadline and evaluation hasn't started. | Run only automated evaluations; reduce human rubric to 5 examples; accept partial results. |
| RSK-011 | **PDF rendering problems** — Chosen PDF library cannot handle complex tables, Unicode, or produces ugly output. | Medium | Medium | Medium | Student | Evaluate PDF library candidates early (Phase 6); test with sample SRS JSON; have a fallback library. | Tables break, Unicode fails, or output is unprofessional. | Switch PDF library; simplify table layout; use Markdown-to-PDF as a fallback. |
| RSK-012 | **Dependency instability** — A critical Python or npm package releases a breaking change or is deprecated. | Low | Medium | Low | Student | Pin all dependency versions in lock files (SEC-033); test against pinned versions; don't upgrade mid-project without reason. | A pinned dependency has a critical CVE. | Update the specific dependency; run full test suite; document the change. |
| RSK-013 | **Model or licence issues** — Qwen3-4B licence changes, model is removed from Ollama, or weights become unavailable. | Low | High | Medium | Student | Download model weights early; document the exact version and download date; provider-independent interface allows fallback. | Model is unavailable for download. | Use the already-downloaded copy; if unavailable, switch to an alternative 4B model (e.g., Phi-3 Mini) and re-evaluate. |
| RSK-014 | **Agent-generated code inconsistency** — AI coding agents produce code that contradicts AGENTS.md, uses wrong naming conventions, or introduces unapproved dependencies. | Medium | Medium | Medium | Student | AGENTS.md is authoritative; all agents must read it; code review enforces conventions; linting catches naming violations. | Agent introduces a new ORM or framework not in the approved stack. | Revert the change; re-prompt the agent with AGENTS.md; add the violation to AGENTS.md as an explicit prohibition. |
| RSK-015 | **Security risks** — Generated SRS contains dangerous content; prompt injection bypasses validation; dependency has a vulnerability. | Low | High | Medium | Student | SEC requirements (SEC-001–SEC-050); THREAT_MODEL.md mitigations; automated security tests; output scanning for exploit patterns. | Security test fails; a generated requirement contains executable code. | Fix the security control; add a regression test; escalate to advisor if the issue is fundamental. |
| RSK-016 | **Demonstration failure** — Live demo fails during presentation due to Ollama crash, slow hardware, or unexpected errors. | Medium | High | High | Student | Prepare offline backup demo (DEMO_PLAN.md §5); pre-generate all outputs; test demo procedure end-to-end before presentation. | Live demo crashes or hangs. | Switch to the offline backup demo immediately; show pre-generated PDFs and evaluation results. |
| RSK-017 | **Catastrophic regression from fine-tuning** — Fine-tuned model produces harmful, offensive, or systematically worse output than the base model. | Low | High | Medium | Student | Catastrophic-behaviour regression checks (FINETUNING_PLAN.md §19); rollback criteria; safety checks in prompts. | Fine-tuned model fails safety checks. | Roll back to the base model; document the failure; investigate the training data for issues. |

---

## Risk Summary by Rating

| Rating | Count | Risk IDs |
|---|---|---|
| Critical | 1 | RSK-001 |
| High | 5 | RSK-002, RSK-004, RSK-007, RSK-010, RSK-016 |
| Medium | 8 | RSK-003, RSK-005, RSK-006, RSK-008, RSK-009, RSK-011, RSK-013–RSK-015, RSK-017 |
| Low | 1 | RSK-012 |

---

## Risk Review Schedule

- **Phase transitions:** Review all risks at each roadmap completion gate.
- **Trigger events:** Re-assess immediately when a trigger condition is met.
- **New risks:** Add to this register as discovered; do not silently ignore.
