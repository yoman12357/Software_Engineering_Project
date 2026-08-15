# Evaluation Plan — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

---

## 1. Four-Way Evaluation Design

All evaluations use the same held-out test set and the same metrics across four model configurations:

| Config | Model | RAG | Description |
|---|---|---|---|
| **C1** | Base Qwen3-4B | No | Baseline — model's built-in knowledge only |
| **C2** | Base Qwen3-4B | Yes | RAG adds domain knowledge and citations |
| **C3** | Fine-tuned Qwen3-4B (QLoRA adapter) | No | Fine-tuning improves RE behaviour without external knowledge |
| **C4** | Fine-tuned Qwen3-4B (QLoRA adapter) | Yes | Full system — fine-tuned behaviour + RAG knowledge |

**Expected ordering (hypothesis):** C4 > C2 ≈ C3 > C1

This ordering is a hypothesis to be validated, not a guaranteed outcome.

---

## 2. Held-Out Evaluation Set

- **Source:** 10% test split from each dataset category (see DATASET_PLAN.md §1).
- **Size:** Approximately 40–55 examples (10% of 390–550 total).
- **Constraint:** The test set is **never** used during training or prompt development.
- **Coverage:** At least 6 of the 8 project categories; all 13 dataset task categories.
- **Freeze:** The test set is frozen before training begins and not modified during evaluation.

---

## 3. Evaluation Metrics

### 3.1 Automated Metrics

| Metric | Type | Description | Threshold (Provisional) |
|---|---|---|---|
| **JSON-schema validity** | Binary per output | Does the output parse as valid JSON and pass Pydantic validation? | C1 ≥ 70%, C4 ≥ 90% |
| **Requirement ID format** | Binary per requirement | Does each ID follow the `XX-NNN` pattern? | ≥ 95% for all configs |
| **Duplicate requirement rate** | Ratio | Fraction of requirements with duplicate IDs within a single SRS | ≤ 5% for all configs |
| **Section completeness** | Checklist (0–1) | Are all mandatory SRS sections present? | C1 ≥ 0.7, C4 ≥ 0.9 |
| **Latency (per section)** | Seconds | Wall-clock time per LLM call | Report only (no threshold) |
| **Memory usage** | MB | Peak memory during inference | Report only |
| **Generation failure rate** | Ratio | Fraction of examples where generation fails after max retries | ≤ 10% for C4 |
| **Retry rate** | Average per run | Average number of retries per generation run | C1: report; C4 ≤ 0.5 |

### 3.2 Rule-Based Metrics

| Metric | Type | Description | Threshold (Provisional) |
|---|---|---|---|
| **Atomicity** | Score (0–1) | Fraction of requirements that are atomic (one concern per requirement). Detected by checking for "and", "or", compound sentences. | C4 ≥ 0.80 |
| **Testability keyword presence** | Score (0–1) | Fraction of requirements containing measurable terms (numbers, thresholds, timeframes). | C4 ≥ 0.70 |
| **"The system shall" compliance** | Score (0–1) | Fraction of requirements starting with "The system shall" or equivalent testable language. | ≥ 0.85 for all configs |
| **Acceptance criteria presence** | Score (0–1) | Fraction of requirements with non-empty acceptance criteria. | C4 ≥ 0.85 |
| **Priority distribution** | Histogram | Distribution of Must/Should/Could across requirements. | No threshold; report for analysis |

### 3.3 Retrieval Metrics (C2 and C4 only)

| Metric | Type | Description | Threshold (Provisional) |
|---|---|---|---|
| **Citation precision** | Score (0–1) | Fraction of cited sources that are actually relevant to the requirement (human-judged). | ≥ 0.70 |
| **Citation recall** | Score (0–1) | Fraction of relevant retrieved chunks that are actually cited. | ≥ 0.50 |
| **Citation support** | Score (0–1) | Fraction of cited sources that factually support the requirement statement (human-judged). | ≥ 0.70 |
| **Hallucinated citation rate** | Ratio | Fraction of citations pointing to non-existent or non-retrieved chunks. | ≤ 0.05 |
| **Retrieval precision@k** | Score (0–1) | Fraction of top-k retrieved chunks that are relevant to the query (human-judged). | ≥ 0.60 |

### 3.4 Human Rubric Metrics

For a subset of test examples (≥ 10), a human evaluator scores each generated SRS on:

| Metric | Scale | Description |
|---|---|---|
| **Requirement completeness** | 1–5 | Does the SRS cover all expected requirement areas for the project type? |
| **Requirement correctness** | 1–5 | Are the requirements factually correct and appropriate for the project? |
| **Ambiguity** | 1–5 (inverse) | 5 = no ambiguity, 1 = highly ambiguous. |
| **Security-control coverage** | 1–5 | Does the SRS address the important security controls for the project type? |
| **Threat-model coverage** | 1–5 | Does the threat model identify the important threats for the project? |
| **Acceptance-criteria quality** | 1–5 | Are the acceptance criteria specific, measurable, and aligned with requirements? |
| **Hallucination rate (subjective)** | 1–5 (inverse) | 5 = no hallucinated facts, 1 = extensive hallucination. |
| **Overall quality** | 1–5 | Holistic assessment of the SRS as a professional document. |

**Human evaluator:** The student (author). For academic purposes, inter-rater reliability is not required but is noted as a limitation.

---

## 4. Evaluation Separation

| Type | Metrics | Automated? | When |
|---|---|---|---|
| **Automated** | Schema validity, ID format, duplicates, completeness, latency, memory, failures, retries | Yes | Every evaluation run |
| **Rule-based** | Atomicity, testability, "shall" compliance, acceptance criteria, priority distribution | Yes | Every evaluation run |
| **Retrieval** | Citation precision/recall/support, hallucinated citations, retrieval precision@k | Partially (hallucinated citations automated; precision/recall/support human-judged) | C2 and C4 only |
| **Human rubric** | Completeness, correctness, ambiguity, security coverage, threat coverage, AC quality, hallucination, overall | No | Subset of examples; all 4 configs |

---

## 5. Experiment-Result Table Templates

### 5.1 Automated Metrics Table

| Metric | C1 (Base) | C2 (Base+RAG) | C3 (FT) | C4 (FT+RAG) |
|---|---|---|---|---|
| JSON-schema validity (%) | ___ | ___ | ___ | ___ |
| Requirement ID format (%) | ___ | ___ | ___ | ___ |
| Duplicate rate (%) | ___ | ___ | ___ | ___ |
| Section completeness (0–1) | ___ | ___ | ___ | ___ |
| Generation failure rate (%) | ___ | ___ | ___ | ___ |
| Avg retry rate | ___ | ___ | ___ | ___ |
| Avg latency (s/section) | ___ | ___ | ___ | ___ |
| Peak memory (MB) | ___ | ___ | ___ | ___ |

### 5.2 Rule-Based Metrics Table

| Metric | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| Atomicity (0–1) | ___ | ___ | ___ | ___ |
| Testability keywords (0–1) | ___ | ___ | ___ | ___ |
| "Shall" compliance (0–1) | ___ | ___ | ___ | ___ |
| AC presence (0–1) | ___ | ___ | ___ | ___ |

### 5.3 Retrieval Metrics Table

| Metric | C2 (Base+RAG) | C4 (FT+RAG) |
|---|---|---|
| Citation precision (0–1) | ___ | ___ |
| Citation recall (0–1) | ___ | ___ |
| Citation support (0–1) | ___ | ___ |
| Hallucinated citation rate | ___ | ___ |
| Retrieval precision@10 | ___ | ___ |

### 5.4 Human Rubric Table (Per Example)

| Example | Config | Completeness | Correctness | Ambiguity | Sec Coverage | Threat Coverage | AC Quality | Hallucination | Overall |
|---|---|---|---|---|---|---|---|---|---|
| Demo 1 | C1 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 |
| Demo 1 | C2 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 |
| Demo 1 | C3 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 |
| Demo 1 | C4 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 | _/5 |

### 5.5 Summary Comparison

| Category | Best Config | Improvement over C1 |
|---|---|---|
| Schema compliance | ___ | ___ pp |
| Requirement quality | ___ | ___ pp |
| Citation accuracy | ___ | ___ pp |
| Overall human score | ___ | ___/5 |

---

## 6. Provisional Thresholds

All thresholds are marked as **provisional** and may be adjusted based on initial baseline results:

> **Important:** If the C1 baseline is very low (e.g., < 50% schema compliance), thresholds for C3/C4 should be adjusted relative to the baseline improvement, not absolute values.

---

## 7. Evaluation Timeline

| Phase | Activity |
|---|---|
| Phase 3 | Record C1 baseline (base model, no RAG). |
| Phase 4 | Record C2 (base model + RAG). Evaluate retrieval metrics. |
| Phase 8 | Record C3 (fine-tuned, no RAG) after training. |
| Phase 9 | Record C4 (fine-tuned + RAG). Full four-way comparison. Human rubric evaluation. |
| Phase 10 | Document final results. |
