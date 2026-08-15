# ADR-0006: Responsibilities of Fine-Tuning in CyberSRS

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Project Architect

---

## Context

CyberSRS fine-tunes Qwen/Qwen3-4B-Instruct-2507 using QLoRA to improve output quality for requirements-engineering tasks. The scope of fine-tuning must be clearly defined to:

1. Prevent overlap with RAG's responsibilities (ADR-0005).
2. Set realistic expectations — fine-tuning a 4B model on a small dataset does not guarantee factual correctness.
3. Guide dataset construction — training examples should target the right behaviours.

## Decision

**Fine-tuning is responsible for improving requirements-engineering behaviour, structure, completeness, atomicity, testability, clarification-question quality, and schema compliance.**

Specifically, fine-tuning improves:

| Responsibility | Example |
|---|---|
| JSON-schema compliance | Producing valid JSON matching the expected Pydantic schema on the first attempt |
| Requirement atomicity | Writing one requirement per item instead of compound statements |
| Requirement testability | Including measurable, verifiable acceptance criteria |
| "The system shall…" language | Using standard requirements-engineering phrasing |
| Requirement ID conventions | Consistently using correct ID formats (FR-001, SEC-003) |
| Clarification-question quality | Asking relevant, targeted, non-redundant questions |
| SRS section completeness | Covering all expected sections with sufficient content |
| Priority assignment | Correctly distinguishing Must/Should/Could |
| Threat-model structure | Well-formed STRIDE entries with mitigations |
| Correction behaviour | Fixing errors when given a corrective prompt |

Fine-tuning does **not** provide:

| Not fine-tuning's responsibility | Why |
|---|---|
| Factual cybersecurity knowledge | Facts update over time; RAG provides current knowledge with citations |
| OWASP, NIST, MITRE ATT&CK, CIS content | These are external knowledge bases → RAG |
| Source attribution / citations | Fine-tuning cannot cite external documents it hasn't seen → RAG |
| Guaranteed factual correctness | A 4B model fine-tuned on a small dataset will still hallucinate |

**Fine-tuning must not be presented as the main mechanism for memorising OWASP, NIST, MITRE ATT&CK, or CIS content.** That is RAG's role.

## Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| **Fine-tuning does everything (no RAG)** | Cannot provide source citations. Would bake in a static snapshot of standards. |
| **Fine-tuning memorises domain content** | Unreliable with a small dataset and a 4B model. Would conflict with RAG. |
| **No fine-tuning (RAG + prompt engineering only)** | Limits the research contribution. Fine-tuning may improve structural quality even if domain knowledge comes from RAG. |
| **Fine-tuning improves both structure and knowledge** | Conflates two concerns. Makes evaluation impossible to interpret — did improvement come from better structure or more memorised facts? |

## Consequences

### Positive
- Clear evaluation: fine-tuning's impact is measured by structural metrics (schema compliance, atomicity, testability) independent of knowledge metrics.
- Dataset focus: training examples target behaviours, not encyclopaedic facts.
- Honest claims: the project does not overclaim fine-tuning's ability to replace RAG.

### Negative
- Fine-tuning alone (C3) may show limited improvement on knowledge-heavy metrics. This is expected and by design.
- The benefit of fine-tuning may be modest for a 4B model with a small dataset. Rollback to the base model is a valid and documented outcome (FINETUNING_PLAN.md §21).

### Neutral
- The four-configuration evaluation (ADR-0007) is designed to isolate RAG's contribution from fine-tuning's contribution. This separation is essential for academic integrity.
