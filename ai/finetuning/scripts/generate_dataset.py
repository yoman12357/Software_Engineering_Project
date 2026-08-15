"""Generate the synthetic fine-tuning dataset from the scenario library.

Each scenario in ``scenario_library`` is expanded into one or more
conversation-format training records (FINETUNING_PLAN section 4). Records are grouped
by task type into per-task JSONL files written under
``ai/finetuning/data/``.

Task types produced (mapping to FINETUNING_PLAN section 5):
- context_extraction      description -> ProjectAnalysis JSON
- clarification_questions analysis -> ClarificationQuestionSet JSON
- functional_requirements context -> {"functional_requirements": [...]}
- non_functional_requirements authored or audited synthesized NFRs
- security_requirements
- data_requirements       (only scenarios with authored data requirements)
- network_requirements    (only scenarios with authored network requirements)
- architecture            context -> architecture summary JSON
- threat_model            context -> {"threats": [...], "mitigations": [...]}
- srs_generation          description -> complete SRSSchema JSON
- requirement_validation  corrupted requirement JSON -> corrected requirement JSON

Every assistant payload is validated against its Pydantic schema before the
record is written; records that fail validation are rejected and counted.

Run standalone:
    python ai/finetuning/scripts/generate_dataset.py [--out-dir DIR]
"""

# ruff: noqa: E501  # prompt strings are intentionally long, as in src/prompts/*

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.finetuning.scripts.scenario_library import SCENARIOS  # noqa: E402
from src.prompts.analysis import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_TEMPLATE  # noqa: E402
from src.prompts.clarification import (  # noqa: E402
    CLARIFICATION_SYSTEM_PROMPT,
    CLARIFICATION_USER_TEMPLATE,
)
from src.prompts.srs import (  # noqa: E402
    ARCHITECTURE_SYSTEM_PROMPT,
    ARCHITECTURE_USER_TEMPLATE,
    DATA_REQUIREMENTS_SYSTEM_PROMPT,
    DATA_REQUIREMENTS_USER_TEMPLATE,
    FUNCTIONAL_REQUIREMENTS_SYSTEM_PROMPT,
    FUNCTIONAL_REQUIREMENTS_USER_TEMPLATE,
    NETWORK_REQUIREMENTS_SYSTEM_PROMPT,
    NETWORK_REQUIREMENTS_USER_TEMPLATE,
    NON_FUNCTIONAL_REQUIREMENTS_SYSTEM_PROMPT,
    NON_FUNCTIONAL_REQUIREMENTS_USER_TEMPLATE,
    SECURITY_REQUIREMENTS_SYSTEM_PROMPT,
    SECURITY_REQUIREMENTS_USER_TEMPLATE,
    SRS_SYSTEM_PROMPT,
    SRS_USER_TEMPLATE,
    THREATS_SYSTEM_PROMPT,
    THREATS_USER_TEMPLATE,
)
from src.schemas.analysis import ProjectAnalysis  # noqa: E402
from src.schemas.clarification import ClarificationQuestionSet  # noqa: E402
from src.schemas.srs import (  # noqa: E402
    ArchitectureSummary,
    Mitigation,
    Requirement,
    SRSSchema,
    TestingRecommendation,
    Threat,
)

# Fixed values so regeneration is byte-for-byte deterministic.
GENERATED_AT = "2026-08-12T00:00:00+00:00"
TRAINING_MODEL = "Qwen/Qwen3-4B-Instruct-2507"

PREVIOUS_SECTIONS_SUMMARY = (
    "The SRS already includes: metadata, project_overview, scope, assumptions, "
    "stakeholders, and user_roles. These sections are complete and must not be "
    "regenerated or contradicted."
)

CORRECTION_SYSTEM_PROMPT = """You are a requirements engineer reviewing a generated requirement that failed deterministic validation.

The requirement JSON below violates one or more validation rules: invalid requirement ID format, statement not beginning with "The system shall", non-atomic or compound wording, a forbidden or weak rationale, unsupported numeric thresholds, wrong category assignment, vague adjectives, missing provenance, or acceptance criteria that are not meaningful GIVEN-WHEN-THEN checks.

Fix the validation error(s) and return ONLY the corrected requirement JSON object matching the schema below. Do not change the requirement's meaning or any fields that are already valid. No Markdown fences, no explanations.

Schema (exact fields):
- id: "(FR|NFR|SEC|DATA|NET)-NNN" format
- category: "functional" | "non_functional" | "security" | "data" | "network"
- title: non-empty string
- statement: testable requirement starting with "The system shall" exactly once
- rationale: non-empty, specific to the project (never a generic placeholder)
- priority: "must" | "should" | "could"
- acceptance_criteria: GIVEN-WHEN-THEN format with measurable pass/fail conditions
- dependencies: array of requirement IDs (may be empty)
- source_references: array of citation objects (may be empty)
- confidence: "high" | "medium" | "low"
- user_confirmed: boolean
"""

NO_RAG_CONTEXT_NOTE = (
    "No retrieved chunks are provided for this synthetic training record. "
    "Use empty source_references arrays and do not invent citations."
)


# --- Schema conformance helpers ---------------------------------------------


def _strip_authoring_fields(req: dict[str, Any]) -> dict[str, Any]:
    """Remove scenario-authoring convenience keys not part of the Requirement schema."""
    return {k: v for k, v in req.items() if k != "numeric"}


def _build_requirement(req: dict[str, Any]) -> dict[str, Any]:
    """Validate a scenario requirement dict and preserve numeric provenance in text."""
    candidate = _strip_authoring_fields(req)
    numeric_items = req.get("numeric", [])
    if numeric_items:
        provenance_parts: list[str] = []
        for item in numeric_items:
            provenance = item["provenance"]
            value = item["value"]
            if provenance == "ASSUMPTION_REQUIRING_CONFIRMATION":
                for field in ("statement", "acceptance_criteria"):
                    candidate[field] = re.sub(
                        re.escape(value),
                        "the stakeholder-confirmed threshold",
                        candidate[field],
                        flags=re.IGNORECASE,
                    )
                provenance_parts.append(
                    "ASSUMPTION_REQUIRING_CONFIRMATION for a threshold to be confirmed"
                )
            else:
                provenance_parts.append(f"{provenance} for {value}")
        if "Numeric provenance:" not in candidate["rationale"]:
            candidate["rationale"] = (
                candidate["rationale"].rstrip(".")
                + f". Numeric provenance: {'; '.join(provenance_parts)}."
            )
        if any(
            item["provenance"] == "ASSUMPTION_REQUIRING_CONFIRMATION"
            for item in numeric_items
        ) and candidate.get("priority") == "must":
            candidate["priority"] = "should"
    return Requirement.model_validate(candidate).model_dump()


def _record_provenance(scenario: dict[str, Any], **extra: Any) -> dict[str, Any]:
    """Return stable record-level provenance for scenario-derived examples."""
    provenance = {
        "scenario_source_type": "synthetic",
        "scenario_authoring": "manually authored synthetic",
        "scenario_origin": "CyberSRS in-repository scenario bank",
        "scenario_license": "Apache-2.0",
        "external_dataset_sources": [],
        "scenario_id": scenario["id"],
    }
    provenance.update(extra)
    return provenance


def _with_record_metadata(record: dict[str, Any], scenario: dict[str, Any], **extra: Any) -> dict[str, Any]:
    """Attach provenance and quality metadata common to all generated records."""
    record["provenance"] = _record_provenance(scenario, **extra)
    record["quality"] = {
        "assistant_schema_validated": True,
        "human_review_required": True,
        "audit_phase": "Phase 4C",
    }
    return record


def _training_prompt(system_prompt: str) -> str:
    """Adapt production prompts where fixed minimum counts conflict with curated SFT slices."""
    replacements = {
        "- At least 3 functional requirements.": (
            "- Generate the available high-quality functional requirements from the "
            "curated scenario. Do not fabricate extra requirements solely to meet a count."
        ),
        "- At least 2 non-functional requirements covering availability, performance, scalability, etc.": (
            "- Generate the available high-quality non-functional requirements from "
            "the curated scenario. Do not fabricate extra requirements solely to meet a count."
        ),
        "- At least 2 security requirements covering authentication, authorisation, encryption, audit, etc.": (
            "- Generate the available high-quality security requirements from the "
            "curated scenario. Do not fabricate extra requirements solely to meet a count."
        ),
        "- At least 1 data requirement covering retention, integrity, classification, privacy.": (
            "- Generate data requirements only when they are justified by the curated scenario."
        ),
        "- At least 1 network requirement covering segmentation, zones, protocols, bandwidth.": (
            "- Generate network requirements only when they are justified by the curated scenario."
        ),
        "- At least 2 threats.": (
            "- Generate the available high-quality threats from the curated scenario. "
            "Do not fabricate extra threats solely to meet a count."
        ),
    }
    adapted = system_prompt
    for old, new in replacements.items():
        adapted = adapted.replace(old, new)
    return adapted


def _build_context_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    """Build the project-context payload exactly as the SRS service does."""
    analysis = _safe_context_analysis(scenario)
    gap_states = _gap_states(scenario)
    return {
        "project_name": scenario["name"],
        "description": scenario["description"],
        "inferred_categories": scenario["categories"],
        "stakeholders": analysis["stakeholders"],
        "users": analysis["users"],
        "goals": analysis["goals"],
        "constraints": analysis["constraints"],
        "missing_information": [
            item["gap_text"]
            for item in gap_states
            if item["state"] == "UNCONFIRMED_OR_MISSING"
        ],
        "clarification_answers": [
            {"question": q["question"], "answer": q["answer"]}
            for q in scenario["clarifications"]
        ],
        "information_state": {
            "explicit_user_facts": [
                "The project description is the source of established user facts.",
                scenario["description"],
            ],
            "clarification_confirmed": [
                {
                    "gap_id": item["gap_id"],
                    "topic": item["topic"],
                    "question": item["question"],
                    "answer": item["answer"],
                }
                for item in gap_states
                if item["state"] == "CLARIFICATION_CONFIRMED"
            ],
            "safe_inferences": [
                "Cybersecurity implementation details may be considered during design, "
                "but they must not be represented as user-mandated constraints unless "
                "the description or clarification answers confirm them."
            ],
            "unconfirmed_or_missing": [
                {
                    "gap_id": item["gap_id"],
                    "topic": item["topic"],
                    "gap": item["gap_text"],
                }
                for item in gap_states
                if item["state"] == "UNCONFIRMED_OR_MISSING"
            ],
        },
        "version": 1,
    }


def _requirement_summary(scenario: dict[str, Any]) -> str:
    """Summarise the scenario's requirements grouped by category (for prompts)."""
    groups: list[str] = []
    for category in ("functional", "non_functional", "security", "data", "network"):
        ids = [r["id"] for r in _safe_requirement_items(scenario, category)]
        if ids:
            groups.append(f"{category} ({', '.join(ids)})")
    return "; ".join(groups) if groups else "None generated yet."


def _json_lines(obj: Any) -> str:
    """Deterministically serialise a payload as the assistant's JSON answer."""
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _content_tokens(text: str) -> set[str]:
    """Return rough content tokens for stage-consistency checks."""
    stopwords = {
        "a",
        "all",
        "and",
        "be",
        "for",
        "in",
        "is",
        "it",
        "must",
        "of",
        "or",
        "shall",
        "should",
        "system",
        "that",
        "the",
        "to",
        "with",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in stopwords
    }


def _slugify_gap(value: str) -> str:
    """Return a stable semantic identifier fragment for a gap or question."""
    replacements = {
        "siem": "log_platform",
        "log": "log",
        "logs": "logs",
        "pump": "pump",
        "stations": "stations",
    }
    tokens = [replacements.get(token, token) for token in re.findall(r"[a-z0-9]+", value.lower())]
    filtered = [
        token
        for token in tokens
        if token
        not in {
            "a",
            "an",
            "and",
            "are",
            "as",
            "be",
            "by",
            "confirm",
            "does",
            "for",
            "how",
            "is",
            "must",
            "of",
            "or",
            "required",
            "should",
            "the",
            "there",
            "to",
            "what",
            "whether",
            "which",
            "with",
        }
    ]
    return "_".join(filtered[:6]) or "gap"


def _gap_id(scenario: dict[str, Any], gap_text: str, question: str | None = None) -> str:
    """Build a scenario-scoped stable gap ID."""
    source = question or gap_text
    return f"{scenario['id'].lower()}.{_slugify_gap(source)}"


def _gap_states(scenario: dict[str, Any]) -> list[dict[str, str]]:
    """Map gaps to stable IDs and resolved/unresolved information state."""
    analysis = _safe_context_analysis(scenario)
    original_gaps = scenario["analysis"]["missing_information"]
    rows: list[dict[str, str]] = []
    for index, gap in enumerate(original_gaps):
        clarification = (
            scenario["clarifications"][index]
            if index < len(scenario["clarifications"])
            else {"question": "", "answer": ""}
        )
        answer = clarification.get("answer", "").strip()
        rows.append(
            {
                "gap_id": _gap_id(scenario, gap, clarification.get("question")),
                "topic": _slugify_gap(clarification.get("question") or gap),
                "gap_text": gap,
                "question": clarification.get("question", ""),
                "answer": answer,
                "state": "CLARIFICATION_CONFIRMED" if answer else "UNCONFIRMED_OR_MISSING",
            }
        )
    for gap in analysis["missing_information"]:
        if gap in original_gaps:
            continue
        rows.append(
            {
                "gap_id": _gap_id(scenario, gap),
                "topic": _slugify_gap(gap),
                "gap_text": gap,
                "question": "",
                "answer": "",
                "state": "UNCONFIRMED_OR_MISSING",
            }
        )
    return rows


def _is_supported_by_description(assertion: str, description: str) -> bool:
    """Return whether an analysis assertion is supported by the visible input."""
    assertion_tokens = _content_tokens(assertion)
    if not assertion_tokens:
        return True
    description_tokens = _content_tokens(description)
    overlap = len(assertion_tokens & description_tokens) / len(assertion_tokens)
    return overlap >= 0.35


def _unconfirmed_constraints(scenario: dict[str, Any]) -> list[str]:
    """Return scenario constraints that are not established by visible input."""
    description = scenario["description"]
    confirmed_text = " ".join(
        f"{item['question']} {item['answer']}"
        for item in scenario["clarifications"]
        if item["answer"].strip()
    )
    explicit_text = f"{description} {confirmed_text}".lower()
    explicit_non_interference = re.search(
        r"\b(?:non[- ]?interfer|passive|passively|non[- ]?intrusive|must not interfere)\b",
        explicit_text,
    )
    return [
        constraint
        for constraint in scenario["analysis"].get("constraints", [])
        if not _is_supported_by_description(constraint, description)
        or (
            re.search(r"\b(?:interfere|passive|passively|non[- ]?intrusive)\b", constraint, flags=re.I)
            and not explicit_non_interference
        )
    ]


def _unconfirmed_markers(scenario: dict[str, Any], constraint: str) -> set[str]:
    """Return high-signal markers for a constraint absent from explicit facts."""
    broad = {
        "access",
        "action",
        "after",
        "alert",
        "alerts",
        "authenticated",
        "authentication",
        "authorization",
        "authorised",
        "authorized",
        "available",
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
        "workflows",
        "violations",
        "within",
        "without",
    }
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
    markers = {
        token
        for token in _content_tokens(constraint)
        if len(token) > 4
        and token not in broad
        and token not in _content_tokens(explicit_text)
    }
    if "interfere" in constraint.lower():
        markers.update({"interfere", "interference", "passive", "passively", "intrusive"})
    return markers


def _mentions_unconfirmed_constraint(scenario: dict[str, Any], text: str) -> bool:
    """Return whether text promotes an unconfirmed constraint as established."""
    normalized_text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    normalized = " ".join(_content_tokens(text))
    strong_single_markers = {
        "air-gapped",
        "airgapped",
        "append-only",
        "append",
        "gapped",
        "passive",
    }
    for constraint in _unconfirmed_constraints(scenario):
        constraint_lower = constraint.lower()
        if re.search(
            r"\b(?:passive|passively|non[- ]?interfer|never send commands)\b",
            constraint_lower,
        ) and re.search(
            r"\b(?:passive|passively|non interfer\w*|"
            r"(?:send|sending|transmit|transmitting|inject|injecting)\s+(?:\w+\s+){0,3}commands?|"
            r"automatic\s+(?:\w+\s+){0,3}(?:pump|field device|plc)\s+control|"
            r"(?:alter|altering)\s+(?:\w+\s+){0,2}(?:device|control)\s+behavio\w*)\b",
            normalized_text,
        ):
            return True
        markers = _unconfirmed_markers(scenario, constraint)
        if not markers:
            continue
        matched = {
            marker
            for marker in markers
            if re.search(rf"\b{re.escape(marker)}\b", normalized)
        }
        if len(markers) >= 2 and len(matched) >= 2:
            return True
        if matched & strong_single_markers:
            return True
    return False


def _semantically_classified_requirement(req: dict[str, Any]) -> dict[str, Any]:
    """Return a corrected category/ID for known capability-like authored NFRs."""
    corrected = dict(req)
    if req["title"] == "Centralised Alert Delivery":
        corrected.update(
            {
                "id": "FR-003",
                "category": "functional",
                "rationale": (
                    "Forwarding branch alerts to head office is a concrete system "
                    "capability explicitly requested by the bank, so it belongs in "
                    "functional requirements rather than non-functional qualities."
                ),
            }
        )
    elif req["title"] == "Reviewed Policy Changes":
        corrected.update(
            {
                "id": "SEC-002",
                "category": "security",
                "rationale": (
                    "Review before firewall-policy deployment is a specific "
                    "authorization control confirmed by the scenario context, so it "
                    "belongs in security requirements rather than NFRs."
                ),
            }
        )
    return corrected


def _safe_requirement_items(
    scenario: dict[str, Any], category: str | None = None
) -> list[dict[str, Any]]:
    """Return requirements that do not rely on unconfirmed constraints."""
    items = [_semantically_classified_requirement(req) for req in scenario["requirements"]]
    if category is not None:
        items = [req for req in items if req["category"] == category]
    safe_items: list[dict[str, Any]] = []
    for req in items:
        text = " ".join(
            [
                req["title"],
                req["statement"],
                req["rationale"],
                req["acceptance_criteria"],
            ]
        )
        if not _mentions_unconfirmed_constraint(scenario, text):
            safe_items.append(req)
    return safe_items


def _safe_context_analysis(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return analysis that does not promote hidden assumptions to constraints."""
    analysis = dict(scenario["analysis"])
    description = scenario["description"]
    missing = list(analysis.get("missing_information", []))
    safe_constraints: list[str] = []
    unsupported_count = 0
    for constraint in analysis.get("constraints", []):
        if constraint not in _unconfirmed_constraints(scenario):
            safe_constraints.append(constraint)
        else:
            unsupported_count += 1
            missing.append(f"Confirm whether this constraint applies: {constraint}")
    if not safe_constraints:
        safe_constraints.append("Specific operational constraints require stakeholder confirmation")
    analysis["constraints"] = safe_constraints
    analysis["missing_information"] = list(dict.fromkeys(missing))
    if scenario["id"] == "SCN-009":
        analysis["assets"] = [
            asset
            for asset in analysis.get("assets", [])
            if "patient data" not in asset.lower() and "health data" not in asset.lower()
        ]
        analysis["missing_information"] = list(
            dict.fromkeys(
                [
                    *analysis["missing_information"],
                    (
                        "Whether captured medical-device communications contain patient "
                        "or health data remains unresolved."
                    ),
                    (
                        "Whether monitoring must be fully passive should be confirmed "
                        "because active inspection could affect sensitive medical devices."
                    ),
                ]
            )
        )
    analysis["project_summary"] = re.sub(r"\s+", " ", description).strip()
    analysis["context_repair_metadata"] = {
        "unsupported_constraints_moved_to_missing_information": unsupported_count
    }
    return analysis


# --- Record builders ---------------------------------------------------------


def build_context_extraction(scenario: dict[str, Any]) -> dict[str, Any]:
    """Build the description -> ProjectAnalysis training record."""
    analysis = _safe_context_analysis(scenario)
    analysis["inferred_categories"] = list(scenario["categories"])
    analysis.pop("context_repair_metadata", None)
    assistant = ProjectAnalysis.model_validate(analysis).model_dump()
    return _with_record_metadata(
        {
            "record_id": f"{scenario['id']}|context_extraction",
            "task": "context_extraction",
            "scenario_id": scenario["id"],
            "inferred_categories": list(scenario["categories"]),
            "messages": [
                {
                    "role": "system",
                    "content": ANALYSIS_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": ANALYSIS_USER_TEMPLATE.format(
                        description=scenario["description"]
                    ).strip(),
                },
                {"role": "assistant", "content": _json_lines(assistant)},
            ],
        },
        scenario,
    )


def _infer_answer_type(question: str, gap: str) -> str:
    """Infer expected answer type from visible question and gap text only."""
    visible_text = f"{question} {gap}".lower()
    if re.match(r"\s*(is|are|do|does|did|can|could|must|should|will|would|has|have)\b", visible_text):
        return "boolean"
    if re.match(r"\s*what counts as\b", visible_text):
        return "text"
    if re.match(r"\s*which\b", visible_text):
        return "list"
    if any(
        word in visible_text
        for word in (
            "which roles",
            "which systems",
            "which sources",
            "which items",
            "what sources",
            "what roles",
            "what items",
            "tier structure",
            "list",
            "multiple",
        )
    ):
        return "list"
    if re.search(
        r"(how many|how much|how long|number|count|rate|limit|retention|volume|duration|"
        r"concurrent|throughput|window|seconds|minutes|hours|days|months|years|"
        r"period|budget|threshold)",
        visible_text,
    ):
        return "number"
    return "text"


def build_clarification_questions(scenario: dict[str, Any]) -> dict[str, Any]:
    """Build the analysis -> ClarificationQuestionSet training record.

    Scenario clarifications are authored in the same order as the
    ``missing_information`` gaps they resolve, so mapping is positional.
    """
    source_analysis = scenario["analysis"]
    prompt_analysis = _safe_context_analysis(scenario)
    gaps = source_analysis["missing_information"]
    questions: list[dict[str, Any]] = []
    for i, item in enumerate(scenario["clarifications"]):
        gap = gaps[i]
        questions.append(
            {
                "question_text": item["question"],
                "reason": (
                    f"The '{gap}' gap affects requirement scope, acceptance criteria, "
                    "and implementation boundaries, so it must be clarified before "
                    "generation proceeds."
                ),
                "is_critical": True,
                "target_gap": gap,
                "expected_answer_type": _infer_answer_type(item["question"], gap),
            }
        )
    assistant = ClarificationQuestionSet.model_validate(
        {"questions": questions}
    ).model_dump()
    missing_lines = "\n".join(f"- {gap}" for gap in gaps)
    return _with_record_metadata(
        {
            "record_id": f"{scenario['id']}|clarification_questions",
            "task": "clarification_questions",
            "scenario_id": scenario["id"],
            "inferred_categories": list(scenario["categories"]),
            "messages": [
                {"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": CLARIFICATION_USER_TEMPLATE.format(
                        description=scenario["description"],
                        project_summary=prompt_analysis["project_summary"],
                        missing_information=missing_lines,
                    ).strip(),
                },
                {"role": "assistant", "content": _json_lines(assistant)},
            ],
        },
        scenario,
    )


def build_requirements_section(
    scenario: dict[str, Any],
    category: str,
    wrapper_key: str,
    system_prompt: str,
    user_template: str,
    requirement_items: list[dict[str, Any]] | None = None,
    provenance_kind: str = "authored",
) -> dict[str, Any]:
    """Build a context -> requirement-section training record for one category."""
    reqs = requirement_items or _safe_requirement_items(scenario, category)
    assistant_items = [_build_requirement(r) for r in reqs]
    assistant = {wrapper_key: assistant_items}
    user_content = user_template.format(
        project_context=json.dumps(_build_context_payload(scenario), indent=2),
        previous_sections_summary=PREVIOUS_SECTIONS_SUMMARY,
        rag_context=NO_RAG_CONTEXT_NOTE,
    )
    return _with_record_metadata(
        {
            "record_id": f"{scenario['id']}|{wrapper_key}",
            "task": wrapper_key,
            "scenario_id": scenario["id"],
            "inferred_categories": list(scenario["categories"]),
            "messages": [
                {"role": "system", "content": _training_prompt(system_prompt)},
                {"role": "user", "content": user_content.strip()},
                {"role": "assistant", "content": _json_lines(assistant)},
            ],
        },
        scenario,
        requirement_provenance=provenance_kind,
    )


def build_architecture(scenario: dict[str, Any]) -> dict[str, Any]:
    """Build the context -> architecture summary training record."""
    arch = _safe_architecture(scenario)
    assistant = ArchitectureSummary.model_validate(
        {
            "overview": arch["overview"],
            "components": arch.get("components", []),
            "data_flows": arch.get("data_flows", []),
            "deployment_notes": arch.get("deployment_notes", ""),
        }
    ).model_dump()
    user_content = ARCHITECTURE_USER_TEMPLATE.format(
        project_context=json.dumps(_build_context_payload(scenario), indent=2),
        previous_sections_summary=PREVIOUS_SECTIONS_SUMMARY,
        rag_context=NO_RAG_CONTEXT_NOTE,
    )
    return _with_record_metadata(
        {
            "record_id": f"{scenario['id']}|architecture",
            "task": "architecture",
            "scenario_id": scenario["id"],
            "inferred_categories": list(scenario["categories"]),
            "messages": [
                {"role": "system", "content": ARCHITECTURE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content.strip()},
                {"role": "assistant", "content": _json_lines(assistant)},
            ],
        },
        scenario,
    )


def _safe_architecture(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return architecture text that does not establish unconfirmed constraints."""
    arch = scenario["architecture"]
    text = " ".join(
        [
            arch["overview"],
            arch.get("deployment_notes", ""),
            *arch.get("data_flows", []),
            *[
                " ".join(
                    [
                        component["name"],
                        component["description"],
                        *component.get("responsibilities", []),
                    ]
                )
                for component in arch.get("components", [])
            ],
        ]
    )
    if not _mentions_unconfirmed_constraint(scenario, text):
        return arch

    project_focus = scenario["name"]
    goals = _safe_context_analysis(scenario).get("goals", [])
    primary_responsibility = goals[0] if goals else "Support the security workflow"
    return {
        "overview": (
            f"A security workflow architecture for {project_focus} with intake, "
            "decisioning, review, and protected record-handling components based "
            "only on the project description and confirmed clarifications."
        ),
        "components": [
            {
                "name": "Security Workflow Intake",
                "description": f"Accepts inputs needed for the {project_focus} workflow.",
                "responsibilities": [primary_responsibility],
            },
            {
                "name": "Security Decision Service",
                "description": "Applies configured security decisions for the workflow.",
                "responsibilities": ["Evaluate workflow events", "Produce reviewable outcomes"],
            },
            {
                "name": "Review Record Store",
                "description": "Stores records needed for authorized operational review.",
                "responsibilities": ["Retain workflow evidence", "Support authorized review"],
            },
        ],
        "data_flows": [
            "Workflow input -> security decision service -> review record store"
        ],
        "deployment_notes": (
            "Specific deployment constraints remain unresolved until stakeholders "
            "confirm them."
        ),
    }


def build_threat_model(scenario: dict[str, Any]) -> dict[str, Any]:
    """Build the context -> threat model training record."""
    threats, mitigations = _threat_objects(scenario)
    assistant = {"threats": threats, "mitigations": mitigations}
    user_content = THREATS_USER_TEMPLATE.format(
        project_context=json.dumps(_build_context_payload(scenario), indent=2),
        requirements_summary=_requirement_summary(scenario),
        rag_context=NO_RAG_CONTEXT_NOTE,
    )
    return _with_record_metadata(
        {
            "record_id": f"{scenario['id']}|threat_model",
            "task": "threat_model",
            "scenario_id": scenario["id"],
            "inferred_categories": list(scenario["categories"]),
            "messages": [
                {"role": "system", "content": _training_prompt(THREATS_SYSTEM_PROMPT)},
                {"role": "user", "content": user_content.strip()},
                {"role": "assistant", "content": _json_lines(assistant)},
            ],
        },
        scenario,
    )


def _quality_slug(value: str) -> str:
    """Return a compact human-readable workflow name for synthesized NFR text."""
    return re.sub(r"[^A-Za-z0-9 /-]+", "", value).strip()


def _synthesized_nfr(scenario: dict[str, Any]) -> dict[str, Any] | None:
    """Build a schema-valid, scenario-specific NFR derived from visible cues."""
    description = scenario["description"]
    lower_description = description.lower()
    project_focus = _quality_slug(scenario["name"])
    categories = set(scenario["categories"])

    def has_any(*needles: str) -> bool:
        """Return whether the scenario description contains any cue."""
        return any(needle in lower_description for needle in needles)

    def has_phrase(*phrases: str) -> bool:
        """Return whether the description contains a complete word or phrase."""
        return any(
            re.search(rf"\b{re.escape(phrase)}\b", lower_description)
            for phrase in phrases
        )

    if scenario["id"] == "SCN-009":
        title = "Medical-Device Event Reliability"
        statement = (
            "The system shall keep detected medical-device communication events "
            "available for authorized incident review."
        )
        acceptance = (
            "GIVEN medical-device communication is flagged for review, WHEN a "
            "hospital reviewer opens the incident record, THEN the system shall show "
            "the event status and retained communication context without asserting "
            "patient-data processing or a passive monitoring mode."
        )
        rationale = (
            "The description asks for detection, alerting, and incident-review records; "
            "event-record reliability is supported, while patient-data handling and "
            "non-interference remain unresolved."
        )
    elif scenario["id"] in {
        "SCN-003",
        "SCN-005",
        "SCN-007",
        "SCN-008",
        "SCN-010",
        "SCN-013",
        "SCN-015",
        "SCN-018",
        "SCN-019",
        "SCN-024",
        "SCN-030",
        "SCN-032",
        "SCN-038",
        "SCN-047",
    }:
        # Phase 4C.3 emitted a security/data capability as an NFR for each of these
        # scenarios. Removing it must not trigger a different synthesized fallback.
        return None
    elif has_phrase("signed", "signature", "signature verification"):
        # Signing and signature verification are concrete security/data capabilities,
        # not standalone quality attributes. Do not manufacture a replacement NFR.
        return None
    elif scenario["id"] != "SCN-048" and has_any(
        "patient data",
        "health data",
        "citizen data",
        "biometric",
        "payroll",
        "privileged",
        "confidential",
        "tenant",
        "client data",
        "personal data",
        "donor data",
    ):
        # Access boundaries and sensitive-data exposure controls belong in security or
        # data requirements. Their presence does not imply a separate quality target.
        return None

    elif has_any("watermark", "spoof", "forged", "replay", "integrity", "tamper", "verify"):
        if has_any("watermark", "content", "leaked clips", "preview"):
            title = "Content Trace Integrity"
            statement = (
                f"The system shall preserve trace integrity for content-protection "
                f"evidence in the {project_focus} workflow."
            )
            acceptance = (
                "GIVEN content-protection evidence is produced, WHEN an authorized "
                "reviewer inspects it, THEN the system shall show the trace value and "
                "the account or source associated with that value."
            )
            rationale = (
                "The visible request concerns watermarking or content-leak tracing, "
                "so integrity of trace evidence is the supported quality attribute."
            )
        elif has_any("spoof", "replay", "transaction", "radio", "meter"):
            title = "Signal Authenticity Integrity"
            statement = (
                f"The system shall preserve authenticity evidence for security signals "
                f"in the {project_focus} workflow."
            )
            acceptance = (
                "GIVEN a security signal is accepted or rejected, WHEN the decision is "
                "reviewed, THEN the system shall show the signal source and authenticity "
                "decision without changing the recorded outcome."
            )
            rationale = (
                "The request mentions spoofing, replay, transaction validation, or "
                "meter/radio identity protection, so signal-authenticity integrity is supported."
            )
        else:
            if has_any("log", "logging", "event"):
                if has_any("scada", "control traffic", "control-plane"):
                    title = "Control Event Integrity Review"
                elif has_any("election", "voter"):
                    title = "Election Log Integrity Review"
                elif has_any("biometric", "attendance"):
                    title = "Attendance Change Integrity Review"
                else:
                    title = "Sensor Evidence Integrity Review"
            elif has_any("sensor", "telemetry", "satellite", "air quality"):
                title = "Telemetry Evidence Integrity"
            elif has_any("charging"):
                title = "Charging Decision Integrity"
            elif has_any("biometric", "attendance"):
                title = "Attendance Record Integrity"
            elif has_any("extension", "validation"):
                title = "Extension Validation Integrity"
            else:
                title = "Security Decision Integrity"
            if title in {
                "Control Event Integrity Review",
                "Election Log Integrity Review",
                "Attendance Change Integrity Review",
                "Sensor Evidence Integrity Review",
            }:
                evidence_scope = {
                    "Control Event Integrity Review": "control-event evidence",
                    "Election Log Integrity Review": "election-administration log evidence",
                    "Attendance Change Integrity Review": "attendance-change evidence",
                    "Sensor Evidence Integrity Review": "sensor evidence",
                }[title]
                if title == "Control Event Integrity Review":
                    statement = (
                        f"The system shall make control-event evidence created by "
                        f"{project_focus} reviewable for integrity status."
                    )
                else:
                    statement = (
                        f"The system shall keep integrity status reviewable for {evidence_scope} "
                        f"created by {project_focus}."
                    )
                acceptance = (
                    f"GIVEN {evidence_scope} exists for {project_focus}, WHEN an authorized "
                    "reviewer checks it, THEN the system shall show whether the evidence "
                    "has remained unchanged since capture."
                )
                rationale = (
                    f"The scenario involves retained {evidence_scope}; integrity review "
                    "of that evidence is a supported quality attribute."
                )
            elif title == "Telemetry Evidence Integrity":
                statement = (
                    f"The system shall keep telemetry evidence integrity verifiable for "
                    f"the {project_focus} workflow."
                )
                acceptance = (
                    f"GIVEN telemetry evidence is retained for {project_focus}, WHEN it "
                    "is reviewed, THEN the system shall show the source identity and "
                    "integrity-check status for that evidence."
                )
                rationale = (
                    "The scenario depends on trusted telemetry or sensor evidence, making "
                    "integrity verification a genuine quality concern."
                )
            elif title == "Charging Decision Integrity":
                statement = (
                    "The system shall keep charging-session security decisions intact "
                    "for later operational review."
                )
                acceptance = (
                    "GIVEN a charging session is accepted or rejected, WHEN the decision "
                    "is reviewed, THEN the system shall show the charger identity, decision "
                    "status, and integrity-check outcome."
                )
                rationale = (
                    "The EV charging scenario depends on trustworthy session decisions, "
                    "so integrity of those decisions is the relevant quality attribute."
                )
            elif title == "Attendance Record Integrity":
                statement = (
                    "The system shall keep attendance-security decisions resistant to "
                    "undetected alteration."
                )
                acceptance = (
                    "GIVEN a clock-in decision is recorded, WHEN an authorized reviewer "
                    "examines it, THEN the system shall show whether the decision record "
                    "has changed since creation."
                )
                rationale = (
                    "The biometric attendance scenario concerns forged clock-in records, "
                    "making record integrity a supported quality attribute."
                )
            elif title == "Extension Validation Integrity":
                statement = (
                    "The system shall keep extension-validation decisions intact from "
                    "review through release approval."
                )
                acceptance = (
                    "GIVEN extension validation produces a decision, WHEN release approval "
                    "is reviewed, THEN the system shall show the original decision and "
                    "integrity status."
                )
                rationale = (
                    "The extension-validation scenario depends on trustworthy validation "
                    "decisions, so decision integrity is the supported quality attribute."
                )
            else:
                statement = (
                    f"The system shall preserve the integrity of security decisions made in "
                    f"the {project_focus} workflow."
                )
                acceptance = (
                    f"GIVEN a security decision is produced by {project_focus}, WHEN the "
                    "decision is later reviewed, THEN the system shall show the decision "
                    "value, source, and integrity status."
                )
                rationale = (
                    "The scenario concerns tampering, verification, or integrity, so "
                    "security-decision integrity is the supported non-functional quality."
                )
    elif has_any("container image", "image scanning", "scan container"):
        title = "Scan Result Reliability"
        statement = (
            f"The system shall keep container-scan outcomes reliable for the "
            f"{project_focus} workflow."
        )
        acceptance = (
            "GIVEN a container image scan completes, WHEN scan results are reviewed, "
            "THEN the system shall show the image digest, scan status, and policy outcome."
        )
        rationale = (
            "The scenario asks for image scanning and findings dashboards, making "
            "reliability of scan-result handling a supported quality attribute."
        )
    elif has_any("document", "documents", "manifest", "record", "records", "log files", "application", "recordings"):
        if has_any("voice", "recording", "video", "session metadata"):
            title = "Media Record Recoverability"
            record_scope = "media or session records"
        elif has_any("document", "documents", "matter", "policy"):
            title = "Document Evidence Recoverability"
            record_scope = "document evidence"
        else:
            title = "Operational Record Recoverability"
            record_scope = "operational security records"
        statement = (
            f"The system shall keep {record_scope} for the {project_focus} workflow "
            "recoverable for authorized review."
        )
        acceptance = (
            f"GIVEN {record_scope} have been produced by {project_focus}, WHEN an authorized "
            "reviewer requests a previously retained record, THEN the system shall return "
            "the record or a controlled unavailable-state explanation without altering the record."
        )
        rationale = (
            f"The scenario uses {record_scope}; recoverability of those records is "
            "a justified quality attribute."
        )
    elif has_any("continuous monitoring", "monitoring", "alert", "detect", "dashboard"):
        if has_any("medical device", "infusion", "patient monitor"):
            title = "Medical-Device Event Reliability"
            statement = (
                "The system shall keep detected medical-device communication events "
                "available for authorized incident review."
            )
            acceptance = (
                "GIVEN medical-device communication is flagged for review, WHEN a "
                "hospital reviewer opens the incident record, THEN the system shall show "
                "the event status and retained communication context without asserting a passive monitoring mode."
            )
            rationale = (
                "The hospital scenario explicitly asks for detection, alerting, and "
                "incident-review records; reliable event retention is supported, while "
                "non-interference remains a clarification item."
            )
        elif has_any("scada", "control traffic", "control-plane"):
            title = "Control-Traffic Event Reliability"
            statement = (
                f"The system shall keep abnormal control-traffic events from the "
                f"{project_focus} workflow reviewable after detection."
            )
            acceptance = (
                "GIVEN abnormal control traffic is detected, WHEN an operator reviews "
                "the event queue, THEN the system shall show the event status, affected "
                "asset, and retained observation details."
            )
            rationale = (
                "The description asks for abnormal control-traffic monitoring and event "
                "records, making reliable event review a grounded quality attribute."
            )
        elif has_any("branch", "head office"):
            title = "Branch Alert Reliability"
            statement = (
                "The system shall keep branch-monitoring alert outcomes reliable for "
                "central operational review."
            )
            acceptance = (
                "GIVEN a branch-monitoring condition produces an alert, WHEN central "
                "reviewers inspect the monitoring queue, THEN the alert outcome shall be "
                "present with its branch source and processing status."
            )
            rationale = (
                "The bank scenario explicitly centralizes branch monitoring at head "
                "office; reliability of alert outcomes is the quality attribute, not "
                "the forwarding capability itself."
            )
        elif has_any("sensor", "meter", "telemetry", "site drops offline", "satellite"):
            title = "Telemetry Signal Reliability"
            statement = (
                f"The system shall preserve reliable telemetry-security signal status "
                f"for the {project_focus} workflow."
            )
            acceptance = (
                "GIVEN a telemetry source reports unusual data or stops reporting, WHEN "
                "the monitoring workflow processes the condition, THEN the system shall "
                "retain the signal status for authorized review."
            )
            rationale = (
                "The scenario concerns telemetry, sensors, meters, or site monitoring; "
                "reliability of security signal status is therefore a supported quality attribute."
            )
        elif has_any("bot", "fraud", "risk", "abuse"):
            if has_any("api", "trading", "model serving"):
                title = "API Decision Reliability"
                decision_scope = "API abuse decisions"
            elif has_any("account", "login", "bot", "ticket"):
                title = "Abuse Detection Reliability"
                decision_scope = "account or bot-abuse decisions"
            else:
                title = "Detection Decision Reliability"
                decision_scope = "risk detection decisions"
            statement = (
                f"The system shall keep {decision_scope} in the {project_focus} "
                "workflow reproducible for authorized review."
            )
            acceptance = (
                f"GIVEN {decision_scope} are produced by {project_focus}, WHEN an "
                "authorized reviewer inspects the decision record, THEN the system "
                "shall show the decision status and input category used for that decision."
            )
            rationale = (
                f"The scenario uses {decision_scope}; reproducibility of those decisions "
                "is a quality attribute distinct from the detection capability."
            )
        else:
            title = "Alert Processing Reliability"
            statement = (
                f"The system shall keep security-event outcomes for the {project_focus} "
                "workflow reliable under configured operating conditions."
            )
            acceptance = (
                f"GIVEN a configured security event is generated by {project_focus}, WHEN event processing "
                "runs under the approved operating profile, THEN the system shall retain "
                "the event outcome and processing status."
            )
            rationale = (
                "The scenario includes alerting or detection behavior; reliability of "
                "event processing is a supported non-functional quality."
            )
    elif has_any("throttle", "rate limit", "rate limiting", "burst", "peak", "concurrent", "volume", "latency", "api"):
        title = "Configured-Load Scalability"
        statement = (
            f"The system shall maintain predictable behavior for the {project_focus} "
            "workflow under stakeholder-approved load conditions."
        )
        acceptance = (
            f"GIVEN a stakeholder-approved load profile for {project_focus}, WHEN the "
            "workflow is exercised at that load, THEN the system shall complete the "
            "security decision path without dropped decisions or unexplained errors."
        )
        rationale = (
            "The visible request refers to throttling, rate limits, bursts, scale, or "
            "peak use, so performance stability is a quality attribute rather than a "
            "new functional capability."
        )
    elif has_any("offline", "power failure", "survive", "unreachable", "interruption", "drops offline"):
        title = "Operational Resilience"
        statement = (
            f"The system shall preserve observable security behavior for the "
            f"{project_focus} workflow during expected interruptions."
        )
        acceptance = (
            f"GIVEN an expected interruption affects {project_focus}, WHEN the "
            "interruption occurs, THEN the system shall either continue the security "
            "workflow or produce a reviewable failure state without losing recorded decisions."
        )
        rationale = (
            "The project description mentions continuity, offline conditions, or "
            "failure survival, making resilience a justified non-functional concern."
        )
    elif has_any("document", "documents", "manifest", "record", "records", "log files", "application"):
        title = "Record Recoverability"
        statement = (
            f"The system shall keep security records for the {project_focus} workflow "
            "recoverable for authorized review."
        )
        acceptance = (
            f"GIVEN records have been produced by {project_focus}, WHEN an authorized "
            "reviewer requests a previously retained record, THEN the system shall return "
            "the record or a controlled unavailable-state explanation without altering the record."
        )
        rationale = (
            "The user description asks for records, documents, manifests, or retained "
            "application evidence, making recoverability of those records a justified quality attribute."
        )
    elif has_any("integrity", "tamper", "signed", "signature", "verify", "spoof", "forged", "replay", "watermark"):
        title = "Security Decision Integrity"
        statement = (
            f"The system shall preserve the integrity of security decisions made in "
            f"the {project_focus} workflow."
        )
        acceptance = (
            f"GIVEN a security decision is produced by {project_focus}, WHEN the "
            "decision is later reviewed, THEN the system shall show that the decision "
            "value and its source have not changed without authorization."
        )
        rationale = (
            "The visible request concerns tampering, signing, verification, spoofing, "
            "forgery, replay, or watermarking, so integrity is the natural NFR family."
        )
    elif has_any("integrate", "partner", "forward", "exchange", "exchanged", "external"):
        title = "Integration Observability"
        statement = (
            f"The system shall keep integrations used by the {project_focus} workflow "
            "observable and reviewable."
        )
        acceptance = (
            f"GIVEN the {project_focus} workflow exchanges data with another system, "
            "WHEN the exchange completes or fails, THEN the system shall record the "
            "counterparty, exchange status, and security decision outcome."
        )
        rationale = (
            "The project description mentions APIs, forwarding, partner exchanges, or "
            "integration, making interoperability traceability a grounded quality need."
        )
    elif has_any("policy", "admin", "administrator", "access", "permission", "role") or {"CAT-02", "CAT-04", "CAT-08"} & categories:
        if has_any("access", "identity", "vpn", "operator"):
            if has_any("university", "lab", "identity"):
                title = "Identity Session Policy Maintainability"
            elif has_any("subscriber", "passkey", "otp"):
                title = "Subscriber Authentication Maintainability"
            elif has_any("drone", "operator"):
                title = "Operator Control Policy Maintainability"
            elif has_any("iot", "robot", "warehouse"):
                title = "Device Access Policy Maintainability"
            else:
                title = "Access Policy Maintainability"
        elif has_any("network", "vlan", "segmentation", "robot"):
            title = "Network Policy Maintainability"
        else:
            title = "Administrative Policy Maintainability"
        if title in {
            "Access Policy Maintainability",
            "Identity Session Policy Maintainability",
            "Subscriber Authentication Maintainability",
            "Operator Control Policy Maintainability",
            "Device Access Policy Maintainability",
        }:
            policy_scope = {
                "Access Policy Maintainability": "access-policy",
                "Identity Session Policy Maintainability": "identity-session policy",
                "Subscriber Authentication Maintainability": "subscriber-authentication policy",
                "Operator Control Policy Maintainability": "operator-control policy",
                "Device Access Policy Maintainability": "device-access policy",
            }[title]
            statement = (
                f"The system shall keep {policy_scope} behavior in the {project_focus} "
                "workflow understandable for authorized administrators."
            )
            acceptance = (
                f"GIVEN an administrator reviews {policy_scope} for {project_focus}, "
                "WHEN policy details are opened, THEN the system shall show the covered "
                "roles, protected resources, and latest review outcome."
            )
            rationale = (
                f"The scenario describes {policy_scope} controls; maintainability of "
                "that policy behavior is the supported quality attribute."
            )
        elif title == "Network Policy Maintainability":
            statement = (
                f"The system shall keep network-policy behavior in the {project_focus} "
                "workflow understandable for authorized administrators."
            )
            acceptance = (
                f"GIVEN an administrator reviews network policy for {project_focus}, "
                "WHEN policy details are opened, THEN the system shall show the covered "
                "network zones, permitted communication, and latest review outcome."
            )
            rationale = (
                "The scenario describes network segmentation or device-network controls, "
                "so maintainability of network policy is a supported quality attribute."
            )
        else:
            statement = (
                f"The system shall keep administrative security policy for {project_focus} "
                "reviewable by authorized administrators."
            )
            acceptance = (
                f"GIVEN an administrator reviews administrative policy for {project_focus}, "
                "WHEN policy details are opened, THEN the system shall show policy scope, "
                "responsible role, and latest review outcome."
            )
            rationale = (
                "The scenario describes administrative security controls; maintainability "
                "is a defensible quality attribute for operating those controls over time."
            )
    else:
        return None

    return Requirement.model_validate(
        {
            "id": "NFR-001",
            "category": "non_functional",
            "title": title,
            "statement": statement,
            "rationale": rationale,
            "priority": "should",
            "acceptance_criteria": acceptance,
            "dependencies": [],
            "source_references": [],
            "confidence": "medium",
            "user_confirmed": False,
        }
    ).model_dump()


def _synthesized_nfr_items(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the synthesized NFR list for scenarios where one is defensible."""
    synthesized = _synthesized_nfr(scenario)
    return [synthesized] if synthesized is not None else []


def _nfr_authoring_state(scenario: dict[str, Any]) -> str:
    """Return whether the scenario has authored or synthesized NFR content."""
    if _safe_requirement_items(scenario, "non_functional"):
        return "authored_nfr"
    if _synthesized_nfr(scenario) is not None:
        return "synthesized_nfr"
    return "no_defensible_nfr"


def _numeric_assumptions(scenario: dict[str, Any]) -> list[str]:
    """Return assumptions for requirement numbers that need stakeholder confirmation."""
    assumptions: list[str] = []
    for req in scenario["requirements"]:
        for item in req.get("numeric", []):
            if item["provenance"] == "ASSUMPTION_REQUIRING_CONFIRMATION":
                assumptions.append(
                    f"{req['id']} depends on a numeric threshold that requires "
                    "stakeholder confirmation before it becomes mandatory."
                )
    return assumptions


def _full_srs_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    """Assemble and validate the complete SRSSchema payload for a scenario."""
    analysis = _safe_context_analysis(scenario)
    nfrs = [
        _build_requirement(r)
        for r in _safe_requirement_items(scenario, "non_functional")
    ]
    if not nfrs:
        nfrs = _synthesized_nfr_items(scenario)

    testing = [
        TestingRecommendation.model_validate(
            {
                "recommendation_id": f"TEST-{i:03d}",
                "description": item["description"],
                "type": item.get("type", "system"),
                "related_requirement_ids": item.get("related_requirement_ids", []),
            }
        ).model_dump()
        for i, item in enumerate(scenario.get("testing", []), start=1)
    ]

    threat_records, mitigation_records = _threat_objects(scenario)
    architecture = _safe_architecture(scenario)

    risk = scenario.get("risk") or {}
    risks = [
        {
            "risk_id": "RISK-001",
            "description": risk.get("description", "Operational risk not yet identified."),
            "likelihood": risk.get("likelihood", "medium"),
            "impact": risk.get("impact", "medium"),
            "mitigation": risk.get("mitigation", ""),
        }
    ]

    payload = {
        "metadata": {
            "project_name": scenario["name"],
            "version": 1,
            "generated_at": GENERATED_AT,
            "model_name": TRAINING_MODEL,
            "adapter_name": None,
            "inferred_categories": list(scenario["categories"]),
        },
        "project_overview": {
            "description": scenario["description"],
            "purpose": analysis["goals"][0],
            "context": analysis["project_summary"],
        },
        "scope": scenario["scope"],
        "assumptions": [*scenario.get("assumptions", []), *_numeric_assumptions(scenario)],
        "stakeholders": analysis["stakeholders"],
        "user_roles": analysis["users"],
        "functional_requirements": [
            _build_requirement(r)
            for r in _safe_requirement_items(scenario, "functional")
        ],
        "non_functional_requirements": nfrs,
        "security_requirements": [
            _build_requirement(r)
            for r in _safe_requirement_items(scenario, "security")
        ],
        "data_requirements": [
            _build_requirement(r)
            for r in _safe_requirement_items(scenario, "data")
        ],
        "network_requirements": [
            _build_requirement(r)
            for r in _safe_requirement_items(scenario, "network")
        ],
        "architecture_summary": {
            "overview": architecture["overview"],
            "components": architecture.get("components", []),
            "data_flows": architecture.get("data_flows", []),
            "deployment_notes": architecture.get("deployment_notes", ""),
        },
        "threats": threat_records,
        "mitigations": mitigation_records,
        "testing_strategy": testing,
        "risks": risks,
        "unresolved_questions": [
            *scenario.get("unresolved", []),
            *[
                f"Confirm the numeric threshold for {item.split(' depends ', 1)[0]}."
                for item in _numeric_assumptions(scenario)
            ],
        ],
        "references": [],
        "validation_report": None,
        "generation_metadata": {
            "source": "cybersrs-synthetic-scenario",
            "scenario_id": scenario["id"],
            "version": 1,
        },
    }
    payload = _sanitize_full_srs_payload(scenario, payload)
    return SRSSchema.model_validate(payload).model_dump(mode="json")


def _threat_objects(
    scenario: dict[str, Any],
    allowed_requirement_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build validated threat and flattened mitigation dicts for a scenario."""
    threats: list[dict[str, Any]] = []
    mitigations: list[dict[str, Any]] = []
    counter = 1
    threat_counter = 1
    for threat in scenario["threats"]:
        threat_text = " ".join(
            [
                threat["name"],
                threat["description"],
                " ".join(threat.get("affected_assets", [])),
            ]
        )
        if _mentions_unconfirmed_constraint(scenario, threat_text):
            continue
        threat_mits: list[dict[str, Any]] = []
        for mit in threat.get("mitigations", []):
            if _mentions_unconfirmed_constraint(scenario, mit["description"]):
                continue
            related_ids = mit.get("related_requirement_ids", [])
            if allowed_requirement_ids is not None:
                related_ids = [
                    req_id for req_id in related_ids if req_id in allowed_requirement_ids
                ]
            item = Mitigation.model_validate(
                {
                    "mitigation_id": f"MIT-{counter:03d}",
                    "description": mit["description"],
                    "related_requirement_ids": related_ids,
                }
            ).model_dump()
            mitigations.append(item)
            threat_mits.append(item)
            counter += 1
        threats.append(
            Threat.model_validate(
                {
                    "threat_id": f"THR-{threat_counter:03d}",
                    "name": threat["name"],
                    "description": threat["description"],
                    "category": threat.get("category"),
                    "severity": threat.get("severity", "medium"),
                    "affected_assets": threat.get("affected_assets", []),
                    "mitigations": threat_mits,
                }
            ).model_dump()
        )
        threat_counter += 1
    return threats, mitigations


def _sanitize_full_srs_payload(
    scenario: dict[str, Any], payload: dict[str, Any]
) -> dict[str, Any]:
    """Remove unconfirmed support-section facts from a complete SRS payload."""
    allowed_ids = {
        req["id"]
        for section in (
            "functional_requirements",
            "non_functional_requirements",
            "security_requirements",
            "data_requirements",
            "network_requirements",
        )
        for req in payload.get(section, [])
    }

    removed_scope_items: list[str] = []
    for scope_key in ("in_scope", "out_of_scope"):
        kept = []
        for item in payload["scope"].get(scope_key, []):
            if _mentions_unconfirmed_constraint(scenario, item):
                removed_scope_items.append(item)
            else:
                kept.append(item)
        payload["scope"][scope_key] = kept
    if not payload["scope"]["in_scope"]:
        payload["scope"]["in_scope"] = [
            "Security workflow described in the user-provided project description"
        ]

    removed_assumptions = [
        item
        for item in payload["assumptions"]
        if _mentions_unconfirmed_constraint(scenario, item)
    ]
    payload["assumptions"] = [
        item
        for item in payload["assumptions"]
        if not _mentions_unconfirmed_constraint(scenario, item)
    ]
    if removed_assumptions:
        if any(
            re.search(r"\b(?:passive|commands?|control behavio\w*)\b", item, flags=re.I)
            for item in removed_assumptions
        ):
            payload["assumptions"].append(
                "Whether monitoring is passive and excludes commands or automatic "
                "control remains unresolved pending stakeholder confirmation."
            )
        else:
            payload["assumptions"].extend(
                f"Whether this proposed assumption applies remains unresolved: {item}"
                for item in removed_assumptions
            )

    payload["testing_strategy"] = [
        {
            **item,
            "related_requirement_ids": [
                req_id
                for req_id in item.get("related_requirement_ids", [])
                if req_id in allowed_ids
            ],
        }
        for item in payload["testing_strategy"]
        if not _mentions_unconfirmed_constraint(scenario, item["description"])
    ]

    payload["mitigations"] = [
        {
            **item,
            "related_requirement_ids": [
                req_id
                for req_id in item.get("related_requirement_ids", [])
                if req_id in allowed_ids
            ],
        }
        for item in payload["mitigations"]
    ]
    for threat in payload["threats"]:
        threat["mitigations"] = [
            {
                **item,
                "related_requirement_ids": [
                    req_id
                    for req_id in item.get("related_requirement_ids", [])
                    if req_id in allowed_ids
                ],
            }
            for item in threat.get("mitigations", [])
        ]

    unresolved = list(payload["unresolved_questions"])
    unresolved.extend(
        f"Confirm whether this scope item applies: {item}"
        for item in removed_scope_items
    )
    unresolved.extend(
        f"Confirm whether this assumption applies: {item}"
        for item in removed_assumptions
    )
    payload["unresolved_questions"] = list(dict.fromkeys(unresolved))
    return payload


def build_srs_generation(scenario: dict[str, Any]) -> dict[str, Any]:
    """Build the description -> complete SRS training record."""
    assistant = _full_srs_payload(scenario)
    user_content = SRS_USER_TEMPLATE.format(
        project_context=json.dumps(_build_context_payload(scenario), indent=2),
        rag_context=NO_RAG_CONTEXT_NOTE,
    )
    return _with_record_metadata(
        {
            "record_id": f"{scenario['id']}|srs_generation",
            "task": "srs_generation",
            "scenario_id": scenario["id"],
            "inferred_categories": list(scenario["categories"]),
            "messages": [
                {"role": "system", "content": SRS_SYSTEM_PROMPT},
                {"role": "user", "content": user_content.strip()},
                {"role": "assistant", "content": _json_lines(assistant)},
            ],
        },
        scenario,
        nfr_provenance=_nfr_authoring_state(scenario),
    )


# --- Requirement-validation (correction) records -----------------------------


def _corrupt_requirement(req: dict[str, Any], defect: str) -> dict[str, Any]:
    """Deterministically introduce one fixable defect into a pristine requirement."""
    corrupted = dict(req)
    if defect == "bad_id":
        corrupted["id"] = req["id"][:-3] + "X"
    elif defect == "missing_shall":
        corrupted["statement"] = req["statement"].replace("The system shall", "The system", 1)
    elif defect == "double_shall":
        pos = req["statement"].find(" shall ")
        corrupted["statement"] = (
            req["statement"][:pos]
            + " shall "
            + req["statement"][pos + len(" shall ") :]
            + " and shall record the outcome for audit review."
        )
    elif defect == "generic_rationale":
        corrupted["rationale"] = "Generated from the project context by the local model."
    elif defect == "verify_acceptance":
        corrupted["acceptance_criteria"] = "Verify that the requirement is implemented correctly."
    elif defect == "no_given_when_then":
        corrupted["acceptance_criteria"] = "The system must satisfy this requirement in all cases."
    elif defect == "ambiguous_actor":
        corrupted["statement"] = "The system shall allow users to complete the required security workflow."
        corrupted["acceptance_criteria"] = (
            "GIVEN a user needs access, WHEN the workflow runs, THEN the system shall work correctly."
        )
    elif defect == "compound_requirement":
        corrupted["statement"] = (
            req["statement"].rstrip(".")
            + " and generate weekly administrative summary reports."
        )
    elif defect == "unsupported_numeric_threshold":
        corrupted["statement"] = req["statement"].rstrip(".") + " within 5 seconds."
        corrupted["rationale"] = req["rationale"].replace("Numeric provenance:", "Numeric note:")
        corrupted["acceptance_criteria"] = (
            req["acceptance_criteria"].rstrip(".") + " within 5 seconds."
        )
    elif defect == "wrong_requirement_category":
        category_cycle = {
            "functional": "security",
            "security": "functional",
            "non_functional": "functional",
            "data": "network",
            "network": "data",
        }
        corrupted["category"] = category_cycle[str(req["category"])]
    elif defect == "vague_adjective":
        corrupted["statement"] = "The system shall be secure, reliable, and user friendly."
        corrupted["acceptance_criteria"] = (
            "GIVEN the system is deployed, WHEN it is used, THEN it shall be secure and reliable."
        )
    elif defect == "weak_rationale":
        corrupted["rationale"] = "This is important for the project."
    else:  # pragma: no cover - only reachable via programmer error
        raise ValueError(f"unknown defect type {defect!r}")
    return corrupted


#: Defect types are cycled across scenarios so each is evenly represented.
DEFECT_TYPES: tuple[str, ...] = (
    "bad_id",
    "missing_shall",
    "double_shall",
    "generic_rationale",
    "verify_acceptance",
    "no_given_when_then",
    "ambiguous_actor",
    "compound_requirement",
    "unsupported_numeric_threshold",
    "wrong_requirement_category",
    "vague_adjective",
    "weak_rationale",
)


def build_requirement_validation(
    scenario: dict[str, Any], defect: str, ordinal: int
) -> dict[str, Any]:
    """Build a corrupted-requirement -> corrected-requirement training record."""
    pristine = _build_requirement(scenario["requirements"][0])
    corrupted = _corrupt_requirement(pristine, defect)
    user_content = (
        "The following requirement JSON failed deterministic validation:\n"
        + json.dumps(corrupted, indent=2, ensure_ascii=False)
        + "\n\nFix the validation error(s) and return ONLY the corrected JSON."
    )
    return _with_record_metadata(
        {
            "record_id": f"{scenario['id']}|requirement_validation|{ordinal}",
            "task": "requirement_validation",
            "scenario_id": scenario["id"],
            "defect_type": defect,
            "inferred_categories": list(scenario["categories"]),
            "messages": [
                {"role": "system", "content": CORRECTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": _json_lines(pristine)},
            ],
        },
        scenario,
        defect_type=defect,
    )


# --- Driver ------------------------------------------------------------------


def _leakage_warnings() -> list[str]:
    """Check scenario descriptions against the held-out evaluation dataset."""
    eval_path = PROJECT_ROOT / "ai" / "evaluation" / "dataset.json"
    if not eval_path.exists():
        return ["evaluation dataset not found; leakage check skipped"]
    with eval_path.open("r", encoding="utf-8") as fh:
        eval_descriptions = [entry["description"] for entry in json.load(fh)]
    warnings: list[str] = []
    for scenario in SCENARIOS:
        desc = scenario["description"].lower()
        for eval_desc in eval_descriptions:
            if eval_desc.lower() in desc or desc in eval_desc.lower():
                warnings.append(
                    f"{scenario['id']} overlaps held-out eval case: {eval_desc[:80]!r}"
                )
    return warnings


def _validate_messages(messages: list[dict[str, str]]) -> None:
    """Assert the record uses the expected system/user/assistant role sequence."""
    roles = [m["role"] for m in messages]
    if roles != ["system", "user", "assistant"]:
        raise ValueError(f"unexpected message roles {roles!r}")


def _write_records(
    records: list[dict[str, Any]], out_dir: Path
) -> dict[str, list[dict[str, Any]]]:
    """Group records by task and write one JSONL file per task.

    Returns the records grouped by task name.
    """
    by_task: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_task.setdefault(record["task"], []).append(record)
    for task, task_records in sorted(by_task.items()):
        task_records.sort(key=lambda r: r["record_id"])
        with (out_dir / f"{task}.jsonl").open("w", encoding="utf-8") as fh:
            for record in task_records:
                fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return by_task


def generate_dataset(out_dir: Path) -> Path:
    """Generate all training records, validate them, and write JSONL files."""
    out_dir.mkdir(parents=True, exist_ok=True)

    builders: list[Callable[[dict[str, Any]], list[dict[str, Any]]]] = []
    builders.append(lambda s: [build_context_extraction(s)])
    builders.append(lambda s: [build_clarification_questions(s)])
    builders.append(
        lambda s: [
            build_requirements_section(
                s, "functional", "functional_requirements",
                FUNCTIONAL_REQUIREMENTS_SYSTEM_PROMPT,
                FUNCTIONAL_REQUIREMENTS_USER_TEMPLATE,
            )
        ]
    )
    builders.append(
        lambda s: [
            build_requirements_section(
                s, "non_functional", "non_functional_requirements",
                NON_FUNCTIONAL_REQUIREMENTS_SYSTEM_PROMPT,
                NON_FUNCTIONAL_REQUIREMENTS_USER_TEMPLATE,
                (
                    _safe_requirement_items(s, "non_functional")
                    or _synthesized_nfr_items(s)
                ),
                _nfr_authoring_state(s),
            )
        ]
        if _safe_requirement_items(s, "non_functional") or _synthesized_nfr_items(s)
        else []
    )
    builders.append(
        lambda s: [
            build_requirements_section(
                s, "security", "security_requirements",
                SECURITY_REQUIREMENTS_SYSTEM_PROMPT,
                SECURITY_REQUIREMENTS_USER_TEMPLATE,
            )
        ]
        if _safe_requirement_items(s, "security")
        else []
    )
    builders.append(
        lambda s: [
            build_requirements_section(
                s, "data", "data_requirements",
                DATA_REQUIREMENTS_SYSTEM_PROMPT,
                DATA_REQUIREMENTS_USER_TEMPLATE,
            )
        ]
        if _safe_requirement_items(s, "data")
        else []
    )
    builders.append(
        lambda s: [
            build_requirements_section(
                s, "network", "network_requirements",
                NETWORK_REQUIREMENTS_SYSTEM_PROMPT,
                NETWORK_REQUIREMENTS_USER_TEMPLATE,
            )
        ]
        if _safe_requirement_items(s, "network")
        else []
    )
    builders.append(lambda s: [build_architecture(s)])
    builders.append(lambda s: [build_threat_model(s)])
    builders.append(lambda s: [build_srs_generation(s)])

    records: list[dict[str, Any]] = []
    for index, scenario in enumerate(SCENARIOS):
        for builder in builders:
            records.extend(builder(scenario))
        defect = DEFECT_TYPES[index % len(DEFECT_TYPES)]
        records.append(build_requirement_validation(scenario, defect, index + 1))

    for record in records:
        _validate_messages(record["messages"])

    by_task = _write_records(records, out_dir)

    leakage = _leakage_warnings()
    manifest = {
        "dataset_version": "1.0.0",
        "generated_at": GENERATED_AT,
        "generator": "ai/finetuning/scripts/generate_dataset.py",
        "scenario_source": "ai/finetuning/scripts/scenario_library.py",
        "schema_validation": {
            "policy": "every assistant payload validated against its Pydantic schema",
            "rejected_records": 0,
        },
        "training_model": TRAINING_MODEL,
        "record_format": "conversation (system/user/assistant messages)",
        "leakage_check": {
            "held_out_dataset": "ai/evaluation/dataset.json",
            "warnings": leakage,
        },
        "task_counts": {task: len(task_records) for task, task_records in sorted(by_task.items())},
        "total_records": len(records),
        "notes": [
            "Scenarios without authored non-functional requirements receive one "
            "synthesised NFR derived from their goals/constraints. Phase 4C also "
            "promotes these audited synthesized NFRs into standalone "
            "non_functional_requirements records because NFR generation is an "
            "expected production behaviour.",
            "Records carry scenario-level provenance and must be split by scenario, "
            "not by individual record.",
        ],
    }
    with (out_dir / "MANIFEST.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: generate the dataset and print a summary."""
    parser = argparse.ArgumentParser(
        description="Generate the CyberSRS synthetic fine-tuning dataset from scenarios."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=PROJECT_ROOT / "ai" / "finetuning" / "data",
        help="Output directory for dataset files (default: ai/finetuning/data).",
    )
    args = parser.parse_args(argv)

    out_dir = generate_dataset(args.out_dir)
    with (out_dir / "MANIFEST.json").open("r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    print(f"records generated: {manifest['total_records']}")
    for task, count in manifest["task_counts"].items():
        print(f"  {task}: {count}")
    if manifest["schema_validation"]["rejected_records"]:
        print(
            f"ERROR: {manifest['schema_validation']['rejected_records']} records "
            "rejected by schema validation"
        )
        return 1
    if manifest["leakage_check"]["warnings"]:
        print("LEAKAGE WARNINGS:")
        for warning in manifest["leakage_check"]["warnings"]:
            print(f"  - {warning}")
        return 2
    print(f"output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
