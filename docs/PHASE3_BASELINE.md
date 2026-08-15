# Phase 3 Baseline

This baseline records the verified local Base Qwen vs Base Qwen + RAG evaluation for CyberSRS Phase 3. The baseline artifacts are preserved in the result directory below and should not be overwritten.

## Configuration

| Item | Value |
|---|---|
| Provider | Ollama |
| Model | `qwen3:4b-instruct-2507-q4_K_M` |
| Embedding model | `nomic-embed-text` |
| Vector database | ChromaDB |
| Chroma collection | `cybersrs_knowledge` |
| Chunk count | 4,470 |
| Context size | 8,192 tokens |
| Evaluation case IDs | `eval-001`, `eval-005`, `eval-007` |
| Result directory | `ai/evaluation/results/eval-20260809-204147-548eb018` |

## Base Metrics

| Metric | Value |
|---|---:|
| Total cases | 3 |
| Fully successful cases | 3 |
| Analysis success | 100.0% |
| Clarification success | 100.0% |
| SRS success | 100.0% |
| Analysis schema validity | 100.0% |
| SRS schema validity | 100.0% |
| Category accuracy mean | 0.611 |
| Average requirements per SRS | 11.7 |
| Duplicate ID rate | 0.000 |
| Missing statement rate | 0.000 |
| Missing acceptance rate | 0.000 |
| Invalid priority rate | 0.000 |
| Average total latency | 106.47s |

## Base + RAG Metrics

| Metric | Value |
|---|---:|
| Total cases | 3 |
| Fully successful cases | 3 |
| Analysis success | 100.0% |
| Clarification success | 100.0% |
| SRS success | 100.0% |
| Analysis schema validity | 100.0% |
| SRS schema validity | 100.0% |
| Category accuracy mean | 0.583 |
| Average requirements per SRS | 12.3 |
| Duplicate ID rate | 0.000 |
| Missing statement rate | 0.000 |
| Missing acceptance rate | 0.000 |
| Invalid priority rate | 0.000 |
| Retrieval success | 100.0% |
| Average retrieval latency | 1.55s |
| Average chunks retrieved | 27.3 |
| Citation presence | 100.0% |
| Citation validity | 100.0% |
| Citation precision | 1.000 |
| Unsupported citation rate | 0.000 |
| Security requirement coverage | 1.000 |
| Hallucination indicator rate | 0.000 |
| Average total latency | 126.95s |
| RAG overhead | 19.53s |

## Baseline Verdict

Phase 3 RAG is baseline-complete for the verified three-case smoke evaluation: retrieval, citation preservation, schema validation, and Base vs RAG comparison all passed with the local Ollama provider.
