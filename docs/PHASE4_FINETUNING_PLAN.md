# Phase 4A: QLoRA Fine-Tuning Readiness Audit — CyberSRS

**Version:** 1.0.0
**Date:** 2026-08-12
**Status:** Audit complete — no training performed
**Scope:** Readiness only. No model was trained, no adapters were merged, no GGUF conversion was performed, and the Phase 3 baseline (`ai/evaluation/results/eval-20260809-204147-548eb018`) was not modified.

---

## 1. Objective

Prepare CyberSRS for QLoRA fine-tuning of the main model on **requirements-engineering behaviour** (structure, atomicity, testability, clarification quality, schema compliance) while leaving RAG's domain-knowledge responsibilities untouched (ADR-0005, ADR-0006). This document records the audited training model, the target environment, the dataset and task plan, the leakage-prevention mechanism, and a conservative QLoRA configuration.

---

## 2. Training Model Identification

### 2.1 Verified model mapping

| Attribute | Value |
|---|---|
| **Ollama inference model** | `qwen3:4b-instruct-2507-q4_K_M` (quantized runtime, **not** fine-tunable directly) |
| **Exact Hugging Face training model** | `Qwen/Qwen3-4B-Instruct-2507` |
| **License** | Apache-2.0 |
| **Architecture** | `Qwen3ForCausalLM` (`model_type: qwen3`) |
| **Parameters** | 4.0B total / 3.6B non-embedding |
| **Layers** | 36 |
| **Hidden size** | 2560 |
| **Intermediate size** | 9728 |
| **Attention heads** | 32 Q / 8 KV (GQA), head_dim 128 |
| **Context length** | 262,144 tokens native (`max_position_embeddings`); CyberSRS runtime uses 8,192 |
| **Tokenizer** | `Qwen2Tokenizer`, vocab 151,936 |
| **Chat template** | ChatML (`<|im_start|>` / `<|im_end|>`), supports system/user/assistant roles |
| **Thinking mode** | This variant is **non-thinking** — does not emit `<think>` blocks (2507 refresh) |
| **torch_dtype** | bfloat16 |
| **rope_theta** | 5,000,000; `tie_word_embeddings: true` |
| **Verified from** | Hugging Face model card + `config.json` + `tokenizer_config.json` (fetched 2026-08-12) |

**Verified module names for LoRA target modules** (from `Qwen3ForCausalLM` architecture): `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.

**Source:** https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507

**Note on Ollama ↔ HF equivalence:** the Ollama tag `qwen3:4b-instruct-2507-q4_K_M` is a GGUF Q4_K_M quantization built from the HF bf16 checkpoint `Qwen/Qwen3-4B-Instruct-2507`. It must never be used as the training base. Training must load the bf16 checkpoint from Hugging Face Hub.

---

## 3. Training Environment Audit

### 3.1 Current machine (verified 2026-08-12)

| Component | Verified value |
|---|---|
| OS | Windows (PowerShell 5.1) |
| Python | 3.12.10 |
| GPU | NVIDIA GeForce RTX 4050 Laptop GPU |
| VRAM | **6,141 MiB (~6 GB)** |
| GPU driver | 592.82, CUDA 13.1 capable |
| GPU utilisation during inference | 100% verified (Phase 3) |
| WSL2 | **Not installed** (no distributions) |
| `torch` | **Not installed** |
| `transformers` | 5.15.0 (installed) |
| `peft` | **Not installed** |
| `trl` | **Not installed** |
| `accelerate` | **Not installed** |
| `bitsandbytes` | **Not installed** |
| `chromadb` | 1.5.9 (installed) |

### 3.2 VRAM feasibility for QLoRA on a 4B model

Estimated peak VRAM for QLoRA training on `Qwen/Qwen3-4B-Instruct-2507` (36 layers, hidden 2560):

| Component | Estimate |
|---|---|
| Base weights in NF4 (4-bit) | ~2.3–2.6 GB |
| LoRA adapter weights + grads + AdamW states | ~0.3–0.5 GB |
| bf16 compute (fp32 master weights are avoided under QLoRA/NF4-with-fp16-compute) | ~0.3–0.6 GB |
| Activations (gradient checkpointing on, batch=1, seq=2048) | ~1.0–1.5 GB |
| Transformers / CUDA context overhead | ~0.5–1.0 GB |
| **Total estimate** | **~4.5–6.0 GB** |

**Verdict: local training is marginal-to-infeasible on the current 6 GB GPU.** It may fit only with batch size 1, `max_seq_length` ≤ 2048, gradient checkpointing on, and NF4 + fp16 compute — and any overhead spike (CUDA context, PyTorch fragmentation, Windows WDDM, concurrent Ollama serving) will push it out of memory. **Do not assume local training fits.** The safe recommendation is an environment with ≥ 16 GB VRAM.

### 3.3 Environment options

| Option | VRAM | Feasibility | Notes |
|---|---|---|---|
| A. Local Windows | 6 GB | Marginal / risky | Would need torch CUDA, bitsandbytes Windows wheel (supported since 0.43), peft, trl, accelerate. WDDM + 6 GB leaves no headroom. Serving must be stopped during training. |
| B. WSL2 Ubuntu | 6 GB (same GPU) | Marginal / risky | Better bitsandbytes support than native Windows, but VRAM is unchanged — still ~6 GB. WSL2 is not installed (needs distro setup). |
| C. Google Colab / Kaggle | 16 GB (T4) free / 40 GB (A100) paid | **Recommended** | Free T4 16 GB is enough for a 4B QLoRA run with headroom; GPU sessions are ephemeral — fine for a 4B model. |
| D. University / cloud NVIDIA GPU | 16–48 GB | Good | Most headroom; slowest queue; best for reproducibility (fixed driver/CUDA images). |

**Recommended environment: Option C (Google Colab or Kaggle free T4, 16 GB).** Rationale:

1. 16 GB gives comfortable headroom for batch size 2–4 at seq 2048 with gradient checkpointing.
2. No local dependency installation risk — clean Linux CUDA images with `bitsandbytes` working out of the box.
3. The dataset is small (target ~500–1,000 examples); a T4 completes a 4B QLoRA run in 1–3 hours.
4. Inference and RAG remain local and untouched; only the training run moves to the cloud, preserving the local-first deployment invariant (ADR-0004).

If the student prefers to keep everything local, the prerequisite is a GPU with ≥ 12 GB VRAM (ideally 16 GB) and a WSL2 Ubuntu or native Linux environment.

### 3.4 Required training libraries (pin at implementation time)

| Library | Purpose |
|---|---|
| `torch` (CUDA 12.x build) | Model compute; base model is bf16 |
| `transformers` (≥ 4.51; 5.15.0 present) | Model/tokenizer loading, chat template |
| `accelerate` | Device placement, DDP/zero |
| `peft` | LoRA / QLoRA adapter construction |
| `trl` | `SFTTrainer` + `DataCollatorForCompletionOnlyLM` |
| `bitsandbytes` | 4-bit NF4 base-model loading (QLoRA) |
| `datasets` | Dataset handling |
| `safetensors` | Adapter serialization (already present) |

**Compatibility guardrails:** `bitsandbytes` requires a CUDA-capable Linux or a supported Windows wheel (≥ 0.43) and a GPU with compute capability ≥ 7.5 (RTX 4050 = sm_89, OK). TRL/PEFT versions must be matched to the installed `transformers` major. Exact pins go into a dedicated `requirements-training.txt` during Phase 4B — none are installed in this audit.

---

## 4. Fine-Tuning Scope (What We Are / Are Not Training)

### 4.1 Behaviours fine-tuning must improve

| Behaviour | Description |
|---|---|
| Cybersecurity project analysis | Description → stakeholders/assets/users/constraints/goals/categories |
| Domain/subdomain inference | Correct CAT-01–CAT-08 inference |
| Missing-information detection | Genuine gaps; no false positives on stated facts |
| Clarification question generation | Relevant, targeted, non-redundant, correct criticality |
| Atomic requirement generation | One requirement = one testable statement |
| Requirement classification | Correct functional / non-functional / security category |
| Testable requirements | Measurable acceptance criteria |
| GIVEN-WHEN-THEN acceptance criteria | Structured, verifiable criteria |
| Useful rationales | Why the requirement exists |
| Numeric provenance | Measurable values traceable to stated input |
| Avoidance of unsupported assumptions | No invented scale/compliance claims |
| Requirement consistency | Stable IDs, no duplicates, cross-references intact |
| Structured JSON | Schema-compliant output on first attempt |
| No malformed "shall" language | Correct RE phrasing |
| Preservation of clarification answers | Context carries user answers into generation |

### 4.2 Behaviours that remain RAG responsibilities (NOT fine-tuning)

| Behaviour | Why |
|---|---|
| NIST / OWASP / MITRE ATT&CK / CIS factual content | External knowledge that updates; RAG retrieves current versions with citations |
| Specific control details | Standards evolve |
| Source attribution / citation | Fine-tuning cannot cite unseen documents |
| General factual grounding | A 4B model fine-tuned on a small dataset will still hallucinate |

---

## 5. Held-Out Evaluation Data Freeze

**Source of truth:** `ai/evaluation/dataset.json` (30 cases: `eval-001` … `eval-030`).

**Deliverable:** `ai/finetuning/eval_exclusion_manifest.json` (created in this audit) contains:

- The exact description of every evaluation case.
- All excluded case IDs and category names.
- Leakage-prevention rules:
  1. No exact match against excluded descriptions.
  2. No paraphrase with embedding cosine similarity > 0.80 to an excluded description.
  3. No generated SRS output derived from an excluded description.
  4. No expected-category mappings copied from excluded cases.
  5. Any candidate example with > 80% token overlap to an excluded description requires manual review.
  6. RAG chunks that directly answer an evaluation case must not be used to build input→output training pairs.

The held-out evaluation dataset itself is **not modified** and remains frozen for Phase 8/9 evaluation.

---

## 6. Multi-Task Training Dataset Plan

### 6.1 Task types

| Task type | Input | Output | Priority |
|---|---|---|---|
| `project_analysis` | Informal description | `ProjectAnalysis` JSON | Core |
| `clarification_generation` | Analysis + missing information | `ClarificationQuestionSet` JSON | Core |
| `missing_information_detection` | Vague description | `missing_information` array | Core |
| `requirement_generation` | Context + category | Requirement JSON | Core |
| `requirement_rewrite` | Poor requirement | Atomic testable requirement(s) | Core |
| `requirement_classification` | Requirement statement | Category + priority | Support |
| `acceptance_criteria_generation` | Requirement | GIVEN-WHEN-THEN criteria | Core |
| `numeric_provenance` | Requirement + facts | Numeric values with source | Support |
| `rationale_generation` | Requirement | Rationale | Support |
| `full_srs_generation` | Full context | Complete sectioned SRS JSON | Capstone |

### 6.2 Recommended distribution (target ~600–1,000 examples total)

| Task type | Target count | Share |
|---|---|---|
| `project_analysis` | 100 | ~12% |
| `clarification_generation` | 100 | ~12% |
| `missing_information_detection` | 60 | ~7% |
| `requirement_generation` | 180 | ~21% |
| `requirement_rewrite` | 100 | ~12% |
| `requirement_classification` | 60 | ~7% |
| `acceptance_criteria_generation` | 100 | ~12% |
| `numeric_provenance` | 60 | ~7% |
| `rationale_generation` | 60 | ~7% |
| `full_srs_generation` | 40 | ~5% |
| **Total** | **860** | 100% |

These targets supersede the smaller per-category targets in the draft `FINETUNING_PLAN.md` §5 (which totalled 390–550) — QLoRA on a 4B model benefits from more behavioural examples, but 1,000 stays small enough for T4-class hardware.

### 6.3 Dataset schema (JSONL, one example per line)

```json
{
  "id": "cybersrs-ft-000123",
  "task_type": "requirement_generation",
  "messages": [
    {"role": "system", "content": "System instructions + JSON schema for requirement generation."},
    {"role": "user", "content": "Project context JSON + clarification answers."},
    {"role": "assistant", "content": "Valid requirement JSON."}
  ],
  "source": {
    "kind": "synthetic",
    "origin": "student-authored from public scenario outline",
    "dataset_version": "cybersrs-training-v1",
    "project_category": "CAT-02",
    "eval_excluded": true
  },
  "quality": {
    "human_reviewed": true,
    "reviewer": "student",
    "schema_validated": true,
    "notes": "No eval-case overlap verified"
  },
  "split": "train",
  "provenance": {
    "licenses": ["Apache-2.0"],
    "attribution": "None required (synthetic)"
  }
}
```

**Field policy:**

- `split`: `train` / `validation` / `test` (80/10/10), assigned **before** any training; `test` never touched by training.
- `source.kind`: `synthetic` | `public` | `model_generated_corrected`.
- `source.eval_excluded`: mandatory boolean; must be `true` when the description is anything but unrelated to the 30 eval cases.
- `quality.schema_validated`: every assistant output must pass its Pydantic schema before it enters the dataset (AGENTS.md §10).
- `provenance.licenses`: records source-material licences; adapter inherits Apache-2.0 from Qwen3.
- No user data from CyberSRS usage may enter training data (PRIVACY_AND_DATA_HANDLING.md).

---

## 7. Data Source Audit

### 7.1 Existing in-repo references

| Source | Location | Reuse? |
|---|---|---|
| Phase 3 RAG corpus (NIST CSF 2.0, SP 800-53r5, SP 800-61r3, SP 800-63-4, SP 800-207, SP 800-41r1, SP 800-92, OWASP ASVS 5.0.0, OWASP Top 10 2025) | `corpus_extract/` + `ai/evaluation/corpus_inventory.json` | **Training: no** (standards content is RAG territory). **Eval: no** (would leak retrieval context). |
| Evaluation cases | `ai/evaluation/dataset.json` | Excluded — see §5. |
| Docs (PRD, SCOPE, SRS samples in DATA_MODEL.md) | `docs/` | Read for schema fidelity only, not copied verbatim. |

### 7.2 Candidate public datasets (audit report — no downloads performed)

| Dataset | Source / URL | License | Size | Fields | Usefulness to CyberSRS | Suitability |
|---|---|---|---|---|---|---|
| **RE-Bench** (requirements-engineering benchmark) | Hugging Face `catenary-ai/RE-Bench` | Apache-2.0 | ~2.6k requirement pairs | Original/issue/refined requirement pairs | Direct fit for `requirement_rewrite` + atomicity training | Training + evaluation (with eval-exclusion) |
| **RE-GSC / Requirements classification** | `anudeex/RE-GSC` (GitHub) | MIT | ~6.8k sentences | Requirement sentences, classes | `requirement_classification` task | Training |
| **QRAQ (Quality Requirements Assessment Quiz)** | `adrvis24/QRAQ_balanced` (Hugging Face) | CC-BY-4.0 | ~1.3k QA | Requirement quality Q/A | `requirement_rewrite`, quality detection, `acceptance_criteria` | Training |
| **WikiData requirements / SRS excerpts** | Public open-source SRS repos (e.g. OpenSRS by Lissi, jbrown132/SRS for smart-lock etc.) | Mixed (check per repo) | 10–100 docs | Full SRS text | `full_srs_generation` structure imitation | Training (careful per-repo licence check) |
| **OWASP / NIST structured controls** | Official GitHub repos (ASVS JSON, CCM, CSF) | CC-BY-4.0 / public-domain | Large | Control lists with verification requirements | **Not for training** — factual standards content stays in RAG | Evaluation only (never training) |
| **MITRE ATT&CK STIX** | `mitre-attack/attack-stix-data` | CC-BY-4.0 (MITRE) | Large | Technique/tactic graphs | **Not for training** — factual content stays in RAG | Evaluation only (never training) |
| **CCC (Cybersecurity & AI-generated RE datasets)** | General public coursework datasets | Mixed | Varies | RE texts | Cherry-pick only after manual review | Verify licence per item |

**Rule applied (per task instructions):** a dataset is considered for training only if it targets *requirements-engineering behaviour*, not *cybersecurity facts*. Standards corpora (NIST/OWASP/MITRE/CIS) are explicitly excluded from training regardless of licence.

---

## 8. Leakage Protection

| Control | Mechanism |
|---|---|
| Evaluation freeze | `ai/finetuning/eval_exclusion_manifest.json` lists all 30 descriptions + IDs + categories |
| Exact-match check | Training candidate description must not equal any excluded description |
| Near-match check | Embedding (nomic-embed-text, dim 768) cosine similarity to every excluded description must be ≤ 0.80; above → manual review |
| Output-level check | No generated SRS/answer in training may be an output produced *for* an excluded description |
| Category-label check | Expected-category sets of eval cases must not be reused as labels without transformation |
| RAG-copy check | Training examples must not be verbatim knowledge-base chunks (FINETUNING_PLAN §9) |
| Tooling | A `leakage_check.py` gate runs before dataset release; any failure blocks dataset export |

---

## 9. Conservative QLoRA Configuration (starting point — to be validated)

> Do not blindly copy settings from other Qwen models. These values are derived from the verified 4B architecture (36 layers, hidden 2560) and the 6–16 GB VRAM envelope, and must be validated on a small run first.

| Hyperparameter | Value | Rationale |
|---|---|---|
| Quantization | 4-bit, `bitsandbytes` NF4, bf16 compute | QLoRA standard; NF4 if supported |
| `double_quant` | `True` | Saves ~0.5 GB of base-model memory |
| LoRA rank `r` | 16 | Conservative; capacity for behavioural tuning without overfit |
| LoRA `alpha` | 32 | 2× rank (verified default convention) |
| LoRA dropout | 0.05 | Light regularisation |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` (all 7) | Verified module names in `Qwen3ForCausalLM`; all-linear coverage is standard for Qwen3 and improves structure learning |
| Learning rate | 2e-4 | QLoRA default for 4B-class |
| Epochs | 3 | Early-stop on validation loss |
| Per-device batch | 1 (local 6 GB) / 2–4 (T4 16 GB) | VRAM bound |
| Gradient accumulation | 8 (local) / 4 (T4) | Effective batch ≈ 16 |
| Gradient checkpointing | On | Required for 6–16 GB VRAM |
| Max sequence length | 2048 (fine-tuning) | Trains the behaviour, not long-context; runtime stays at 8192 |
| Optimizer | `paged_adamw_8bit` | Lowers optimizer memory; recommended for QLoRA |
| LR scheduler | Cosine | Standard |
| Warmup ratio | 0.03 | Standard |
| Weight decay | 0.01 | Light regularisation |
| Logging | `wandb=disabled`; console + TensorBoard CSV (local-first, no external service) | ADR-0004 |
| Checkpoint strategy | `steps`, save every 100 steps; keep best 3 by val loss | FINETUNING_PLAN §13 |
| Seed | `42` (Python, NumPy, torch, CUDA) | Reproducibility (FINETUNING_PLAN §17) |
| `report_to` | `none` (or local `tensorboard`) | No cloud tracking |

---

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| OOM on 6 GB local GPU | Training aborts mid-run | Prefer T4/Colab/Kaggle; batch=1 + checkpointing; stop Ollama during training |
| Qwen3 requires recent `transformers` | Loading fails | Pin `transformers>=4.51` (5.15.0 present); use latest PEFT/TRL matched to it |
| `bitsandbytes` Windows issues | Quantized load fails | Use WSL2/Linux (Colab/Kaggle) or bnb ≥ 0.43 Windows wheel |
| Small dataset overfits | Good train loss, poor held-out metrics | Dropout 0.05, early stopping, dedup, keep dataset ≤ 1,000 curated examples |
| Data leakage into training | False evaluation improvement | Exclusion manifest + similarity gate + category-label rule |
| Adapter does not help | C3 ≈ C1 | **Rollback is a valid documented outcome** (FINETUNING_PLAN §21) |
| Catastrophic regression (attack code, worse JSON) | Safety/schema failures | Post-training regression checks (FINETUNING_PLAN §19); rollback on failure |
| Ollama adapter loading unsupported (UDEC-003) | Deployment blocker | Fallback: load via Transformers + `PeftModel` directly |

---

## 11. Expected Evaluation (post-training)

Per EVALUATION_PLAN.md and ADR-0007, the fine-tuned adapter will be measured in the frozen 2×2 design:

| Config | Model | RAG |
|---|---|---|
| C1 (baseline, exists) | Base Qwen3-4B | Off |
| C2 (baseline, exists) | Base Qwen3-4B | On |
| C3 (new, Phase 8) | Fine-tuned (adapter) | Off |
| C4 (new, Phase 9) | Fine-tuned (adapter) | On |

**Success criteria (provisional, EVALUATION_PLAN §3):** C4 ≥ 90% schema validity; atomicity ≥ 0.80; testability keywords ≥ 0.70; acceptance-criteria presence ≥ 0.85; generation failure ≤ 10%; retries ≤ 0.5 avg. Expected ordering hypothesis: **C4 > C2 ≈ C3 > C1** — to be validated, not assumed.

---

## 12. Deliverables of This Audit

| Deliverable | Path |
|---|---|
| Evaluation exclusion manifest | `ai/finetuning/eval_exclusion_manifest.json` (created) |
| This plan | `docs/PHASE4_FINETUNING_PLAN.md` (created) |

**Files NOT modified in this audit:** `ai/evaluation/dataset.json`, all files under `ai/evaluation/results/eval-20260809-204147-548eb018`, the Chroma collection, the Ollama/Ollama model configuration, and all Phase 1–3 source code.

**Explicitly out of scope for this audit:** dataset construction (Phase 4B), training (Phase 4C), adapter merge, GGUF conversion, and any change to production inference.
