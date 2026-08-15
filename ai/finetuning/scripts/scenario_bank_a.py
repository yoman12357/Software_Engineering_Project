"""Scenario bank A (SCN-001..SCN-020) for the CyberSRS QLoRA training dataset.

Hand-authored, genuinely distinct synthetic cybersecurity project scenarios.
Each scenario models a complete CyberSRS project: informal description, full
ProjectAnalysis, clarification Q&A, and a validated requirement set. No
scenario mirrors the 30 held-out evaluation cases in
``ai/evaluation/dataset.json``.

All content is original and authored for this project; license: Apache-2.0.
"""

from __future__ import annotations

from typing import Any

# Compact requirement builder: fills stable defaults so authoring stays terse.
def req(
    req_id: str,
    category: str,
    title: str,
    statement: str,
    rationale: str,
    acceptance_criteria: str,
    priority: str = "must",
    confidence: str = "high",
    numeric: list[dict[str, str]] | None = None,
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    """Build a Requirement-shaped dict with stable defaults."""
    return {
        "id": req_id,
        "category": category,
        "title": title,
        "statement": statement,
        "rationale": rationale,
        "priority": priority,
        "acceptance_criteria": acceptance_criteria,
        "dependencies": dependencies or [],
        "source_references": [],
        "confidence": confidence,
        "user_confirmed": False,
        "numeric": numeric or [],
    }


SCN_001: dict[str, Any] = {
    "id": "SCN-001",
    "name": "Municipal Water Utility SCADA Monitoring",
    "description": (
        "We need a monitoring system for the SCADA network at our municipal water "
        "treatment and distribution utility. It should watch for abnormal control "
        "traffic, alert operators to possible tampering, and keep a secure record "
        "of all events for at least two years."
    ),
    "categories": ["CAT-03", "CAT-07", "CAT-01"],
    "analysis": {
        "stakeholders": [
            "Municipal water utility operations",
            "City IT department",
            "State public-health regulator",
        ],
        "assets": [
            "SCADA control network",
            "PLC controllers and field devices",
            "Pump stations and distribution valves",
            "Event and alarm records",
        ],
        "users": [
            "Control-room operators",
            "OT security analysts",
            "Maintenance technicians",
        ],
        "constraints": [
            "System must be passive: it must never send commands to PLCs",
            "Must operate within the air-gapped OT segment",
            "Retention records must be append-only",
        ],
        "goals": [
            "Detect abnormal control-plane traffic",
            "Alert operators to suspected tampering",
            "Maintain a tamper-evident event archive",
        ],
        "missing_information": [
            "Number of pump stations to monitor",
            "Existing SIEM or log platform to integrate with",
            "Regulatory reporting requirements",
        ],
        "project_summary": (
            "A passive monitoring system for a municipal water utility's SCADA "
            "network that detects abnormal control traffic, alerts operators to "
            "tampering, and keeps tamper-evident event records for two years."
        ),
    },
    "clarifications": [
        {
            "question": "How many pump stations must be covered by monitoring?",
            "answer": "Eleven pump stations across three districts.",
        },
        {
            "question": "Is there an existing log platform to forward events to?",
            "answer": "No, we want this system to be the primary store.",
        },
        {
            "question": "Must events be reported to the state regulator automatically?",
            "answer": "Only on request; manual export is enough for now.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Abnormal Traffic Detection",
            "The system shall detect control-plane traffic that deviates from "
            "baselined patterns and raise an alert.",
            "The description asks the system to watch for abnormal control traffic, "
            "so a detection capability over baselined patterns is an explicit user requirement.",
            "GIVEN a live SCADA network with an established traffic baseline, WHEN a packet "
            "sequence exceeds the baseline deviation threshold, THEN the system shall raise an alert within 30 seconds.",
            priority="must",
            numeric=[
                {"value": "30 seconds", "provenance": "ASSUMPTION_REQUIRING_CONFIRMATION"}
            ],
        ),
        req(
            "SEC-001",
            "security",
            "Append-Only Event Archive",
            "The system shall store all detected events in an append-only archive "
            "that cannot be modified or deleted by operators.",
            "The user explicitly requires a secure record of all events, and tampering "
            "by insiders is a core risk for OT event stores.",
            "GIVEN an operator with administrative access, WHEN the operator attempts to edit or delete an "
            "archived event, THEN the system shall reject the change and log the attempt.",
            priority="must",
        ),
        req(
            "NFR-001",
            "non_functional",
            "Passive Operation Constraint",
            "The system shall operate entirely passively and never transmit commands "
            "to field devices.",
            "The operator explicitly states the monitoring system must never send commands "
            "to PLCs, which is a hard safety constraint for OT networks.",
            "GIVEN the system connected inline to the OT segment, WHEN it is powered on and running, "
            "THEN it shall transmit no outbound control packets during a planned soak test.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A passive tap-based sensor on the OT segment feeding a central "
            "monitoring appliance with a tamper-evident archive."
        ),
        "components": [
            {
                "name": "OT Network Sensor",
                "description": "Passive traffic capture at the SCADA segment.",
                "responsibilities": ["Capture control-plane packets", "Compute baseline deviations"],
            },
            {
                "name": "Monitoring Appliance",
                "description": "Correlates alerts and stores the archive.",
                "responsibilities": ["Raise operator alerts", "Write append-only event archive"],
            },
        ],
        "data_flows": ["OT segment -> sensor -> monitoring appliance"],
        "deployment_notes": "Deployed inside the OT network; outbound access is denied.",
    },
    "threats": [
        {
            "name": "Insider Event Tampering",
            "description": "An operator or attacker alters archived events to hide an incident.",
            "category": "Repudiation",
            "severity": "high",
            "affected_assets": ["Event and alarm records"],
            "mitigations": [
                {
                    "description": "Append-only archive with write-once media and tamper logging.",
                    "related_requirement_ids": ["SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Passive OT traffic monitoring",
            "Operator alerting",
            "Two-year tamper-evident archive",
        ],
        "out_of_scope": [
            "Sending commands to field devices",
            "Automatic pump control",
        ],
    },
    "assumptions": [
        "Monitoring is passive and never alters control behaviour.",
    ],
    "testing": [
        {
            "description": "Inject a synthetic deviating packet sequence and verify an alert is raised.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "Alert fatigue may reduce operator attention.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Severity-ranked alerting and quiet periods.",
    },
    "unresolved": [
        "Regulator export format to be confirmed.",
    ],
}


SCN_002: dict[str, Any] = {
    "id": "SCN-002",
    "name": "Regional Airport Guest Wi-Fi Security",
    "description": (
        "Build a secure guest Wi-Fi system for a regional airport terminal. Guests "
        "connect to a separate portal network, and the system must prevent guests "
        "from reaching internal airline systems, throttle heavy users, and log "
        "connection metadata for law enforcement requests."
    ),
    "categories": ["CAT-08", "CAT-02"],
    "analysis": {
        "stakeholders": [
            "Airport authority",
            "Airlines operating at the terminal",
            "Law enforcement liaison",
        ],
        "assets": [
            "Guest wireless access points",
            "Captive portal and DNS services",
            "Connection metadata logs",
            "Internal airline and operations networks",
        ],
        "users": [
            "Airport visitors",
            "Airport IT administrators",
            "Security response staff",
        ],
        "constraints": [
            "Guest traffic must be fully isolated from internal networks",
            "Retention of connection metadata is legally required",
            "No guest authentication beyond a click-through portal",
        ],
        "goals": [
            "Provide free guest connectivity",
            "Isolate guest traffic from internal systems",
            "Throttle heavy users to preserve fairness",
            "Log metadata for law enforcement requests",
        ],
        "missing_information": [
            "Peak concurrent guest count",
            "Required metadata retention period",
            "Bandwidth budget per guest",
        ],
        "project_summary": (
            "A secure guest Wi-Fi system for a regional airport terminal that isolates "
            "guest traffic from internal airline systems, throttles heavy users, and "
            "retains connection metadata for law enforcement requests."
        ),
    },
    "clarifications": [
        {
            "question": "What is the peak number of concurrent guests?",
            "answer": "Up to 800 concurrent guests at peak.",
        },
        {
            "question": "How long must connection metadata be retained?",
            "answer": "Six months.",
        },
        {
            "question": "Is there a bandwidth limit per guest?",
            "answer": "Two megabits per second per guest.",
        },
    ],
    "requirements": [
        req(
            "NET-001",
            "network",
            "Guest Network Isolation",
            "The system shall place all guest wireless traffic in a network segment "
            "with no routable path to internal airline or operations networks.",
            "Isolation of guest traffic from internal systems is the explicit security "
            "goal stated in the project description.",
            "GIVEN a guest connected to the portal network, WHEN the guest attempts to reach any internal "
            "network address, THEN the connection shall be blocked and the attempt logged.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Per-Guest Bandwidth Throttling",
            "The system shall limit each guest session to a configured bandwidth cap.",
            "The operator specifies a two megabits per second cap per guest, making "
            "throttling an explicit USER_SPECIFIED requirement.",
            "GIVEN an active guest session, WHEN sustained throughput exceeds two megabits per second, "
            "THEN the system shall enforce the cap and log the throttling event.",
            priority="must",
            numeric=[
                {"value": "2 megabits per second", "provenance": "USER_SPECIFIED"}
            ],
        ),
        req(
            "DATA-001",
            "data",
            "Connection Metadata Retention",
            "The system shall retain connection metadata for a configured retention "
            "period and purge older records.",
            "Retention is legally required per the description and the operator "
            "confirms six months during clarification.",
            "GIVEN records older than the six-month retention window, WHEN the purge job runs, "
            "THEN those records shall be irrecoverably removed and the purge logged.",
            priority="must",
            numeric=[
                {"value": "6 months", "provenance": "USER_SPECIFIED"}
            ],
        ),
    ],
    "architecture": {
        "overview": (
            "Guest access points tunnel into a dedicated guest VRF with a captive "
            "portal and per-user shaping."
        ),
        "components": [
            {
                "name": "Captive Portal",
                "description": "Click-through terms portal for guests.",
                "responsibilities": ["Issue guest sessions", "Record connection metadata"],
            },
            {
                "name": "Guest VRF",
                "description": "Isolated routing domain for guest traffic.",
                "responsibilities": ["Enforce isolation", "Apply per-guest bandwidth caps"],
            },
        ],
        "data_flows": ["Guest device -> access point -> guest VRF -> internet"],
        "deployment_notes": "Guest VRF terminates at the airport DMZ.",
    },
    "threats": [
        {
            "name": "Guest Pivoting to Internal Networks",
            "description": "A guest scans for internal airline systems and pivots toward them.",
            "category": "Lateral Movement",
            "severity": "critical",
            "affected_assets": ["Internal airline and operations networks"],
            "mitigations": [
                {
                    "description": "Full network isolation plus inter-VRF blocking.",
                    "related_requirement_ids": ["NET-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Guest portal Wi-Fi",
            "Isolation and throttling",
            "Metadata retention",
        ],
        "out_of_scope": [
            "Staff Wi-Fi",
            "Device onboarding for passengers",
        ],
    },
    "assumptions": [
        "Guests require only a click-through portal, not real authentication.",
    ],
    "testing": [
        {
            "description": "Attempt routing from guest VRF to internal address and verify the block.",
            "type": "security",
            "related_requirement_ids": ["NET-001"],
        }
    ],
    "risk": {
        "description": "Wireless interference in the terminal reduces coverage quality.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "AP density planning and channel planning.",
    },
    "unresolved": [
        "Exact format for law enforcement metadata export.",
    ],
}


SCN_003: dict[str, Any] = {
    "id": "SCN-003",
    "name": "Insurance Broker Client Portal",
    "description": (
        "Our insurance brokerage needs a client-facing web portal where brokers "
        "upload policy documents, clients review and sign them, and every "
        "view and signature is recorded. The portal must not allow a client to "
        "see documents from other clients."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Insurance brokerage partners",
            "Client organisations",
            "Compliance and legal team",
        ],
        "assets": [
            "Policy documents",
            "Client account records",
            "Signature audit log",
            "Web application and API layer",
        ],
        "users": [
            "Brokers",
            "Client representatives",
            "Portal administrators",
        ],
        "constraints": [
            "Client data must never cross client boundaries",
            "Signatures must be evidenced with timestamps",
            "Must integrate with the existing CRM",
        ],
        "goals": [
            "Let brokers upload policy documents securely",
            "Let clients review and sign documents",
            "Record every view and signature for audit",
        ],
        "missing_information": [
            "SSO provider for client authentication",
            "Document storage location and encryption requirements",
            "Audit log retention period",
        ],
        "project_summary": (
            "A client-facing insurance portal where brokers upload policy documents, "
            "clients review and sign them, and every view and signature is recorded "
            "in an audit log, with strict client data isolation."
        ),
    },
    "clarifications": [
        {
            "question": "Which identity provider should authenticate clients?",
            "answer": "We will use the existing Azure AD tenant with guest accounts.",
        },
        {
            "question": "Where should documents be stored?",
            "answer": "Encrypted object storage; we prefer S3-compatible.",
        },
        {
            "question": "How long should the audit log be kept?",
            "answer": "Seven years for signed documents.",
        },
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Client Data Isolation",
            "The system shall enforce per-client data isolation so that a "
            "client user can only access documents belonging to their own account.",
            "The description makes cross-client access the primary forbidden behaviour.",
            "GIVEN a client user authenticated for account A, WHEN the user requests a document ID owned by "
            "account B, THEN the system shall return a not-found response and log the attempt.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Document Review Workflow",
            "The system shall allow clients to review uploaded documents and "
            "record each view event with user and timestamp.",
            "Recording every view is an explicit requirement in the project description.",
            "GIVEN a signed-in client, WHEN the client opens an available policy document, THEN the system "
            "shall record the view event with user identity and UTC timestamp.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Electronic Signature Capture",
            "The system shall capture an electronic signature for a document and "
            "store the signature event with the signer identity and timestamp.",
            "Signature capture with evidential timestamping is a stated portal function.",
            "GIVEN a client with an open document awaiting signature, WHEN the client submits the signature, "
            "THEN the system shall store an unalterable signature record within 5 seconds.",
            priority="must",
            numeric=[
                {"value": "5 seconds", "provenance": "ASSUMPTION_REQUIRING_CONFIRMATION"}
            ],
        ),
    ],
    "architecture": {
        "overview": (
            "A web portal backed by an API layer, encrypted object storage for "
            "documents, and an append-only audit store."
        ),
        "components": [
            {
                "name": "Portal Web App",
                "description": "Client-facing document review interface.",
                "responsibilities": ["Authenticate via Azure AD", "Serve documents by account"],
            },
            {
                "name": "Audit Store",
                "description": "Append-only log of views and signatures.",
                "responsibilities": ["Record view events", "Record signature events"],
            },
        ],
        "data_flows": ["Client -> portal -> API -> document store"],
        "deployment_notes": "Deployed in the brokerage cloud subscription.",
    },
    "threats": [
        {
            "name": "IDOR Document Access",
            "description": "A client guesses another account's document ID and accesses it.",
            "category": "Broken Access Control",
            "severity": "critical",
            "affected_assets": ["Policy documents"],
            "mitigations": [
                {
                    "description": "Account-scoped authorization on every document read.",
                    "related_requirement_ids": ["SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Client document review and signature",
            "Audit logging",
        ],
        "out_of_scope": [
            "Underwriting workflow",
            "Payment processing",
        ],
    },
    "assumptions": [
        "Azure AD guest accounts provide client identities.",
    ],
    "testing": [
        {
            "description": "Attempt cross-account document access and verify the block.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "Broker error uploads documents to the wrong client account.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Confirmation step before publishing a document to a client.",
    },
    "unresolved": [
        "Whether two-factor authentication is required for clients.",
    ],
}


SCN_004: dict[str, Any] = {
    "id": "SCN-004",
    "name": "Retail POS Network Segmentation",
    "description": (
        "A national retail chain wants to segment its store networks so card "
        "payment devices are isolated from the general store network and from "
        "each other. We need to isolate the payment LAN, restrict admin access, "
        "and detect any attempts to bridge the two networks."
    ),
    "categories": ["CAT-08", "CAT-02", "CAT-03"],
    "analysis": {
        "stakeholders": [
            "Retail IT operations",
            "Payment card compliance officer",
            "Store operations management",
        ],
        "assets": [
            "Payment terminal network (PIN pads)",
            "General store network",
            "Payment gateway credentials",
            "Network switch and firewall inventory",
        ],
        "users": [
            "Store managers",
            "Payment system administrators",
            "Regional IT support",
        ],
        "constraints": [
            "Payment traffic must not mix with general store traffic",
            "Changes must not disrupt till operation during trading hours",
            "PCI-DSS scope must shrink, not expand",
        ],
        "goals": [
            "Isolate the payment LAN from the store LAN",
            "Restrict administrative access to the segmented network",
            "Detect bridging attempts between networks",
        ],
        "missing_information": [
            "Number of stores and terminal types",
            "Existing switch vendor and model mix",
            "Cardholder data storage locations",
        ],
        "project_summary": (
            "Store network segmentation for a retail chain that isolates payment "
            "terminals from the general store network, restricts admin access, and "
            "detects bridging attempts."
        ),
    },
    "clarifications": [
        {
            "question": "How many stores and terminal types are in scope?",
            "answer": "120 stores, countertop PIN pads and mobile terminals.",
        },
        {
            "question": "Which switch vendor is deployed?",
            "answer": "A mix of two vendors across stores.",
        },
        {
            "question": "Where is cardholder data currently stored?",
            "answer": "Terminals only; no central card data store.",
        },
    ],
    "requirements": [
        req(
            "NET-001",
            "network",
            "Payment LAN Isolation",
            "The system shall keep payment terminal traffic on a dedicated network "
            "segment that has no routing relationship with the general store network.",
            "Isolation of payment devices from the store network is the central "
            "requirement stated in the description.",
            "GIVEN a payment terminal on the payment segment, WHEN the terminal attempts to reach the "
            "general store network, THEN the attempt shall be blocked at the segment boundary.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Bridging Attempt Detection",
            "The system shall detect and alert on any attempt to bridge the payment "
            "and general store networks.",
            "Detecting bridging attempts is an explicit security goal in the project description.",
            "GIVEN an active store network, WHEN traffic matching a bridging attempt is observed, THEN the "
            "system shall raise a high-severity alert within 60 seconds.",
            priority="must",
            numeric=[
                {"value": "60 seconds", "provenance": "ASSUMPTION_REQUIRING_CONFIRMATION"}
            ],
        ),
        req(
            "SEC-001",
            "security",
            "Restricted Payment Segment Administration",
            "The system shall require multi-factor authentication for all "
            "administrative access to the payment segment devices.",
            "Admin access to the payment LAN is a stated concern; MFA follows standard "
            "access-control practice for the risk identified.",
            "GIVEN an administrator, WHEN authenticating to a payment segment device, THEN a second "
            "factor shall be required in addition to the primary credential.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": (
            "Store-level segmentation with a payment VRF per store and central "
            "monitoring of segment boundaries."
        ),
        "components": [
            {
                "name": "Payment Segment Switch",
                "description": "Dedicated switch domain for terminals.",
                "responsibilities": ["Isolate terminal traffic", "Apply ACLs"],
            },
            {
                "name": "Segment Monitoring",
                "description": "Watches for cross-segment bridging.",
                "responsibilities": ["Detect bridging", "Raise alerts"],
            },
        ],
        "data_flows": ["Terminal -> payment segment -> payment gateway"],
        "deployment_notes": "Deployed per store; centrally managed.",
    },
    "threats": [
        {
            "name": "Network Bridging",
            "description": "An attacker uses a dual-homed device to bridge payment and store networks.",
            "category": "Lateral Movement",
            "severity": "critical",
            "affected_assets": ["Payment terminal network (PIN pads)"],
            "mitigations": [
                {
                    "description": "Segment isolation and active bridging detection.",
                    "related_requirement_ids": ["NET-001", "FR-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Store payment network segmentation",
            "Bridging detection",
        ],
        "out_of_scope": [
            "Central card data storage",
            "Terminal hardware procurement",
        ],
    },
    "assumptions": [
        "Terminals are the only cardholder data locations.",
    ],
    "testing": [
        {
            "description": "Simulate a bridge attempt and confirm the alert fires.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "Misconfiguration during rollout could expand PCI-DSS scope.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Baseline configuration review before store rollout.",
    },
    "unresolved": [
        "Central management tool for the switch mix.",
    ],
}


SCN_005: dict[str, Any] = {
    "id": "SCN-005",
    "name": "Pharmaceutical Research DLP",
    "description": (
        "A pharmaceutical company needs to stop confidential research documents "
        "from leaving the organisation. We want to classify documents on the "
        "research share, block email and web uploads of classified files, and "
        "review an alert list of risky actions."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Pharma research and development",
            "Legal and compliance",
            "IT security team",
        ],
        "assets": [
            "Research document share",
            "Clinical trial data",
            "Email and web gateway",
            "DLP classification store",
        ],
        "users": [
            "Research scientists",
            "Legal reviewers",
            "Security analysts",
        ],
        "constraints": [
            "Classification must not block legitimate research sharing",
            "No data may leave the company network via unsanctioned channels",
            "Alert review must be possible without legal exposure",
        ],
        "goals": [
            "Classify documents on the research share",
            "Block email and web uploads of classified files",
            "Provide an alert list for review",
        ],
        "missing_information": [
            "Document metadata standard for classification",
            "Whether encrypted archives are in scope",
            "Alert review workflow owner",
        ],
        "project_summary": (
            "A data loss prevention system for a pharmaceutical company that classifies "
            "research documents, blocks unsanctioned email and web uploads of classified "
            "files, and provides an alert list for security review."
        ),
    },
    "clarifications": [
        {
            "question": "What metadata standard should drive classification?",
            "answer": "Use the existing SharePoint sensitivity labels.",
        },
        {
            "question": "Should encrypted archives be scanned?",
            "answer": "Yes, flag them as alerts even if contents are undecryptable.",
        },
        {
            "question": "Who owns the alert workflow?",
            "answer": "The security team reviews; legal is consulted on disputes.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Document Classification",
            "The system shall classify documents on the research share using the "
            "configured sensitivity-label scheme.",
            "Classification is the first capability named in the description.",
            "GIVEN a document on the research share, WHEN the classification engine evaluates it, THEN the "
            "document shall be tagged with the matching sensitivity label.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Exfiltration Blocking",
            "The system shall block email and web uploads of documents carrying a "
            "classified label.",
            "Blocking unsanctioned transfers of classified documents is the core "
            "protection goal stated by the organisation.",
            "GIVEN a user sending a classified document via email or web upload, WHEN the DLP engine "
            "matches the label, THEN the transfer shall be blocked and an alert created.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Encrypted Archive Flagging",
            "The system shall flag encrypted archives as alerts even when their "
            "contents cannot be inspected.",
            "The clarification answer explicitly extends coverage to encrypted archives.",
            "GIVEN an encrypted archive traversing the gateway, WHEN the DLP engine cannot inspect it, "
            "THEN the system shall raise a review alert.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": (
            "Cloud-native DLP with connector-based classification of the research "
            "share and inline inspection of email and web traffic."
        ),
        "components": [
            {
                "name": "Classification Engine",
                "description": "Applies sensitivity labels to documents.",
                "responsibilities": ["Evaluate documents", "Apply labels"],
            },
            {
                "name": "Gateway Inspector",
                "description": "Inline email and web upload inspection.",
                "responsibilities": ["Match labels", "Block transfers", "Create alerts"],
            },
        ],
        "data_flows": ["Share -> classification engine", "Email/web -> gateway inspector"],
        "deployment_notes": "SaaS-managed DLP platform.",
    },
    "threats": [
        {
            "name": "Insider Data Exfiltration",
            "description": "A researcher leaks classified documents via email or web upload.",
            "category": "Data Loss",
            "severity": "high",
            "affected_assets": ["Research document share"],
            "mitigations": [
                {
                    "description": "Inline blocking of classified transfers.",
                    "related_requirement_ids": ["SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Research share classification",
            "Email and web upload blocking",
            "Alert review list",
        ],
        "out_of_scope": [
            "Endpoint device control",
            "Printing controls",
        ],
    },
    "assumptions": [
        "SharePoint sensitivity labels drive classification.",
    ],
    "testing": [
        {
            "description": "Send a labelled document via the gateway and verify the block.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "Over-blocking disrupts legitimate research collaboration.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Review workflows and exception handling.",
    },
    "unresolved": [
        "Whether removable media must be covered.",
    ],
}


SCN_006: dict[str, Any] = {
    "id": "SCN-006",
    "name": "University Research Lab Zero-Trust Access",
    "description": (
        "Our university wants to stop students sharing credentials for lab "
        "systems. We need identity-based access to research workstations where "
        "each user is verified per session, access is limited to the lab resources "
        "they are allowed, and unusual access patterns trigger a review."
    ),
    "categories": ["CAT-08", "CAT-04"],
    "analysis": {
        "stakeholders": [
            "University research faculty",
            "IT operations",
            "Research ethics office",
        ],
        "assets": [
            "Research workstation fleet",
            "Research data stores",
            "Identity directory",
            "Lab network segments",
        ],
        "users": [
            "Graduate researchers",
            "Faculty principal investigators",
            "Lab administrators",
        ],
        "constraints": [
            "Must support researchers who move between labs",
            "Access decisions must be per-session, not per-device",
            "Must not require changes to research applications",
        ],
        "goals": [
            "Verify each user identity per session",
            "Limit access to allowed lab resources",
            "Flag unusual access patterns for review",
        ],
        "missing_information": [
            "Number of research workstations",
            "Identity source of truth",
            "Review escalation path",
        ],
        "project_summary": (
            "Zero-trust access for university research labs that verifies each user "
            "per session, limits access to allowed lab resources, and flags unusual "
            "access patterns for review."
        ),
    },
    "clarifications": [
        {
            "question": "How many research workstations are in scope?",
            "answer": "Around 240 workstations across six labs.",
        },
        {
            "question": "What is the identity source of truth?",
            "answer": "The university central identity directory.",
        },
        {
            "question": "Who handles review alerts?",
            "answer": "Faculty PIs review, escalated to IT security when needed.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Per-Session Identity Verification",
            "The system shall verify the identity of each user for every access "
            "session to a lab workstation.",
            "Per-session verification is the central anti-credential-sharing goal "
            "described by the university.",
            "GIVEN a user requesting a lab workstation session, WHEN the request is made, THEN the system "
            "shall require fresh identity verification before granting access.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Least-Privilege Resource Access",
            "The system shall restrict each session to only the lab resources "
            "explicitly permitted for that user.",
            "Limiting access to allowed resources is the stated access-control "
            "requirement for the zero-trust design.",
            "GIVEN an authenticated user session, WHEN the user accesses a resource outside their "
            "permitted set, THEN the access shall be denied and logged.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Unusual Access Pattern Detection",
            "The system shall flag sessions whose access patterns deviate from the "
            "user's established behaviour for review.",
            "Flagging unusual access is the detection goal stated in the description.",
            "GIVEN an active session history, WHEN a session deviates from the established behaviour "
            "baseline, THEN the system shall create a review ticket.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": (
            "An access broker in front of lab resources enforcing per-session "
            "identity checks and policy."
        ),
        "components": [
            {
                "name": "Access Broker",
                "description": "Central policy enforcement point.",
                "responsibilities": ["Verify identity per session", "Enforce resource policy"],
            },
            {
                "name": "Behaviour Analytics",
                "description": "Detects unusual access patterns.",
                "responsibilities": ["Baseline user behaviour", "Flag deviations"],
            },
        ],
        "data_flows": ["User -> access broker -> lab workstation"],
        "deployment_notes": "Deployed in the university data centre.",
    },
    "threats": [
        {
            "name": "Credential Sharing",
            "description": "Researchers share passwords to access lab systems.",
            "category": "Credential Abuse",
            "severity": "high",
            "affected_assets": ["Research workstation fleet"],
            "mitigations": [
                {
                    "description": "Per-session identity verification defeats shared credentials.",
                    "related_requirement_ids": ["FR-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Per-session access control for lab workstations",
            "Behavioural review alerts",
        ],
        "out_of_scope": [
            "Research application code changes",
            "Physical lab security",
        ],
    },
    "assumptions": [
        "The university central directory provides authoritative identities.",
    ],
    "testing": [
        {
            "description": "Attempt to reuse an ended session token and verify denial.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "False-positive behaviour alerts overwhelm faculty reviewers.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "Threshold tuning during pilot.",
    },
    "unresolved": [
        "Whether MFA must apply to all lab access.",
    ],
}


SCN_007: dict[str, Any] = {
    "id": "SCN-007",
    "name": "Cloud HR SaaS Platform Hardening",
    "description": (
        "A company that sells HR software wants to harden its multi-tenant SaaS "
        "platform. We need strong tenant isolation, audit logging of all admin "
        "actions, and protection for the file upload feature that customers use "
        "for payroll spreadsheets."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "SaaS vendor product team",
            "Enterprise customers",
            "Compliance officers at customer firms",
        ],
        "assets": [
            "Multi-tenant application data",
            "Payroll spreadsheet uploads",
            "Admin audit log",
            "Cloud infrastructure",
        ],
        "users": [
            "Tenant administrators",
            "End users (employees)",
            "Platform engineers",
        ],
        "constraints": [
            "Tenant data must never be visible across tenants",
            "Admin actions must be fully attributable",
            "Uploads must be scanned before processing",
        ],
        "goals": [
            "Enforce strong tenant isolation",
            "Log all administrative actions",
            "Protect the payroll upload feature",
        ],
        "missing_information": [
            "Cloud region and compliance certifications required",
            "Upload size limits",
            "Admin role hierarchy",
        ],
        "project_summary": (
            "Hardening of a multi-tenant HR SaaS platform with strong tenant "
            "isolation, full audit logging of admin actions, and protection for "
            "customer payroll spreadsheet uploads."
        ),
    },
    "clarifications": [
        {
            "question": "Which compliance certifications must the platform hold?",
            "answer": "ISO 27001 and SOC 2 Type II.",
        },
        {
            "question": "What is the maximum upload size?",
            "answer": "Ten megabytes per spreadsheet.",
        },
        {
            "question": "Is there a hierarchy of admin roles?",
            "answer": "Yes: tenant admin and platform admin.",
        },
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Tenant Isolation",
            "The system shall prevent any data access across tenant boundaries at "
            "the application and storage layers.",
            "Tenant isolation is the first hardening goal named by the vendor.",
            "GIVEN an authenticated user of tenant A, WHEN the user issues a query scoped to tenant B, "
            "THEN the system shall return no tenant B data and log the attempt.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Admin Action Audit Log",
            "The system shall record every administrative action with actor, "
            "tenant, timestamp, and before-and-after state.",
            "Attributable admin actions are an explicit requirement of the project.",
            "GIVEN a tenant or platform admin performing any action, WHEN the action completes, THEN an "
            "audit record with actor, tenant, and state change shall be persisted.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Payroll Upload Scanning",
            "The system shall scan every uploaded payroll spreadsheet for malware "
            "before making it available for processing.",
            "Protecting the file upload feature is a stated goal; scanning before "
            "processing is the protection the vendor requires.",
            "GIVEN a payroll spreadsheet upload, WHEN the upload completes, THEN the file shall be "
            "scanned and processing held until the scan result is clean.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A tenant-scoped service architecture with per-tenant data routing "
            "and a central audit pipeline."
        ),
        "components": [
            {
                "name": "Tenant Router",
                "description": "Scopes every request to a tenant context.",
                "responsibilities": ["Validate tenant scoping", "Reject cross-tenant access"],
            },
            {
                "name": "Audit Pipeline",
                "description": "Central log of admin actions.",
                "responsibilities": ["Capture admin actions", "Persist immutable records"],
            },
        ],
        "data_flows": ["Client -> tenant router -> tenant services"],
        "deployment_notes": "Multi-region cloud deployment.",
    },
    "threats": [
        {
            "name": "Cross-Tenant Data Access",
            "description": "A bug or attacker leaks tenant A data to tenant B.",
            "category": "Broken Access Control",
            "severity": "critical",
            "affected_assets": ["Multi-tenant application data"],
            "mitigations": [
                {
                    "description": "Application and storage-layer tenant isolation.",
                    "related_requirement_ids": ["SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Tenant isolation hardening",
            "Admin audit logging",
            "Payroll upload protection",
        ],
        "out_of_scope": [
            "Payroll processing itself",
            "Customer-side endpoint security",
        ],
    },
    "assumptions": [
        "Payroll uploads are processed only after clean scan results.",
    ],
    "testing": [
        {
            "description": "Attempt cross-tenant query and verify empty response.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "A malicious spreadsheet could exploit the processing engine.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Sandboxed processing and malware scanning.",
    },
    "unresolved": [
        "Whether uploads must be encrypted client-side.",
    ],
}


SCN_008: dict[str, Any] = {
    "id": "SCN-008",
    "name": "Kubernetes Container Security Platform",
    "description": (
        "A software vendor wants a security platform for the Kubernetes clusters "
        "it runs for clients. It should scan container images on push, enforce "
        "runtime policies in the clusters, and surface a dashboard of findings "
        "for each client tenant."
    ),
    "categories": ["CAT-01", "CAT-08", "CAT-03"],
    "analysis": {
        "stakeholders": [
            "Managed Kubernetes vendor",
            "Client engineering teams",
            "Vendor security operations",
        ],
        "assets": [
            "Container images and registries",
            "Kubernetes cluster fleet",
            "Runtime policy store",
            "Per-tenant findings dashboard",
        ],
        "users": [
            "Client developers",
            "Vendor platform operators",
            "Security analysts",
        ],
        "constraints": [
            "Image scanning must not block legitimate deploys without review",
            "Policies must be tenant-scoped",
            "Runtime enforcement must not break cluster availability",
        ],
        "goals": [
            "Scan container images on push",
            "Enforce runtime security policies",
            "Provide per-tenant findings dashboards",
        ],
        "missing_information": [
            "Supported registry types",
            "Policy granularity required per tenant",
            "Scan failure severity handling",
        ],
        "project_summary": (
            "A Kubernetes security platform that scans container images on push, "
            "enforces runtime policies per tenant, and provides per-tenant findings "
            "dashboards for a managed cluster vendor."
        ),
    },
    "clarifications": [
        {
            "question": "Which container registries must be supported?",
            "answer": "Our own registry and public Docker Hub pulls.",
        },
        {
            "question": "How granular must tenant policies be?",
            "answer": "Per-namespace policy is required.",
        },
        {
            "question": "How should critical scan findings be handled?",
            "answer": "Block deploy by default, allow override with approval.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Image Scanning on Push",
            "The system shall scan container images for vulnerabilities when they "
            "are pushed to the registry.",
            "Scan-on-push is the first capability named in the description.",
            "GIVEN an image pushed to the registry, WHEN the push completes, THEN a vulnerability scan "
            "shall be triggered and results stored per image digest.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Tenant-Scoped Runtime Policies",
            "The system shall enforce runtime security policies scoped to each "
            "client namespace without affecting other tenants.",
            "Tenant-scoped policy enforcement is the explicit isolation requirement "
            "for the multi-tenant platform.",
            "GIVEN a violation of a policy in a client namespace, WHEN the enforcement engine evaluates "
            "the event, THEN the violation shall be blocked or flagged only within that tenant's scope.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Critical Finding Deploy Block",
            "The system shall block image deployment by default when a critical "
            "vulnerability is found, unless an approved override exists.",
            "The clarification answer establishes block-by-default for critical "
            "findings with approval override.",
            "GIVEN a deploy attempt referencing an image with a critical finding, WHEN no approved override "
            "exists, THEN the deploy shall be blocked and the vendor notified.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "Registry webhook scanning plus in-cluster admission control with a "
            "central policy and findings service."
        ),
        "components": [
            {
                "name": "Registry Scanner",
                "description": "Scans images on push.",
                "responsibilities": ["Trigger scans", "Store results by digest"],
            },
            {
                "name": "Cluster Admission Controller",
                "description": "Enforces policies at deploy time.",
                "responsibilities": ["Evaluate policies", "Block or flag violations"],
            },
        ],
        "data_flows": ["Registry -> scanner", "Deploy -> admission controller -> cluster"],
        "deployment_notes": "Deployed in the vendor's management plane.",
    },
    "threats": [
        {
            "name": "Vulnerable Image Deployment",
            "description": "A client deploys an image with known critical vulnerabilities.",
            "category": "Supply Chain",
            "severity": "high",
            "affected_assets": ["Container images and registries"],
            "mitigations": [
                {
                    "description": "Scan-on-push with block-by-default for criticals.",
                    "related_requirement_ids": ["FR-001", "FR-002"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Image scanning",
            "Runtime policy enforcement",
            "Per-tenant dashboards",
        ],
        "out_of_scope": [
            "Cluster provisioning",
            "Network policy management",
        ],
    },
    "assumptions": [
        "Per-namespace policy is the required granularity.",
    ],
    "testing": [
        {
            "description": "Push a test image with a synthetic critical finding and verify deploy blocking.",
            "type": "security",
            "related_requirement_ids": ["FR-002"],
        }
    ],
    "risk": {
        "description": "Runtime enforcement could destabilise client workloads.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Default-deny only for high-confidence policies.",
    },
    "unresolved": [
        "Whether host-level (node) scanning is required.",
    ],
}


SCN_009: dict[str, Any] = {
    "id": "SCN-009",
    "name": "Hospital Medical Device Network Monitoring",
    "description": (
        "Our hospital wants continuous monitoring of the network segment that "
        "carries connected medical devices such as infusion pumps and patient "
        "monitors. We need to detect unexpected device communication, alert on "
        "new device behaviour, and keep records for incident review."
    ),
    "categories": ["CAT-03", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Hospital biomedical engineering",
            "Clinical IT",
            "Patient safety committee",
        ],
        "assets": [
            "Connected medical devices",
            "Medical device network segment",
            "Patient data flows",
            "Monitoring records",
        ],
        "users": [
            "Biomedical technicians",
            "Security analysts",
            "Clinical engineers",
        ],
        "constraints": [
            "Monitoring must not interfere with device operation",
            "Patient data handling must follow hospital policy",
            "Alerts must be actionable for non-security staff",
        ],
        "goals": [
            "Detect unexpected device communication",
            "Alert on new device behaviour",
            "Keep incident review records",
        ],
        "missing_information": [
            "Number and types of medical devices",
            "Existing network instrumentation",
            "Alert routing to biomedical engineering",
        ],
        "project_summary": (
            "Continuous monitoring of a hospital medical device network segment to "
            "detect unexpected device communication, alert on new behaviour, and "
            "retain incident review records."
        ),
    },
    "clarifications": [
        {
            "question": "How many medical devices are on the segment?",
            "answer": "About 900 devices across 40 device types.",
        },
        {
            "question": "Is there existing network instrumentation?",
            "answer": "Span ports are available on the segment switches.",
        },
        {
            "question": "Where should alerts go?",
            "answer": "To the biomedical engineering team first.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Unexpected Device Communication Detection",
            "The system shall detect communication between medical devices and "
            "hosts outside the expected device-to-device and device-to-server set.",
            "Detecting unexpected device communication is the primary monitoring "
            "goal in the description.",
            "GIVEN a device communication event, WHEN the destination is not in the expected set, THEN the "
            "system shall raise an alert within 60 seconds.",
            priority="must",
            numeric=[
                {"value": "60 seconds", "provenance": "ASSUMPTION_REQUIRING_CONFIRMATION"}
            ],
        ),
        req(
            "SEC-001",
            "security",
            "Non-Interference Monitoring",
            "The system shall monitor medical device traffic passively without "
            "injecting packets or altering device behaviour.",
            "The hospital requires monitoring that cannot interfere with device "
            "operation.",
            "GIVEN the monitoring system active on the segment, WHEN a full shift of clinical traffic "
            "occurs, THEN no monitoring-originated packets shall appear in the capture.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Incident Review Records",
            "The system shall retain monitoring records that allow incident review "
            "of device communication history.",
            "Keeping records for incident review is an explicit requirement in the "
            "project description.",
            "GIVEN a past incident date, WHEN a reviewer queries the device communication history, THEN "
            "the system shall return records for the requested window.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": (
            "Passive span-port monitoring feeding a medical-device-aware analytics "
            "service."
        ),
        "components": [
            {
                "name": "Span Sensor",
                "description": "Passive capture from segment span ports.",
                "responsibilities": ["Capture device traffic", "Never inject packets"],
            },
            {
                "name": "Device Behaviour Analytics",
                "description": "Models expected device communication.",
                "responsibilities": ["Model expected flows", "Detect anomalies"],
            },
        ],
        "data_flows": ["Medical device segment -> span sensor -> analytics"],
        "deployment_notes": "Sensor deployed on segment switch span ports.",
    },
    "threats": [
        {
            "name": "Compromised Device Pivoting",
            "description": "A compromised infusion pump communicates with an unexpected internal host.",
            "category": "Lateral Movement",
            "severity": "high",
            "affected_assets": ["Connected medical devices"],
            "mitigations": [
                {
                    "description": "Unexpected communication detection and alerting.",
                    "related_requirement_ids": ["FR-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Passive medical device monitoring",
            "Behaviour anomaly alerts",
        ],
        "out_of_scope": [
            "Device firmware management",
            "Wireless device security",
        ],
    },
    "assumptions": [
        "Span ports are available on segment switches.",
    ],
    "testing": [
        {
            "description": "Inject a synthetic out-of-set communication and verify the alert.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "Device behaviour baselines drift as clinical workflow changes.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Periodic baseline review with biomedical engineering.",
    },
    "unresolved": [
        "Whether patient data in captured flows must be redacted.",
    ],
}


SCN_010: dict[str, Any] = {
    "id": "SCN-010",
    "name": "Law Firm Privileged Document Access",
    "description": (
        "A law firm needs to control access to privileged documents in its "
        "matter management system. Attorneys should only see documents for "
        "matters they are assigned to, access should be granted temporarily and "
        "revocable, and every access to privileged documents must be logged."
    ),
    "categories": ["CAT-04", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Law firm partners",
            "Associates and paralegals",
            "Risk and compliance team",
        ],
        "assets": [
            "Privileged legal documents",
            "Matter management system",
            "Access control policies",
            "Access audit log",
        ],
        "users": [
            "Partners",
            "Associates",
            "Paralegals",
            "Knowledge management staff",
        ],
        "constraints": [
            "Access must be limited to assigned matters",
            "Temporary grants must expire automatically",
            "Access to privileged documents must be fully logged",
        ],
        "goals": [
            "Limit document access to assigned matters",
            "Provide temporary, revocable grants",
            "Log every privileged document access",
        ],
        "missing_information": [
            "Identity directory for attorneys",
            "Whether external counsel need access",
            "Log retention requirement",
        ],
        "project_summary": (
            "Access control for privileged documents in a law firm's matter "
            "management system with matter-scoped permissions, temporary revocable "
            "grants, and full access logging."
        ),
    },
    "clarifications": [
        {
            "question": "Which directory holds attorney identities?",
            "answer": "The firm's Active Directory.",
        },
        {
            "question": "Do external counsel need access?",
            "answer": "Yes, on a temporary basis per matter.",
        },
        {
            "question": "How long must access logs be retained?",
            "answer": "Ten years to align with the records policy.",
        },
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Matter-Scoped Document Access",
            "The system shall allow users to access documents only for matters to "
            "which they are explicitly assigned.",
            "Matter-scoped access is the explicit access-control requirement for "
            "privileged documents.",
            "GIVEN an attorney assigned only to matter A, WHEN the attorney requests a document for "
            "matter B, THEN the system shall deny access and log the attempt.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Temporary Revocable Grants",
            "The system shall support temporary document access grants that expire "
            "automatically and can be revoked at any time.",
            "Temporary and revocable grants are a stated requirement for both "
            "internal and external counsel access.",
            "GIVEN a temporary grant with an expiry time, WHEN the expiry time passes, THEN the system "
            "shall revoke the grant and log the revocation.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Privileged Access Audit Log",
            "The system shall log every access to a privileged document with user, "
            "matter, and timestamp.",
            "Full logging of privileged access is a mandatory requirement stated by "
            "the firm.",
            "GIVEN any access to a privileged document, WHEN the access is performed, THEN an audit "
            "record with user, matter, and timestamp shall be created.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "An authorization service in front of the matter management system "
            "with an immutable access log."
        ),
        "components": [
            {
                "name": "Authorization Service",
                "description": "Enforces matter-scoped access decisions.",
                "responsibilities": ["Evaluate assignments", "Enforce grants and expiries"],
            },
            {
                "name": "Access Log",
                "description": "Immutable log of privileged access events.",
                "responsibilities": ["Record accesses", "Support audit queries"],
            },
        ],
        "data_flows": ["User -> matter management -> authorization service -> documents"],
        "deployment_notes": "Deployed on-premise at the firm.",
    },
    "threats": [
        {
            "name": "Over-Privileged Document Access",
            "description": "An attorney accesses documents outside their assigned matters.",
            "category": "Broken Access Control",
            "severity": "high",
            "affected_assets": ["Privileged legal documents"],
            "mitigations": [
                {
                    "description": "Matter-scoped enforcement with full logging.",
                    "related_requirement_ids": ["SEC-001", "FR-002"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Matter-scoped access control",
            "Temporary grants",
            "Access logging",
        ],
        "out_of_scope": [
            "Document drafting tools",
            "Physical records",
        ],
    },
    "assumptions": [
        "Active Directory is the identity source.",
    ],
    "testing": [
        {
            "description": "Attempt cross-matter access and verify denial plus audit record.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "Expired external counsel access could disrupt active matters.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Renewal notifications before expiry.",
    },
    "unresolved": [
        "Whether matter-level document classification is required.",
    ],
}


SCN_011: dict[str, Any] = {
    "id": "SCN-011",
    "name": "Manufacturing OT/IT Firewall",
    "description": (
        "A manufacturer wants a firewall between its factory floor network and "
        "the corporate IT network. Only specific protocols for production data "
        "should cross, every crossing attempt should be logged, and the firewall "
        "must survive a power failure without losing its ruleset."
    ),
    "categories": ["CAT-02", "CAT-01"],
    "analysis": {
        "stakeholders": [
            "Manufacturing plant operations",
            "Corporate IT",
            "Safety and compliance",
        ],
        "assets": [
            "Factory floor network",
            "Production databases",
            "Firewall appliances",
            "Protocol gateway endpoints",
        ],
        "users": [
            "Plant engineers",
            "IT administrators",
            "Automation technicians",
        ],
        "constraints": [
            "Only production-data protocols may cross the boundary",
            "Logging must not be disabled during operations",
            "Ruleset must survive power loss",
        ],
        "goals": [
            "Filter OT/IT boundary traffic to allowed protocols",
            "Log all crossing attempts",
            "Survive power failure with ruleset intact",
        ],
        "missing_information": [
            "Production protocol list",
            "Traffic volume across the boundary",
            "High-availability requirement",
        ],
        "project_summary": (
            "A firewall between a manufacturer's factory floor and corporate IT "
            "networks that permits only specific production protocols, logs every "
            "crossing attempt, and preserves its ruleset across power failures."
        ),
    },
    "clarifications": [
        {
            "question": "Which production protocols must cross the boundary?",
            "answer": "OPC UA and MQTT only.",
        },
        {
            "question": "What traffic volume is expected?",
            "answer": "Roughly 2 Gbps of production telemetry.",
        },
        {
            "question": "Is high availability required?",
            "answer": "Yes, active/passive pair.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Protocol Allowlist Enforcement",
            "The system shall permit only the configured production protocols "
            "(OPC UA and MQTT) to cross the OT/IT boundary.",
            "Restricting the boundary to the stated production protocols is the "
            "explicit goal of the firewall project.",
            "GIVEN traffic attempting to cross the boundary, WHEN the protocol is not in the configured "
            "allowlist, THEN the traffic shall be dropped and logged.",
            priority="must",
        ),
        req(
            "NET-001",
            "network",
            "Crossing Attempt Logging",
            "The system shall log every blocked and permitted crossing attempt "
            "with source, destination, protocol, and timestamp.",
            "Logging all crossing attempts is an explicit requirement of the "
            "manufacturer.",
            "GIVEN any traffic crossing attempt, WHEN the firewall processes it, THEN a log entry with "
            "source, destination, protocol, and timestamp shall be recorded.",
            priority="must",
        ),
        req(
            "NFR-001",
            "non_functional",
            "Ruleset Survival Across Power Loss",
            "The system shall preserve its full ruleset across power failures "
            "without operator reconfiguration.",
            "Surviving power failure with the ruleset intact is a stated "
            "availability requirement.",
            "GIVEN a sudden power loss and restoration, WHEN the firewall reboots, THEN the complete "
            "ruleset shall be active without manual re-entry.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "An active/passive firewall pair at the OT/IT boundary with a "
            "persistent configuration store."
        ),
        "components": [
            {
                "name": "Boundary Firewall",
                "description": "Enforces the protocol allowlist.",
                "responsibilities": ["Filter protocols", "Log crossing attempts"],
            },
            {
                "name": "Config Store",
                "description": "Persists the ruleset across reboots.",
                "responsibilities": ["Store ruleset", "Restore on boot"],
            },
        ],
        "data_flows": ["Factory floor -> boundary firewall -> corporate IT"],
        "deployment_notes": "Active/passive pair in the plant data centre.",
    },
    "threats": [
        {
            "name": "OT/IT Boundary Breach",
            "description": "An attacker crosses from corporate IT into the factory floor.",
            "category": "Lateral Movement",
            "severity": "critical",
            "affected_assets": ["Factory floor network"],
            "mitigations": [
                {
                    "description": "Protocol allowlist with full crossing logging.",
                    "related_requirement_ids": ["FR-001", "NET-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "OT/IT boundary filtering",
            "Crossing attempt logging",
        ],
        "out_of_scope": [
            "Production process control",
            "Corporate IT endpoint protection",
        ],
    },
    "assumptions": [
        "OPC UA and MQTT are the only protocols requiring crossing.",
    ],
    "testing": [
        {
            "description": "Send non-allowlisted protocol traffic and verify it is dropped.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "A new production protocol is blocked, disrupting operations.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Change-management workflow for the allowlist.",
    },
    "unresolved": [
        "Whether the boundary must support remote plant access.",
    ],
}


SCN_012: dict[str, Any] = {
    "id": "SCN-012",
    "name": "Crypto Exchange API Rate Limiting",
    "description": (
        "A cryptocurrency exchange needs to protect its public trading API from "
        "abuse. We need per-key rate limiting, detection of burst behaviour, "
        "and automatic suspension of keys that exceed hard limits."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Exchange platform team",
            "Algorithmic trading customers",
            "Market operations",
        ],
        "assets": [
            "Public trading API",
            "API keys and credentials",
            "Order book data",
            "Rate-limit counters",
        ],
        "users": [
            "Retail traders",
            "Institutional API customers",
            "Platform engineers",
        ],
        "constraints": [
            "Rate limiting must not break legitimate high-volume trading",
            "Limits must be enforceable per API key",
            "Suspension decisions must be logged and reviewable",
        ],
        "goals": [
            "Enforce per-key rate limits",
            "Detect burst behaviour",
            "Suspend abusive keys automatically",
        ],
        "missing_information": [
            "Tier structure for API limits",
            "Burst detection window",
            "Suspension duration",
        ],
        "project_summary": (
            "API abuse protection for a cryptocurrency exchange trading API with "
            "per-key rate limiting, burst detection, and automatic suspension of "
            "abusive keys."
        ),
    },
    "clarifications": [
        {
            "question": "What API tier structure applies?",
            "answer": "Retail, pro, and institutional tiers.",
        },
        {
            "question": "What burst window should trigger detection?",
            "answer": "Ten requests within one second.",
        },
        {
            "question": "How long should a suspension last?",
            "answer": "Fifteen minutes per event.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Per-Key Rate Limiting",
            "The system shall enforce configurable rate limits for each API key "
            "based on its assigned tier.",
            "Per-key rate limiting is the first abuse-protection goal named in the "
            "description.",
            "GIVEN an API key exceeding its tier's request limit, WHEN the limit is exceeded, THEN the "
            "system shall return a rate-limit response and log the event.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Burst Behaviour Detection",
            "The system shall detect burst behaviour where a key sends ten requests "
            "within one second.",
            "The clarification answer defines the burst detection window as ten "
            "requests per second.",
            "GIVEN an API key sending ten requests within one second, WHEN the window is observed, THEN "
            "the system shall flag the key for burst behaviour.",
            priority="must",
            numeric=[
                {"value": "10 requests per second", "provenance": "USER_SPECIFIED"}
            ],
        ),
        req(
            "SEC-001",
            "security",
            "Automatic Key Suspension",
            "The system shall automatically suspend an API key that exceeds its "
            "hard limit, and lift the suspension after the configured duration.",
            "Automatic suspension of abusive keys is an explicit requirement for "
            "API abuse protection.",
            "GIVEN a suspended API key, WHEN the fifteen-minute suspension window ends, THEN the system "
            "shall restore the key to service and log the event.",
            priority="must",
            numeric=[
                {"value": "15 minutes", "provenance": "USER_SPECIFIED"}
            ],
        ),
    ],
    "architecture": {
        "overview": (
            "An API gateway fronting the trading API with a distributed "
            "rate-limiter and suspension service."
        ),
        "components": [
            {
                "name": "API Gateway",
                "description": "Front door for the trading API.",
                "responsibilities": ["Enforce per-key limits", "Detect bursts"],
            },
            {
                "name": "Suspension Service",
                "description": "Manages key suspensions.",
                "responsibilities": ["Suspend abusive keys", "Lift suspensions on schedule"],
            },
        ],
        "data_flows": ["Trader -> API gateway -> trading API"],
        "deployment_notes": "Horizontally scaled in the exchange cloud.",
    },
    "threats": [
        {
            "name": "API Abuse",
            "description": "An attacker uses stolen or excess keys to flood the trading API.",
            "category": "Denial of Service",
            "severity": "high",
            "affected_assets": ["Public trading API"],
            "mitigations": [
                {
                    "description": "Per-key limits, burst detection, and auto-suspension.",
                    "related_requirement_ids": ["FR-001", "FR-002", "SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Per-key rate limiting",
            "Burst detection",
            "Automatic suspension",
        ],
        "out_of_scope": [
            "Trading engine internals",
            "Wallet security",
        ],
    },
    "assumptions": [
        "API tiers are retail, pro, and institutional.",
    ],
    "testing": [
        {
            "description": "Drive a test key past its limit and verify the rate-limit response.",
            "type": "performance",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "Rate-limit configuration errors could block legitimate institutional trading.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Tier limit review before changes go live.",
    },
    "unresolved": [
        "Whether suspension notifications must reach customers by email.",
    ],
}


SCN_013: dict[str, Any] = {
    "id": "SCN-013",
    "name": "Telehealth Remote Access VPN",
    "description": (
        "A telehealth provider needs remote access for clinicians from home. We "
        "want a VPN that requires device posture checks, limits access to the "
        "clinical systems each clinician needs, and logs all remote sessions."
    ),
    "categories": ["CAT-06", "CAT-08"],
    "analysis": {
        "stakeholders": [
            "Telehealth provider clinical operations",
            "IT and security team",
            "Clinician staff",
        ],
        "assets": [
            "Clinical systems and patient records",
            "Remote access gateway",
            "Device posture data",
            "Remote session logs",
        ],
        "users": [
            "Physicians",
            "Nurses",
            "Administrative staff",
        ],
        "constraints": [
            "Access must be limited to required clinical systems",
            "Devices must pass posture checks before connection",
            "Remote sessions must be fully logged",
        ],
        "goals": [
            "Require device posture checks",
            "Limit access to needed clinical systems",
            "Log all remote sessions",
        ],
        "missing_information": [
            "Number of remote clinicians",
            "Device types in use",
            "Clinical system list",
        ],
        "project_summary": (
            "A remote access VPN for telehealth clinicians with device posture "
            "checks, least-privilege access to clinical systems, and full remote "
            "session logging."
        ),
    },
    "clarifications": [
        {
            "question": "How many clinicians need remote access?",
            "answer": "About 350 clinicians.",
        },
        {
            "question": "What devices are used?",
            "answer": "Company laptops and managed iPads.",
        },
        {
            "question": "Which clinical systems must be reachable?",
            "answer": "The EMR and the scheduling system.",
        },
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Device Posture Enforcement",
            "The system shall verify device posture (OS patch state and managed "
            "agent status) before establishing a remote access session.",
            "Device posture checks before connection are an explicit requirement of "
            "the telehealth provider.",
            "GIVEN a device requesting remote access, WHEN the posture check runs, THEN the connection "
            "shall be refused if the device fails patch or agent requirements.",
            priority="must",
        ),
        req(
            "NET-001",
            "network",
            "Least-Privilege Remote Access",
            "The system shall restrict each remote session to only the clinical "
            "systems the user is permitted to reach.",
            "Limiting remote access to required clinical systems is the stated "
            "access-control requirement.",
            "GIVEN an established remote session, WHEN the user attempts to reach a non-permitted "
            "system, THEN the attempt shall be blocked and logged.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Remote Session Logging",
            "The system shall log every remote session with user, device, "
            "duration, and accessed systems.",
            "Full logging of remote sessions is a stated requirement.",
            "GIVEN any remote access session, WHEN the session ends, THEN a log entry with user, device, "
            "duration, and accessed systems shall be written.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A zero-trust remote access gateway with posture verification and "
            "per-user route restrictions."
        ),
        "components": [
            {
                "name": "Access Gateway",
                "description": "Terminates remote access sessions.",
                "responsibilities": ["Enforce posture checks", "Route permitted sessions"],
            },
            {
                "name": "Session Logger",
                "description": "Records remote session activity.",
                "responsibilities": ["Log sessions", "Store accessed-system history"],
            },
        ],
        "data_flows": ["Clinician -> access gateway -> clinical systems"],
        "deployment_notes": "Deployed in the provider cloud.",
    },
    "threats": [
        {
            "name": "Compromised Home Device",
            "description": "A clinician's home device is compromised and used to reach clinical systems.",
            "category": "Credential Abuse",
            "severity": "high",
            "affected_assets": ["Clinical systems and patient records"],
            "mitigations": [
                {
                    "description": "Posture enforcement and least-privilege routing.",
                    "related_requirement_ids": ["SEC-001", "NET-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Remote access gateway",
            "Posture checks",
            "Session logging",
        ],
        "out_of_scope": [
            "Endpoint procurement",
            "EMR application changes",
        ],
    },
    "assumptions": [
        "Clinicians use company-managed laptops and iPads.",
    ],
    "testing": [
        {
            "description": "Attempt connection from a device failing posture and verify refusal.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "Posture checks block clinicians during incident response windows.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Allowlisted maintenance windows.",
    },
    "unresolved": [
        "Whether MFA is required in addition to posture.",
    ],
}


SCN_014: dict[str, Any] = {
    "id": "SCN-014",
    "name": "Election Infrastructure Event Logging",
    "description": (
        "A state election authority needs a central event logging system for "
        "its voter registration database and election management servers. All "
        "administrative changes must be logged, logs must be tamper-evident, and "
        "independent auditors need read-only access."
    ),
    "categories": ["CAT-07", "CAT-03"],
    "analysis": {
        "stakeholders": [
            "State election authority",
            "Election security office",
            "Independent auditors",
        ],
        "assets": [
            "Voter registration database",
            "Election management servers",
            "Central event log",
            "Audit access accounts",
        ],
        "users": [
            "Election administrators",
            "Security analysts",
            "Independent auditors",
        ],
        "constraints": [
            "Logs must be tamper-evident",
            "Auditors need read-only access without operational permissions",
            "Log source clocks must be synchronised",
        ],
        "goals": [
            "Log all administrative changes centrally",
            "Make logs tamper-evident",
            "Provide read-only access for auditors",
        ],
        "missing_information": [
            "Log sources and volume",
            "Auditor access frequency",
            "Retention period",
        ],
        "project_summary": (
            "A central tamper-evident event logging system for a state election "
            "authority's voter registration database and election management "
            "servers, with read-only access for independent auditors."
        ),
    },
    "clarifications": [
        {
            "question": "Which systems must send logs?",
            "answer": "The registration database and all election management servers.",
        },
        {
            "question": "How often do auditors review?",
            "answer": "After each election cycle and on request.",
        },
        {
            "question": "How long must logs be retained?",
            "answer": "Eight years per records law.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Central Administrative Change Logging",
            "The system shall collect and store administrative change events from "
            "the registration database and election management servers.",
            "Central logging of administrative changes is the core purpose stated "
            "by the election authority.",
            "GIVEN an administrative change on a connected source, WHEN the event is generated, THEN it "
            "shall be collected into the central store within one minute.",
            priority="must",
            numeric=[
                {"value": "1 minute", "provenance": "ASSUMPTION_REQUIRING_CONFIRMATION"}
            ],
        ),
        req(
            "SEC-001",
            "security",
            "Tamper-Evident Log Storage",
            "The system shall store logs so that any modification or deletion is "
            "detectable.",
            "Tamper-evidence is an explicit integrity requirement for election "
            "logging.",
            "GIVEN a modification to any stored log record, WHEN an integrity check runs, THEN the "
            "modification shall be detected and reported.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Read-Only Auditor Access",
            "The system shall provide independent auditors with read-only access "
            "to the log store with no administrative capability.",
            "Read-only auditor access is an explicit requirement of the election "
            "authority.",
            "GIVEN an auditor account, WHEN the auditor attempts an administrative action, THEN the "
            "system shall reject the action and log the attempt.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A central log service with hash-chained tamper-evident storage and "
            "scoped auditor access."
        ),
        "components": [
            {
                "name": "Log Collector",
                "description": "Ingests events from sources.",
                "responsibilities": ["Collect events", "Normalise records"],
            },
            {
                "name": "Tamper-Evident Store",
                "description": "Hash-chained log persistence.",
                "responsibilities": ["Append records", "Detect modifications"],
            },
        ],
        "data_flows": ["Sources -> log collector -> tamper-evident store"],
        "deployment_notes": "Deployed in the state data centre.",
    },
    "threats": [
        {
            "name": "Election Log Tampering",
            "description": "An insider alters or deletes election-related log entries.",
            "category": "Repudiation",
            "severity": "critical",
            "affected_assets": ["Central event log"],
            "mitigations": [
                {
                    "description": "Hash-chained tamper-evident storage with integrity checks.",
                    "related_requirement_ids": ["SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Central event logging",
            "Tamper-evident storage",
            "Auditor read-only access",
        ],
        "out_of_scope": [
            "Election system application changes",
            "Ballot security",
        ],
    },
    "assumptions": [
        "Log source clocks are synchronised via NTP.",
    ],
    "testing": [
        {
            "description": "Modify a stored record in a test environment and verify detection.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "Log volume spikes during an election overwhelm the collector.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Capacity testing before election cycles.",
    },
    "unresolved": [
        "Whether ballot-counting machines must be connected.",
    ],
}


SCN_015: dict[str, Any] = {
    "id": "SCN-015",
    "name": "Maritime Logistics Supply-Chain Integrity",
    "description": (
        "A maritime logistics company wants to verify the integrity of shipping "
        "manifests exchanged between its offices, port authorities, and customs "
        "brokers. We need signed digital documents, verification on receipt, and "
        "alerts when a document fails verification."
    ),
    "categories": ["CAT-05", "CAT-03"],
    "analysis": {
        "stakeholders": [
            "Maritime logistics company",
            "Port authorities",
            "Customs brokers",
        ],
        "assets": [
            "Shipping manifests",
            "Digital signature infrastructure",
            "Document exchange platform",
            "Verification alert records",
        ],
        "users": [
            "Operations staff",
            "Port authority users",
            "Customs broker users",
        ],
        "constraints": [
            "Documents must be verifiable without a central connection",
            "Faulty signatures must alert responsible parties",
            "Time-of-signature must be trustworthy",
        ],
        "goals": [
            "Digitally sign shipping manifests",
            "Verify documents on receipt",
            "Alert on failed verification",
        ],
        "missing_information": [
            "Document interchange format",
            "Signature certificate management",
            "Whether timestamps require a trusted authority",
        ],
        "project_summary": (
            "Digital signing and verification of shipping manifests for a maritime "
            "logistics company with alerts on verification failures."
        ),
    },
    "clarifications": [
        {
            "question": "What format will manifests be exchanged in?",
            "answer": "Signed PDFs and XML messages.",
        },
        {
            "question": "Who manages signing certificates?",
            "answer": "The company IT team manages the certificate chain.",
        },
        {
            "question": "Are third-party trusted timestamps needed?",
            "answer": "Yes, for legal evidence.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Document Signing",
            "The system shall digitally sign each shipping manifest using the "
            "organisation's certificate chain before exchange.",
            "Signing manifests is the core integrity capability requested by the "
            "company.",
            "GIVEN a shipping manifest ready for exchange, WHEN the signing operation runs, THEN a "
            "digital signature verifiable with the organisation's chain shall be attached.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Verification on Receipt",
            "The system shall verify the digital signature of every received "
            "manifest before accepting it as valid.",
            "Verification on receipt is an explicit requirement for document "
            "integrity.",
            "GIVEN a received manifest with a digital signature, WHEN the verification runs, THEN the "
            "document shall be accepted only if the signature validates.",
            priority="must",
        ),
        req(
            "FR-003",
            "functional",
            "Verification Failure Alerting",
            "The system shall alert the responsible parties when a received "
            "document fails signature verification.",
            "Alerting on verification failure is a stated requirement.",
            "GIVEN a document that fails verification, WHEN the failure is detected, THEN the system "
            "shall notify the responsible parties and record the event.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A document exchange platform with a signing service and an "
            "independent verification path."
        ),
        "components": [
            {
                "name": "Signing Service",
                "description": "Signs outgoing manifests.",
                "responsibilities": ["Apply signatures", "Manage certificate chain"],
            },
            {
                "name": "Verification Service",
                "description": "Validates incoming signatures.",
                "responsibilities": ["Verify signatures", "Raise failure alerts"],
            },
        ],
        "data_flows": ["Author -> signing service -> exchange -> verification service"],
        "deployment_notes": "Deployed in the company cloud.",
    },
    "threats": [
        {
            "name": "Manifest Forgery",
            "description": "A forged manifest is presented as genuine.",
            "category": "Spoofing",
            "severity": "high",
            "affected_assets": ["Shipping manifests"],
            "mitigations": [
                {
                    "description": "Digital signatures with verification on receipt.",
                    "related_requirement_ids": ["FR-001", "FR-002"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Manifest signing and verification",
            "Failure alerting",
        ],
        "out_of_scope": [
            "Cargo tracking",
            "Customs filing systems",
        ],
    },
    "assumptions": [
        "Signed PDF and XML are the interchange formats.",
    ],
    "testing": [
        {
            "description": "Submit a tampered manifest and verify rejection with alert.",
            "type": "security",
            "related_requirement_ids": ["FR-002", "FR-003"],
        }
    ],
    "risk": {
        "description": "Certificate expiry blocks legitimate document exchange.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Automated certificate renewal and monitoring.",
    },
    "unresolved": [
        "Whether external parties must share the same trust anchor.",
    ],
}


SCN_016: dict[str, Any] = {
    "id": "SCN-016",
    "name": "Smart Building IoT Access Control",
    "description": (
        "A commercial building operator wants to secure the IoT network that "
        "controls HVAC, lighting, and door locks. Devices should be grouped by "
        "function, only the management server should talk to them, and any "
        "device talking to an unexpected host should be cut off and reported."
    ),
    "categories": ["CAT-08", "CAT-03", "CAT-01"],
    "analysis": {
        "stakeholders": [
            "Building operator",
            "Facility management",
            "Tenant organisations",
        ],
        "assets": [
            "HVAC controllers",
            "Lighting controllers",
            "Door lock controllers",
            "IoT management server",
        ],
        "users": [
            "Facility managers",
            "IoT administrators",
            "Security operators",
        ],
        "constraints": [
            "Devices must be grouped by function",
            "Only the management server may talk to devices",
            "Unexpected communication must trigger isolation",
        ],
        "goals": [
            "Group IoT devices by function",
            "Restrict device communication to the management server",
            "Isolate and report unexpected communication",
        ],
        "missing_information": [
            "Number of buildings and devices",
            "Device vendor and protocol mix",
            "Isolation response time requirement",
        ],
        "project_summary": (
            "IoT network security for a commercial building that groups devices "
            "by function, restricts communication to a management server, and "
            "isolates devices that communicate unexpectedly."
        ),
    },
    "clarifications": [
        {
            "question": "How many devices are deployed?",
            "answer": "Roughly 2,000 devices across three buildings.",
        },
        {
            "question": "Which protocols do devices use?",
            "answer": "A mix of BACnet, Zigbee, and vendor TCP APIs.",
        },
        {
            "question": "How fast must isolation be?",
            "answer": "Within five minutes of detection.",
        },
    ],
    "requirements": [
        req(
            "NET-001",
            "network",
            "Device Grouping by Function",
            "The system shall organise IoT devices into function-based network "
            "groups with isolated communication domains.",
            "Grouping devices by function is the first requirement named by the "
            "building operator.",
            "GIVEN the device inventory, WHEN the system provisions groups, THEN each device shall "
            "belong to a function group with isolation from other groups.",
            priority="must",
        ),
        req(
            "NET-002",
            "network",
            "Management-Server-Only Communication",
            "The system shall restrict IoT device communication so that only the "
            "management server may send commands to devices.",
            "Restricting device communication to the management server is the "
            "explicit security goal.",
            "GIVEN any host other than the management server, WHEN it attempts to send a command to an "
            "IoT device, THEN the communication shall be blocked.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Unexpected Communication Isolation",
            "The system shall isolate and report any IoT device that communicates "
            "with an unexpected host within five minutes of detection.",
            "Isolation of unexpectedly-communicating devices is a stated "
            "requirement with a confirmed five-minute window.",
            "GIVEN a device communicating with an unexpected host, WHEN the communication is detected, "
            "THEN the device shall be isolated within five minutes and reported.",
            priority="must",
            numeric=[
                {"value": "5 minutes", "provenance": "USER_SPECIFIED"}
            ],
        ),
    ],
    "architecture": {
        "overview": (
            "Function-based VLAN groups with a management server and an "
            "anomaly-driven isolation service."
        ),
        "components": [
            {
                "name": "IoT VLAN Fabric",
                "description": "Function-grouped network domains.",
                "responsibilities": ["Isolate groups", "Block non-management traffic"],
            },
            {
                "name": "Isolation Service",
                "description": "Detects and isolates anomalous devices.",
                "responsibilities": ["Detect unexpected flows", "Trigger isolation"],
            },
        ],
        "data_flows": ["Management server -> IoT devices", "Devices -> vendors"],
        "deployment_notes": "Per-building deployment with central policy.",
    },
    "threats": [
        {
            "name": "Compromised IoT Device",
            "description": "A compromised door-lock controller attempts lateral movement.",
            "category": "Lateral Movement",
            "severity": "high",
            "affected_assets": ["Door lock controllers"],
            "mitigations": [
                {
                    "description": "Function grouping and automatic isolation.",
                    "related_requirement_ids": ["NET-001", "FR-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "IoT device grouping",
            "Management-only communication",
            "Anomaly isolation",
        ],
        "out_of_scope": [
            "Physical lock hardware",
            "HVAC firmware",
        ],
    },
    "assumptions": [
        "A management server is the sole legitimate device controller.",
    ],
    "testing": [
        {
            "description": "Simulate a device talking to an unexpected host and verify isolation.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "Isolation of a legitimate device disrupts building services.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Manual review queue before permanent quarantine.",
    },
    "unresolved": [
        "Whether vendor cloud access is permitted for device updates.",
    ],
}


SCN_017: dict[str, Any] = {
    "id": "SCN-017",
    "name": "Telecom Subscriber Authentication Platform",
    "description": (
        "A telecom operator wants to replace password logins to its subscriber "
        "portal with passkeys and one-time codes sent to the subscriber's "
        "registered device. The platform must revoke access instantly when a "
        "SIM swap is reported and log every authentication event."
    ),
    "categories": ["CAT-04", "CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Telecom operator",
            "Subscriber base",
            "Regulatory authority",
        ],
        "assets": [
            "Subscriber accounts",
            "Passkey and OTP infrastructure",
            "SIM swap reporting service",
            "Authentication log",
        ],
        "users": [
            "Subscribers",
            "Customer service agents",
            "Platform administrators",
        ],
        "constraints": [
            "Access must be revoked instantly on SIM swap reports",
            "Every authentication event must be logged",
            "Must support passkeys and device OTPs",
        ],
        "goals": [
            "Authenticate subscribers with passkeys and OTPs",
            "Revoke access instantly on SIM swap",
            "Log all authentication events",
        ],
        "missing_information": [
            "Subscriber count",
            "Passkey ecosystem support on devices",
            "OTP delivery channel",
        ],
        "project_summary": (
            "A telecom subscriber authentication platform using passkeys and "
            "device OTPs, with instant revocation on SIM swap reports and complete "
            "authentication logging."
        ),
    },
    "clarifications": [
        {
            "question": "How many subscribers use the portal?",
            "answer": "About 1.2 million subscribers.",
        },
        {
            "question": "Do subscriber devices support passkeys?",
            "answer": "Mostly yes; fallback to OTP is needed.",
        },
        {
            "question": "Where should OTPs be delivered?",
            "answer": "To the registered device via push or SMS.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Passkey Authentication",
            "The system shall authenticate portal logins using passkeys on "
            "supported subscriber devices.",
            "Passkey authentication is the primary mechanism requested by the "
            "operator.",
            "GIVEN a subscriber with a registered passkey, WHEN the subscriber attempts to log in, THEN "
            "the system shall complete authentication via passkey verification.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Instant SIM Swap Revocation",
            "The system shall revoke access to an account immediately when a SIM "
            "swap is reported for that subscriber.",
            "Instant revocation on SIM swap is the explicit anti-fraud requirement "
            "of the operator.",
            "GIVEN a SIM swap report for a subscriber, WHEN the report is processed, THEN all active "
            "sessions shall be revoked immediately and the change logged.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Authentication Event Logging",
            "The system shall log every authentication event with subscriber, "
            "method, result, and timestamp.",
            "Full logging of authentication events is a stated requirement for the "
            "platform.",
            "GIVEN any authentication event, WHEN the event completes, THEN a log record with subscriber, "
            "method, result, and timestamp shall be written.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "An authentication service with passkey and OTP flows plus a "
            "real-time revocation feed from SIM swap reports."
        ),
        "components": [
            {
                "name": "Authentication Service",
                "description": "Handles passkey and OTP flows.",
                "responsibilities": ["Verify passkeys", "Issue and validate OTPs"],
            },
            {
                "name": "Revocation Engine",
                "description": "Consumes SIM swap reports and revokes sessions.",
                "responsibilities": ["Process swap reports", "Revoke sessions instantly"],
            },
        ],
        "data_flows": ["Subscriber -> portal -> authentication service"],
        "deployment_notes": "Deployed in the operator's core network cloud.",
    },
    "threats": [
        {
            "name": "SIM Swap Fraud",
            "description": "An attacker hijacks a subscriber number to reset authentication.",
            "category": "Identity Spoofing",
            "severity": "critical",
            "affected_assets": ["Subscriber accounts"],
            "mitigations": [
                {
                    "description": "Instant revocation on reported SIM swaps.",
                    "related_requirement_ids": ["SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Passkey and OTP authentication",
            "SIM swap revocation",
            "Authentication logging",
        ],
        "out_of_scope": [
            "Call and data network operations",
            "Billing systems",
        ],
    },
    "assumptions": [
        "A push or SMS channel delivers OTPs to the registered device.",
    ],
    "testing": [
        {
            "description": "Simulate a SIM swap and verify active sessions are revoked.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "Passkey ecosystem gaps force heavy reliance on OTP.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Support OTP fallback while promoting passkey adoption.",
    },
    "unresolved": [
        "Whether biometric passkeys are acceptable to the regulator.",
    ],
}


SCN_018: dict[str, Any] = {
    "id": "SCN-018",
    "name": "Government Citizen Services Portal",
    "description": (
        "A government agency needs a citizen services portal where residents "
        "submit applications and upload supporting documents. We need strong "
        "identity verification for citizens, protection against form abuse, and "
        "a record of every submitted application."
    ),
    "categories": ["CAT-05", "CAT-04", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Government agency",
            "Citizens and residents",
            "Privacy regulator",
        ],
        "assets": [
            "Citizen application data",
            "Supporting documents",
            "Identity verification service",
            "Application records",
        ],
        "users": [
            "Citizens",
            "Agency case workers",
            "Portal administrators",
        ],
        "constraints": [
            "Identity verification must meet government standards",
            "Applications must not be altered after submission",
            "Form abuse must be detected",
        ],
        "goals": [
            "Verify citizen identity strongly",
            "Protect forms from abuse",
            "Record every application",
        ],
        "missing_information": [
            "Identity verification provider",
            "Application volume",
            "Document types accepted",
        ],
        "project_summary": (
            "A government citizen services portal with strong identity "
            "verification, protection against form abuse, and complete records "
            "of every submitted application."
        ),
    },
    "clarifications": [
        {
            "question": "Which identity verification service is used?",
            "answer": "The national digital identity service.",
        },
        {
            "question": "What application volume is expected?",
            "answer": "Peaks of 4,000 submissions per day.",
        },
        {
            "question": "Which documents are accepted?",
            "answer": "PDF and JPEG proof documents.",
        },
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Strong Citizen Identity Verification",
            "The system shall verify citizen identity through the national digital "
            "identity service before allowing application submission.",
            "Strong identity verification to government standards is the explicit "
            "access requirement.",
            "GIVEN a citizen starting an application, WHEN the identity verification completes, THEN the "
            "application flow shall proceed only with a successful verification.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Form Abuse Protection",
            "The system shall detect and limit automated form abuse including "
            "excessive submissions from a single source.",
            "Protection against form abuse is a stated requirement for portal "
            "integrity.",
            "GIVEN submissions exceeding the configured abuse threshold, WHEN the threshold is "
            "exceeded, THEN the system shall block further submissions and alert staff.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Immutable Application Records",
            "The system shall store submitted applications immutably and prevent "
            "alteration after submission.",
            "Immutable application records are required by the agency.",
            "GIVEN a submitted application, WHEN any change is attempted to the stored record, THEN the "
            "change shall be rejected and logged.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A portal backed by the national identity service and an immutable "
            "application store."
        ),
        "components": [
            {
                "name": "Citizen Portal",
                "description": "Application submission interface.",
                "responsibilities": ["Verify identity", "Accept applications"],
            },
            {
                "name": "Application Store",
                "description": "Immutable application persistence.",
                "responsibilities": ["Store submissions", "Reject alterations"],
            },
        ],
        "data_flows": ["Citizen -> portal -> identity service", "Portal -> application store"],
        "deployment_notes": "Hosted in the government cloud.",
    },
    "threats": [
        {
            "name": "Identity Fraud",
            "description": "An attacker submits applications using a stolen identity.",
            "category": "Identity Spoofing",
            "severity": "high",
            "affected_assets": ["Citizen application data"],
            "mitigations": [
                {
                    "description": "National identity service verification.",
                    "related_requirement_ids": ["SEC-001"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Identity verification",
            "Form abuse protection",
            "Immutable records",
        ],
        "out_of_scope": [
            "Benefit payment processing",
            "Citizen account self-service",
        ],
    },
    "assumptions": [
        "The national digital identity service is available.",
    ],
    "testing": [
        {
            "description": "Simulate excessive submissions and verify the block.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "Identity service outages block all submissions.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Queueing and graceful fallback status messaging.",
    },
    "unresolved": [
        "Whether offline document upload is needed.",
    ],
}


SCN_019: dict[str, Any] = {
    "id": "SCN-019",
    "name": "Fitness App Data Protection",
    "description": (
        "A fitness application company stores health and location data for its "
        "members. They want to encrypt health data at rest, give members control "
        "to delete their data, and stop employees from viewing member health "
        "records without a logged business reason."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Fitness app company",
            "App members",
            "Data protection authority",
        ],
        "assets": [
            "Health and fitness data",
            "Location data",
            "Member accounts",
            "Employee access log",
        ],
        "users": [
            "App members",
            "Support staff",
            "Data engineers",
        ],
        "constraints": [
            "Health data must be encrypted at rest",
            "Members must be able to delete their data",
            "Employee access requires a logged business reason",
        ],
        "goals": [
            "Encrypt health data at rest",
            "Support member data deletion",
            "Log employee data access",
        ],
        "missing_information": [
            "Member count",
            "Data retention policy",
            "Data sharing with partners",
        ],
        "project_summary": (
            "Data protection for a fitness application covering encryption of "
            "health data at rest, member-controlled deletion, and logged employee "
            "access to member records."
        ),
    },
    "clarifications": [
        {
            "question": "How many members use the app?",
            "answer": "Approximately 2.5 million members.",
        },
        {
            "question": "What is the retention policy?",
            "answer": "Health data is kept while the account is active.",
        },
        {
            "question": "Is health data shared with partners?",
            "answer": "No partner sharing currently.",
        },
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Health Data Encryption at Rest",
            "The system shall encrypt member health data at rest using strong "
            "key management.",
            "Encryption of health data at rest is an explicit requirement of the "
            "company.",
            "GIVEN stored member health data, WHEN the storage layer is inspected, THEN the data shall "
            "be found encrypted and unreadable without authorised access.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Member Data Deletion",
            "The system shall delete a member's health and location data within a "
            "configurable window after the member requests deletion.",
            "Member-controlled deletion is an explicit requirement and the "
            "clarification confirms active-account retention.",
            "GIVEN a member deletion request, WHEN the deletion job processes the account, THEN all "
            "health and location data for the member shall be removed.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Logged Employee Data Access",
            "The system shall record employee access to member health records "
            "with the stated business reason and member context.",
            "Logging employee access is required to prevent unwarranted viewing of "
            "member health records.",
            "GIVEN an employee accessing a member health record, WHEN access is granted, THEN a log "
            "with the business reason and member context shall be recorded.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A member data platform with encryption at rest, a deletion pipeline, "
            "and an access logging service."
        ),
        "components": [
            {
                "name": "Data Platform",
                "description": "Stores member health and location data.",
                "responsibilities": ["Encrypt at rest", "Serve member-controlled access"],
            },
            {
                "name": "Deletion Pipeline",
                "description": "Executes member deletion requests.",
                "responsibilities": ["Remove member data", "Confirm deletion"],
            },
        ],
        "data_flows": ["Member app -> data platform", "Employee console -> access log"],
        "deployment_notes": "Cloud-hosted with regional storage.",
    },
    "threats": [
        {
            "name": "Insider Health Data Viewing",
            "description": "An employee views member health records without authorisation.",
            "category": "Privacy Breach",
            "severity": "high",
            "affected_assets": ["Health and fitness data"],
            "mitigations": [
                {
                    "description": "Mandatory business reason with full access logging.",
                    "related_requirement_ids": ["FR-002"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Encryption at rest",
            "Member deletion",
            "Employee access logging",
        ],
        "out_of_scope": [
            "Wearable device security",
            "Third-party analytics",
        ],
    },
    "assumptions": [
        "No partner sharing of health data.",
    ],
    "testing": [
        {
            "description": "Verify stored member data is encrypted at rest.",
            "type": "security",
            "related_requirement_ids": ["SEC-001"],
        }
    ],
    "risk": {
        "description": "Deletion requests from a large member base strain the pipeline.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Queued processing with completion reporting.",
    },
    "unresolved": [
        "Whether deletion must extend to backups.",
    ],
}


SCN_020: dict[str, Any] = {
    "id": "SCN-020",
    "name": "Streaming Platform Content Integrity",
    "description": (
        "A video streaming platform wants to stop leaks of unreleased content. "
        "We need to watermark preview streams, detect re-uploads of leaked "
        "clips, and track which internal account opened a preview stream."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": [
            "Streaming platform content team",
            "Legal team",
            "Content production partners",
        ],
        "assets": [
            "Unreleased video content",
            "Preview stream infrastructure",
            "Watermarking engine",
            "Leak detection service",
        ],
        "users": [
            "Content reviewers",
            "Marketing staff",
            "Security analysts",
        ],
        "constraints": [
            "Preview streams must be traceable per viewer",
            "Re-uploads must be detected promptly",
            "Access tracking must not break reviewer workflows",
        ],
        "goals": [
            "Watermark preview streams",
            "Detect re-uploads of leaked clips",
            "Track internal preview access",
        ],
        "missing_information": [
            "Preview audience size",
            "Watermark visibility requirements",
            "Detection turnaround time",
        ],
        "project_summary": (
            "Content integrity protection for a video streaming platform with "
            "per-viewer watermarking of preview streams, leak re-upload detection, "
            "and internal access tracking."
        ),
    },
    "clarifications": [
        {
            "question": "How large is the preview audience?",
            "answer": "About 400 internal reviewers and partners.",
        },
        {
            "question": "How visible may watermarks be?",
            "answer": "Subtle, per-viewer unique marks.",
        },
        {
            "question": "How fast must leaks be detected?",
            "answer": "Within 24 hours of re-upload.",
        },
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Per-Viewer Preview Watermarking",
            "The system shall apply a unique, subtle watermark to each preview "
            "stream that identifies the viewing account.",
            "Per-viewer watermarking is the core traceability requirement of the "
            "content team.",
            "GIVEN a preview stream request from an internal account, WHEN the stream is served, THEN a "
            "unique watermark identifying that account shall be embedded.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Leaked Clip Detection",
            "The system shall detect re-uploads of watermarked leaked clips "
            "within 24 hours of publication.",
            "Leak detection within 24 hours is a stated requirement with a "
            "confirmed window.",
            "GIVEN a re-uploaded clip published online, WHEN the detection service scans, THEN the "
            "system shall identify the watermark and report the source account within 24 hours.",
            priority="must",
            numeric=[
                {"value": "24 hours", "provenance": "USER_SPECIFIED"}
            ],
        ),
        req(
            "FR-003",
            "functional",
            "Preview Access Tracking",
            "The system shall record which internal account opened each preview "
            "stream and when.",
            "Tracking preview access is required to attribute any leak to a source "
            "account.",
            "GIVEN an internal account opening a preview stream, WHEN the stream opens, THEN an access "
            "record with account and timestamp shall be created.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": (
            "A watermarking pipeline for preview streams plus an online leak "
            "detection service."
        ),
        "components": [
            {
                "name": "Watermarking Pipeline",
                "description": "Embeds per-viewer watermarks.",
                "responsibilities": ["Encode watermarks", "Track viewer identity"],
            },
            {
                "name": "Leak Detection",
                "description": "Scans for re-uploads.",
                "responsibilities": ["Detect watermarks", "Report source accounts"],
            },
        ],
        "data_flows": ["Reviewer -> preview stream -> watermarking pipeline"],
        "deployment_notes": "Streaming infrastructure in the platform cloud.",
    },
    "threats": [
        {
            "name": "Content Leak",
            "description": "An internal reviewer leaks an unreleased title.",
            "category": "Data Loss",
            "severity": "high",
            "affected_assets": ["Unreleased video content"],
            "mitigations": [
                {
                    "description": "Per-viewer watermarking and leak detection.",
                    "related_requirement_ids": ["FR-001", "FR-002"],
                }
            ],
        }
    ],
    "scope": {
        "in_scope": [
            "Preview watermarking",
            "Leak detection",
            "Access tracking",
        ],
        "out_of_scope": [
            "Cinema distribution security",
            "Set security",
        ],
    },
    "assumptions": [
        "Reviewers access previews through the internal platform only.",
    ],
    "testing": [
        {
            "description": "Extract the watermark from a test clip and verify account attribution.",
            "type": "security",
            "related_requirement_ids": ["FR-001"],
        }
    ],
    "risk": {
        "description": "Visible watermarks annoy reviewers and partners.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "Subtle watermark design review.",
    },
    "unresolved": [
        "Whether partner screenshots are in scope for detection.",
    ],
}


SCENARIOS_A: list[dict[str, Any]] = [SCN_001, SCN_002, SCN_003, SCN_004, SCN_005, SCN_006, SCN_007, SCN_008, SCN_009, SCN_010, SCN_011, SCN_012, SCN_013, SCN_014, SCN_015, SCN_016, SCN_017, SCN_018, SCN_019, SCN_020]
