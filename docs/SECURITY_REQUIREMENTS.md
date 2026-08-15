# Security Requirements — CyberSRS Application

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

> These requirements define how CyberSRS itself must be secured. They complement SEC-001 through SEC-007 in REQUIREMENTS_CATALOG.md and extend the numbering from SEC-008 onward. Every requirement uses testable "The system shall…" language.

---

## 1. Local-First Operation

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-008 | The system shall not open any listening port accessible from external hosts; all services shall bind to `127.0.0.1` or `localhost`. | Prevents remote exploitation of a development tool. | Must | Network scan from another device shows no reachable ports. | Test | THR-011 | 1 |
| SEC-009 | The system shall not depend on any external network service at runtime, except the locally hosted Ollama instance on `localhost`. | Local-first constraint; no data leakage. | Must | Disconnecting the network adapter after setup does not cause errors. | Test | THR-011 | 1 |

## 2. Input Validation

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-010 | The system shall validate all user-supplied strings (project name, description, clarification answers) against maximum length limits before processing. | Prevents memory exhaustion and buffer-overflow-class bugs. | Must | Strings exceeding limits are rejected with HTTP 400. | Test | THR-009 | 1 |
| SEC-011 | The system shall reject any API request whose body size exceeds a configurable maximum (`CYBERSRS_MAX_REQUEST_BODY_BYTES`, default 1 MB). | Prevents request-flooding DoS. | Must | Requests larger than the limit return HTTP 413. | Test | THR-009 | 1 |
| SEC-012 | The system shall strip or escape HTML, JavaScript, and shell metacharacters from user input before including it in LLM prompts. | Reduces prompt-injection attack surface. | Must | Injected `<script>` tags and shell commands are neutralised in prompts. | Test | THR-001 | 2 |

## 3. File-Upload Safety

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-013 | The system shall accept only PDF, Markdown, and plain-text files for knowledge-base ingestion. | Limits attack surface from malicious file types. | Must | Uploading `.exe`, `.zip`, or `.html` is rejected. | Test | THR-003 | 4 |
| SEC-014 | The system shall validate uploaded file MIME types using content inspection, not only the file extension. | Prevents extension-spoofing attacks. | Must | A renamed `.exe` with a `.pdf` extension is rejected. | Test | THR-003 | 4 |
| SEC-015 | The system shall limit individual uploaded file size to a configurable maximum (`CYBERSRS_MAX_UPLOAD_BYTES`, default 20 MB). | Prevents disk exhaustion. | Must | Files exceeding the limit are rejected with HTTP 413. | Test | THR-009 | 4 |

## 4. PDF and Document Parsing Safety

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-016 | The system shall parse PDF files using a sandboxed or memory-safe library and shall not execute embedded JavaScript, forms, or actions within PDFs. | Malicious PDFs can exploit parser vulnerabilities. | Must | A PDF with embedded JavaScript does not trigger execution. | Test | THR-003 | 4 |
| SEC-017 | The system shall strip or ignore embedded HTML, scripts, and active content when parsing Markdown documents for ingestion. | Prevents stored XSS and script injection via knowledge documents. | Must | Markdown containing `<script>` tags is sanitised. | Test | THR-003 | 4 |

## 5. Prompt-Injection Resistance

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-018 | The system shall separate user-supplied content from system instructions in every LLM prompt using clear delimiters and role-based prompt structure. | Makes prompt-injection harder. | Must | System prompt and user content occupy distinct message roles. | Inspection | THR-001 | 2 |
| SEC-019 | The system shall not include raw retrieved-chunk content in the system-role portion of any LLM prompt. | Retrieved content may contain adversarial text. | Must | All retrieved chunks are placed in a clearly delimited context section within the user or assistant role. | Inspection | THR-004 | 4 |
| SEC-020 | The system shall validate LLM output against the expected JSON schema regardless of the prompt content that produced it. | Schema validation is the last line of defence against prompt-injection-influenced output. | Must | Injected instructions in a description cannot cause the system to skip schema validation. | Test | THR-001 | 2 |

## 6. Retrieval Poisoning Risks

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-021 | The system shall record the SHA-256 hash of every ingested source document and store it alongside the source-document metadata. | Enables integrity verification and tamper detection. | Must | Re-ingesting a modified file produces a different hash; a warning is issued. | Test | THR-004 | 4 |
| SEC-022 | The system shall allow the operator to review and approve source documents before ingestion into the knowledge base. | Prevents accidental ingestion of untrusted content. | Should | Ingestion CLI requires a `--confirm` flag or interactive prompt. | Demonstration | THR-004 | 4 |

## 7. Unsafe Retrieved Content

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-023 | The system shall not render raw retrieved-chunk content directly in the frontend without sanitisation. | Retrieved chunks could contain HTML injection payloads. | Must | Chunks displayed in the UI are HTML-escaped. | Test | THR-005 | 4 |

## 8. Output Validation

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-024 | The system shall validate every LLM-generated JSON response against its Pydantic schema before storing, displaying, or exporting it. | Prevents corrupt or malicious data from entering the pipeline. | Must | Invalid JSON is never written to SQLite or displayed in the UI. | Test | THR-006 | 2 |
| SEC-025 | The system shall scan generated security requirements for patterns resembling executable exploit code and flag them for review. | Prevents CyberSRS from producing weaponisable output. | Should | A regex/pattern check runs on all generated `security_requirements`; flagged items are marked in the validation report. | Test | THR-006 | 5 |

## 9. JSON-Schema Validation

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-026 | The system shall reject any LLM output that contains JSON keys not defined in the expected schema (strict mode). | Prevents unexpected data injection via extra fields. | Should | Pydantic model with `model_config = ConfigDict(extra='forbid')` rejects extra keys. | Test | THR-006 | 2 |

## 10. Access-Control Assumptions

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-027 | The system shall document that the MVP assumes a single trusted local user and does not implement authentication or authorisation. | Explicit threat-model assumption. | Must | README and API_CONTRACT state this assumption. No auth middleware is implemented in MVP. | Inspection | THR-011 | 1 |
| SEC-028 | The system shall not expose admin-level or destructive API endpoints (e.g., database wipe, knowledge-base purge) without a confirmation mechanism. | Even a single local user can make accidental destructive calls. | Should | DELETE endpoints require a `?confirm=true` query parameter. | Test | THR-011 | 1 |

## 11. Secret Handling

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-029 | The system shall read all configuration secrets and sensitive paths from environment variables or a `.env` file, never from hard-coded values. | Prevents accidental secret exposure in source code. | Must | grep for hard-coded URLs, ports, or paths in source returns zero results. | Inspection | THR-015 | 1 |
| SEC-030 | The `.env` file shall be listed in `.gitignore` and never committed to version control. | Standard secret-hygiene practice. | Must | `.gitignore` contains `.env`. | Inspection | THR-015 | 1 |

## 12. Logging and Sensitive-Data Exposure

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-031 | The system shall not log the full text of user project descriptions, clarification answers, or generated SRS content at any log level in production configuration. | Prevents sensitive project data leakage via logs. | Must | Log output at INFO and WARNING levels contains no user text. | Inspection | THR-015 | 1 |
| SEC-032 | The system shall redact or truncate user-supplied content in log messages to a configurable maximum of 50 characters with a `[REDACTED]` marker. | Provides debugging context without exposing full content. | Should | Log messages show truncated user content. | Test | THR-015 | 2 |

## 13. Dependency Security

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-033 | The system shall pin all Python and Node.js dependency versions in lock files (`requirements.txt` or `poetry.lock`, `package-lock.json`). | Prevents supply-chain attacks via unpinned dependencies. | Must | Lock files exist and are committed. | Inspection | THR-012 | 1 |
| SEC-034 | The system shall periodically audit dependencies for known vulnerabilities using `pip-audit` or `npm audit`. | Catches known CVEs in dependencies. | Should | Audit commands run without critical findings before each phase transition. | Test | THR-012 | 1 |

## 14. Model-File and Adapter Integrity

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-035 | The system shall verify that the Ollama model identifier matches the expected value (`CYBERSRS_MODEL_NAME`) before making inference calls. | Prevents accidental use of a wrong or tampered model. | Must | Model name returned by Ollama `/api/tags` matches configuration. | Test | THR-013 | 2 |
| SEC-036 | The system shall record the SHA-256 hash of each QLoRA adapter file at training time and verify it at loading time. | Detects adapter tampering. | Should | Loading an adapter with a mismatched hash raises an error. | Test | THR-013 | 8 |

## 15. Knowledge-Source Integrity

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-037 | The system shall maintain a source manifest listing every ingested document with its SHA-256 hash, source URL, and ingestion timestamp. | Enables knowledge-base auditing. | Must | Source manifest file or database table exists and is populated. | Inspection | THR-004 | 4 |

## 16. Citation Traceability

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-038 | The system shall not display a source citation in the UI or PDF unless the cited chunk ID exists in the vector store. | Prevents hallucinated citations. | Must | A citation pointing to a non-existent chunk is flagged in the validation report. | Test | THR-005 | 4 |

## 17. Denial-of-Service Controls

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-039 | The system shall enforce a configurable timeout on every LLM inference call (`CYBERSRS_LLM_TIMEOUT_SECONDS`, default 120 s). | Prevents runaway inference from hanging the application. | Must | An LLM call exceeding the timeout returns an error. | Test | THR-009 | 2 |
| SEC-040 | The system shall limit the maximum number of concurrent generation runs to a configurable value (`CYBERSRS_MAX_CONCURRENT_RUNS`, default 1). | Prevents resource exhaustion from parallel requests. | Must | A second generation request while one is running returns HTTP 429. | Test | THR-009 | 3 |

## 18. Resource Limits

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-041 | The system shall limit the total number of projects stored in the database to a configurable maximum (`CYBERSRS_MAX_PROJECTS`, default 100). | Prevents unbounded disk usage. | Should | Creating project 101 returns HTTP 400 with a clear message. | Test | THR-009 | 1 |
| SEC-042 | The system shall limit the total ChromaDB storage size by capping the number of ingested source documents (`CYBERSRS_MAX_KNOWLEDGE_DOCS`, default 200). | Prevents unbounded vector-store growth. | Should | Ingesting document 201 returns an error. | Test | THR-009 | 4 |

## 19. Path Traversal Prevention

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-043 | The system shall resolve all file paths to canonical absolute paths and verify they fall within allowed directories (`CYBERSRS_PDF_OUTPUT_DIR`, `CYBERSRS_DB_PATH` parent, `CYBERSRS_CHROMA_PATH`) before any file read or write. | Prevents path-traversal attacks via crafted filenames. | Must | A path containing `../` that escapes the allowed directory is rejected. | Test | THR-014 | 4 |

## 20. Safe PDF Generation

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-044 | The PDF generator shall only consume validated SRS JSON; it shall never render raw LLM text output. | Ensures content integrity in exported documents. | Must | PDF renderer function signature requires an `SRSVersion` Pydantic model, not raw text. | Inspection | THR-008 | 6 |
| SEC-045 | The PDF generator shall escape any user-supplied text (project name, description, requirement text) to prevent PDF injection. | User text could contain PDF control sequences. | Must | Text with special PDF characters renders correctly without corruption. | Test | THR-008 | 6 |

## 21. Error-Message Sanitisation

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-046 | The system shall not expose internal stack traces, file paths, or database queries in API error responses returned to the frontend. | Prevents information leakage. | Must | Error responses contain only `code` and `message`; no tracebacks. | Test | THR-015 | 1 |

## 22. Data Deletion

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-047 | The system shall delete all associated data (SRS versions, clarifications, generation runs, exported PDFs) when a project is deleted. | Prevents orphaned sensitive data. | Must | After project deletion, no related records exist in SQLite and no orphaned PDFs remain. | Test | — | 1 |
| SEC-048 | The system shall provide a mechanism to purge the entire knowledge base (ChromaDB collection and source-document records). | Allows operator to reset the system. | Should | Purge command removes all chunks and metadata. | Test | — | 4 |

## 23. Backup Considerations

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-049 | The system shall document a recommended backup procedure for the SQLite database and ChromaDB persistence directory. | Data recovery guidance. | Should | README or operations guide includes backup instructions. | Inspection | — | 10 |

## 24. Security Testing

| ID | Statement | Rationale | Priority | Acceptance Criteria | Verification | Related Threat | Phase |
|---|---|---|---|---|---|---|---|
| SEC-050 | The system shall include automated security tests covering prompt injection, path traversal, file-upload bypass, and oversized request handling. | Ensures security controls are regression-tested. | Must | Security test suite runs in CI and passes. | Test | — | 5 |

---

## Requirement Summary

| Range | Count | Topic |
|---|---|---|
| SEC-008 – SEC-009 | 2 | Local-first operation |
| SEC-010 – SEC-012 | 3 | Input validation |
| SEC-013 – SEC-015 | 3 | File-upload safety |
| SEC-016 – SEC-017 | 2 | Document parsing safety |
| SEC-018 – SEC-020 | 3 | Prompt-injection resistance |
| SEC-021 – SEC-022 | 2 | Retrieval poisoning |
| SEC-023 | 1 | Unsafe retrieved content |
| SEC-024 – SEC-025 | 2 | Output validation |
| SEC-026 | 1 | JSON-schema strictness |
| SEC-027 – SEC-028 | 2 | Access control |
| SEC-029 – SEC-030 | 2 | Secret handling |
| SEC-031 – SEC-032 | 2 | Logging safety |
| SEC-033 – SEC-034 | 2 | Dependency security |
| SEC-035 – SEC-036 | 2 | Model/adapter integrity |
| SEC-037 | 1 | Knowledge-source integrity |
| SEC-038 | 1 | Citation traceability |
| SEC-039 – SEC-040 | 2 | DoS controls |
| SEC-041 – SEC-042 | 2 | Resource limits |
| SEC-043 | 1 | Path traversal |
| SEC-044 – SEC-045 | 2 | Safe PDF generation |
| SEC-046 | 1 | Error-message sanitisation |
| SEC-047 – SEC-048 | 2 | Data deletion |
| SEC-049 | 1 | Backup |
| SEC-050 | 1 | Security testing |
| **Total** | **43** | |
