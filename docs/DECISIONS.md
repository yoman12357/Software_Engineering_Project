# Decision Log — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

---

## Approved Decisions

These decisions are final unless a new ADR supersedes them.

| ID | Decision | Rationale | ADR |
|---|---|---|---|
| DEC-001 | **Main LLM:** Qwen/Qwen3-4B-Instruct-2507 | Selected for the project as the single model for inference, RAG-assisted generation, and QLoRA fine-tuning. Balances capability and local-deployment feasibility. | [ADR-0001](adr/0001-main-model.md) |
| DEC-002 | **Backend:** Python + FastAPI | FastAPI provides async support, automatic OpenAPI docs, and Pydantic integration. Python is the natural choice for ML/LLM ecosystem. | [ADR-0002](adr/0002-application-stack.md) |
| DEC-003 | **Frontend:** React + TypeScript + Vite | React is the most widely adopted frontend framework. TypeScript adds type safety. Vite provides fast dev experience. | [ADR-0002](adr/0002-application-stack.md) |
| DEC-004 | **Database (MVP):** SQLite | Simple, file-based, zero-config. Sufficient for single-user local deployment. | [ADR-0002](adr/0002-application-stack.md) |
| DEC-005 | **Vector database:** ChromaDB | Lightweight, embeddable, Python-native. Good fit for local deployment. | [ADR-0002](adr/0002-application-stack.md) |
| DEC-006 | **Local model serving:** Ollama | Simple CLI and HTTP API for running models locally. Wide model support. | [ADR-0004](adr/0004-local-first-deployment.md) |
| DEC-007 | **Document generation:** Structured JSON → template-based PDF | Ensures data integrity, enables editing and re-rendering, separates content from presentation. | [ADR-0003](adr/0003-structured-json-first.md) |
| DEC-008 | **Fine-tuning method:** QLoRA via Hugging Face PEFT + TRL | Parameter-efficient fine-tuning suitable for consumer hardware. | [ADR-0001](adr/0001-main-model.md) |
| DEC-009 | **Architecture:** Modular monolith (no microservices) | Simplicity for single-developer project. All services in one process. | [ADR-0002](adr/0002-application-stack.md) |
| DEC-010 | **Local-first deployment** | All components run on a single machine. No cloud dependencies. | [ADR-0004](adr/0004-local-first-deployment.md) |
| DEC-011 | **LLM interface:** Provider-independent abstraction | Allows future swapping of LLM providers without changing application logic. | [ADR-0002](adr/0002-application-stack.md) |
| DEC-012 | **No active exploitation features** | Safety requirement. CyberSRS generates requirements documents, not attack tools. | [ADR-0008](adr/0008-security-boundaries.md) |
| DEC-013 | **No manual domain selection** | The system infers the cybersecurity subdomain. The user never chooses from a dropdown. | — |
| DEC-014 | **RAG vs. fine-tuning responsibility split** | RAG provides current domain knowledge and source citations. Fine-tuning improves requirements-engineering behaviour and output structure. They are complementary, not interchangeable. | [ADR-0005](adr/0005-rag-responsibilities.md), [ADR-0006](adr/0006-finetuning-responsibilities.md) |
| DEC-015 | **Environment variables prefixed with `CYBERSRS_`** | Prevents naming collisions; makes configuration discoverable. | — |
| DEC-016 | **UTC timestamps everywhere** | Eliminates timezone ambiguity in stored data. | — |
| DEC-017 | **Four-way evaluation design** (C1/C2/C3/C4) | Isolates RAG contribution from fine-tuning contribution using a 2×2 experimental design. Essential for academic rigour. | [ADR-0007](adr/0007-evaluation-baselines.md) |
| DEC-018 | **RAG provides knowledge; fine-tuning provides behaviour** | RAG supplies OWASP, NIST, MITRE ATT&CK, CIS content and citations. Fine-tuning improves JSON compliance, atomicity, testability, and requirement structure. Neither replaces the other. | [ADR-0005](adr/0005-rag-responsibilities.md), [ADR-0006](adr/0006-finetuning-responsibilities.md) |
| DEC-019 | **Sectioned SRS generation** (one LLM call per section) | Avoids overwhelming a 4B model. Each section is generated, validated, and stored independently. | — |
| DEC-020 | **No reranking in MVP** | Embedding-model ranking is used directly. Cross-encoder reranking deferred to post-MVP. | — |
| DEC-021 | **Safety boundaries: describe threats yes, produce exploits no** | Threat descriptions (STRIDE, ATT&CK references) are permitted. Executable attack code, exploit generation, and active scanning are prohibited. | [ADR-0008](adr/0008-security-boundaries.md) |

---

## Unresolved Decisions

These decisions have not been made yet. They should be resolved in the phase indicated.

| ID | Question | Options Under Consideration | Needed By Phase | Notes |
|---|---|---|---|---|
| UDEC-001 | **Which embedding model to use for ChromaDB?** | `all-MiniLM-L6-v2`, `nomic-embed-text`, `bge-small-en-v1.5`, Ollama-hosted embedding | Phase 4 | Must be locally runnable. Evaluate on cybersecurity text retrieval quality. |
| UDEC-002 | **Which PDF generation library?** | `WeasyPrint`, `ReportLab`, `FPDF2`, `pdfkit` (wkhtmltopdf) | Phase 6 | Must support professional templates, table of contents, and Unicode. |
| UDEC-003 | **How to handle Ollama adapter loading?** | Ollama native Modelfile with adapter, or bypass Ollama and use Hugging Face Transformers directly for fine-tuned inference | Phase 8 | Depends on Ollama's adapter-loading support at implementation time. |
| UDEC-004 | **Which evaluation metrics for fine-tuning comparison?** | BLEU, ROUGE, BERTScore, custom schema-compliance score, human evaluation rubric | Phase 9 | Need both automated and qualitative metrics. |
| UDEC-005 | **State management approach for the React frontend?** | React Context + useReducer, Zustand, TanStack Query for server state | Phase 1 | Should be lightweight. Avoid Redux complexity. |
| UDEC-006 | **Prompt-engineering approach:** single mega-prompt vs. multi-step chain? | Single prompt per section, multi-step chain with intermediate validation, or hybrid | Phase 2 | Depends on Qwen3-4B's performance with complex prompts. Experiment required. |
| UDEC-007 | **SRS generation: synchronous vs. asynchronous?** | Synchronous with streaming, async with polling, or async with WebSocket updates | Phase 3 | Async with polling is simplest for MVP; WebSocket is better UX. |
| UDEC-008 | **How to chunk cybersecurity documents?** | Fixed token count, sentence-based, paragraph-based, section-based, or hybrid | Phase 4 | Needs experimentation with cybersecurity documents. |
| UDEC-009 | **Docker support:** official Dockerfile or optional community contribution? | Official Dockerfile, docker-compose, or no Docker | Phase 10 | Docker is optional for convenience but must not be required. |
| UDEC-010 | **Licence for the project** | MIT, Apache 2.0, GPL-3.0, or academic use only | Phase 10 | Depends on student/university policy. |
| UDEC-011 | **Which PDF parser for knowledge ingestion?** | `PyMuPDF`, `pdfplumber`, `pymupdf4llm` | Phase 4 | Must extract text with page numbers; handle multi-column NIST PDFs. |
| UDEC-012 | **Optimal chunk size for cybersecurity documents?** | 256, 512, or 1024 tokens (experimentally validated) | Phase 4 | Default 512; must be tested on retrieval precision with cybersecurity queries. |

---

## Decision-Making Rules

1. **Do not silently make unresolved decisions.** When a decision is needed, add it to the "Unresolved" table with options.
2. **Resolve decisions when needed, not before.** Premature decisions create unnecessary constraints.
3. **Document alternatives considered.** Every resolved decision should list what was rejected and why.
4. **Create an ADR for significant decisions.** If a decision affects architecture, technology choice, or security, it deserves an ADR in `docs/adr/`.
