# ADR-0004: Local-First Deployment

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Project Architect

---

## Context

CyberSRS handles potentially sensitive information:

- Informal project descriptions may contain details about an organisation's network architecture, security gaps, or planned defences.
- Generated SRS documents contain detailed security requirements, threat models, and architectural descriptions that an adversary could exploit.
- Fine-tuning datasets may include curated examples derived from real-world projects.

Additionally, the project is designed for individual practitioners and students who may not have access to cloud infrastructure, paid API subscriptions, or enterprise-grade internet connectivity.

The deployment model must balance:

1. **Privacy** — sensitive project data must not leave the user's machine.
2. **Accessibility** — the application must work without cloud accounts, API keys, or internet (after initial setup).
3. **Simplicity** — a single student developer must be able to set up and run the application.
4. **Cost** — no recurring costs for inference or storage.

## Decision

CyberSRS is **local-first**: all components run on a single machine with no external network dependencies at runtime.

Specifically:

| Component | Deployment |
|---|---|
| React frontend | Served locally (Vite dev server or static build) |
| FastAPI backend | Runs locally on `localhost:8000` |
| SQLite database | Local file |
| ChromaDB | Embedded, local persistence directory |
| Ollama + Qwen3-4B | Runs locally on `localhost:11434` |

**No data is transmitted to any external service.** The only network communication is between local processes on `localhost`.

**Internet is required only during initial setup** for:

- Installing Python and Node.js dependencies.
- Pulling the Qwen3-4B model via Ollama.
- Downloading cybersecurity documents for knowledge-base ingestion.

After setup, the application works fully offline.

## Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| **Cloud-hosted SaaS** | Violates privacy requirements. Users would need to send sensitive project data to a third party. Adds hosting cost. |
| **Hybrid (local app + cloud LLM API)** | Sends project descriptions and generated content to cloud APIs (OpenAI, Anthropic). Violates privacy. Adds per-token cost. |
| **Docker-required deployment** | Docker adds a setup step and assumes familiarity. Acceptable as an *optional* convenience but must not be *required*. |
| **Client-only (browser-based, no backend)** | WebGPU/WASM-based LLM inference is not mature enough for a 4B model. Cannot run ChromaDB or SQLite reliably in-browser. |

## Consequences

### Positive

- **Full data privacy.** No project data ever leaves the user's machine. Users can work on sensitive security projects without risk of data exposure.
- **Zero recurring cost.** No API usage fees, cloud hosting charges, or subscription costs.
- **Offline operation.** Works without internet after initial setup. Suitable for air-gapped or restricted environments.
- **Simplicity.** Single-machine deployment eliminates distributed-system concerns (networking, DNS, load balancing, certificates).
- **Reproducibility.** The entire stack can be set up on a fresh machine by following documented steps.

### Negative

- **Hardware requirements.** The user must have a machine capable of running a 4B LLM. Minimum 8 GB RAM; GPU recommended for acceptable performance. This excludes very low-spec machines.
- **Performance variability.** Inference speed depends entirely on the user's hardware. CPU-only inference may be slow (30+ seconds per generation step). Mitigated by progress indicators and async generation.
- **No multi-device access.** The application is accessible only from the machine it runs on (via `localhost`). Not suitable for team use across multiple machines in the MVP.
- **Update burden on user.** The user must manually update models, knowledge-base documents, and dependencies. No auto-update mechanism.

### Neutral

- The local-first constraint does not prevent a future cloud-hosted deployment option. The architecture is designed so that swapping Ollama for a cloud LLM provider (via the `LLMProvider` interface) and SQLite for PostgreSQL would be straightforward changes, requiring no modification to business logic.
- Docker support may be added as an optional convenience in Phase 10 (see UDEC-009 in DECISIONS.md), but it must never be the only way to run the application.
