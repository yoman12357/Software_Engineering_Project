# Future SDLC and Development Planner

> **FUTURE WORK - NOT YET IMPLEMENTED**
>
> This document is an implementation-ready plan for work that begins only after
> the current QLoRA fine-tuning and comparative evaluation phases are complete.
> It does not change the current training dataset, evaluation baseline, RAG
> pipeline, or model configuration.

**Status:** Proposed future extension

**Planning date:** 2026-08-13

**Prerequisite:** CyberSRS SRS generation, approval, fine-tuning, and evaluation
work is complete and stable

---

## 1. Purpose and Boundary

CyberSRS currently answers: **What must be built?**

The future SDLC and Development Planner will answer: **How should the approved
requirements be implemented and verified?**

It will accept an approved SRS, derive a provenance-backed development profile,
recommend an explainable lifecycle or hybrid methodology, map every requirement
to implementation and verification work, and produce a second document titled
**Software Development Plan**.

This extension is a planning and review system. It will not:

- generate or deploy production source code;
- autonomously change infrastructure, networks, or security controls;
- execute penetration tests, exploits, or attack payloads;
- silently invent team size, schedule, budget, technology, or regulatory facts;
- replace project managers, architects, developers, testers, or approvers;
- modify an approved SRS while producing its development plan;
- require a second model or fine-tuning experiment before evidence justifies one.

The human remains responsible for methodology acceptance, plan correction,
approval, execution, and verification signoff.

## 2. Entry Gate and Future Workflow

The planner may start only when an immutable SRS version has passed validation
and has an explicit approval record. Editing the SRS after that point invalidates
or supersedes its linked development plan.

```text
Project Description
  -> Analysis and Clarifications
  -> Cybersecurity RAG
  -> Structured SRS
  -> Validation
  -> Human SRS Approval
  -> Project Development Profile
  -> Deterministic SDLC Suitability Engine
  -> Constrained Qwen Recommendation Explanation
  -> Human Methodology Selection
  -> Requirement Implementation Mapping
  -> Dependency and Development-Order Analysis
  -> Testing and Verification Mapping
  -> Milestone / Iteration / Sprint Planning
  -> Structured Software Development Plan
  -> Human Review and Approval
  -> PDF Export
```

The approval gate separates requirement authority from planning advice. A
development plan always references one exact SRS version and must never quietly
follow a later draft.

## 3. Proposed Architecture

The feature remains within the existing FastAPI modular monolith and continues
the structured-JSON-first architecture.

```text
Approved SRS Snapshot
        |
        v
Development Profile Extractor ----> Provenance / Assumption Validator
        |                                      |
        v                                      v
Versioned SDLC Catalogue ------> Deterministic Suitability Engine
                                           |
                                           v
                                  Ranked Candidate Set
                                           |
                                           v
                              Qwen Recommendation Reasoner
                                           |
                                           v
                              Methodology Review / Approval
                                           |
          +----------------+---------------+----------------+
          |                |                                |
          v                v                                v
 Requirement Mapper   Dependency Analyzer          Verification Mapper
          |                |                                |
          +----------------+---------------+----------------+
                                           |
                                           v
                         Traceability and Coverage Validator
                                           |
                                           v
                         Development Plan Assembly Service
                                           |
                              Structured JSON -> UI / PDF
```

### 3.1 Component Responsibilities

| Component | Responsibility | Logic type |
|---|---|---|
| Approved SRS loader | Load and hash the exact approved SRS version | Deterministic |
| Development Profile Extractor | Extract project characteristics and evidence | LLM-assisted, schema constrained |
| Provenance Validator | Reject unsupported profile values and surface unknowns | Deterministic |
| SDLC Catalogue | Store controlled, versioned methodology metadata | Curated structured data |
| Suitability Engine | Apply exclusions, rules, weights, and hybrid compatibility | Deterministic |
| Recommendation Reasoner | Explain top candidates without changing their evidence | LLM-assisted, schema constrained |
| Methodology Approval Service | Record recommendation acceptance or user override | Deterministic |
| Requirement Mapper | Draft one implementation plan per SRS requirement | LLM-assisted, schema constrained |
| Dependency Analyzer | Validate explicit dependencies and propose evidenced edges | Hybrid |
| Verification Mapper | Reuse acceptance criteria and select appropriate test levels | Hybrid |
| Traceability Validator | Enforce coverage, valid references, and graph consistency | Deterministic |
| Development Plan Assembler | Build the canonical Software Development Plan JSON | Deterministic |
| Development Plan Renderer | Render the approved plan to PDF | Deterministic |

### 3.2 Canonical State and Versioning

The canonical artefact is validated development-plan JSON, never raw model text.
Each version records:

- project ID and approved SRS version ID;
- approved SRS content hash;
- SDLC catalogue version;
- rule-set version and scoring configuration version;
- prompt-template and model/adapter versions;
- SDLC/RAG source references used;
- recommendation and user selection history;
- plan status: `draft`, `methodology_approved`, `plan_approved`, or `superseded`;
- generation and approval timestamps in UTC.

Any change to the SRS, catalogue, material project-profile fact, or selected
methodology creates a new plan version. Previously approved plans remain
readable and auditable.

## 4. Controlled SDLC Knowledge Catalogue

The first catalogue should be deliberately bounded. It includes common,
academically defensible lifecycles and delivery overlays, without claiming that
all methodology names are mutually exclusive.

| Catalogue entry | Kind | Primary use |
|---|---|---|
| Waterfall | Lifecycle | Stable, sequential, documentation-heavy work |
| V-Model | Lifecycle | Formal requirement-to-verification traceability |
| Iterative | Lifecycle | Repeated refinement under moderate uncertainty |
| Incremental | Lifecycle | Delivery in coherent capability slices |
| Spiral | Risk-driven lifecycle | High-risk or technically uncertain work |
| Prototyping | Discovery approach | User or technical uncertainty requiring validation |
| RAD | Delivery approach | Time-constrained, modular, UI/data-oriented work |
| Agile | Principles/family | Adaptive planning and frequent feedback |
| Scrum | Agile framework | Time-boxed work with an available product owner |
| Kanban | Flow framework | Continuous intake and work-in-progress control |
| DevOps | Delivery overlay | Build, release, operations, and feedback automation |
| DevSecOps | Security delivery overlay | Continuous security controls throughout delivery |
| Hybrid | Composition | Compatible lifecycle/framework/overlay combination |

Agile is not scored as though it were identical to Scrum. DevOps and DevSecOps
are overlays, not complete substitutes for a project lifecycle. Hybrid entries
must name the responsibility contributed by each component.

### 4.1 Catalogue Record

```json
{
  "methodology_id": "v-model",
  "catalogue_version": "1.0.0",
  "name": "V-Model",
  "kind": "lifecycle",
  "summary": "A lifecycle pairing specification stages with verification stages.",
  "suitability": {
    "requirement_stability": ["medium", "high"],
    "customer_involvement": ["low", "medium"],
    "risk_level": ["medium", "high"],
    "project_size": ["medium", "large"],
    "complexity": ["medium", "high"],
    "regulatory_suitability": "high",
    "safety_security_critical_suitability": "high",
    "change_frequency": ["low", "medium"],
    "documentation_need": ["high"],
    "release_frequency": ["low", "medium"]
  },
  "testing_strategy": [
    "Pair each specification level with a verification level",
    "Maintain bidirectional requirement-to-test traceability"
  ],
  "advantages": ["Strong traceability", "Early verification planning"],
  "disadvantages": ["Costly change after baselines", "Limited rapid discovery"],
  "do_not_select_when": [
    "Requirements are highly volatile and cannot be baselined",
    "Stakeholders need rapid product discovery before specification"
  ],
  "compatible_overlays": ["devops", "devsecops"],
  "incompatible_combinations": [],
  "source_references": []
}
```

Every entry must provide:

- stable ID, display name, kind, version, and concise definition;
- suitable project characteristics and explicit anti-selection conditions;
- requirement stability, stakeholder availability, risk, size, and complexity;
- regulatory, safety-critical, and security-critical suitability;
- expected change, documentation, testing, and release patterns;
- advantages, disadvantages, and operational tradeoffs;
- compatible lifecycle, framework, and delivery overlays;
- authoritative catalogue source references.

Catalogue changes require review and a version bump. Project-specific facts do
not belong in the catalogue.

### 4.2 Initial Hybrid Policies

The engine may propose only allow-listed, responsibility-separated hybrids:

| Hybrid | Responsibility split | Typical evidence |
|---|---|---|
| Agile + DevSecOps | Adaptive delivery + continuous security assurance | Volatile scope, frequent delivery, high security need |
| Scrum + DevSecOps | Sprint governance + continuous security controls | Available product owner, stable team, incremental releases |
| V-Model + DevSecOps | Formal traceability + automated security assurance | Regulated/security-critical work with controlled releases |
| Incremental + DevSecOps | Capability slices + secure build/release controls | Modular system with staged deployment |
| Spiral + Agile | Risk reduction + short feedback cycles | High uncertainty and accessible stakeholders |

A hybrid receives no bonus merely for containing more approaches. The engine
must identify a distinct responsibility and supporting profile evidence for
each component. Contradictory combinations are rejected by compatibility rules.

## 5. Project Development Profile

`ProjectDevelopmentProfile` is derived primarily from the approved SRS and its
confirmed project context. Unknown values remain unknown and become review
questions; they are not filled with typical defaults.

### 5.1 Evidence-Bearing Value

Every profile field uses the same evidence wrapper:

```json
{
  "value": "high",
  "provenance": "SRS_DERIVED",
  "evidence_references": ["SEC-004", "THR-002"],
  "explanation": "Multiple high-impact security controls and threats require intensive verification.",
  "confidence": "medium",
  "requires_confirmation": false
}
```

Allowed provenance values are:

- `USER_SPECIFIED`: explicitly present in the user description;
- `CLARIFICATION_CONFIRMED`: explicitly answered by the user;
- `SRS_DERIVED`: logically supported by named approved SRS elements;
- `ASSUMPTION_REQUIRING_CONFIRMATION`: a proposed planning value that cannot
  affect selection as an established fact until confirmed.

The validator requires evidence references for `SRS_DERIVED`. Assumptions are
excluded from positive suitability scoring by default. They may produce a
condition such as, "If stakeholder availability is low, Scrum should be
reconsidered."

### 5.2 Profile Fields

| Field | Suggested type | Typical evidence |
|---|---|---|
| requirement_stability | `low/medium/high/unknown` | unresolved questions, change statements, approval maturity |
| requirement_completeness | `low/medium/high/unknown` | SRS validation and unresolved gaps |
| expected_change_frequency | `low/medium/high/unknown` | user statement or confirmed delivery context |
| system_complexity | `low/medium/high/unknown` | components, integrations, requirements, dependencies |
| technical_uncertainty | `low/medium/high/unknown` | prototypes, novel integrations, unresolved architecture |
| security_criticality | `low/medium/high/unknown` | security requirements, threats, protected assets |
| safety_criticality | `low/medium/high/unknown` | explicit safety impact only |
| regulatory_constraints | structured list or `unknown` | explicit SRS constraints and sources |
| documentation_burden | `low/medium/high/unknown` | regulatory and approval obligations |
| stakeholder_availability | `low/medium/high/unknown` | user or clarification answer only |
| team_size | integer/range or `unknown` | user or clarification answer only |
| project_duration | duration/range or `unknown` | user or clarification answer only |
| deployment_frequency | enum or `unknown` | confirmed release expectation |
| integration_complexity | `low/medium/high/unknown` | interfaces and architecture components |
| hardware_dependencies | list | approved architecture and network requirements |
| testing_intensity | `low/medium/high/unknown` | acceptance, security, performance, safety needs |
| prototype_need | `none/optional/required/unknown` | explicit uncertainty or user request |
| overall_risk | `low/medium/high/unknown` | approved risk and threat records |
| availability_criticality | `low/medium/high/unknown` | supported availability requirements |
| maintenance_expectation | enum or `unknown` | user/SRS lifecycle statements |

The profile also records `open_questions`, `conflicts`, and a profile-level
completeness score. That score describes evidence coverage, not project quality.

### 5.3 Extraction and Validation

1. Deterministically collect SRS requirements, risks, threats, architecture,
   assumptions, unresolved questions, and validation results.
2. Ask Qwen to emit only the profile schema with evidence references.
3. Validate references against the approved SRS and project context.
4. Recompute fields that have deterministic definitions where possible.
5. Downgrade unsupported values to `ASSUMPTION_REQUIRING_CONFIRMATION` or
   `unknown`.
6. Present material unknowns to the user before final methodology selection.

Conflicting evidence is preserved as a conflict; the model may not resolve it
silently.

## 6. Explainable SDLC Selection

The selection engine is hybrid in implementation, not merely in output:

```text
Validated ProjectDevelopmentProfile
  -> hard eligibility and anti-selection rules
  -> deterministic weighted suitability scores
  -> allow-listed hybrid composition
  -> top candidates with rule evidence
  -> constrained Qwen explanation
  -> deterministic explanation/provenance validation
  -> human acceptance or override
```

### 6.1 Deterministic Scoring

Each catalogue method defines dimension rules. A rule contains:

- profile field and accepted values;
- weight and direction;
- rule rationale;
- whether it is a hard exclusion;
- evidence requirements;
- conditions that reverse or weaken the rule.

Illustrative scoring, to be calibrated during Phase C:

```text
raw_score = sum(applicable weighted matches) - sum(applicable penalties)
available_weight = sum(weights for fields supported by confirmed evidence)
selection_score = 100 * raw_score / available_weight
```

Unknown and unconfirmed values do not count as matches. The output includes
score coverage so a high score based on sparse evidence cannot look certain.
Hard exclusions are visible and cite their triggering profile evidence.

Recommended controls:

- normalize scores to `0..100` only after eligibility checks;
- retain every triggered rule in a score breakdown;
- return at least two candidates when more than one is eligible;
- detect near ties and label them instead of creating false precision;
- run sensitivity analysis on unknown or assumption-backed dimensions;
- never let Qwen add a candidate outside the deterministic candidate set;
- permit a human override but require an optional/required rationale according
  to governance policy.

### 6.2 Recommendation Schema

```json
{
  "recommended_methodology": {
    "components": ["v-model", "devsecops"],
    "selection_score": 86.0,
    "score_coverage": 0.91,
    "component_responsibilities": {
      "v-model": "Requirement-to-verification traceability",
      "devsecops": "Continuous security checks and controlled delivery"
    }
  },
  "alternative_methodologies": [
    {
      "components": ["scrum", "devsecops"],
      "selection_score": 72.0,
      "reason_not_primary": "Current requirements are stable and formal traceability has greater weight."
    }
  ],
  "selection_reasons": [],
  "tradeoffs": [],
  "risks": [],
  "assumptions": [],
  "conditions_that_would_change_the_choice": [],
  "rule_evidence": [],
  "catalogue_version": "1.0.0",
  "rule_set_version": "1.0.0"
}
```

Qwen explains the ranked evidence in readable language. It does not calculate
the authoritative score or erase tradeoffs, assumptions, exclusions, or near
ties.

## 7. Requirement-to-Implementation Mapping

Every functional, non-functional, security, data, and network requirement in
the approved SRS receives exactly one top-level
`RequirementImplementationPlan`. A plan may contain multiple tasks and tests.
No implementation record may point to an unknown requirement.

### 7.1 Conceptual Schema

```text
RequirementImplementationPlan
  plan_item_id
  requirement_id
  requirement_statement
  requirement_type
  priority
  implementation_summary
  components[]
  work_breakdown
    backend_work[]
    frontend_work[]
    database_work[]
    infrastructure_work[]
    security_work[]
  development_tasks[]
    task_id
    title
    description
    lifecycle_activity
    completion_evidence
  dependencies[]
  prerequisite_requirements[]
  implementation_phase
  estimated_complexity
  responsible_role
  testing_strategy[]
  acceptance_criteria_references[]
  verification_methods[]
  security_validation[]
  expected_deliverables[]
  risks[]
  assumptions[]
  source_references[]
```

`estimated_complexity` is relative (`low`, `medium`, `high`, `unknown`) unless
the user supplies an estimation scale. The planner must not invent hours,
calendar dates, costs, team assignments, or named technologies. `responsible_role`
uses role categories such as backend engineer or security reviewer, not invented
people.

Empty work areas are valid. A backend-only requirement does not need fabricated
frontend or database tasks.

### 7.2 Example: Privileged MFA

**Requirement `SR-004`:** The system shall require multi-factor authentication
for privileged administrative access.

**Implementation summary:** Integrate MFA into the existing authentication path
and enforce successful second-factor verification before privileged routes are
authorized.

**Components:** Authentication Service, User Management, Admin Portal, Audit
Service.

**Development tasks:**

- define privileged-access MFA policy and recovery constraints;
- integrate the selected identity provider's supported second-factor flow;
- implement administrator enrollment and recovery UI;
- enforce MFA state in privileged-route authorization middleware;
- record enrollment, challenge, recovery, success, and failure events;
- document configuration and operational recovery procedures.

**Prerequisites:** `FR-002` User Authentication and `FR-005` User Role
Management, if those IDs exist in the approved SRS.

**Lifecycle placement:** Authentication / Identity milestone. In a V-Model plan,
the item appears in requirements allocation, module design, implementation,
integration verification, and system verification. In Scrum, the same work is
expressed as a feature and tasks within an approved sprint.

**Verification:**

- unit: MFA policy evaluation and privileged-route guard decisions;
- integration: identity-provider enrollment and challenge flow;
- security: authorized test cases for bypass, recovery, and session downgrade;
- acceptance: reuse the approved `SR-004` GIVEN-WHEN-THEN criterion by reference.

**Deliverables:** MFA integration, configuration, automated tests, security test
results, and recovery procedure.

The generated record must not introduce the example IDs if they do not exist in
the actual SRS.

## 8. Methodology-Aware Work Breakdown

The internal planning model uses neutral `WorkItem` and `LifecycleActivity`
objects. The renderer applies terminology and structure appropriate to the
approved methodology.

| Selected approach | Presentation hierarchy |
|---|---|
| Scrum | Epic -> feature/story -> task -> definition-of-done evidence |
| Kanban | Service/work-item class -> task -> workflow state |
| V-Model | Requirement -> system design -> module design -> implementation -> verification |
| Waterfall | Requirement -> design -> implementation -> integration -> testing |
| Incremental | Increment -> capability -> task -> release verification |
| Spiral | Risk cycle -> objective -> prototype/implementation -> evaluation |
| Hybrid | Primary lifecycle hierarchy with named overlay activities |

Agile terms are not inserted into V-Model or Waterfall plans unless the accepted
hybrid explicitly calls for them. DevSecOps activities are attached to relevant
lifecycle stages rather than represented as a cosmetic label.

## 9. Dependency and Development-Order Analysis

The internal dependency representation is a directed graph.

```text
DependencyEdge
  edge_id
  predecessor_requirement_id
  successor_requirement_id
  relationship_type
  rationale
  provenance
  confidence
  requires_confirmation
```

Supported relationship types initially are:

- `requires`: successor cannot be implemented correctly first;
- `enables`: predecessor supplies a reusable capability;
- `verifies_with`: requirements share an integration verification activity;
- `conflicts_with`: plans require an explicit resolution before approval;
- `parallelizable_with`: informative scheduling relation, not a DAG edge.

The analyzer first imports explicit requirement dependencies. It may then propose
semantic dependencies with rationale and evidence. Unconfirmed proposed edges do
not become hard blockers until approved.

Deterministic graph checks must:

- reject missing and self-referencing nodes;
- deduplicate equivalent edges;
- detect cycles in hard ordering edges;
- produce a topological order when the graph is acyclic;
- identify blockers, roots, leaves, and parallelizable groups;
- preserve conflicts instead of forcing an order;
- avoid adding edges solely to make the graph appear complete.

Visual graphs are derived from the validated adjacency list. The graph is not
the authoritative data store.

## 10. Testing and Verification Plan

Every requirement mapping includes one or more verification methods appropriate
to its type and risk. The first choice is to reuse the approved SRS acceptance
criterion by stable reference. The planner may add lower-level test design work,
but must not rewrite the acceptance criterion unless the user edits the SRS.

| Requirement signal | Candidate verification work |
|---|---|
| Pure business/functional behavior | Unit, integration, system, acceptance |
| External interface or data flow | Contract and integration testing |
| Authorization or authentication | Unit, integration, authorized security testing |
| Performance or scalability | Performance/load testing using confirmed targets |
| Availability or recovery | Resilience, restoration, and failover testing |
| Data retention or integrity | Storage lifecycle and integrity verification |
| Network boundary | Configuration review and controlled integration testing |
| Usability | Task-based usability and acceptance review |
| Safety-related behavior | Formal traceability and safety verification as authorized |

The plan can schedule an authorized penetration-test activity and define its
objective and evidence. CyberSRS itself must not execute the test, generate
exploit payloads, or target a live system.

### 10.1 Verification Record

Each test record includes a stable test ID, linked requirement IDs, level/type,
objective, acceptance-criterion references, prerequisites, expected evidence,
responsible role, lifecycle stage, and assumptions. Numeric thresholds must come
from the SRS, confirmed context, or cited guidance.

The coverage gate requires:

- 100% of approved requirements have an implementation mapping;
- 100% have at least one verification mapping or an explicit approved exception;
- every acceptance criterion is referenced by a verification item;
- every test and task reference resolves;
- coverage is reported, not confused with correctness.

## 11. Security Development Lifecycle Integration

Cybersecurity activities are planned across the selected lifecycle:

| Stage | Planned security activity |
|---|---|
| Requirements | Validate security requirements and abuse/misuse cases |
| Design | Review trust boundaries and update threat model |
| Implementation | Secure coding, peer review, secret handling controls |
| Build | SAST, dependency and secret scanning where applicable |
| Integration | Security-focused integration and configuration checks |
| Testing | DAST or authorized security testing where suitable |
| Deployment | Hardened configuration, provenance, rollback, approval gates |
| Operation | Logging, monitoring, incident response, patch/review cadence |

For V-Model + DevSecOps, the V-Model controls traceability and paired
verification while DevSecOps supplies continuous security evidence at build,
integration, and release gates. For Agile + DevSecOps, security activities enter
the backlog and definition of done. The planner never assumes a CI/CD platform
or scanning product unless confirmed.

## 12. Traceability Model

The core traceability chain is:

```text
Approved Requirement
  -> Design Component
  -> Development Task
  -> Test / Verification Item
  -> Verification Result (future execution data)
  -> Deliverable
  -> Milestone / Iteration / Sprint
```

The plan stores stable IDs and explicit links rather than relying on matching
text. The Requirements Traceability Matrix is a derived view with columns:

| Requirement ID | Components | Task IDs | Test IDs | Plan stage | Deliverables | Status |
|---|---|---|---|---|---|---|

Status initially represents planning state (`planned`, `approved`, `blocked`,
or `not_applicable`). Execution and verification-result statuses belong to a
later deployment/project-tracking integration.

Deterministic traceability validation checks forward and reverse coverage,
orphan tasks/tests, duplicate IDs, invalid references, superseded SRS links,
unapproved assumptions, and requirements omitted from the matrix.

## 13. SDLC RAG Strategy

A small software-engineering/SDLC corpus is useful for current, source-backed
methodology definitions and lifecycle guidance. It remains logically separate
from the cybersecurity corpus.

```text
Cybersecurity RAG collection
  purpose: security controls, threats, and cybersecurity guidance

SDLC / Software Engineering RAG collection
  purpose: lifecycle, development, testing, traceability, and secure-SDLC guidance
```

The two collections may reuse the existing ingestion and retrieval interfaces,
metadata contract, embedding provider, and ChromaDB infrastructure, while using
separate collection names and retrieval policies. Cross-corpus retrieval is an
explicit orchestration decision, not a merged index.

Initial source categories should include authoritative lifecycle standards,
software engineering and verification standards, official Scrum/Agile
documentation, and recognized DevOps/DevSecOps or secure-development guidance.
Licensing, version, section/page, document identity, and retrieval score remain
mandatory metadata.

No corpus is downloaded or ingested as part of this planning work. Exact sources
and licensing require a future knowledge-base review before Phase A or B exits.

## 14. Model Strategy

The first implementation uses the same approved CyberSRS Qwen model through the
existing provider-independent interface.

The model receives:

- the exact approved SRS and confirmed project context;
- the validated `ProjectDevelopmentProfile`;
- deterministic candidate scores and rule evidence;
- selected catalogue records;
- relevant SDLC RAG excerpts when available;
- strict task-specific output schemas.

Qwen may extract evidence, explain ranked candidates, draft implementation
tasks, and propose dependency/test mappings. It may not own scoring, reference
validation, graph validation, coverage calculation, plan versioning, or PDF
assembly.

A second fine-tuning round is considered only after evaluation demonstrates a
repeatable weakness in methodology explanations, requirement-to-task relevance,
dependency reasoning, structured output, or traceability. SDLC facts should be
retrieved from the catalogue/RAG rather than memorized through fine-tuning.

## 15. Human Review Workflow

The UI should extend the current SRS workspace after approval:

```text
SRS Generated
  -> Review SRS
  -> Approve Requirements
  -> Analyze Development Approach
  -> Review Development Profile and Open Questions
  -> Compare Recommended and Alternative Methodologies
  -> Accept Recommendation or Choose an Alternative
  -> Generate Development Plan
  -> Review Requirement Mappings and Traceability
  -> Edit / Regenerate Selected Plan Items
  -> Approve Development Plan
  -> Export PDF
```

The methodology view shows score, score coverage, evidence-backed reasons,
tradeoffs, assumptions, exclusions, and conditions that would change the
choice. Choosing an alternative records the user selection and preserves the
original recommendation for audit.

The plan workspace supports requirement-by-requirement review, filters for
unmapped or assumption-backed items, dependency visualization, test coverage,
validation findings, version history, and approval. A visible count must refer
to the actual number of approved SRS requirements, not the dataset's 519
training records.

## 16. Software Development Plan Document

Document 2 is generated from validated development-plan JSON and contains:

1. Project Overview
2. Approved SRS Reference and Content Hash
3. Project Development Profile
4. Selected SDLC or Hybrid Methodology
5. SDLC Selection Rationale and Score Evidence
6. Alternative Methodologies Considered
7. Development Lifecycle
8. System Module Breakdown
9. Requirement Implementation Matrix
10. Requirement Dependency Graph
11. Development Tasks / Methodology-Aware Work Breakdown
12. Testing and Verification Plan
13. Security Development Activities
14. Milestones, Iterations, or Sprints
15. Deliverables
16. Risks and Mitigations
17. Assumptions and Open Questions
18. Requirements Traceability Matrix
19. Review and Approval Record
20. Sources and Generation Metadata

The document must clearly distinguish confirmed facts, SRS-derived conclusions,
and assumptions requiring confirmation. PDF rendering follows the existing
structured JSON to template pattern and does not render raw model output.

## 17. Likely Future Modules and Files

Names are proposals and should be reconciled with the repository at the start of
implementation.

```text
src/schemas/development_plan.py
src/sdlc/catalogue.py
src/sdlc/catalogue/methodologies.json
src/sdlc/rules.py
src/sdlc/scoring.py
src/sdlc/dependency_graph.py
src/prompts/development_planning.py
src/services/development_profile_service.py
src/services/sdlc_selection_service.py
src/services/implementation_planning_service.py
src/services/verification_planning_service.py
src/services/development_plan_service.py
src/services/development_plan_validation_service.py
src/repositories/development_plan_repository.py
src/api/routes/development_plans.py
frontend/src/components/development-plan/
frontend/src/hooks/useDevelopmentPlan.ts
tests/test_development_profile.py
tests/test_sdlc_selection.py
tests/test_implementation_mapping.py
tests/test_dependency_graph.py
tests/test_verification_mapping.py
tests/test_development_plan_api.py
```

Before implementation, future work must update `docs/API_CONTRACT.md`,
`docs/DATA_MODEL.md`, `docs/REQUIREMENTS_CATALOG.md`, and create an ADR covering
the deterministic scoring model, catalogue governance, and approval/versioning
boundary.

## 18. Future Phased Roadmap

All phases below are **FUTURE WORK - NOT YET IMPLEMENTED**.

### Phase A - SDLC Knowledge Model and Catalogue

**Objective:** Define the controlled methodology taxonomy, metadata schema,
hybrid compatibility, and catalogue governance.

**Likely files:** `src/schemas/development_plan.py`, `src/sdlc/catalogue.py`,
`src/sdlc/catalogue/methodologies.json`, catalogue tests, ADR and data-model docs.

**Input:** Approved planning document and reviewed authoritative source list.

**Output:** Versioned, schema-valid catalogue and compatibility matrix.

**Tests:** Schema validation, unique IDs, required metadata, hybrid compatibility,
anti-selection rule completeness, source-reference validation.

**Completion criteria:** Every initial catalogue entry passes review; versions and
sources are recorded; no runtime model call is needed to read catalogue facts.

### Phase B - Project Development Profile Extraction

**Objective:** Derive a provenance-backed profile from an approved SRS without
inventing unknown project characteristics.

**Likely files:** profile schema, prompt, extraction service, provenance validator,
and unit/integration tests.

**Input:** Approved SRS snapshot, project context, clarification answers, and SRS
validation report.

**Output:** Validated `ProjectDevelopmentProfile` plus open questions/conflicts.

**Tests:** Provenance cases, missing-value behavior, invalid SRS references,
conflict preservation, unsupported-assumption rejection, mocked model output.

**Completion criteria:** All profile values have valid provenance; assumptions do
not appear as confirmed; material unknowns are reviewable.

### Phase C - Explainable SDLC Selection Engine

**Objective:** Rank pure and allow-listed hybrid approaches using deterministic
rules, then produce constrained explanations.

**Likely files:** rule schema/data, scoring service, hybrid composer, explanation
prompt/service, ADR, and selection tests.

**Input:** Validated profile and versioned catalogue.

**Output:** Ranked candidates, score breakdown, recommendation, alternatives,
tradeoffs, assumptions, and change conditions.

**Tests:** Golden profiles, hard exclusions, unknown-value neutrality, near ties,
sensitivity analysis, hybrid compatibility, deterministic repeatability, and
explanation fidelity.

**Completion criteria:** Same profile and versions produce the same scores; every
score is explainable; Qwen cannot introduce an unranked method.

### Phase D - Requirement-to-Implementation Planning

**Objective:** Generate one implementation mapping for every approved SRS
requirement using methodology-aware work structures.

**Likely files:** implementation schemas, planning prompt/service, coverage
validator, repository changes, and mapping tests.

**Input:** Approved SRS, selected methodology, architecture, and project profile.

**Output:** Validated `RequirementImplementationPlan` records and component/task
breakdown.

**Tests:** Requirement coverage, ID integrity, no filler work areas, no invented
technology/schedule, methodology terminology, source and assumption validation.

**Completion criteria:** 100% mapping coverage with zero orphan or unknown
requirement references; human review can edit each mapping independently.

### Phase E - Dependency and Development-Order Analysis

**Objective:** Build an evidenced dependency DAG and identify blockers,
parallelizable groups, and implementation order.

**Likely files:** graph schema, graph algorithms, dependency prompt/service, and
graph tests.

**Input:** SRS dependencies and approved implementation mappings.

**Output:** Validated dependency edges, cycle/conflict findings, and ordering.

**Tests:** Missing nodes, self edges, cycles, topological ordering, explicit versus
inferred provenance, parallel paths, and unconfirmed-edge handling.

**Completion criteria:** Hard ordering graph is acyclic or blocked with a clear
finding; every inferred edge has rationale and review status.

### Phase F - Testing and Verification Mapping

**Objective:** Map each requirement and acceptance criterion to suitable,
methodology-aware verification work.

**Likely files:** verification schemas, mapping rules, prompt/service, security
activity planner, and tests.

**Input:** Approved SRS criteria, implementation plans, risk/threat information,
and selected methodology.

**Output:** Test/verification items, security lifecycle activities, and coverage
report.

**Tests:** Criterion reuse, requirement coverage, test-level suitability, numeric
provenance, security boundary compliance, and duplicate-criterion detection.

**Completion criteria:** All requirements and acceptance criteria are traceable to
verification or an explicit approved exception; no active test is executed.

### Phase G - Software Development Plan Generation

**Objective:** Assemble, validate, version, persist, and render Document 2.

**Likely files:** orchestration/validation service, repository and database
migration, PDF template/renderer extension, API contract, and integration tests.

**Input:** Approved methodology and all validated planning artefacts.

**Output:** Canonical development-plan JSON, traceability matrix, and PDF.

**Tests:** End-to-end assembly, schema validation, version linkage, content hash,
PDF rendering, traceability, failure recovery, and stale-SRS invalidation.

**Completion criteria:** A complete plan validates and exports from one approved
SRS; raw model text never reaches UI or PDF.

### Phase H - UI and Human Approval Integration

**Objective:** Add profile, methodology comparison, plan review, editing,
traceability, versioning, and approval workflows.

**Likely files:** future API routes/client types, development-plan components,
hooks/stores, and frontend tests.

**Input:** Backend APIs and validated plan artefacts.

**Output:** End-to-end user workflow from SRS approval to plan approval/export.

**Tests:** Component, API integration, accessibility, stale-version warning,
methodology override, mapping edit/regeneration, and responsive UI tests.

**Completion criteria:** Users can inspect evidence, choose methodology, review all
mappings, approve a version, and export without hidden automated decisions.

### Phase I - Evaluation

**Objective:** Measure methodology selection and implementation-plan quality on a
frozen, independently reviewed evaluation set.

**Likely files:** evaluation cases, deterministic metrics, blind review rubric,
runner, and evaluation report.

**Input:** Representative approved SRS cases and expert reference judgments.

**Output:** Reproducible metrics, error analysis, and go/no-go recommendation.

**Tests:** Metric unit tests, frozen-set leakage checks, repeatability, evaluator
agreement calculation, and report integrity.

**Completion criteria:** Evaluation reports limitations honestly and supports a
decision on prompt/rule improvement or evidence-based fine-tuning.

### Phase J - Deployment and Project-Tracking Integration

**Objective:** Package the stable planner and, only if separately approved, expose
export/integration boundaries for development tracking tools.

**Likely files:** configuration, deployment docs, export adapters, observability,
backup/migration tests, and optional integration ADRs.

**Input:** Evaluated and approved planner from Phase I.

**Output:** Locally deployable feature with supported export formats and operating
documentation.

**Tests:** Local deployment, upgrade/migration, backup/restore, authorization,
offline operation, and integration contract tests.

**Completion criteria:** Existing local-first and security boundaries remain
intact; integrations are opt-in and do not create hidden cloud dependencies.

## 19. Evaluation Plan

### 19.1 SDLC Selection Metrics

- methodology appropriateness against expert ratings;
- rationale fidelity to deterministic score evidence;
- consistency for identical profiles and catalogue versions;
- sensitivity when one material characteristic changes;
- unsupported-assumption rate;
- top-k candidate recall and human override rate;
- inter-reviewer agreement on appropriateness.

### 19.2 Implementation and Verification Metrics

- requirement implementation coverage;
- implementation relevance and actionability;
- dependency precision and reviewer-confirmed correctness;
- acceptance-criterion reuse and testability;
- forward/reverse traceability completeness;
- unsupported assumption and invented-technology rates;
- orphan task/test/deliverable count;
- methodology-structure consistency;
- human edit and rejection rates.

The target is 100% structural mapping coverage, not automatic 100% semantic
correctness. Appropriateness and correctness require independent human review.
The evaluation dataset must be frozen and excluded from any future planner
fine-tuning data.

## 20. Risks and Controls

| Risk | Control |
|---|---|
| Methodology recommendation appears arbitrary | Deterministic score breakdown and evidence references |
| Sparse project facts create false confidence | Score coverage, unknown neutrality, and sensitivity analysis |
| LLM invents tasks, technologies, or dependencies | Schemas, provenance validation, allow-lists, human review |
| Hybrid recommendation becomes label stacking | Compatibility matrix and distinct responsibility requirement |
| Mapping count is confused with dataset records | Count only approved SRS requirements |
| Traceability breaks after SRS edits | SRS content hash and stale-plan invalidation |
| Security testing guidance crosses execution boundary | Planning-only records; no scanning, payloads, or execution |
| SDLC RAG contaminates cybersecurity retrieval | Separate collections and explicit routing |
| Fine-tuning memorizes methodology facts | Catalogue/RAG first; fine-tune only evaluated behavior gaps |
| Plan is mistaken for guaranteed schedule | No invented dates/effort; visible assumptions and approval |

## 21. Definition of Done for the Future Module

The future module is complete only when:

- an approved SRS version is a mandatory, immutable input;
- all profile values have accepted provenance or remain unresolved;
- methodology scoring is deterministic, versioned, and explainable;
- hybrid recommendations have compatible and distinct responsibilities;
- every requirement has an implementation mapping;
- every requirement has verification coverage or an approved exception;
- the dependency graph is valid and reviewable;
- traceability is complete in both directions;
- all model output is schema validated;
- human methodology and plan approvals are persisted;
- the Software Development Plan JSON and PDF reference the exact approved SRS;
- security, local-first, model-provider, and RAG separation boundaries remain
  intact;
- evaluation is completed without contamination or unsupported claims.
