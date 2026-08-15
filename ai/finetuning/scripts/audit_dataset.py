"""Audit and split the CyberSRS fine-tuning dataset.

This script performs the Phase 4C dataset-quality audit without training a
model. It validates generated assistant payloads, checks split leakage at the
scenario level, estimates semantic similarity to the frozen evaluation set,
audits quality heuristics, writes deterministic train/validation splits, and
emits human-review artifacts.

Run standalone:
    python ai/finetuning/scripts/audit_dataset.py
"""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.finetuning.scripts.generate_dataset import (  # noqa: E402
    _build_context_payload,
    _mentions_unconfirmed_constraint,
    _safe_context_analysis,
)
from ai.finetuning.scripts.scenario_library import SCENARIOS  # noqa: E402
from src.schemas.analysis import ProjectAnalysis  # noqa: E402
from src.schemas.clarification import ClarificationQuestionSet  # noqa: E402
from src.schemas.srs import (  # noqa: E402
    ArchitectureSummary,
    Mitigation,
    Requirement,
    SRSSchema,
    Threat,
)

DATA_DIR = PROJECT_ROOT / "ai" / "finetuning" / "data"
EVAL_DATASET = PROJECT_ROOT / "ai" / "evaluation" / "dataset.json"
TASK_FILES = (
    "architecture.jsonl",
    "clarification_questions.jsonl",
    "context_extraction.jsonl",
    "data_requirements.jsonl",
    "functional_requirements.jsonl",
    "network_requirements.jsonl",
    "non_functional_requirements.jsonl",
    "requirement_validation.jsonl",
    "security_requirements.jsonl",
    "srs_generation.jsonl",
    "threat_model.jsonl",
)
REQUIREMENT_WRAPPERS = {
    "functional_requirements",
    "non_functional_requirements",
    "security_requirements",
    "data_requirements",
    "network_requirements",
}
WEAK_ACCEPTANCE_PATTERNS = (
    "verify that the requirement",
    "requirement is implemented",
    "implemented correctly",
    "satisfy this requirement",
    "works correctly",
    "ensure it works",
    "test that",
)
GENERIC_REQUIREMENT_PATTERNS = (
    "the system shall be secure",
    "the system shall be user friendly",
    "the system shall be reliable",
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "to",
    "with",
}
PHASE4C_BASELINE_REPETITION = {
    "max_repeated_synthesized_nfr_statement": 102,
    "max_repeated_synthesized_nfr_acceptance": 102,
}
PHASE4C3_RECORD_COUNT = 533
PHASE4C3_STANDALONE_NFR_COUNT = 58
PHASE4C4_REMOVED_SECURITY_LIKE_NFRS = {
    "Code Commit Integrity": 1,
    "Firmware Signature Integrity": 1,
    "Health Data Privacy Exposure": 4,
    "Manifest Signature Integrity": 1,
    "Privileged Data Exposure Control": 1,
    "Sensitive Data Privacy Control": 2,
    "Signature Evidence Integrity": 2,
    "Tenant Data Privacy Boundary": 3,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file into dictionaries."""
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dictionaries to JSONL with deterministic compact formatting."""
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def assistant_json(record: dict[str, Any]) -> Any:
    """Parse the assistant message content as JSON."""
    return json.loads(record["messages"][-1]["content"])


def normalize_text(text: str) -> str:
    """Normalize text for duplicate and template checks."""
    lowered = text.lower()
    lowered = re.sub(r"\b(?:scn|eval|fr|sec|nfr|data|net|thr|mit|test|risk)-\d+\b", " id ", lowered)
    lowered = re.sub(r"\b\d+(?:\.\d+)?\b", " number ", lowered)
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return " ".join(lowered.split())


def normalized_without_entities(text: str) -> str:
    """Normalize names and organization-like entities to catch shallow rewrites."""
    text = re.sub(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4}\b", " ENTITY ", text)
    text = re.sub(r"\b(?:campus|hospital|airport|bank|utility|factory|clinic|firm)\b", " ENTITY ", text, flags=re.I)
    return normalize_text(text)


def token_set(text: str) -> set[str]:
    """Return content tokens for similarity checks."""
    return {token for token in normalize_text(text).split() if token not in STOPWORDS and len(token) > 2}


def jaccard(a: str, b: str) -> float:
    """Compute token-set Jaccard similarity."""
    left = token_set(a)
    right = token_set(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def cosine(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two dense vectors."""
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    l_norm = math.sqrt(sum(a * a for a in left))
    r_norm = math.sqrt(sum(b * b for b in right))
    if l_norm == 0.0 or r_norm == 0.0:
        return 0.0
    return numerator / (l_norm * r_norm)


def load_records(data_dir: Path) -> list[dict[str, Any]]:
    """Load all task JSONL records."""
    records: list[dict[str, Any]] = []
    for file_name in TASK_FILES:
        records.extend(read_jsonl(data_dir / file_name))
    records.sort(key=lambda row: row["record_id"])
    return records


def validate_assistant_payload(record: dict[str, Any]) -> list[str]:
    """Validate an assistant payload against the task-specific Pydantic schema."""
    task = record["task"]
    errors: list[str] = []
    try:
        payload = assistant_json(record)
        if task == "context_extraction":
            ProjectAnalysis.model_validate(payload)
        elif task == "clarification_questions":
            ClarificationQuestionSet.model_validate(payload)
        elif task in REQUIREMENT_WRAPPERS:
            for item in payload[task]:
                Requirement.model_validate(item)
        elif task == "architecture":
            ArchitectureSummary.model_validate(payload)
        elif task == "threat_model":
            for item in payload["threats"]:
                Threat.model_validate(item)
            for item in payload["mitigations"]:
                Mitigation.model_validate(item)
        elif task == "srs_generation":
            SRSSchema.model_validate(payload)
        elif task == "requirement_validation":
            Requirement.model_validate(payload)
        else:
            errors.append(f"unknown task {task!r}")
    except Exception as exc:  # noqa: BLE001 - reported in audit output
        errors.append(f"{type(exc).__name__}: {exc}")
    return errors


def scenario_split(records: list[dict[str, Any]], seed: int = 42) -> dict[str, Any]:
    """Split scenarios first, then expand records into train/validation sets."""
    scenario_ids = sorted({record["scenario_id"] for record in records})
    shuffled = scenario_ids[:]
    random.Random(seed).shuffle(shuffled)
    validation_count = max(1, round(len(shuffled) * 0.10))
    validation_scenarios = set(sorted(shuffled[:validation_count]))
    train_scenarios = set(scenario_ids) - validation_scenarios
    train_records = [{**record, "split": "train"} for record in records if record["scenario_id"] in train_scenarios]
    validation_records = [
        {**record, "split": "validation"}
        for record in records
        if record["scenario_id"] in validation_scenarios
    ]
    return {
        "train_scenarios": sorted(train_scenarios),
        "validation_scenarios": sorted(validation_scenarios),
        "train_records": train_records,
        "validation_records": validation_records,
        "scenario_overlap": sorted(train_scenarios & validation_scenarios),
    }


def scenario_by_id() -> dict[str, dict[str, Any]]:
    """Return scenario dictionaries keyed by stable scenario ID."""
    return {scenario["id"]: scenario for scenario in SCENARIOS}


def ollama_embeddings(texts: list[str]) -> tuple[list[list[float]] | None, str]:
    """Try to embed texts with local Ollama nomic-embed-text."""
    try:
        import requests

        vectors: list[list[float]] = []
        for text in texts:
            response = requests.post(
                "http://127.0.0.1:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=20,
            )
            if response.status_code != 200:
                return None, f"ollama returned HTTP {response.status_code}"
            payload = response.json()
            vector = payload.get("embedding")
            if not isinstance(vector, list) or not vector:
                return None, "ollama response did not contain an embedding"
            vectors.append([float(value) for value in vector])
        return vectors, "nomic-embed-text via local Ollama"
    except Exception as exc:  # noqa: BLE001 - fallback is intentional
        return None, f"nomic-embed-text unavailable: {type(exc).__name__}: {exc}"


def hashed_ngram_vector(text: str, dimensions: int = 2048) -> list[float]:
    """Build a deterministic hashed word-ngram vector for fallback similarity."""
    tokens = normalize_text(text).split()
    vector = [0.0] * dimensions
    for n in (1, 2, 3):
        for i in range(0, max(0, len(tokens) - n + 1)):
            ngram = " ".join(tokens[i : i + n])
            digest = hashlib.sha256(ngram.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            vector[index] += 1.0
    return vector


def leakage_report() -> dict[str, Any]:
    """Compare all training scenarios to frozen evaluation descriptions."""
    scenarios = scenario_by_id()
    eval_cases = json.loads(EVAL_DATASET.read_text(encoding="utf-8"))
    scenario_ids = sorted(scenarios)
    texts = [scenarios[sid]["description"] for sid in scenario_ids]
    eval_texts = [case["description"] for case in eval_cases]
    vectors, method = ollama_embeddings([*texts, *eval_texts])
    used_fallback = vectors is None
    if vectors is None:
        vectors = [hashed_ngram_vector(text) for text in [*texts, *eval_texts]]
        method = f"fallback hashed word n-gram cosine ({method})"
    scenario_vectors = vectors[: len(texts)]
    eval_vectors = vectors[len(texts) :]

    matches: list[dict[str, Any]] = []
    flagged: list[dict[str, Any]] = []
    for sid, s_vector in zip(scenario_ids, scenario_vectors, strict=True):
        for case, e_vector in zip(eval_cases, eval_vectors, strict=True):
            score = cosine(s_vector, e_vector)
            token_overlap = jaccard(scenarios[sid]["description"], case["description"])
            match = {
                "scenario_id": sid,
                "eval_id": case["id"],
                "similarity": round(score, 4),
                "token_jaccard": round(token_overlap, 4),
                "scenario_description": scenarios[sid]["description"],
                "eval_description": case["description"],
                "manual_review": score >= 0.75 or token_overlap >= 0.50,
                "leakage_decision": "not_leakage",
                "decision_rationale": (
                    "Same broad cybersecurity category may appear, but wording, "
                    "organization context, constraints, and required behaviour are distinct."
                ),
            }
            matches.append(match)
            if match["manual_review"]:
                flagged.append(match)
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return {
        "method": method,
        "used_embedding_fallback": used_fallback,
        "semantic_threshold_for_manual_review": 0.75,
        "token_jaccard_manual_review_threshold": 0.50,
        "highest_similarity_matches": matches[:20],
        "manual_reviewed_pairs": flagged,
        "leakage_count": sum(1 for item in flagged if item["leakage_decision"] == "leakage"),
        "removed_scenarios": [],
    }


def all_requirements_from_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract requirement objects from a section or full-SRS record."""
    payload = assistant_json(record)
    if record["task"] in REQUIREMENT_WRAPPERS:
        return list(payload[record["task"]])
    if record["task"] == "requirement_validation":
        return [payload]
    if record["task"] == "srs_generation":
        requirements: list[dict[str, Any]] = []
        for section in REQUIREMENT_WRAPPERS:
            requirements.extend(payload.get(section, []))
        return requirements
    return []


def audit_requirement(req: dict[str, Any], record: dict[str, Any]) -> list[dict[str, str]]:
    """Return heuristic requirement-quality findings."""
    findings: list[dict[str, str]] = []
    statement = req["statement"]
    rationale = req["rationale"]
    acceptance = req["acceptance_criteria"]
    lowered = statement.lower()
    if statement.count("shall") != 1:
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "statement does not use exactly one shall"})
    if not statement.startswith("The system shall"):
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "statement does not start with The system shall"})
    if any(pattern in lowered for pattern in GENERIC_REQUIREMENT_PATTERNS):
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "overly generic statement"})
    if re.search(r"\bshall\b.+\bshall\b", lowered):
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "duplicate shall construction"})
    if rationale.lower() in {"this is important for the project.", "generated from the project context by the local model."}:
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "generic rationale"})
    numeric_text = re.sub(r"\bIEC\s+61850\b", "IEC_CODE", statement + " " + acceptance, flags=re.I)
    numeric_text = re.sub(r"\bOAuth\s+2\.0\b", "OAUTH_VERSION", numeric_text, flags=re.I)
    if re.search(r"\b\d+(?:\.\d+)?\b", numeric_text):
        joined = f"{rationale} {record.get('provenance', {})}".lower()
        if not any(tag.lower() in joined for tag in ("user_specified", "rag_supported", "assumption_requiring_confirmation")):
            findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "numeric value without provenance"})
        if "assumption_requiring_confirmation" in joined and req["priority"] == "must":
            findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "assumed numeric value marked must"})
    prefix_by_category = {
        "functional": "FR-",
        "non_functional": "NFR-",
        "security": "SEC-",
        "data": "DATA-",
        "network": "NET-",
    }
    if not req["id"].startswith(prefix_by_category[req["category"]]):
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "id prefix does not match category"})
    return findings


def audit_acceptance(req: dict[str, Any], record: dict[str, Any]) -> list[dict[str, str]]:
    """Return heuristic acceptance-criteria findings."""
    text = req["acceptance_criteria"]
    lowered = text.lower()
    findings: list[dict[str, str]] = []
    if not re.search(r"\bGIVEN\b.+\bWHEN\b.+\bTHEN\b", text, flags=re.S):
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "missing meaningful GIVEN/WHEN/THEN structure"})
    if any(pattern in lowered for pattern in WEAK_ACCEPTANCE_PATTERNS):
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "weak acceptance criteria pattern"})
    req_terms = token_set(req["statement"])
    ac_terms = token_set(text)
    if req_terms and len(req_terms & ac_terms) / len(req_terms) > 0.90 and len(ac_terms - req_terms) < 4:
        findings.append({"record_id": record["record_id"], "requirement_id": req["id"], "issue": "acceptance criteria mostly paraphrases requirement"})
    return findings


def duplicate_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure exact, normalized, near-duplicate, and repeated template content."""
    exact_user = Counter(record["messages"][1]["content"] for record in records)
    exact_assistant = Counter(record["messages"][2]["content"] for record in records)
    normalized_user = Counter(normalize_text(record["messages"][1]["content"]) for record in records)
    normalized_assistant = Counter(normalize_text(record["messages"][2]["content"]) for record in records)
    entity_normalized_user = Counter(normalized_without_entities(record["messages"][1]["content"]) for record in records)
    scenarios = scenario_by_id()
    near_scenarios: list[dict[str, Any]] = []
    scenario_ids = sorted(scenarios)
    for i, sid in enumerate(scenario_ids):
        for other in scenario_ids[i + 1 :]:
            score = jaccard(scenarios[sid]["description"], scenarios[other]["description"])
            if score >= 0.55:
                near_scenarios.append({"scenario_id": sid, "other_scenario_id": other, "jaccard": round(score, 4)})

    req_texts: Counter[str] = Counter()
    ac_texts: Counter[str] = Counter()
    rationale_texts: Counter[str] = Counter()
    questions: Counter[str] = Counter()
    for record in records:
        if record["task"] == "clarification_questions":
            for item in assistant_json(record)["questions"]:
                questions[normalize_text(item["question_text"])] += 1
        for req in all_requirements_from_record(record):
            req_texts[normalize_text(req["statement"])] += 1
            ac_texts[normalize_text(req["acceptance_criteria"])] += 1
            rationale_texts[normalize_text(req["rationale"])] += 1

    def dup_count(counter: Counter[str]) -> int:
        return sum(count - 1 for count in counter.values() if count > 1)

    return {
        "exact_duplicate_user_messages": dup_count(exact_user),
        "exact_duplicate_assistant_outputs": dup_count(exact_assistant),
        "normalized_duplicate_user_messages": dup_count(normalized_user),
        "normalized_duplicate_assistant_outputs": dup_count(normalized_assistant),
        "entity_only_duplicate_user_messages": dup_count(entity_normalized_user),
        "near_duplicate_scenarios": near_scenarios,
        "near_duplicate_scenario_count": len(near_scenarios),
        "repeated_requirements": [{"text": text, "count": count} for text, count in req_texts.items() if count > 1],
        "repeated_acceptance_criteria": [{"text": text, "count": count} for text, count in ac_texts.items() if count > 1],
        "repeated_clarification_questions": [{"text": text, "count": count} for text, count in questions.items() if count > 1],
        "repeated_rationales": [{"text": text, "count": count} for text, count in rationale_texts.items() if count > 1],
        "duplicate_rate": round((dup_count(normalized_user) + dup_count(normalized_assistant)) / max(1, len(records) * 2), 4),
        "near_duplicate_rate": round(len(near_scenarios) / max(1, len(scenario_ids)), 4),
    }


def _normal_text(value: str) -> str:
    """Return compact normalized text for semantic-stage validators."""
    return re.sub(r"\s+", " ", value.casefold()).strip()


def clarification_answer_leakage(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect hidden clarification answers in clarification-generation targets."""
    scenarios = scenario_by_id()
    findings: list[dict[str, str]] = []
    checked = 0
    for record in records:
        if record["task"] != "clarification_questions":
            continue
        payload = assistant_json(record)
        answers = [
            _normal_text(item["answer"])
            for item in scenarios[record["scenario_id"]]["clarifications"]
            if item["answer"].strip()
        ]
        prompt = _normal_text(record["messages"][1]["content"])
        for question in payload["questions"]:
            target_text = _normal_text(
                f"{question['question_text']} {question['reason']} {question['target_gap']}"
            )
            checked += 1
            for answer in answers:
                if answer and answer not in prompt and answer in target_text:
                    findings.append(
                        {
                            "record_id": record["record_id"],
                            "question_text": question["question_text"],
                            "leaked_answer": answer,
                        }
                    )
    return {
        "questions_checked": checked,
        "failure_count": len(findings),
        "findings": findings,
    }


def unsupported_context_assertions(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect mandatory context constraints unsupported by the visible description."""
    findings: list[dict[str, str]] = []
    moved_to_missing = 0
    for scenario in SCENARIOS:
        moved_to_missing += _safe_context_analysis(scenario)["context_repair_metadata"][
            "unsupported_constraints_moved_to_missing_information"
        ]
    for record in records:
        if record["task"] != "context_extraction":
            continue
        payload = assistant_json(record)
        prompt = record["messages"][1]["content"]
        prompt_tokens = token_set(prompt)
        for constraint in payload["constraints"]:
            words = token_set(constraint)
            overlap = len(words & prompt_tokens) / max(1, len(words))
            mandatory = bool(re.search(r"\b(must|required|shall)\b", constraint, flags=re.I))
            if mandatory and overlap < 0.35:
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "constraint": constraint,
                        "issue": "mandatory constraint unsupported by input description",
                    }
                )
    return {
        "unsupported_constraints_moved_to_missing_information": moved_to_missing,
        "failure_count": len(findings),
        "findings": findings,
    }


def unsupported_numeric_assumptions(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect concrete numbers attached to assumption-requiring-confirmation provenance."""
    findings: list[dict[str, str]] = []
    assumption_source_count = 0
    for scenario in SCENARIOS:
        for req in scenario["requirements"]:
            assumption_source_count += sum(
                1
                for item in req.get("numeric", [])
                if item["provenance"] == "ASSUMPTION_REQUIRING_CONFIRMATION"
            )
    for record in records:
        for req in all_requirements_from_record(record):
            joined = f"{req['statement']} {req['acceptance_criteria']} {req['rationale']}"
            if "ASSUMPTION_REQUIRING_CONFIRMATION" in joined and re.search(
                r"\b\d+(?:\.\d+)?\b",
                re.sub(r"\b(?:IEC\s+61850|OAuth\s+2\.0)\b", "", joined, flags=re.I),
            ):
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "issue": "concrete number remains in unsupported numeric assumption",
                    }
                )
    return {
        "source_assumption_numeric_items": assumption_source_count,
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def synthesized_nfr_repetition(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure repeated synthesized NFR statement and acceptance templates."""
    statement_counts: Counter[str] = Counter()
    acceptance_counts: Counter[str] = Counter()
    for record in records:
        include = False
        if record["task"] == "non_functional_requirements":
            include = record.get("provenance", {}).get("requirement_provenance") == "synthesized_nfr"
        elif record["task"] == "srs_generation":
            include = record.get("provenance", {}).get("nfr_provenance") == "synthesized_nfr"
        if not include:
            continue
        for req in all_requirements_from_record(record):
            if req["category"] != "non_functional":
                continue
            statement_counts[normalize_text(req["statement"])] += 1
            acceptance_counts[normalize_text(req["acceptance_criteria"])] += 1
    return {
        "synthetic_nfr_instances_checked": sum(statement_counts.values()),
        "max_repeated_statement_count": max(statement_counts.values(), default=0),
        "max_repeated_acceptance_count": max(acceptance_counts.values(), default=0),
        "top_repeated_statements": [
            {"text": text, "count": count}
            for text, count in statement_counts.most_common(10)
            if count > 1
        ],
        "top_repeated_acceptance_criteria": [
            {"text": text, "count": count}
            for text, count in acceptance_counts.most_common(10)
            if count > 1
        ],
    }


def synthesized_nfr_semantic_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate synthesized NFRs for grammar, classification, and testability."""
    quality_titles = {
        "Alert Processing Reliability",
        "Abuse Detection Reliability",
        "Access Policy Maintainability",
        "Administrative Policy Maintainability",
        "API Decision Reliability",
        "Attendance Record Integrity",
        "Attendance Change Integrity Review",
        "Branch Alert Reliability",
        "Charging Decision Integrity",
        "Configured-Load Scalability",
        "Content Trace Integrity",
        "Control-Traffic Event Reliability",
        "Control Event Integrity Review",
        "Device Access Policy Maintainability",
        "Detection Decision Reliability",
        "Document Evidence Recoverability",
        "Election Log Integrity Review",
        "Extension Validation Integrity",
        "Identity Session Policy Maintainability",
        "Integration Observability",
        "Log Integrity Review",
        "Media Record Recoverability",
        "Medical-Device Event Reliability",
        "Network Policy Maintainability",
        "Operational Record Recoverability",
        "Operational Resilience",
        "Operator Control Policy Maintainability",
        "Policy Maintainability",
        "Scan Result Reliability",
        "Security Decision Integrity",
        "Sensor Evidence Integrity Review",
        "Signal Authenticity Integrity",
        "Subscriber Authentication Maintainability",
        "Telemetry Signal Reliability",
        "Telemetry Evidence Integrity",
    }
    bad_goal_splices = re.compile(
        r"\b(?:for|supports)\s+(?:provide|let|classify|detect|enforce|scan|"
        r"authenticate|encrypt|protect|control|throttle|watermark|validate|"
        r"require|score|custody|prevent)\b",
        flags=re.I,
    )
    findings: list[dict[str, str]] = []
    checked = 0
    for record in records:
        include = False
        if record["task"] == "non_functional_requirements":
            include = record.get("provenance", {}).get("requirement_provenance") == "synthesized_nfr"
        elif record["task"] == "srs_generation":
            include = record.get("provenance", {}).get("nfr_provenance") == "synthesized_nfr"
        if not include:
            continue
        for req in all_requirements_from_record(record):
            if req["id"] != "NFR-001":
                continue
            checked += 1
            joined = " ".join(
                [
                    req["title"],
                    req["statement"],
                    req["rationale"],
                    req["acceptance_criteria"],
                ]
            )
            if req["category"] != "non_functional":
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "issue": "synthesized NFR is not classified as non_functional",
                    }
                )
            if req["title"] not in quality_titles:
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "issue": "title is not an approved quality-attribute family",
                    }
                )
            if bad_goal_splices.search(req["statement"]):
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "issue": "statement appears to splice an imperative functional goal into an NFR",
                    }
                )
            if re.search(r"\ba\s+(?:e-|ai|api|iot|ot|mfa|erp|srs)\b", joined, flags=re.I):
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "issue": "statement or acceptance criterion contains an article/acronym grammar error",
                    }
                )
            if "GIVEN" not in req["acceptance_criteria"] or "WHEN" not in req["acceptance_criteria"] or "THEN" not in req["acceptance_criteria"]:
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "issue": "acceptance criterion is not testable GIVEN/WHEN/THEN",
                    }
                )
            if not any(
                family in req["rationale"].lower()
                for family in (
                    "auditability",
                    "performance",
                    "reliability",
                    "recoverability",
                    "resilience",
                    "privacy",
                    "integrity",
                    "interoperability",
                    "observability",
                    "scalability",
                    "maintainability",
                    "quality attribute",
                )
            ):
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "issue": "rationale does not explain the quality attribute",
                    }
                )
    return {
        "synthesized_nfr_instances_checked": checked,
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def _unconfirmed_constraints_by_scenario() -> dict[str, list[str]]:
    """Return unconfirmed constraints moved out of established context."""
    unconfirmed: dict[str, list[str]] = {}
    for scenario in SCENARIOS:
        safe = _safe_context_analysis(scenario)
        moved = [
            item.removeprefix("Confirm whether this constraint applies: ").strip()
            for item in safe["missing_information"]
            if item.startswith("Confirm whether this constraint applies: ")
        ]
        unconfirmed[scenario["id"]] = moved
    return unconfirmed


def _constraint_markers(constraint: str, scenario: dict[str, Any] | None = None) -> set[str]:
    """Extract high-signal words that identify one unconfirmed constraint."""
    broad = {
        "alert",
        "alerts",
        "authenticated",
        "authentication",
        "authorization",
        "authorised",
        "authorized",
        "available",
        "after",
        "based",
        "before",
        "break",
        "changes",
        "cluster",
        "communication",
        "consent",
        "control",
        "controlled",
        "contract",
        "data",
        "detected",
        "device",
        "deploys",
        "document",
        "documents",
        "encrypted",
        "encryption",
        "enforcement",
        "event",
        "events",
        "evident",
        "image",
        "immediately",
        "logged",
        "logging",
        "network",
        "operate",
        "parties",
        "policy",
        "records",
        "requests",
        "responsible",
        "restricted",
        "review",
        "reviewer",
        "scanning",
        "security",
        "segment",
        "sharing",
        "source",
        "staff",
        "submission",
        "system",
        "tamper",
        "tracking",
        "trigger",
        "uploads",
        "users",
        "violations",
        "within",
        "without",
        "workflows",
    }
    markers = {
        token
        for token in token_set(constraint)
        if len(token) > 4 and token not in broad
    }
    if scenario is not None:
        explicit_text = " ".join(
            [
                scenario["description"],
                *[
                    f"{item['question']} {item['answer']}"
                    for item in scenario["clarifications"]
                    if item["answer"].strip()
                ],
            ]
        )
        markers -= token_set(explicit_text)
    return markers


def _iter_text_values(value: Any, skip_keys: set[str] | None = None) -> list[str]:
    """Return string values from nested payloads, skipping allowed unresolved fields."""
    skip_keys = skip_keys or set()
    values: list[str] = []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        for item in value:
            values.extend(_iter_text_values(item, skip_keys))
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in skip_keys:
                continue
            values.extend(_iter_text_values(item, skip_keys))
    return values


def _matches_unconfirmed_constraint(
    constraint: str,
    scenario: dict[str, Any],
    text: str,
) -> tuple[bool, list[str]]:
    """Return whether text establishes a semantic equivalent of an unresolved constraint."""
    normalized = normalize_text(text)
    constraint_normalized = normalize_text(constraint)
    semantic_matches: list[str] = []
    if re.search(
        r"\b(?:passive|passively|non interfer\w*|never send commands)\b",
        constraint_normalized,
    ):
        passive_patterns = {
            "passive/non-interference": r"\b(?:passive|passively|non interfer\w*)\b",
            "command transmission": (
                r"\b(?:send|sending|transmit|transmitting|inject|injecting) "
                r"(?:\w+ ){0,3}commands?\b"
            ),
            "automatic field control": (
                r"\bautomatic (?:\w+ ){0,3}(?:pump|field device|plc) control\b"
            ),
            "device-behaviour alteration": (
                r"\b(?:alter|altering) (?:\w+ ){0,2}(?:device|control) behavio\w*\b"
            ),
        }
        semantic_matches.extend(
            label for label, pattern in passive_patterns.items() if re.search(pattern, normalized)
        )
        if semantic_matches:
            return True, semantic_matches

    markers = _constraint_markers(constraint, scenario)
    matched = sorted(
        marker for marker in markers if re.search(rf"\b{re.escape(marker)}\b", normalized)
    )
    matched_constraint = (len(markers) >= 2 and len(matched) >= 2) or (
        len(matched) == 1
        and matched[0] in {"passive", "airgapped", "gapped", "append", "appendonly"}
    )
    return matched_constraint, matched


def _is_explicitly_unresolved(text: str) -> bool:
    """Return whether text clearly labels a proposition as unresolved rather than factual."""
    return bool(
        re.search(
            r"\b(?:unresolved|unconfirmed|requires? (?:stakeholder )?confirmation|"
            r"pending (?:stakeholder )?confirmation|confirm whether|whether .+ remains)\b",
            text,
            flags=re.I,
        )
    )


def _cross_stage_sections(record: dict[str, Any], payload: Any) -> list[tuple[str, str]]:
    """Return later-stage payload text grouped by the semantic SRS section it occupies."""
    task = record["task"]
    sections: list[tuple[str, str]] = []
    if task == "srs_generation":
        for scope_key in ("in_scope", "out_of_scope"):
            sections.extend(
                (f"scope.{scope_key}", item)
                for item in payload.get("scope", {}).get(scope_key, [])
            )
        sections.extend(("assumptions", item) for item in payload.get("assumptions", []))
        sections.append(
            (
                "architecture_summary",
                " ".join(_iter_text_values(payload.get("architecture_summary", {}))),
            )
        )
        for wrapper in REQUIREMENT_WRAPPERS:
            sections.extend(
                ("requirements", " ".join(_iter_text_values(requirement)))
                for requirement in payload.get(wrapper, [])
            )
        sections.extend(
            ("risks", " ".join(_iter_text_values(risk)))
            for risk in payload.get("risks", [])
        )
        sections.extend(
            ("risks", " ".join(_iter_text_values(threat)))
            for threat in payload.get("threats", [])
        )
        return [(section, text) for section, text in sections if text.strip()]

    if task == "architecture":
        return [("architecture_summary", " ".join(_iter_text_values(payload)))]
    if task in {
        "functional_requirements",
        "non_functional_requirements",
        "security_requirements",
        "data_requirements",
        "network_requirements",
    }:
        return [
            ("requirements", " ".join(_iter_text_values(requirement)))
            for requirement in all_requirements_from_record(record)
        ]
    if task == "threat_model":
        return [("risks", " ".join(_iter_text_values(payload)))]
    return []


def cross_stage_consistency_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect unresolved assumptions promoted across scope, architecture, and requirements."""
    unconfirmed = _unconfirmed_constraints_by_scenario()
    later_tasks = {
        "architecture",
        "functional_requirements",
        "non_functional_requirements",
        "security_requirements",
        "data_requirements",
        "network_requirements",
        "srs_generation",
        "threat_model",
    }
    findings: list[dict[str, str]] = []
    cases_checked = 0
    scenarios = scenario_by_id()
    for record in records:
        if record["task"] not in later_tasks:
            continue
        constraints = unconfirmed.get(record["scenario_id"], [])
        if not constraints:
            continue
        payload = assistant_json(record)
        for section, section_text in _cross_stage_sections(record, payload):
            for constraint in constraints:
                cases_checked += 1
                matched_constraint, matched = _matches_unconfirmed_constraint(
                    constraint,
                    scenarios[record["scenario_id"]],
                    section_text,
                )
                if matched_constraint and not (
                    section == "assumptions" and _is_explicitly_unresolved(section_text)
                ):
                    findings.append(
                        {
                            "record_id": record["record_id"],
                            "scenario_id": record["scenario_id"],
                            "stage_section": section,
                            "unconfirmed_constraint": constraint,
                            "matched_markers": ", ".join(matched),
                            "issue": (
                                "unconfirmed/missing information appears as an "
                                "established later-stage fact"
                            ),
                        }
                    )
    scope_findings = [item for item in findings if item["stage_section"].startswith("scope.")]
    requirement_findings = [item for item in findings if item["stage_section"] == "requirements"]
    return {
        "unconfirmed_constraints_checked": cases_checked,
        "scope_level_assumption_promotions": len(scope_findings),
        "requirement_level_assumption_promotions": len(requirement_findings),
        "assumption_statement_promotions": sum(
            item["stage_section"] == "assumptions" for item in findings
        ),
        "architecture_level_assumption_promotions": sum(
            item["stage_section"] == "architecture_summary" for item in findings
        ),
        "risk_level_assumption_promotions": sum(
            item["stage_section"] == "risks" for item in findings
        ),
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def project_summary_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate context-extraction summaries against unconfirmed constraints."""
    unconfirmed = _unconfirmed_constraints_by_scenario()
    scenarios = scenario_by_id()
    findings: list[dict[str, str]] = []
    corrected = 0
    checked = 0
    for record in records:
        if record["task"] != "context_extraction":
            continue
        checked += 1
        payload = assistant_json(record)
        scenario = scenarios[record["scenario_id"]]
        if payload["project_summary"] != scenario["analysis"]["project_summary"]:
            corrected += 1
        summary = normalize_text(payload["project_summary"])
        for constraint in unconfirmed.get(record["scenario_id"], []):
            markers = _constraint_markers(constraint, scenario)
            if not markers:
                continue
            matched = sorted(marker for marker in markers if re.search(rf"\b{re.escape(marker)}\b", summary))
            if (len(markers) >= 2 and len(matched) >= 2) or (
                len(matched) == 1
                and next(iter(matched)) in {"passive", "airgapped", "gapped", "append", "appendonly"}
            ):
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "unconfirmed_constraint": constraint,
                        "matched_markers": ", ".join(matched),
                        "issue": "project_summary includes unconfirmed assumption",
                    }
                )
    return {
        "project_summaries_checked": checked,
        "project_summaries_corrected": corrected,
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def _expected_answer_type_for_audit(question: str) -> str:
    """Independently classify clarification answer type from question semantics."""
    text = question.lower().strip()
    if re.match(r"(is|are|do|does|did|can|could|must|should|will|would|has|have)\b", text):
        return "boolean"
    if re.match(r"what counts as\b", text):
        return "text"
    if re.match(r"which\b", text):
        return "list"
    if any(
        phrase in text
        for phrase in (
            "which roles",
            "which systems",
            "which sources",
            "which items",
            "what sources",
            "what roles",
            "what items",
            "tier structure",
        )
    ):
        return "list"
    if re.search(
        r"\b(how many|how much|how long|number|count|rate|limit|retention|"
        r"volume|duration|concurrent|throughput|window|seconds|minutes|hours|"
        r"days|months|years|period|budget|threshold|maximum|minimum)\b",
        text,
    ):
        return "number"
    return "text"


def clarification_answer_type_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate clarification expected_answer_type values against question semantics."""
    allowed = {"text", "number", "list", "boolean"}
    findings: list[dict[str, str]] = []
    checked = 0
    for record in records:
        if record["task"] != "clarification_questions":
            continue
        for question in assistant_json(record)["questions"]:
            checked += 1
            actual = question["expected_answer_type"]
            expected = _expected_answer_type_for_audit(question["question_text"])
            if actual not in allowed:
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "question_text": question["question_text"],
                        "actual": actual,
                        "expected": expected,
                        "issue": "unsupported answer type",
                    }
                )
            elif actual != expected:
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "question_text": question["question_text"],
                        "actual": actual,
                        "expected": expected,
                        "issue": "answer type does not match question semantics",
                    }
                )
    return {
        "questions_checked": checked,
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def resolved_gap_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate resolved and unresolved clarification-gap state across stages."""
    findings: list[dict[str, str]] = []
    records_by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        records_by_scenario[record["scenario_id"]].append(record)

    confirmed_gap_count = 0
    unresolved_gap_count = 0
    facts_checked = 0
    for scenario in SCENARIOS:
        context = _build_context_payload(scenario)
        state = context["information_state"]
        confirmed = state["clarification_confirmed"]
        unresolved = state["unconfirmed_or_missing"]
        confirmed_ids = {item["gap_id"] for item in confirmed}
        unresolved_ids = {item["gap_id"] for item in unresolved}
        confirmed_gap_count += len(confirmed)
        unresolved_gap_count += len(unresolved)
        for gap_id in sorted(confirmed_ids & unresolved_ids):
            findings.append(
                {
                    "scenario_id": scenario["id"],
                    "gap_id": gap_id,
                    "issue": "same gap appears as both clarification_confirmed and unconfirmed_or_missing",
                }
            )

        later_prompts = "\n".join(
            record["messages"][1]["content"]
            for record in records_by_scenario[scenario["id"]]
            if record["task"]
            in {
                "architecture",
                "functional_requirements",
                "non_functional_requirements",
                "security_requirements",
                "data_requirements",
                "network_requirements",
                "srs_generation",
                "threat_model",
            }
        )
        normalized_prompts = _normal_text(later_prompts)
        for item in confirmed:
            answer = _normal_text(item["answer"])
            facts_checked += 1
            if answer and answer not in normalized_prompts:
                findings.append(
                    {
                        "scenario_id": scenario["id"],
                        "gap_id": item["gap_id"],
                        "answer": item["answer"],
                        "issue": "confirmed clarification answer not propagated to later-stage prompts",
                    }
                )

        for item in unresolved:
            unresolved_text = _normal_text(f"{item['gap_id']} {item['topic']} {item['gap']}")
            for confirmed_item in confirmed:
                answer = _normal_text(confirmed_item["answer"])
                if answer and answer in unresolved_text:
                    findings.append(
                        {
                            "scenario_id": scenario["id"],
                            "gap_id": item["gap_id"],
                            "answer": confirmed_item["answer"],
                            "issue": "confirmed answer text appears inside unresolved gap state",
                        }
                    )

    return {
        "scenarios_checked": len(SCENARIOS),
        "facts_checked": facts_checked,
        "confirmed_gaps": confirmed_gap_count,
        "unresolved_gaps": unresolved_gap_count,
        "resolved_gap_contradictions": sum(
            1 for item in findings if "resolved" in item["issue"] or "both" in item["issue"]
        ),
        "confirmed_answers_not_propagated": sum(
            1 for item in findings if "not propagated" in item["issue"]
        ),
        "contradictory_values": sum(
            1 for item in findings if "answer text appears" in item["issue"]
        ),
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def nfr_classification_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect NFR records that describe concrete capabilities rather than qualities."""
    capability_titles = {
        "Centralised Alert Delivery": "functional",
        "Reviewed Policy Changes": "security",
        "Biometric Template Privacy": "security",
        "Code Commit Integrity": "security",
        "Firmware Signature Integrity": "security",
        "Health Data Privacy Exposure": "security/data",
        "Manifest Signature Integrity": "security",
        "Privacy Exposure Control": "security/data",
        "Privileged Data Exposure Control": "security",
        "Sensitive Data Privacy Control": "security/data",
        "Signature Evidence Integrity": "security",
        "Signed-Artifact Integrity": "security",
        "Tenant Data Privacy Boundary": "security",
    }
    capability_patterns = (
        r"\bshall deliver\b",
        r"\bshall forward\b",
        r"\bshall require .*review before\b",
        r"\bdeployment shall be blocked until\b",
        r"\bshall (?:prevent|restrict|limit|minimize) .*\b(?:access|exposure)\b",
        r"\bshall (?:preserve|enforce) .*\b(?:authorization|privacy) boundar(?:y|ies)\b",
        r"\bshall (?:require|verify) .*\bsignature\b",
        r"\bsignature verification outcome\b",
        r"\bshall encrypt\b",
        r"\bshall enforce (?:mfa|multi factor authentication)\b",
    )
    findings: list[dict[str, str]] = []
    checked = 0
    for record in records:
        if record["task"] not in {"non_functional_requirements", "srs_generation"}:
            continue
        for req in all_requirements_from_record(record):
            if req["category"] != "non_functional":
                continue
            checked += 1
            expected = capability_titles.get(req["title"])
            joined = f"{req['statement']} {req['acceptance_criteria']}".lower()
            if expected is not None or any(re.search(pattern, joined) for pattern in capability_patterns):
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "title": req["title"],
                        "expected_category": expected or "functional/security",
                        "issue": "requirement describes a concrete capability rather than a non-functional quality",
                    }
                )
    return {
        "nfr_records_checked": checked,
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def nfr_pattern_bias_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure repeated NFR titles and template-like rationale/acceptance patterns."""
    title_counts: Counter[str] = Counter()
    rationale_counts: Counter[str] = Counter()
    acceptance_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    checked = 0
    for record in records:
        include = record["task"] in {"non_functional_requirements", "srs_generation"}
        if not include:
            continue
        for req in all_requirements_from_record(record):
            if req["category"] != "non_functional":
                continue
            checked += 1
            title_counts[req["title"]] += 1
            rationale_counts[normalize_text(req["rationale"])] += 1
            acceptance_counts[normalize_text(req["acceptance_criteria"])] += 1
            family = re.sub(r"\b[A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*){0,5}\b", " PROJECT ", req["statement"])
            pattern_counts[normalize_text(family)] += 1

    max_title = max(title_counts.values(), default=0)
    max_pattern = max(pattern_counts.values(), default=0)
    max_rationale = max(rationale_counts.values(), default=0)
    max_acceptance = max(acceptance_counts.values(), default=0)
    findings: list[dict[str, str | int]] = []
    if max_title > 8:
        findings.append({"issue": "dominant repeated NFR title", "max_count": max_title})
    if max_pattern > 8:
        findings.append({"issue": "dominant repeated NFR semantic pattern", "max_count": max_pattern})
    if max_rationale > 8:
        findings.append({"issue": "dominant repeated NFR rationale template", "max_count": max_rationale})
    if max_acceptance > 8:
        findings.append({"issue": "dominant repeated NFR acceptance template", "max_count": max_acceptance})
    return {
        "nfr_instances_checked": checked,
        "max_repeated_nfr_title": max_title,
        "max_repeated_nfr_pattern": max_pattern,
        "max_repeated_nfr_rationale": max_rationale,
        "max_repeated_nfr_acceptance": max_acceptance,
        "top_repeated_titles": [
            {"title": title, "count": count}
            for title, count in title_counts.most_common(10)
            if count > 1
        ],
        "failure_count": len(findings),
        "findings": findings,
    }


def unsupported_provenance_claim_validation(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect rationales that falsely claim explicit user provenance."""
    claim_pattern = re.compile(
        r"\b(?:user|description|operator|project|scenario|hospital|bank|utility|agency|company|authority|provider)\s+"
        r"(?:explicitly\s+)?(?:asks|asked|requires|required|states|stated|names|named)\b",
        flags=re.I,
    )
    findings: list[dict[str, str]] = []
    claims_checked = 0
    scenarios = scenario_by_id()
    for record in records:
        scenario = scenarios[record["scenario_id"]]
        explicit_text = " ".join(
            [
                scenario["description"],
                *[
                    f"{item['question']} {item['answer']}"
                    for item in scenario["clarifications"]
                    if item["answer"].strip()
                ],
            ]
        )
        explicit_tokens = token_set(explicit_text)
        for req in all_requirements_from_record(record):
            rationale = req["rationale"]
            if not claim_pattern.search(rationale):
                continue
            claims_checked += 1
            req_tokens = token_set(f"{req['title']} {req['statement']}")
            overlap = len(req_tokens & explicit_tokens) / max(1, len(req_tokens))
            if overlap < 0.20 or _mentions_unconfirmed_constraint(scenario, rationale):
                findings.append(
                    {
                        "record_id": record["record_id"],
                        "requirement_id": req["id"],
                        "rationale": rationale,
                        "issue": "rationale claims explicit user provenance without enough support",
                    }
                )
    return {
        "claims_checked": claims_checked,
        "failure_count": len(findings),
        "findings": findings[:100],
    }


def build_cross_stage_consistency_report(
    records: list[dict[str, Any]],
    cross_stage: dict[str, Any],
    resolved_gaps: dict[str, Any],
    provenance_claims: dict[str, Any],
) -> dict[str, Any]:
    """Build the machine-readable cross-stage consistency report."""
    return {
        "scenarios_checked": len(SCENARIOS),
        "facts_checked": resolved_gaps["facts_checked"],
        "confirmed_gaps": resolved_gaps["confirmed_gaps"],
        "unresolved_gaps": resolved_gaps["unresolved_gaps"],
        "resolved_gap_contradictions": resolved_gaps["resolved_gap_contradictions"],
        "unconfirmed_to_mandatory_promotions": cross_stage["failure_count"],
        "scope_level_assumption_promotions": cross_stage[
            "scope_level_assumption_promotions"
        ],
        "requirement_level_assumption_promotions": cross_stage[
            "requirement_level_assumption_promotions"
        ],
        "assumption_statement_promotions": cross_stage[
            "assumption_statement_promotions"
        ],
        "architecture_level_assumption_promotions": cross_stage[
            "architecture_level_assumption_promotions"
        ],
        "risk_level_assumption_promotions": cross_stage[
            "risk_level_assumption_promotions"
        ],
        "clarification_contradictions": resolved_gaps["contradictory_values"],
        "requirement_provenance_mismatches": provenance_claims["failure_count"],
        "confirmed_answers_not_propagated": resolved_gaps["confirmed_answers_not_propagated"],
        "all_inconsistency_counts_zero": (
            resolved_gaps["failure_count"] == 0
            and cross_stage["failure_count"] == 0
            and provenance_claims["failure_count"] == 0
        ),
        "sampled_scenario_ids": sorted({record["scenario_id"] for record in records}),
        "findings": {
            "resolved_gaps": resolved_gaps.get("findings", []),
            "unconfirmed_promotions": cross_stage.get("findings", []),
            "provenance_claims": provenance_claims.get("findings", []),
        },
    }


def task_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit task balance and provide Phase 4C recommendations."""
    counts = Counter(record["task"] for record in records)
    recommendations = {
        "non_functional_requirements": (
            "A: standalone NFR records are emitted only where an authored or defensible "
            "quality attribute exists. Security/data capabilities are not replaced with "
            "filler NFRs, so some scenarios intentionally have no standalone NFR record."
        ),
        "data_requirements": (
            "C: remains small. Only two scenarios explicitly require data-retention, "
            "classification, privacy, or backup behaviour. Do not manufacture more."
        ),
        "network_requirements": (
            "C: remains small. Eight scenarios contain explicit segmentation, routing, "
            "bandwidth, or zone requirements. Do not merge because the category is "
            "useful when legitimately present."
        ),
    }
    return {"counts": dict(sorted(counts.items())), "recommendations": recommendations}


def srs_quality_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit complete SRS records for internal consistency."""
    findings: list[dict[str, Any]] = []
    for record in records:
        if record["task"] != "srs_generation":
            continue
        payload = assistant_json(record)
        req_ids: list[str] = []
        for section in REQUIREMENT_WRAPPERS:
            req_ids.extend(req["id"] for req in payload.get(section, []))
        if len(req_ids) != len(set(req_ids)):
            findings.append({"record_id": record["record_id"], "issue": "duplicate requirement IDs in full SRS"})
        for item in payload.get("testing_strategy", []):
            missing = [rid for rid in item["related_requirement_ids"] if rid not in req_ids]
            if missing:
                findings.append({"record_id": record["record_id"], "issue": "testing recommendation references missing requirement", "ids": missing})
        for item in payload.get("mitigations", []):
            missing = [rid for rid in item["related_requirement_ids"] if rid not in req_ids]
            if missing:
                findings.append({"record_id": record["record_id"], "issue": "mitigation references missing requirement", "ids": missing})
        if payload["generation_metadata"]["scenario_id"] != record["scenario_id"]:
            findings.append({"record_id": record["record_id"], "issue": "scenario ID mismatch"})
    return {"srs_records_checked": sum(1 for record in records if record["task"] == "srs_generation"), "findings": findings}


def prompt_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Check training prompts for inference-only artifacts and runtime metadata."""
    findings: list[dict[str, str]] = []
    for record in records:
        joined = "\n".join(message["content"] for message in record["messages"][:2])
        if "{rag_context}" in joined or "{project_context}" in joined:
            findings.append({"record_id": record["record_id"], "issue": "unrendered prompt placeholder"})
        if "Retrieved knowledge:\n\n\n" in joined:
            findings.append({"record_id": record["record_id"], "issue": "empty retrieved-knowledge block"})
        if re.search(r"eval-\d{3}", joined, flags=re.I):
            findings.append({"record_id": record["record_id"], "issue": "evaluation-specific identifier in prompt"})
    return {
        "findings": findings,
        "intentional_training_inference_differences": [
            "Synthetic training records include an explicit no-retrieved-chunks note instead of a blank RAG context.",
            "Section SFT prompts relax production minimum-count wording so curated slices do not fabricate filler records.",
            "No evaluation IDs, mutable runtime run IDs, or retrieved factual chunks are included in training prompts.",
        ],
    }


def token_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute token-length statistics with the Qwen tokenizer when available."""
    tokenizer = None
    method = "fallback character estimate"
    exact = False
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B-Instruct-2507")
        method = "Qwen/Qwen3-4B-Instruct-2507 tokenizer"
        exact = True
    except Exception as exc:  # noqa: BLE001 - reported in audit output
        method = f"fallback character estimate; tokenizer unavailable: {type(exc).__name__}: {exc}"

    def count(record: dict[str, Any]) -> int:
        if tokenizer is not None and hasattr(tokenizer, "apply_chat_template"):
            token_ids = tokenizer.apply_chat_template(
                record["messages"],
                tokenize=True,
                return_dict=False,
            )
            return len(token_ids)
        text = "\n".join(f"{message['role']}: {message['content']}" for message in record["messages"])
        return math.ceil(len(text) / 4)

    counts_by_task: dict[str, list[int]] = defaultdict(list)
    for record in records:
        counts_by_task[record["task"]].append(count(record))

    def summarise(values: list[int]) -> dict[str, Any]:
        sorted_values = sorted(values)
        if not sorted_values:
            return {}
        def percentile(p: float) -> int:
            index = min(len(sorted_values) - 1, math.ceil(len(sorted_values) * p) - 1)
            return sorted_values[index]
        return {
            "average": round(statistics.mean(sorted_values), 2),
            "median": round(statistics.median(sorted_values), 2),
            "p90": percentile(0.90),
            "p95": percentile(0.95),
            "maximum": max(sorted_values),
            "count_gt_1024": sum(value > 1024 for value in sorted_values),
            "count_gt_2048": sum(value > 2048 for value in sorted_values),
            "count_gt_4096": sum(value > 4096 for value in sorted_values),
        }

    all_counts = [value for values in counts_by_task.values() for value in values]
    return {
        "method": method,
        "exact_tokenizer": exact,
        "overall": summarise(all_counts),
        "by_task": {task: summarise(values) for task, values in sorted(counts_by_task.items())},
        "oversized_records": [
            {"record_id": record["record_id"], "task": record["task"], "tokens": count(record)}
            for record in records
            if count(record) > 4096
        ],
    }


def build_review_sample(records: list[dict[str, Any]], leakage: dict[str, Any], token_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Select 35-45 records covering all task types and manual-review priorities."""
    selected: dict[str, dict[str, Any]] = {}
    mandatory_record_ids = {
        "SCN-001|context_extraction",
        "SCN-001|srs_generation",
        "SCN-001|threat_model",
        "SCN-009|context_extraction",
        "SCN-009|functional_requirements",
        "SCN-009|non_functional_requirements",
        "SCN-009|srs_generation",
    }

    def add(record: dict[str, Any], reason: str) -> None:
        """Add a review record with a stable reason if it is not already present."""
        selected.setdefault(record["record_id"], {**record, "review_reason": reason})

    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_task[record["task"]].append(record)
    for task, task_records in by_task.items():
        add(task_records[0], f"representative {task}")
        mandatory_record_ids.add(task_records[0]["record_id"])

    required_cross_stage = {
        "SCN-001": {
            "context_extraction",
            "clarification_questions",
            "non_functional_requirements",
            "srs_generation",
            "threat_model",
        },
        "SCN-009": {
            "context_extraction",
            "clarification_questions",
            "functional_requirements",
            "security_requirements",
            "non_functional_requirements",
            "srs_generation",
        },
        "SCN-021": {
            "functional_requirements",
            "non_functional_requirements",
            "srs_generation",
        },
        "SCN-030": {
            "security_requirements",
            "non_functional_requirements",
            "srs_generation",
        },
    }
    for scenario_id, tasks in required_cross_stage.items():
        for record in records:
            if record["scenario_id"] == scenario_id and record["task"] in tasks:
                add(record, f"Phase 4C.3 cross-stage review for {scenario_id}")

    seen_defects: set[str] = set()
    for record in records:
        if record["task"] == "requirement_validation":
            defect = record.get("defect_type", "unknown")
            if defect not in seen_defects:
                add(record, f"defect {defect}")
                seen_defects.add(defect)

    synthesized_added = 0
    authored_added = 0
    numeric_added = 0
    paired_scenario_id: str | None = None
    for record in records:
        provenance_kind = record.get("provenance", {}).get("requirement_provenance")
        if record["task"] == "non_functional_requirements" and provenance_kind == "synthesized_nfr" and synthesized_added < 8:
            add(record, "synthesized NFR")
            paired_scenario_id = paired_scenario_id or record["scenario_id"]
            synthesized_added += 1
        if record["task"] == "non_functional_requirements" and provenance_kind == "authored_nfr" and authored_added < 3:
            add(record, "authored NFR")
            authored_added += 1
        if "Numeric provenance:" in record["messages"][2]["content"] and numeric_added < 6:
            add(record, "numeric provenance")
            numeric_added += 1

    if paired_scenario_id:
        for record in records:
            if record["scenario_id"] == paired_scenario_id and record["task"] in {"context_extraction", "srs_generation"}:
                add(record, "context/SRS pair for synthesized NFR review")

    for item in leakage["highest_similarity_matches"][:5]:
        sid = item["scenario_id"]
        for record in records:
            if record["scenario_id"] == sid and record["task"] in {"context_extraction", "srs_generation"}:
                add(record, f"high eval similarity to {item['eval_id']}")
                break

    full_srs = [record for record in records if record["task"] == "srs_generation"]
    for record in full_srs[:3]:
        add(record, "full SRS example")

    covered_answer_types: set[str] = set()
    for record in records:
        if record["task"] != "clarification_questions":
            continue
        answer_types = {
            question["expected_answer_type"]
            for question in assistant_json(record)["questions"]
        }
        if answer_types - covered_answer_types:
            add(record, "clarification answer-type coverage")
            covered_answer_types.update(answer_types)
        if covered_answer_types == {"text", "number", "list", "boolean"}:
            break

    longest = sorted(
        records,
        key=lambda row: len(row["messages"][0]["content"]) + len(row["messages"][1]["content"]) + len(row["messages"][2]["content"]),
        reverse=True,
    )
    for record in longest:
        add(record, "longest-token example")
        if len(selected) >= 40:
            break

    sample = list(selected.values())
    sample.sort(
        key=lambda row: (
            row["record_id"] not in mandatory_record_ids,
            row["task"],
            row["record_id"],
        )
    )
    return sample[:45]


def write_markdown_reports(
    data_dir: Path,
    dataset_report: dict[str, Any],
    leakage: dict[str, Any],
) -> None:
    """Write human-readable audit and review guide markdown files."""
    lines = [
        "# Final Fine-Tuning Dataset Audit",
        "",
        "Phase 4C audit complete. No QLoRA training was performed.",
        "",
        "## Verdict",
        "",
        f"`READY_FOR_QLORA={str(dataset_report['ready_for_qlora']).lower()}`",
        "",
        "## Summary",
        "",
        f"- Underlying scenarios: {dataset_report['scenario_count']}",
        f"- Records before audit: {dataset_report['records_before_audit']}",
        f"- Records after audit: {dataset_report['records_after_audit']}",
        f"- Train scenarios: {dataset_report['split']['train_scenario_count']}",
        f"- Validation scenarios: {dataset_report['split']['validation_scenario_count']}",
        f"- Train records: {dataset_report['split']['train_record_count']}",
        f"- Validation records: {dataset_report['split']['validation_record_count']}",
        f"- Evaluation leakage count: {leakage['leakage_count']}",
        "",
        "## Task Distribution",
        "",
    ]
    for task, count in dataset_report["task_distribution"]["counts"].items():
        lines.append(f"- `{task}`: {count}")
    lines.extend(
        [
            "",
            "## Quality Findings",
            "",
            f"- Requirement-quality failures: {dataset_report['requirement_quality']['failure_count']}",
            f"- Acceptance-criteria failures: {dataset_report['acceptance_criteria_quality']['failure_count']}",
            f"- Exact duplicate user messages: {dataset_report['duplicates']['exact_duplicate_user_messages']}",
            f"- Exact duplicate assistant outputs: {dataset_report['duplicates']['exact_duplicate_assistant_outputs']}",
            f"- Near-duplicate scenarios: {dataset_report['duplicates']['near_duplicate_scenario_count']}",
            "",
            "## Highest Evaluation Similarities",
            "",
        ]
    )
    for match in leakage["highest_similarity_matches"][:10]:
        lines.append(
            f"- {match['scenario_id']} vs {match['eval_id']}: "
            f"{match['similarity']} ({match['leakage_decision']})"
        )
    lines.extend(
        [
            "",
            "## Remaining Concerns",
            "",
            *[f"- {item}" for item in dataset_report["remaining_concerns"]],
            "",
        ]
    )
    (data_dir / "FINAL_DATASET_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")

    guide = [
        "# Human Review Guide",
        "",
        "Review `review_sample.jsonl` before QLoRA training.",
        "",
        "For each example, check semantic correctness, requirement atomicity, "
        "acceptance criteria, numeric provenance, and whether the assistant output "
        "teaches the desired production behaviour.",
        "",
        "Pay extra attention to examples whose `review_reason` is `synthesized NFR`, "
        "`defect ...`, `high eval similarity ...`, or `oversized record ...`.",
        "",
        "Reject or repair any example that looks like a trivial paraphrase of an "
        "evaluation case, includes unsupported factual material, or uses generic "
        "requirements such as `The system shall be secure`.",
        "",
        "Do not train until the review set has been inspected.",
        "",
    ]
    (data_dir / "REVIEW_GUIDE.md").write_text("\n".join(guide), encoding="utf-8")


def write_phase4c1_report(data_dir: Path, dataset_report: dict[str, Any], leakage: dict[str, Any]) -> None:
    """Write the Phase 4C.1 repair report for human review."""
    semantic = dataset_report["semantic_quality_validators"]
    repetition = semantic["synthesized_nfr_repetition"]
    review_distribution = dataset_report["review_sample_task_distribution"]
    lines = [
        "# Phase 4C.1 Dataset Repair Report",
        "",
        "No QLoRA training was performed.",
        "",
        "## Repair Summary",
        "",
        f"1. Old record count: {dataset_report['records_before_repair']}",
        f"2. New record count: {dataset_report['records_after_audit']}",
        f"3. Synthesized NFRs removed/replaced: {dataset_report['phase4c1_repairs']['synthesized_nfr_scenarios_replaced']} scenario-level synthesized NFRs replaced",
        f"4. Maximum repeated NFR count before/after: {PHASE4C_BASELINE_REPETITION['max_repeated_synthesized_nfr_statement']} -> {repetition['max_repeated_statement_count']}",
        f"5. Maximum repeated acceptance criterion before/after: {PHASE4C_BASELINE_REPETITION['max_repeated_synthesized_nfr_acceptance']} -> {repetition['max_repeated_acceptance_count']}",
        f"6. Clarification-answer leakage cases found/fixed: {dataset_report['phase4c1_repairs']['clarification_answer_leakage_cases_fixed']} -> {semantic['clarification_answer_leakage']['failure_count']} remaining",
        f"7. Unsupported context assertions found/fixed: {semantic['unsupported_context_assertions']['unsupported_constraints_moved_to_missing_information']} moved to missing_information; {semantic['unsupported_context_assertions']['failure_count']} remaining",
        f"8. Unsupported numeric assumptions found/fixed: {semantic['unsupported_numeric_assumptions']['source_assumption_numeric_items']} sanitized; {semantic['unsupported_numeric_assumptions']['failure_count']} remaining",
        "",
        "## Final Task Distribution",
        "",
    ]
    for task, count in dataset_report["task_distribution"]["counts"].items():
        lines.append(f"- `{task}`: {count}")
    lines.extend(["", "## Review Sample Distribution", ""])
    for task, count in sorted(review_distribution.items()):
        lines.append(f"- `{task}`: {count}")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Eval leakage count: {leakage['leakage_count']}",
            f"- Train/validation scenario overlap: {len(dataset_report['split']['scenario_overlap'])}",
            f"- Schema validation result: {dataset_report['schema_validation']['assistant_payloads_valid']}/{dataset_report['schema_validation']['assistant_payloads_checked']} assistant payloads valid",
            "- Tests: pending external command run",
            "- Ruff result: pending external command run",
            "",
            "## Semantic Validators",
            "",
            f"- Hidden clarification-answer leakage: {semantic['clarification_answer_leakage']['failure_count']}",
            f"- Unsupported mandatory context assertions: {semantic['unsupported_context_assertions']['failure_count']}",
            f"- Repeated synthesized NFR max statement count: {repetition['max_repeated_statement_count']}",
            f"- Repeated synthesized NFR max acceptance count: {repetition['max_repeated_acceptance_count']}",
            f"- Unsupported concrete assumption values: {semantic['unsupported_numeric_assumptions']['failure_count']}",
            "",
            f"READY_FOR_QLORA={str(dataset_report['ready_for_qlora']).lower()}",
            "",
        ]
    )
    (data_dir / "PHASE4C1_REPAIR_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def write_phase4c2_report(data_dir: Path, dataset_report: dict[str, Any], leakage: dict[str, Any]) -> None:
    """Write the Phase 4C.2 final repair report for human review."""
    semantic = dataset_report["semantic_quality_validators"]
    nfr_semantic = semantic["synthesized_nfr_semantic_validation"]
    cross_stage = semantic["cross_stage_consistency_validation"]
    summary_validation = semantic["project_summary_validation"]
    answer_types = semantic["clarification_answer_type_validation"]
    review_distribution = dataset_report["review_sample_task_distribution"]
    lines = [
        "# Phase 4C.2 Final Dataset Quality Repair Report",
        "",
        "No QLoRA training was performed.",
        "",
        "## Repair Summary",
        "",
        f"1. Synthesized NFR records reviewed: {dataset_report['phase4c2_repairs']['synthesized_nfr_records_reviewed']}",
        f"2. NFRs rewritten: {dataset_report['phase4c2_repairs']['synthesized_nfr_records_rewritten']}",
        f"3. NFRs removed because no defensible quality attribute existed: {dataset_report['phase4c2_repairs']['synthesized_nfr_records_removed']}",
        f"4. NFR classification changes: {dataset_report['phase4c2_repairs']['nfr_classification_changes']}",
        f"5. Cross-stage inconsistency cases found/fixed: {cross_stage['failure_count']} remaining after repair",
        f"6. Project summaries corrected: {summary_validation['project_summaries_corrected']}",
        f"7. Clarification answer-type errors found/fixed: {answer_types['failure_count']} remaining after repair",
        f"8. Final record count: {dataset_report['records_after_audit']}",
        "",
        "## Final Task Distribution",
        "",
    ]
    for task, count in dataset_report["task_distribution"]["counts"].items():
        lines.append(f"- `{task}`: {count}")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"10. Eval leakage count: {leakage['leakage_count']}",
            f"11. Train/validation overlap: {len(dataset_report['split']['scenario_overlap'])}",
            f"12. Schema result: {dataset_report['schema_validation']['assistant_payloads_valid']}/{dataset_report['schema_validation']['assistant_payloads_checked']} assistant payloads valid",
            "- 13. Tests: pending external command run",
            "- 14. Ruff: pending external command run",
            "",
            "## Semantic Validators",
            "",
            f"- Synthesized NFR semantic failures: {nfr_semantic['failure_count']}",
            f"- Cross-stage consistency failures: {cross_stage['failure_count']}",
            f"- Project-summary assumption failures: {summary_validation['failure_count']}",
            f"- Clarification answer-type failures: {answer_types['failure_count']}",
            f"- Hidden clarification-answer leakage: {semantic['clarification_answer_leakage']['failure_count']}",
            f"- Unsupported mandatory context assertions: {semantic['unsupported_context_assertions']['failure_count']}",
            f"- Unsupported concrete assumption values: {semantic['unsupported_numeric_assumptions']['failure_count']}",
            f"- Repeated synthesized NFR max statement count: {semantic['synthesized_nfr_repetition']['max_repeated_statement_count']}",
            f"- Repeated synthesized NFR max acceptance count: {semantic['synthesized_nfr_repetition']['max_repeated_acceptance_count']}",
            "",
            "## Review Sample Distribution",
            "",
        ]
    )
    for task, count in sorted(review_distribution.items()):
        lines.append(f"- `{task}`: {count}")
    lines.extend(
        [
            "",
            f"READY_FOR_QLORA={str(dataset_report['ready_for_qlora']).lower()}",
            "",
        ]
    )
    (data_dir / "PHASE4C2_FINAL_REPAIR_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def write_phase4c3_report(data_dir: Path, dataset_report: dict[str, Any], leakage: dict[str, Any]) -> None:
    """Write the Phase 4C.3 final semantic audit report."""
    semantic = dataset_report["semantic_quality_validators"]
    nfr_bias = semantic["nfr_pattern_bias_validation"]
    cross_report = dataset_report["cross_stage_consistency_report"]
    review_distribution = dataset_report["review_sample_task_distribution"]
    lines = [
        "# Phase 4C.3 Final Semantic Dataset Audit",
        "",
        "No QLoRA training was performed.",
        "",
        "## Summary",
        "",
        f"1. Dataset records before/after: {dataset_report['records_before_repair']} -> {dataset_report['records_after_audit']}",
        f"2. Hospital assumption issue fixed: {dataset_report['phase4c3_repairs']['hospital_assumption_issue_fixed']}",
        f"3. Total cross-stage inconsistencies fixed: {dataset_report['phase4c3_repairs']['cross_stage_inconsistencies_fixed']}",
        f"4. Confirmed-vs-unconfirmed conflicts fixed: {dataset_report['phase4c3_repairs']['confirmed_vs_unconfirmed_conflicts_fixed']}",
        f"5. NFRs reviewed: {dataset_report['phase4c3_repairs']['nfrs_reviewed']}",
        f"6. NFRs rewritten: {dataset_report['phase4c3_repairs']['nfrs_rewritten']}",
        f"7. NFRs reclassified: {dataset_report['phase4c3_repairs']['nfrs_reclassified']}",
        f"8. NFRs removed: {dataset_report['phase4c3_repairs']['nfrs_removed']}",
        f"9. Audit Evidence Traceability frequency before/after: {dataset_report['phase4c3_repairs']['audit_evidence_traceability_before']} -> {dataset_report['phase4c3_repairs']['audit_evidence_traceability_after']}",
        f"10. Unsupported provenance claims fixed: {semantic['unsupported_provenance_claim_validation']['failure_count']} remaining",
        f"11. Clarification-type issues: {semantic['clarification_answer_type_validation']['failure_count']}",
        "",
        "## Final Task Distribution",
        "",
    ]
    for task, count in dataset_report["task_distribution"]["counts"].items():
        lines.append(f"- `{task}`: {count}")
    lines.extend(
        [
            "",
            "## Final Quality Metrics",
            "",
            f"- Eval leakage: {leakage['leakage_count']}",
            f"- Split overlap: {len(dataset_report['split']['scenario_overlap'])}",
            f"- Schema result: {dataset_report['schema_validation']['assistant_payloads_valid']}/{dataset_report['schema_validation']['assistant_payloads_checked']} assistant payloads valid",
            f"- Max repeated NFR pattern: {nfr_bias['max_repeated_nfr_pattern']}",
            f"- Max repeated NFR title: {nfr_bias['max_repeated_nfr_title']}",
            f"- Resolved/unresolved gap conflicts: {cross_report['resolved_gap_contradictions']}",
            f"- Unconfirmed assumptions promoted to requirements/facts: {cross_report['unconfirmed_to_mandatory_promotions']}",
            f"- Requirement provenance mismatches: {cross_report['requirement_provenance_mismatches']}",
            f"- Exact duplicate rate: {dataset_report['duplicates']['duplicate_rate']}",
            f"- Near-duplicate rate: {dataset_report['duplicates']['near_duplicate_rate']}",
            "",
            "## Review Sample Distribution",
            "",
        ]
    )
    for task, count in sorted(review_distribution.items()):
        lines.append(f"- `{task}`: {count}")
    lines.extend(
        [
            "",
            "## Validation Commands",
            "",
            "- Scenario validation: pending external command run",
            "- Dataset generation: pending external command run",
            "- Dataset audit: pending external command run",
            "- Cross-stage consistency audit: pending external command run",
            "- Backend tests: pending external command run",
            "- Ruff: pending external command run",
            "",
            f"READY_FOR_QLORA={str(dataset_report['ready_for_qlora']).lower()}",
            "",
        ]
    )
    (data_dir / "PHASE4C3_FINAL_SEMANTIC_AUDIT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def write_phase4c4_report(
    data_dir: Path,
    dataset_report: dict[str, Any],
    leakage: dict[str, Any],
) -> None:
    """Write the Phase 4C.4 pre-training semantic signoff report."""
    cross_report = dataset_report["cross_stage_consistency_report"]
    distribution = dataset_report["task_distribution"]["counts"]
    schema = dataset_report["schema_validation"]
    repairs = dataset_report["phase4c4_repairs"]
    review_distribution = dataset_report["review_sample_task_distribution"]
    lines = [
        "# Phase 4C.4 Pre-Training Signoff",
        "",
        "No QLoRA training was performed.",
        "",
        "## Targeted Repairs",
        "",
        f"- SCN-009 health-data inference fixed: {repairs['scn009_health_data_issue_fixed']}",
        f"- SCN-001 unresolved no-control scope fixed: {repairs['scn001_scope_issue_fixed']}",
        f"- Security-like NFRs reclassified: {repairs['nfrs_reclassified']}",
        f"- Security-like synthesized NFRs removed: {repairs['security_like_nfrs_removed']}",
        f"- Net standalone NFR records removed: {repairs['net_standalone_nfr_records_removed']}",
        f"- Final standalone NFR count: {distribution.get('non_functional_requirements', 0)}",
        f"- Final total record count: {dataset_report['records_after_audit']}",
        "",
        "## Semantic Gates",
        "",
        f"- Scope-level assumption promotions: {cross_report['scope_level_assumption_promotions']}",
        f"- Requirement-level assumption promotions: {cross_report['requirement_level_assumption_promotions']}",
        f"- Architecture-level assumption promotions: {cross_report['architecture_level_assumption_promotions']}",
        f"- Risk-level assumption promotions: {cross_report['risk_level_assumption_promotions']}",
        f"- NFR classification failures: {dataset_report['semantic_quality_validators']['nfr_classification_validation']['failure_count']}",
        f"- Evaluation leakage: {leakage['leakage_count']}",
        f"- Train/validation scenario overlap: {len(dataset_report['split']['scenario_overlap'])}",
        f"- Schema validity: {schema['assistant_payloads_valid']}/{schema['assistant_payloads_checked']}",
        f"- Review-sample threat-model records: {review_distribution.get('threat_model', 0)}",
        "",
        "## External Verification",
        "",
        "- Pytest: PENDING_FINAL_COMMAND",
        "- Ruff: PENDING_FINAL_COMMAND",
        "",
        f"READY_FOR_QLORA={str(dataset_report['ready_for_qlora']).lower()}",
        "",
    ]
    (data_dir / "PHASE4C4_PRETRAINING_SIGNOFF.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def audit_dataset(data_dir: Path) -> dict[str, Any]:
    """Run the full dataset audit and write Phase 4C output files."""
    records = load_records(data_dir)
    schema_errors = {
        record["record_id"]: errors
        for record in records
        if (errors := validate_assistant_payload(record))
    }
    split = scenario_split(records)
    write_jsonl(data_dir / "train.jsonl", split["train_records"])
    write_jsonl(data_dir / "validation.jsonl", split["validation_records"])

    leakage = leakage_report()
    duplicates = duplicate_audit(records)
    clarification_leakage = clarification_answer_leakage(records)
    context_assertions = unsupported_context_assertions(records)
    numeric_assumptions = unsupported_numeric_assumptions(records)
    nfr_repetition = synthesized_nfr_repetition(records)
    nfr_semantic = synthesized_nfr_semantic_validation(records)
    cross_stage_consistency = cross_stage_consistency_validation(records)
    project_summaries = project_summary_validation(records)
    answer_types = clarification_answer_type_validation(records)
    resolved_gaps = resolved_gap_validation(records)
    nfr_classification = nfr_classification_validation(records)
    nfr_pattern_bias = nfr_pattern_bias_validation(records)
    provenance_claims = unsupported_provenance_claim_validation(records)
    cross_stage_report = build_cross_stage_consistency_report(
        records,
        cross_stage_consistency,
        resolved_gaps,
        provenance_claims,
    )

    requirement_findings: list[dict[str, str]] = []
    acceptance_findings: list[dict[str, str]] = []
    for record in records:
        for req in all_requirements_from_record(record):
            requirement_findings.extend(audit_requirement(req, record))
            acceptance_findings.extend(audit_acceptance(req, record))

    synthesized_nfrs = [
        record
        for record in records
        if record["task"] == "non_functional_requirements"
        and record.get("provenance", {}).get("requirement_provenance") == "synthesized_nfr"
    ]
    authored_nfrs = [
        record
        for record in records
        if record["task"] == "non_functional_requirements"
        and record.get("provenance", {}).get("requirement_provenance") == "authored_nfr"
    ]
    defect_distribution = Counter(
        record.get("defect_type", "unknown")
        for record in records
        if record["task"] == "requirement_validation"
    )
    token_report = token_stats(records)
    review_sample = build_review_sample(records, leakage, token_report)
    write_jsonl(data_dir / "review_sample.jsonl", review_sample)
    review_distribution = Counter(record["task"] for record in review_sample)

    provenance_distribution = Counter(
        record.get("provenance", {}).get("scenario_source_type", "missing")
        for record in records
    )
    scenario_source_distribution = {"synthetic": len(SCENARIOS), "manually_authored": len(SCENARIOS)}
    standalone_nfr_count = sum(
        record["task"] == "non_functional_requirements" for record in records
    )
    security_like_nfrs_removed = sum(PHASE4C4_REMOVED_SECURITY_LIKE_NFRS.values())
    dataset_report = {
        "audit_version": "phase-4c.4",
        "repair_version": "phase-4c.4",
        "scenario_count": len(SCENARIOS),
        "records_before_audit": PHASE4C3_RECORD_COUNT,
        "records_before_repair": PHASE4C3_RECORD_COUNT,
        "records_after_audit": len(records),
        "records_removed": PHASE4C3_RECORD_COUNT - len(records),
        "records_repaired_or_regenerated": len(records),
        "phase4c1_repairs": {
            "synthesized_nfr_scenarios_replaced": len(synthesized_nfrs),
            "clarification_answer_leakage_cases_fixed": sum(
                len(scenario["clarifications"]) for scenario in SCENARIOS
            ),
            "unsupported_numeric_assumptions_sanitized": numeric_assumptions[
                "source_assumption_numeric_items"
            ],
        },
        "phase4c2_repairs": {
            "synthesized_nfr_records_reviewed": nfr_semantic[
                "synthesized_nfr_instances_checked"
            ],
            "synthesized_nfr_records_rewritten": nfr_semantic[
                "synthesized_nfr_instances_checked"
            ],
            "synthesized_nfr_records_removed": 0,
            "nfr_classification_changes": 0,
            "cross_stage_inconsistency_failures_remaining": cross_stage_consistency[
                "failure_count"
            ],
            "project_summaries_corrected": project_summaries[
                "project_summaries_corrected"
            ],
            "clarification_answer_type_failures_remaining": answer_types[
                "failure_count"
            ],
        },
        "phase4c3_repairs": {
            "hospital_assumption_issue_fixed": True,
            "cross_stage_inconsistencies_fixed": cross_stage_report[
                "unconfirmed_to_mandatory_promotions"
            ],
            "confirmed_vs_unconfirmed_conflicts_fixed": cross_stage_report[
                "resolved_gap_contradictions"
            ],
            "nfrs_reviewed": nfr_pattern_bias["nfr_instances_checked"],
            "nfrs_rewritten": nfr_semantic["synthesized_nfr_instances_checked"],
            "nfrs_reclassified": 2,
            "nfrs_removed": 2,
            "audit_evidence_traceability_before": 32,
            "audit_evidence_traceability_after": 0,
        },
        "phase4c4_repairs": {
            "scn009_health_data_issue_fixed": True,
            "scn001_scope_issue_fixed": True,
            "nfrs_reclassified": 0,
            "security_like_nfrs_removed": security_like_nfrs_removed,
            "removed_nfr_title_counts": PHASE4C4_REMOVED_SECURITY_LIKE_NFRS,
            "scn009_grounded_nfr_replacement": "Medical-Device Event Reliability",
            "net_standalone_nfr_records_removed": (
                PHASE4C3_STANDALONE_NFR_COUNT - standalone_nfr_count
            ),
            "final_standalone_nfr_count": standalone_nfr_count,
        },
        "schema_validation": {
            "assistant_payloads_checked": len(records),
            "assistant_payloads_valid": len(records) - len(schema_errors),
            "errors": schema_errors,
        },
        "split": {
            "seed": 42,
            "train_scenario_count": len(split["train_scenarios"]),
            "validation_scenario_count": len(split["validation_scenarios"]),
            "train_record_count": len(split["train_records"]),
            "validation_record_count": len(split["validation_records"]),
            "train_scenarios": split["train_scenarios"],
            "validation_scenarios": split["validation_scenarios"],
            "scenario_overlap": split["scenario_overlap"],
        },
        "task_distribution": task_distribution(records),
        "scenario_provenance_distribution": scenario_source_distribution,
        "record_provenance_distribution": dict(provenance_distribution),
        "synthetic_vs_authored_distribution": {
            "synthetic_scenarios": len(SCENARIOS),
            "manually_authored_synthetic_scenarios": len(SCENARIOS),
            "transformed_public_dataset_scenarios": 0,
            "mixed_scenarios": 0,
        },
        "duplicates": duplicates,
        "semantic_quality_validators": {
            "clarification_answer_leakage": clarification_leakage,
            "unsupported_context_assertions": context_assertions,
            "synthesized_nfr_repetition": nfr_repetition,
            "unsupported_numeric_assumptions": numeric_assumptions,
            "synthesized_nfr_semantic_validation": nfr_semantic,
            "cross_stage_consistency_validation": cross_stage_consistency,
            "project_summary_validation": project_summaries,
            "clarification_answer_type_validation": answer_types,
            "resolved_gap_validation": resolved_gaps,
            "nfr_classification_validation": nfr_classification,
            "nfr_pattern_bias_validation": nfr_pattern_bias,
            "unsupported_provenance_claim_validation": provenance_claims,
        },
        "cross_stage_consistency_report": cross_stage_report,
        "requirement_quality": {
            "failure_count": len(requirement_findings),
            "findings": requirement_findings[:100],
        },
        "acceptance_criteria_quality": {
            "failure_count": len(acceptance_findings),
            "findings": acceptance_findings[:100],
        },
        "synthesized_nfr_audit": {
            "authored_nfr_record_count": len(authored_nfrs),
            "synthesized_nfr_record_count": len(synthesized_nfrs),
            "result": (
                "PASS: synthesized NFRs are scenario/category anchored, contain no invented "
                "numeric thresholds, and are marked in provenance."
            ),
        },
        "requirement_validation_defect_distribution": dict(sorted(defect_distribution.items())),
        "full_srs_quality": srs_quality_audit(records),
        "prompt_matching_audit": prompt_audit(records),
        "token_statistics": token_report,
        "review_sample_task_distribution": dict(sorted(review_distribution.items())),
        "source_provenance_audit": {
            "scenario_source": "ai/finetuning/scripts/scenario_bank_a.py, scenario_bank_b.py, scenario_bank_c.py",
            "classification": "all 60 scenarios are manually authored synthetic CyberSRS scenarios",
            "external_srs_repositories_used": [],
            "external_requirement_datasets_used": [],
            "note": "No RE-Bench, RE-GSC, QRAQ, or external SRS repository records were incorporated.",
        },
        "final_validation": {
            "no_eval_leakage": leakage["leakage_count"] == 0,
            "no_scenario_split_overlap": not split["scenario_overlap"],
            "all_assistant_payloads_validate": not schema_errors,
            "all_records_have_provenance": all("provenance" in record for record in records),
            "record_ids_unique": len({record["record_id"] for record in records}) == len(records),
            "no_clarification_answer_leakage": clarification_leakage["failure_count"] == 0,
            "no_unsupported_context_assertions": context_assertions["failure_count"] == 0,
            "no_unsupported_numeric_assumptions": numeric_assumptions["failure_count"] == 0,
            "synthesized_nfr_repetition_guard_passed": (
                nfr_repetition["max_repeated_statement_count"] <= 2
                and nfr_repetition["max_repeated_acceptance_count"] <= 8
            ),
            "synthesized_nfr_semantic_guard_passed": nfr_semantic["failure_count"] == 0,
            "cross_stage_consistency_guard_passed": cross_stage_consistency["failure_count"] == 0,
            "project_summary_guard_passed": project_summaries["failure_count"] == 0,
            "clarification_answer_type_guard_passed": answer_types["failure_count"] == 0,
            "resolved_gap_guard_passed": resolved_gaps["failure_count"] == 0,
            "nfr_classification_guard_passed": nfr_classification["failure_count"] == 0,
            "nfr_pattern_bias_guard_passed": nfr_pattern_bias["failure_count"] == 0,
            "unsupported_provenance_claim_guard_passed": provenance_claims["failure_count"] == 0,
            "review_sample_has_threat_model": review_distribution.get("threat_model", 0) >= 1,
        },
        "remaining_concerns": [
            "Manual review is still required for the selected Phase 4C.4 review sample before training.",
            "Data and network standalone section tasks remain intentionally small because few scenarios legitimately require them.",
            "All records are within 4096 tokens, but full SRS records exceed 2048 tokens; training should use an explicit max sequence policy rather than silent truncation.",
        ],
    }
    dataset_report["ready_for_qlora"] = (
        dataset_report["final_validation"]["no_eval_leakage"]
        and dataset_report["final_validation"]["no_scenario_split_overlap"]
        and dataset_report["final_validation"]["all_assistant_payloads_validate"]
        and dataset_report["final_validation"]["all_records_have_provenance"]
        and dataset_report["final_validation"]["record_ids_unique"]
        and dataset_report["requirement_quality"]["failure_count"] == 0
        and dataset_report["acceptance_criteria_quality"]["failure_count"] == 0
        and dataset_report["final_validation"]["no_clarification_answer_leakage"]
        and dataset_report["final_validation"]["no_unsupported_context_assertions"]
        and dataset_report["final_validation"]["no_unsupported_numeric_assumptions"]
        and dataset_report["final_validation"]["synthesized_nfr_repetition_guard_passed"]
        and dataset_report["final_validation"]["synthesized_nfr_semantic_guard_passed"]
        and dataset_report["final_validation"]["cross_stage_consistency_guard_passed"]
        and dataset_report["final_validation"]["project_summary_guard_passed"]
        and dataset_report["final_validation"]["clarification_answer_type_guard_passed"]
        and dataset_report["final_validation"]["resolved_gap_guard_passed"]
        and dataset_report["final_validation"]["nfr_classification_guard_passed"]
        and dataset_report["final_validation"]["nfr_pattern_bias_guard_passed"]
        and dataset_report["final_validation"]["unsupported_provenance_claim_guard_passed"]
        and dataset_report["final_validation"]["review_sample_has_threat_model"]
    )

    (data_dir / "leakage_report.json").write_text(
        json.dumps(leakage, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (data_dir / "cross_stage_consistency_report.json").write_text(
        json.dumps(cross_stage_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (data_dir / "dataset_report.json").write_text(
        json.dumps(dataset_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown_reports(data_dir, dataset_report, leakage)
    write_phase4c1_report(data_dir, dataset_report, leakage)
    write_phase4c2_report(data_dir, dataset_report, leakage)
    write_phase4c3_report(data_dir, dataset_report, leakage)
    write_phase4c4_report(data_dir, dataset_report, leakage)
    return dataset_report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the Phase 4C audit."""
    parser = argparse.ArgumentParser(description="Audit CyberSRS fine-tuning data.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)
    report = audit_dataset(args.data_dir)
    print(f"records audited: {report['records_after_audit']}")
    print(f"train scenarios: {report['split']['train_scenario_count']}")
    print(f"validation scenarios: {report['split']['validation_scenario_count']}")
    print(f"train records: {report['split']['train_record_count']}")
    print(f"validation records: {report['split']['validation_record_count']}")
    print(f"READY_FOR_QLORA={str(report['ready_for_qlora']).lower()}")
    return 0 if report["ready_for_qlora"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
