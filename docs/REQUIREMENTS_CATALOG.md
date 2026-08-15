# Requirements Catalogue — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

> This is the traceable master catalogue of all requirements. Every requirement has a unique, stable ID and is cross-referenced with the PRD. Requirements are grouped by category.

---

## Legend

| Column                  | Description                                           |
| ----------------------- | ----------------------------------------------------- |
| **ID**                  | Unique stable identifier (prefix + sequential number) |
| **Category**            | FR, NFR, SEC, DATA, AI, RAG, UX                       |
| **Statement**           | Testable "The system shall…" language                 |
| **Priority**            | Must / Should / Could                                 |
| **Rationale**           | Why this requirement exists                           |
| **Acceptance Criteria** | How to verify the requirement is met                  |
| **Phase**               | Roadmap phase when this is implemented                |
| **Dependencies**        | Other requirement IDs this depends on                 |
| **Verification**        | Test, Inspection, Demonstration, or Analysis          |

---

## Functional Requirements (FR)

### Project Management

| ID     | Category | Statement                                                                                     | Priority | Rationale                                                       | Acceptance Criteria                                                                                     | Phase | Dependencies | Verification |
| ------ | -------- | --------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----- | ------------ | ------------ |
| FR-001 | FR       | The system shall allow the user to create a new project with a name and informal description. | Must     | Entry point for all workflows.                                  | A project record is created in SQLite with the given name and description.                              | 1     | —            | Test         |
| FR-002 | FR       | The system shall allow the user to list all existing projects.                                | Must     | Users need to resume previous work.                             | GET /projects returns a list of all projects with id, name, and created_at.                             | 1     | FR-001       | Test         |
| FR-003 | FR       | The system shall allow the user to open an existing project and view its latest SRS version.  | Must     | Core navigation requirement.                                    | Project detail page shows project metadata and latest SRS (if generated).                               | 1     | FR-001       | Test         |
| FR-004 | FR       | The system shall allow the user to update a project's name or description.                    | Should   | Users may want to refine their description after initial entry. | PUT /projects/{id} updates the project and re-analysis is triggered.                                    | 1     | FR-001       | Test         |
| FR-005 | FR       | The system shall allow the user to delete a project and all associated data.                  | Should   | Housekeeping; storage management.                               | DELETE /projects/{id} removes the project, SRS versions, clarifications, and exports from the database. | 1     | FR-001       | Test         |

### Description Analysis

| ID     | Category | Statement                                                                                                               | Priority | Rationale                                      | Acceptance Criteria                                                                                                                           | Phase | Dependencies   | Verification        |
| ------ | -------- | ----------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------------- | ------------------- |
| FR-010 | FR       | The system shall analyse the informal project description using the main LLM.                                           | Must     | Core AI capability.                            | LLM is called with the description and a structured analysis prompt; response is received.                                                    | 2     | FR-001, AI-001 | Test                |
| FR-011 | FR       | The system shall infer the relevant cybersecurity subdomain(s) from the description without requiring manual selection. | Must     | Key UX principle — no manual domain selection. | Analysis result contains inferred_categories matching at least one of CAT-01 through CAT-08. User is never shown a domain-selection dropdown. | 2     | FR-010         | Test, Demonstration |
| FR-012 | FR       | The system shall extract stakeholders, assets, users, constraints, and goals from the description.                      | Must     | Builds the project context for SRS generation. | Analysis JSON contains non-empty arrays for stakeholders, assets, users, constraints, and goals.                                              | 2     | FR-010         | Test                |
| FR-013 | FR       | The system shall detect missing information in the description.                                                         | Must     | Drives the clarification workflow.             | Analysis JSON contains a missing_information array (may be empty for very complete descriptions).                                             | 2     | FR-010         | Test                |
| FR-014 | FR       | The system shall generate the analysis result as validated JSON conforming to a predefined schema.                      | Must     | Ensures structured, reliable output.           | LLM output is parsed against the ProjectAnalysis Pydantic model without errors.                                                               | 2     | FR-010, AI-004 | Test                |

### Clarification Questions

| ID     | Category | Statement                                                                                                  | Priority | Rationale                                                 | Acceptance Criteria                                                                      | Phase | Dependencies   | Verification  |
| ------ | -------- | ---------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ----- | -------------- | ------------- |
| FR-020 | FR       | The system shall generate a set of essential clarification questions when missing information is detected. | Must     | Improves SRS quality by filling information gaps.         | When missing_information is non-empty, the system generates ≥ 1 clarification question.  | 2     | FR-013         | Test          |
| FR-021 | FR       | The system shall present clarification questions to the user in the UI.                                    | Must     | Users must be able to see and answer questions.           | Clarification panel shows question text, reason, and criticality flag.                   | 2     | FR-020         | Demonstration |
| FR-022 | FR       | The system shall accept the user's answers and incorporate them into the project context.                  | Must     | Answers enrich the project context for better generation. | Submitted answers are stored in the database and included in the ProjectContext object.  | 2     | FR-021         | Test          |
| FR-023 | FR       | The system shall allow the user to skip non-critical clarification questions.                              | Should   | Reduces friction; some questions may not have answers.    | Questions with criticality=false can be submitted without an answer.                     | 2     | FR-021         | Test          |
| FR-024 | FR       | The system shall generate clarification questions as validated JSON.                                       | Must     | Consistency with structured-JSON-first principle.         | LLM output is parsed against the ClarificationQuestionSet Pydantic model without errors. | 2     | FR-020, AI-004 | Test          |

### RAG Retrieval

| ID     | Category | Statement                                                                                                         | Priority | Rationale                                           | Acceptance Criteria                                                                        | Phase | Dependencies     | Verification |
| ------ | -------- | ----------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----- | ---------------- | ------------ |
| FR-030 | FR       | The system shall retrieve relevant cybersecurity knowledge from the vector database based on the project context. | Must     | Grounds requirements in domain knowledge.           | ChromaDB query returns ≥ 1 chunk for a supported project category.                         | 4     | RAG-001, RAG-004 | Test         |
| FR-031 | FR       | The system shall rank retrieved chunks by relevance score.                                                        | Must     | Ensures the most relevant knowledge is prioritised. | Chunks are returned in descending order of relevance_score.                                | 4     | FR-030           | Test         |
| FR-032 | FR       | The system shall include source-document metadata with each retrieved chunk.                                      | Must     | Enables traceability and citations.                 | Each chunk includes source_document_id, chunk_index, page_or_section, and relevance_score. | 4     | FR-030, RAG-005  | Test         |
| FR-033 | FR       | The system shall pass the top-k retrieved chunks as context to the LLM during SRS generation.                     | Must     | RAG-augmented generation core requirement.          | The SRS-generation prompt includes the content of the top-k chunks.                        | 4     | FR-030, FR-040   | Inspection   |
| FR-034 | FR       | The system shall provide a knowledge-ingestion pipeline to add documents to the vector database.                  | Must     | The knowledge base must be populated.               | Running the ingestion script with a document produces chunks in ChromaDB.                  | 4     | RAG-001          | Test         |

### SRS Generation

| ID     | Category | Statement                                                                            | Priority | Rationale                                   | Acceptance Criteria                                                                                   | Phase | Dependencies   | Verification |
| ------ | -------- | ------------------------------------------------------------------------------------ | -------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----- | -------------- | ------------ |
| FR-040 | FR       | The system shall generate structured functional requirements using the main LLM.     | Must     | Core SRS section.                           | Generated SRS JSON contains a functional_requirements array with ≥ 1 requirement.                     | 3     | FR-010, AI-001 | Test         |
| FR-041 | FR       | The system shall generate structured non-functional requirements.                    | Must     | Core SRS section.                           | Generated SRS JSON contains a non_functional_requirements array.                                      | 3     | FR-040         | Test         |
| FR-042 | FR       | The system shall generate cybersecurity-specific requirements.                       | Must     | Core differentiator of CyberSRS.            | Generated SRS JSON contains a security_requirements array.                                            | 3     | FR-040         | Test         |
| FR-043 | FR       | The system shall generate a high-level system architecture description.              | Must     | Provides structural context.                | Generated SRS JSON contains a system_architecture object.                                             | 3     | FR-040         | Test         |
| FR-044 | FR       | The system shall generate a threat model identifying threats and mitigations.        | Must     | Critical for cybersecurity projects.        | Generated SRS JSON contains a threat_model object with ≥ 1 threat, each having ≥ 1 mitigation.        | 5     | FR-040         | Test         |
| FR-045 | FR       | The system shall generate acceptance criteria and testing recommendations.           | Must     | Ensures requirements are verifiable.        | Generated SRS JSON contains acceptance_criteria and testing_recommendations arrays.                   | 3     | FR-040         | Test         |
| FR-046 | FR       | The system shall produce all SRS sections as validated JSON before any rendering.    | Must     | Structured-JSON-first principle (ADR-0003). | All SRS sections pass Pydantic validation before being returned to the UI.                            | 3     | AI-004         | Test         |
| FR-047 | FR       | The system shall assign a unique requirement ID to each generated requirement.       | Must     | Traceability.                               | Every requirement in the SRS has a unique ID following the naming convention (e.g., FR-001, SEC-001). | 3     | FR-040         | Test         |
| FR-048 | FR       | The system shall record which retrieved chunks were used for each generated section. | Must     | Citation traceability.                      | Each SRS section includes a sources array listing chunk references.                                   | 4     | FR-030, FR-040 | Test         |

### Requirement Validation

| ID     | Category | Statement                                                             | Priority | Rationale                                       | Acceptance Criteria                                                 | Phase | Dependencies | Verification  |
| ------ | -------- | --------------------------------------------------------------------- | -------- | ----------------------------------------------- | ------------------------------------------------------------------- | ----- | ------------ | ------------- |
| FR-050 | FR       | The system shall validate generated requirements for completeness.    | Must     | Ensures all mandatory SRS sections are present. | Validation report flags any missing mandatory section.              | 5     | FR-040       | Test          |
| FR-051 | FR       | The system shall validate generated requirements for testability.     | Must     | Untestable requirements are low quality.        | Validation report flags requirements that lack measurable criteria. | 5     | FR-040       | Test          |
| FR-052 | FR       | The system shall validate generated requirements for consistency.     | Should   | Contradictory requirements reduce quality.      | Validation report flags detected contradictions.                    | 5     | FR-040       | Test          |
| FR-053 | FR       | The system shall flag validation issues and present them to the user. | Must     | User must see quality problems.                 | Validation issues appear inline in the SRS view.                    | 5     | FR-050       | Demonstration |
| FR-054 | FR       | The system shall assign a quality score to each generated SRS.        | Should   | Provides a summary quality indicator.           | A numeric score (0–100) is displayed in the UI.                     | 5     | FR-050       | Test          |

### Review and Editing

| ID     | Category | Statement                                                                                             | Priority | Rationale                                       | Acceptance Criteria                                                              | Phase | Dependencies   | Verification  |
| ------ | -------- | ----------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------- | -------------------------------------------------------------------------------- | ----- | -------------- | ------------- |
| FR-060 | FR       | The system shall display the generated SRS in a structured, section-by-section view.                  | Must     | Core UI requirement.                            | All SRS sections are visible and navigable in the UI.                            | 3     | FR-040         | Demonstration |
| FR-061 | FR       | The system shall allow the user to edit any requirement or section.                                   | Must     | User agency over the output.                    | Edited text is saved to the database and reflected in the UI.                    | 6     | FR-060         | Test          |
| FR-062 | FR       | The system shall allow the user to regenerate a selected section without regenerating the entire SRS. | Must     | Efficiency — avoid re-generating good sections. | Only the selected section is re-generated; other sections remain unchanged.      | 6     | FR-060, FR-040 | Test          |
| FR-063 | FR       | The system shall preserve user edits in sections that are not regenerated.                            | Must     | Prevents data loss.                             | After partial regeneration, unmodified sections retain user edits.               | 6     | FR-062         | Test          |
| FR-064 | FR       | The system shall maintain version history of SRS generations.                                         | Should   | Enables comparison and rollback.                | Each generation creates a new SRSVersion record; previous versions are retained. | 6     | FR-040         | Test          |
| FR-065 | FR       | The system shall display source references for requirements derived from retrieved knowledge.         | Must     | Transparency and trust.                         | Requirements with RAG sources show clickable source references.                  | 4     | FR-048         | Demonstration |

### PDF Export

| ID     | Category | Statement                                                                                                 | Priority | Rationale                               | Acceptance Criteria                                                                     | Phase | Dependencies   | Verification |
| ------ | -------- | --------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------- | --------------------------------------------------------------------------------------- | ----- | -------------- | ------------ |
| FR-070 | FR       | The system shall export the approved SRS as a PDF document.                                               | Must     | Primary output deliverable.             | A PDF file is generated and downloadable.                                               | 6     | FR-060         | Test         |
| FR-071 | FR       | The system shall use a professional template for the PDF.                                                 | Must     | Document quality expectation.           | PDF includes title page, table of contents, formatted sections, and consistent styling. | 6     | FR-070         | Inspection   |
| FR-072 | FR       | The system shall include a table of contents, requirement traceability matrix, and references in the PDF. | Should   | Professional document standards.        | PDF contains these sections.                                                            | 6     | FR-070         | Inspection   |
| FR-073 | FR       | The system shall generate the PDF from the validated JSON structure, not from raw LLM text.               | Must     | Ensures data integrity and consistency. | PDF generation reads from the SRSVersion JSON, not from LLM responses.                  | 6     | FR-046, FR-070 | Inspection   |

---

## Non-Functional Requirements (NFR)

| ID      | Category | Statement                                                                                                                         | Priority | Rationale                                   | Acceptance Criteria                                                                      | Phase | Dependencies   | Verification  |
| ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------- | ---------------------------------------------------------------------------------------- | ----- | -------------- | ------------- |
| NFR-001 | NFR      | The system shall return the description-analysis result within 30 seconds on consumer hardware with the main LLM running locally. | Should   | Responsiveness.                             | Measured latency ≤ 30 s on reference hardware.                                           | 2     | AI-001         | Test          |
| NFR-002 | NFR      | The system shall generate a complete SRS within 5 minutes on consumer hardware.                                                   | Should   | Usability — users should not wait too long. | Measured latency ≤ 300 s.                                                                | 3     | AI-001         | Test          |
| NFR-003 | NFR      | The system shall return RAG retrieval results within 5 seconds.                                                                   | Should   | RAG should not bottleneck generation.       | Measured latency ≤ 5 s.                                                                  | 4     | RAG-004        | Test          |
| NFR-004 | NFR      | The API shall respond to non-LLM requests within 500 ms.                                                                          | Should   | Standard API responsiveness.                | Measured latency ≤ 500 ms for CRUD operations.                                           | 1     | —              | Test          |
| NFR-010 | NFR      | The system shall provide clear progress indicators during LLM generation.                                                         | Must     | Users must know the system is working.      | Progress bar or spinner visible during all LLM calls.                                    | 3     | —              | Demonstration |
| NFR-011 | NFR      | The system shall display validation issues inline next to the relevant requirement.                                               | Should   | Usability.                                  | Validation warnings appear next to flagged requirements.                                 | 5     | FR-053         | Demonstration |
| NFR-012 | NFR      | The system shall be usable without reading a manual.                                                                              | Should   | Low barrier to entry.                       | A new user can create a project and generate an SRS without external instructions.       | 6     | —              | Demonstration |
| NFR-020 | NFR      | The system shall handle LLM failures gracefully by retrying up to a configurable limit and surfacing errors to the user.          | Must     | Reliability.                                | After max retries, user sees a clear error message; no crash.                            | 2     | AI-005         | Test          |
| NFR-021 | NFR      | The system shall handle RAG retrieval failures by generating requirements without retrieved context and warning the user.         | Must     | Degraded-mode operation.                    | SRS is generated with a warning banner; no crash.                                        | 4     | RAG-007        | Test          |
| NFR-022 | NFR      | The system shall handle invalid JSON from the LLM by retrying with a corrective prompt.                                           | Must     | Reliability.                                | After invalid JSON, system retries; if still invalid after max retries, user sees error. | 2     | AI-004, AI-005 | Test          |
| NFR-023 | NFR      | The system shall persist all project data to SQLite; no data shall be lost on application restart.                                | Must     | Data durability.                            | After restart, all projects and SRS versions are intact.                                 | 1     | DATA-001       | Test          |
| NFR-030 | NFR      | The codebase shall be structured as a modular monolith with clear service boundaries.                                             | Must     | Maintainability.                            | Code review confirms separate service modules.                                           | 1     | —              | Inspection    |
| NFR-031 | NFR      | All Python code shall have type hints and docstrings.                                                                             | Must     | Code quality.                               | Linting (mypy, ruff) passes.                                                             | 1     | —              | Inspection    |
| NFR-032 | NFR      | The LLM provider shall be abstracted behind an interface to allow future provider changes.                                        | Must     | Extensibility.                              | An LLMProvider abstract base class exists; Ollama is one implementation.                 | 2     | —              | Inspection    |

---

## Security Requirements (SEC)

| ID      | Category | Statement                                                                                                                         | Priority | Rationale                    | Acceptance Criteria                                                        | Phase | Dependencies | Verification |
| ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------- | -------------------------------------------------------------------------- | ----- | ------------ | ------------ |
| SEC-001 | SEC      | The system shall not perform active penetration testing, exploit execution, malware execution, or automatic network modification. | Must     | Safety.                      | Code review and testing confirm no such functionality exists.              | All   | —            | Inspection   |
| SEC-002 | SEC      | The system shall not transmit any user data to external services.                                                                 | Must     | Privacy; local-first.        | Network audit confirms no outbound connections except to localhost Ollama. | 1     | —            | Test         |
| SEC-003 | SEC      | The system shall not store credentials or secrets in source code or logs.                                                         | Must     | Security best practice.      | grep for secrets in codebase and logs returns no results.                  | 1     | —            | Inspection   |
| SEC-004 | SEC      | The system shall not generate executable attack code in SRS output.                                                               | Must     | Safety.                      | Output validation confirms no code blocks containing exploit patterns.     | 3     | AI-004       | Test         |
| SEC-005 | SEC      | The system shall sanitise user input before passing it to the LLM.                                                                | Must     | Prompt-injection mitigation. | Input sanitisation function is called before every LLM prompt.             | 2     | —            | Test         |
| SEC-006 | SEC      | The system shall not log full project descriptions at DEBUG level in production.                                                  | Should   | Privacy.                     | Log review at DEBUG level does not contain full descriptions.              | 1     | —            | Inspection   |
| SEC-007 | SEC      | The system shall not include the SQLite database in version control.                                                              | Must     | Data protection.             | .gitignore includes _.db and _.sqlite.                                     | 1     | —            | Inspection   |

> **SEC-008 through SEC-050** (43 additional security requirements: application hardening, file-upload safety, prompt-injection resistance, retrieval poisoning, output validation, access-control assumptions, secret handling, logging rules, dependency security, model/adapter integrity, knowledge-source integrity, citation traceability, DoS controls, resource limits, path traversal, safe PDF generation, error sanitisation, data deletion, backup, and security testing) are maintained in [`SECURITY_REQUIREMENTS.md`](SECURITY_REQUIREMENTS.md). They are part of the master security requirement set and use the same unique-ID convention. The master total below includes these 43 requirements.

---

## Data Requirements (DATA)

| ID       | Category | Statement                                                                        | Priority | Rationale              | Acceptance Criteria                                              | Phase | Dependencies | Verification |
| -------- | -------- | -------------------------------------------------------------------------------- | -------- | ---------------------- | ---------------------------------------------------------------- | ----- | ------------ | ------------ |
| DATA-001 | DATA     | The system shall store projects, SRS versions, and clarification data in SQLite. | Must     | Persistence.           | Data survives application restart.                               | 1     | —            | Test         |
| DATA-002 | DATA     | The system shall store vector embeddings in ChromaDB.                            | Must     | RAG infrastructure.    | Ingested documents are queryable in ChromaDB.                    | 4     | RAG-001      | Test         |
| DATA-003 | DATA     | The system shall preserve source-document metadata through the entire pipeline.  | Must     | Citation traceability. | Metadata present at ingestion is available in the generated SRS. | 4     | RAG-005      | Test         |
| DATA-004 | DATA     | The system shall support exporting project data as JSON for backup.              | Should   | Data portability.      | Export endpoint returns valid JSON containing all project data.  | 6     | —            | Test         |
| DATA-005 | DATA     | The system shall use UTC timestamps for all stored records.                      | Must     | Consistency.           | All datetime fields in the database are in UTC.                  | 1     | —            | Inspection   |

---

## AI and Model Requirements (AI)

| ID     | Category | Statement                                                                                                             | Priority | Rationale                             | Acceptance Criteria                                                                                            | Phase | Dependencies | Verification |
| ------ | -------- | --------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ----- | ------------ | ------------ |
| AI-001 | AI       | The system shall use Qwen/Qwen3-4B-Instruct-2507 as the main LLM.                                                     | Must     | Approved decision (ADR-0001).         | Model configuration references this specific model.                                                            | 2     | —            | Inspection   |
| AI-002 | AI       | The system shall support loading a QLoRA fine-tuned adapter alongside the base model.                                 | Must     | Fine-tuning is a project goal.        | Application can switch between base and adapter-enhanced inference.                                            | 8     | AI-001       | Test         |
| AI-003 | AI       | The system shall include structured system prompts for each generation task.                                          | Must     | Prompt quality drives output quality. | Separate prompt templates exist for analysis, clarification, SRS generation, validation, and threat modelling. | 2     | AI-001       | Inspection   |
| AI-004 | AI       | The system shall validate all LLM output against predefined JSON schemas.                                             | Must     | Structured-JSON-first principle.      | Every LLM response is validated against its Pydantic model.                                                    | 2     | —            | Test         |
| AI-005 | AI       | The system shall retry LLM calls with a corrective prompt when output fails validation, up to a configurable maximum. | Must     | Reliability.                          | After invalid output, system retries with error context appended.                                              | 2     | AI-004       | Test         |
| AI-006 | AI       | The system shall log generation metadata (model version, adapter version, prompt template version, generation time).  | Should   | Auditability and evaluation.          | GenerationRun records include all metadata fields.                                                             | 3     | AI-001       | Inspection   |
| AI-007 | AI       | The system shall support comparative evaluation between base-model and fine-tuned-model outputs.                      | Must     | Academic evaluation requirement.      | Evaluation script produces comparison metrics.                                                                 | 9     | AI-002       | Test         |
| AI-008 | AI       | The system shall persist a model run for each model-backed artifact-generation operation.                             | Must     | Experiment traceability.               | New analysis, clarification, and SRS artifacts reference a completed model run; failed attempts remain recorded. | Provenance | AI-001 | Test |
| AI-009 | AI       | The system shall expose an allow-listed read-only API for active model information and SRS provenance.                | Should   | Debugging and academic demonstration.  | API identifies model variant/name and artifact run without exposing secrets, prompts, or filesystem paths.       | Provenance | AI-008 | Test |

---

## RAG Requirements (RAG)

| ID      | Category | Statement                                                                                                           | Priority | Rationale                                   | Acceptance Criteria                                                 | Phase | Dependencies | Verification  |
| ------- | -------- | ------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------- | ------------------------------------------------------------------- | ----- | ------------ | ------------- |
| RAG-001 | RAG      | The system shall provide a pipeline to ingest cybersecurity documents (PDF, Markdown, plain text) into ChromaDB.    | Must     | Knowledge base must be populated.           | Ingestion script processes documents and stores chunks in ChromaDB. | 4     | DATA-002     | Test          |
| RAG-002 | RAG      | The system shall chunk documents with configurable chunk size and overlap.                                          | Must     | Chunking quality affects retrieval quality. | Configuration allows setting chunk_size and chunk_overlap.          | 4     | RAG-001      | Test          |
| RAG-003 | RAG      | The system shall embed chunks using an embedding model.                                                             | Must     | Required for vector search.                 | Chunks are embedded and stored with vectors in ChromaDB.            | 4     | RAG-001      | Test          |
| RAG-004 | RAG      | The system shall retrieve top-k chunks relevant to the project context.                                             | Must     | Core RAG functionality.                     | Query returns top-k chunks ranked by relevance.                     | 4     | RAG-003      | Test          |
| RAG-005 | RAG      | The system shall preserve source-document metadata (title, author, section, page) in each chunk.                    | Must     | Citation traceability.                      | Retrieved chunks include all metadata fields.                       | 4     | RAG-001      | Inspection    |
| RAG-006 | RAG      | The system shall display source references to the user for transparency.                                            | Must     | Trust and verifiability.                    | UI shows source references next to sourced requirements.            | 4     | FR-065       | Demonstration |
| RAG-007 | RAG      | The system shall function without RAG when the vector database is empty, falling back to base-model knowledge only. | Should   | Graceful degradation.                       | SRS is generated with a warning when ChromaDB is empty.             | 4     | —            | Test          |
| RAG-008 | RAG      | The system shall persist the KB version and retrieved chunk, source-document, and citation IDs for RAG model runs.   | Must     | Reproducible retrieval evidence.            | Provenance API returns identifiers without duplicating vectors or full retrieved documents in SQLite. | Provenance | RAG-005 | Test |

---

## UX Requirements (UX)

| ID     | Category | Statement                                                                                                 | Priority | Rationale         | Acceptance Criteria                                                  | Phase | Dependencies | Verification  |
| ------ | -------- | --------------------------------------------------------------------------------------------------------- | -------- | ----------------- | -------------------------------------------------------------------- | ----- | ------------ | ------------- |
| UX-001 | UX       | The system shall present a single-page workflow that guides the user from project creation to PDF export. | Must     | Simplicity.       | UI flow matches the workflow in USER_WORKFLOW.md.                    | 3     | —            | Demonstration |
| UX-002 | UX       | The system shall not require the user to manually select a cybersecurity domain.                          | Must     | Key UX principle. | No domain-selection dropdown or radio-button group exists in the UI. | 2     | FR-011       | Inspection    |
| UX-003 | UX       | The system shall show a progress indicator during each LLM generation step.                               | Must     | Responsiveness.   | Spinner or progress bar visible during LLM calls.                    | 3     | —            | Demonstration |
| UX-004 | UX       | The system shall allow section-level navigation in the generated SRS.                                     | Must     | Usability.        | Sidebar or tabs allow jumping to any SRS section.                    | 6     | FR-060       | Demonstration |
| UX-005 | UX       | The system shall provide inline editing for any requirement or section.                                   | Must     | User agency.      | Clicking a requirement makes it editable in place.                   | 6     | FR-061       | Demonstration |
| UX-006 | UX       | The system shall clearly indicate which requirements are sourced from retrieved knowledge.                | Should   | Transparency.     | A visual indicator (icon or label) marks sourced requirements.       | 4     | FR-065       | Demonstration |
| UX-007 | UX       | The system shall be usable on a 1366×768 screen.                                                          | Should   | Accessibility.    | UI layout does not break at 1366×768.                                | 6     | —            | Demonstration |
| UX-008 | UX       | The generated-SRS workspace shall show a compact model and RAG provenance indicator.                    | Should   | Demonstration clarity. | Workspace identifies base/fine-tuned model, RAG state, and retrieved source/chunk count without cluttering chat. | Provenance | AI-009 | Demonstration |

---

## Requirement Count Summary

| Category       | Count   | Notes                                      |
| -------------- | ------- | ------------------------------------------ |
| FR             | 33      | Catalogue §2                               |
| NFR            | 15      | Catalogue §3                               |
| SEC            | 7       | Catalogue §4 (SEC-001–SEC-007)             |
| SEC (extended) | 43      | SECURITY_REQUIREMENTS.md (SEC-008–SEC-050) |
| DATA           | 5       | Catalogue §7                               |
| AI             | 9       | Catalogue §5                               |
| RAG            | 8       | Catalogue §6                               |
| UX             | 8       | Catalogue §8                               |
| **Total**      | **128** | 85 + 43 extended security requirements     |
