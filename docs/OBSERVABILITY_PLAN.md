# Observability Plan — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

> All observability is **local and privacy-aware**. The system must not log full sensitive user content by default.

---

## 1. Structured Logs

All log entries are structured JSON written to stdout (or a configurable file).

**Log entry schema:**

```json
{
  "timestamp": "2026-01-01T00:00:00.000Z",
  "level": "INFO",
  "logger": "cybersrs.services.srs_generator",
  "correlation_id": "uuid",
  "generation_run_id": "uuid | null",
  "event": "srs_section_generated",
  "component": "srs_generator",
  "duration_ms": 12340,
  "details": {}
}
```

**Log level configuration:** `CYBERSRS_LOG_LEVEL` environment variable (default `INFO`).

| Level | When to use |
|---|---|
| `DEBUG` | Development only. Prompt template names, chunk IDs, model parameters. Never user content. |
| `INFO` | Request lifecycle, generation-run lifecycle, phase transitions. |
| `WARNING` | Retry attempts, RAG fallback, low quality scores, validation warnings. |
| `ERROR` | Failures: LLM errors, database errors, PDF errors, schema validation failures. |

---

## 2. Correlation IDs

Every API request is assigned a unique `correlation_id` (UUID v4).

- Generated at the API layer when a request arrives.
- Passed through all service calls, LLM calls, and database operations.
- Included in every log entry for that request.
- Returned to the frontend in the `X-Correlation-ID` response header.
- Enables tracing a request through the entire system.

---

## 3. Generation-Run IDs

Every SRS generation (or regeneration) creates a `GenerationRun` with a unique ID.

- The `generation_run_id` is included in all log entries during that generation.
- Links logs to the `GenerationRun` database record.
- Enables post-hoc analysis of generation performance and failures.

---

## 4. Timing Metrics

| Metric | What is timed | Stored in |
|---|---|---|
| `llm_call_duration_ms` | Each individual LLM inference call | Log entry |
| `total_generation_duration_ms` | Wall-clock time for the entire SRS generation | `GenerationRun.generation_time_seconds` |
| `rag_retrieval_duration_ms` | ChromaDB query time | Log entry |
| `pdf_generation_duration_ms` | PDF rendering time | Log entry |
| `api_request_duration_ms` | Total API request handling time | Log entry |
| `schema_validation_duration_ms` | Pydantic validation time | Log entry (DEBUG only) |

---

## 5. Token Estimates

Since Ollama does not always return exact token counts, the system estimates token usage:

| Metric | How estimated | Stored in |
|---|---|---|
| `prompt_tokens_est` | Character count ÷ 4 (rough estimate) | Log entry |
| `completion_tokens_est` | Character count of response ÷ 4 | Log entry |
| `total_tokens_est` | Sum of above | Log entry |

If Ollama returns actual token counts in the response, use those instead.

---

## 6. Retrieval Metrics

| Metric | Description | Stored in |
|---|---|---|
| `chunks_retrieved` | Number of chunks returned by ChromaDB | Log entry |
| `chunks_after_filtering` | Number after score filtering | Log entry |
| `top_relevance_score` | Highest relevance score | Log entry |
| `bottom_relevance_score` | Lowest relevance score (above threshold) | Log entry |
| `retrieval_queries_issued` | Number of queries issued | Log entry |
| `chunks_deduplicated` | Number of duplicates removed | Log entry |

---

## 7. Error Categories

Errors are categorised for aggregation:

| Category | Examples |
|---|---|
| `llm_connection_error` | Ollama unreachable |
| `llm_timeout_error` | LLM call exceeded timeout |
| `llm_invalid_json` | LLM returned non-JSON or invalid JSON |
| `llm_schema_error` | JSON valid but fails Pydantic validation |
| `rag_connection_error` | ChromaDB unreachable |
| `rag_empty_result` | No chunks retrieved |
| `db_write_error` | SQLite write failure |
| `db_read_error` | SQLite read failure |
| `pdf_generation_error` | PDF rendering failure |
| `file_validation_error` | Uploaded file rejected |
| `input_validation_error` | API request validation failure |
| `path_traversal_error` | Path-traversal attempt detected |

Each error log entry includes the `error_category` field.

---

## 8. Model Configuration Recording

Every `GenerationRun` records:

| Field | Description |
|---|---|
| `model_name` | Ollama model identifier (e.g., `qwen3:4b`) |
| `adapter_name` | QLoRA adapter identifier (null if base model) |
| `prompt_template_version` | Version string of the prompt templates used |
| `rag_enabled` | Whether RAG retrieval was used |
| `rag_top_k` | Number of chunks requested |
| `rag_min_score` | Minimum relevance score threshold |
| `llm_temperature` | Temperature setting (if configurable) |
| `llm_max_tokens` | Maximum output tokens |

---

## 9. Knowledge-Base Version Recording

| Field | Description | Stored in |
|---|---|---|
| `kb_document_count` | Number of source documents in ChromaDB | `GenerationRun` metadata |
| `kb_chunk_count` | Total chunks in ChromaDB | `GenerationRun` metadata |
| `kb_last_ingestion_date` | Timestamp of the most recent ingestion | `GenerationRun` metadata |

This enables tracing which version of the knowledge base was used for each generation.

---

## 10. Adapter Version Recording

| Field | Description | Stored in |
|---|---|---|
| `adapter_version` | Adapter directory name (e.g., `adapter_v1`) | `GenerationRun.adapter_name` |
| `adapter_hash` | SHA-256 hash of the adapter weights | `GenerationRun` metadata |
| `training_date` | When the adapter was trained | Adapter directory metadata |

---

## 11. Redaction Rules

| Rule | Implementation |
|---|---|
| **R-01:** User project descriptions are never logged in full. | Truncate to 50 characters + `[REDACTED]`. |
| **R-02:** Clarification answers are never logged. | Replace with `[ANSWER_REDACTED]`. |
| **R-03:** Generated SRS content is never logged. | Replace with `[SRS_CONTENT_REDACTED]`. |
| **R-04:** LLM prompt content (user portion) is never logged. | Log only the prompt template name and version. |
| **R-05:** LLM response content is never logged at INFO or above. | At DEBUG: log first 100 characters only. |
| **R-06:** `.env` values are never logged. | Configuration values logged with `[CONFIG_VALUE]`. |
| **R-07:** File paths in error messages are truncated to basenames. | Remove directory prefixes. |

**Implementation:** A `RedactionFilter` log filter is applied to all loggers. It processes each log record before output and applies the rules above.

---

## 12. MVP Observability Limitations

| Limitation | Accepted for MVP |
|---|---|
| No centralised log aggregation | Logs are local files/stdout only. |
| No metrics dashboard | Metrics are in logs; no Grafana/Prometheus. |
| No alerting | Errors are logged but no notifications are sent. |
| No distributed tracing | Single-process application; correlation IDs are sufficient. |
| No log rotation | User manages log files manually. |
| No performance baseline database | Metrics are in logs and GenerationRun records. |
