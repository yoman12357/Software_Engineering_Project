"""Evaluation metrics for CyberSRS base model assessment.

Implements automated metrics for JSON validity, schema compliance,
requirement quality, and generation performance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CaseMetrics:
    """Metrics for a single evaluation case."""

    case_id: str
    description: str
    expected_categories: list[str]

    # Generation metadata
    analysis_latency_seconds: float = 0.0
    clarification_latency_seconds: float = 0.0
    srs_latency_seconds: float = 0.0
    total_latency_seconds: float = 0.0

    analysis_retry_count: int = 0
    clarification_retry_count: int = 0
    srs_retry_count: int = 0

    # Success flags
    analysis_success: bool = False
    clarification_success: bool = False
    srs_success: bool = False

    # Analysis metrics
    analysis_json_valid: bool = False
    analysis_schema_valid: bool = False
    inferred_categories: list[str] = field(default_factory=list)
    category_accuracy: float = 0.0
    missing_info_count: int = 0

    # Clarification metrics
    clarification_json_valid: bool = False
    clarification_schema_valid: bool = False
    question_count: int = 0
    questions_have_target_gap: int = 0
    questions_have_reason: int = 0

    # SRS metrics
    srs_json_valid: bool = False
    srs_schema_valid: bool = False
    requirement_count: int = 0
    duplicate_requirement_ids: list[str] = field(default_factory=list)
    missing_statements: int = 0
    missing_acceptance_criteria: int = 0
    invalid_priorities: int = 0
    functional_req_count: int = 0
    non_functional_req_count: int = 0
    security_req_count: int = 0
    data_req_count: int = 0
    network_req_count: int = 0
    threat_count: int = 0
    has_architecture: bool = False
    has_testing_strategy: bool = False
    has_risks: bool = False

    # Error details
    analysis_error: str | None = None
    clarification_error: str | None = None
    srs_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "description": self.description,
            "expected_categories": self.expected_categories,
            "latency": {
                "analysis_seconds": self.analysis_latency_seconds,
                "clarification_seconds": self.clarification_latency_seconds,
                "srs_seconds": self.srs_latency_seconds,
                "total_seconds": self.total_latency_seconds,
            },
            "retry_counts": {
                "analysis": self.analysis_retry_count,
                "clarification": self.clarification_retry_count,
                "srs": self.srs_retry_count,
            },
            "success": {
                "analysis": self.analysis_success,
                "clarification": self.clarification_success,
                "srs": self.srs_success,
            },
            "analysis": {
                "json_valid": self.analysis_json_valid,
                "schema_valid": self.analysis_schema_valid,
                "inferred_categories": self.inferred_categories,
                "category_accuracy": self.category_accuracy,
                "missing_info_count": self.missing_info_count,
            },
            "clarification": {
                "json_valid": self.clarification_json_valid,
                "schema_valid": self.clarification_schema_valid,
                "question_count": self.question_count,
                "questions_have_target_gap": self.questions_have_target_gap,
                "questions_have_reason": self.questions_have_reason,
            },
            "srs": {
                "json_valid": self.srs_json_valid,
                "schema_valid": self.srs_schema_valid,
                "requirement_count": self.requirement_count,
                "duplicate_requirement_ids": self.duplicate_requirement_ids,
                "missing_statements": self.missing_statements,
                "missing_acceptance_criteria": self.missing_acceptance_criteria,
                "invalid_priorities": self.invalid_priorities,
                "requirements_by_category": {
                    "functional": self.functional_req_count,
                    "non_functional": self.non_functional_req_count,
                    "security": self.security_req_count,
                    "data": self.data_req_count,
                    "network": self.network_req_count,
                },
                "threat_count": self.threat_count,
                "has_architecture": self.has_architecture,
                "has_testing_strategy": self.has_testing_strategy,
                "has_risks": self.has_risks,
            },
            "errors": {
                "analysis": self.analysis_error,
                "clarification": self.clarification_error,
                "srs": self.srs_error,
            },
        }


@dataclass
class AggregateMetrics:
    """Aggregate metrics across all evaluation cases."""

    total_cases: int = 0
    successful_cases: int = 0

    # Success rates
    analysis_success_rate: float = 0.0
    clarification_success_rate: float = 0.0
    srs_success_rate: float = 0.0

    # JSON/schema validity
    analysis_json_validity_rate: float = 0.0
    analysis_schema_validity_rate: float = 0.0
    clarification_json_validity_rate: float = 0.0
    clarification_schema_validity_rate: float = 0.0
    srs_json_validity_rate: float = 0.0
    srs_schema_validity_rate: float = 0.0

    # Subdomain accuracy
    category_accuracy_mean: float = 0.0
    category_accuracy_std: float = 0.0

    # Requirement quality
    total_requirements: int = 0
    avg_requirements_per_srs: float = 0.0
    duplicate_id_rate: float = 0.0
    missing_statement_rate: float = 0.0
    missing_acceptance_rate: float = 0.0
    invalid_priority_rate: float = 0.0

    # Clarification quality
    avg_questions_per_case: float = 0.0
    target_gap_coverage_rate: float = 0.0

    # Performance
    avg_analysis_latency: float = 0.0
    avg_clarification_latency: float = 0.0
    avg_srs_latency: float = 0.0
    avg_total_latency: float = 0.0
    avg_retry_count: float = 0.0

    # Generation failures
    analysis_failure_count: int = 0
    clarification_failure_count: int = 0
    srs_failure_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "successful_cases": self.successful_cases,
            "success_rates": {
                "analysis": self.analysis_success_rate,
                "clarification": self.clarification_success_rate,
                "srs": self.srs_success_rate,
            },
            "json_validity": {
                "analysis": self.analysis_json_validity_rate,
                "clarification": self.clarification_json_validity_rate,
                "srs": self.srs_json_validity_rate,
            },
            "schema_validity": {
                "analysis": self.analysis_schema_validity_rate,
                "clarification": self.clarification_schema_validity_rate,
                "srs": self.srs_schema_validity_rate,
            },
            "category_accuracy": {
                "mean": self.category_accuracy_mean,
                "std": self.category_accuracy_std,
            },
            "requirement_quality": {
                "total_requirements": self.total_requirements,
                "avg_per_srs": self.avg_requirements_per_srs,
                "duplicate_id_rate": self.duplicate_id_rate,
                "missing_statement_rate": self.missing_statement_rate,
                "missing_acceptance_rate": self.missing_acceptance_rate,
                "invalid_priority_rate": self.invalid_priority_rate,
            },
            "clarification_quality": {
                "avg_questions_per_case": self.avg_questions_per_case,
                "target_gap_coverage_rate": self.target_gap_coverage_rate,
            },
            "performance": {
                "avg_analysis_latency_seconds": self.avg_analysis_latency,
                "avg_clarification_latency_seconds": self.avg_clarification_latency,
                "avg_srs_latency_seconds": self.avg_srs_latency,
                "avg_total_latency_seconds": self.avg_total_latency,
                "avg_retry_count": self.avg_retry_count,
            },
            "generation_failures": {
                "analysis": self.analysis_failure_count,
                "clarification": self.clarification_failure_count,
                "srs": self.srs_failure_count,
            },
        }


def compute_category_accuracy(predicted: list[str], expected: list[str]) -> float:
    """Compute Jaccard similarity between predicted and expected categories."""
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    pred_set = set(predicted)
    exp_set = set(expected)
    intersection = pred_set & exp_set
    union = pred_set | exp_set
    return len(intersection) / len(union)


def validate_requirement_id_format(req_id: str) -> bool:
    """Check if requirement ID follows the pattern (FR|NFR|SEC|DATA|NET)-NNN."""
    return bool(re.match(r"^(FR|NFR|SEC|DATA|NET)-\d{3}$", req_id))


def count_duplicate_ids(requirements: list[dict]) -> list[str]:
    """Find duplicate requirement IDs across all sections."""
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    for req in requirements:
        req_id = req.get("id", "")
        if req_id in seen:
            if seen[req_id] == 1:
                duplicates.append(req_id)
            seen[req_id] += 1
        else:
            seen[req_id] = 1
    return duplicates


def check_requirement_quality(requirements: list[dict]) -> dict[str, int]:
    """Check quality of requirements."""
    missing_statements = 0
    missing_acceptance = 0
    invalid_priorities = 0

    valid_priorities = {"must", "should", "could"}

    for req in requirements:
        stmt = req.get("statement", "")
        if not stmt or not stmt.strip():
            missing_statements += 1

        acc = req.get("acceptance_criteria", "")
        if not acc or not acc.strip():
            missing_acceptance += 1

        pri = req.get("priority", "")
        if pri not in valid_priorities:
            invalid_priorities += 1

    return {
        "missing_statements": missing_statements,
        "missing_acceptance": missing_acceptance,
        "invalid_priorities": invalid_priorities,
    }


def compute_aggregate(metrics_list: list[CaseMetrics]) -> AggregateMetrics:
    """Compute aggregate metrics from case metrics."""
    if not metrics_list:
        return AggregateMetrics()

    total = len(metrics_list)

    # Success rates
    analysis_success = sum(1 for m in metrics_list if m.analysis_success)
    clarification_success = sum(1 for m in metrics_list if m.clarification_success)
    srs_success = sum(1 for m in metrics_list if m.srs_success)
    fully_successful = sum(
        1 for m in metrics_list if m.analysis_success and m.clarification_success and m.srs_success
    )

    # JSON validity
    analysis_json_valid = sum(1 for m in metrics_list if m.analysis_json_valid)
    analysis_schema_valid = sum(1 for m in metrics_list if m.analysis_schema_valid)
    clarification_json_valid = sum(1 for m in metrics_list if m.clarification_json_valid)
    clarification_schema_valid = sum(1 for m in metrics_list if m.clarification_schema_valid)
    srs_json_valid = sum(1 for m in metrics_list if m.srs_json_valid)
    srs_schema_valid = sum(1 for m in metrics_list if m.srs_schema_valid)

    # Category accuracy
    cat_accuracies = [m.category_accuracy for m in metrics_list if m.analysis_success]
    cat_mean = sum(cat_accuracies) / len(cat_accuracies) if cat_accuracies else 0.0
    cat_std = (
        (sum((x - cat_mean) ** 2 for x in cat_accuracies) / len(cat_accuracies)) ** 0.5
        if cat_accuracies
        else 0.0
    )

    # Requirement quality
    total_duplicates = 0
    total_missing_stmt = 0
    total_missing_acc = 0
    total_invalid_pri = 0
    total_reqs = 0

    func_count = 0
    nfunc_count = 0
    sec_count = 0
    data_count = 0
    net_count = 0
    threat_total = 0
    arch_count = 0
    test_count = 0
    risk_count = 0

    total_questions = 0
    total_target_gap = 0

    analysis_latencies = []
    clarification_latencies = []
    srs_latencies = []
    total_latencies = []
    all_retries = []

    analysis_failures = 0
    clarification_failures = 0
    srs_failures = 0

    for m in metrics_list:
        analysis_latencies.append(m.analysis_latency_seconds)
        clarification_latencies.append(m.clarification_latency_seconds)
        srs_latencies.append(m.srs_latency_seconds)
        total_latencies.append(m.total_latency_seconds)
        all_retries.extend(
            [m.analysis_retry_count, m.clarification_retry_count, m.srs_retry_count]
        )

        if not m.analysis_success:
            analysis_failures += 1
        if not m.clarification_success:
            clarification_failures += 1
        if not m.srs_success:
            srs_failures += 1

        if m.srs_success:
            # We'd need the actual SRS to compute detailed req metrics
            # For now, use the counts we tracked
            total_reqs += m.requirement_count
            total_duplicates += len(m.duplicate_requirement_ids)
            total_missing_stmt += m.missing_statements
            total_missing_acc += m.missing_acceptance_criteria
            total_invalid_pri += m.invalid_priorities

            func_count += m.functional_req_count
            nfunc_count += m.non_functional_req_count
            sec_count += m.security_req_count
            data_count += m.data_req_count
            net_count += m.network_req_count
            threat_total += m.threat_count
            if m.has_architecture:
                arch_count += 1
            if m.has_testing_strategy:
                test_count += 1
            if m.has_risks:
                risk_count += 1

        total_questions += m.question_count
        total_target_gap += m.questions_have_target_gap

    successful_srs = sum(1 for m in metrics_list if m.srs_success)

    return AggregateMetrics(
        total_cases=total,
        successful_cases=fully_successful,
        analysis_success_rate=analysis_success / total,
        clarification_success_rate=clarification_success / total,
        srs_success_rate=srs_success / total,
        analysis_json_validity_rate=analysis_json_valid / total,
        analysis_schema_validity_rate=analysis_schema_valid / total,
        clarification_json_validity_rate=clarification_json_valid / total,
        clarification_schema_validity_rate=clarification_schema_valid / total,
        srs_json_validity_rate=srs_json_valid / total,
        srs_schema_validity_rate=srs_schema_valid / total,
        category_accuracy_mean=cat_mean,
        category_accuracy_std=cat_std,
        total_requirements=total_reqs,
        avg_requirements_per_srs=total_reqs / successful_srs if successful_srs else 0.0,
        duplicate_id_rate=total_duplicates / total_reqs if total_reqs else 0.0,
        missing_statement_rate=total_missing_stmt / total_reqs if total_reqs else 0.0,
        missing_acceptance_rate=total_missing_acc / total_reqs if total_reqs else 0.0,
        invalid_priority_rate=total_invalid_pri / total_reqs if total_reqs else 0.0,
        avg_questions_per_case=total_questions / total,
        target_gap_coverage_rate=total_target_gap / total_questions if total_questions else 0.0,
avg_analysis_latency=(
                sum(analysis_latencies) / len(analysis_latencies) if analysis_latencies else 0.0
            ),
            avg_clarification_latency=(
                sum(clarification_latencies) / len(clarification_latencies)
                if clarification_latencies
                else 0.0
            ),
            avg_srs_latency=(
                sum(srs_latencies) / len(srs_latencies) if srs_latencies else 0.0
            ),
            avg_total_latency=(
                sum(total_latencies) / len(total_latencies) if total_latencies else 0.0
            ),
            avg_retry_count=(
                sum(all_retries) / len(all_retries) if all_retries else 0.0
            ),
        analysis_failure_count=analysis_failures,
        clarification_failure_count=clarification_failures,
        srs_failure_count=srs_failures,
    )