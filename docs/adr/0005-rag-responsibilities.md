# ADR-0005: Responsibilities of RAG in CyberSRS

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Project Architect

---

## Context

CyberSRS uses both Retrieval-Augmented Generation (RAG) and QLoRA fine-tuning to enhance LLM output quality. These two mechanisms serve complementary purposes, but their responsibilities must be clearly separated to avoid confusion, wasted effort, and incorrect evaluation.

Without clear separation:
- Fine-tuning datasets might try to "teach" the model NIST or OWASP content, duplicating RAG's role and baking in stale knowledge.
- RAG might be expected to improve requirement structure and testability, which it cannot do.
- Evaluation would conflate knowledge improvements (RAG) with behavioural improvements (fine-tuning).

## Decision

**RAG is responsible for supplying external cybersecurity knowledge, framework guidance, standards, controls, and source attribution.**

Specifically, RAG provides:

| Responsibility | Example |
|---|---|
| Current cybersecurity standards | OWASP ASVS v4.0, NIST SP 800-41 |
| Framework guidance | NIST CSF Identify/Protect/Detect/Respond/Recover |
| Specific security controls | CIS Controls, MITRE ATT&CK mitigations |
| Threat intelligence | ATT&CK technique descriptions |
| Source attribution | Citations linking requirements to source documents |
| Version-specific guidance | Content from a specific version of a standard |

RAG does **not** provide:

| Not RAG's responsibility | Why |
|---|---|
| Requirement structure improvement | This is a model-behaviour issue → fine-tuning |
| JSON-schema compliance | This is a model-behaviour issue → fine-tuning |
| Atomicity and testability | These are requirements-engineering behaviours → fine-tuning |
| Clarification-question quality | This is a model-behaviour issue → fine-tuning |

## Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| **RAG does everything (no fine-tuning)** | RAG retrieves facts but cannot improve the model's requirement-writing behaviour. |
| **RAG provides structural templates** | Templates in retrieved chunks would compete with prompt instructions, causing confusion. Prompt templates are the correct mechanism for structure. |
| **No RAG (fine-tuning only)** | Fine-tuning cannot reliably memorise large bodies of external knowledge, especially standards that update over time. |

## Consequences

### Positive
- Clear evaluation: RAG's impact is measured by citation accuracy and knowledge-based requirement quality.
- Updatable knowledge: new document versions can be ingested without retraining.
- Source transparency: every knowledge-grounded requirement has a traceable citation.

### Negative
- Retrieval quality directly affects output quality; poor retrieval degrades SRS even with good fine-tuning.
- Knowledge base must be manually curated and maintained.
