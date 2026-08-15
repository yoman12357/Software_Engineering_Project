# Privacy and Data Handling — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

---

## 1. Data Collected

CyberSRS collects and stores the following categories of data — all locally.

| Category | Examples | Storage | Sensitivity |
|---|---|---|---|
| **Project metadata** | Project name, status, timestamps | SQLite | Low–Medium |
| **Project descriptions** | Informal user-entered text describing cybersecurity projects | SQLite | High — may contain organisational details, network layouts, security gaps |
| **Clarification answers** | User responses to system-generated questions | SQLite | High — elaborates on project-specific details |
| **Project context** | Extracted stakeholders, assets, users, constraints, goals | SQLite (JSON field) | High |
| **Generated SRS content** | Requirements, threat models, architecture descriptions | SQLite (JSON field) | High — reveals security posture of target system |
| **Validation reports** | Quality scores, flagged issues | SQLite (JSON field) | Low |
| **Generation-run metadata** | Model name, adapter name, prompt template version, timing, retry count | SQLite | Low |
| **Evaluation-run data** | Comparison metrics between base and fine-tuned models | SQLite | Low |
| **Retrieved chunks** | Text passages from ingested cybersecurity documents | ChromaDB | Low — public documents |
| **Source-document metadata** | Title, author, URL, hash, ingestion timestamp | SQLite + ChromaDB | Low |
| **Exported PDFs** | Rendered SRS documents | Local file system | High |
| **Application logs** | Structured log entries (redacted) | Stdout / file | Low (if redaction rules enforced) |
| **Configuration** | Environment variables, `.env` file | Local file system | Medium — contains paths and ports |

## 2. Data Intentionally Not Collected

| Data | Reason |
|---|---|
| **User identity** (name, email, account) | MVP is single-user, no authentication; no need to identify the user. |
| **Usage analytics / telemetry** | Local-first principle; no external data transmission. |
| **Browser cookies or tracking data** | Not needed; SPA communicates via API only. |
| **Keystroke or interaction timing data** | Not collected; unnecessary for functionality. |
| **IP addresses** | All traffic is localhost; IP logging serves no purpose. |
| **Hardware fingerprints** | Not relevant to application functionality. |
| **LLM inference logs with full prompts** | Redacted by default (SEC-031). |

## 3. Local Storage

All data is stored locally on the user's machine:

| Store | Path (configurable) | Format |
|---|---|---|
| SQLite database | `CYBERSRS_DB_PATH` (default `./data/cybersrs.db`) | Single file |
| ChromaDB persistence | `CYBERSRS_CHROMA_PATH` (default `./data/chroma/`) | Directory |
| Exported PDFs | `CYBERSRS_PDF_OUTPUT_DIR` (default `./data/exports/`) | PDF files |
| Application logs | Stdout (or configurable file path) | Structured JSON |
| Fine-tuning dataset | `./data/datasets/` (not in version control) | JSONL files |
| QLoRA adapter | `CYBERSRS_ADAPTER_PATH` | Directory with adapter weights |

**No data is transmitted to any external service.** The only network communication is to `localhost` (Ollama).

## 4. Retention

| Data | Retention policy |
|---|---|
| Project data (descriptions, context, SRS, clarifications) | Retained until the user explicitly deletes the project. |
| SRS version history | All versions retained unless the user deletes the project. |
| Exported PDFs | Retained on disk until manually deleted by the user. |
| Knowledge-base chunks | Retained until the operator purges the knowledge base. |
| Source-document metadata | Retained alongside chunks. |
| Generation-run metadata | Retained with the associated SRS version. |
| Application logs | Retained until manually rotated or deleted by the user. No automatic rotation in MVP. |
| Fine-tuning datasets | Retained on disk; not automatically deleted. |

**MVP limitation:** There is no automatic data expiry or scheduled cleanup. The user is responsible for managing disk usage.

## 5. Deletion

| Action | What is deleted | How |
|---|---|---|
| Delete a project (API) | Project record, description, clarifications, all SRS versions, generation runs, exported PDFs for that project | `DELETE /api/v1/projects/{id}` with cascade |
| Purge knowledge base (CLI) | All ChromaDB chunks, source-document records | CLI command with `--confirm` flag |
| Delete exported PDF (manual) | Individual PDF file | User deletes the file from disk |
| Full reset | SQLite database file, ChromaDB directory, exports directory | User deletes the `./data/` directory |

**Guarantee:** After project deletion via the API, no project-related data remains in SQLite. Exported PDFs associated with the project are also removed from disk (SEC-047).

## 6. Logs

| Log level | What is logged | What is NOT logged |
|---|---|---|
| INFO | Request method, path, status code, generation-run lifecycle events | User text content |
| WARNING | Retry attempts, RAG fallback, low quality scores | User text content |
| ERROR | Error codes, component names, failure types | Stack traces in production; user content |
| DEBUG (dev only) | Prompt template names, chunk IDs, model parameters | Full user descriptions; full SRS content; full prompts |

**Redaction rules (SEC-031, SEC-032):**
- User-supplied text is truncated to 50 characters with `[REDACTED]` appended.
- Generated SRS content is never logged.
- Clarification answers are never logged.
- `.env` values are never logged.

## 7. User-Entered Sensitive Information

User project descriptions and clarification answers may contain sensitive information:

- Organisation names and structure
- Network topology details
- Known security vulnerabilities
- Planned security controls
- Compliance requirements
- Personnel information

**Protections:**
1. All data stays on the local machine (no external transmission).
2. Logs do not contain full descriptions (SEC-031).
3. Error messages do not leak user content (SEC-046).
4. Database files are excluded from version control (SEC-007).
5. The user is responsible for physical and OS-level security of their machine.

**MVP limitation:** No encryption-at-rest for SQLite or ChromaDB. This is accepted for a single-user local application. Post-MVP may add optional encryption.

## 8. Knowledge Documents

Ingested cybersecurity documents (NIST, OWASP, CIS, etc.) are:

- Publicly available documents with no personal data.
- Stored as chunks in ChromaDB with full source metadata.
- Hashed for integrity verification (SEC-021).
- Approved by the operator before ingestion (SEC-022).

**No user-generated content is mixed into the knowledge base.** The knowledge base contains only curated cybersecurity reference material.

## 9. Generated SRS Documents

Generated SRS content:
- Is stored as validated JSON in SQLite.
- Contains AI-generated content that may be inaccurate.
- Includes a disclaimer in the exported PDF stating the content is AI-generated.
- Includes source citations so the user can verify claims.
- Is the user's property; no licence is claimed over generated output.

## 10. Fine-Tuning Datasets

| Concern | Handling |
|---|---|
| Source provenance | Each dataset example must document its source (public, synthetic, human-corrected). |
| No user data in training | Fine-tuning datasets must not include real user project descriptions or SRS documents. |
| Anonymisation | If any real-world examples are adapted, all identifying information must be removed. |
| Storage | Datasets are stored locally in `./data/datasets/` and excluded from version control via `.gitignore`. |
| Licence | Datasets must comply with the licence of their source material. |

## 11. Dataset Anonymisation

If any training example is derived from a real-world project:

1. All organisation names must be replaced with generic names (e.g., "Acme Corp").
2. All IP addresses, domain names, and hostnames must be replaced with RFC 5737 / RFC 2606 examples.
3. All personnel names must be replaced with generic roles.
4. All specific compliance references that could identify an organisation must be generalised.
5. A `provenance` field in the dataset must indicate `anonymised_real` vs. `synthetic` vs. `public_reference`.

## 12. Exported Files

Exported PDF documents:
- Are saved to `CYBERSRS_PDF_OUTPUT_DIR`.
- Contain the full SRS including requirements, threat model, and architecture.
- Are the user's responsibility to secure, distribute, or delete.
- Include a generation timestamp and model metadata for traceability.
- Include an AI-generated disclaimer.

## 13. Backup Policy

**MVP recommendation (not automated):**

| Component | Backup method |
|---|---|
| SQLite database | Copy `cybersrs.db` to a secure location. |
| ChromaDB | Copy the `chroma/` directory. |
| Exported PDFs | Already on disk; copy as needed. |
| Fine-tuning adapters | Copy the adapter directory. |
| `.env` file | Maintain a secure copy separately. |

**Future:** Automated backup and restore via a CLI command.

## 14. Privacy Limitations of the MVP

| Limitation | Accepted Risk |
|---|---|
| No encryption at rest | Accepted for single-user local deployment. |
| No authentication | Accepted; single-user assumption (SEC-027). |
| No automatic log rotation | Logs may grow unbounded; user must manage manually. |
| No data expiry | Old projects persist until manually deleted. |
| No secure deletion (disk overwrite) | Standard file deletion; forensic recovery possible. Accepted for MVP. |
| Shared-machine risk | Another user on the same OS account could access all CyberSRS data. |
| LLM may memorise training data | Qwen3-4B's pre-training data is outside our control. Not a CyberSRS-specific risk. |
