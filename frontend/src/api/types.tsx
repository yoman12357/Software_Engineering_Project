// TypeScript types aligned with the backend API contracts (docs/API_CONTRACT.md
// and the backend Pydantic schemas).

export interface ProjectRead {
  id: string;
  name: string;
  description: string;
  status: string;
  inferred_categories: string[];
  created_at: string;
  updated_at: string;
}

export interface ProjectCreatePayload {
  name: string;
  description: string;
}

export interface ProjectDocumentRead {
  id: string;
  project_id: string;
  original_filename: string;
  media_type: string;
  file_extension: string;
  file_size_bytes: number;
  sha256: string;
  status: string;
  chunk_count: number;
  created_at: string;
}

export interface ProjectAnalysis {
  stakeholders: string[];
  assets: string[];
  users: string[];
  constraints: string[];
  goals: string[];
  inferred_categories: string[];
  missing_information: string[];
  project_summary: string;
}

export interface AnalysisResponse {
  project_id: string;
  analysis: ProjectAnalysis;
  has_missing_information: boolean;
  provider: string;
  model_name: string;
  generated_at: string;
}

export interface ProjectContextRead {
  id: string;
  project_id: string;
  stakeholders: string[];
  assets: string[];
  users: string[];
  constraints: string[];
  goals: string[];
  inferred_categories: string[];
  missing_information: string[] | null;
  enriched_context: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export type AnswerType = "text" | "number" | "list" | "boolean";

export interface ClarificationAnswerRead {
  id: string;
  question_id: string;
  answer_text: string;
  skipped: boolean;
  created_at: string;
}

export interface ClarificationQuestionRead {
  id: string;
  project_id: string;
  question_text: string;
  reason: string;
  is_critical: boolean;
  display_order: number;
  expected_answer_type: AnswerType;
  target_gap: string;
  created_at: string;
  answer: ClarificationAnswerRead | null;
}

export interface ClarificationQuestionListResponse {
  project_id: string;
  questions: ClarificationQuestionRead[];
}

export interface ClarificationAnswerItem {
  question_id: string;
  answer_text: string;
  skipped: boolean;
}

export interface ClarificationAnswerSubmissionResponse {
  project_id: string;
  answers_saved: number;
  context_updated: boolean;
}

export type RequirementCategory =
  | "functional"
  | "non_functional"
  | "security"
  | "data"
  | "network";

export type Priority = "must" | "should" | "could";
export type Confidence = "high" | "medium" | "low";

export interface SourceReference {
  source_id: string;
  document_title: string;
  section_heading: string | null;
  relevance_score: number;
  excerpt?: string;
}

export interface Requirement {
  id: string;
  category: RequirementCategory;
  title: string;
  statement: string;
  rationale: string;
  priority: Priority;
  acceptance_criteria: string;
  dependencies: string[];
  source_references: SourceReference[];
  confidence: Confidence;
  user_confirmed: boolean;
}

export interface Threat {
  threat_id: string;
  name: string;
  description: string;
  category: string | null;
  severity: "critical" | "high" | "medium" | "low";
  affected_assets: string[];
  mitigations: Array<{
    mitigation_id: string;
    description: string;
    related_requirement_ids: string[];
  }>;
}

export interface SRSSchema {
  metadata: {
    project_name: string;
    version: number;
    generated_at: string;
    model_name: string;
    adapter_name: string | null;
    inferred_categories: string[];
  };
  project_overview: {
    description: string;
    purpose: string;
    context: string;
  };
  scope: {
    in_scope: string[];
    out_of_scope: string[];
  };
  assumptions: string[];
  stakeholders: string[];
  user_roles: string[];
  functional_requirements: Requirement[];
  non_functional_requirements: Requirement[];
  security_requirements: Requirement[];
  data_requirements: Requirement[];
  network_requirements: Requirement[];
  architecture_summary: {
    overview: string;
    components: Array<{
      name: string;
      description: string;
      responsibilities: string[];
    }>;
    data_flows: string[];
    deployment_notes: string;
  };
  threats: Threat[];
  mitigations: Array<{
    mitigation_id: string;
    description: string;
    related_requirement_ids: string[];
  }>;
  testing_strategy: Array<{
    recommendation_id: string;
    description: string;
    type: string;
    related_requirement_ids: string[];
  }>;
  risks: Array<{
    risk_id: string;
    description: string;
    likelihood: string;
    impact: string;
    mitigation: string;
  }>;
  unresolved_questions: string[];
  references: unknown[];
  validation_report: {
    overall_score: number;
    issues: Array<{
      issue_id: string;
      severity: "error" | "warning" | "info";
      section: string;
      requirement_id: string | null;
      message: string;
    }>;
  } | null;
  generation_metadata: {
    provider: string;
    model_name: string;
    generation_time_ms: number;
    rag_enabled: boolean;
    retrieval_context: string[] | null;
    retrieved_chunks: number;
    retrieval_time_ms: number;
    kb_version: string | null;
    validation_issues: Array<{
      code: string;
      severity: string;
      section: string;
      requirement_id: string | null;
      message: string;
    }>;
  };
}

export interface SRSGenerationResponse {
  project_id: string;
  version_id: string;
  version_number: number;
  status: string;
}

export interface SRSVersionRead {
  id: string;
  project_id: string;
  version_number: number;
  status: string;
  quality_score: number | null;
  created_at: string;
  srs: SRSSchema | null;
}

export interface SourceChunk {
  chunk_id: string;
  text: string;
  metadata: {
    source_id: string;
    document_title: string;
    organisation: string;
    version: string;
    publication_date: string;
    retrieval_date: string;
    source_url: string;
    section_heading: string;
    section_level: number;
    page_number: number;
    chunk_index: number;
    file_hash_sha256: string;
    categories: string;
    licence_note: string;
  };
}

export interface SRSSourcesResponse {
  sources: SourceChunk[];
}

export interface SRSVersionSummary {
  id: string;
  version_number: number;
  quality_score: number | null;
  status: string;
  created_at: string;
}

export interface SRSVersionListResponse {
  project_id: string;
  versions: SRSVersionSummary[];
}

export interface SRSGenerationProgressEvent {
  phase: "preparing" | "retrieving" | "generating" | "validating" | "completed" | "failed";
  progress: number;
  message: string;
  result: SRSGenerationResponse | null;
  error_code?: string | null;
}

export interface ModelRunProvenance {
  id: string;
  operation_type: string;
  model_variant: string;
  model_name: string;
  rag_enabled: boolean;
  embedding_model: string | null;
  knowledge_base_version: string | null;
  retrieved_chunk_ids: string[];
  retrieved_document_ids: string[];
  citation_ids: string[];
  started_at: string;
  completed_at: string | null;
  latency_seconds: number | null;
  status: string;
  error_message: string | null;
  deterministic_validation_applied: boolean | null;
  deterministic_repair_applied: boolean | null;
}

export interface ArtifactProvenanceResponse {
  artifact_type: string;
  artifact_id: string;
  provenance_status: "recorded" | "legacy_unknown";
  model_run: ModelRunProvenance | null;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  database_ok: boolean;
}

export interface ModelInfoResponse {
  active_model_variant: string;
  active_model_name: string;
  provider: string;
  rag_enabled: boolean;
  embedding_model: string | null;
  knowledge_base_version: string;
}

export interface SRSEditSection {
  section: string;
  requirement_id: string;
  field: string;
  new_value: string;
}

export interface SRSEditRequest {
  updates: SRSEditSection[];
}

export interface ValidationIssue {
  issue_id: string;
  severity: "error" | "warning" | "info";
  section: string;
  requirement_id: string | null;
  message: string;
}

export interface SRSValidationResponse {
  srs_version_id: string;
  overall_score: number;
  issues: ValidationIssue[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  type?: "text" | "analysis" | "clarification" | "generation" | "srs" | "error";
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export type SRSRegeneratableSection =
  | "functional_requirements"
  | "non_functional_requirements"
  | "security_requirements"
  | "data_requirements"
  | "network_requirements"
  | "architecture_summary"
  | "threats"
  | "testing_strategy";

export interface ChatSessionSnapshot {
  id: string;
  project_id: string | null;
  name: string;
  messages: ChatMessage[];
  stage: "welcome" | "analyzing" | "clarifying" | "generating" | "ready" | "error";
  analysis: Record<string, unknown> | null;
  clarification_questions: unknown[] | null;
  srs: unknown | null;
  srs_version_id: string | null;
  pending_project_description: string | null;
  pinned_at: string | null;
  created_at: string;
  updated_at: string;
}

export type ChatSessionWrite = Omit<
  ChatSessionSnapshot,
  "id" | "pinned_at" | "created_at" | "updated_at"
>;

export interface ChatSessionListResponse {
  sessions: ChatSessionSnapshot[];
  total: number;
}

export interface ChatCitation {
  source_id: string;
  source_document_id: string;
  document_title: string;
  chunk_index: number;
  page_or_section: string | null;
  relevance_score: number;
}

export interface ChatCompletionResponse {
  content: string;
  is_project_description: boolean;
  model_name: string;
  rag_enabled: boolean;
  citations: ChatCitation[];
  warnings: string[];
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor(status: number, envelope: ApiErrorEnvelope) {
    super(envelope.error.message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = envelope.error.code;
    this.details = envelope.error.details;
  }
}
