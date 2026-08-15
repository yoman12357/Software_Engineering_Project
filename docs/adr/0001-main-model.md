# ADR-0001: Qwen/Qwen3-4B-Instruct-2507 as the Single Main LLM

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Project Architect

---

## Context

CyberSRS requires a main LLM for multiple tasks:

1. **Description analysis** — extracting entities and inferring cybersecurity subdomains from informal text.
2. **Clarification-question generation** — identifying gaps and producing targeted questions.
3. **SRS generation** — producing structured functional, non-functional, and security requirements.
4. **Threat-model generation** — identifying threats and mitigations.
5. **Requirement validation** — assessing requirement quality (hybrid LLM + rules).
6. **QLoRA fine-tuning** — improving output quality for requirements-engineering tasks.

The model must:

- Run locally on consumer hardware (≥ 8 GB RAM, CPU-only acceptable).
- Support structured JSON output.
- Be instruction-tuned for following complex prompts.
- Be supported by Hugging Face Transformers and PEFT for QLoRA fine-tuning.
- Be available on Ollama for convenient local serving.

## Decision

Use **Qwen/Qwen3-4B-Instruct-2507** as the single main LLM for all six tasks listed above.

A separate embedding model (to be selected in Phase 4; see UDEC-001 in DECISIONS.md) will be used solely for vector retrieval in RAG. The embedding model is a utility and is not considered the main LLM.

## Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| **Llama 3.1 8B** | Larger model; higher hardware requirements for fine-tuning and inference on CPU. |
| **Mistral 7B** | Same concern as Llama 3.1 8B — 7B parameters increase memory and compute. |
| **Phi-3 Mini (3.8B)** | Viable size, but Qwen3-4B-Instruct-2507 was selected as the project's fixed decision. |
| **GPT-4o / Claude (cloud APIs)** | Violates the local-first deployment constraint. Adds cost and external dependency. |
| **No fine-tuning; prompt engineering only** | Limits the research contribution. Fine-tuning comparison is a project goal. |

## Consequences

### Positive

- **Feasible on consumer hardware.** 4B parameters fit in ≤ 8 GB RAM with quantisation (Q4_K_M).
- **Single model simplifies evaluation.** The same model is used for all tasks, making comparative evaluation straightforward.
- **QLoRA fine-tuning is feasible.** 4B models can be fine-tuned with QLoRA on a single consumer GPU (or even CPU with patience).
- **Ollama support.** Qwen3 models are available in the Ollama model library.
- **Hugging Face ecosystem support.** Full compatibility with Transformers, PEFT, and TRL.

### Negative

- **Capability ceiling.** A 4B model may produce lower-quality output than larger models (7B+). Mitigated by structured prompts, JSON-schema validation, retry logic, and QLoRA fine-tuning.
- **Structured output challenges.** Smaller models sometimes struggle with complex JSON. Mitigated by detailed prompt templates and corrective-prompt retries.
- **Single point of failure.** If Qwen3-4B is fundamentally unsuitable for a task, there is no fallback model in the MVP. Mitigated by the provider-independent interface, which allows swapping models if needed.

### Neutral

- The embedding model for RAG is a separate decision (UDEC-001) and does not affect this ADR.
