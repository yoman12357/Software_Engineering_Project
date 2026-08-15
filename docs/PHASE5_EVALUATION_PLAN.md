# Phase 5 Evaluation Plan

**Status:** Framework implemented; fine-tuned execution depends on the local adapter  
**Updated:** 2026-08-14

## Design

Phase 5 is a two-factor ablation over exactly four configurations:

| Configuration | `model_variant` | `rag_enabled` |
|---|---|---|
| `BASE` | `base` | `false` |
| `BASE_RAG` | `base` | `true` |
| `FINETUNED` | `finetuned` | `false` |
| `FINETUNED_RAG` | `finetuned` | `true` |

`ai/evaluation/phase5_metrics.py` contains the only four-way
`ConfigVariant`. It is an experiment configuration, not a second runtime
model-variant enum. `ai/evaluation/phase5_runner.py` starts an isolated,
in-process CyberSRS API for each configuration. Every cell therefore runs the
same project, analysis, clarification, SRS, retrieval, validation, and
provenance services with different settings; there are not four pipelines.

## Held-Out Boundary

The official source is `ai/evaluation/dataset.json` (30 frozen cases). The
runner rejects paths under `ai/finetuning`, including:

- `ai/finetuning/data/train.jsonl`
- `ai/finetuning/data/validation.jsonl`

The exclusion manifest remains `ai/finetuning/eval_exclusion_manifest.json`.
Phase 5 does not alter the evaluation dataset, fine-tuning files, RAG corpus,
or historical result folders.

## Raw and Final Outputs

A transparent provider decorator captures each unmodified SRS model response.
Raw JSON validity is strict: Markdown fences or prefaces remain invalid even
when production normalization can recover the enclosed object. The evaluator
stores `raw_output` and `raw_metrics` before deterministic processing, then
stores `final_output` and `final_metrics` from the persisted post-validation
artifact. Repair therefore cannot hide raw model behavior.

Metrics are deterministic: generation/schema success, requirement and threat
counts, clarification count, latency, double-shall, acceptance-criteria
format/paraphrase findings, unsupported numeric claims, numeric-provenance
violations, generic rationales, retrieval counts, and citation presence and
validity. Atomicity has no approved deterministic rule and is explicitly
`manual_unsupported`; no subjective score is fabricated. The final validation
score is the existing deterministic service score.

## Availability and Failure Semantics

Before running a cell, the runner checks `/api/tags` on local Ollama for the
exact resolved model name. Missing models are `UNAVAILABLE` with null metric
groups, never zero-valued fake results. `--config all` continues to later
cells and preserves already completed base results. A RAG cell is failed if
RAG was requested but provenance shows retrieval was not actually used.

## Storage

Each run creates a new directory under `ai/evaluation/phase5_results/` and
writes:

- `summary.json`
- `per_case_results.json`
- `comparison.md`
- `evaluation.sqlite`

Portable and SQLite records include evaluation/configuration IDs, requested
configuration, actual model name, case ID, raw/final metrics, retrieval
identifiers, latencies, timestamp, and status. SQLite stores metrics and
identifier metadata, not full Chroma documents or vectors.

## CLI

```powershell
python -m ai.evaluation.phase5_runner --config base
python -m ai.evaluation.phase5_runner --config base-rag
python -m ai.evaluation.phase5_runner --config finetuned
python -m ai.evaluation.phase5_runner --config finetuned-rag
python -m ai.evaluation.phase5_runner --config all
```

Use `--case-ids` or `--max-cases` for a smoke run. A nonzero exit indicates
that no selected configuration completed; per-configuration details remain in
`summary.json`.
