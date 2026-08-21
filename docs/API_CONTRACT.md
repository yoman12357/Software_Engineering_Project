# API Contract — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

---

## General Conventions

| Convention           | Value                                                                   |
| -------------------- | ----------------------------------------------------------------------- |
| Base path            | `/api/v1`                                                               |
| Content type         | `application/json`                                                      |
| ID format            | UUID v4 strings                                                         |
| Timestamps           | ISO 8601, UTC                                                           |
| Authentication (MVP) | None — single-user, local-only deployment                               |
| Error format         | `{ "error": { "code": "string", "message": "string", "details": {} } }` |

### Standard Error Responses

| Status | Meaning                                                            |
| ------ | ------------------------------------------------------------------ |
| 400    | Bad Request — invalid input, validation error                      |
| 404    | Not Found — resource does not exist                                |
| 422    | Unprocessable Entity — LLM output validation failure after retries |
| 500    | Internal Server Error                                              |
| 503    | Service Unavailable — LLM or ChromaDB unreachable after retries    |

---

## 1. Health Check

### `GET /api/v1/health`

**Purpose:** Check that the backend is running and its dependencies are reachable.

**Request:** No body.

**Response (200):**

```json
{
  "status": "healthy",
  "ollama_reachable": true,
  "chromadb_reachable": true,
  "database_ok": true,
  "model_loaded": "qwen3:4b",
  "adapter_loaded": null,
  "timestamp": "2026-01-01T00:00:00Z"
}
```

**Response (503):**

```json
{
  "status": "degraded",
  "ollama_reachable": false,
  "chromadb_reachable": true,
  "database_ok": true,
  "model_loaded": null,
  "adapter_loaded": null,
  "timestamp": "2026-01-01T00:00:00Z"
}
```

---

## 2. Project Management

### `POST /api/v1/projects`

**Purpose:** Create a new project.

**Request:**

```json
{
  "name": "Campus Firewall Project",
  "description": "I want to build a firewall and network-monitoring system for a college campus."
}
```

**Validation:**

- `name`: required, 1–200 characters.
- `description`: required, ≥ 10 characters.

**Response (201):**

```json
{
  "id": "uuid",
  "name": "Campus Firewall Project",
  "description": "I want to build a firewall and network-monitoring system for a college campus.",
  "status": "draft",
  "inferred_categories": [],
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**

- 400: `name` or `description` fails validation.
- 409: `project_limit_reached` — the configured `CYBERSRS_MAX_PROJECTS` limit has been reached; the user must delete an existing project before creating another.

---

### `GET /api/v1/projects`

**Purpose:** List all projects.

**Request:** No body. Optional query parameters: `?sort_by=created_at&order=desc`.

**Response (200):**

```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "Campus Firewall Project",
      "status": "generated",
      "inferred_categories": ["CAT-02", "CAT-03"],
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

### `GET /api/v1/projects/{project_id}`

**Purpose:** Retrieve a single project with its latest SRS version summary.

**Response (200):**

```json
{
  "id": "uuid",
  "name": "Campus Firewall Project",
  "description": "...",
  "status": "generated",
  "inferred_categories": ["CAT-02", "CAT-03"],
  "latest_srs_version": {
    "id": "uuid",
    "version_number": 2,
    "quality_score": 78,
    "status": "validated",
    "created_at": "2026-01-01T00:00:00Z"
  },
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**

- 404: Project not found.

---

### `PUT /api/v1/projects/{project_id}`

**Purpose:** Update a project's name or description.

**Request:**

```json
{
  "name": "Updated Project Name",
  "description": "Updated description..."
}
```

Both fields are optional. Only provided fields are updated.

**Response (200):** Updated project object (same schema as GET).

**Errors:**

- 400: Validation failure.
- 404: Project not found.

---

### `DELETE /api/v1/projects/{project_id}`

**Purpose:** Delete a project and all associated data (SRS versions, clarifications, exports).

**Response (204):** No body.

**Errors:**

- 404: Project not found.

---

### `POST /api/v1/projects/{id}/documents`

**Purpose:** Upload one local reference file for a project as `multipart/form-data` field `file`. Supported extensions are `.pdf`, `.md`, `.markdown`, `.txt`, and `.csv`. The server enforces configured per-file and per-project limits, generates the stored filename, parses the content locally, and isolates any vector chunks by project ID.

**Response (201):** document metadata including `id`, `project_id`, `original_filename`, `media_type`, `file_size_bytes`, `sha256`, `status`, `chunk_count`, and timestamps. Extracted text and server paths are never returned.

### `GET /api/v1/projects/{id}/documents`

**Purpose:** List uploaded reference-document metadata for a project.

### `DELETE /api/v1/projects/{id}/documents/{document_id}`

**Purpose:** Delete the document record, generated local file, and project-scoped vector chunks.

**Errors:** 404 for a missing project/document; 413 for file/count limits; 415 for an unsupported or mismatched file type; 422 when safe parsing fails.

---

## 3. Description Analysis

### `POST /api/v1/projects/{project_id}/analyse`

**Purpose:** Analyse the project's description using the main LLM (Phase 1B: deterministic mock provider). Infers subdomain, extracts entities, detects missing information, persists a `ProjectContext`, and advances the project state (`draft`/`analysed`/`clarifying` → `analysed` or `clarifying`).

**Request:** No body (uses the stored description).

**Response (200):**

```json
{
  "project_id": "uuid",
  "analysis": {
    "stakeholders": ["Campus IT department", "Students", "Faculty"],
    "assets": ["Campus network", "Firewall hardware", "Monitoring server"],
    "users": ["Network administrators", "Security analysts"],
    "constraints": [
      "Budget limitations",
      "Must integrate with existing infrastructure"
    ],
    "goals": [
      "Monitor network traffic",
      "Block malicious connections",
      "Generate alerts"
    ],
    "inferred_categories": ["CAT-02", "CAT-03"],
    "missing_information": [
      "Number of network nodes",
      "Compliance requirements",
      "Expected traffic volume"
    ],
    "project_summary": "A firewall and network-monitoring system for a college campus network..."
  },
  "has_missing_information": true,
  "provider": "mock",
  "model_name": "cybersrs-mock-1b",
  "generated_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**

- 400: Empty stored description; project state does not allow analysis.
- 404: Project not found.
- 422: LLM produced output that fails schema validation.

---

### `GET /api/v1/projects/{project_id}/context`

**Purpose:** Retrieve the latest stored `ProjectContext` for a project (DATA_MODEL §2.5).

**Request:** No body.

**Response (200):**

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "stakeholders": ["Campus IT department", "Students", "Faculty"],
  "assets": ["Campus network", "Firewall hardware", "Monitoring server"],
  "users": ["Network administrators", "Security analysts"],
  "constraints": [
    "Budget limitations",
    "Must integrate with existing infrastructure"
  ],
  "goals": [
    "Monitor network traffic",
    "Block malicious connections",
    "Generate alerts"
  ],
  "inferred_categories": ["CAT-02", "CAT-03"],
  "missing_information": ["Number of network nodes"],
  "enriched_context": null,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**

- 404: Project not found, or the project has not been analysed yet.

---

## 4. Clarification Questions

### `POST /api/v1/projects/{project_id}/clarifications/generate`

**Purpose:** Generate (or regenerate) clarification questions for a project. Questions are generated from the missing information detected during analysis, persisted with stable IDs, and returned (USER_WORKFLOW Step 6).

**Request:** No body.

**Response (200):** Same structure as `GET /clarifications` below.

**Errors:**

- 400: Project state does not allow clarification generation.
- 404: Project not found, or the project has not been analysed yet.
- 422: The provider produced output that fails schema validation.

---

### `GET /api/v1/projects/{project_id}/clarifications`

**Purpose:** Get generated clarification questions for the project.

**Response (200):**

```json
{
  "project_id": "uuid",
  "questions": [
    {
      "id": "q-001",
      "project_id": "uuid",
      "question_text": "How many network nodes will the firewall protect?",
      "reason": "Scale affects architecture and performance requirements.",
      "is_critical": true,
      "display_order": 0,
      "expected_answer_type": "number",
      "target_gap": "Expected number of network nodes",
      "created_at": "2026-01-01T00:00:00Z",
      "answer": null
    },
    {
      "id": "q-002",
      "project_id": "uuid",
      "question_text": "Are there specific compliance standards to meet (e.g., PCI-DSS, HIPAA)?",
      "reason": "Compliance requirements drive security requirements.",
      "is_critical": false,
      "display_order": 1,
      "expected_answer_type": "boolean",
      "target_gap": "Compliance requirements",
      "created_at": "2026-01-01T00:00:00Z",
      "answer": null
    }
  ]
}
```

**Errors:**

- 404: Project not found or no questions generated yet.

---

### `POST /api/v1/projects/{project_id}/clarifications`

**Purpose:** Submit answers to clarification questions.

**Request:**

```json
{
  "answers": [
    {
      "question_id": "q-001",
      "answer_text": "Approximately 500 nodes.",
      "skipped": false
    },
    {
      "question_id": "q-002",
      "answer_text": "",
      "skipped": true
    }
  ]
}
```

**Validation:**

- If `skipped` is false, `answer_text` must not be empty.
- `question_id` must reference an existing question for this project.

**Response (200):**

```json
{
  "project_id": "uuid",
  "answers_saved": 2,
  "context_updated": true
}
```

**Errors:**

- 400: Validation failure (e.g., non-skipped answer with empty text).
- 404: Project or question not found.

---

## 5. SRS Generation

### `POST /api/v1/projects/{project_id}/srs/generate`

**Purpose:** Generate a complete SRS for the project (Phase 1C: deterministic mock provider, no RAG). Validates the output against the SRS schema and saves a new SRS version. History is preserved: each call inserts a new row with an incremented `version_number` (starts at 1).

**Request:** No body.

**Response (200):**

```json
{
  "project_id": "uuid",
  "version_id": "uuid",
  "version_number": 1,
  "status": "generated"
}
```

**Errors:**

- 400: Project state does not allow generation.
- 404: Project not found, or the project has not been analysed yet.
- 422: The provider produced output that fails schema validation.

---

### `GET /api/v1/projects/{project_id}/srs`

**Purpose:** Retrieve the latest SRS version for the project.

**Response (200):**

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "version_number": 1,
  "status": "validated",
  "quality_score": 82,
  "srs": {
    "metadata": { "...": "..." },
    "project_summary": { "...": "..." },
    "functional_requirements": ["..."],
    "non_functional_requirements": ["..."],
    "security_requirements": ["..."],
    "system_architecture": { "...": "..." },
    "threat_model": { "...": "..." },
    "acceptance_criteria": ["..."],
    "testing_recommendations": ["..."],
    "references": ["..."],
    "validation_report": { "...": "..." }
  },
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**

- 404: Project not found or no SRS generated yet.

---

### `GET /api/v1/projects/{project_id}/srs/versions/{version_id}`

**Purpose:** Retrieve a specific SRS version for a project (Phase 1C).

**Response (200):** Same structure as `GET /projects/{id}/srs` above.

**Errors:**

- 404: Project not found, or SRS version not found for this project.

---

### `PUT /api/v1/projects/{project_id}/srs/versions/{version_id}`

**Purpose:** Apply validated user edits to a specific SRS version (Phase 1C). After the edits are applied, the SRS is re-validated against the full schema.

**Request:**

```json
{
  "updates": [
    {
      "section": "functional_requirements",
      "requirement_id": "FR-003",
      "field": "statement",
      "new_value": "The system shall support up to 1000 concurrent connections."
    }
  ]
}
```

**Response (200):** Updated SRS object (status is reset to `draft` after editing).

**Errors:**

- 400: Invalid section, requirement ID, field, or schema-invalid edit (e.g., duplicate IDs).
- 404: Project or SRS version not found.

---

### `POST /api/v1/projects/{project_id}/srs/versions/{version_id}/validate`

**Purpose:** Run deterministic validation on a specific SRS version (Phase 1C): duplicate IDs, missing IDs, empty statements, missing acceptance criteria, invalid priorities, malformed sections.

**Request:** No body.

**Response (200):**

```json
{
  "srs_version_id": "uuid",
  "overall_score": 82,
  "issues": [
    {
      "issue_id": "VAL-001",
      "severity": "warning",
      "section": "functional_requirements",
      "requirement_id": "FR-005",
      "message": "Requirement is missing acceptance criteria."
    }
  ]
}
```

**Errors:**

- 404: Project or SRS version not found.

---

### `GET /api/v1/projects/{project_id}/srs/versions`

**Purpose:** List all SRS versions for a project.

**Response (200):**

```json
{
  "project_id": "uuid",
  "versions": [
    {
      "id": "uuid",
      "version_number": 2,
      "quality_score": 85,
      "status": "validated",
      "created_at": "2026-01-01T01:00:00Z"
    },
    {
      "id": "uuid",
      "version_number": 1,
      "quality_score": 72,
      "status": "validated",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

### `PUT /api/v1/projects/{project_id}/srs/{version_id}`

**Purpose:** Update the SRS (user edits to individual requirements or sections).

**Request:**

```json
{
  "updates": [
    {
      "section": "functional_requirements",
      "requirement_id": "FR-003",
      "field": "statement",
      "new_value": "The system shall support up to 1000 concurrent connections."
    }
  ]
}
```

**Response (200):** Updated SRS object.

**Errors:**

- 400: Invalid section, requirement_id, or field.
- 404: Project or SRS version not found.

---

## 6. Requirement Validation

### `POST /api/v1/projects/{project_id}/srs/{version_id}/validate`

**Purpose:** Run validation on the specified SRS version.

**Request:** No body.

**Response (200):**

```json
{
  "srs_version_id": "uuid",
  "overall_score": 82,
  "issues": [
    {
      "issue_id": "VAL-001",
      "severity": "warning",
      "section": "functional_requirements",
      "requirement_id": "FR-005",
      "message": "Requirement lacks measurable acceptance criteria."
    }
  ],
  "summary": {
    "total_requirements": 28,
    "requirements_with_issues": 3,
    "sections_complete": true
  }
}
```

**Errors:**

- 404: SRS version not found.

---

## 7. Section Regeneration

The implemented single-section, version-preserving contract is documented under
`POST /api/v1/projects/{id}/srs/versions/{vid}/regenerate` below. It returns the
validated new `SRSVersionRead` synchronously and never mutates the source version.

---

## 8. Source References

### `GET /api/v1/projects/{project_id}/srs/{version_id}/sources`

**Purpose:** Retrieve source references (retrieved chunks) used for the specified SRS version.

**Response (200):**

```json
{
  "srs_version_id": "uuid",
  "sources": [
    {
      "chunk_id": "uuid",
      "source_document": {
        "id": "uuid",
        "title": "NIST SP 800-41 Rev 1: Guidelines on Firewalls and Firewall Policy",
        "author": "NIST"
      },
      "page_or_section": "Section 3.2",
      "relevance_score": 0.87,
      "content_preview": "Firewalls should be configured to deny all inbound traffic..."
    }
  ],
  "total": 10
}
```

**Errors:**

- 404: SRS version not found.

---

## 9. PDF Export

### `GET /api/v1/projects/{project_id}/srs/versions/{version_id}/export/pdf`

**Purpose:** Deterministically render a validated stored SRS version as a PDF.

**Request:** No body.

**Response (200):** Binary PDF file (`Content-Type: application/pdf`) with a
content-disposition filename.

**Errors:**

- 404: SRS version not found.
- 500: PDF generation failed.

---

## 10. Experiment and Model Provenance

### `GET /api/v1/system/model-info`

**Purpose:** Return a safe, read-only summary of the active model and RAG
configuration for debugging, evaluation, and demonstrations.

**Response (200):**

```json
{
  "active_model_variant": "base",
  "active_model_name": "qwen3:4b-instruct-2507-q4_K_M",
  "provider": "ollama",
  "rag_enabled": true,
  "embedding_model": "nomic-embed-text",
  "knowledge_base_version": "7591b1d38fd349a9"
}
```

The response never includes API keys, credentials, environment-variable
values, prompts, database or Chroma paths, or model-store paths. An unavailable
knowledge-base version is represented as `"unknown"`.

---

### `GET /api/v1/projects/{project_id}/srs/versions/{version_id}/provenance`

**Purpose:** Inspect which model run produced a stored SRS version, including
the RAG identifiers available to that run. Retrieved document contents and
embeddings are not returned.

**Response (200, recorded provenance):**

```json
{
  "artifact_type": "srs",
  "artifact_id": "uuid",
  "provenance_status": "recorded",
  "model_run": {
    "id": "uuid",
    "operation_type": "srs_generation",
    "model_variant": "base",
    "model_name": "qwen3:4b-instruct-2507-q4_K_M",
    "rag_enabled": true,
    "embedding_model": "nomic-embed-text",
    "knowledge_base_version": "7591b1d38fd349a9",
    "retrieved_chunk_ids": ["nist-csf-2.0_chunk_14"],
    "retrieved_document_ids": ["nist-csf-2.0"],
    "citation_ids": ["nist-csf-2.0_chunk_14"],
    "started_at": "2026-08-14T00:00:00Z",
    "completed_at": "2026-08-14T00:01:20Z",
    "latency_seconds": 80.0,
    "status": "succeeded",
    "error_message": null,
    "deterministic_validation_applied": true,
    "deterministic_repair_applied": true
  }
}
```

**Response (200, legacy artifact):**

```json
{
  "artifact_type": "srs",
  "artifact_id": "uuid",
  "provenance_status": "legacy_unknown",
  "model_run": null
}
```

Legacy records remain valid and are never assigned invented model, RAG, or
timing values.

**Errors:**

- 404: Project or SRS version not found.

---

## 12. Conversational Assistant

### `POST /api/v1/chat/completions`

**Purpose:** Answer a conversational cybersecurity question through the configured `LLMProvider` with optional local RAG context. The generated payload and every citation are validated before return. This endpoint does not create projects.

**Request:**

```json
{
  "messages": [
    {"role": "user", "content": "What controls should a zero-trust VPN use?"}
  ],
  "project_id": null
}
```

**Response (200):**

```json
{
  "content": "A zero-trust VPN should combine identity, device, and session controls...",
  "is_project_description": false,
  "model_name": "qwen3:4b-instruct-2507-q4_K_M",
  "rag_enabled": true,
  "citations": [
    {
      "source_id": "chunk-id",
      "source_document_id": "document-id",
      "document_title": "NIST publication",
      "chunk_index": 1,
      "page_or_section": "Access control",
      "relevance_score": 0.82
    }
  ],
  "warnings": []
}
```

RAG failure alone does not fail the request and is reported in `warnings`.

### `POST /api/v1/chat/intent`

**Purpose:** Deterministically classify explicit chat workflow commands such as a project description, SRS generation, or SRS modification.

The request may include `workflow_stage` so deterministic routing can treat a numbered answer set as `clarification` while a project is awaiting answers. The `intent` value may be `general_question`, `project_description`, `srs_project_request`, `srs_generation`, `srs_modification`, or `clarification`. `srs_project_request` means the same message contains both a project-specific description/document and an explicit SRS or requirements-document signal; clients must create the project, analyse it, present clarification review, and wait for answers before generation. A bare command such as `generate SRS` remains `srs_generation` and uses previously retained project context or attached project files. Prefixing a message with `ask:` while clarifying explicitly routes it as a general question.

### Chat-session persistence

Chat state is persisted locally in SQLite through these endpoints. Session payloads contain the workflow stage, optional project/SRS snapshots, and ordered messages. No cloud service is contacted.

- `GET /api/v1/chat/sessions?limit=50` lists sessions with pinned sessions first and then newest activity.
- `PUT /api/v1/chat/sessions/{session_id}` creates or replaces a complete session snapshot.
- `GET /api/v1/chat/sessions/{session_id}` restores one complete session.
- `PATCH /api/v1/chat/sessions/{session_id}` updates `name` and/or `pinned`.
- `DELETE /api/v1/chat/sessions/{session_id}` permanently removes the session and its messages.

Missing sessions return `404 chat_session_not_found`. Session IDs are client-generated local identifiers; timestamps are assigned by the backend.

### `POST /api/v1/projects/{id}/srs/generate/stream`

Streams schema-validated Server-Sent Events for deterministic generation phases. Events contain `phase`, `progress`, and `message`; the terminal `completed` event additionally contains the validated `SRSGenerationResponse`. If generation fails after bounded correction attempts, a terminal `failed` event contains a safe `error_code` and user-facing message so the UI can stop waiting and offer Retry. Raw LLM tokens, validation details, or unvalidated model output are never streamed. Closing the client connection cancels delivery; the UI may retry safely to create a new version.

### `POST /api/v1/projects/{id}/srs/versions/{vid}/regenerate`

Regenerates one supported SRS section and creates a new immutable version. The request contains a `section` selected from the five requirement sections, `architecture_summary`, `threats`, or `testing_strategy`. Non-targeted content is copied from the source version, while metadata and provenance describe the new generation.

---

## 13. Endpoint Summary

| Method | Path                                                | Purpose                          | Phase |
| ------ | --------------------------------------------------- | -------------------------------- | ----- |
| GET    | `/api/v1/health`                                    | Health check                     | 1     |
| POST   | `/api/v1/projects`                                  | Create project                   | 1     |
| GET    | `/api/v1/projects`                                  | List projects                    | 1     |
| GET    | `/api/v1/projects/{id}`                             | Get project                      | 1     |
| PUT    | `/api/v1/projects/{id}`                             | Update project                   | 1     |
| DELETE | `/api/v1/projects/{id}`                             | Delete project                   | 1     |
| POST   | `/api/v1/projects/{id}/documents`                   | Upload project reference file    | SRS   |
| GET    | `/api/v1/projects/{id}/documents`                   | List project reference files     | SRS   |
| DELETE | `/api/v1/projects/{id}/documents/{document_id}`     | Delete project reference file    | SRS   |
| POST   | `/api/v1/projects/{id}/analyse`                     | Analyse description              | 1B    |
| GET    | `/api/v1/projects/{id}/context`                     | Get stored project context       | 1B    |
| POST   | `/api/v1/projects/{id}/clarifications/generate`     | Generate clarification questions | 1B    |
| GET    | `/api/v1/projects/{id}/clarifications`              | Get clarification questions      | 1B    |
| POST   | `/api/v1/projects/{id}/clarifications`              | Submit clarification answers     | 1B    |
| POST   | `/api/v1/projects/{id}/srs/generate`                | Generate SRS                     | 1C    |
| GET    | `/api/v1/projects/{id}/srs`                         | Get latest SRS                   | 1C    |
| GET    | `/api/v1/projects/{id}/srs/versions`                | List SRS versions                | 1C    |
| GET    | `/api/v1/projects/{id}/srs/versions/{vid}`          | Get specific SRS version         | 1C    |
| PUT    | `/api/v1/projects/{id}/srs/versions/{vid}`          | Update SRS (validated edit)      | 1C    |
| POST   | `/api/v1/projects/{id}/srs/versions/{vid}/validate` | Validate SRS (deterministic)     | 1C    |
| GET    | `/api/v1/projects/{id}/srs/versions/{vid}/sources`  | Get source references            | 4     |
| GET    | `/api/v1/projects/{id}/srs/versions/{vid}/export/pdf` | Export PDF                     | 6     |
| GET    | `/api/v1/system/model-info`                          | Safe active model/RAG information | Provenance |
| GET    | `/api/v1/projects/{id}/srs/versions/{vid}/provenance` | Inspect SRS model-run provenance | Provenance |
| POST   | `/api/v1/chat/completions`                           | Validated RAG-grounded chat answer | Chat |
| POST   | `/api/v1/chat/intent`                                | Classify chat workflow intent | Chat |
| GET    | `/api/v1/chat/sessions`                              | List persisted chat sessions | Chat |
| PUT    | `/api/v1/chat/sessions/{id}`                         | Create or replace a chat session | Chat |
| GET    | `/api/v1/chat/sessions/{id}`                         | Restore a chat session | Chat |
| PATCH  | `/api/v1/chat/sessions/{id}`                         | Rename or pin a chat session | Chat |
| DELETE | `/api/v1/chat/sessions/{id}`                         | Permanently delete a chat session | Chat |
| POST   | `/api/v1/projects/{id}/srs/generate/stream`           | Stream validated SRS generation progress | SRS |
| POST   | `/api/v1/projects/{id}/srs/versions/{vid}/regenerate` | Regenerate one section into a new version | SRS |
