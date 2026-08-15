import type {
  ArtifactProvenanceResponse,
  AnalysisResponse,
  ClarificationQuestionListResponse,
  ProjectRead,
  SRSSchema,
  SRSGenerationResponse,
  SRSVersionRead,
} from "../api/types";

export const SAMPLE_PROJECT: ProjectRead = {
  id: "project-123",
  name: "Campus Firewall",
  description:
    "I want to build a firewall and monitoring system for my college network.",
  status: "clarifying",
  inferred_categories: ["CAT-02", "CAT-03"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

export const SAMPLE_ANALYSIS_RESPONSE: AnalysisResponse = {
  project_id: "project-123",
  analysis: {
    stakeholders: ["Campus IT department", "Students", "Faculty"],
    assets: ["Campus network", "Firewall hardware", "Monitoring server"],
    users: ["Network administrators", "Security analysts"],
    constraints: ["Budget limitations"],
    goals: ["Monitor network traffic", "Block malicious connections"],
    inferred_categories: ["CAT-02", "CAT-03"],
    missing_information: ["Number of network nodes", "Compliance requirements"],
    project_summary: "A firewall and network-monitoring system for a college campus.",
  },
  has_missing_information: true,
  provider: "mock",
  model_name: "cybersrs-mock-1b",
  generated_at: "2026-01-01T00:00:00Z",
};

export const SAMPLE_CLARIFICATIONS: ClarificationQuestionListResponse = {
  project_id: "project-123",
  questions: [
    {
      id: "q-001",
      project_id: "project-123",
      question_text: "How many network nodes will the firewall protect?",
      reason: "Scale affects architecture and performance requirements.",
      is_critical: true,
      display_order: 0,
      expected_answer_type: "number",
      target_gap: "Expected number of network nodes",
      created_at: "2026-01-01T00:00:00Z",
      answer: null,
    },
    {
      id: "q-002",
      project_id: "project-123",
      question_text: "Are there specific compliance standards to meet?",
      reason: "Compliance requirements drive security requirements.",
      is_critical: false,
      display_order: 1,
      expected_answer_type: "boolean",
      target_gap: "Compliance requirements",
      created_at: "2026-01-01T00:00:00Z",
      answer: null,
    },
  ],
};

export const SAMPLE_SRS_GENERATION: SRSGenerationResponse = {
  project_id: "project-123",
  version_id: "version-1",
  version_number: 1,
  status: "generated",
};

export const SAMPLE_SRS: SRSSchema = {
  metadata: {
    project_name: "Campus Firewall",
    version: 1,
    generated_at: "2026-01-01T00:00:00Z",
    model_name: "cybersrs-mock-1b",
    adapter_name: null,
    inferred_categories: ["CAT-02", "CAT-03"],
  },
  project_overview: {
    description: "A firewall for the campus.",
    purpose: "Filter traffic and monitor threats.",
    context: "College campus.",
  },
  scope: {
    in_scope: ["Firewall", "Monitoring"],
    out_of_scope: [],
  },
  assumptions: ["Existing infrastructure in place."],
  stakeholders: ["Campus IT department"],
  user_roles: ["Network administrators"],
  functional_requirements: [
    {
      id: "FR-001",
      category: "functional",
      title: "Traffic Filtering",
      statement: "The system shall filter inbound and outbound traffic by default.",
      rationale: "Core access control.",
      priority: "must",
      acceptance_criteria: "Verify denied traffic is blocked.",
      dependencies: [],
      source_references: [],
      confidence: "high",
      user_confirmed: false,
    },
  ],
  non_functional_requirements: [
    {
      id: "NFR-001",
      category: "non_functional",
      title: "Availability",
      statement: "The system shall be available with minimal downtime.",
      rationale: "Operational continuity.",
      priority: "must",
      acceptance_criteria: "Verify 99.9% uptime measured over a month.",
      dependencies: [],
      source_references: [],
      confidence: "high",
      user_confirmed: false,
    },
  ],
  security_requirements: [],
  data_requirements: [],
  network_requirements: [],
  architecture_summary: {
    overview: "Layered security architecture.",
    components: [
      {
        name: "Firewall",
        description: "Edge filtering.",
        responsibilities: ["Filter traffic"],
      },
    ],
    data_flows: [],
    deployment_notes: "",
  },
  threats: [],
  mitigations: [],
  testing_strategy: [],
  risks: [],
  unresolved_questions: [],
  references: [],
  validation_report: null,
  generation_metadata: {
    provider: "mock",
    model_name: "cybersrs-mock-1b",
    generation_time_ms: 1000,
    rag_enabled: true,
    retrieval_context: ["context1", "context2"],
    retrieved_chunks: 5,
    retrieval_time_ms: 100,
    kb_version: "v1.0",
    validation_issues: [],
  },
};

export const SAMPLE_SRS_VERSION: SRSVersionRead = {
  id: "version-1",
  project_id: "project-123",
  version_number: 1,
  status: "generated",
  quality_score: null,
  created_at: "2026-01-01T00:00:00Z",
  srs: SAMPLE_SRS,
};

export const SAMPLE_SRS_PROVENANCE: ArtifactProvenanceResponse = {
  artifact_type: "srs",
  artifact_id: "version-1",
  provenance_status: "recorded",
  model_run: {
    id: "run-1",
    operation_type: "srs_generation",
    model_variant: "base",
    model_name: "qwen3:4b-instruct-2507-q4_K_M",
    rag_enabled: true,
    embedding_model: "nomic-embed-text",
    knowledge_base_version: "kb-test-v1",
    retrieved_chunk_ids: ["chunk-1", "chunk-2"],
    retrieved_document_ids: ["source-1"],
    citation_ids: ["chunk-1"],
    started_at: "2026-01-01T00:00:00Z",
    completed_at: "2026-01-01T00:00:02Z",
    latency_seconds: 2,
    status: "succeeded",
    error_message: null,
    deterministic_validation_applied: true,
    deterministic_repair_applied: true,
  },
};
