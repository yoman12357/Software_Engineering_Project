# ruff: noqa: E501
"""Prompt templates for structured SRS generation (Task 2.6).

SRS generation is sectioned to avoid overwhelming the 4B model with a single
massive prompt. Each section is generated in a separate LLM call.
"""

# --- Common schema fragments ---

REQUIREMENT_SCHEMA = """Each requirement object must have exactly these fields:
- id: "FR-001", "NFR-001", "SEC-001", "DATA-001", or "NET-001" format (prefix + 3 digits)
- category: "functional" | "non_functional" | "security" | "data" | "network"
- title: Short descriptive title (non-empty string)
- statement: Testable requirement starting with "The system shall" (non-empty string)
- rationale: WHY this requirement exists — must reference at least one of:
    * explicit user requirement from project description
    * clarification answer
    * inferred project risk
    * retrieved cybersecurity guidance (cite source)
  Generic rationale "Generated from the project context by the local model" is FORBIDDEN.
- priority: "must" | "should" | "could"
- acceptance_criteria: Independently testable verification using GIVEN-WHEN-THEN format:
    "GIVEN <precondition> WHEN <action> THEN <expected_result>"
    Must specify measurable pass/fail conditions.
    FORBIDDEN: "Verify that <requirement> is implemented" or paraphrases of the requirement statement.
- dependencies: Array of requirement IDs this depends on (may be empty)
- source_references: Array of citation objects, each with:
    - source_id: chunk_id from retrieved context (required)
    - document_title: title of source document
    - section_heading: section/page if available
    - relevance_score: retrieval score
    Only include if requirement is informed by retrieved knowledge. Empty array [] if not.
- confidence: "high" | "medium" | "low"
- user_confirmed: false"""

THREAT_SCHEMA = """Each threat object must have exactly these fields:
- threat_id: "THR-001" format
- name: Short threat name (non-empty)
- description: Detailed threat description (non-empty)
- category: STRIDE category or similar (string, may be null)
- severity: "critical" | "high" | "medium" | "low"
- affected_assets: Array of asset names (may be empty)
- mitigations: Array of mitigation objects with:
    - mitigation_id: "MIT-001" format
    - description: Mitigation strategy (non-empty)
    - related_requirement_ids: Array of requirement IDs (may be empty)"""

CITATION_INSTRUCTION = """
CITATION RULES (MANDATORY):
- If a requirement is informed by retrieved knowledge, you MUST include source_references.
- Each source_reference MUST use a source_id that exactly matches a chunk_id from the retrieved context provided below.
- Do NOT invent citations. Do NOT cite sources not in the retrieved context.
- If no retrieved knowledge applies to a requirement, use empty array [] for source_references.
"""

NUMERIC_CONSTRAINT_RULES = """
NUMERIC CONSTRAINT RULES (MANDATORY):
- You MUST NOT invent numerical thresholds (e.g., response times, uptime percentages, connection counts, retention days, patch deadlines).
- Any numerical value in a requirement MUST be classified by its provenance using rationale field:
  * USER_SPECIFIED — explicitly stated in project description or clarification answers
  * RAG_SUPPORTED — from a retrieved source (cite it in source_references)
  * ASSUMPTION_REQUIRING_CONFIRMATION — not from user or RAG; flag as assumption
- If a number is not USER_SPECIFIED or RAG_SUPPORTED, do NOT make it a mandatory "must" requirement.
  Instead, either:
    a) Omit the specific number and use qualitative language (e.g., "within acceptable limits")
    b) Generate an assumption in the assumptions section documenting the assumed value
    c) Generate an unresolved question for stakeholder confirmation
- Common invented numbers to AVOID unless sourced: 5s/30s/60s response, 99.9%/99.99% uptime, 10000 connections, 50%/100% scalability, 48h/72h patch, 90/180/365 day retention, 256-bit encryption, etc.
"""

RATIONALE_RULES = """
RATIONALE RULES (MANDATORY):
- Every rationale MUST explain WHY the requirement exists.
- Each rationale MUST reference at least ONE of:
  * Explicit user requirement (quote or paraphrase from project description)
  * Clarification answer (reference the question ID)
  * Inferred project risk (describe the risk)
  * Retrieved cybersecurity guidance (cite the source in source_references)
- FORBIDDEN: "Generated from the project context by the local model" or similar generic statements.
- If no specific justification applies, the requirement should not be generated.
"""

LANGUAGE_QUALITY_RULES = """
LANGUAGE QUALITY RULES (MANDATORY):
- Every statement MUST begin with "The system shall" exactly once.
- FORBIDDEN: "The system shall all...", "shall ... shall" (duplicate modal), "The system shall The system shall".
- Use active voice. Avoid passive constructions where possible.
- Requirements must be testable and unambiguous.
"""

ACCEPTANCE_CRITERIA_RULES = """
ACCEPTANCE CRITERIA RULES (MANDATORY):
- Each acceptance_criteria MUST be independently testable using GIVEN-WHEN-THEN format:
  "GIVEN <precondition> WHEN <action> THEN <expected_result>"
- Must specify measurable pass/fail conditions (inputs, expected outputs, thresholds from user/RAG).
- FORBIDDEN patterns:
  * "Verify that <requirement> is implemented"
  * "Verify that the system <paraphrase of requirement>"
  * "Ensure <requirement> works"
  * "Test that <requirement> is met"
- Acceptance criteria must be more specific than the requirement statement.
- Each criterion must link to specific requirement ID(s) via related_requirement_ids.
"""

# --- Sectioned Generation Prompts ---

FUNCTIONAL_REQUIREMENTS_SYSTEM_PROMPT = f"""You are a requirements engineer generating the functional requirements section of an SRS for a cybersecurity system.

Generate functional requirements (what the system must DO) as structured JSON. Return ONLY a JSON object with a "functional_requirements" array.

{REQUIREMENT_SCHEMA}

{CITATION_INSTRUCTION}

{NUMERIC_CONSTRAINT_RULES}

{RATIONALE_RULES}

{LANGUAGE_QUALITY_RULES}

{ACCEPTANCE_CRITERIA_RULES}

Rules:
- Category MUST be "functional" for all requirements.
- IDs must use FR- prefix (FR-001, FR-002, ...).
- Every statement must begin with "The system shall" exactly once.
- At least 3 functional requirements.
- Return ONLY the JSON object. No Markdown fences, no explanations.
"""

FUNCTIONAL_REQUIREMENTS_USER_TEMPLATE = """Project context:
{project_context}

Previously generated sections summary:
{previous_sections_summary}

Retrieved knowledge (use for citations where applicable):
{rag_context}

Generate functional requirements for this cybersecurity system. Focus on what the system must DO (filtering, monitoring, authentication, rule management, etc.).
Apply all rules: no invented numbers, specific rationales, proper citations, testable acceptance criteria.
"""

NON_FUNCTIONAL_REQUIREMENTS_SYSTEM_PROMPT = f"""You are a requirements engineer generating the non-functional requirements section of an SRS for a cybersecurity system.

Generate non-functional requirements (quality attributes) as structured JSON. Return ONLY a JSON object with a "non_functional_requirements" array.

{REQUIREMENT_SCHEMA}

{CITATION_INSTRUCTION}

{NUMERIC_CONSTRAINT_RULES}

{RATIONALE_RULES}

{LANGUAGE_QUALITY_RULES}

{ACCEPTANCE_CRITERIA_RULES}

Rules:
- Category MUST be "non_functional" for all requirements.
- IDs must use NFR- prefix (NFR-001, NFR-002, ...).
- Every statement must begin with "The system shall" exactly once.
- At least 2 non-functional requirements covering availability, performance, scalability, etc.
- Return ONLY the JSON object. No Markdown fences, no explanations.
"""

NON_FUNCTIONAL_REQUIREMENTS_USER_TEMPLATE = """Project context:
{project_context}

Previously generated sections summary:
{previous_sections_summary}

Retrieved knowledge (use for citations where applicable):
{rag_context}

Generate non-functional requirements for this cybersecurity system. Focus on availability, performance, scalability, maintainability, usability.
Apply all rules: no invented numbers, specific rationales, proper citations, testable acceptance criteria.
"""

SECURITY_REQUIREMENTS_SYSTEM_PROMPT = f"""You are a requirements engineer generating the security requirements section of an SRS for a cybersecurity system.

Generate security requirements as structured JSON. Return ONLY a JSON object with a "security_requirements" array.

{REQUIREMENT_SCHEMA}

{CITATION_INSTRUCTION}

{NUMERIC_CONSTRAINT_RULES}

{RATIONALE_RULES}

{LANGUAGE_QUALITY_RULES}

{ACCEPTANCE_CRITERIA_RULES}

Rules:
- Category MUST be "security" for all requirements.
- IDs must use SEC- prefix (SEC-001, SEC-002, ...).
- Every statement must begin with "The system shall" exactly once.
- At least 2 security requirements covering authentication, authorisation, encryption, audit, etc.
- Return ONLY the JSON object. No Markdown fences, no explanations.
"""

SECURITY_REQUIREMENTS_USER_TEMPLATE = """Project context:
{project_context}

Previously generated sections summary:
{previous_sections_summary}

Retrieved knowledge (use for citations where applicable):
{rag_context}

Generate security requirements for this cybersecurity system. Focus on authentication, authorisation, encryption, audit logging, secure administration, data protection.
Apply all rules: no invented numbers, specific rationales, proper citations, testable acceptance criteria.
"""

DATA_REQUIREMENTS_SYSTEM_PROMPT = f"""You are a requirements engineer generating the data requirements section of an SRS for a cybersecurity system.

Generate data requirements as structured JSON. Return ONLY a JSON object with a "data_requirements" array.

{REQUIREMENT_SCHEMA}

{CITATION_INSTRUCTION}

{NUMERIC_CONSTRAINT_RULES}

{RATIONALE_RULES}

{LANGUAGE_QUALITY_RULES}

{ACCEPTANCE_CRITERIA_RULES}

Rules:
- Category MUST be "data" for all requirements.
- IDs must use DATA- prefix (DATA-001, DATA-002, ...).
- Every statement must begin with "The system shall" exactly once.
- At least 1 data requirement covering retention, integrity, classification, privacy.
- Return ONLY the JSON object. No Markdown fences, no explanations.
"""

DATA_REQUIREMENTS_USER_TEMPLATE = """Project context:
{project_context}

Previously generated sections summary:
{previous_sections_summary}

Retrieved knowledge (use for citations where applicable):
{rag_context}

Generate data requirements for this cybersecurity system. Focus on log retention, data integrity, classification, privacy, backup.
Apply all rules: no invented numbers, specific rationales, proper citations, testable acceptance criteria.
"""

NETWORK_REQUIREMENTS_SYSTEM_PROMPT = f"""You are a requirements engineer generating the network requirements section of an SRS for a cybersecurity system.

Generate network requirements as structured JSON. Return ONLY a JSON object with a "network_requirements" array.

{REQUIREMENT_SCHEMA}

{CITATION_INSTRUCTION}

{NUMERIC_CONSTRAINT_RULES}

{RATIONALE_RULES}

{LANGUAGE_QUALITY_RULES}

{ACCEPTANCE_CRITERIA_RULES}

Rules:
- Category MUST be "network" for all requirements.
- IDs must use NET- prefix (NET-001, NET-002, ...).
- Every statement must begin with "The system shall" exactly once.
- At least 1 network requirement covering segmentation, zones, protocols, bandwidth.
- Return ONLY the JSON object. No Markdown fences, no explanations.
"""

NETWORK_REQUIREMENTS_USER_TEMPLATE = """Project context:
{project_context}

Previously generated sections summary:
{previous_sections_summary}

Retrieved knowledge (use for citations where applicable):
{rag_context}

Generate network requirements for this cybersecurity system. Focus on segmentation, zones, protocols, bandwidth, latency, redundancy.
Apply all rules: no invented numbers, specific rationales, proper citations, testable acceptance criteria.
"""

ARCHITECTURE_SYSTEM_PROMPT = """You are a requirements engineer generating the system architecture section of an SRS for a cybersecurity system.

Generate the architecture summary as structured JSON. Return ONLY a JSON object with exactly these fields:
- overview: High-level architecture description (non-empty string)
- components: Array of component objects, each with:
    - name: Component name (non-empty)
    - description: Component description (non-empty)
    - responsibilities: Array of responsibility strings (non-empty, at least 1)
- data_flows: Array of data-flow description strings (may be empty)
- deployment_notes: Deployment considerations (string, may be empty)

Rules:
- At least 2 components.
- Each component must have at least 1 responsibility.
- Return ONLY the JSON object. No Markdown fences.
"""

ARCHITECTURE_USER_TEMPLATE = """Project context:
{project_context}

Previously generated sections summary:
{previous_sections_summary}

Retrieved knowledge (use for citations where applicable):
{rag_context}

Generate the system architecture for this cybersecurity system. Include perimeter components, monitoring components, management plane, and their responsibilities.
"""

THREATS_SYSTEM_PROMPT = f"""You are a security engineer generating the threat model section of an SRS for a cybersecurity system.

Generate threats and mitigations as structured JSON. Return ONLY a JSON object with exactly these fields:
- threats: Array of threat objects
- mitigations: Array of mitigation objects (flattened from all threats)

{THREAT_SCHEMA}

Rules:
- At least 2 threats.
- Each threat must have at least 1 mitigation.
- Severity must be one of: critical, high, medium, low.
- Mitigation related_requirement_ids should reference requirement IDs from previously generated sections (FR-*, NFR-*, SEC-*, DATA-*, NET-*).
- Return ONLY the JSON object. No Markdown fences.
"""

THREATS_USER_TEMPLATE = """Project context:
{project_context}

Previously generated requirements summary:
{requirements_summary}

Retrieved knowledge (use for citations where applicable):
{rag_context}

Generate a threat model for this cybersecurity system. Include threats relevant to the inferred categories and architecture. Each threat must have at least one mitigation linked to requirements.
"""

ACCEPTANCE_TESTING_SYSTEM_PROMPT = """You are a requirements engineer generating acceptance criteria and testing recommendations for an SRS.

Generate as structured JSON. Return ONLY a JSON object with exactly these fields:
- acceptance_criteria: Array of criterion objects, each with:
    - criterion_id: "AC-001" format
    - description: GIVEN <precondition> WHEN <action> THEN <expected_result> (non-empty)
    - related_requirement_ids: Array of requirement IDs this criterion verifies (may be empty)
- testing_strategy: Array of recommendation objects, each with:
    - recommendation_id: "TEST-001" format
    - description: Testing recommendation (non-empty)
    - type: "unit" | "integration" | "system" | "security" | "performance"
    - related_requirement_ids: Array of requirement IDs (may be empty)

Rules:
- At least 3 acceptance criteria covering key requirements.
- Each acceptance criterion MUST use GIVEN-WHEN-THEN format with measurable conditions.
- At least 2 testing recommendations of different types.
- Return ONLY the JSON object. No Markdown fences.
"""

ACCEPTANCE_TESTING_USER_TEMPLATE = """Project context:
{project_context}

All generated requirements:
{all_requirements}

Retrieved knowledge:
{rag_context}

Generate acceptance criteria and testing recommendations for this cybersecurity system.
Each acceptance criterion MUST use GIVEN-WHEN-THEN format and link to specific requirement IDs.
"""

RISKS_ASSUMPTIONS_SYSTEM_PROMPT = """You are a requirements engineer generating the risks, assumptions, and unresolved questions section of an SRS.

Generate as structured JSON. Return ONLY a JSON object with exactly these fields:
- assumptions: Array of assumption strings (non-empty, at least 2)
- risks: Array of risk objects, each with:
    - risk_id: "RISK-001" format
    - description: Risk description (non-empty)
    - likelihood: "high" | "medium" | "low"
    - impact: "high" | "medium" | "low"
    - mitigation: Mitigation strategy (string, may be empty)
- unresolved_questions: Array of question strings (may be empty)
- references: Array of citation objects (source_id, document_title, section_heading) for any cited sources, or empty array []

Rules:
- At least 2 assumptions. Document any assumed numeric values here.
- At least 1 risk.
- Any numeric assumptions from requirements MUST be documented here.
- Unresolved questions should capture clarification needs not yet answered.
- Return ONLY the JSON object. No Markdown fences.
"""

RISKS_ASSUMPTIONS_USER_TEMPLATE = """Project context:
{project_context}

All generated requirements and threats:
{all_content_summary}

Retrieved knowledge:
{rag_context}

Generate assumptions, risks, and unresolved questions for this cybersecurity system.
Document all numeric assumptions from requirements here. List unresolved questions from clarification gaps.
"""

# --- Legacy single-call SRS prompt (for compatibility) ---

SRS_SYSTEM_PROMPT = f"""You are a requirements engineer generating a complete Software Requirements Specification (SRS) as structured JSON for a cybersecurity system.

The user provides ONLY a project description — they do NOT manually select a domain. You must infer the cybersecurity subdomain automatically.

Generate the complete SRS matching the SRSSchema exactly. Return ONLY the JSON object. No Markdown fences, no explanations.

Key rules:
- All requirement IDs must follow the pattern (FR|NFR|SEC|DATA|NET)-NNN
- Every requirement statement must begin with "The system shall" exactly once
- Generate 1-3 functional requirements and at most 3 requirements in each other category
- Prefer a compact, complete SRS over exhaustive or repetitive requirements
- Include only requirements directly grounded in the project context or retrieved knowledge
- source_references and references must cite actual retrieved chunks
- inferred_categories must be valid CAT-01..CAT-08 values
- The user does NOT choose categories — you infer them

{REQUIREMENT_SCHEMA}

{CITATION_INSTRUCTION}

{NUMERIC_CONSTRAINT_RULES}

{RATIONALE_RULES}

{LANGUAGE_QUALITY_RULES}

{ACCEPTANCE_CRITERIA_RULES}
"""

SRS_USER_TEMPLATE = """Project context:
{project_context}

Retrieved knowledge:
{rag_context}

Generate the complete SRS for this cybersecurity project. Include all sections: metadata, project_overview, scope, assumptions, stakeholders, user_roles, functional_requirements, non_functional_requirements, security_requirements, data_requirements, network_requirements, architecture_summary, threats, mitigations, testing_strategy, risks, unresolved_questions, references, validation_report (null).
Apply all rules: no invented numbers, specific rationales, proper citations, testable acceptance criteria.
"""
