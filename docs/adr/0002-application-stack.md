# ADR-0002: React, FastAPI, SQLite, and ChromaDB as the MVP Stack

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Project Architect

---

## Context

CyberSRS needs a full-stack application composed of:

1. A **frontend** for project management, SRS review, editing, and PDF export.
2. A **backend** that orchestrates LLM calls, RAG retrieval, validation, and data persistence.
3. A **relational database** for storing projects, SRS versions, clarifications, and generation metadata.
4. A **vector database** for storing and querying document embeddings used in RAG.

The stack must:

- Be locally deployable on a single machine.
- Be manageable by a single student developer.
- Support the Python ML/LLM ecosystem (Hugging Face, PEFT, TRL, ChromaDB).
- Provide a responsive, modern UI.
- Keep complexity low for an MVP.

## Decision

| Layer | Technology |
|---|---|
| Frontend | React 18+, TypeScript, Vite |
| Backend | Python 3.11+, FastAPI |
| Relational database | SQLite |
| Vector database | ChromaDB |
| Architecture | Modular monolith (no microservices) |

The backend exposes a REST API consumed by the React SPA. The LLM provider is abstracted behind an `LLMProvider` interface so that the backend does not depend directly on Ollama.

## Alternatives Considered

### Frontend

| Alternative | Reason for Rejection |
|---|---|
| **Next.js** | Server-side rendering is unnecessary for a local-only SPA. Adds complexity. |
| **Vue.js** | Viable, but React has a larger ecosystem and the developer has more experience with it. |
| **Svelte** | Smaller ecosystem; less library support for complex UIs. |
| **Plain HTML/JS** | Insufficient for a complex, interactive SRS editor with section navigation, inline editing, and progress indicators. |

### Backend

| Alternative | Reason for Rejection |
|---|---|
| **Django** | Heavier; includes ORM and template engine not needed here. FastAPI is lighter and async-native. |
| **Flask** | No built-in async support, no automatic OpenAPI docs, no Pydantic integration. |
| **Node.js (Express)** | Would split the ML ecosystem (Python) from the API layer (Node). Adds complexity. |

### Relational Database

| Alternative | Reason for Rejection |
|---|---|
| **PostgreSQL** | Requires a separate server process. Overkill for single-user MVP. Reserved for post-MVP upgrade. |
| **MySQL/MariaDB** | Same as PostgreSQL — unnecessary complexity. |
| **JSON files** | No query support, no transactions, fragile. |

### Vector Database

| Alternative | Reason for Rejection |
|---|---|
| **Pinecone** | Cloud-hosted; violates local-first constraint. |
| **Weaviate** | Requires a separate server process; heavier than ChromaDB. |
| **FAISS** | Library-level only; no built-in persistence, metadata, or filtering. |
| **Qdrant** | Viable, but ChromaDB is simpler to embed in a Python application. |

### Architecture

| Alternative | Reason for Rejection |
|---|---|
| **Microservices** | Excessive for a single-developer project. Adds deployment, networking, and debugging complexity. |
| **Serverless** | Requires cloud infrastructure; violates local-first constraint. |

## Consequences

### Positive

- **Unified Python ecosystem.** Backend, LLM integration, RAG, fine-tuning, and evaluation all use Python. No language boundary.
- **FastAPI + Pydantic synergy.** Request/response validation, LLM output validation, and OpenAPI documentation use the same Pydantic models.
- **SQLite simplicity.** Zero-config, file-based, transactions supported. Perfect for single-user MVP.
- **ChromaDB embeddability.** Runs in-process; no separate server needed. Python-native API.
- **React maturity.** Extensive component libraries, TypeScript support, and community resources.
- **Vite speed.** Fast HMR (hot module replacement) during development.
- **Modular monolith.** Single deploy unit keeps operations simple while internal modules maintain separation of concerns.

### Negative

- **SQLite limitations.** No concurrent writes from multiple processes. Acceptable for single-user MVP but must be upgraded for multi-user post-MVP.
- **ChromaDB maturity.** Less battle-tested than Pinecone or Weaviate. Acceptable for MVP; can migrate later if needed.
- **React learning curve.** TypeScript + React requires some ramp-up if the developer is unfamiliar. Mitigated by extensive documentation and community.
- **Monolith coupling risk.** If modules are not properly separated, the codebase may become entangled. Mitigated by clear service interfaces and the architecture document.

### Neutral

- The provider-independent `LLMProvider` interface means the backend does not depend on Ollama's API directly. This is an intentional decoupling that simplifies future provider changes.
- SQLite → PostgreSQL migration is planned for post-MVP and should be straightforward if the data-access layer uses a repository pattern.
