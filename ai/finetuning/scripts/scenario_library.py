"""Aggregated scenario library for the CyberSRS QLoRA training dataset.

Combines all scenario banks into a single ordered list with id uniqueness
guarantees. Every scenario is a dict following the schema documented in
``scenario_bank_a.py``.
"""

from __future__ import annotations

from typing import Any

from .scenario_bank_a import SCENARIOS_A
from .scenario_bank_b import SCENARIOS_B
from .scenario_bank_c import SCENARIOS_C

SCENARIOS: list[dict[str, Any]] = [*SCENARIOS_A, *SCENARIOS_B, *SCENARIOS_C]

_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in SCENARIOS}
if len(_BY_ID) != len(SCENARIOS):
    raise ValueError("Duplicate scenario ids across banks")


def get_scenario(scenario_id: str) -> dict[str, Any]:
    """Return the scenario with the given id."""
    return _BY_ID[scenario_id]
