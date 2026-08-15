# Dataset Plan — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

> No ready-to-use perfect dataset exists for this task. All datasets must be constructed, validated, and documented before use.

---

## 1. Dataset Categories

### 1.1 Informal Idea → Structured Context

| Attribute | Value |
|---|---|
| **Input format** | Informal project description (1–5 sentences of free text). |
| **Output format** | `ProjectAnalysis` JSON (stakeholders, assets, users, constraints, goals, inferred_categories, missing_information). |
| **Minimum quality criteria** | Output is valid JSON; all required fields populated; inferred categories are from CAT-01–CAT-08; extraction is accurate. |
| **Positive examples** | Well-structured extractions from clear descriptions across all 8 categories. |
| **Negative/correction examples** | Partially correct extractions that are then corrected (shows the model what to fix). |
| **Human-review requirements** | Every example must be reviewed by a human for accuracy of extraction. |
| **Approximate initial target** | 60–80 examples. |
| **Split strategy** | 80/10/10 (train/val/test). |
| **Source-provenance requirements** | Descriptions are synthetic (written by the student) or adapted from public project descriptions (with provenance noted). |

### 1.2 Subdomain Classification

| Attribute | Value |
|---|---|
| **Input format** | Informal project description. |
| **Output format** | List of inferred categories (CAT-01–CAT-08). |
| **Minimum quality criteria** | Correct category assignment; multi-category descriptions correctly identify all relevant categories. |
| **Positive examples** | Descriptions that clearly map to 1–3 categories. |
| **Negative/correction examples** | Descriptions with incorrect initial classification, then corrected. Out-of-scope descriptions correctly labelled as unsupported. |
| **Human-review requirements** | All examples must be human-verified. |
| **Approximate initial target** | Covered within §1.1 (same examples, focus on the `inferred_categories` field). |
| **Split strategy** | Same split as §1.1. |
| **Source-provenance requirements** | Same as §1.1. |

### 1.3 Missing-Information Detection

| Attribute | Value |
|---|---|
| **Input format** | Informal project description (intentionally vague or missing key details). |
| **Output format** | `missing_information` array listing specific gaps. |
| **Minimum quality criteria** | Identified gaps are genuine and not trivial; no false positives (claiming something is missing when it's stated). |
| **Positive examples** | Vague descriptions with 3–5 correctly identified gaps. Complete descriptions with empty `missing_information`. |
| **Negative/correction examples** | Examples where the model identifies too many or too few gaps, then corrected. |
| **Human-review requirements** | All examples must be human-verified. |
| **Approximate initial target** | Covered within §1.1. |
| **Split strategy** | Same as §1.1. |
| **Source-provenance requirements** | Same as §1.1. |

### 1.4 Clarification Questions

| Attribute | Value |
|---|---|
| **Input format** | `ProjectAnalysis` JSON with `missing_information`. |
| **Output format** | `ClarificationQuestionSet` JSON (questions with reason, criticality, target gap). |
| **Minimum quality criteria** | Questions are relevant to the identified gaps; not redundant; correctly marked as critical/non-critical; well-phrased. |
| **Positive examples** | 3–5 well-targeted questions per project. |
| **Negative/correction examples** | Poorly phrased, redundant, or irrelevant questions that are then corrected. |
| **Human-review requirements** | All examples must be human-reviewed for question quality. |
| **Approximate initial target** | 40–60 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic (authored by the student). |

### 1.5 Functional Requirements

| Attribute | Value |
|---|---|
| **Input format** | `ProjectContext` JSON (enriched after clarification). |
| **Output format** | Array of functional requirement objects (id, category, title, statement, rationale, priority, acceptance_criteria, source_references, confidence). |
| **Minimum quality criteria** | Requirements use "The system shall…" language; are atomic (one requirement per item); are testable; have correct IDs; no duplicates. |
| **Positive examples** | 8–15 well-structured FRs per project context. |
| **Negative/correction examples** | Compound requirements split into atomic ones; untestable requirements rewritten. |
| **Human-review requirements** | All examples must be human-reviewed. |
| **Approximate initial target** | 60–80 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic; adapted from public SRS documents (with provenance). |

### 1.6 Non-Functional Requirements

| Attribute | Value |
|---|---|
| **Input format** | `ProjectContext` JSON. |
| **Output format** | Array of NFR objects (same schema as FR but category = `non_functional`). |
| **Minimum quality criteria** | Requirements address performance, usability, reliability, scalability; are measurable. |
| **Positive examples** | 5–10 NFRs per project. |
| **Negative/correction examples** | Vague NFRs (e.g., "The system shall be fast") rewritten to be measurable. |
| **Human-review requirements** | All examples. |
| **Approximate initial target** | 40–60 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic. |

### 1.7 Security Requirements

| Attribute | Value |
|---|---|
| **Input format** | `ProjectContext` JSON + inferred categories. |
| **Output format** | Array of security requirement objects (same schema, category = `security`). |
| **Minimum quality criteria** | Requirements are cybersecurity-specific; testable; correctly prioritised; no executable attack code. |
| **Positive examples** | 8–15 SECs per project, covering authentication, authorisation, encryption, logging, etc. |
| **Negative/correction examples** | Requirements that are too vague, duplicated, or contain offensive content — corrected. |
| **Human-review requirements** | All examples. Critical review for safety. |
| **Approximate initial target** | 60–80 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic; may reference public frameworks but must not copy verbatim. |

### 1.8 Requirement Rewriting

| Attribute | Value |
|---|---|
| **Input format** | A poorly written requirement (vague, compound, untestable). |
| **Output format** | One or more well-written, atomic, testable requirements. |
| **Minimum quality criteria** | The rewritten requirement preserves the intent; is atomic; is testable; uses correct language. |
| **Positive examples** | Clear before/after pairs. |
| **Negative/correction examples** | Cases where the rewrite introduces errors, then corrected. |
| **Human-review requirements** | All examples. |
| **Approximate initial target** | 30–50 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic. |

### 1.9 Requirement Atomicity

| Attribute | Value |
|---|---|
| **Input format** | A compound requirement (e.g., "The system shall authenticate users AND encrypt data AND log all access"). |
| **Output format** | Multiple atomic requirements, each addressing one concern. |
| **Minimum quality criteria** | Each output requirement is atomic; the set covers all concerns in the original. |
| **Positive examples** | Compound → atomic splits. |
| **Negative/correction examples** | Over-splitting (splitting too finely) corrected. |
| **Human-review requirements** | All examples. |
| **Approximate initial target** | Covered within §1.8. |
| **Split strategy** | Same as §1.8. |
| **Source-provenance requirements** | Synthetic. |

### 1.10 Acceptance Criteria

| Attribute | Value |
|---|---|
| **Input format** | A requirement statement. |
| **Output format** | One or more acceptance criteria (testable conditions). |
| **Minimum quality criteria** | Criteria are specific, measurable, and directly related to the requirement. |
| **Positive examples** | Well-matched requirement → criteria pairs. |
| **Negative/correction examples** | Vague criteria (e.g., "it works correctly") rewritten to be measurable. |
| **Human-review requirements** | All examples. |
| **Approximate initial target** | 30–40 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic. |

### 1.11 Threat Modelling

| Attribute | Value |
|---|---|
| **Input format** | `ProjectContext` JSON + `system_architecture` JSON. |
| **Output format** | `ThreatModel` JSON (threats with STRIDE category, severity, mitigations, related requirements). |
| **Minimum quality criteria** | Threats are realistic; STRIDE categories are correct; mitigations are actionable; no executable attack code. |
| **Positive examples** | 3–8 threats per project with appropriate mitigations. |
| **Negative/correction examples** | Threats without mitigations corrected; irrelevant threats removed. |
| **Human-review requirements** | All examples. Safety review for harmful content. |
| **Approximate initial target** | 40–60 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic. |

### 1.12 Invalid-Output Correction

| Attribute | Value |
|---|---|
| **Input format** | A prompt + the model's invalid output + the validation error message. |
| **Output format** | The corrected valid output. |
| **Minimum quality criteria** | The corrected output fixes the specific error while preserving the content intent. |
| **Positive examples** | JSON syntax errors fixed; missing required fields added; invalid enum values corrected. |
| **Negative/correction examples** | Over-corrections that change content unnecessarily. |
| **Human-review requirements** | All examples. |
| **Approximate initial target** | 30–50 examples. |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic (generated by running the base model and collecting failures). |

### 1.13 SRS-Section Generation (End-to-End)

| Attribute | Value |
|---|---|
| **Input format** | Full `ProjectContext` + retrieved chunks (simulated). |
| **Output format** | Complete SRS section JSON. |
| **Minimum quality criteria** | Valid schema; comprehensive coverage; testable requirements; proper IDs; correct citations to provided chunks. |
| **Positive examples** | Full section outputs for each of the 6 SRS sections. |
| **Negative/correction examples** | Incomplete sections corrected. |
| **Human-review requirements** | All examples. |
| **Approximate initial target** | 30–40 examples (spanning different project types). |
| **Split strategy** | 80/10/10. |
| **Source-provenance requirements** | Synthetic. |

---

## 2. Data Provenance Categories

| Category | Description | Examples |
|---|---|---|
| **Publicly sourced** | Adapted from publicly available SRS documents, academic papers, or open project descriptions. Source documented. | Public university capstone SRS documents; open-source project README descriptions. |
| **Synthetically generated** | Written by the student specifically for this project. Inspired by real-world scenarios but not copied. | Custom project descriptions, custom requirements. |
| **Human-corrected** | Generated by the base model, then manually corrected by the student. Documents what the model got wrong and what the correct answer is. | Corrected SRS outputs, corrected clarification questions. |
| **Evaluation-only** | Reserved exclusively for the held-out test set. Never used in training. | 10% of each category. |

---

## 3. Dataset Documentation (Dataset Card)

Each dataset version will include a dataset card containing:

| Field | Description |
|---|---|
| Name | `cybersrs-training-v{N}` |
| Version | Semantic version |
| Size | Total examples, per-category counts |
| Format | JSONL |
| Split | Train/Val/Test counts |
| Categories covered | Which of the 13 categories are included |
| Project types covered | Which of CAT-01–CAT-08 |
| Provenance | Breakdown by publicly sourced / synthetic / human-corrected |
| Schema validation | All examples validated against Pydantic schemas |
| Known limitations | Size, category imbalance, quality gaps |
| Licence | Licence of source materials |
| Created by | Student name |
| Date | Creation date |

---

## 4. Category Coverage Requirements

The dataset must cover at least 6 of the 8 supported project categories:

| Category | Required in dataset? |
|---|---|
| CAT-01 Network security | Yes |
| CAT-02 Firewalls and access control | Yes (demo project 1) |
| CAT-03 Intrusion detection | Yes |
| CAT-04 Identity and access management | Yes (demo project 3) |
| CAT-05 Secure web applications and APIs | Yes (demo project 2) |
| CAT-06 VPN and remote access | Should |
| CAT-07 Security logging and alerting | Should |
| CAT-08 Zero trust / network segmentation | Should |
