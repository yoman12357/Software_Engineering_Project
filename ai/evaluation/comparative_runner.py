# ruff: noqa: E501
"""Comparative evaluation runner for CyberSRS: Base Qwen vs Base Qwen + RAG.

Uses service layer directly (no HTTP) for fast, reliable evaluation.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.core.config import Settings
from src.db.database import Database
from src.db.models import Project
from src.llm.factory import create_llm_provider
from src.llm.registry import resolve_model_name
from src.schemas.analysis import ProjectAnalysis
from src.schemas.clarification import ClarificationQuestionSet
from src.schemas.project import generate_uuid
from src.schemas.srs import SRSSchema
from src.services.analysis_service import AnalysisService
from src.services.clarification_service import ClarificationService
from src.services.srs_generation_service import SRSGenerationService

from .metrics import (
    AggregateMetrics,
    CaseMetrics,
    check_requirement_quality,
    compute_aggregate,
    compute_category_accuracy,
    count_duplicate_ids,
)


@dataclass
class RAGCaseMetrics(CaseMetrics):
    """Extended metrics with RAG-specific fields."""

    # Retrieval metrics
    retrieval_attempted: bool = False
    retrieval_success: bool = False
    retrieval_latency_seconds: float = 0.0
    chunks_retrieved: int = 0
    kb_version: str | None = None
    query_texts: list[str] = field(default_factory=list)

    # Citation metrics
    citations_present: int = 0
    citations_valid: int = 0
    citations_invalid: int = 0
    unsupported_citation_count: int = 0
    citation_precision: float = 0.0
    citation_support: float = 0.0

    # RAG-specific quality
    relevant_source_retrieval: float = 0.0
    security_req_coverage: float = 0.0
    hallucination_indicators: int = 0

    # Latency overhead
    rag_overhead_seconds: float = 0.0


@dataclass
class RAGAggregateMetrics(AggregateMetrics):
    """Extended aggregate metrics with RAG-specific fields."""

    retrieval_success_rate: float = 0.0
    avg_retrieval_latency: float = 0.0
    avg_chunks_retrieved: float = 0.0
    citation_presence_rate: float = 0.0
    citation_validity_rate: float = 0.0
    citation_precision_mean: float = 0.0
    citation_support_mean: float = 0.0
    unsupported_citation_rate: float = 0.0
    relevant_source_retrieval_mean: float = 0.0
    security_req_coverage_mean: float = 0.0
    hallucination_indicator_rate: float = 0.0
    avg_rag_overhead: float = 0.0


class DirectComparativeRunner:
    """Runs evaluation cases using service layer directly."""

    def __init__(
        self,
        dataset_path: str | None = None,
        output_dir: str | None = None,
    ):
        self.dataset_path = dataset_path or "ai/evaluation/dataset.json"
        self.output_dir = Path(output_dir or "ai/evaluation/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.run_id = f"eval-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.timestamp = datetime.now(UTC).isoformat()

        self.base_results: list[RAGCaseMetrics] = []
        self.rag_results: list[RAGCaseMetrics] = []

        # Shared database
        self.settings = Settings()
        # Provider and RAG mode will be set per configuration run
        self.settings.rag_enabled = False
        self.db = Database(self.settings.database_url)
        self.db.init_db()
        self.Session = self.db.session_factory

    def load_dataset(self) -> list[dict[str, Any]]:
        with open(self.dataset_path) as f:
            return json.load(f)

    def _create_services(self, use_rag: bool):
        """Create service instances with the given RAG setting."""
        session = self.Session()
        self.settings.rag_enabled = use_rag
        provider = create_llm_provider(self.settings)
        
        analysis_svc = AnalysisService(session, provider)
        clarification_svc = ClarificationService(session, provider)
        srs_svc = SRSGenerationService(session, provider, self.settings)
        
        return session, analysis_svc, clarification_svc, srs_svc

    def _create_project(self, session, case_id: str, description: str) -> str:
        project = Project(
            id=generate_uuid(),
            name=f"Eval {case_id}",
            description=description,
            status="draft",
        )
        session.add(project)
        session.commit()
        return project.id

    def _run_analysis(self, analysis_svc, project_id: str) -> tuple[Any, float, bool, bool, list[str], int, str | None]:
        start = time.time()
        try:
            result = analysis_svc.analyse_project(project_id)
            latency = time.time() - start
            categories = result.analysis.inferred_categories
            missing_count = len(result.analysis.missing_information)
            try:
                ProjectAnalysis.model_validate(result.analysis.model_dump())
                schema_valid = True
            except Exception:
                schema_valid = False
            return result, latency, True, schema_valid, categories, missing_count, None
        except Exception as e:
            return None, time.time() - start, False, False, [], 0, str(e)

    def _run_clarification(self, clarification_svc, project_id: str) -> tuple[Any, float, bool, bool, int, int, int, str | None]:
        start = time.time()
        try:
            result = clarification_svc.generate_questions(project_id)
            latency = time.time() - start
            questions = result.questions
            q_count = len(questions)
            tg_count = sum(1 for q in questions if q.target_gap)
            reason_count = sum(1 for q in questions if q.reason)
            try:
                ClarificationQuestionSet.model_validate({"questions": [
                    {"question_text": q.question_text, "reason": q.reason,
                     "is_critical": q.is_critical, "target_gap": q.target_gap,
                     "expected_answer_type": q.expected_answer_type}
                    for q in questions
                ]})
                schema_valid = True
            except Exception:
                schema_valid = False
            return result, latency, True, schema_valid, q_count, tg_count, reason_count, None
        except Exception as e:
            return None, time.time() - start, False, False, 0, 0, 0, str(e)

    def _submit_answers(self, clarification_svc, project_id: str, questions: list) -> None:
        from src.schemas.clarification import ClarificationAnswerItem, ClarificationAnswerSubmission
        answers = []
        for q in questions:
            # Handle both enum and string
            ans_type = q.expected_answer_type
            if hasattr(ans_type, 'value'):
                ans_type_str = ans_type.value
            else:
                ans_type_str = str(ans_type)
            if ans_type_str == "number":
                answers.append(ClarificationAnswerItem(question_id=q.id, answer_text="100", skipped=False))
            elif ans_type_str == "boolean":
                answers.append(ClarificationAnswerItem(question_id=q.id, answer_text="", skipped=True))
            elif ans_type_str == "list":
                answers.append(ClarificationAnswerItem(question_id=q.id, answer_text="item1, item2", skipped=False))
            else:
                answers.append(ClarificationAnswerItem(question_id=q.id, answer_text="Standard requirements apply", skipped=False))
        clarification_svc.submit_answers(project_id, ClarificationAnswerSubmission(answers=answers))

    def _run_srs_generation(self, srs_svc, project_id: str, use_rag: bool) -> tuple[Any, float, bool, bool, dict[str, Any], str | None]:
        start = time.time()
        try:
            result = srs_svc.generate_srs(project_id, use_rag=use_rag)
            latency = time.time() - start
            
            # Get the full SRS
            version = srs_svc.get_version(project_id, result.version_id)
            srs = version.srs
            gen_meta = srs.generation_metadata if srs and srs.generation_metadata else {}
            
            try:
                SRSSchema.model_validate(srs.model_dump() if srs else {})
                schema_valid = True
            except Exception:
                schema_valid = False

            # Extract RAG metrics from generation metadata
            rag_attempted = gen_meta.get("rag_enabled", False) if gen_meta else False
            retrieved_chunks = gen_meta.get("retrieved_chunks", 0) if gen_meta else 0
            kb_version = gen_meta.get("kb_version", None) if gen_meta else None
            retrieval_latency_seconds = (
                float(gen_meta.get("retrieval_time_ms", 0)) / 1000.0 if gen_meta else 0.0
            )

            # Citation analysis
            citations_present = 0
            citations_valid = 0
            citations_invalid = 0
            unsupported_count = 0

            all_reqs = []
            if srs:
                for section in [
                    "functional_requirements", "non_functional_requirements",
                    "security_requirements", "data_requirements", "network_requirements"
                ]:
                    reqs = getattr(srs, section, [])
                    all_reqs.extend(reqs)
                    for req in reqs:
                        for ref in req.source_references:
                            citations_present += 1
                            if getattr(ref, "supported", True):
                                citations_valid += 1
                            else:
                                citations_invalid += 1
                                unsupported_count += 1

            citation_precision = citations_valid / citations_present if citations_present > 0 else 0.0
            citation_support = citations_valid / max(1, citations_present)

            # Security requirement coverage
            security_reqs = srs.security_requirements if srs else []
            security_req_coverage = 1.0 if len(security_reqs) >= 2 else 0.5 if len(security_reqs) == 1 else 0.0

            # Hallucination indicators
            hallucinations = 0
            for req in all_reqs:
                stmt = req.statement
                if not stmt or not stmt.strip().lower().startswith("the system shall"):
                    hallucinations += 1

            rag_metrics = {
                "retrieval_attempted": rag_attempted,
                "retrieval_success": rag_attempted and retrieved_chunks > 0,
                "retrieval_latency_seconds": retrieval_latency_seconds,
                "chunks_retrieved": retrieved_chunks,
                "kb_version": kb_version,
                "citations_present": citations_present,
                "citations_valid": citations_valid,
                "citations_invalid": citations_invalid,
                "unsupported_citation_count": unsupported_count,
                "citation_precision": citation_precision,
                "citation_support": citation_support,
                "security_req_coverage": security_req_coverage,
                "hallucination_indicators": hallucinations,
            }

            return result, latency, True, schema_valid, rag_metrics, None
        except Exception as e:
            return None, time.time() - start, False, False, {}, str(e)

    def _extract_srs_metrics(self, srs) -> dict:
        """Extract requirement metrics from SRS object."""
        if not srs:
            return {}
        
        all_reqs = []
        counts = {}
        metric_names = {
            "functional_requirements": "functional_req_count",
            "non_functional_requirements": "non_functional_req_count",
            "security_requirements": "security_req_count",
            "data_requirements": "data_req_count",
            "network_requirements": "network_req_count",
        }
        for section in [
            "functional_requirements", "non_functional_requirements",
            "security_requirements", "data_requirements", "network_requirements"
        ]:
            reqs = getattr(srs, section, [])
            all_reqs.extend(reqs)
            counts[metric_names[section]] = len(reqs)
        
        quality = check_requirement_quality([r.model_dump() for r in all_reqs])
        
        return {
            "requirement_count": len(all_reqs),
            "duplicate_ids": count_duplicate_ids([r.model_dump() for r in all_reqs]),
            "missing_statements": quality["missing_statements"],
            "missing_acceptance": quality["missing_acceptance"],
            "invalid_priorities": quality["invalid_priorities"],
            "threat_count": len(srs.threats) if srs.threats else 0,
            "has_architecture": bool(srs.architecture_summary and srs.architecture_summary.components),
            "has_testing": bool(srs.testing_strategy),
            "has_risks": bool(srs.risks),
            **counts,
        }

    def run_case(self, case: dict[str, Any], use_rag: bool) -> RAGCaseMetrics:
        """Run a single evaluation case."""
        case_id = case["id"]
        description = case["description"]
        expected_categories = case.get("expected_categories", [])
        rag_suffix = " [RAG]" if use_rag else " [BASE]"

        print(f"\n{'='*60}")
        print(f"Running case: {case_id}{rag_suffix} ({case.get('category', 'unknown')})")
        print(f"Description: {description[:80]}...")
        print(f"Expected categories: {expected_categories}")
        print(f"{'='*60}")

        session, analysis_svc, clarification_svc, srs_svc = self._create_services(use_rag)
        
        try:
            project_id = self._create_project(session, case_id, description)

            metrics = RAGCaseMetrics(
                case_id=case_id,
                description=description,
                expected_categories=expected_categories,
            )

            # Analysis
            print("  Running analysis...")
            analysis_result, a_lat, a_success, a_schema, a_cats, a_missing, a_err = self._run_analysis(analysis_svc, project_id)
            metrics.analysis_latency_seconds = a_lat
            metrics.analysis_success = a_success
            metrics.analysis_json_valid = a_success
            metrics.analysis_schema_valid = a_schema
            metrics.inferred_categories = a_cats
            metrics.category_accuracy = compute_category_accuracy(a_cats, expected_categories)
            metrics.missing_info_count = a_missing
            metrics.analysis_error = a_err

            if not a_success:
                print(f"  Analysis failed: {a_err}")
                metrics.total_latency_seconds = a_lat
                return metrics

            print(f"  Analysis OK - Categories: {a_cats} (accuracy: {metrics.category_accuracy:.2f})")

            # Clarification
            print("  Generating clarifications...")
            clar_result, c_lat, c_success, c_schema, c_qcount, c_tg, c_reason, c_err = self._run_clarification(clarification_svc, project_id)
            metrics.clarification_latency_seconds = c_lat
            metrics.clarification_success = c_success
            metrics.clarification_json_valid = c_success
            metrics.clarification_schema_valid = c_schema
            metrics.question_count = c_qcount
            metrics.questions_have_target_gap = c_tg
            metrics.questions_have_reason = c_reason
            metrics.clarification_error = c_err

            if c_success:
                print(f"  Clarifications OK - {c_qcount} questions")
                self._submit_answers(clarification_svc, project_id, clar_result.questions)
            else:
                print(f"  Clarification failed: {c_err}")

            # SRS Generation
            print("  Generating SRS...")
            srs_result, s_lat, s_success, s_schema, rag_metrics, s_err = self._run_srs_generation(srs_svc, project_id, use_rag)
            metrics.srs_latency_seconds = s_lat
            metrics.srs_success = s_success
            metrics.srs_json_valid = s_success
            metrics.srs_schema_valid = s_schema
            metrics.srs_error = s_err

            if not s_success:
                print(f"  SRS failed: {s_err}")
                metrics.total_latency_seconds = metrics.analysis_latency_seconds + metrics.clarification_latency_seconds + metrics.srs_latency_seconds
                return metrics

            # Extract SRS metrics
            version = srs_svc.get_version(project_id, srs_result.version_id)
            srs_metrics = self._extract_srs_metrics(version.srs)
            for k, v in srs_metrics.items():
                setattr(metrics, k, v)

            # Apply RAG metrics
            for k, v in rag_metrics.items():
                setattr(metrics, k, v)

            metrics.total_latency_seconds = (
                metrics.analysis_latency_seconds
                + metrics.clarification_latency_seconds
                + metrics.srs_latency_seconds
            )

            print(f"  SRS OK - {metrics.requirement_count} reqs, {metrics.threat_count} threats")
            if use_rag:
                print(f"  RAG: chunks={rag_metrics.get('chunks_retrieved', 0)}, "
                      f"citations={rag_metrics.get('citations_present', 0)}, "
                      f"precision={rag_metrics.get('citation_precision', 0):.2f}")

            return metrics
        finally:
            session.close()

    def run_configuration(self, use_rag: bool, case_ids: list[str] | None = None, max_cases: int | None = None, provider_name: str = "mock") -> list[RAGCaseMetrics]:
        """Run evaluation for one configuration (base or RAG)."""
        dataset = self.load_dataset()

        if case_ids:
            cases = [c for c in dataset if c["id"] in case_ids]
        else:
            cases = dataset

        if max_cases:
            cases = cases[:max_cases]

        config_name = "BASE_QWEN_RAG" if use_rag else "BASE_QWEN"
        print(f"\n{'#'*60}")
        print(f"# Starting {config_name} evaluation (provider: {provider_name})")
        print(f"# Run ID: {self.run_id}")
        print(f"# Cases: {len(cases)}")
        print(f"{'#'*60}")

        # Set provider
        self.settings.llm_provider = provider_name

        results = []
        for case in cases:
            try:
                metrics = self.run_case(case, use_rag)
                results.append(metrics)
            except Exception as e:
                print(f"Case {case['id']} failed: {e}")
                metrics = RAGCaseMetrics(
                    case_id=case["id"],
                    description=case["description"],
                    expected_categories=case.get("expected_categories", []),
                    analysis_error=str(e),
                )
                results.append(metrics)

        return results

    def run_comparison(
        self,
        case_ids: list[str] | None = None,
        max_cases: int | None = None,
        provider_name: str = "mock",
    ) -> tuple[AggregateMetrics, RAGAggregateMetrics]:
        """Run both configurations and compute comparison."""
        print(f"\n{'#'*60}")
        print(f"# Running BASE_QWEN (no RAG) with {provider_name}")
        print(f"{'#'*60}")
        self.base_results = self.run_configuration(False, case_ids, max_cases, provider_name)

        print(f"\n{'#'*60}")
        print(f"# Running BASE_QWEN_RAG (with RAG) with {provider_name}")
        print(f"{'#'*60}")
        self.rag_results = self.run_configuration(True, case_ids, max_cases, provider_name)

        base_by_case = {m.case_id: m for m in self.base_results}
        for rag_metric in self.rag_results:
            base_metric = base_by_case.get(rag_metric.case_id)
            if base_metric and base_metric.srs_success and rag_metric.srs_success:
                rag_metric.rag_overhead_seconds = (
                    rag_metric.srs_latency_seconds - base_metric.srs_latency_seconds
                )

        # Compute aggregates
        base_agg = compute_aggregate(self.base_results)
        rag_agg = compute_rag_aggregate(self.rag_results)

        # Save results
        self.save_results(base_agg, rag_agg, provider_name)

        return base_agg, rag_agg

    def save_results(self, base_agg: AggregateMetrics, rag_agg: RAGAggregateMetrics, provider_name: str = "mock") -> None:
        run_dir = self.output_dir / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Determine model name based on provider
        if provider_name == "ollama":
            model_name = resolve_model_name(self.settings)
        else:
            model_name = "cybersrs-mock-1b"

        # Save individual case metrics
        base_cases_file = run_dir / "base_case_metrics.json"
        with open(base_cases_file, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.base_results], f, indent=2)

        rag_cases_file = run_dir / "rag_case_metrics.json"
        with open(rag_cases_file, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.rag_results], f, indent=2)

        # Save aggregates
        base_agg_file = run_dir / "base_aggregate_metrics.json"
        with open(base_agg_file, "w", encoding="utf-8") as f:
            json.dump(base_agg.to_dict(), f, indent=2)

        rag_agg_file = run_dir / "rag_aggregate_metrics.json"
        with open(rag_agg_file, "w", encoding="utf-8") as f:
            json.dump(rag_agg.to_dict(), f, indent=2)

        # Save comparison
        comparison = self.compute_comparison(base_agg, rag_agg)
        comp_file = run_dir / "comparison.json"
        with open(comp_file, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)

        # Save run metadata
        meta = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "provider": provider_name,
            "model_name": model_name,
            "embedding_model": "nomic-embed-text",
            "vector_db": "ChromaDB",
            "dataset_path": self.dataset_path,
            "total_cases_base": len(self.base_results),
            "total_cases_rag": len(self.rag_results),
            "rag_config": {
                "enabled": True,
                "top_k": self.settings.rag_top_k,
                "min_score": self.settings.rag_min_score,
                "collection": self.settings.chroma_collection,
            },
        }
        meta_file = run_dir / "run_metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Save human-readable report
        report_file = run_dir / "comparison_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(self.format_comparison_report(base_agg, rag_agg, comparison))

        print(f"\nResults saved to: {run_dir}")
        print(f"  - {base_cases_file}")
        print(f"  - {rag_cases_file}")
        print(f"  - {base_agg_file}")
        print(f"  - {rag_agg_file}")
        print(f"  - {comp_file}")
        print(f"  - {meta_file}")
        print(f"  - {report_file}")

    def compute_comparison(self, base: AggregateMetrics, rag: RAGAggregateMetrics) -> dict[str, Any]:
        """Compute comparison deltas."""
        return {
            "base_metrics": base.to_dict(),
            "rag_metrics": rag.to_dict(),
            "absolute_differences": {
                "analysis_success_rate": rag.analysis_success_rate - base.analysis_success_rate,
                "clarification_success_rate": rag.clarification_success_rate - base.clarification_success_rate,
                "srs_success_rate": rag.srs_success_rate - base.srs_success_rate,
                "analysis_schema_validity_rate": rag.analysis_schema_validity_rate - base.analysis_schema_validity_rate,
                "clarification_schema_validity_rate": rag.clarification_schema_validity_rate - base.clarification_schema_validity_rate,
                "srs_schema_validity_rate": rag.srs_schema_validity_rate - base.srs_schema_validity_rate,
                "category_accuracy_mean": rag.category_accuracy_mean - base.category_accuracy_mean,
                "avg_requirements_per_srs": rag.avg_requirements_per_srs - base.avg_requirements_per_srs,
                "duplicate_id_rate": rag.duplicate_id_rate - base.duplicate_id_rate,
                "missing_statement_rate": rag.missing_statement_rate - base.missing_statement_rate,
                "missing_acceptance_rate": rag.missing_acceptance_rate - base.missing_acceptance_rate,
                "invalid_priority_rate": rag.invalid_priority_rate - base.invalid_priority_rate,
                "avg_questions_per_case": rag.avg_questions_per_case - base.avg_questions_per_case,
                "target_gap_coverage_rate": rag.target_gap_coverage_rate - base.target_gap_coverage_rate,
                "avg_analysis_latency": rag.avg_analysis_latency - base.avg_analysis_latency,
                "avg_clarification_latency": rag.avg_clarification_latency - base.avg_clarification_latency,
                "avg_srs_latency": rag.avg_srs_latency - base.avg_srs_latency,
                "avg_total_latency": rag.avg_total_latency - base.avg_total_latency,
                "avg_retry_count": rag.avg_retry_count - base.avg_retry_count,
            },
            "rag_specific": {
                "retrieval_success_rate": rag.retrieval_success_rate,
                "avg_retrieval_latency": rag.avg_retrieval_latency,
                "avg_chunks_retrieved": rag.avg_chunks_retrieved,
                "citation_presence_rate": rag.citation_presence_rate,
                "citation_validity_rate": rag.citation_validity_rate,
                "citation_precision_mean": rag.citation_precision_mean,
                "citation_support_mean": rag.citation_support_mean,
                "unsupported_citation_rate": rag.unsupported_citation_rate,
                "relevant_source_retrieval_mean": rag.relevant_source_retrieval_mean,
                "security_req_coverage_mean": rag.security_req_coverage_mean,
                "hallucination_indicator_rate": rag.hallucination_indicator_rate,
                "avg_rag_overhead": rag.avg_rag_overhead,
            },
        }

    def format_comparison_report(self, base: AggregateMetrics, rag: RAGAggregateMetrics, comp: dict) -> str:
        diff = comp["absolute_differences"]
        rag_spec = comp["rag_specific"]

        # Determine model display name
        provider = self.settings.llm_provider
        if provider == "ollama":
            model_display = f"{self.settings.model_name} (Ollama)"
        else:
            model_display = "cybersrs-mock-1b (mock)"

        lines = [
            "=" * 70,
            "CYBERSRS COMPARATIVE EVALUATION REPORT",
            "=" * 70,
            f"Run ID: {self.run_id}",
            f"Timestamp: {self.timestamp}",
            f"Provider: {provider}",
            f"Model: {model_display}",
            "Embedding: nomic-embed-text",
            f"Vector DB: ChromaDB ({self.settings.chroma_collection}, 4470 chunks)",
            f"Cases: {base.total_cases} (same held-out set for both)",
            "",
            "=" * 70,
            "1. BASE METRICS (BASE_QWEN)",
            "=" * 70,
            f"  Total Cases:          {base.total_cases}",
            f"  Fully Successful:     {base.successful_cases}",
            f"  Analysis Success:     {base.analysis_success_rate:.1%}",
            f"  Clarification Succ:   {base.clarification_success_rate:.1%}",
            f"  SRS Success:          {base.srs_success_rate:.1%}",
            f"  Analysis Schema Valid: {base.analysis_schema_validity_rate:.1%}",
            f"  SRS Schema Valid:      {base.srs_schema_validity_rate:.1%}",
            f"  Category Accuracy:     {base.category_accuracy_mean:.3f} ± {base.category_accuracy_std:.3f}",
            f"  Avg Requirements/SRS:  {base.avg_requirements_per_srs:.1f}",
            f"  Duplicate ID Rate:     {base.duplicate_id_rate:.3f}",
            f"  Missing Statement:     {base.missing_statement_rate:.3f}",
            f"  Missing Acceptance:    {base.missing_acceptance_rate:.3f}",
            f"  Invalid Priority:      {base.invalid_priority_rate:.3f}",
            f"  Avg Questions/Case:    {base.avg_questions_per_case:.1f}",
            f"  Target Gap Coverage:   {base.target_gap_coverage_rate:.1%}",
            f"  Avg Analysis Latency:  {base.avg_analysis_latency:.2f}s",
            f"  Avg Clarification Lat: {base.avg_clarification_latency:.2f}s",
            f"  Avg SRS Latency:       {base.avg_srs_latency:.2f}s",
            f"  Avg Total Latency:     {base.avg_total_latency:.2f}s",
            "",
            "=" * 70,
            "2. RAG METRICS (BASE_QWEN_RAG)",
            "=" * 70,
            f"  Total Cases:          {rag.total_cases}",
            f"  Fully Successful:     {rag.successful_cases}",
            f"  Analysis Success:     {rag.analysis_success_rate:.1%}",
            f"  Clarification Succ:   {rag.clarification_success_rate:.1%}",
            f"  SRS Success:          {rag.srs_success_rate:.1%}",
            f"  Analysis Schema Valid: {rag.analysis_schema_validity_rate:.1%}",
            f"  SRS Schema Valid:      {rag.srs_schema_validity_rate:.1%}",
            f"  Category Accuracy:     {rag.category_accuracy_mean:.3f} ± {rag.category_accuracy_std:.3f}",
            f"  Avg Requirements/SRS:  {rag.avg_requirements_per_srs:.1f}",
            f"  Duplicate ID Rate:     {rag.duplicate_id_rate:.3f}",
            f"  Missing Statement:     {rag.missing_statement_rate:.3f}",
            f"  Missing Acceptance:    {rag.missing_acceptance_rate:.3f}",
            f"  Invalid Priority:      {rag.invalid_priority_rate:.3f}",
            f"  Avg Questions/Case:    {rag.avg_questions_per_case:.1f}",
            f"  Target Gap Coverage:   {rag.target_gap_coverage_rate:.1%}",
            f"  Avg Analysis Latency:  {rag.avg_analysis_latency:.2f}s",
            f"  Avg Clarification Lat: {rag.avg_clarification_latency:.2f}s",
            f"  Avg SRS Latency:       {rag.avg_srs_latency:.2f}s",
            f"  Avg Total Latency:     {rag.avg_total_latency:.2f}s",
            "",
            "--- RAG-Specific Metrics ---",
            f"  Retrieval Success:     {rag_spec['retrieval_success_rate']:.1%}",
            f"  Avg Retrieval Latency: {rag_spec['avg_retrieval_latency']:.2f}s",
            f"  Avg Chunks Retrieved:  {rag_spec['avg_chunks_retrieved']:.1f}",
            f"  Citation Presence:     {rag_spec['citation_presence_rate']:.1%}",
            f"  Citation Validity:     {rag_spec['citation_validity_rate']:.1%}",
            f"  Citation Precision:    {rag_spec['citation_precision_mean']:.3f}",
            f"  Citation Support:      {rag_spec['citation_support_mean']:.3f}",
            f"  Unsupported Cites:     {rag_spec['unsupported_citation_rate']:.3f}",
            f"  Relevant Source Retrieval: {rag_spec['relevant_source_retrieval_mean']:.3f}",
            f"  Security Req Coverage: {rag_spec['security_req_coverage_mean']:.3f}",
            f"  Hallucination Rate:    {rag_spec['hallucination_indicator_rate']:.3f}",
            f"  RAG Overhead:          {rag_spec['avg_rag_overhead']:.2f}s",
            "",
            "=" * 70,
            "3. ABSOLUTE DIFFERENCES (RAG - BASE)",
            "=" * 70,
            f"  Analysis Success Rate:      {diff['analysis_success_rate']:+.3f}",
            f"  Clarification Success Rate: {diff['clarification_success_rate']:+.3f}",
            f"  SRS Success Rate:           {diff['srs_success_rate']:+.3f}",
            f"  Analysis Schema Validity:   {diff['analysis_schema_validity_rate']:+.3f}",
            f"  SRS Schema Validity:        {diff['srs_schema_validity_rate']:+.3f}",
            f"  Category Accuracy:          {diff['category_accuracy_mean']:+.3f}",
            f"  Avg Requirements/SRS:       {diff['avg_requirements_per_srs']:+.1f}",
            f"  Duplicate ID Rate:          {diff['duplicate_id_rate']:+.3f}",
            f"  Missing Statement Rate:     {diff['missing_statement_rate']:+.3f}",
            f"  Missing Acceptance Rate:    {diff['missing_acceptance_rate']:+.3f}",
            f"  Invalid Priority Rate:      {diff['invalid_priority_rate']:+.3f}",
            f"  Avg Questions/Case:         {diff['avg_questions_per_case']:+.1f}",
            f"  Target Gap Coverage:        {diff['target_gap_coverage_rate']:+.3f}",
            f"  Avg Analysis Latency:       {diff['avg_analysis_latency']:+.2f}s",
            f"  Avg Clarification Latency:  {diff['avg_clarification_latency']:+.2f}s",
            f"  Avg SRS Latency:            {diff['avg_srs_latency']:+.2f}s",
            f"  Avg Total Latency:          {diff['avg_total_latency']:+.2f}s",
            "",
            "=" * 70,
            "4. ANALYSIS",
            "=" * 70,
            self._analyze_results(diff, rag_spec),
            "",
            "=" * 70,
            "5. MILESTONE STATUS",
            "=" * 70,
            self._milestone_status(rag, rag_spec),
            "",
            "=" * 70,
            "6. RESULT LOCATIONS",
            "=" * 70,
            f"  Base case metrics:    ai/evaluation/results/{self.run_id}/base_case_metrics.json",
            f"  RAG case metrics:     ai/evaluation/results/{self.run_id}/rag_case_metrics.json",
            f"  Base aggregate:       ai/evaluation/results/{self.run_id}/base_aggregate_metrics.json",
            f"  RAG aggregate:        ai/evaluation/results/{self.run_id}/rag_aggregate_metrics.json",
            f"  Comparison JSON:      ai/evaluation/results/{self.run_id}/comparison.json",
            f"  Run metadata:         ai/evaluation/results/{self.run_id}/run_metadata.json",
            f"  Human report:         ai/evaluation/results/{self.run_id}/comparison_report.txt",
        ]
        return "\n".join(lines)

    def _analyze_results(self, diff: dict, rag_spec: dict) -> str:
        lines = []

        # Improvements
        improvements = []
        if diff["srs_schema_validity_rate"] > 0.02:
            improvements.append(f"SRS schema validity improved by {diff['srs_schema_validity_rate']:.1%}")
        if diff["category_accuracy_mean"] > 0.02:
            improvements.append(f"Category accuracy improved by {diff['category_accuracy_mean']:.3f}")
        if rag_spec["citation_precision_mean"] > 0.5:
            improvements.append(f"Citation precision: {rag_spec['citation_precision_mean']:.1%}")
        if rag_spec["citation_presence_rate"] > 0.5:
            improvements.append(f"Citations present in {rag_spec['citation_presence_rate']:.1%} of cases")
        if diff["missing_acceptance_rate"] < -0.02:
            improvements.append(f"Missing acceptance criteria reduced by {abs(diff['missing_acceptance_rate']):.1%}")
        if rag_spec["security_req_coverage_mean"] > 0.7:
            improvements.append(f"Security requirement coverage: {rag_spec['security_req_coverage_mean']:.1%}")
        if rag_spec["hallucination_indicator_rate"] < 0.1:
            improvements.append(f"Low hallucination indicator rate: {rag_spec['hallucination_indicator_rate']:.1%}")

        if improvements:
            lines.append("IMPROVEMENTS WITH RAG:")
            for imp in improvements:
                lines.append(f"  + {imp}")
        else:
            lines.append("IMPROVEMENTS WITH RAG: None significant")

        lines.append("")

        # Regressions
        regressions = []
        if diff["avg_srs_latency"] > 5.0:
            regressions.append(f"SRS latency increased by {diff['avg_srs_latency']:.1f}s (RAG overhead)")
        if diff["avg_total_latency"] > 10.0:
            regressions.append(f"Total latency increased by {diff['avg_total_latency']:.1f}s")
        if diff["duplicate_id_rate"] > 0.02:
            regressions.append(f"Duplicate ID rate increased by {diff['duplicate_id_rate']:.1%}")
        if rag_spec["unsupported_citation_rate"] > 0.2:
            regressions.append(f"High unsupported citation rate: {rag_spec['unsupported_citation_rate']:.1%}")
        if diff["category_accuracy_mean"] < -0.02:
            regressions.append(f"Category accuracy decreased by {abs(diff['category_accuracy_mean']):.3f}")
        if rag_spec["retrieval_success_rate"] < 0.9:
            regressions.append(f"Retrieval success rate only {rag_spec['retrieval_success_rate']:.1%}")

        if regressions:
            lines.append("REGRESSIONS WITH RAG:")
            for reg in regressions:
                lines.append(f"  - {reg}")
        else:
            lines.append("REGRESSIONS WITH RAG: None significant")

        lines.append("")

        # Unchanged
        lines.append("UNCHANGED:")
        if abs(diff["analysis_success_rate"]) < 0.02:
            lines.append("  - Analysis success rate")
        if abs(diff["clarification_success_rate"]) < 0.02:
            lines.append("  - Clarification success rate")
        if abs(diff["srs_success_rate"]) < 0.02:
            lines.append("  - SRS success rate")
        if abs(diff["avg_requirements_per_srs"]) < 0.5:
            lines.append("  - Requirements per SRS")
        if abs(diff["missing_statement_rate"]) < 0.02:
            lines.append("  - Missing statement rate")
        if abs(diff["invalid_priority_rate"]) < 0.02:
            lines.append("  - Invalid priority rate")

        lines.append("")

        # Retrieval failures
        if rag_spec["retrieval_success_rate"] < 1.0:
            lines.append(f"RETRIEVAL FAILURES: {1 - rag_spec['retrieval_success_rate']:.1%} of cases had retrieval issues")

        # Citation failures
        if rag_spec["unsupported_citation_rate"] > 0.1:
            lines.append(f"CITATION FAILURES: {rag_spec['unsupported_citation_rate']:.1%} of citations unsupported")

        # Latency cost
        lines.append(f"LATENCY COST: RAG adds ~{rag_spec['avg_rag_overhead']:.1f}s overhead per SRS generation")

        # Cases where irrelevant context hurt
        if rag_spec["hallucination_indicator_rate"] > 0.15:
            lines.append("WARNING: Elevated hallucination indicators suggest irrelevant context may be degrading output")

        return "\n".join(lines)

    def _milestone_status(self, rag: RAGAggregateMetrics, rag_spec: dict) -> str:
        """Determine if RAG milestone passes."""
        checks = [
            ("Retrieval success >= 90%", rag_spec["retrieval_success_rate"] >= 0.9),
            ("Citation presence >= 50%", rag_spec["citation_presence_rate"] >= 0.5),
            ("Citation precision >= 70%", rag_spec["citation_precision_mean"] >= 0.7),
            ("Unsupported citations <= 20%", rag_spec["unsupported_citation_rate"] <= 0.2),
            ("Schema validity >= 95%", rag.srs_schema_validity_rate >= 0.95),
            ("Security coverage >= 50%", rag_spec["security_req_coverage_mean"] >= 0.5),
            ("Latency overhead <= 30s", rag_spec["avg_rag_overhead"] <= 30),
            ("Hallucination rate <= 15%", rag_spec["hallucination_indicator_rate"] <= 0.15),
        ]

        passed = sum(1 for _, p in checks if p)
        total = len(checks)

        lines = [f"RAG Milestone Checks: {passed}/{total} passed", ""]
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            lines.append(f"  [{status}] {name}")

        lines.append("")
        if passed == total:
            lines.append("OVERALL: RAG MILESTONE PASSES")
        elif passed >= total * 0.75:
            lines.append("OVERALL: RAG MILESTONE PARTIAL - Minor issues to address")
        else:
            lines.append("OVERALL: RAG MILESTONE FAILS - Significant issues")

        return "\n".join(lines)


def compute_rag_aggregate(metrics_list: list[RAGCaseMetrics]) -> RAGAggregateMetrics:
    """Compute aggregate metrics including RAG-specific fields."""
    base_agg = compute_aggregate(metrics_list)

    if not metrics_list:
        return RAGAggregateMetrics()

    total = len(metrics_list)
    srs_successful = [m for m in metrics_list if m.srs_success]

    # RAG-specific aggregates
    retrieval_attempted = sum(1 for m in metrics_list if m.retrieval_attempted)
    retrieval_success = sum(1 for m in metrics_list if m.retrieval_success)
    total_chunks = sum(m.chunks_retrieved for m in metrics_list)
    retrieval_latencies = [m.retrieval_latency_seconds for m in metrics_list if m.retrieval_attempted]

    total_citations = sum(m.citations_present for m in metrics_list)
    total_valid_cites = sum(m.citations_valid for m in metrics_list)
    total_unsupported = sum(m.unsupported_citation_count for m in metrics_list)

    citation_precisions = [m.citation_precision for m in metrics_list if m.citations_present > 0]
    citation_supports = [m.citation_support for m in metrics_list if m.citations_present > 0]
    security_coverages = [m.security_req_coverage for m in srs_successful]
    hallucinations = sum(m.hallucination_indicators for m in srs_successful)
    total_reqs = sum(m.requirement_count for m in srs_successful)

    rag_overheads = [m.rag_overhead_seconds for m in metrics_list if m.rag_overhead_seconds > 0]

    return RAGAggregateMetrics(
        total_cases=base_agg.total_cases,
        successful_cases=base_agg.successful_cases,
        analysis_success_rate=base_agg.analysis_success_rate,
        clarification_success_rate=base_agg.clarification_success_rate,
        srs_success_rate=base_agg.srs_success_rate,
        analysis_json_validity_rate=base_agg.analysis_json_validity_rate,
        analysis_schema_validity_rate=base_agg.analysis_schema_validity_rate,
        clarification_json_validity_rate=base_agg.clarification_json_validity_rate,
        clarification_schema_validity_rate=base_agg.clarification_schema_validity_rate,
        srs_json_validity_rate=base_agg.srs_json_validity_rate,
        srs_schema_validity_rate=base_agg.srs_schema_validity_rate,
        category_accuracy_mean=base_agg.category_accuracy_mean,
        category_accuracy_std=base_agg.category_accuracy_std,
        total_requirements=base_agg.total_requirements,
        avg_requirements_per_srs=base_agg.avg_requirements_per_srs,
        duplicate_id_rate=base_agg.duplicate_id_rate,
        missing_statement_rate=base_agg.missing_statement_rate,
        missing_acceptance_rate=base_agg.missing_acceptance_rate,
        invalid_priority_rate=base_agg.invalid_priority_rate,
        avg_questions_per_case=base_agg.avg_questions_per_case,
        target_gap_coverage_rate=base_agg.target_gap_coverage_rate,
        avg_analysis_latency=base_agg.avg_analysis_latency,
        avg_clarification_latency=base_agg.avg_clarification_latency,
        avg_srs_latency=base_agg.avg_srs_latency,
        avg_total_latency=base_agg.avg_total_latency,
        avg_retry_count=base_agg.avg_retry_count,
        analysis_failure_count=base_agg.analysis_failure_count,
        clarification_failure_count=base_agg.clarification_failure_count,
        srs_failure_count=base_agg.srs_failure_count,
        retrieval_success_rate=retrieval_success / retrieval_attempted if retrieval_attempted else 0.0,
        avg_retrieval_latency=sum(retrieval_latencies) / len(retrieval_latencies) if retrieval_latencies else 0.0,
        avg_chunks_retrieved=total_chunks / total if total else 0.0,
        citation_presence_rate=sum(1 for m in metrics_list if m.citations_present > 0) / total if total else 0.0,
        citation_validity_rate=total_valid_cites / total_citations if total_citations else 0.0,
        citation_precision_mean=sum(citation_precisions) / len(citation_precisions) if citation_precisions else 0.0,
        citation_support_mean=sum(citation_supports) / len(citation_supports) if citation_supports else 0.0,
        unsupported_citation_rate=total_unsupported / total_citations if total_citations else 0.0,
        relevant_source_retrieval_mean=0.0,
        security_req_coverage_mean=sum(security_coverages) / len(security_coverages) if security_coverages else 0.0,
        hallucination_indicator_rate=hallucinations / total_reqs if total_reqs else 0.0,
        avg_rag_overhead=sum(rag_overheads) / len(rag_overheads) if rag_overheads else 0.0,
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CyberSRS Comparative Evaluation: Base vs RAG")
    parser.add_argument("--case-ids", nargs="+", help="Specific case IDs to evaluate")
    parser.add_argument("--max-cases", type=int, help="Maximum number of cases to evaluate")
    parser.add_argument("--dataset", default="ai/evaluation/dataset.json", help="Dataset path")
    parser.add_argument("--output-dir", default="ai/evaluation/results", help="Output directory")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test (3 cases)")
    parser.add_argument("--provider", choices=["mock", "ollama"], default="mock", help="LLM provider to use")
    args = parser.parse_args()

    max_cases = 3 if args.smoke else args.max_cases

    runner = DirectComparativeRunner(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
    )
    runner.run_comparison(case_ids=args.case_ids, max_cases=max_cases, provider_name=args.provider)


if __name__ == "__main__":
    main()
