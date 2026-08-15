# ADR-0007: Four Evaluation Baselines

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Project Architect

---

## Context

CyberSRS enhances Qwen/Qwen3-4B-Instruct-2507 with two orthogonal mechanisms:

1. **RAG** — supplies external cybersecurity knowledge and source citations.
2. **QLoRA fine-tuning** — improves requirements-engineering behaviour and structural quality.

To understand the individual and combined contribution of each mechanism, a controlled evaluation design is required. Without this design, it would be impossible to claim whether improvement comes from RAG, fine-tuning, both, or neither.

## Decision

Evaluate the system in **four configurations** using the same held-out test set and the same metrics:

| Config | Abbreviation | Model | RAG | Purpose |
|---|---|---|---|---|
| Configuration 1 | **C1** | Base Qwen3-4B | Off | Pure baseline — model's built-in capability only |
| Configuration 2 | **C2** | Base Qwen3-4B | On | Isolates RAG's contribution |
| Configuration 3 | **C3** | Fine-tuned Qwen3-4B | Off | Isolates fine-tuning's contribution |
| Configuration 4 | **C4** | Fine-tuned Qwen3-4B | On | Full system — combined contribution |

**Analysis framework:**

| Comparison | What it measures |
|---|---|
| C2 vs C1 | Impact of RAG on the base model |
| C3 vs C1 | Impact of fine-tuning without external knowledge |
| C4 vs C1 | Total system improvement |
| C4 vs C2 | Additional value of fine-tuning when RAG is present |
| C4 vs C3 | Additional value of RAG when fine-tuning is present |

**Expected hypothesis (to be validated, not assumed):**
- C4 ≥ C2 and C4 ≥ C3 (combined is at least as good as either alone).
- C2 and C3 each outperform C1 on their respective strengths.
- If fine-tuning does not help, C3 ≈ C1 and C4 ≈ C2. This is a valid outcome.

## Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| **Two-way evaluation (base vs. full system)** | Cannot determine whether improvement comes from RAG or fine-tuning. |
| **Three-way (no C3)** | Cannot isolate fine-tuning's contribution independent of RAG. |
| **Three-way (no C2)** | Cannot isolate RAG's contribution independent of fine-tuning. |
| **Evaluate only C4 (full system)** | No baseline for comparison; impossible to claim any mechanism helps. |

## Consequences

### Positive
- **Scientific rigour.** The 2×2 design isolates each mechanism's contribution.
- **Honest reporting.** If fine-tuning does not help, the evaluation reveals this clearly.
- **Academic value.** The comparison is suitable for academic reporting and paper-writing.
- **Debuggability.** If C4 underperforms, the four-way comparison identifies which mechanism is at fault.

### Negative
- **Evaluation cost.** Running all test examples through 4 configurations takes 4× the time. Mitigated by automating metrics and limiting human evaluation to a subset.
- **Complexity.** Managing 4 evaluation runs with reproducibility requires discipline. Mitigated by evaluation scripts and GenerationRun metadata.

### Neutral
- The expected ordering is a hypothesis. If results differ, that is a valid finding to document.
- Human rubric evaluation is applied to a subset only (≥ 10 examples across all 4 configurations). Full-set human evaluation is not feasible for one student.
