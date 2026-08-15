"""Deterministic mock LLM provider (Phase 1B).

This provider exercises the full application flow without calling Ollama,
Qwen, nomic-embed-text, ChromaDB, or any real inference engine (Phase 1B rule).

Design (explicitly *not* keyword-based AI): a small fixed catalog maps the
documented demo descriptions (DEMO_PLAN.md) to curated structured outputs; any
other description is mapped deterministically via a stable content hash. The
same input always produces the same output, which is all the Phase 1B mock
needs to exercise the software flow.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from ..schemas.analysis import ProjectAnalysis
from ..schemas.clarification import ClarificationQuestionSet
from ..schemas.srs import RequirementCategory, SRSSchema
from .base import LLMOutputError, LLMProvider, LLMRequest, LLMResponse, LLMTask

MOCK_MODEL_NAME = "cybersrs-mock-1b"


def _normalise(text: str) -> str:
    """Normalise text for deterministic key lookup (lowercase, collapsed)."""
    return " ".join(text.lower().split())


def _content_hash(text: str) -> int:
    """Return a stable non-negative hash of the normalised text."""
    digest = hashlib.sha256(_normalise(text).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


class MockLLMProvider(LLMProvider):
    """A fixed, deterministic provider implementing :class:`LLMProvider`.

    The provider returns validated structured JSON for the ``ANALYSIS``,
    ``CLARIFICATION``, and ``SRS`` tasks. The caller (service layer) is still
    responsible for schema validation via :meth:`LLMProvider.parse_structured`;
    the mock's payloads are crafted to pass that validation.
    """

    provider_name = "mock"

    def __init__(self, model_name: str = MOCK_MODEL_NAME) -> None:
        super().__init__(model_name)

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a deterministic structured response for the task."""
        if request.task == LLMTask.ANALYSIS:
            payload: dict[str, Any] = self._analysis(request.user_content)
        elif request.task == LLMTask.CLARIFICATION:
            payload = self._clarification(request.user_content)
        elif request.task == LLMTask.SRS:
            payload = self._srs(request.user_content)
        else:  # pragma: no cover - guarded by the enum above
            raise LLMOutputError(f"unsupported task {request.task}")

        return LLMResponse(
            content=json.dumps(payload, sort_keys=True),
            model_name=self.model_name,
            is_deterministic=True,
        )

    # --- Deterministic data sources ------------------------------------

    _SAMPLE_ANALYSIS: dict[str, Any] = {
        "stakeholders": [
            "Campus IT department",
            "Network security team",
            "Faculty and staff",
            "Students",
        ],
        "assets": [
            "Campus network infrastructure",
            "Firewall appliances",
            "Monitoring servers",
            "End-user workstations",
        ],
        "users": [
            "Network administrators",
            "Security analysts",
            "Campus IT helpdesk",
        ],
        "constraints": [
            "Must integrate with existing campus network infrastructure",
            "Budget limitations for hardware and licensing",
            "Must follow institutional IT security policies",
            "Minimal disruption to teaching and administrative operations",
        ],
        "goals": [
            "Block malicious inbound and outbound traffic",
            "Monitor network traffic for suspicious activity",
            "Generate alerts for security incidents",
            "Maintain availability of the campus network",
        ],
        "inferred_categories": ["CAT-02", "CAT-03"],
        "missing_information": [
            "Expected number of network nodes",
            "Compliance requirements",
            "Expected traffic volume",
        ],
        "project_summary": (
            "A firewall and network-monitoring system for a college campus "
            "network that filters inbound and outbound traffic, detects "
            "suspicious activity, and alerts the IT security team."
        ),
    }

    _SAMPLE_CLARIFICATION: dict[str, Any] = {
        "questions": [
            {
                "question_text": "How many network nodes will the firewall protect?",
                "reason": "Scale affects architecture and performance requirements.",
                "is_critical": True,
                "target_gap": "Expected number of network nodes",
                "expected_answer_type": "number",
            },
            {
                "question_text": "Are there specific compliance standards to meet "
                "(e.g., PCI-DSS, HIPAA)?",
                "reason": "Compliance requirements drive security requirements.",
                "is_critical": False,
                "target_gap": "Compliance requirements",
                "expected_answer_type": "boolean",
            },
            {
                "question_text": "What is the expected network traffic volume?",
                "reason": "Traffic volume determines monitoring and alerting capacity.",
                "is_critical": False,
                "target_gap": "Expected traffic volume",
                "expected_answer_type": "number",
            },
        ]
    }

    # Documented demo projects (DEMO_PLAN.md): finite curated catalog.
    _CATALOG: dict[str, dict[str, Any]] = {
        _normalise("I want to build a firewall and monitoring system for my college network."): {
            "analysis": _SAMPLE_ANALYSIS,
            "clarification": _SAMPLE_CLARIFICATION,
        },
        _normalise(
            "Design a secure API gateway for a fintech startup. The gateway must "
            "handle authentication, rate limiting, input validation, and protect "
            "against OWASP API Top 10 risks. It should support OAuth 2.0 and API "
            "key management."
        ): {
            "analysis": {
                "stakeholders": [
                    "Fintech startup engineering team",
                    "Product management",
                    "Compliance and legal",
                    "External API consumers",
                ],
                "assets": [
                    "API gateway instance",
                    "Backend services and databases",
                    "API credentials and keys",
                    "Customer data",
                ],
                "users": [
                    "API consumers",
                    "Platform engineers",
                    "Security team",
                ],
                "constraints": [
                    "Must support OAuth 2.0 and API key management",
                    "Must protect against OWASP API Top 10 risks",
                    "Low-latency requirements for financial transactions",
                ],
                "goals": [
                    "Authenticate and authorise all API requests",
                    "Rate limit to prevent abuse",
                    "Validate input to block injection attacks",
                    "Log and audit API activity",
                ],
                "inferred_categories": ["CAT-05"],
                "missing_information": [
                    "Expected number of API consumers",
                    "Data sensitivity and PCI-DSS scope",
                    "Performance requirements (requests per second)",
                ],
                "project_summary": (
                    "A secure API gateway for a fintech startup that handles "
                    "authentication, rate limiting, input validation, and protects "
                    "against OWASP API Top 10 risks."
                ),
            },
            "clarification": {
                "questions": [
                    {
                        "question_text": "How many API consumers are expected?",
                        "reason": "Consumer count affects scalability and rate-limit design.",
                        "is_critical": True,
                        "target_gap": "Expected number of API consumers",
                        "expected_answer_type": "number",
                    },
                    {
                        "question_text": "What is the data sensitivity level "
                        "(e.g., PCI-DSS scope)?",
                        "reason": "Sensitive data drives security and compliance requirements.",
                        "is_critical": False,
                        "target_gap": "Data sensitivity and PCI-DSS scope",
                        "expected_answer_type": "text",
                    },
                    {
                        "question_text": "What performance requirements apply "
                        "(requests per second)?",
                        "reason": "Performance targets shape the rate-limiting and "
                        "capacity design.",
                        "is_critical": False,
                        "target_gap": "Performance requirements (requests per second)",
                        "expected_answer_type": "number",
                    },
                ]
            },
        },
        _normalise(
            "Build a centralised identity and access management portal for a "
            "medium-sized enterprise with 2,000 employees. The system needs single "
            "sign-on, multi-factor authentication, role-based access control, user "
            "provisioning, and an audit trail."
        ): {
            "analysis": {
                "stakeholders": [
                    "Enterprise HR department",
                    "IT operations",
                    "Security and compliance team",
                    "All employees",
                ],
                "assets": [
                    "Identity store and directory services",
                    "SSO portal",
                    "MFA tokens and devices",
                    "User accounts and roles",
                ],
                "users": [
                    "Employees",
                    "IT administrators",
                    "HR user-provisioning staff",
                    "Security auditors",
                ],
                "constraints": [
                    "Must integrate with existing directory services",
                    "Must support MFA for privileged accounts",
                    "Must provide a complete audit trail",
                ],
                "goals": [
                    "Provide single sign-on across enterprise applications",
                    "Enforce multi-factor authentication",
                    "Manage role-based access control",
                    "Automate user provisioning and de-provisioning",
                ],
                "inferred_categories": ["CAT-04"],
                "missing_information": [
                    "Existing identity providers or directory services",
                    "MFA method requirements",
                    "Compliance requirements such as SOC 2 or ISO 27001",
                ],
                "project_summary": (
                    "A centralised identity and access management portal with "
                    "single sign-on, MFA, role-based access control, user "
                    "provisioning, and an audit trail."
                ),
            },
            "clarification": {
                "questions": [
                    {
                        "question_text": "Which identity providers or directory "
                        "services must be integrated (e.g., LDAP, Active Directory)?",
                        "reason": "Existing directories determine the integration architecture.",
                        "is_critical": True,
                        "target_gap": "Existing identity providers or directory services",
                        "expected_answer_type": "list",
                    },
                    {
                        "question_text": "Which MFA methods must be supported?",
                        "reason": "MFA method choices affect the authentication design.",
                        "is_critical": False,
                        "target_gap": "MFA method requirements",
                        "expected_answer_type": "list",
                    },
                    {
                        "question_text": "What compliance requirements apply "
                        "(e.g., SOC 2, ISO 27001)?",
                        "reason": "Compliance drives audit-trail and control requirements.",
                        "is_critical": False,
                        "target_gap": "Compliance requirements such as SOC 2 or ISO 27001",
                        "expected_answer_type": "text",
                    },
                ]
            },
        },
    }

    # Generic deterministic fallback for any unlisted description.
    _FALLBACK_POOLS: dict[str, list[list[str]]] = {
        "stakeholders": [
            ["Project sponsor", "End users", "Operations team", "Security team"],
            ["System owners", "Maintenance staff", "External auditors"],
        ],
        "assets": [
            ["Network systems", "Servers and applications", "Sensitive data stores"],
            ["Infrastructure components", "Authorisation mechanisms", "Monitoring tools"],
        ],
        "users": [
            ["System administrators", "Operators"],
            ["Authorised users", "Helpdesk staff", "Managers"],
        ],
        "constraints": [
            ["Must operate within existing infrastructure", "Budget limitations apply"],
            ["Must comply with organisational security policies"],
        ],
        "goals": [
            ["Protect critical assets from unauthorised access", "Maintain system availability"],
            ["Detect and respond to security incidents", "Ensure accountability through logging"],
        ],
        "categories": [
            ["CAT-01"],
            ["CAT-04", "CAT-07"],
        ],
        "missing": [
            ["Exact system scale", "Compliance requirements"],
            ["User population size", "Integration requirements"],
        ],
    }

    # --- Deterministic generation --------------------------------------

    def _analysis(self, user_content: str) -> dict[str, Any]:
        # Extract description from template format if present
        description = user_content
        if user_content.startswith("Project description:"):
            lines = user_content.split("\n")
            # Description is on line 1 (index 1) after "Project description:"
            if len(lines) > 1:
                description = lines[1].strip()

        key = _normalise(description)
        entry = self._CATALOG.get(key)
        if entry is not None:
            return entry["analysis"]

        seed = _content_hash(description)
        pools = self._FALLBACK_POOLS
        pool_index = seed % 2
        categories = pools["categories"][pool_index]
        summary = (
            f"A cybersecurity system derived from the provided description ({seed & 0xFFFF:04x})."
        )
        analysis = {
            "stakeholders": pools["stakeholders"][pool_index],
            "assets": pools["assets"][pool_index],
            "users": pools["users"][pool_index],
            "constraints": pools["constraints"][pool_index],
            "goals": pools["goals"][pool_index],
            "inferred_categories": categories,
            "missing_information": pools["missing"][pool_index],
            "project_summary": summary,
        }
        # Guard: every generated payload must satisfy the schema. If the fixed
        # pools ever break validation, fail loudly rather than emit bad data.
        ProjectAnalysis.model_validate(analysis)
        return analysis

    def _clarification(self, user_content: str) -> dict[str, Any]:
        # Extract description from template format if present
        description = user_content
        if user_content.startswith("Project description:"):
            lines = user_content.split("\n")
            if len(lines) > 1:
                description = lines[1].strip()

        key = _normalise(description)
        entry = self._CATALOG.get(key)
        if entry is not None:
            return entry["clarification"]

        seed = _content_hash(description)
        missing = self._FALLBACK_POOLS["missing"][seed % 2]
        questions = [
            {
                "question_text": f"Please clarify: {gap}?",
                "reason": "The description does not specify this information; it "
                "is needed to produce accurate requirements.",
                "is_critical": index == 0,
                "target_gap": gap,
                "expected_answer_type": "text",
            }
            for index, gap in enumerate(missing)
        ]
        ClarificationQuestionSet.model_validate({"questions": questions})
        return {"questions": questions}

    def _srs(self, context_json: str) -> dict[str, Any]:
        """Build a deterministic, schema-valid SRS from serialised context.

        The context JSON is produced by the service layer from the stored
        ProjectContext; the resulting SRS contains no external citations
        because RAG does not exist yet (Phase 1C rule).

        Handles both the legacy direct JSON format and the new template format
        that prefixes with "Project context:\n".
        """
        # Extract JSON from template format if present
        if context_json.strip().startswith("Project context:"):
            # Find the first { and extract the complete JSON object
            json_start = context_json.find("{")
            if json_start >= 0:
                # Find the matching closing brace
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(context_json[json_start:], start=json_start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                context_json = context_json[json_start:json_end]
        context = json.loads(context_json) if context_json.strip() else {}
        description = context.get("description", "A cybersecurity project.")
        categories = context.get("inferred_categories") or ["CAT-01"]
        stakeholders = context.get("stakeholders") or ["Project sponsors", "Operations team"]
        users = context.get("users") or ["System administrators", "Operators"]
        project_name = context.get("project_name", "Untitled Cybersecurity Project")

        def _req(
            req_id: str,
            category: RequirementCategory,
            title: str,
            statement: str,
            rationale: str,
            priority: str = "must",
            acceptance: str | None = None,
            confidence: str = "high",
        ) -> dict[str, Any]:
            return {
                "id": req_id,
                "category": category,
                "title": title,
                "statement": statement,
                "rationale": rationale,
                "priority": priority,
                "acceptance_criteria": acceptance
                or f"Verify that {statement.rstrip('.')} is demonstrated under test.",
                "dependencies": [],
                "source_references": [],
                "confidence": confidence,
                "user_confirmed": False,
            }

        requirements = [
            _req(
                "FR-001",
                RequirementCategory.FUNCTIONAL,
                "Traffic Filtering",
                "The system shall filter inbound and outbound network traffic "
                "according to configurable allow and deny rules.",
                "Filtering is the core control that prevents unauthorised access "
                "through the perimeter.",
                priority="must",
            ),
            _req(
                "FR-002",
                RequirementCategory.FUNCTIONAL,
                "Monitoring and Alerting",
                "The system shall monitor network traffic for suspicious activity "
                "and generate alerts for the security team.",
                "Monitoring provides the detection capability required to respond to incidents.",
                priority="must",
            ),
            _req(
                "FR-003",
                RequirementCategory.FUNCTIONAL,
                "Rule Management",
                "The system shall allow administrators to manage firewall rules "
                "through a secure interface.",
                "Administrators need a controlled way to update filtering behaviour.",
                priority="should",
            ),
            _req(
                "NFR-001",
                RequirementCategory.NON_FUNCTIONAL,
                "Availability",
                "The system shall maintain availability of the monitored network "
                "with no more than 5 minutes of downtime per month.",
                "Campus operations depend on continuous network availability.",
                priority="must",
            ),
            _req(
                "NFR-002",
                RequirementCategory.NON_FUNCTIONAL,
                "Performance",
                "The system shall process at least 10,000 packets per second "
                "without dropping legitimate traffic.",
                "Performance ensures the security controls do not become a bottleneck.",
                priority="should",
            ),
            _req(
                "SEC-001",
                RequirementCategory.SECURITY,
                "Authenticated Administration",
                "The system shall require multi-factor authentication for all "
                "administrative access.",
                "Protects the control plane from unauthorised modification.",
                priority="must",
            ),
            _req(
                "SEC-002",
                RequirementCategory.SECURITY,
                "Encrypted Logs",
                "The system shall store security logs in an encrypted format at rest.",
                "Protects sensitive monitoring data from disclosure.",
                priority="should",
            ),
            _req(
                "DATA-001",
                RequirementCategory.DATA,
                "Log Retention",
                "The system shall retain security logs for at least 90 days.",
                "Retention supports post-incident analysis and compliance.",
                priority="should",
            ),
            _req(
                "NET-001",
                RequirementCategory.NETWORK,
                "Network Segmentation",
                "The system shall support segmented network zones with distinct "
                "filtering policies.",
                "Segmentation limits lateral movement in the campus network.",
                priority="should",
            ),
        ]

        threats = [
            {
                "threat_id": "THR-001",
                "name": "Unauthorised Perimeter Access",
                "description": "An attacker attempts to bypass the firewall to "
                "reach internal systems.",
                "category": "Tampering",
                "severity": "high",
                "affected_assets": ["Campus network infrastructure"],
                "mitigations": [
                    {
                        "mitigation_id": "MIT-001",
                        "description": "Enforce deny-by-default firewall rules "
                        "and rate-limit failed connection attempts.",
                        "related_requirement_ids": ["FR-001", "SEC-001"],
                    }
                ],
            },
            {
                "threat_id": "THR-002",
                "name": "Log Tampering",
                "description": "An attacker with administrative access alters "
                "or deletes security logs.",
                "category": "Repudiation",
                "severity": "medium",
                "affected_assets": ["Monitoring servers"],
                "mitigations": [
                    {
                        "mitigation_id": "MIT-002",
                        "description": "Use append-only, cryptographically signed log storage.",
                        "related_requirement_ids": ["SEC-002"],
                    }
                ],
            },
        ]

        payload = {
            "metadata": {
                "project_name": project_name,
                "version": context.get("version", 1),
                "generated_at": datetime.now(UTC).isoformat(),
                "model_name": self.model_name,
                "adapter_name": None,
                "inferred_categories": categories,
            },
            "project_overview": {
                "description": description,
                "purpose": f"Deliver a structured SRS for: {description}",
                "context": "Generated deterministically by the CyberSRS mock provider.",
            },
            "scope": {
                "in_scope": categories,
                "out_of_scope": [
                    "Active penetration testing",
                    "Malware analysis or exploit development",
                    "Automatic network configuration changes",
                ],
            },
            "assumptions": [
                "The system operates within the existing campus network infrastructure.",
                "Administrative users are trusted and subject to organisational policy.",
            ],
            "stakeholders": stakeholders,
            "user_roles": users,
            "functional_requirements": [r for r in requirements if r["category"] == "functional"],
            "non_functional_requirements": [
                r for r in requirements if r["category"] == "non_functional"
            ],
            "security_requirements": [r for r in requirements if r["category"] == "security"],
            "data_requirements": [r for r in requirements if r["category"] == "data"],
            "network_requirements": [r for r in requirements if r["category"] == "network"],
            "architecture_summary": {
                "overview": "A layered security architecture with a perimeter "
                "firewall, monitoring sensors, and a central management plane.",
                "components": [
                    {
                        "name": "Perimeter Firewall",
                        "description": "Enforces allow/deny filtering rules at the network edge.",
                        "responsibilities": ["Filter traffic", "Block malicious connections"],
                    },
                    {
                        "name": "Monitoring Server",
                        "description": "Collects and analyses network flow data.",
                        "responsibilities": ["Detect anomalies", "Generate alerts"],
                    },
                ],
                "data_flows": ["Network packets -> Firewall -> Internal segments"],
                "deployment_notes": "Deployed on dedicated campus infrastructure.",
            },
            "threats": threats,
            "mitigations": [
                mitigation for threat in threats for mitigation in threat.get("mitigations", [])
            ],
            "testing_strategy": [
                {
                    "recommendation_id": "TEST-001",
                    "description": "Validate that firewall rules block all denied traffic.",
                    "type": "security",
                    "related_requirement_ids": ["FR-001"],
                },
                {
                    "recommendation_id": "TEST-002",
                    "description": "Verify alert generation for known attack patterns.",
                    "type": "system",
                    "related_requirement_ids": ["FR-002"],
                },
            ],
            "risks": [
                {
                    "risk_id": "RISK-001",
                    "description": "Budget constraints may limit hardware capacity.",
                    "likelihood": "medium",
                    "impact": "high",
                    "mitigation": "Prioritise essential filtering and monitoring features.",
                }
            ],
            "unresolved_questions": [
                "Exact compliance standards to be confirmed by the project owner."
            ],
            "references": [],
            "validation_report": None,
        }

        # Guard: the payload must satisfy the full SRS schema before it is
        # returned; never emit an invalid SRS.
        SRSSchema.model_validate(payload)
        return payload
