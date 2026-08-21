# Product Requirements Document — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Author:** Project Architect
**Status:** Phase 0 — Planning

---

## 1. Executive Summary

CyberSRS is a locally deployable, AI-assisted software requirements engineering platform focused on cybersecurity and network-infrastructure projects. A user provides only an informal project description. CyberSRS analyses it, infers the cybersecurity subdomain, asks clarification questions, retrieves domain knowledge via RAG, generates a complete Software Requirements Specification (SRS) — including functional requirements, non-functional requirements, cybersecurity requirements, a threat model, and acceptance criteria — and exports the result as a professional PDF. The system uses Qwen/Qwen3-4B-Instruct-2507 as the single main LLM, with QLoRA fine-tuning to improve requirements-engineering output quality over time.

## 2. Problem Statement

Writing a high-quality SRS for cybersecurity projects requires simultaneously understanding informal stakeholder intent, applying cybersecurity domain knowledge, structuring requirements traceably, and modelling threats. This process is:

1. **Time-consuming** — even experienced engineers spend days producing a first draft.
2. **Error-prone** — missing requirements, unstated assumptions, and inconsistent threat models are common.
3. **Knowledge-intensive** — practitioners must recall or research standards, attack patterns, and architectural best practices.
4. **Inaccessible** — students and small teams often lack the expertise to produce professional-grade documents.

No existing tool combines LLM-based generation with RAG-grounded cybersecurity knowledge, structured-output validation, and threat modelling in a single, locally deployable package.

## 3. Product Vision

To become the reference tool that makes professional-quality cybersecurity requirements engineering accessible to any practitioner — from students to small security teams — without relying on cloud services, without exposing sensitive project data, and without requiring manual domain selection.

## 4. Product Goals

| ID | Goal |
|---|---|
| G-01 | Reduce the time to produce a first-draft cybersecurity SRS from days to under one hour. |
| G-02 | Ensure generated requirements are traceable, testable, and grounded in retrieved domain knowledge. |
| G-03 | Run entirely on a single local machine with no cloud dependencies. |
| G-04 | Automatically infer the cybersecurity subdomain — the user never manually selects a domain. |
| G-05 | Provide a QLoRA fine-tuned model that outperforms the base model on requirements-engineering tasks. |
| G-06 | Produce a professional, exportable PDF document. |

## 5. Non-Goals

| ID | Non-Goal |
|---|---|
| NG-01 | Active penetration testing, exploit execution, malware analysis, or automatic network modification. |
| NG-02 | Multi-user collaboration or real-time co-editing in the MVP. |
| NG-03 | Cloud-hosted SaaS deployment. |
| NG-04 | Support for non-cybersecurity project domains (e.g., e-commerce, healthcare, unless they have a cybersecurity focus). |
| NG-05 | Full formal verification of generated requirements. |
| NG-06 | Integration with external project-management or issue-tracking tools. |
| NG-07 | Automated code generation from requirements. |

## 6. Target Users

### 6.1 Primary Users

- **Software-engineering students** working on cybersecurity capstone or course projects who need to produce an SRS but lack requirements-engineering experience.
- **Individual requirements engineers** who want to accelerate early-phase documentation for security-focused systems.

### 6.2 Secondary Users

- **Small-team security practitioners** building firewalls, IDS, IAM, or VPN systems who need structured documentation.
- **Academic advisors** reviewing student-generated SRS documents.

## 7. User Personas

### Persona 1 — Arjun (Student)

| Attribute | Detail |
|---|---|
| Role | Final-year CS student |
| Context | Capstone project: "Build a network-monitoring system for the campus" |
| Pain point | Has never written a formal SRS; unsure what cybersecurity requirements look like |
| Goal | Generate a complete, well-structured SRS to submit as a deliverable |
| Technical skill | Can run Docker and basic CLI tools; limited security knowledge |

### Persona 2 — Samira (Requirements Engineer)

| Attribute | Detail |
|---|---|
| Role | Junior requirements engineer at a security consultancy |
| Context | New client engagement for a zero-trust network segmentation project |
| Pain point | Spends two to three days writing the first SRS draft; frequently misses edge-case requirements |
| Goal | Produce a thorough first draft in under an hour, then refine manually |
| Technical skill | Strong software-engineering skills; moderate security expertise |

### Persona 3 — David (Security Practitioner)

| Attribute | Detail |
|---|---|
| Role | Network-security engineer at a mid-size company |
| Context | Needs documentation for a VPN and remote-access overhaul |
| Pain point | Documentation is always deprioritised; threat models are ad hoc |
| Goal | Generate requirements and a threat model to present to management |
| Technical skill | Deep networking knowledge; limited formal RE experience |

## 8. Core User Problems

| ID | Problem |
|---|---|
| P-01 | Users cannot quickly translate an informal idea into structured requirements. |
| P-02 | Users miss cybersecurity-specific requirements because they lack domain knowledge. |
| P-03 | Users do not know which clarification questions to ask themselves. |
| P-04 | Users produce inconsistent or untestable requirements. |
| P-05 | Users lack threat-modelling expertise. |
| P-06 | Users want a professional document but lack document-formatting skills. |

## 9. Primary Use Cases

### UC-01: Generate SRS from Informal Description

**Actor:** User
**Precondition:** CyberSRS is running locally.
**Flow:**

1. User creates a new project.
2. User enters an informal description (e.g., "I want to build a firewall and network-monitoring system for a college campus").
3. System analyses the description and infers the cybersecurity subdomain.
4. System identifies missing information.
5. System presents clarification questions.
6. User answers the questions.
7. System retrieves relevant cybersecurity knowledge via RAG.
8. System generates a structured SRS (JSON).
9. System validates the SRS.
10. User reviews the SRS in the UI.
11. User edits or regenerates specific sections.
12. User approves the document.
13. System exports a PDF.

**Postcondition:** A validated, professional SRS PDF is saved locally.

### UC-02: Edit and Regenerate Requirements

**Actor:** User
**Precondition:** An SRS has been generated.
**Flow:**

1. User selects a section or requirement.
2. User edits the text or requests regeneration.
3. System regenerates the selected section while preserving the rest.
4. System re-validates the modified SRS.
5. User reviews the changes.

### UC-03: Resume a Previous Project

**Actor:** User
**Precondition:** A project exists in the database.
**Flow:**

1. User opens the project list.
2. User selects an existing project.
3. System loads the latest SRS version.
4. User continues editing or exports.

## 10. Supported Project Categories

The system must initially support these cybersecurity project types. The category is **inferred** from the user's description — never manually selected.

| ID | Category |
|---|---|
| CAT-01 | Network security systems |
| CAT-02 | Firewalls and network access control |
| CAT-03 | Intrusion detection and security monitoring |
| CAT-04 | Identity and access management (IAM) |
| CAT-05 | Secure web applications and APIs |
| CAT-06 | VPN and secure remote-access systems |
| CAT-07 | Security logging and alerting |
| CAT-08 | Network segmentation and zero-trust-oriented systems |

## 11. Product Capabilities

| ID | Capability |
|---|---|
| CAP-01 | Natural-language project-description analysis |
| CAP-02 | Automatic cybersecurity-subdomain inference |
| CAP-03 | Stakeholder, asset, user, constraint, and goal extraction |
| CAP-04 | Missing-information detection |
| CAP-05 | Clarification-question generation |
| CAP-06 | RAG-based cybersecurity knowledge retrieval |
| CAP-07 | Structured functional-requirement generation |
| CAP-08 | Structured non-functional-requirement generation |
| CAP-09 | Cybersecurity-requirement generation |
| CAP-10 | High-level system-architecture generation |
| CAP-11 | Threat-model generation |
| CAP-12 | Acceptance-criteria and testing-recommendation generation |
| CAP-13 | Requirement-quality validation |
| CAP-14 | User review and editing |
| CAP-15 | Section-level regeneration |
| CAP-16 | PDF export |
| CAP-17 | QLoRA fine-tuning for improved output quality |

---

## 12. Functional Requirements

### 12.1 Project Management

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | The system shall allow the user to create a new project with a name and informal description. | Must |
| FR-002 | The system shall allow the user to list all existing projects. | Must |
| FR-003 | The system shall allow the user to open an existing project and view its latest SRS version. | Must |
| FR-004 | The system shall allow the user to update a project's name or description. | Should |
| FR-005 | The system shall allow the user to delete a project and all associated data. | Should |

### 12.2 Description Analysis

| ID | Requirement | Priority |
|---|---|---|
| FR-010 | The system shall analyse the informal project description using the main LLM. | Must |
| FR-011 | The system shall infer the relevant cybersecurity subdomain(s) from the description without requiring manual selection. | Must |
| FR-012 | The system shall extract stakeholders, assets, users, constraints, and goals from the description. | Must |
| FR-013 | The system shall detect missing information in the description. | Must |
| FR-014 | The system shall generate the analysis result as validated JSON conforming to a predefined schema. | Must |

### 12.3 Clarification Questions

| ID | Requirement | Priority |
|---|---|---|
| FR-020 | The system shall generate a set of essential clarification questions when missing information is detected. | Must |
| FR-021 | The system shall present clarification questions to the user in the UI. | Must |
| FR-022 | The system shall accept the user's answers and incorporate them into the project context. | Must |
| FR-023 | The system shall allow the user to skip non-critical clarification questions. | Should |
| FR-024 | The system shall generate clarification questions as validated JSON. | Must |

### 12.4 RAG Retrieval

| ID | Requirement | Priority |
|---|---|---|
| FR-030 | The system shall retrieve relevant cybersecurity knowledge from the vector database based on the project context. | Must |
| FR-031 | The system shall rank retrieved chunks by relevance score. | Must |
| FR-032 | The system shall include source-document metadata with each retrieved chunk. | Must |
| FR-033 | The system shall pass the top-k retrieved chunks as context to the LLM during SRS generation. | Must |
| FR-034 | The system shall provide a knowledge-ingestion pipeline to add documents to the vector database. | Must |

### 12.5 SRS Generation

| ID | Requirement | Priority |
|---|---|---|
| FR-040 | The system shall generate structured functional requirements using the main LLM. | Must |
| FR-041 | The system shall generate structured non-functional requirements. | Must |
| FR-042 | The system shall generate cybersecurity-specific requirements. | Must |
| FR-043 | The system shall generate a high-level system architecture description. | Must |
| FR-044 | The system shall generate a threat model identifying threats and mitigations. | Must |
| FR-045 | The system shall generate acceptance criteria and testing recommendations. | Must |
| FR-046 | The system shall produce all SRS sections as validated JSON before any rendering. | Must |
| FR-047 | The system shall assign a unique requirement ID to each generated requirement. | Must |
| FR-048 | The system shall record which retrieved chunks were used for each generated section. | Must |

### 12.6 Requirement Validation

| ID | Requirement | Priority |
|---|---|---|
| FR-050 | The system shall validate generated requirements for completeness (all mandatory SRS sections present). | Must |
| FR-051 | The system shall validate generated requirements for testability (each requirement is verifiable). | Must |
| FR-052 | The system shall validate generated requirements for consistency (no contradictions detected). | Should |
| FR-053 | The system shall flag validation issues and present them to the user. | Must |
| FR-054 | The system shall assign a quality score to each generated SRS. | Should |

### 12.7 Review and Editing

| ID | Requirement | Priority |
|---|---|---|
| FR-060 | The system shall display the generated SRS in a structured, section-by-section view. | Must |
| FR-061 | The system shall allow the user to edit any requirement or section. | Must |
| FR-062 | The system shall allow the user to regenerate a selected section without regenerating the entire SRS. | Must |
| FR-063 | The system shall preserve user edits in sections that are not regenerated. | Must |
| FR-064 | The system shall maintain version history of SRS generations. | Should |
| FR-065 | The system shall display source references for requirements derived from retrieved knowledge. | Must |

### 12.8 PDF Export

| ID | Requirement | Priority |
|---|---|---|
| FR-070 | The system shall export the approved SRS as a PDF document. | Must |
| FR-071 | The system shall use a professional template for the PDF. | Must |
| FR-072 | The system shall include a table of contents, requirement traceability matrix, and references in the PDF. | Should |
| FR-073 | The system shall generate the PDF from the validated JSON structure, not from raw LLM text. | Must |

### 12.9 Conversational Assistant

| ID | Requirement | Priority |
|---|---|---|
| FR-080 | The system shall answer general cybersecurity questions through a conversational interface without automatically creating a project. | Must |
| FR-081 | The assistant shall use the local RAG knowledge base for relevant questions and return validated source citations. | Must |
| FR-082 | The system shall preserve a detected project description until the user explicitly confirms SRS generation. | Must |
| FR-083 | The UI shall retain submitted messages and show a retryable error when chat delivery or generation fails. | Must |
| FR-084 | General conversation shall use the base main model and shall not require RAG. | Must |
| FR-085 | Analysis, clarification, SRS generation, and SRS editing shall use the configured SRS-task model variant. | Must |
| FR-086 | Users shall be able to upload safe PDF, Markdown, text, and CSV reference documents to a project. | Must |
| FR-087 | Project documents shall inform analysis and SRS generation while remaining isolated from the global knowledge base and other projects. | Must |
| FR-088 | A project-specific SRS request or requirements document shall immediately enter analysis and clarification review, and generation shall wait for submitted answers. | Must |
| FR-089 | Users shall be able to permanently delete a locally stored chat, which shall disappear from the sidebar immediately. | Must |
| FR-090 | Users shall be able to pin and unpin chats, with pinned chats persisted and displayed above date-grouped conversations. | Should |

---

## 13. Non-Functional Requirements

### 13.1 Performance

| ID | Requirement | Priority |
|---|---|---|
| NFR-001 | The system shall return the description-analysis result within 30 seconds on consumer hardware with the main LLM running locally. | Should |
| NFR-002 | The system shall generate a complete SRS within 5 minutes on consumer hardware. | Should |
| NFR-003 | The system shall return RAG retrieval results within 5 seconds. | Should |
| NFR-004 | The API shall respond to non-LLM requests within 500 ms. | Should |

### 13.2 Usability

| ID | Requirement | Priority |
|---|---|---|
| NFR-010 | The system shall provide clear progress indicators during LLM generation. | Must |
| NFR-011 | The system shall display validation issues inline next to the relevant requirement. | Should |
| NFR-012 | The system shall be usable without reading a manual — the UI flow should be self-guiding. | Should |

### 13.3 Reliability

| ID | Requirement | Priority |
|---|---|---|
| NFR-020 | The system shall handle LLM failures gracefully by retrying up to a configurable limit and surfacing errors to the user. | Must |
| NFR-021 | The system shall handle RAG retrieval failures by generating requirements without retrieved context and warning the user. | Must |
| NFR-022 | The system shall handle invalid JSON from the LLM by retrying with a corrective prompt. | Must |
| NFR-023 | The system shall persist all project data to SQLite; no data shall be lost on application restart. | Must |

### 13.4 Maintainability

| ID | Requirement | Priority |
|---|---|---|
| NFR-030 | The codebase shall be structured as a modular monolith with clear service boundaries. | Must |
| NFR-031 | All Python code shall have type hints and docstrings. | Must |
| NFR-032 | The LLM provider shall be abstracted behind an interface to allow future provider changes. | Must |

---

## 14. Security and Privacy Requirements

| ID | Requirement | Priority |
|---|---|---|
| SEC-001 | The system shall not perform active penetration testing, exploit execution, malware execution, or automatic network modification. | Must |
| SEC-002 | The system shall not transmit any user data to external services. | Must |
| SEC-003 | The system shall not store credentials or secrets in source code or logs. | Must |
| SEC-004 | The system shall not generate executable attack code in SRS output. | Must |
| SEC-005 | The system shall sanitise user input before passing it to the LLM. | Must |
| SEC-006 | The system shall not log full project descriptions at DEBUG level in production. | Should |
| SEC-007 | The system shall not include the SQLite database in version control. | Must |

## 15. Data Requirements

| ID | Requirement | Priority |
|---|---|---|
| DATA-001 | The system shall store projects, SRS versions, and clarification data in SQLite. | Must |
| DATA-002 | The system shall store vector embeddings in ChromaDB. | Must |
| DATA-003 | The system shall preserve source-document metadata through the entire pipeline. | Must |
| DATA-004 | The system shall support exporting project data as JSON for backup. | Should |
| DATA-005 | The system shall use UTC timestamps for all stored records. | Must |

## 16. AI and Model Requirements

| ID | Requirement | Priority |
|---|---|---|
| AI-001 | The system shall use Qwen/Qwen3-4B-Instruct-2507 as the main LLM. | Must |
| AI-002 | The system shall support loading a QLoRA fine-tuned adapter alongside the base model. | Must |
| AI-003 | The system shall include structured system prompts for each generation task (analysis, clarification, SRS generation, validation, threat modelling). | Must |
| AI-004 | The system shall validate all LLM output against predefined JSON schemas. | Must |
| AI-005 | The system shall retry LLM calls with a corrective prompt when output fails validation, up to a configurable maximum. | Must |
| AI-006 | The system shall log generation metadata (model version, adapter version, prompt template version, generation time). | Should |
| AI-007 | The system shall support comparative evaluation between base-model and fine-tuned-model outputs. | Must |

## 17. RAG Requirements

| ID | Requirement | Priority |
|---|---|---|
| RAG-001 | The system shall provide a pipeline to ingest cybersecurity documents (PDF, Markdown, plain text) into ChromaDB. | Must |
| RAG-002 | The system shall chunk documents with configurable chunk size and overlap. | Must |
| RAG-003 | The system shall embed chunks using an embedding model (to be selected). | Must |
| RAG-004 | The system shall retrieve top-k chunks relevant to the project context. | Must |
| RAG-005 | The system shall preserve source-document metadata (title, author, section, page) in each chunk. | Must |
| RAG-006 | The system shall display source references to the user for transparency. | Must |
| RAG-007 | The system shall function without RAG when the vector database is empty, falling back to base-model knowledge only. | Should |

## 18. UX Requirements

| ID | Requirement | Priority |
|---|---|---|
| UX-001 | The system shall present a single-page workflow that guides the user from project creation to PDF export. | Must |
| UX-002 | The system shall not require the user to manually select a cybersecurity domain. | Must |
| UX-003 | The system shall show a progress indicator during each LLM generation step. | Must |
| UX-004 | The system shall allow section-level navigation in the generated SRS. | Must |
| UX-005 | The system shall provide inline editing for any requirement or section. | Must |
| UX-006 | The system shall clearly indicate which requirements are sourced from retrieved knowledge. | Should |
| UX-007 | The system shall be usable on a 1366×768 screen. | Should |

---

## 19. Local-First Constraints

- The entire application (frontend, backend, LLM, vector database) must run on a single machine.
- No internet connection shall be required after initial setup (model download, dependency installation, knowledge-base ingestion).
- The application must work on machines with ≥ 8 GB RAM and a modern CPU (GPU recommended but not required for inference with Ollama).

## 20. Assumptions

| ID | Assumption |
|---|---|
| A-01 | The user has Ollama installed and the Qwen3-4B model pulled before first use. |
| A-02 | The user's machine has at least 8 GB of RAM. |
| A-03 | The user provides descriptions in English. |
| A-04 | The cybersecurity knowledge base will be seeded with publicly available documents (NIST, OWASP, CIS, etc.). |
| A-05 | The project is built and evaluated by a single student. |

## 21. Dependencies

| ID | Dependency | Type |
|---|---|---|
| D-01 | Ollama runtime | External runtime |
| D-02 | Qwen/Qwen3-4B-Instruct-2507 model weights | External model |
| D-03 | Python 3.11+ | Language runtime |
| D-04 | Node.js 18+ and npm | Build tool |
| D-05 | Hugging Face Transformers, PEFT, TRL | Python libraries |
| D-06 | ChromaDB | Python library |
| D-07 | Publicly available cybersecurity documents for RAG | External data |

## 22. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Qwen3-4B produces low-quality or off-topic requirements | Medium | High | Structured prompts, JSON-schema validation, QLoRA fine-tuning |
| R-02 | QLoRA fine-tuning does not significantly improve output | Medium | Medium | Use rigorous comparative evaluation; fall back to prompt engineering |
| R-03 | RAG retrieval returns irrelevant chunks | Medium | Medium | Tune embedding model, chunk size, and top-k; allow fallback |
| R-04 | 4B parameter model is too slow on CPU-only hardware | Medium | Medium | Provide Ollama quantisation guidance; set realistic timeout |
| R-05 | Single developer cannot complete all phases | Low | High | Phased roadmap with clear completion gates; prioritise MVP |
| R-06 | Generated output contains unsafe cybersecurity advice | Low | High | Output validation, safety guardrails in prompts, no executable code |

## 23. MVP Acceptance Criteria

The MVP is complete when:

1. A user can create a project by entering only an informal description.
2. The system infers the cybersecurity subdomain without manual selection.
3. The system asks at least 3 relevant clarification questions.
4. The system retrieves relevant knowledge from a seeded ChromaDB instance.
5. The system generates a complete SRS containing functional requirements, non-functional requirements, cybersecurity requirements, a threat model, and acceptance criteria — all as validated JSON.
6. The user can review, edit, and regenerate individual sections.
7. The user can export the SRS as a PDF.
8. The system runs entirely locally.
9. A QLoRA fine-tuned adapter exists and can be loaded for generation.
10. A comparative evaluation between base-model and fine-tuned outputs is documented.

## 24. Success Metrics

| Metric | Target |
|---|---|
| Time from description to first SRS draft | < 60 minutes |
| Percentage of generated requirements that are testable | ≥ 80 % |
| JSON-schema validation pass rate | ≥ 95 % on first attempt |
| User edits required to finalise SRS | < 30 % of generated content |
| Fine-tuned model improvement over base model | Measurable improvement on evaluation dataset |

## 25. Future Enhancements (Post-MVP)

| ID | Enhancement |
|---|---|
| FE-01 | Support additional project domains beyond cybersecurity |
| FE-02 | Multi-user collaboration and role-based access |
| FE-03 | Integration with issue trackers (Jira, GitHub Issues) |
| FE-04 | Interactive threat-model diagram editor |
| FE-05 | Multi-language SRS generation |
| FE-06 | PostgreSQL or other production-grade database |
| FE-07 | Cloud-hosted deployment option |
| FE-08 | Compliance-mapping to specific standards (ISO 27001, NIST CSF) |
| FE-09 | Version-diff visualisation between SRS versions |
| FE-10 | Automated requirement-priority suggestions |
