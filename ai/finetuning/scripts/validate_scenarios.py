"""Static validation of the scenario library.

Run standalone: python ai/finetuning/scripts/validate_scenarios.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai.finetuning.scripts.scenario_library import SCENARIOS  # noqa: E402

VALID_CATEGORIES = {"functional", "non_functional", "security", "data", "network"}
VALID_PRIORITIES = {"must", "should", "could"}
ID_PREFIXES = ("FR-", "SEC-", "NFR-", "DATA-", "NET-")


def main() -> int:
    errors: list[str] = []
    cat_counts: Counter[str] = Counter()

    for s in SCENARIOS:
        sid = s["id"]
        ana = s["analysis"]
        for field in ("stakeholders", "assets", "users", "constraints", "goals", "project_summary"):
            if not ana.get(field):
                errors.append(f"{sid}: analysis.{field} empty")
        for field in ("stakeholders", "assets", "users"):
            for item in ana.get(field, []):
                if not item.strip():
                    errors.append(f"{sid}: analysis.{field} contains empty string")
        for c in s["categories"]:
            cat_counts[c] += 1

        if len(s["clarifications"]) < 2:
            errors.append(f"{sid}: fewer than 2 clarifications")

        req_ids = [r["id"] for r in s["requirements"]]
        if len(req_ids) != len(set(req_ids)):
            errors.append(f"{sid}: duplicate requirement ids")
        if len(s["requirements"]) < 3:
            errors.append(f"{sid}: fewer than 3 requirements")

        for r in s["requirements"]:
            rid = r["id"]
            st = r["statement"]
            if not rid.startswith(ID_PREFIXES):
                errors.append(f"{sid}/{rid}: bad id prefix")
            if st.count(" shall ") != 1:
                errors.append(f"{sid}/{rid}: statement does not contain exactly one ' shall '")
            if "The system shall" not in st:
                errors.append(f"{sid}/{rid}: statement missing 'The system shall'")
            if r["category"] not in VALID_CATEGORIES:
                errors.append(f"{sid}/{rid}: invalid category {r['category']}")
            if r["priority"] not in VALID_PRIORITIES:
                errors.append(f"{sid}/{rid}: invalid priority")
            ac = r["acceptance_criteria"]
            for marker in ("GIVEN", "WHEN", "THEN"):
                if marker not in ac:
                    errors.append(f"{sid}/{rid}: acceptance_criteria missing {marker}")
            if "Verify that" in ac.lower():
                errors.append(f"{sid}/{rid}: forbidden 'Verify that' in acceptance_criteria")
            if "Generated from the project context" in r["rationale"]:
                errors.append(f"{sid}/{rid}: forbidden generic rationale")

        arch = s["architecture"]
        if not arch["overview"] or not arch["components"]:
            errors.append(f"{sid}: architecture incomplete")
        if not s["threats"]:
            errors.append(f"{sid}: no threats defined")

    print(f"scenarios validated: {len(SCENARIOS)}")
    print(f"category distribution: {dict(sorted(cat_counts.items()))}")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("all scenario checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
