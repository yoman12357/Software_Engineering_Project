"""SQLAlchemy ORM models.

Phase 1A implements full CRUD only for :class:`Project`. The remaining tables
mirror the entities defined in ``DATA_MODEL.md`` so the Phase 1 completion
gate ("SQLite schema includes all entities from DATA_MODEL.md") is satisfied
and future phases can build on a stable schema. Foreign keys use
``ondelete="CASCADE"`` and ORM relationships use ``cascade="all, delete-orphan"``
so SEC-047 (delete all associated data when a project is deleted) is enforced
from the data layer.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from .database import Base


class UTCDateTime(TypeDecorator):
    """Store timezone-aware UTC datetimes in a naive SQLite column.

    SQLite does not persist ``tzinfo``; this decorator normalises values to
    naive UTC on write and restores the UTC timezone on read, so timestamps
    round-trip as ISO 8601 UTC (DATA_MODEL / API_CONTRACT).
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        """Strip tzinfo so SQLite stores naive UTC."""
        if value is None or value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        """Restore the UTC timezone on read."""
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=UTC)


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)


class Project(Base):
    """A user's cybersecurity project (DATA_MODEL §2.1)."""

    __tablename__ = "project"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    inferred_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships used for cascade deletion (SEC-047).
    descriptions: Mapped[list[ProjectDescription]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    clarification_questions: Mapped[list[ClarificationQuestion]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    contexts: Mapped[list[ProjectContext]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    srs_versions: Mapped[list[SRSVersion]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    model_runs: Mapped[list[ModelRun]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectDescription(Base):
    """Versioned informal project description (DATA_MODEL §2.2).

    Phase 1A stores the description directly on :class:`Project` for the
    project CRUD API; this table is the versioned long-term representation
    exercised by later phases.
    """

    __tablename__ = "project_description"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

    project: Mapped[Project] = relationship(back_populates="descriptions")


class ClarificationQuestion(Base):
    """Clarification question generated for a project (DATA_MODEL §2.3).

    ``id`` is a UUID primary key; ``stable_id`` carries the human-readable
    per-project identifier (``q-001`` …) that the API exposes. The
    ``(project_id, stable_id)`` unique constraint keeps stable IDs unique
    within a project while allowing different projects to reuse ``q-001``.
    """

    __tablename__ = "clarification_question"
    __table_args__ = (
        UniqueConstraint("project_id", "stable_id", name="uq_clarification_project_stable"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stable_id: Mapped[str] = mapped_column(String(10), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Phase 1B additions: the expected answer type and the gap this question
    # targets (PROMPT_AND_OUTPUT_DESIGN §2.4 / task requirements).
    expected_answer_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    target_gap: Mapped[str] = mapped_column(Text, nullable=False, default="")
    model_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_run.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

    project: Mapped[Project] = relationship(back_populates="clarification_questions")
    model_run: Mapped[ModelRun | None] = relationship(back_populates="clarification_questions")
    answers: Mapped[list[ClarificationAnswer]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    @property
    def answer(self) -> ClarificationAnswer | None:
        """Return the first answer for this question, or None.

        A convenience used by API serialisation models
        (:class:`ClarificationQuestionRead`) so ``from_attributes`` exposes a
        singular ``answer`` attribute even though the relationship is plural.
        """
        if not self.answers:
            return None
        return self.answers[0]


class ClarificationAnswer(Base):
    """User's answer to a clarification question (DATA_MODEL §2.4)."""

    __tablename__ = "clarification_answer"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_id: Mapped[str] = mapped_column(
        ForeignKey("clarification_question.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

    question: Mapped[ClarificationQuestion] = relationship(back_populates="answers")

    @property
    def api_question_id(self) -> str:
        """Expose the stable question ID (``q-001``) to API serialisation."""
        return self.question.stable_id


class ProjectContext(Base):
    """Structured, enriched representation of a project (DATA_MODEL §2.5)."""

    __tablename__ = "project_context"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stakeholders: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    assets: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    users: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    constraints: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    goals: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    inferred_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    enriched_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_run.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False, default=utcnow, onupdate=utcnow
    )

    project: Mapped[Project] = relationship(back_populates="contexts")
    model_run: Mapped[ModelRun | None] = relationship(back_populates="project_contexts")


class SRSVersion(Base):
    """A versioned snapshot of a generated SRS (DATA_MODEL §2.6)."""

    __tablename__ = "srs_version"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    srs_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

    # Model provenance (Phase 8)
    model_variant: Mapped[str | None] = mapped_column(String(20), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    adapter_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rag_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    generation_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_run.id", ondelete="SET NULL"), nullable=True, index=True
    )

    project: Mapped[Project] = relationship(back_populates="srs_versions")
    model_run: Mapped[ModelRun | None] = relationship(back_populates="srs_versions")
    requirements: Mapped[list[Requirement]] = relationship(
        back_populates="srs_version", cascade="all, delete-orphan"
    )
    acceptance_criteria: Mapped[list[AcceptanceCriterion]] = relationship(
        back_populates="srs_version", cascade="all, delete-orphan"
    )
    threats: Mapped[list[Threat]] = relationship(
        back_populates="srs_version", cascade="all, delete-orphan"
    )
    generation_runs: Mapped[list[GenerationRun]] = relationship(
        back_populates="srs_version", cascade="all, delete-orphan"
    )
    exports: Mapped[list[ExportedDocument]] = relationship(
        back_populates="srs_version", cascade="all, delete-orphan"
    )


class Requirement(Base):
    """A single requirement within an SRS version (DATA_MODEL §2.7)."""

    __tablename__ = "requirement"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    srs_version_id: Mapped[str] = mapped_column(
        ForeignKey("srs_version.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_id: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sources: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    srs_version: Mapped[SRSVersion] = relationship(back_populates="requirements")


class AcceptanceCriterion(Base):
    """Acceptance criterion associated with an SRS version (DATA_MODEL §2.8)."""

    __tablename__ = "acceptance_criterion"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    srs_version_id: Mapped[str] = mapped_column(
        ForeignKey("srs_version.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criterion_id: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    related_requirement_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    srs_version: Mapped[SRSVersion] = relationship(back_populates="acceptance_criteria")


class Threat(Base):
    """A threat identified in the threat model (DATA_MODEL §2.9)."""

    __tablename__ = "threat"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    srs_version_id: Mapped[str] = mapped_column(
        ForeignKey("srs_version.id", ondelete="CASCADE"), nullable=False, index=True
    )
    threat_id: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    affected_assets: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    srs_version: Mapped[SRSVersion] = relationship(back_populates="threats")
    mitigations: Mapped[list[Mitigation]] = relationship(
        back_populates="threat", cascade="all, delete-orphan"
    )


class Mitigation(Base):
    """A mitigation strategy for a threat (DATA_MODEL §2.10)."""

    __tablename__ = "mitigation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    threat_id: Mapped[str] = mapped_column(
        ForeignKey("threat.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mitigation_id: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    related_requirement_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    threat: Mapped[Threat] = relationship(back_populates="mitigations")


class SourceDocument(Base):
    """A document ingested into the knowledge base (DATA_MODEL §2.12)."""

    __tablename__ = "source_document"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(String(10), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)

    chunks: Mapped[list[RetrievedChunk]] = relationship(
        back_populates="source_document", cascade="all, delete-orphan"
    )


class RetrievedChunk(Base):
    """A chunk of text retrieved via RAG (DATA_MODEL §2.11)."""

    __tablename__ = "retrieved_chunk"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_document_id: Mapped[str] = mapped_column(
        ForeignKey("source_document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_or_section: Mapped[str | None] = mapped_column(String(200), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)

    source_document: Mapped[SourceDocument] = relationship(back_populates="chunks")


class ModelRun(Base):
    """Provenance for one model-backed operation across artifact types."""

    __tablename__ = "model_run"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), nullable=True, index=True
    )
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_variant: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="unknown")
    rag_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    knowledge_base_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retrieved_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    retrieved_document_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    citation_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    latency_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped[Project | None] = relationship(back_populates="model_runs")
    project_contexts: Mapped[list[ProjectContext]] = relationship(back_populates="model_run")
    clarification_questions: Mapped[list[ClarificationQuestion]] = relationship(
        back_populates="model_run"
    )
    srs_versions: Mapped[list[SRSVersion]] = relationship(back_populates="model_run")
    evaluation_runs: Mapped[list[Phase5EvaluationRun]] = relationship(back_populates="model_run")


class GenerationRun(Base):
    """Metadata about one SRS-generation execution (DATA_MODEL §2.13)."""

    __tablename__ = "generation_run"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    srs_version_id: Mapped[str] = mapped_column(
        ForeignKey("srs_version.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    adapter_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_template_version: Mapped[str] = mapped_column(String(50), nullable=False)
    retrieved_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    generation_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

    srs_version: Mapped[SRSVersion] = relationship(back_populates="generation_runs")
    base_evaluations: Mapped[list[EvaluationRun]] = relationship(
        back_populates="base_generation_run",
        cascade="all, delete-orphan",
        foreign_keys="EvaluationRun.base_generation_run_id",
    )
    finetuned_evaluations: Mapped[list[EvaluationRun]] = relationship(
        back_populates="finetuned_generation_run",
        cascade="all, delete-orphan",
        foreign_keys="EvaluationRun.finetuned_generation_run_id",
    )


class EvaluationRun(Base):
    """Comparative evaluation of base and fine-tuned outputs (DATA_MODEL §2.14)."""

    __tablename__ = "evaluation_run"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    base_generation_run_id: Mapped[str] = mapped_column(
        ForeignKey("generation_run.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finetuned_generation_run_id: Mapped[str] = mapped_column(
        ForeignKey("generation_run.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    evaluator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

    base_generation_run: Mapped[GenerationRun] = relationship(
        back_populates="base_evaluations", foreign_keys=[base_generation_run_id]
    )
    finetuned_generation_run: Mapped[GenerationRun] = relationship(
        back_populates="finetuned_evaluations", foreign_keys=[finetuned_generation_run_id]
    )


class ExportedDocument(Base):
    """Records a PDF export of an SRS version (DATA_MODEL §2.15)."""

    __tablename__ = "exported_document"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    srs_version_id: Mapped[str] = mapped_column(
        ForeignKey("srs_version.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    exported_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)

    srs_version: Mapped[SRSVersion] = relationship(back_populates="exports")


class Phase5EvaluationRun(Base):
    """A Phase 5 evaluation run covering one or more configurations.

    Stores aggregate results for a single evaluation session across
    one or more configurations (base, base_rag, finetuned, finetuned_rag).
    """

    __tablename__ = "phase5_evaluation_run"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    config: Mapped[str] = mapped_column(String(32), nullable=False)  # ConfigVariant value
    model_variant: Mapped[str] = mapped_column(String(20), nullable=False)  # base | finetuned
    rag_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    adapter_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Aggregate metrics (JSON for flexibility)
    aggregate_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_run.id", ondelete="SET NULL"), nullable=True, index=True
    )

    case_results: Mapped[list[Phase5CaseResult]] = relationship(
        back_populates="evaluation_run", cascade="all, delete-orphan"
    )
    model_run: Mapped[ModelRun | None] = relationship(back_populates="evaluation_runs")


class Phase5CaseResult(Base):
    """Individual case result within a Phase 5 evaluation run.

    Stores both raw model output metrics and final post-repair metrics
    to enable comparison of raw model capability vs. repaired output.
    """

    __tablename__ = "phase5_case_result"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    evaluation_run_id: Mapped[str] = mapped_column(
        ForeignKey("phase5_evaluation_run.id", ondelete="CASCADE"), nullable=False, index=True
    )

    case_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    config: Mapped[str] = mapped_column(String(32), nullable=False)  # ConfigVariant value

    model_variant: Mapped[str] = mapped_column(String(20), nullable=False)  # base | finetuned
    rag_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    adapter_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Raw model output metrics (pre-validation/repair)
    raw_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Final output metrics (post-validation/repair)
    final_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Timing
    analysis_latency_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    clarification_latency_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    srs_latency_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_latency_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Retrieval metadata
    retrieval_chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retrieval_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kb_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Category accuracy
    inferred_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    category_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Errors
    analysis_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    clarification_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    srs_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Generation metadata
    model_variant_used: Mapped[str] = mapped_column(String(20), nullable=False)
    rag_enabled_used: Mapped[bool] = mapped_column(Boolean, nullable=False)
    model_name_used: Mapped[str] = mapped_column(String(100), nullable=False)
    adapter_name_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_timestamp: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    generation_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    evaluation_run: Mapped[Phase5EvaluationRun] = relationship(back_populates="case_results")
