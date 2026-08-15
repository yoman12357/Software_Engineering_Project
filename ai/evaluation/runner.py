"""Evaluation runner for CyberSRS base model benchmark.

Runs the full evaluation pipeline (analysis -> clarification -> SRS)
against the real Ollama/Qwen model and collects metrics.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from src.core.config import Settings
from src.llm.registry import resolve_model_name
from src.schemas.analysis import ProjectAnalysis
from src.schemas.clarification import ClarificationQuestionSet
from src.schemas.srs import SRSSchema

from .metrics import (
    AggregateMetrics,
    CaseMetrics,
    check_requirement_quality,
    compute_aggregate,
    compute_category_accuracy,
    count_duplicate_ids,
)

# API base URL
API_BASE = os.getenv("CYBERSRS_API_BASE", "http://127.0.0.1:8000/api/v1")

# Timeouts
ANALYSIS_TIMEOUT = 180.0
CLARIFICATION_TIMEOUT = 180.0
SRS_TIMEOUT = 300.0


class EvaluationRunner:
    """Runs evaluation cases against the CyberSRS API."""

    def __init__(
        self,
        api_base: str = API_BASE,
        dataset_path: str | None = None,
        output_dir: str | None = None,
    ):
        self.api_base = api_base
        self.client = httpx.AsyncClient(timeout=300.0)
        self.dataset_path = dataset_path or "ai/evaluation/dataset.json"
        self.output_dir = Path(output_dir or "ai/evaluation/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.run_id = f"eval-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.timestamp = datetime.now(UTC).isoformat()
        self.model_name = resolve_model_name(Settings())
        self.provider = os.getenv("CYBERSRS_LLM_PROVIDER", "ollama")

        self.case_metrics: list[CaseMetrics] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def load_dataset(self) -> list[dict[str, Any]]:
        """Load evaluation dataset."""
        with open(self.dataset_path) as f:
            data = json.load(f)
        return data

    async def run_analysis(self, project_id: str) -> tuple[dict, CaseMetrics]:
        """Run analysis endpoint and collect metrics."""
        metrics = CaseMetrics(
            case_id="",  # Will be set by caller
            description="",
            expected_categories=[],
        )

        start = time.time()
        try:
            resp = await self.client.post(
                f"{self.api_base}/projects/{project_id}/analyse",
                timeout=ANALYSIS_TIMEOUT,
            )
            latency = time.time() - start
            metrics.analysis_latency_seconds = latency

            if resp.status_code == 200:
                data = resp.json()
                metrics.analysis_success = True
                metrics.analysis_json_valid = True

                # Validate schema
                try:
                    ProjectAnalysis.model_validate(data["analysis"])
                    metrics.analysis_schema_valid = True
                except Exception as e:
                    metrics.analysis_schema_valid = False
                    metrics.analysis_error = f"Schema validation failed: {e}"

                metrics.inferred_categories = data["analysis"].get("inferred_categories", [])
                metrics.missing_info_count = len(data["analysis"].get("missing_information", []))

                return data, metrics
            else:
                metrics.analysis_error = f"HTTP {resp.status_code}: {resp.text}"
                return {}, metrics

        except Exception as e:
            metrics.analysis_latency_seconds = time.time() - start
            metrics.analysis_error = str(e)
            return {}, metrics

    async def run_clarification_generation(self, project_id: str) -> tuple[dict, CaseMetrics]:
        """Run clarification generation and collect metrics."""
        metrics = CaseMetrics(
            case_id="",
            description="",
            expected_categories=[],
        )

        start = time.time()
        try:
            resp = await self.client.post(
                f"{self.api_base}/projects/{project_id}/clarifications/generate",
                timeout=CLARIFICATION_TIMEOUT,
            )
            latency = time.time() - start
            metrics.clarification_latency_seconds = latency

            if resp.status_code == 200:
                data = resp.json()
                metrics.clarification_success = True
                metrics.clarification_json_valid = True

                # Validate only draft fields (question_text, reason, is_critical,
                # target_gap, expected_answer_type). API returns full
                # question objects with extra DB fields.
                draft_questions = []
                for q in data.get("questions", []):
                    draft_questions.append({
                        "question_text": q.get("question_text", ""),
                        "reason": q.get("reason", ""),
                        "is_critical": q.get("is_critical", False),
                        "target_gap": q.get("target_gap", ""),
                        "expected_answer_type": q.get("expected_answer_type", "text"),
                    })
                try:
                    ClarificationQuestionSet.model_validate({"questions": draft_questions})
                    metrics.clarification_schema_valid = True
                except Exception as e:
                    metrics.clarification_schema_valid = False
                    metrics.clarification_error = f"Schema validation failed: {e}"

                questions = data.get("questions", [])
                metrics.question_count = len(questions)

                for q in questions:
                    if q.get("target_gap"):
                        metrics.questions_have_target_gap += 1
                    if q.get("reason"):
                        metrics.questions_have_reason += 1

                return data, metrics
            else:
                metrics.clarification_error = f"HTTP {resp.status_code}: {resp.text}"
                return {}, metrics

        except Exception as e:
            metrics.clarification_latency_seconds = time.time() - start
            metrics.clarification_error = str(e)
            return {}, metrics

    async def run_srs_generation(self, project_id: str) -> tuple[dict, CaseMetrics]:
        """Run SRS generation and collect metrics."""
        metrics = CaseMetrics(
            case_id="",
            description="",
            expected_categories=[],
        )

        start = time.time()
        try:
            resp = await self.client.post(
                f"{self.api_base}/projects/{project_id}/srs/generate",
                timeout=SRS_TIMEOUT,
            )
            latency = time.time() - start
            metrics.srs_latency_seconds = latency

            if resp.status_code == 200:
                data = resp.json()
                metrics.srs_success = True

                # Get the full SRS
                version_id = data["version_id"]
                srs_resp = await self.client.get(
                    f"{self.api_base}/projects/{project_id}/srs/versions/{version_id}",
                    timeout=30.0,
                )
                if srs_resp.status_code == 200:
                    srs_data = srs_resp.json()
                    srs = srs_data.get("srs", {})
                    metrics.srs_json_valid = True

                    try:
                        SRSSchema.model_validate(srs)
                        metrics.srs_schema_valid = True
                    except Exception as e:
                        metrics.srs_schema_valid = False
                        metrics.srs_error = f"Schema validation failed: {e}"

                    # Collect requirement metrics
                    all_reqs = []
                    for section in [
                        "functional_requirements",
                        "non_functional_requirements",
                        "security_requirements",
                        "data_requirements",
                        "network_requirements",
                    ]:
                        reqs = srs.get(section, [])
                        all_reqs.extend(reqs)
                        if section == "functional_requirements":
                            metrics.functional_req_count = len(reqs)
                        elif section == "non_functional_requirements":
                            metrics.non_functional_req_count = len(reqs)
                        elif section == "security_requirements":
                            metrics.security_req_count = len(reqs)
                        elif section == "data_requirements":
                            metrics.data_req_count = len(reqs)
                        elif section == "network_requirements":
                            metrics.network_req_count = len(reqs)

                    metrics.requirement_count = len(all_reqs)
                    metrics.duplicate_requirement_ids = count_duplicate_ids(all_reqs)

                    quality = check_requirement_quality(all_reqs)
                    metrics.missing_statements = quality["missing_statements"]
                    metrics.missing_acceptance_criteria = quality["missing_acceptance"]
                    metrics.invalid_priorities = quality["invalid_priorities"]

                    metrics.threat_count = len(srs.get("threats", []))
                    arch = srs.get("architecture_summary", {})
                    metrics.has_architecture = bool(arch.get("components"))
                    metrics.has_testing_strategy = bool(srs.get("testing_strategy"))
                    metrics.has_risks = bool(srs.get("risks"))

                return data, metrics
            else:
                metrics.srs_error = f"HTTP {resp.status_code}: {resp.text}"
                return {}, metrics

        except Exception as e:
            metrics.srs_latency_seconds = time.time() - start
            metrics.srs_error = str(e)
            return {}, metrics

    async def run_case(self, case: dict[str, Any]) -> CaseMetrics:
        """Run a single evaluation case through the full pipeline."""
        case_id = case["id"]
        description = case["description"]
        expected_categories = case.get("expected_categories", [])

        print(f"\n{'='*60}")
        print(f"Running case: {case_id} ({case.get('category', 'unknown')})")
        print(f"Description: {description[:80]}...")
        print(f"Expected categories: {expected_categories}")
        print(f"{'='*60}")

        # Create project
        create_resp = await self.client.post(
            f"{self.api_base}/projects",
            json={"name": f"Eval {case_id}", "description": description},
            timeout=30.0,
        )
        if create_resp.status_code != 201:
            raise RuntimeError(f"Failed to create project: {create_resp.text}")

        project = create_resp.json()
        project_id = project["id"]

        # Initialize metrics
        metrics = CaseMetrics(
            case_id=case_id,
            description=description,
            expected_categories=expected_categories,
        )

        # Run analysis
        print("  Running analysis...")
        analysis_data, analysis_metrics = await self.run_analysis(project_id)
        metrics.analysis_latency_seconds = analysis_metrics.analysis_latency_seconds
        metrics.analysis_success = analysis_metrics.analysis_success
        metrics.analysis_json_valid = analysis_metrics.analysis_json_valid
        metrics.analysis_schema_valid = analysis_metrics.analysis_schema_valid
        metrics.inferred_categories = analysis_metrics.inferred_categories
        metrics.category_accuracy = compute_category_accuracy(
            metrics.inferred_categories, expected_categories
        )
        metrics.missing_info_count = analysis_metrics.missing_info_count
        metrics.analysis_error = analysis_metrics.analysis_error

        if not metrics.analysis_success:
            print(f"  Analysis failed: {metrics.analysis_error}")
            metrics.total_latency_seconds = metrics.analysis_latency_seconds
            self.case_metrics.append(metrics)
            return metrics

        print(
            f"  Analysis OK - Categories: {metrics.inferred_categories} "
            f"(accuracy: {metrics.category_accuracy:.2f})"
        )

        # Run clarification generation
        print("  Generating clarifications...")
        clarification_data, clarification_metrics = await self.run_clarification_generation(
            project_id
        )
        metrics.clarification_latency_seconds = clarification_metrics.clarification_latency_seconds
        metrics.clarification_success = clarification_metrics.clarification_success
        metrics.clarification_json_valid = clarification_metrics.clarification_json_valid
        metrics.clarification_schema_valid = clarification_metrics.clarification_schema_valid
        metrics.question_count = clarification_metrics.question_count
        metrics.questions_have_target_gap = clarification_metrics.questions_have_target_gap
        metrics.questions_have_reason = clarification_metrics.questions_have_reason
        metrics.clarification_error = clarification_metrics.clarification_error

        if not metrics.clarification_success:
            print(f"  Clarification failed: {metrics.clarification_error}")
            # Still try SRS generation
        else:
            print(f"  Clarifications OK - {metrics.question_count} questions")

        # Submit dummy answers for all questions
        if metrics.clarification_success and metrics.question_count > 0:
            questions = clarification_data.get("questions", [])
            answers = []
            for q in questions:
                ans_type = q.get("expected_answer_type", "text")
                if ans_type == "number":
                    answers.append(
                        {"question_id": q["id"], "answer_text": "100", "skipped": False}
                    )
                elif ans_type == "boolean":
                    answers.append(
                        {"question_id": q["id"], "answer_text": "", "skipped": True}
                    )
                elif ans_type == "list":
                    answers.append(
                        {"question_id": q["id"], "answer_text": "item1, item2", "skipped": False}
                    )
                else:
                    answers.append(
                        {
                            "question_id": q["id"],
                            "answer_text": "Standard requirements apply",
                            "skipped": False,
                        }
                    )

            await self.client.post(
                f"{self.api_base}/projects/{project_id}/clarifications",
                json={"answers": answers},
                timeout=30.0,
            )

        # Run SRS generation
        print("  Generating SRS...")
        srs_data, srs_metrics = await self.run_srs_generation(project_id)
        metrics.srs_latency_seconds = srs_metrics.srs_latency_seconds
        metrics.srs_success = srs_metrics.srs_success
        metrics.srs_json_valid = srs_metrics.srs_json_valid
        metrics.srs_schema_valid = srs_metrics.srs_schema_valid
        metrics.requirement_count = srs_metrics.requirement_count
        metrics.duplicate_requirement_ids = srs_metrics.duplicate_requirement_ids
        metrics.missing_statements = srs_metrics.missing_statements
        metrics.missing_acceptance_criteria = srs_metrics.missing_acceptance_criteria
        metrics.invalid_priorities = srs_metrics.invalid_priorities
        metrics.functional_req_count = srs_metrics.functional_req_count
        metrics.non_functional_req_count = srs_metrics.non_functional_req_count
        metrics.security_req_count = srs_metrics.security_req_count
        metrics.data_req_count = srs_metrics.data_req_count
        metrics.network_req_count = srs_metrics.network_req_count
        metrics.threat_count = srs_metrics.threat_count
        metrics.has_architecture = srs_metrics.has_architecture
        metrics.has_testing_strategy = srs_metrics.has_testing_strategy
        metrics.has_risks = srs_metrics.has_risks
        metrics.srs_error = srs_metrics.srs_error

        if not metrics.srs_success:
            print(f"  SRS failed: {metrics.srs_error}")
        else:
            print(
                f"  SRS OK - {metrics.requirement_count} requirements, "
                f"{metrics.threat_count} threats"
            )

        metrics.total_latency_seconds = (
            metrics.analysis_latency_seconds
            + metrics.clarification_latency_seconds
            + metrics.srs_latency_seconds
        )

        self.case_metrics.append(metrics)
        return metrics

    async def run_evaluation(
        self,
        case_ids: list[str] | None = None,
        max_cases: int | None = None,
    ) -> AggregateMetrics:
        """Run evaluation on specified cases."""
        dataset = self.load_dataset()

        if case_ids:
            cases = [c for c in dataset if c["id"] in case_ids]
        else:
            cases = dataset

        if max_cases:
            cases = cases[:max_cases]

        print(f"Starting evaluation run: {self.run_id}")
        print(f"Model: {self.model_name} (provider: {self.provider})")
        print(f"Cases to evaluate: {len(cases)}")
        print(f"Output directory: {self.output_dir}")

        for case in cases:
            try:
                await self.run_case(case)
            except Exception as e:
                print(f"Case {case['id']} failed with exception: {e}")
                metrics = CaseMetrics(
                    case_id=case["id"],
                    description=case["description"],
                    expected_categories=case.get("expected_categories", []),
                    analysis_error=str(e),
                )
                self.case_metrics.append(metrics)

        # Compute aggregates
        aggregate = compute_aggregate(self.case_metrics)

        # Save results
        await self.save_results(aggregate)

        return aggregate

    async def save_results(self, aggregate: AggregateMetrics) -> None:
        """Save evaluation results to disk."""
        run_dir = self.output_dir / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save individual case metrics
        cases_file = run_dir / "case_metrics.json"
        with open(cases_file, "w") as f:
            json.dump([m.to_dict() for m in self.case_metrics], f, indent=2)

        # Save aggregate metrics
        agg_file = run_dir / "aggregate_metrics.json"
        with open(agg_file, "w") as f:
            json.dump(aggregate.to_dict(), f, indent=2)

        # Save run metadata
        meta = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model_name": self.model_name,
            "dataset_path": self.dataset_path,
            "total_cases": len(self.case_metrics),
            "api_base": self.api_base,
        }
        meta_file = run_dir / "run_metadata.json"
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)

        # Save human-readable summary
        summary_file = run_dir / "summary.txt"
        with open(summary_file, "w") as f:
            f.write(self.format_summary(aggregate))

        print(f"\nResults saved to: {run_dir}")
        print(f"  - {cases_file}")
        print(f"  - {agg_file}")
        print(f"  - {meta_file}")
        print(f"  - {summary_file}")

    def format_summary(self, agg: AggregateMetrics) -> str:
        """Format human-readable summary."""
        lines = [
            "=" * 60,
            "CYBERSRS BASE MODEL EVALUATION SUMMARY",
            "=" * 60,
            f"Run ID: {self.run_id}",
            f"Timestamp: {self.timestamp}",
            f"Provider: {self.provider}",
            f"Model: {self.model_name}",
            f"Total Cases: {agg.total_cases}",
            f"Fully Successful: {agg.successful_cases}",
            "",
            "SUCCESS RATES:",
            f"  Analysis:      {agg.analysis_success_rate:.1%}",
            f"  Clarification: {agg.clarification_success_rate:.1%}",
            f"  SRS:           {agg.srs_success_rate:.1%}",
            "",
            "JSON VALIDITY:",
            f"  Analysis:      {agg.analysis_json_validity_rate:.1%}",
            f"  Clarification: {agg.clarification_json_validity_rate:.1%}",
            f"  SRS:           {agg.srs_json_validity_rate:.1%}",
            "",
            "SCHEMA VALIDITY:",
            f"  Analysis:      {agg.analysis_schema_validity_rate:.1%}",
            f"  Clarification: {agg.clarification_schema_validity_rate:.1%}",
            f"  SRS:           {agg.srs_schema_validity_rate:.1%}",
            "",
            "CATEGORY ACCURACY:",
            f"  Mean:  {agg.category_accuracy_mean:.3f}",
            f"  Std:   {agg.category_accuracy_std:.3f}",
            "",
            "REQUIREMENT QUALITY:",
            f"  Total Requirements:     {agg.total_requirements}",
            f"  Avg per SRS:            {agg.avg_requirements_per_srs:.1f}",
            f"  Duplicate ID Rate:      {agg.duplicate_id_rate:.3f}",
            f"  Missing Statement Rate: {agg.missing_statement_rate:.3f}",
            f"  Missing Acceptance:     {agg.missing_acceptance_rate:.3f}",
            f"  Invalid Priority Rate:  {agg.invalid_priority_rate:.3f}",
            "",
            "CLARIFICATION QUALITY:",
            f"  Avg Questions/Case:     {agg.avg_questions_per_case:.1f}",
            f"  Target Gap Coverage:    {agg.target_gap_coverage_rate:.1%}",
            "",
            "PERFORMANCE:",
            f"  Avg Analysis Latency:   {agg.avg_analysis_latency:.1f}s",
            f"  Avg Clarification:      {agg.avg_clarification_latency:.1f}s",
            f"  Avg SRS Latency:        {agg.avg_srs_latency:.1f}s",
            f"  Avg Total Latency:      {agg.avg_total_latency:.1f}s",
            f"  Avg Retry Count:        {agg.avg_retry_count:.2f}",
            "",
            "GENERATION FAILURES:",
            f"  Analysis:      {agg.analysis_failure_count}",
            f"  Clarification: {agg.clarification_failure_count}",
            f"  SRS:           {agg.srs_failure_count}",
            "",
            "=" * 60,
        ]
        return "\n".join(lines)


async def main():
    """Main entry point for evaluation runner."""
    import argparse

    parser = argparse.ArgumentParser(description="CyberSRS Base Model Evaluation Runner")
    parser.add_argument("--case-ids", nargs="+", help="Specific case IDs to evaluate")
    parser.add_argument("--max-cases", type=int, help="Maximum number of cases to evaluate")
    parser.add_argument("--api-base", default=API_BASE, help="API base URL")
    parser.add_argument("--dataset", default="ai/evaluation/dataset.json", help="Dataset path")
    parser.add_argument("--output-dir", default="ai/evaluation/results", help="Output directory")
    args = parser.parse_args()

    async with EvaluationRunner(
        api_base=args.api_base,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
    ) as runner:
        await runner.run_evaluation(case_ids=args.case_ids, max_cases=args.max_cases)


if __name__ == "__main__":
    asyncio.run(main())
