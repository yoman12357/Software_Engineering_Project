# AGENTS.md — Coding-Agent Instructions for CyberSRS

> Every coding agent (human or AI) must read this file **and** the referenced planning documents before writing or modifying code in this repository.

---

## 1. Project Purpose

CyberSRS is a locally deployable, AI-assisted platform that generates complete Software Requirements Specifications (SRS) for cybersecurity and network-infrastructure projects. The user provides only an informal project description; the system infers the domain, asks clarification questions, retrieves domain knowledge via RAG, generates structured requirements, validates them, and exports a professional PDF.

## 2. Approved Technology Stack

| Component | Technology | Notes |
|---|---|---|
| Main LLM | Qwen/Qwen3-4B-Instruct-2507 | Single model for inference, RAG-assisted generation, and QLoRA fine-tuning |
| Fine-tuning | QLoRA via Hugging Face Transformers, PEFT, TRL | For improving requirements-engineering output quality |
| Backend | Python 3.11+, FastAPI | Modular monolith, no microservices |
| Frontend | React 18+, TypeScript, Vite | Single-page application |
| Database | SQLite | MVP only; upgrade path to PostgreSQL is reserved |
| Vector database | ChromaDB | For RAG retrieval |
| Local model serving | Ollama | Behind a provider-independent interface |
| Document generation | Structured JSON → template-based PDF | JSON is the canonical representation |
| Embedding model | TBD | Retrieval utility only; not the main LLM |

Do **not** introduce additional frameworks, ORMs, or LLM providers without an approved ADR in `docs/adr/`.

## 3. Main-Model Decision

The single main LLM for CyberSRS is **Qwen/Qwen3-4B-Instruct-2507**.

- All prompt engineering, structured-output schemas, and evaluation benchmarks must target this model.
- An embedding model may be used for vector retrieval, but it is a utility, not the main model.
- See [ADR-0001](docs/adr/0001-main-model.md).

## 4. Architectural Principles

1. **Modular monolith.** All services live in a single deployable unit. No microservices.
2. **Provider-independent LLM interface.** The application calls an abstract `LLMProvider` interface, not Ollama directly.
3. **Structured JSON first.** Every LLM-generated artefact is produced as validated JSON before any rendering (see [ADR-0003](docs/adr/0003-structured-json-first.md)).
4. **Deterministic vs generative separation.** Business logic (validation, routing, PDF rendering) must be deterministic Python code, not LLM output.
5. **Local-first deployment.** The application must run entirely on a single machine with no cloud dependencies (see [ADR-0004](docs/adr/0004-local-first-deployment.md)).
6. **RAG ≠ fine-tuning.** RAG retrieves current domain knowledge and provides source citations. Fine-tuning improves the model's requirements-engineering behaviour and output structure. These responsibilities must not be conflated.

## 5. Security Boundaries

### Hard prohibitions

The application must **never**:

- Perform active penetration testing or vulnerability scanning against live systems.
- Execute exploits, malware, or attack payloads.
- Modify network configurations, firewall rules, or system settings automatically.
- Store or transmit credentials, API keys, or secrets in plain text within the codebase.
- Suggest executable attack code in generated requirements.

### Data handling

- All data stays local. No telemetry, analytics, or external API calls (except to the locally hosted Ollama instance).
- Personally identifiable information (PII) entered in project descriptions must not be logged verbatim in debug logs.
- SQLite database files must not be committed to version control.

## 6. Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Python files | `snake_case.py` | `srs_generator.py` |
| Python classes | `PascalCase` | `SRSGenerationService` |
| Python functions/methods | `snake_case` | `generate_requirements()` |
| Python constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| TypeScript files | `PascalCase.tsx` / `camelCase.ts` | `ProjectView.tsx`, `apiClient.ts` |
| TypeScript components | `PascalCase` | `ClarificationPanel` |
| TypeScript functions | `camelCase` | `fetchProject()` |
| API paths | `kebab-case` | `/api/v1/projects/{id}/srs-versions` |
| Database tables | `snake_case` | `clarification_question` |
| Environment variables | `UPPER_SNAKE_CASE` prefixed with `CYBERSRS_` | `CYBERSRS_OLLAMA_BASE_URL` |
| Requirement IDs | Prefix + sequential number | `FR-001`, `SEC-012` |

## 7. Documentation Rules

1. Every public Python function and class must have a docstring.
2. Every new API endpoint must be documented in `docs/API_CONTRACT.md` before implementation.
3. Every architectural change must have an ADR in `docs/adr/`.
4. New requirement IDs must be registered in `docs/REQUIREMENTS_CATALOG.md`.
5. The README must remain accurate as the project evolves.

## 8. Testing Expectations

| Layer | Minimum expectation |
|---|---|
| Unit tests | All service-layer functions; all JSON-schema validators; all data-access functions |
| Integration tests | API endpoint round-trips; database read/write; LLM provider interface with mocked responses |
| Schema validation tests | Every LLM-generated JSON output must be validated against its Pydantic or JSON-Schema definition |
| Evaluation tests | Compare LLM output quality against a reference dataset when fine-tuned adapters are loaded |
| Manual tests | PDF export visual inspection; end-to-end workflow on at least two project descriptions |

- Use **pytest** as the test runner.
- Use **pytest-asyncio** for async tests.
- Maintain a `tests/` directory mirroring `src/` structure.
- Tests must pass before any merge or phase transition.

## 9. Environment Variables and Secrets

- All configuration must be read from environment variables or a `.env` file.
- The `.env` file must be listed in `.gitignore`.
- Provide a `.env.example` with placeholder values and comments.
- Prefix all environment variables with `CYBERSRS_`.
- Never hard-code model names, ports, file paths, or API base URLs.

## 10. LLM Output Validation

- Every LLM response used by the application must be parsed and validated against a predefined schema (Pydantic model or JSON Schema).
- If validation fails, the application must retry with a corrective prompt (up to a configurable limit) or surface a structured error to the user.
- Raw LLM output must never be rendered directly in the UI without validation.

## 11. RAG Source-Citation Rules

- Every retrieved chunk must carry its `source_document_id`, `chunk_index`, `page_or_section`, and `relevance_score`.
- Generated requirements that rely on retrieved knowledge must include a `sources` field listing the chunks used.
- Source metadata must be preserved end-to-end from ingestion through generation to PDF export.

## 12. Task-Execution Rules for Agents

1. **Read first.** Before modifying any code, read `AGENTS.md`, `docs/PRD.md`, `docs/SCOPE.md`, `docs/ARCHITECTURE.md`, and the relevant section of `docs/ROADMAP.md`.
2. **One bounded task at a time.** Do not combine unrelated changes in a single work session.
3. **Do not rewrite unrelated files.** If a task is "add PDF export," do not refactor the database layer in the same changeset.
4. **Report tests executed.** At the end of every task, list the tests you ran and their results.
5. **Do not claim success when tests fail.** If any test fails, report the failure and either fix it or flag it.
6. **Preserve existing behaviour.** Do not remove or rename public interfaces unless the task explicitly requires it.
7. **No speculative features.** Implement only what the current phase requires.

## 13. Definition of Done

A coding task is complete when:

- [ ] The feature or fix is implemented as described in the task.
- [ ] All new code has docstrings and type hints.
- [ ] Unit tests cover the new code and pass.
- [ ] Integration tests (if applicable) pass.
- [ ] LLM-generated output is validated against schemas.
- [ ] Source citations are preserved in RAG-related features.
- [ ] No new linting errors are introduced.
- [ ] Documentation (`API_CONTRACT.md`, `REQUIREMENTS_CATALOG.md`, etc.) is updated if affected.
- [ ] The agent has listed all tests executed and their results.
- [ ] No unrelated files were modified.
