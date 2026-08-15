# Phase 1 to 3 Report

This report summarizes the already implemented CyberSRS work through Phase 3. It does not define or implement future phases.

## Phase 1: Core CyberSRS Workflow

Phase 1 established the local CyberSRS application flow for turning an informal cybersecurity project description into a structured Software Requirements Specification.

Implemented capabilities:

- Project creation with a name and informal description.
- Backend API foundation using FastAPI and SQLite.
- Frontend workflow for project analysis, clarification questions, and SRS generation.
- Cybersecurity subdomain inference from the project description.
- Extraction of stakeholders, assets, user roles, constraints, and goals.
- Clarification-question generation for missing or ambiguous requirements.
- Clarification-answer submission and enrichment of project context.
- Structured SRS generation using validated JSON as the canonical representation.
- Deterministic schema validation before generated SRS content is persisted.
- Versioned SRS persistence and retrieval.

## Phase 2: Local Qwen Integration

Phase 2 replaced mock-only generation with the local Ollama-backed Qwen provider while preserving the provider-independent LLM interface.

Implemented capabilities:

- Local Ollama provider for `qwen3:4b-instruct-2507-q4_K_M`.
- Configurable Ollama base URL, model name, timeout, retry count, and context size through environment variables.
- Synchronous provider path used by the service layer.
- Structured-output parsing and validation against Pydantic schemas.
- Corrective retry support for invalid structured LLM output.
- Local-only model execution with no external LLM API dependency.

Verified configuration:

- Provider: Ollama.
- Model: `qwen3:4b-instruct-2507-q4_K_M`.
- Context size: 8,192 tokens.
- Real local Qwen generation works for analysis, clarification, and SRS generation.

## Phase 3: RAG Baseline

Phase 3 added retrieval-augmented generation using local embeddings and ChromaDB.

Implemented capabilities:

- Local embedding generation with `nomic-embed-text`.
- ChromaDB persistent vector store.
- Rebuilt `cybersrs_knowledge` collection with 4,470 chunks.
- RAG retrieval through the service layer using precomputed query embeddings.
- Bounded prompt assembly so retrieved context fits the local Qwen context window.
- Citation preservation from generated requirements.
- Deterministic citation validation against retrieved chunk IDs.
- Repair of common near-match citation IDs only when they map to an actually retrieved chunk.
- Base vs Base+RAG evaluation runner and saved result artifacts.

Verified Phase 3 baseline:

- Result directory: `ai/evaluation/results/eval-20260809-204147-548eb018`.
- Case IDs: `eval-001`, `eval-005`, `eval-007`.
- Base SRS success: 100.0%.
- Base+RAG SRS success: 100.0%.
- RAG retrieval success: 100.0%.
- Citation presence: 100.0%.
- Citation validity: 100.0%.
- Unsupported citation rate: 0.000.

## Future Work

- Phase 4: QLoRA fine-tuning.
- Phase 5: four-way evaluation.
- Phase 6: final PDF/report improvements.
