# Test Strategy — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

---

## 1. Testing Principles

1. **Tests must pass before each phase transition** (roadmap completion gate).
2. **LLM-dependent tests use mocked responses** for determinism and speed.
3. **Real LLM tests are run separately** and documented as manual/integration tests.
4. **All test data is synthetic** — no real user data in test fixtures.
5. **Test runner:** pytest (Python), Vitest (TypeScript).

---

## 2. Test Categories

### 2.1 Unit Testing

| Scope | Examples | Phase |
|---|---|---|
| Pydantic schema models | Validate that sample JSON passes/fails correctly | 2 |
| Input sanitisation functions | HTML/shell metacharacter stripping | 2 |
| Requirement-ID generator | Unique, correctly formatted IDs | 3 |
| Chunk-metadata builder | Correct metadata fields populated | 4 |
| Validation rules (deterministic) | Completeness checks, atomicity heuristics | 5 |
| Path-traversal checker | Rejects `../` paths, allows valid paths | 1 |
| Redaction utility | Truncates and redacts sensitive strings | 1 |
| File-type validator | Accepts PDF/MD/TXT, rejects others | 4 |
| Configuration loader | Reads `.env`, applies defaults | 1 |
| PDF text escaper | Special characters safely escaped | 6 |

### 2.2 Schema Testing

| Scope | Examples | Phase |
|---|---|---|
| `ProjectAnalysis` schema | Valid and invalid samples | 2 |
| `ClarificationQuestionSet` schema | Valid and invalid samples | 2 |
| `SRSVersion` schema (all sections) | Valid and invalid SRS JSON | 3 |
| `ThreatModel` schema | Valid and invalid threat JSON | 5 |
| `ValidationReport` schema | Valid and invalid reports | 5 |
| Extra-key rejection (strict mode) | JSON with unexpected keys rejected | 2 |

### 2.3 API Testing

| Scope | Examples | Phase |
|---|---|---|
| Project CRUD endpoints | Create, list, get, update, delete | 1 |
| Health-check endpoint | Returns service status | 1 |
| Description-analysis endpoint | Returns valid analysis (mocked LLM) | 2 |
| Clarification endpoints | Get questions, submit answers | 2 |
| SRS-generation endpoint | Returns 202, generation-run status works | 3 |
| SRS-retrieval endpoint | Returns latest SRS JSON | 3 |
| Validation endpoint | Returns validation report | 5 |
| Regeneration endpoint | Regenerates selected section | 6 |
| Source-references endpoint | Returns chunk references | 4 |
| PDF-export endpoint | Returns export metadata | 6 |
| PDF-download endpoint | Returns PDF binary | 6 |
| Error responses | 400/404/422/503 with correct format | 1 |
| Request body-size limit | Oversized request returns 413 | 1 |
| Concurrent-run limit | Second run returns 429 | 3 |

### 2.4 Database Testing

| Scope | Examples | Phase |
|---|---|---|
| Project CRUD | Insert, read, update, delete | 1 |
| Cascade delete | Deleting project removes all related records | 1 |
| SRS version creation | New version increments version_number | 3 |
| Timestamp handling | All timestamps stored in UTC | 1 |
| Transaction integrity | Failed write does not leave partial data | 1 |
| Migration | Schema matches DATA_MODEL.md | 1 |

### 2.5 RAG Ingestion Testing

| Scope | Examples | Phase |
|---|---|---|
| Document parsing (PDF) | Extracts text with page numbers | 4 |
| Document parsing (Markdown) | Strips HTML, extracts sections | 4 |
| Chunking | Produces chunks within size limits; respects section boundaries | 4 |
| Metadata generation | All required metadata fields populated | 4 |
| Duplicate detection | Re-ingesting the same document does not create duplicates | 4 |
| File-type rejection | Rejects non-PDF/MD/TXT files | 4 |
| File-hash recording | SHA-256 hash matches expected value | 4 |
| Source-manifest update | Manifest records ingestion | 4 |

### 2.6 Retrieval Testing

| Scope | Examples | Phase |
|---|---|---|
| Query construction | Produces non-empty query strings from ProjectContext | 4 |
| ChromaDB query | Returns top-k results with metadata | 4 |
| Score filtering | Chunks below threshold are excluded | 4 |
| Empty collection | Returns empty results with no error | 4 |
| Deduplication | Multiple queries produce deduplicated results | 4 |

### 2.7 Citation Mapping Testing

| Scope | Examples | Phase |
|---|---|---|
| Valid citation | Cited source_id exists in ChromaDB | 4 |
| Hallucinated citation | Cited source_id does not exist → flagged | 4 |
| Citation propagation | Citations preserved from generation through storage to API response | 4 |

### 2.8 Prompt-Output Contract Testing

| Scope | Examples | Phase |
|---|---|---|
| Analysis prompt → ProjectAnalysis | Mocked LLM returns valid analysis JSON | 2 |
| Clarification prompt → ClarificationQuestionSet | Mocked LLM returns valid questions | 2 |
| SRS prompt → SRS section | Mocked LLM returns valid SRS section JSON | 3 |
| Threat prompt → ThreatModel | Mocked LLM returns valid threat JSON | 5 |
| Validation prompt → ValidationReport | Mocked LLM returns valid report | 5 |
| Corrective prompt → corrected JSON | Mocked LLM fixes errors after retry | 2 |

### 2.9 Invalid Model Output Testing

| Scope | Examples | Phase |
|---|---|---|
| Non-JSON response | System retries with corrective prompt | 2 |
| Truncated JSON | System retries | 2 |
| Extra keys (strict mode) | System rejects | 2 |
| Missing required fields | System retries | 2 |
| Invalid enum values | System retries | 2 |
| All retries exhausted | System returns structured error | 2 |

### 2.10 LLM Timeout Testing

| Scope | Examples | Phase |
|---|---|---|
| Timeout on inference | System returns error after configured timeout | 2 |
| Retry after timeout | System retries up to max retries | 2 |
| All timeouts exhausted | System returns 503 | 2 |

### 2.11 Vector-Store Failure Testing

| Scope | Examples | Phase |
|---|---|---|
| ChromaDB unreachable | System generates without RAG, warns user | 4 |
| ChromaDB returns error | Same as above | 4 |
| ChromaDB returns empty | System generates without context, shows notice | 4 |

### 2.12 PDF Generation Testing

| Scope | Examples | Phase |
|---|---|---|
| Valid SRS → PDF | PDF is generated without errors | 6 |
| PDF contains all sections | Section headings present | 6 |
| PDF text escaping | Special characters render correctly | 6 |
| PDF file size > 0 | Non-empty file produced | 6 |
| PDF from non-validated SRS | Rejected (SEC-044) | 6 |

### 2.13 Security Testing

| Scope | Examples | Phase |
|---|---|---|
| Prompt injection | Adversarial description does not bypass schema validation | 5 |
| Path traversal | `../` paths rejected | 4 |
| File-upload bypass | Renamed `.exe` with `.pdf` extension rejected | 4 |
| Oversized request | Returns 413 | 1 |
| Error-message sanitisation | No stack traces in API responses | 1 |
| Localhost binding | Verify API not accessible from external hosts | 1 |

### 2.14 Frontend Testing

| Scope | Examples | Phase |
|---|---|---|
| Project list renders | Shows projects from API | 1 |
| Project creation form | Creates project on submit | 1 |
| Description input | Saves description | 2 |
| Clarification panel | Shows questions, accepts answers | 2 |
| SRS viewer | Displays all sections | 3 |
| Inline editing | Edits save correctly | 6 |
| Progress indicators | Visible during generation | 3 |
| PDF download | File downloads successfully | 6 |

**Framework:** Vitest for unit tests; React Testing Library for component tests.

### 2.15 End-to-End Testing

| Scope | Examples | Phase |
|---|---|---|
| Full workflow (mocked LLM) | Create project → analyse → clarify → generate → validate → export | 6 |
| Full workflow (real LLM) | Same as above with Ollama running | 10 |
| Demo project 1 | College firewall (DEMO_PLAN.md) | 10 |
| Demo project 2 | Secure API gateway | 10 |
| Demo project 3 | IAM portal | 10 |

### 2.16 Regression Testing

- All existing tests run before each phase transition.
- Any test that previously passed must continue to pass.
- New features must not break existing functionality.

### 2.17 Fine-Tuning Pipeline Smoke Tests

| Scope | Examples | Phase |
|---|---|---|
| Dataset loading | JSONL loads without errors | 7 |
| Training starts | One training step completes without error | 8 |
| Checkpoint saving | Checkpoint file is created | 8 |
| Adapter loading | Adapter loads and produces output | 8 |
| Adapter hash verification | Hash matches recorded value | 8 |

### 2.18 Evaluation Reproducibility

| Scope | Examples | Phase |
|---|---|---|
| Same input → same metrics | Running evaluation twice on the same config produces identical automated metrics | 9 |
| Evaluation script exits cleanly | No errors or missing data | 9 |
| Results table is populated | All cells in the template tables are filled | 9 |

---

## 3. Tests Blocking Phase Transitions

| Phase Gate | Required Tests |
|---|---|
| **Phase 1 → 2** | Unit: config, path traversal, redaction. API: CRUD, health, error responses, body-size limit. DB: CRUD, cascade, transactions, timestamps. Frontend: project list, creation. |
| **Phase 2 → 3** | Schema: ProjectAnalysis, ClarificationQuestionSet. API: analysis, clarification. Prompt-output: analysis, clarification. Invalid output: all retry scenarios. Timeout: all. |
| **Phase 3 → 4** | Schema: all SRS sections. API: SRS generation, retrieval, status. Prompt-output: SRS sections. E2E (mocked): create → generate → view. |
| **Phase 4 → 5** | Ingestion: parsing, chunking, metadata, dedup, file-type, hash. Retrieval: query, score filter, empty collection. Citation: valid, hallucinated, propagation. Vector-store failure: all. |
| **Phase 5 → 6** | Schema: ThreatModel, ValidationReport. API: validation. Security: prompt injection, path traversal, file upload, error sanitisation. |
| **Phase 6 → 7** | PDF: generation, sections, escaping, non-validated rejection. API: export, download, update, regenerate. E2E (mocked): full workflow. |
| **Phase 7 → 8** | Dataset: loading, schema validation. |
| **Phase 8 → 9** | Fine-tuning smoke: training step, checkpoint, adapter loading, hash. |
| **Phase 9 → 10** | Evaluation: reproducibility, results populated. |
| **Phase 10 (release)** | All tests pass. E2E (real LLM): 3 demo projects. |
