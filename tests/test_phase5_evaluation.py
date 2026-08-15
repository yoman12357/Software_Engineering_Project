"""Final integration coverage for the canonical Phase 5 evaluator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from ai.evaluation.phase5_metrics import ConfigVariant, parse_raw_output
from ai.evaluation.phase5_runner import (
    CapturingProvider,
    Phase5EvaluationRunner,
    ollama_model_available,
    parse_configs,
    validate_official_dataset_path,
)
from src.core.config import Settings
from src.db.database import Database
from src.db.models import Phase5CaseResult, Phase5EvaluationRun
from src.llm.base import LLMProvider, LLMRequest, LLMResponse, LLMTask
from src.main import create_app as production_create_app


def _write_dataset(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "id": "heldout-test-001",
                    "description": "A campus firewall with segmented networks.",
                    "expected_categories": ["CAT-02", "CAT-03"],
                }
            ]
        ),
        encoding="utf-8",
    )


def test_exact_four_configuration_matrix_and_cli_spellings() -> None:
    """The runner exposes one canonical four-way matrix."""
    assert ConfigVariant.all() == (
        ConfigVariant.BASE,
        ConfigVariant.BASE_RAG,
        ConfigVariant.FINETUNED,
        ConfigVariant.FINETUNED_RAG,
    )
    assert [(item.model_variant, item.rag_enabled) for item in ConfigVariant.all()] == [
        ("base", False),
        ("base", True),
        ("finetuned", False),
        ("finetuned", True),
    ]
    assert parse_configs("all") == ConfigVariant.all()
    assert parse_configs("finetuned-rag") == (ConfigVariant.FINETUNED_RAG,)


def test_training_and_validation_files_are_rejected() -> None:
    """Official Phase 5 execution cannot consume fine-tuning inputs."""
    for path in (
        "ai/finetuning/data/train.jsonl",
        "ai/finetuning/data/validation.jsonl",
    ):
        with pytest.raises(ValueError, match="held-out"):
            validate_official_dataset_path(path)


def test_raw_parser_does_not_hide_markdown_repair() -> None:
    """Recoverable fenced output remains marked invalid as raw JSON."""
    payload, strictly_valid = parse_raw_output('```json\n{"value": 1}\n```')
    assert payload == {"value": 1}
    assert strictly_valid is False


def test_capturing_provider_preserves_first_raw_output_and_all_attempts() -> None:
    """Retry capture keeps untouched first-attempt evidence."""
    class SequenceProvider(LLMProvider):
        provider_name = "sequence"

        def __init__(self) -> None:
            super().__init__("sequence-model")
            self.index = 0

        def generate(self, request: LLMRequest) -> LLMResponse:
            self.index += 1
            return LLMResponse(
                content=f"raw-attempt-{self.index}",
                model_name=self.model_name,
            )

    provider = CapturingProvider(SequenceProvider())
    request = LLMRequest(task=LLMTask.SRS, system_prompt="s", user_content="u")
    provider.generate(request)
    provider.generate(request)

    assert provider.outputs[LLMTask.SRS] == "raw-attempt-1"
    assert provider.attempt_outputs[LLMTask.SRS] == [
        "raw-attempt-1",
        "raw-attempt-2",
    ]


def test_runner_writes_portable_artifacts_and_database_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A completed base run keeps raw/final metrics and persists associations."""
    dataset = tmp_path / "heldout.json"
    _write_dataset(dataset)

    def create_mock_app(settings: Settings):
        values = settings.model_dump()
        values["llm_provider"] = "mock"
        values["rag_enabled"] = False
        return production_create_app(Settings(_env_file=None, **values))

    monkeypatch.setattr("ai.evaluation.phase5_runner.create_app", create_mock_app)
    runner = Phase5EvaluationRunner(
        dataset_path=dataset,
        output_dir=tmp_path / "results",
        configs=(ConfigVariant.BASE,),
        settings=Settings(_env_file=None, llm_provider="mock"),
        availability_check=lambda _settings, _model: (True, None),
    )
    summary = runner.run_all()

    assert summary["configurations"][0]["status"] == "COMPLETED"
    assert {path.name for path in runner.run_dir.iterdir()} >= {
        "summary.json",
        "per_case_results.json",
        "comparison.md",
        "evaluation.sqlite",
    }
    case_results = json.loads(
        (runner.run_dir / "per_case_results.json").read_text(encoding="utf-8")
    )
    assert len(case_results) == 1
    assert case_results[0]["raw_output"]
    assert case_results[0]["raw_attempts"] == [case_results[0]["raw_output"]]
    assert case_results[0]["generation_attempts"][0]["status"] == "valid"
    assert case_results[0]["final_output"]
    assert case_results[0]["raw_metrics"] is not case_results[0]["final_metrics"]
    assert case_results[0]["evaluation_run_id"].endswith("-base")

    database = Database(runner.database_url)
    with database.session_factory() as session:
        run = session.scalar(select(Phase5EvaluationRun))
        case = session.scalar(select(Phase5CaseResult))
        assert run is not None and run.status == "completed"
        assert case is not None and case.evaluation_run_id == run.id
        assert case.raw_metrics and case.final_metrics
    database.engine.dispose()


def test_unavailable_finetuned_config_has_no_fake_zero_metrics(tmp_path: Path) -> None:
    """Missing adapters produce UNAVAILABLE rather than zero-valued results."""
    dataset = tmp_path / "heldout.json"
    _write_dataset(dataset)
    runner = Phase5EvaluationRunner(
        dataset_path=dataset,
        output_dir=tmp_path / "results",
        configs=(ConfigVariant.FINETUNED,),
        settings=Settings(_env_file=None),
        availability_check=lambda _settings, _model: (False, "model unavailable"),
    )
    summary = runner.run_all()
    config = summary["configurations"][0]
    assert config["status"] == "UNAVAILABLE"
    assert config["raw_metrics"] is None
    assert config["final_metrics"] is None
    assert json.loads(
        (runner.run_dir / "per_case_results.json").read_text(encoding="utf-8")
    ) == []


def test_ollama_availability_accepts_implicit_latest_tag(monkeypatch) -> None:
    """A canonical name matches the `:latest` name returned by Ollama tags."""
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"models": [{"name": "cybersrs-qwen3-4b-ft:latest"}]}

    monkeypatch.setattr("ai.evaluation.phase5_runner.httpx.get", lambda *_a, **_k: Response())
    available, error = ollama_model_available(
        Settings(_env_file=None), "cybersrs-qwen3-4b-ft"
    )
    assert available is True
    assert error is None
