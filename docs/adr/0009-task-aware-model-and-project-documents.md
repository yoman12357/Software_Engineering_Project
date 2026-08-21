# ADR-0009: Task-Aware Model Routing and Project Documents

**Status:** Accepted
**Date:** 2026-08-21

## Context

CyberSRS must answer ordinary questions with the approved local main model while preserving an SRS-specialised path that can later load a QLoRA-derived model. Users also need to provide project specifications without adding private project material to the shared cybersecurity knowledge base.

## Decision

The provider-independent `LLMProvider` interface remains the only model boundary. The application creates a general provider fixed to the base Qwen model and an SRS-task provider selected by `CYBERSRS_MODEL_VARIANT`. General chat uses the former. Analysis, clarification, SRS generation, and SRS editing use the latter. Both may share one instance when the base variant is selected.

Project uploads use generated storage names under a configured local directory. Metadata and bounded extracted text are stored in SQLite. When RAG is enabled, chunks are stored in a separate ChromaDB collection and queried with a mandatory project-ID filter. Uploaded data never enters the global knowledge collection or a training dataset.

## Consequences

- A requirements-engineering adapter cannot narrow general chat.
- The application stays local-first and provider-independent.
- Uploaded content contributes to analysis even when ChromaDB is unavailable.
- File type, size, count, path containment, parsing, deletion, and prompt-size limits require deterministic enforcement and tests.
