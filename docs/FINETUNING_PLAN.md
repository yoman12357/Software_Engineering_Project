# Fine-Tuning Plan — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

> Fine-tuning improves the model's **requirements-engineering behaviour, structure, completeness, atomicity, testability, clarification-question quality, and schema compliance**. It does **not** replace RAG as the mechanism for cybersecurity domain knowledge, standards, or source attribution.

> Fine-tuning does **not guarantee factual correctness**. Factual grounding is the responsibility of RAG retrieval and user review.

---

## 1. Fine-Tuning Objectives

| ID | Objective | Measurable? |
|---|---|---|
| FT-OBJ-01 | Improve JSON-schema compliance rate of generated SRS output. | Yes — schema validation pass rate. |
| FT-OBJ-02 | Improve requirement atomicity (one requirement = one testable statement). | Yes — atomicity rubric score. |
| FT-OBJ-03 | Improve requirement testability (every requirement has measurable acceptance criteria). | Yes — testability rubric score. |
| FT-OBJ-04 | Improve completeness of generated SRS sections (all expected sections present with sufficient content). | Yes — completeness checklist score. |
| FT-OBJ-05 | Improve quality of clarification questions (relevant, targeted, non-redundant). | Yes — question-quality rubric score. |
| FT-OBJ-06 | Reduce ambiguity in generated requirements. | Yes — ambiguity rubric score. |
| FT-OBJ-07 | Improve correct use of requirement ID naming conventions. | Yes — ID-format validation. |
| FT-OBJ-08 | Reduce retry rate (fewer invalid outputs per generation). | Yes — retry count per generation run. |

## 2. Behaviours to Improve (Fine-Tuning Territory)

| Behaviour | Description |
|---|---|
| Structured output adherence | Consistently producing valid JSON matching the expected Pydantic schema. |
| Requirements-engineering conventions | Using "The system shall…" language, assigning proper IDs, categorising correctly. |
| Atomicity | Writing one requirement per item instead of compound statements. |
| Testability | Including measurable, verifiable acceptance criteria. |
| Completeness | Covering all expected SRS sections with sufficient detail. |
| Clarification quality | Asking relevant, specific, non-obvious questions targeting real information gaps. |
| Priority assignment | Correctly distinguishing Must/Should/Could priorities. |
| Threat-model structure | Producing well-structured STRIDE-based threat entries with mitigations. |

## 3. Behaviours That Should Remain in RAG

| Behaviour | Why NOT fine-tuning |
|---|---|
| OWASP, NIST, MITRE ATT&CK, CIS content | These are external knowledge that updates over time. RAG retrieves current versions; fine-tuning would bake in stale snapshots. |
| Specific security controls and their details | Same as above — standards evolve. |
| Source attribution and citation | RAG provides traceable source references; fine-tuning cannot provide citations to external documents. |
| Domain-specific technical facts | Fine-tuning a 4B model on a small dataset will not reliably memorise technical facts. |

---

## 4. Training-Example Format

Each training example is an instruction-input-output triple in JSONL format:

```json
{
  "instruction": "Generate functional requirements for the following cybersecurity project.",
  "input": "Project context: [structured context JSON]. Retrieved knowledge: [relevant chunks].",
  "output": "[Expected SRS section JSON conforming to the schema]"
}
```

**Conversation format (alternative, for multi-turn tasks):**

```json
{
  "messages": [
    {"role": "system", "content": "[System instructions + schema]"},
    {"role": "user", "content": "[Project context + retrieved knowledge]"},
    {"role": "assistant", "content": "[Expected output JSON]"}
  ]
}
```

The specific format depends on Qwen3's chat template. The conversation format is preferred for compatibility with TRL's `SFTTrainer`.

## 5. Multi-Task Dataset Categories

| Category | Task | Approximate Target |
|---|---|---|
| Context extraction | Description → `ProjectAnalysis` JSON | 60–80 examples |
| Clarification questions | Analysis + gaps → `ClarificationQuestionSet` JSON | 40–60 examples |
| Functional requirements | Context → FR JSON | 60–80 examples |
| Non-functional requirements | Context → NFR JSON | 40–60 examples |
| Security requirements | Context → SEC JSON | 60–80 examples |
| System architecture | Context → ARCH JSON | 30–40 examples |
| Threat model | Context + architecture → THREAT JSON | 40–60 examples |
| Acceptance criteria | Context → AC JSON | 30–40 examples |
| Correction examples | Invalid output → corrected output | 30–50 examples |
| **Total** | | **390–550 examples** |

See [DATASET_PLAN.md](DATASET_PLAN.md) for detailed specifications per category.

## 6. Data Cleaning

1. Remove duplicate examples (exact match on input+output).
2. Validate every output against its Pydantic schema.
3. Remove examples with inconsistent requirement IDs.
4. Remove examples with hallucinated citations (cite sources not in the input).
5. Normalise whitespace and JSON formatting.
6. Verify no PII or real organisational data in examples.

## 7. Data Deduplication

- Exact-match deduplication on the `output` field.
- Near-duplicate detection using Jaccard similarity on tokenised output (threshold > 0.85 → deduplicate).
- After deduplication, verify category balance is maintained.

## 8. Train, Validation, and Test Splits

| Split | Proportion | Purpose |
|---|---|---|
| Training | 80% | Model training |
| Validation | 10% | Hyperparameter tuning, early stopping |
| Test (held-out) | 10% | Final evaluation only; never used during training |

**Constraint:** The test split must contain examples from all dataset categories. It must remain untouched until Phase 9 evaluation.

## 9. Leakage Prevention

| Risk | Prevention |
|---|---|
| Test examples seen during training | Strict split before training begins; automated check that no test example appears in training set. |
| RAG chunks appearing as training examples | Training examples must not be copied verbatim from knowledge-base documents. |
| Evaluation prompts used in training | Evaluation prompts from DEMO_PLAN.md must not appear in the training set. |

## 10. Baseline Recording

Before any fine-tuning, record the base model's performance on the test set:

1. Run all test examples through the base model (no adapter).
2. Record all metrics defined in [EVALUATION_PLAN.md](EVALUATION_PLAN.md).
3. Store results as `EvaluationRun` records in the database.
4. This baseline is one of the four evaluation configurations (see ADR-0007).

## 11. Hardware Constraints

| Resource | Minimum | Recommended |
|---|---|---|
| GPU VRAM | 8 GB (with 4-bit quantisation) | 16 GB |
| System RAM | 16 GB | 32 GB |
| Disk | 20 GB free | 50 GB free |
| Training time (estimated) | 2–6 hours (consumer GPU) | 1–3 hours (better GPU) |

**CPU-only training:** Possible but extremely slow (days). Not recommended. If no GPU is available, consider using a cloud GPU instance for training only (inference remains local).

## 12. Initial Conservative Hyperparameter Plan

These are starting points. They must be experimentally validated.

| Hyperparameter | Initial Value | Notes |
|---|---|---|
| LoRA rank (r) | 16 | Conservative; higher rank = more capacity but more compute |
| LoRA alpha | 32 | Typically 2× rank |
| LoRA dropout | 0.05 | Light regularisation |
| Target modules | `q_proj`, `v_proj` | Standard for Qwen; may expand to `k_proj`, `o_proj` |
| Learning rate | 2e-4 | Standard for QLoRA |
| Batch size | 4 (with gradient accumulation of 4) | Effective batch size = 16 |
| Epochs | 3–5 | Monitor validation loss for early stopping |
| Warmup ratio | 0.03 | Standard |
| Weight decay | 0.01 | Light regularisation |
| Quantisation | 4-bit (nf4) | QLoRA standard |
| Max sequence length | 2048 tokens | Balance between context and memory |
| Scheduler | Cosine | Standard for QLoRA |

## 13. Checkpointing

- Save checkpoints every N steps (e.g., every 100 steps or every epoch).
- Save the best checkpoint by validation loss.
- Retain the top 3 checkpoints and delete older ones to save disk space.
- Each checkpoint records the training step, validation loss, and training hyperparameters.

## 14. Experiment Tracking

| What to track | How |
|---|---|
| Hyperparameters | Logged to a training config JSON file and/or TensorBoard. |
| Training loss (per step) | TensorBoard or CSV log. |
| Validation loss (per epoch) | TensorBoard or CSV log. |
| Evaluation metrics (per checkpoint) | Recorded as `EvaluationRun` records. |
| Training time | Wall-clock time logged. |
| Hardware used | GPU model, VRAM, RAM logged. |

**MVP approach:** Use TRL's built-in logging + TensorBoard. No MLflow or Weights & Biases (would add external dependencies).

## 15. Adapter Storage

- Adapters are saved to `CYBERSRS_ADAPTER_PATH` (configurable, default `./data/adapters/`).
- Each adapter version is stored in a subdirectory named `adapter_v{N}`.
- The adapter directory contains:
  - `adapter_config.json` — LoRA configuration
  - `adapter_model.safetensors` — adapter weights
  - `training_config.json` — hyperparameters used
  - `adapter_hash.sha256` — SHA-256 hash (SEC-036)

## 16. Adapter Loading

Two paths (UDEC-003 in DECISIONS.md):

1. **Ollama Modelfile:** Create a Modelfile that references the base model + adapter. Requires Ollama to support LoRA adapters.
2. **Hugging Face Transformers direct:** Load the base model + PEFT adapter directly using `AutoModelForCausalLM` + `PeftModel`. Bypass Ollama for fine-tuned inference.

Decision is deferred to Phase 8 based on Ollama's adapter support at implementation time.

## 17. Reproducibility

| Requirement | How |
|---|---|
| Deterministic training | Set random seeds (Python, PyTorch, NumPy). |
| Reproducible results | Log all hyperparameters, dataset version, and model version. |
| Environment reproducibility | Pin all training dependencies in a separate `requirements-training.txt`. |

## 18. Overfitting Checks

| Check | Trigger |
|---|---|
| Validation loss increases for 2+ consecutive epochs | Stop training; use best checkpoint. |
| Training loss near zero but validation loss plateaus | Likely overfitting; reduce epochs or increase dropout. |
| Model memorises training examples verbatim | Spot-check generated output against training examples; apply deduplication. |
| Model loses general instruction-following ability | Run a small set of general-knowledge prompts before and after; compare. |

## 19. Catastrophic-Behaviour Regression Checks

After training, verify that the fine-tuned model does not:

1. Produce executable attack code (SEC-004, SEC-025).
2. Fail to generate valid JSON on previously successful prompts.
3. Generate offensive or harmful content.
4. Hallucinate more than the base model (measured by citation precision).

If any regression is detected, roll back to the base model and investigate.

## 20. Stopping Criteria

Stop training when:

1. Validation loss has not improved for 2 epochs (early stopping).
2. The maximum number of epochs is reached.
3. A catastrophic-behaviour check fails (immediate stop + investigation).

## 21. Rollback Criteria

Roll back to the base model (discard adapter) if:

1. The fine-tuned model performs worse than the base model on the test set across a majority of metrics.
2. Catastrophic-behaviour regression is detected and cannot be fixed.
3. The adapter produces systematically invalid JSON at a higher rate than the base model.

**Rollback is a valid outcome.** If fine-tuning does not help, the project documents this honestly.

## 22. Licence and Dataset Documentation

- All training data must be documented in a dataset card (see DATASET_PLAN.md).
- Training data must comply with the licences of source materials.
- The adapter weights inherit the licence of the base model (Qwen3's licence).
- No user data shall be included in the training dataset (PRIVACY_AND_DATA_HANDLING.md §10).
