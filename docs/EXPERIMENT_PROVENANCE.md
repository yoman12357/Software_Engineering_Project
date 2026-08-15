# Experiment and Model Provenance

**Status:** Implemented for analysis, clarification, and SRS generation  
**Scope:** Lightweight SQLite metadata only; no training-data, Chroma-vector,
RAG-document, adapter, prompt, or model-behaviour changes

## 1. Purpose

CyberSRS records enough evidence to answer a practical academic question:
"Which model and retrieval configuration produced this artifact?" The design
uses one general `model_run` row per model-backed operation and nullable links
from generated artifacts. It deliberately avoids copying prompts, project
descriptions, retrieved document text, embeddings, or model files.

The pre-existing `generation_run` table remains available for its original
SRS/evaluation design. `model_run` is the cross-operation provenance layer and
can represent analysis and clarification attempts before an SRS exists.

## 2. Recorded Run Lifecycle

1. Validate that the project and prerequisite artifact exist.
2. Commit a `model_run` with `status=running` before calling the provider.
3. Execute inference through the existing `LLMProvider` interface.
4. Validate/repair output using the existing deterministic pipeline.
5. Persist the generated artifact with its nullable `model_run_id`.
6. Complete the run as `succeeded` in the same commit as the association.
7. If generation fails, roll back partial artifact writes and update the
   already-committed run to `failed` with a sanitized exception-class message.

This lifecycle makes failures traceable without leaving half-written
artifacts. Model prompts and raw user content are never written to the run.

## 3. Artifact Associations

| Artifact | Association | Operation type |
|---|---|---|
| Project analysis | `project_context.model_run_id` | `project_analysis` |
| Clarification set | `clarification_question.model_run_id` | `clarification_generation` |
| Complete SRS, including embedded threat model and architecture | `srs_version.model_run_id` | `srs_generation` |
| Phase 5 configuration result | `phase5_evaluation_run`; case rows in `phase5_case_result` | Phase 5 evaluation |

One clarification run may produce multiple question rows; each points to the
same run. Threat-model and architecture sections are inside canonical SRS JSON,
so their provenance is the SRS version's run rather than duplicate rows.

## 4. RAG Provenance

For an SRS where RAG was actually used, the run stores:

- embedding model identifier;
- knowledge-base version;
- retrieved Chroma chunk IDs;
- source-document IDs from chunk metadata;
- citation IDs retained in the validated SRS;
- retrieval latency, prompt chunk count, and prompt context character count in
  controlled metadata.

SQLite does **not** store full retrieved text or vectors. Chroma remains the
authoritative vector/document-chunk store. Identifier lists are sufficient to
reconstruct which evidence was available while avoiding data duplication.

If retrieval fails and generation falls back to non-RAG operation,
`rag_enabled` is false. Controlled metadata still records that RAG was
requested, distinguishing fallback from an intentionally non-RAG run.

## 5. What CyberSRS Can Prove

### Which model generated an SRS?

`srs_version.model_run_id` resolves to `model_run.model_variant` and
`model_run.model_name`. The model name is taken from the provider response on
successful SRS generation.

### Was RAG enabled?

`model_run.rag_enabled` records actual use, not only configured intent.
`metadata_json.rag_requested` records the requested mode.

### Which KB version was used?

`model_run.knowledge_base_version` stores the version returned with the
retrieval context. Configuration uses
`CYBERSRS_KNOWLEDGE_BASE_VERSION`; when absent, the local corpus inventory is
read without modifying Chroma. Unavailable legacy values remain `unknown`.

### Which retrieved chunks were available?

`retrieved_chunk_ids` and `retrieved_document_ids` identify the retrieval set.
`citation_ids` identifies the subset retained by validated requirements.

### How long did generation take?

`started_at`, `completed_at`, and `latency_seconds` cover the operation from
the pre-inference run record through persistence and deterministic processing.
The SRS generation metadata continues to retain model-only and retrieval timing
for finer inspection.

### Was deterministic validation or repair applied?

The safe provenance API exposes `deterministic_validation_applied` and
`deterministic_repair_applied`. SRS generation records both as true because it
normalizes model output, repairs only defensible citation-ID near matches, runs
semantic checks, and validates citations before persistence. Analysis and
clarification record schema validation and no deterministic content repair.

## 6. Read-Only APIs

### `GET /api/v1/system/model-info`

Returns only the active model variant/name, provider, RAG state, embedding
model, and KB version. It does not return database URLs, Chroma/model paths,
environment variables, credentials, prompts, or user content.

### `GET /api/v1/projects/{project_id}/srs/versions/{version_id}/provenance`

Returns the allow-listed run fields for one SRS. Arbitrary `metadata_json` is
not exposed. Older versions with no association return:

```json
{
  "artifact_type": "srs",
  "artifact_id": "...",
  "provenance_status": "legacy_unknown",
  "model_run": null
}
```

## 7. Migration and Legacy Safety

At startup, `Base.metadata.create_all()` creates new tables. The canonical,
idempotent SQLite compatibility migration then adds any missing nullable SRS
provenance fields and nullable `model_run_id` artifact links, plus indexes,
without rebuilding tables. Both historical migration scripts delegate to this
startup path rather than maintaining separate SQL definitions.

Fresh databases receive ORM-declared foreign keys with `ON DELETE SET NULL`.
SQLite cannot add a foreign-key constraint to an existing table in place, so
migrated databases receive indexed nullable columns and application-managed
associations. No table is rebuilt and no existing value is rewritten.

Existing records remain `NULL` and are reported as `legacy_unknown`. There is
no speculative backfill from old SRS metadata because that could incorrectly
claim a model, adapter, KB version, or retrieval set.

Phase 5 uses one evaluation row per configuration and metric-only case rows.
The associated SRS artifacts retain their own `model_run` records; the
evaluation row does not invent one aggregate model run across many cases.

## 8. Privacy and Security

- Failure messages contain only the exception class.
- `metadata_json` is populated from controlled literals and counts.
- API responses use explicit allow lists and omit arbitrary metadata.
- Full prompts, project descriptions, answers, retrieved text, vectors,
  filesystem locations, secrets, and adapter contents are excluded.
- Project deletion cascades through ORM ownership to its model runs.

## 9. Demonstration

1. Start CyberSRS and generate an SRS normally.
2. Open `/api/v1/system/model-info` to show the active model and RAG setup.
3. Open the SRS workspace and point out the compact model/RAG/source indicator.
4. Copy the project and version IDs from the application URL/state.
5. Open `/api/v1/projects/{project_id}/srs/versions/{version_id}/provenance`.
6. Show model identity, actual RAG state, KB version, identifier lists, latency,
   status, and deterministic validation/repair flags.
7. For a pre-provenance SRS, show `legacy_unknown` rather than fabricated data.
