# Model Variant Architecture

**Status:** Implemented and integration-audited  
**Updated:** 2026-08-14

## Canonical Representation

`src/llm/registry.py` owns the only `ModelVariant` enum:

| Variant | Default Ollama model | Adapter identifier |
|---|---|---|
| `base` | `qwen3:4b-instruct-2507-q4_K_M` | none |
| `finetuned` | `cybersrs-qwen3-4b-ft` | same as model tag |

The two default model tags are defined once in
`src/core/model_constants.py`. Settings and the registry both import those
constants. Prompt modules do not select models.

`CYBERSRS_MODEL_VARIANT` defaults to `base`. The optional
`CYBERSRS_BASE_MODEL_NAME` and `CYBERSRS_FINETUNED_MODEL_NAME` variables
override the corresponding local Ollama tags. For backward compatibility,
an installation that only sets the older `CYBERSRS_MODEL_NAME` variable uses
that value as its base-model override.

## Resolution and Failure Behavior

`resolve_model_config(settings)` validates the variant and returns one
`ModelConfig`. `create_llm_provider(settings)` copies the resolved name into
the provider settings before constructing the Ollama provider.

There is no fallback from `finetuned` to `base`. An empty fine-tuned model
name is rejected during configuration. If the configured tag is absent from
Ollama, generation returns a clear `LLMOutputError` naming the missing tag and
the corresponding `ollama pull` command. The application does not claim that
the adapter is currently installed.

## RAG Independence

RAG is controlled only by `CYBERSRS_RAG_ENABLED` or the service's `use_rag`
argument. It does not depend on `ModelVariant`. The supported matrix is:

| Configuration | Model variant | RAG |
|---|---|---|
| `BASE` | `base` | off |
| `BASE_RAG` | `base` | on |
| `FINETUNED` | `finetuned` | off |
| `FINETUNED_RAG` | `finetuned` | on |

Both model variants use the same provider class, prompts, schemas, SRS
service, deterministic validation, retrieval implementation, and citation
validation. Only the Ollama model tag and independent RAG flag differ.

## Provenance

Successful generated artifacts record the configured variant and the actual
provider model name. SRS provenance additionally records actual RAG use, KB
version, retrieved identifiers, citations, timing, and deterministic
validation/repair flags. Legacy rows remain nullable and are reported as
`legacy_unknown`.

## Verification

Regression tests cover base defaults, both variant resolutions, custom model
tags, the legacy base override, invalid/empty configuration, missing Ollama
models, no silent fallback, and all four independent model/RAG combinations.
