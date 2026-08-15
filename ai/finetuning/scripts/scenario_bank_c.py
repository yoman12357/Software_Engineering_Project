"""Scenario bank C (SCN-041..SCN-060) for the CyberSRS QLoRA training dataset.

Hand-authored, genuinely distinct synthetic cybersecurity project scenarios.
See scenario_bank_a.py for schema conventions.
"""

from __future__ import annotations

from typing import Any

from .scenario_bank_a import req


SCN_041: dict[str, Any] = {
    "id": "SCN-041",
    "name": "Nuclear Research Facility Access Control",
    "description": (
        "A nuclear research facility needs tighter access control to its "
        "sensitive computing cluster. They want two-person rule enforcement for "
        "administrator actions, multi-factor authentication for all access, and "
        "an alarm when concurrent access violates the two-person rule."
    ),
    "categories": ["CAT-04", "CAT-07"],
    "analysis": {
        "stakeholders": ["Nuclear research facility", "Researchers", "Safety regulator"],
        "assets": [
            "Sensitive computing cluster",
            "Administrator accounts",
            "Access control system",
            "Two-person rule records",
        ],
        "users": ["Researchers", "System administrators", "Safety officers"],
        "constraints": [
            "Administrator actions must follow the two-person rule",
            "All access requires multi-factor authentication",
            "Violations must alarm immediately",
        ],
        "goals": [
            "Enforce the two-person rule for admin actions",
            "Require multi-factor authentication",
            "Alarm on two-person rule violations",
        ],
        "missing_information": [
            "Cluster size",
            "Administrator count",
            "Alarm escalation path",
        ],
        "project_summary": (
            "Access control for a nuclear research computing cluster with "
            "two-person rule enforcement, multi-factor authentication, and "
            "violation alarms."
        ),
    },
    "clarifications": [
        {"question": "How large is the computing cluster?", "answer": "About 1,200 compute nodes."},
        {"question": "How many administrators are there?", "answer": "Six senior administrators."},
        {"question": "Who receives violation alarms?", "answer": "The safety officer on duty."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Two-Person Rule Enforcement",
            "The system shall require two distinct authorised persons to approve "
            "each administrator action.",
            "The two-person rule is the explicit regulatory requirement for sensitive actions.",
            "GIVEN an administrator action, WHEN the action is submitted, THEN it shall require "
            "approval by a second distinct authorised person before execution.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Multi-Factor Access",
            "The system shall require multi-factor authentication for all access "
            "to the computing cluster.",
            "Multi-factor authentication for all access is a stated requirement.",
            "GIVEN a user requesting cluster access, WHEN authentication occurs, THEN a second factor "
            "shall be required in addition to the primary credential.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Violation Alarm",
            "The system shall raise an alarm immediately when concurrent access "
            "violates the two-person rule.",
            "Alarming on violations is required to react to rule breaches in real time.",
            "GIVEN a two-person rule violation, WHEN the violation is detected, THEN an immediate "
            "alarm shall be raised to the duty safety officer.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "An access-control gateway with two-person approval and real-time alarms.",
        "components": [
            {"name": "Access Gateway", "description": "Enforces access policy.", "responsibilities": ["Enforce MFA", "Track approvals"]},
            {"name": "Alarm Engine", "description": "Detects rule violations.", "responsibilities": ["Detect violations", "Notify safety officer"]},
        ],
        "data_flows": ["User -> access gateway -> compute cluster"],
        "deployment_notes": "On-premise facility network.",
    },
    "threats": [
        {
            "name": "Sole-Actor Administrator Action",
            "description": "A single compromised admin performs a sensitive action.",
            "category": "Insider Threat",
            "severity": "critical",
            "affected_assets": ["Sensitive computing cluster"],
            "mitigations": [{"description": "Two-person rule with real-time alarms.", "related_requirement_ids": ["SEC-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Two-person rule", "MFA", "Violation alarms"],
        "out_of_scope": ["Physical reactor control", "Material tracking"],
    },
    "assumptions": ["The safety regulator requires the two-person rule."],
    "testing": [
        {"description": "Simulate a same-person double approval and verify the alarm.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Two-person rule slows urgent maintenance.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Pre-approved emergency procedures.",
    },
    "unresolved": ["Whether batch operations need per-item approval."],
}


SCN_042: dict[str, Any] = {
    "id": "SCN-042",
    "name": "Aviation MRO System Security",
    "description": (
        "An aviation maintenance, repair, and overhaul company wants to secure "
        "the system technicians use to record maintenance work. They need "
        "individual technician accountability, protected records against "
        "alteration, and alerts when work records are changed after sign-off."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Aviation MRO company", "Technicians", "Aviation regulator"],
        "assets": [
            "Maintenance records",
            "Technician accounts",
            "Work sign-off process",
            "Record integrity checks",
        ],
        "users": ["Technicians", "Supervisors", "Quality assurance"],
        "constraints": [
            "Every record entry must be attributable to a technician",
            "Records must resist alteration",
            "Post-sign-off changes must alert",
        ],
        "goals": [
            "Attribute records to individual technicians",
            "Protect records from alteration",
            "Alert on post-sign-off changes",
        ],
        "missing_information": [
            "Technician count",
            "System integration points",
            "Regulator reporting",
        ],
        "project_summary": (
            "Security for an aviation maintenance record system with technician "
            "accountability, tamper protection, and post-sign-off change alerts."
        ),
    },
    "clarifications": [
        {"question": "How many technicians use the system?", "answer": "About 300 technicians."},
        {"question": "Which systems must integrate?", "answer": "The scheduling and parts systems."},
        {"question": "Is regulator reporting required?", "answer": "Yes, on request."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Technician Attribution",
            "The system shall attribute every maintenance record entry to the "
            "authenticated technician who made it.",
            "Individual accountability is the core requirement for maintenance records.",
            "GIVEN a maintenance record entry, WHEN the entry is saved, THEN it shall be bound to the "
            "authenticated technician identity.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Record Alteration Protection",
            "The system shall prevent unauthorised alteration of signed "
            "maintenance records.",
            "Protecting records against alteration is required for record integrity.",
            "GIVEN a signed maintenance record, WHEN an unauthorised alteration is attempted, THEN the "
            "attempt shall be rejected and logged.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Post-Sign-Off Change Alert",
            "The system shall alert quality assurance when a signed record is "
            "changed after sign-off.",
            "Alerting on post-sign-off changes supports auditability.",
            "GIVEN a change to a signed record, WHEN the change is saved, THEN quality assurance shall "
            "receive an alert.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "An MRO record system with signed records and integrity alerting.",
        "components": [
            {"name": "Record Service", "description": "Stores maintenance records.", "responsibilities": ["Bind entries to technicians", "Protect signed records"]},
            {"name": "Integrity Monitor", "description": "Detects post-sign-off changes.", "responsibilities": ["Detect changes", "Alert quality assurance"]},
        ],
        "data_flows": ["Technician -> record service -> integrity monitor"],
        "deployment_notes": "Deployed in the MRO facility.",
    },
    "threats": [
        {
            "name": "Maintenance Record Fraud",
            "description": "A technician alters a record to hide faulty work.",
            "category": "Repudiation",
            "severity": "high",
            "affected_assets": ["Maintenance records"],
            "mitigations": [{"description": "Technician attribution and alteration protection.", "related_requirement_ids": ["SEC-001", "SEC-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Attribution", "Alteration protection", "Change alerts"],
        "out_of_scope": ["Aircraft systems", "Parts inventory"],
    },
    "assumptions": ["Technicians authenticate individually."],
    "testing": [
        {"description": "Attempt to alter a signed record and verify the block and alert.", "type": "security", "related_requirement_ids": ["SEC-002", "FR-001"]}
    ],
    "risk": {
        "description": "Integrity checks slow down routine record corrections.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Authorised correction workflow with audit trail.",
    },
    "unresolved": ["Whether regulator API reporting is required."],
}


SCN_043: dict[str, Any] = {
    "id": "SCN-043",
    "name": "EV Charging Network Security",
    "description": (
        "An electric vehicle charging network operator wants to secure its "
        "charging stations. They need authentication of charging sessions, "
        "encrypted communication with the management cloud, and detection of "
        "tampered charging hardware."
    ),
    "categories": ["CAT-01", "CAT-06", "CAT-03"],
    "analysis": {
        "stakeholders": ["EV charging operator", "Drivers", "Utility partner"],
        "assets": [
            "Charging stations",
            "Charging session data",
            "Management cloud",
            "Station telemetry",
        ],
        "users": ["Drivers", "Station technicians", "Network operators"],
        "constraints": [
            "Charging sessions must be authenticated",
            "Station-to-cloud traffic must be encrypted",
            "Tampered hardware must be detected",
        ],
        "goals": [
            "Authenticate charging sessions",
            "Encrypt station-cloud communication",
            "Detect tampered hardware",
        ],
        "missing_information": [
            "Station count",
            "Charging protocol",
            "Tamper detection method",
        ],
        "project_summary": (
            "Security for an EV charging network with session authentication, "
            "encrypted cloud communication, and tampered-hardware detection."
        ),
    },
    "clarifications": [
        {"question": "How many charging stations are deployed?", "answer": "About 800 stations."},
        {"question": "Which charging protocol is used?", "answer": "OCPP over TLS."},
        {"question": "How should tampering be detected?", "answer": "Via enclosure sensors and anomalous telemetry."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Charging Session Authentication",
            "The system shall authenticate every charging session before energy "
            "delivery begins.",
            "Authenticating sessions prevents unauthorised energy use and session spoofing.",
            "GIVEN a driver starting a charging session, WHEN the session is initiated, THEN energy "
            "delivery shall begin only after authentication succeeds.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Encrypted Cloud Communication",
            "The system shall encrypt all communication between stations and the "
            "management cloud.",
            "Encrypted station-cloud traffic is the stated communication requirement.",
            "GIVEN station-to-cloud communication, WHEN it transits the network, THEN it shall be "
            "encrypted.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Tampered Hardware Detection",
            "The system shall detect tampered charging hardware via enclosure "
            "sensors and telemetry anomalies.",
            "Detecting tampered hardware is the stated physical-integrity requirement.",
            "GIVEN a tamper indicator on a charging station, WHEN the indicator is detected, THEN the "
            "station shall be flagged and taken out of service.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "OCPP stations with authenticated sessions and cloud telemetry.",
        "components": [
            {"name": "Station Agent", "description": "Runs at each charging station.", "responsibilities": ["Authenticate sessions", "Report telemetry"]},
            {"name": "Cloud Management", "description": "Monitors the network.", "responsibilities": ["Track sessions", "Detect tampering"]},
        ],
        "data_flows": ["Driver -> station -> management cloud"],
        "deployment_notes": "Stations across a regional grid.",
    },
    "threats": [
        {
            "name": "Session Spoofing",
            "description": "An attacker forges a charging session.",
            "category": "Spoofing",
            "severity": "high",
            "affected_assets": ["Charging session data"],
            "mitigations": [{"description": "Session authentication before energy delivery.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Session authentication", "Encrypted comms", "Tamper detection"],
        "out_of_scope": ["Vehicle-side systems", "Grid balancing"],
    },
    "assumptions": ["OCPP over TLS is the standard protocol."],
    "testing": [
        {"description": "Attempt an unauthenticated session and verify energy delivery is blocked.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Station connectivity loss disrupts the charging network.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Local fallback modes and alerting.",
    },
    "unresolved": ["Whether driver apps require additional authentication."],
}


SCN_044: dict[str, Any] = {
    "id": "SCN-044",
    "name": "Water Desalination Plant Control Security",
    "description": (
        "A water desalination plant wants to secure the control system for its "
        "treatment process. Operators must use two-factor access, control "
        "changes must be logged with approvals, and the plant must continue "
        "running safely if the control network is disrupted."
    ),
    "categories": ["CAT-04", "CAT-07", "CAT-01"],
    "analysis": {
        "stakeholders": ["Desalination plant", "Plant operators", "Municipal water authority"],
        "assets": [
            "Control system",
            "Treatment process equipment",
            "Operator accounts",
            "Control change logs",
        ],
        "users": ["Plant operators", "Maintenance engineers", "Control administrators"],
        "constraints": [
            "Operators must use two-factor access",
            "Control changes require logged approval",
            "Safe operation must continue on network disruption",
        ],
        "goals": [
            "Require two-factor operator access",
            "Log approved control changes",
            "Continue safe operation under disruption",
        ],
        "missing_information": [
            "Operator count",
            "Change approval workflow",
            "Fallback control mode",
        ],
        "project_summary": (
            "Control system security for a water desalination plant with "
            "two-factor operator access, approved and logged control changes, and "
            "safe continued operation under disruption."
        ),
    },
    "clarifications": [
        {"question": "How many operators use the system?", "answer": "About 40 operators."},
        {"question": "How are control changes approved?", "answer": "By a shift supervisor."},
        {"question": "What fallback mode exists?", "answer": "A safe-mode local controller."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Two-Factor Operator Access",
            "The system shall require two-factor authentication for operator "
            "access to the control system.",
            "Two-factor access is the first access-control requirement for the plant.",
            "GIVEN an operator requesting control access, WHEN authentication occurs, THEN a second "
            "factor shall be required.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Approved Control Changes",
            "The system shall require supervisor approval for control changes "
            "and log the full change trail.",
            "Approved and logged control changes are required for operational accountability.",
            "GIVEN a control change, WHEN it is submitted, THEN it shall be applied only after "
            "supervisor approval and the change shall be logged.",
            priority="must",
        ),
        req(
            "NFR-001",
            "non_functional",
            "Safe Operation on Disruption",
            "The system shall maintain safe operation of the treatment process "
            "when the control network is disrupted.",
            "Continued safe operation under disruption is a stated operational requirement.",
            "GIVEN a control network disruption, WHEN the disruption is detected, THEN the plant shall "
            "transition to safe mode without unsafe process changes.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A control system with two-factor access, approved changes, and safe mode.",
        "components": [
            {"name": "Control Workstation", "description": "Operator interface.", "responsibilities": ["Enforce two-factor access", "Capture changes"]},
            {"name": "Safe-Mode Controller", "description": "Maintains safe operation.", "responsibilities": ["Fallback control", "Hold safe state"]},
        ],
        "data_flows": ["Operator -> control workstation -> process equipment"],
        "deployment_notes": "Plant control room with redundant links.",
    },
    "threats": [
        {
            "name": "Unapproved Control Change",
            "description": "An operator makes an unsafe control change without approval.",
            "category": "Sabotage",
            "severity": "critical",
            "affected_assets": ["Treatment process equipment"],
            "mitigations": [{"description": "Supervisor approval and change logging.", "related_requirement_ids": ["FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Two-factor access", "Approved changes", "Safe mode"],
        "out_of_scope": ["Water quality chemistry", "Pump hardware"],
    },
    "assumptions": ["A shift supervisor approves control changes."],
    "testing": [
        {"description": "Submit a control change without approval and verify it is held.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Safe-mode transitions could disrupt water output.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Regular safe-mode drills.",
    },
    "unresolved": ["Whether remote operator access is allowed."],
}


SCN_045: dict[str, Any] = {
    "id": "SCN-045",
    "name": "City Emergency Services Radio Security",
    "description": (
        "A city's emergency services use a digital radio network for dispatch. "
        "They need to protect radio identities from spoofing, encrypt dispatch "
        "traffic, and detect radios that have been cloned."
    ),
    "categories": ["CAT-01", "CAT-03"],
    "analysis": {
        "stakeholders": ["City emergency services", "Dispatch centre", "Public safety agency"],
        "assets": [
            "Digital radio network",
            "Radio identities",
            "Dispatch traffic",
            "Radio registration records",
        ],
        "users": ["First responders", "Dispatch operators", "Radio administrators"],
        "constraints": [
            "Radio identities must resist spoofing",
            "Dispatch traffic must be encrypted",
            "Cloned radios must be detected",
        ],
        "goals": [
            "Protect radio identities from spoofing",
            "Encrypt dispatch traffic",
            "Detect cloned radios",
        ],
        "missing_information": [
            "Radio count",
            "Radio protocol",
            "Key management approach",
        ],
        "project_summary": (
            "Security for a city emergency services radio network with spoofing "
            "protection, encrypted dispatch traffic, and clone detection."
        ),
    },
    "clarifications": [
        {"question": "How many radios are deployed?", "answer": "About 5,000 radios."},
        {"question": "Which protocol is used?", "answer": "A P25 digital trunking system."},
        {"question": "How are keys managed?", "answer": "Over-the-air rekeying."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Radio Identity Protection",
            "The system shall validate radio identities against a trusted "
            "registration before granting network access.",
            "Validating identities protects against radio spoofing.",
            "GIVEN a radio requesting network access, WHEN the registration is validated, THEN access "
            "shall be granted only for registered identities.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Dispatch Traffic Encryption",
            "The system shall encrypt dispatch traffic end to end.",
            "Encrypting dispatch traffic protects sensitive operations.",
            "GIVEN dispatch traffic, WHEN it transits the radio network, THEN it shall be encrypted.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Cloned Radio Detection",
            "The system shall detect radios that transmit with a duplicate "
            "identity.",
            "Detecting cloned radios prevents identity reuse by attackers.",
            "GIVEN two radios transmitting with the same identity, WHEN the duplication is observed, "
            "THEN both units shall be flagged.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A validated radio network with encrypted dispatch and registration monitoring.",
        "components": [
            {"name": "Radio Registrar", "description": "Validates radio identities.", "responsibilities": ["Validate registration", "Reject spoofs"]},
            {"name": "Identity Monitor", "description": "Detects cloned identities.", "responsibilities": ["Detect duplicates", "Flag radios"]},
        ],
        "data_flows": ["Radio -> radio network -> dispatch centre"],
        "deployment_notes": "City-wide trunking infrastructure.",
    },
    "threats": [
        {
            "name": "Radio Spoofing",
            "description": "An attacker impersonates a responder radio.",
            "category": "Spoofing",
            "severity": "critical",
            "affected_assets": ["Radio identities"],
            "mitigations": [{"description": "Registration validation and clone detection.", "related_requirement_ids": ["SEC-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Identity validation", "Traffic encryption", "Clone detection"],
        "out_of_scope": ["Dispatch software", "Vehicle hardware"],
    },
    "assumptions": ["Over-the-air rekeying manages encryption keys."],
    "testing": [
        {"description": "Duplicate a radio identity and verify both units are flagged.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Rekeying failures could take radios offline.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Phased rekeying and fallback keys.",
    },
    "unresolved": ["Whether dispatch recording requires separate protection."],
}


SCN_046: dict[str, Any] = {
    "id": "SCN-046",
    "name": "Legal eDiscovery Platform Access Control",
    "description": (
        "A legal eDiscovery provider handles sensitive documents for lawsuits. "
        "They want per-matter access controls, logging of document reviews, and "
        "the ability to quarantine a document set instantly if a breach is "
        "suspected."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["eDiscovery provider", "Law firms", "Case clients"],
        "assets": [
            "Case documents",
            "Matter workspaces",
            "Review logs",
            "Quarantine controls",
        ],
        "users": ["Review attorneys", "Case managers", "Platform admins"],
        "constraints": [
            "Access must be per-matter",
            "Document reviews must be logged",
            "Quarantine must be instant",
        ],
        "goals": [
            "Enforce per-matter access",
            "Log document reviews",
            "Enable instant quarantine",
        ],
        "missing_information": [
            "Case volume",
            "Reviewer count",
            "Quarantine workflow",
        ],
        "project_summary": (
            "Access control for a legal eDiscovery platform with per-matter "
            "controls, review logging, and instant document quarantine."
        ),
    },
    "clarifications": [
        {"question": "How many active cases are handled?", "answer": "About 45 active matters."},
        {"question": "How many reviewers use the platform?", "answer": "Roughly 200 reviewers."},
        {"question": "How should quarantine work?", "answer": "One-click set isolation with notice."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Per-Matter Access Control",
            "The system shall restrict document access to users assigned to the "
            "relevant matter.",
            "Per-matter access is the core confidentiality requirement.",
            "GIVEN a user requesting documents, WHEN the request is evaluated, THEN access shall be "
            "granted only for matters the user is assigned to.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Document Review Logging",
            "The system shall log every document review with user, matter, and "
            "timestamp.",
            "Review logging is required for litigation accountability.",
            "GIVEN a document review, WHEN the document is opened, THEN a log with user, matter, and "
            "timestamp shall be recorded.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Instant Document Quarantine",
            "The system shall quarantine a document set instantly on demand, "
            "removing it from normal access.",
            "Instant quarantine supports rapid response to suspected breaches.",
            "GIVEN a quarantine request for a document set, WHEN the request is issued, THEN the set "
            "shall be removed from normal access immediately.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A matter-scoped document platform with review logging and quarantine.",
        "components": [
            {"name": "Matter Workspace", "description": "Scoped document area.", "responsibilities": ["Enforce matter access", "Log reviews"]},
            {"name": "Quarantine Service", "description": "Isolates document sets.", "responsibilities": ["Isolate sets", "Restore on approval"]},
        ],
        "data_flows": ["Reviewer -> matter workspace -> documents"],
        "deployment_notes": "Cloud-hosted with regional data residency.",
    },
    "threats": [
        {
            "name": "Cross-Matter Document Exposure",
            "description": "A reviewer accesses documents from an unrelated case.",
            "category": "Broken Access Control",
            "severity": "high",
            "affected_assets": ["Case documents"],
            "mitigations": [{"description": "Per-matter access enforcement.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Per-matter access", "Review logging", "Quarantine"],
        "out_of_scope": ["Document production formats", "Court filing"],
    },
    "assumptions": ["Reviewers are assigned to matters explicitly."],
    "testing": [
        {"description": "Attempt access to an unassigned matter and verify denial.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Accidental quarantine blocks legitimate review work.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Confirm dialog and swift restore path.",
    },
    "unresolved": ["Whether reviewer MFA is required."],
}


SCN_047: dict[str, Any] = {
    "id": "SCN-047",
    "name": "Gaming Studio Code Integrity",
    "description": (
        "A game studio wants to protect its proprietary game code. They need "
        "signed code commits, restricted access to the source repository, and "
        "detection of suspicious changes to build pipelines."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Game studio", "Game developers", "Publishing partner"],
        "assets": [
            "Source code repository",
            "Build pipelines",
            "Developer accounts",
            "Commit signatures",
        ],
        "users": ["Developers", "Build engineers", "Release managers"],
        "constraints": [
            "Commits must be signed",
            "Repository access must be restricted",
            "Build pipeline changes must be monitored",
        ],
        "goals": [
            "Require signed code commits",
            "Restrict repository access",
            "Detect suspicious build changes",
        ],
        "missing_information": [
            "Developer count",
            "Repository structure",
            "Pipeline tooling",
        ],
        "project_summary": (
            "Code integrity protection for a game studio with signed commits, "
            "restricted repository access, and build pipeline monitoring."
        ),
    },
    "clarifications": [
        {"question": "How many developers work on the codebase?", "answer": "About 120 developers."},
        {"question": "How is the repository structured?", "answer": "A monorepo with per-project permissions."},
        {"question": "Which build tooling is used?", "answer": "A cloud CI/CD service."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Signed Code Commits",
            "The system shall require every code commit to be signed by an "
            "approved developer identity.",
            "Signed commits are the primary code-integrity mechanism requested.",
            "GIVEN a code commit, WHEN it is pushed, THEN it shall be accepted only with a valid "
            "developer signature.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Restricted Repository Access",
            "The system shall restrict source repository access according to "
            "per-project permissions.",
            "Restricting repository access protects proprietary code.",
            "GIVEN a developer requesting repository access, WHEN the request is evaluated, THEN access "
            "shall be granted only for permitted projects.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Build Pipeline Change Monitoring",
            "The system shall flag suspicious changes to build pipeline "
            "configuration for review.",
            "Monitoring build changes protects the supply chain.",
            "GIVEN a change to build pipeline configuration, WHEN the change is detected, THEN it "
            "shall be flagged for review.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A signed-commit repository with permissioned access and pipeline monitoring.",
        "components": [
            {"name": "Repository Service", "description": "Hosts the source code.", "responsibilities": ["Enforce signatures", "Enforce permissions"]},
            {"name": "Pipeline Monitor", "description": "Tracks build changes.", "responsibilities": ["Detect changes", "Flag suspicious edits"]},
        ],
        "data_flows": ["Developer -> repository service -> build pipelines"],
        "deployment_notes": "Cloud-hosted development platform.",
    },
    "threats": [
        {
            "name": "Supply-Chain Compromise",
            "description": "An attacker injects malicious code into the build pipeline.",
            "category": "Supply Chain",
            "severity": "high",
            "affected_assets": ["Build pipelines"],
            "mitigations": [{"description": "Signed commits and pipeline change monitoring.", "related_requirement_ids": ["SEC-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Signed commits", "Repository access", "Pipeline monitoring"],
        "out_of_scope": ["Game client code", "Live game services"],
    },
    "assumptions": ["All developers hold signing keys."],
    "testing": [
        {"description": "Push an unsigned commit and verify it is rejected.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Signature enforcement blocks urgent hotfixes.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Emergency-key workflow for hotfixes.",
    },
    "unresolved": ["Whether build artifacts must be signed too."],
}


SCN_048: dict[str, Any] = {
    "id": "SCN-048",
    "name": "Biometric Time-and-Attendance System",
    "description": (
        "A manufacturing firm uses biometric attendance for its workforce. They "
        "need to protect stored biometric templates, ensure clock-in records "
        "cannot be forged, and log all administrative changes to the system."
    ),
    "categories": ["CAT-04", "CAT-07"],
    "analysis": {
        "stakeholders": ["Manufacturing firm", "Workforce", "Labour compliance"],
        "assets": [
            "Biometric templates",
            "Attendance records",
            "Biometric devices",
            "Admin change log",
        ],
        "users": ["Employees", "HR administrators", "Payroll staff"],
        "constraints": [
            "Biometric templates must be protected",
            "Clock-in records must resist forgery",
            "Admin changes must be logged",
        ],
        "goals": [
            "Protect stored biometric templates",
            "Prevent forged attendance records",
            "Log administrative changes",
        ],
        "missing_information": [
            "Workforce size",
            "Biometric modality",
            "Integration with payroll",
        ],
        "project_summary": (
            "Security for a biometric time-and-attendance system with template "
            "protection, forgery-resistant records, and admin change logging."
        ),
    },
    "clarifications": [
        {"question": "How large is the workforce?", "answer": "About 2,000 employees."},
        {"question": "Which biometric modality is used?", "answer": "Fingerprint and face recognition."},
        {"question": "Does payroll integrate?", "answer": "Yes, via a scheduled export."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Biometric Template Protection",
            "The system shall store biometric templates in a protected form that "
            "cannot be reversed to raw biometric data.",
            "Protecting biometric templates is the core privacy requirement.",
            "GIVEN a stored biometric template, WHEN the storage is inspected, THEN the template shall "
            "be found in a non-reversible protected form.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Forgery-Resistant Attendance",
            "The system shall bind each attendance record to the live biometric "
            "verification event.",
            "Binding records to live verification prevents forged clock-ins.",
            "GIVEN an attendance record, WHEN it is written, THEN it shall reference the biometric "
            "verification event that produced it.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Admin Change Logging",
            "The system shall log all administrative changes with actor and "
            "timestamp.",
            "Logging administrative changes is required for accountability.",
            "GIVEN an administrative change, WHEN the change completes, THEN a log with actor and "
            "timestamp shall be recorded.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A biometric attendance service with protected templates and verified records.",
        "components": [
            {"name": "Biometric Service", "description": "Verifies clock-ins.", "responsibilities": ["Verify live samples", "Protect templates"]},
            {"name": "Record Store", "description": "Stores attendance records.", "responsibilities": ["Bind records to events", "Log admin changes"]},
        ],
        "data_flows": ["Employee -> biometric device -> record store"],
        "deployment_notes": "On-premise with payroll export.",
    },
    "threats": [
        {
            "name": "Template Theft",
            "description": "An attacker steals biometric templates.",
            "category": "Data Breach",
            "severity": "high",
            "affected_assets": ["Biometric templates"],
            "mitigations": [{"description": "Non-reversible protected template storage.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Template protection", "Forgery resistance", "Admin logging"],
        "out_of_scope": ["Payroll processing", "Access-control doors"],
    },
    "assumptions": ["Fingerprint and face are the supported modalities."],
    "testing": [
        {"description": "Attempt to reconstruct a raw template from storage and verify impossibility.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Biometric failures block legitimate clock-ins.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Supervisor verification fallback.",
    },
    "unresolved": ["Whether biometric data consent records are required."],
}


SCN_049: dict[str, Any] = {
    "id": "SCN-049",
    "name": "Warehouse Robotics Network Security",
    "description": (
        "A warehouse operator uses automated robots for picking. They need to "
        "segment the robot control network from office systems, ensure only "
        "approved devices join the robot network, and monitor robot controllers "
        "for anomalies."
    ),
    "categories": ["CAT-08", "CAT-02", "CAT-03"],
    "analysis": {
        "stakeholders": ["Warehouse operator", "Automation vendor", "Logistics clients"],
        "assets": [
            "Robot control network",
            "Automated picking robots",
            "Approved device registry",
            "Controller monitoring",
        ],
        "users": ["Warehouse supervisors", "Automation technicians", "IT support"],
        "constraints": [
            "Robot network must be segmented from office systems",
            "Only approved devices may join the robot network",
            "Controller anomalies must be monitored",
        ],
        "goals": [
            "Segment the robot network",
            "Restrict device onboarding",
            "Monitor controllers for anomalies",
        ],
        "missing_information": [
            "Robot count",
            "Device onboarding method",
            "Monitoring coverage",
        ],
        "project_summary": (
            "Network security for warehouse robotics with segmentation, approved "
            "device onboarding, and controller anomaly monitoring."
        ),
    },
    "clarifications": [
        {"question": "How many robots are deployed?", "answer": "About 150 picking robots."},
        {"question": "How are devices onboarded?", "answer": "By serial number and certificate."},
        {"question": "What monitoring coverage is needed?", "answer": "Controller health and behaviour."},
    ],
    "requirements": [
        req(
            "NET-001",
            "network",
            "Robot Network Segmentation",
            "The system shall segment the robot control network from office "
            "systems.",
            "Segmentation is the first network-security requirement for the facility.",
            "GIVEN traffic from the office network attempting to reach the robot network, WHEN the "
            "attempt is made, THEN it shall be blocked.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Approved Device Onboarding",
            "The system shall permit only devices with approved serial numbers "
            "and certificates to join the robot network.",
            "Restricting onboarding prevents rogue devices from joining the network.",
            "GIVEN a device requesting network access, WHEN the serial and certificate are validated, "
            "THEN access shall be granted only for approved devices.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Controller Anomaly Monitoring",
            "The system shall monitor robot controllers for behavioural anomalies "
            "and alert on deviation.",
            "Monitoring controllers for anomalies is a stated requirement.",
            "GIVEN a controller behaviour anomaly, WHEN the anomaly is detected, THEN an alert shall "
            "be raised.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": "A segmented robot network with certificate-based onboarding.",
        "components": [
            {"name": "Robot Network Switch", "description": "Segments robot traffic.", "responsibilities": ["Enforce segmentation", "Validate onboarding"]},
            {"name": "Controller Monitor", "description": "Tracks controller health.", "responsibilities": ["Detect anomalies", "Raise alerts"]},
        ],
        "data_flows": ["Robot -> robot network -> automation server"],
        "deployment_notes": "On-premise warehouse network.",
    },
    "threats": [
        {
            "name": "Rogue Device Join",
            "description": "An unauthorised device joins the robot network.",
            "category": "Lateral Movement",
            "severity": "high",
            "affected_assets": ["Robot control network"],
            "mitigations": [{"description": "Approved onboarding and segmentation.", "related_requirement_ids": ["SEC-001", "NET-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Segmentation", "Device onboarding", "Controller monitoring"],
        "out_of_scope": ["Robot mechanical safety", "Warehouse ERP"],
    },
    "assumptions": ["Robots ship with unique certificates."],
    "testing": [
        {"description": "Attempt to join the network with an unapproved device and verify denial.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Segmentation breaks robot-vendor remote support.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Vendor support access via approved jump host.",
    },
    "unresolved": ["Whether Wi-Fi robot control is in scope."],
}


SCN_050: dict[str, Any] = {
    "id": "SCN-050",
    "name": "Satellite Ground Station Monitoring",
    "description": (
        "A satellite operator wants to secure its ground station network. They "
        "need to authenticate remote commands, monitor for anomalous uplink "
        "activity, and protect the integrity of telemetry records."
    ),
    "categories": ["CAT-01", "CAT-03", "CAT-07"],
    "analysis": {
        "stakeholders": ["Satellite operator", "Ground station staff", "Telemetry consumers"],
        "assets": [
            "Ground station network",
            "Satellite command links",
            "Telemetry records",
            "Uplink monitoring",
        ],
        "users": ["Ground station operators", "Mission planners", "Telemetry analysts"],
        "constraints": [
            "Remote commands must be authenticated",
            "Anomalous uplink activity must be monitored",
            "Telemetry records must be tamper-evident",
        ],
        "goals": [
            "Authenticate remote commands",
            "Monitor uplink activity",
            "Protect telemetry integrity",
        ],
        "missing_information": [
            "Ground station count",
            "Command protocol",
            "Telemetry consumers",
        ],
        "project_summary": (
            "Security for a satellite ground station network with authenticated "
            "commands, uplink monitoring, and tamper-evident telemetry."
        ),
    },
    "clarifications": [
        {"question": "How many ground stations exist?", "answer": "Three ground stations."},
        {"question": "What command protocol is used?", "answer": "CCSDS over encrypted links."},
        {"question": "Who consumes telemetry?", "answer": "Mission control and data partners."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Authenticated Remote Commands",
            "The system shall authenticate every remote command before it is "
            "uplinked to a satellite.",
            "Authenticating commands prevents unauthorised satellite control.",
            "GIVEN a remote command, WHEN it is submitted, THEN it shall be authenticated before "
            "uplink occurs.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Anomalous Uplink Monitoring",
            "The system shall monitor uplink activity and alert on anomalous "
            "patterns.",
            "Monitoring uplink activity is a stated security requirement.",
            "GIVEN an uplink activity anomaly, WHEN the anomaly is detected, THEN an alert shall be "
            "raised to ground station staff.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Tamper-Evident Telemetry",
            "The system shall store telemetry records so that any alteration is "
            "detectable.",
            "Tamper-evident telemetry preserves record integrity for partners.",
            "GIVEN an alteration to a telemetry record, WHEN the integrity check runs, THEN the "
            "alteration shall be detected.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "An authenticated command path with uplink monitoring and protected telemetry.",
        "components": [
            {"name": "Command Gateway", "description": "Authenticates and uplinks commands.", "responsibilities": ["Validate commands", "Enforce uplink policy"]},
            {"name": "Telemetry Store", "description": "Preserves telemetry integrity.", "responsibilities": ["Store records", "Detect alterations"]},
        ],
        "data_flows": ["Mission control -> command gateway -> satellite"],
        "deployment_notes": "Ground station network with encrypted links.",
    },
    "threats": [
        {
            "name": "Unauthorised Satellite Command",
            "description": "An attacker uplinks a command to a satellite.",
            "category": "Spoofing",
            "severity": "critical",
            "affected_assets": ["Satellite command links"],
            "mitigations": [{"description": "Command authentication before uplink.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Command authentication", "Uplink monitoring", "Telemetry integrity"],
        "out_of_scope": ["Satellite payload design", "Orbital operations"],
    },
    "assumptions": ["CCSDS commands are used over encrypted links."],
    "testing": [
        {"description": "Submit an unauthenticated command and verify it is not uplinked.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Command latency increases could affect satellite operations.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Performance testing of the command path.",
    },
    "unresolved": ["Whether partner telemetry access needs separate controls."],
}


SCN_051: dict[str, Any] = {
    "id": "SCN-051",
    "name": "Border Inspection Port Control Security",
    "description": (
        "A border inspection authority wants to secure the control systems at "
        "its inspection ports. Operators need authenticated access, system "
        "changes must be audited, and the systems must continue operating "
        "during network outages."
    ),
    "categories": ["CAT-04", "CAT-07"],
    "analysis": {
        "stakeholders": ["Border inspection authority", "Port operators", "National security office"],
        "assets": [
            "Inspection control systems",
            "Operator accounts",
            "Change audit log",
            "Inspection records",
        ],
        "users": ["Inspection operators", "System administrators", "Auditors"],
        "constraints": [
            "Operator access must be authenticated",
            "System changes must be audited",
            "Operation must continue during outages",
        ],
        "goals": [
            "Authenticate operator access",
            "Audit system changes",
            "Continue operation during outages",
        ],
        "missing_information": [
            "Port count",
            "Access authentication method",
            "Outage tolerance",
        ],
        "project_summary": (
            "Security for border inspection port control systems with "
            "authenticated access, audited changes, and outage-resilient "
            "operation."
        ),
    },
    "clarifications": [
        {"question": "How many ports are covered?", "answer": "Five inspection ports."},
        {"question": "What authentication is used?", "answer": "Smart cards plus PIN."},
        {"question": "How long can systems tolerate outages?", "answer": "Up to four hours."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Authenticated Operator Access",
            "The system shall require smart card and PIN authentication for "
            "operator access.",
            "Strong authentication for operator access is the stated requirement.",
            "GIVEN an operator requesting access, WHEN authentication occurs, THEN both the smart card "
            "and PIN shall be required.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "System Change Audit",
            "The system shall audit all configuration changes with operator and "
            "timestamp.",
            "Auditing system changes is required for accountability.",
            "GIVEN a configuration change, WHEN the change is applied, THEN an audit record with "
            "operator and timestamp shall be created.",
            priority="must",
        ),
        req(
            "NFR-001",
            "non_functional",
            "Outage-Resilient Operation",
            "The system shall continue essential inspection operation for up to "
            "four hours during a network outage.",
            "Continuing operation during outages is a stated operational requirement.",
            "GIVEN a network outage, WHEN the outage lasts up to four hours, THEN essential "
            "inspection functions shall remain available.",
            priority="must",
            numeric=[{"value": "4 hours", "provenance": "USER_SPECIFIED"}],
        ),
    ],
    "architecture": {
        "overview": "Authenticated inspection terminals with local fallback for outages.",
        "components": [
            {"name": "Inspection Terminal", "description": "Operator interface.", "responsibilities": ["Authenticate operators", "Record changes"]},
            {"name": "Local Fallback", "description": "Maintains operation offline.", "responsibilities": ["Cache records", "Sync on reconnect"]},
        ],
        "data_flows": ["Operator -> inspection terminal -> central system"],
        "deployment_notes": "Port sites with central oversight.",
    },
    "threats": [
        {
            "name": "Unauthorised System Access",
            "description": "An attacker gains control of an inspection system.",
            "category": "Credential Abuse",
            "severity": "critical",
            "affected_assets": ["Inspection control systems"],
            "mitigations": [{"description": "Smart card and PIN authentication.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Operator authentication", "Change audit", "Outage resilience"],
        "out_of_scope": ["Physical inspection process", "Border databases"],
    },
    "assumptions": ["Smart card and PIN credentials are issued to operators."],
    "testing": [
        {"description": "Attempt access without a smart card and verify denial.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Authentication failures block ports during peak hours.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Fallback verification procedures.",
    },
    "unresolved": ["Whether remote administration is allowed."],
}


SCN_052: dict[str, Any] = {
    "id": "SCN-052",
    "name": "Clinical Trial Data Platform Security",
    "description": (
        "A clinical research organisation runs trials and collects participant "
        "data. They need strict role-based access to trial data, complete "
        "logging of data changes, and the ability to anonymize participant "
        "records for analysis."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Clinical research organisation", "Sponsors", "Trial participants"],
        "assets": [
            "Trial participant data",
            "Trial datasets",
            "Role-based access controls",
            "Change log",
        ],
        "users": ["Data managers", "Clinical monitors", "Biostatisticians"],
        "constraints": [
            "Trial data access must be role-based",
            "Data changes must be fully logged",
            "Anonymization must be available",
        ],
        "goals": [
            "Enforce role-based trial access",
            "Log all data changes",
            "Anonymize participant records",
        ],
        "missing_information": [
            "Trial count",
            "Participant numbers",
            "Anonymization standard",
        ],
        "project_summary": (
            "Security for a clinical trial data platform with role-based access, "
            "complete change logging, and participant anonymization."
        ),
    },
    "clarifications": [
        {"question": "How many trials are managed?", "answer": "About 30 active trials."},
        {"question": "How many participants per trial?", "answer": "Between 200 and 2,000."},
        {"question": "Which anonymization standard applies?", "answer": "The sponsor's internal standard."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Role-Based Trial Access",
            "The system shall grant trial data access strictly according to role "
            "and trial assignment.",
            "Role-based access is the primary confidentiality requirement.",
            "GIVEN a user requesting trial data, WHEN the request is evaluated, THEN access shall be "
            "granted only for the user's assigned trials and role.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Data Change Logging",
            "The system shall log every data change with user, record, and "
            "timestamp.",
            "Complete change logging is required for trial integrity.",
            "GIVEN a data change, WHEN it is applied, THEN a log with user, record, and timestamp "
            "shall be recorded.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Participant Anonymization",
            "The system shall anonymize participant records on demand for "
            "analysis without exposing identities.",
            "Anonymization for analysis is a stated requirement.",
            "GIVEN an anonymization request, WHEN it is processed, THEN the output shall contain no "
            "identifying participant data.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A trial data platform with role access, change logs, and anonymization.",
        "components": [
            {"name": "Trial Data Service", "description": "Manages trial datasets.", "responsibilities": ["Enforce role access", "Log changes"]},
            {"name": "Anonymization Engine", "description": "Removes identifying data.", "responsibilities": ["Anonymize records", "Produce safe datasets"]},
        ],
        "data_flows": ["Data manager -> trial data service -> datasets"],
        "deployment_notes": "Cloud-hosted with compliance controls.",
    },
    "threats": [
        {
            "name": "Unauthorised Trial Data Access",
            "description": "A staff member accesses trial data outside their assignment.",
            "category": "Broken Access Control",
            "severity": "high",
            "affected_assets": ["Trial participant data"],
            "mitigations": [{"description": "Role and trial scoping with logging.", "related_requirement_ids": ["SEC-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Role access", "Change logging", "Anonymization"],
        "out_of_scope": ["Trial design", "Participant recruitment"],
    },
    "assumptions": ["Sponsor internal standards drive anonymization."],
    "testing": [
        {"description": "Attempt access to an unassigned trial and verify denial.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Anonymization errors leak participant identities.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Automated identity-field checks after anonymization.",
    },
    "unresolved": ["Whether participant consent records are in scope."],
}


SCN_053: dict[str, Any] = {
    "id": "SCN-053",
    "name": "Logistics Warehouse DLP",
    "description": (
        "A logistics company handles shipping manifests and client contracts. "
        "They want to detect sensitive documents leaving via email, control "
        "uploads of contracts to external systems, and review a list of "
        "policy violations."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Logistics company", "Clients", "Compliance team"],
        "assets": [
            "Shipping manifests",
            "Client contracts",
            "Email gateway",
            "Policy violation log",
        ],
        "users": ["Operations staff", "Compliance reviewers", "IT administrators"],
        "constraints": [
            "Sensitive document transfers must be detected",
            "Contract uploads must be controlled",
            "Violations must be reviewable",
        ],
        "goals": [
            "Detect sensitive email exits",
            "Control external contract uploads",
            "Provide a violation review list",
        ],
        "missing_information": [
            "Document volume",
            "Policy rules",
            "Review workflow",
        ],
        "project_summary": (
            "Data loss prevention for a logistics company covering email exits, "
            "external contract uploads, and violation review."
        ),
    },
    "clarifications": [
        {"question": "What document volume is handled?", "answer": "About 5,000 documents daily."},
        {"question": "Which policies apply?", "answer": "Client contracts and manifests are sensitive."},
        {"question": "Who reviews violations?", "answer": "The compliance team."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Sensitive Email Exit Detection",
            "The system shall detect sensitive documents being sent via email "
            "and flag them.",
            "Detecting email exits is the first DLP requirement.",
            "GIVEN an email containing a sensitive document, WHEN the email is sent, THEN the system "
            "shall flag the transfer for review.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Contract Upload Control",
            "The system shall block uploads of client contracts to unapproved "
            "external systems.",
            "Controlling contract uploads prevents data leaving the company.",
            "GIVEN an upload of a contract to an unapproved external system, WHEN the upload is "
            "attempted, THEN it shall be blocked.",
            priority="must",
        ),
        req(
            "FR-003",
            "functional",
            "Violation Review List",
            "The system shall present policy violations to compliance reviewers "
            "in a queue.",
            "A reviewable violation list is the stated workflow requirement.",
            "GIVEN a policy violation, WHEN it is recorded, THEN it shall appear in the compliance "
            "review queue.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A DLP engine inspecting email and upload paths with a review queue.",
        "components": [
            {"name": "DLP Engine", "description": "Detects sensitive data.", "responsibilities": ["Scan email", "Control uploads"]},
            {"name": "Review Queue", "description": "Presents violations.", "responsibilities": ["Track violations", "Support disposition"]},
        ],
        "data_flows": ["Email/upload -> DLP engine -> review queue"],
        "deployment_notes": "Cloud or on-premise gateway.",
    },
    "threats": [
        {
            "name": "Contract Exfiltration",
            "description": "An employee sends a client contract outside the company.",
            "category": "Data Loss",
            "severity": "high",
            "affected_assets": ["Client contracts"],
            "mitigations": [{"description": "Email detection and upload control.", "related_requirement_ids": ["FR-001", "FR-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Email detection", "Upload control", "Violation review"],
        "out_of_scope": ["Endpoint control", "Removable media"],
    },
    "assumptions": ["Contracts and manifests are the sensitive document classes."],
    "testing": [
        {"description": "Send a sensitive document by email and verify the flag.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "False positives flood the compliance queue.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "Policy tuning and exception handling.",
    },
    "unresolved": ["Whether encrypted attachments must be inspected."],
}


SCN_054: dict[str, Any] = {
    "id": "SCN-054",
    "name": "AI Model Serving Platform Security",
    "description": (
        "An AI company serves models to clients through an API. They need "
        "authentication for API calls, protection of client model outputs, and "
        "usage logging for billing and abuse detection."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["AI company", "Client developers", "Platform operations"],
        "assets": [
            "Model API",
            "Client API keys",
            "Model outputs",
            "Usage logs",
        ],
        "users": ["Client applications", "Platform engineers", "Billing analysts"],
        "constraints": [
            "API calls must be authenticated",
            "Client outputs must be protected",
            "Usage must be logged for billing",
        ],
        "goals": [
            "Authenticate API calls",
            "Protect client model outputs",
            "Log usage for billing and abuse detection",
        ],
        "missing_information": [
            "Client count",
            "API request volume",
            "Billing granularity",
        ],
        "project_summary": (
            "Security for an AI model serving API with call authentication, "
            "output protection, and usage logging."
        ),
    },
    "clarifications": [
        {"question": "How many clients use the API?", "answer": "About 250 client organisations."},
        {"question": "What request volume is expected?", "answer": "Roughly 10 million calls per month."},
        {"question": "What billing granularity is needed?", "answer": "Per-client per-model tokens."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "API Call Authentication",
            "The system shall require authentication for every model API call.",
            "Authenticating calls prevents unauthorised model use.",
            "GIVEN a model API call, WHEN the call arrives, THEN it shall be authenticated before "
            "serving.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Client Output Protection",
            "The system shall ensure model outputs are delivered only to the "
            "requesting client.",
            "Protecting outputs prevents cross-client data exposure.",
            "GIVEN a model output for a client, WHEN the output is delivered, THEN it shall be "
            "accessible only by that client.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Usage Logging for Billing",
            "The system shall log per-client, per-model usage sufficient for "
            "billing.",
            "Usage logging is required for billing and abuse detection.",
            "GIVEN a completed API call, WHEN the call finishes, THEN a usage record with client, "
            "model, and token counts shall be stored.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "An authenticated model gateway with per-client scoping and usage logs.",
        "components": [
            {"name": "Model Gateway", "description": "Authenticates and routes calls.", "responsibilities": ["Verify keys", "Scope outputs"]},
            {"name": "Usage Logger", "description": "Records per-client usage.", "responsibilities": ["Log calls", "Support billing"]},
        ],
        "data_flows": ["Client -> model gateway -> model backend"],
        "deployment_notes": "Cloud-hosted with GPU backends.",
    },
    "threats": [
        {
            "name": "Unauthorised Model Use",
            "description": "An attacker calls the model API without valid credentials.",
            "category": "Credential Abuse",
            "severity": "high",
            "affected_assets": ["Model API"],
            "mitigations": [{"description": "API call authentication with usage logging.", "related_requirement_ids": ["SEC-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Call authentication", "Output scoping", "Usage logging"],
        "out_of_scope": ["Model training", "Model content safety"],
    },
    "assumptions": ["Clients hold per-organisation API keys."],
    "testing": [
        {"description": "Call the API without credentials and verify rejection.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Usage logging latency affects billing accuracy.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Idempotent usage records with reconciliation.",
    },
    "unresolved": ["Whether prompt content must be audited."],
}


SCN_055: dict[str, Any] = {
    "id": "SCN-055",
    "name": "Browser Extension Security Validation",
    "description": (
        "A software vendor distributes browser extensions to enterprise "
        "customers. They want a pipeline that validates extension code before "
        "release, signs the released extension, and monitors the distribution "
        "channel for tampered copies."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Software vendor", "Enterprise customers", "Browser vendors"],
        "assets": [
            "Extension codebase",
            "Validation pipeline",
            "Extension signatures",
            "Distribution channel",
        ],
        "users": ["Extension developers", "Release engineers", "Security reviewers"],
        "constraints": [
            "Extensions must be validated before release",
            "Released extensions must be signed",
            "Tampered copies must be detected",
        ],
        "goals": [
            "Validate extension code pre-release",
            "Sign released extensions",
            "Monitor distribution for tampering",
        ],
        "missing_information": [
            "Extension count",
            "Validation rules",
            "Distribution channels",
        ],
        "project_summary": (
            "Release security for browser extensions with pre-release validation, "
            "signing, and distribution tamper monitoring."
        ),
    },
    "clarifications": [
        {"question": "How many extensions are maintained?", "answer": "About 15 extensions."},
        {"question": "What validation rules apply?", "answer": "No remote code and minimal permissions."},
        {"question": "Which channels distribute them?", "answer": "The official browser stores."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Pre-Release Code Validation",
            "The system shall validate extension code against release rules "
            "before release.",
            "Pre-release validation is the first supply-chain requirement.",
            "GIVEN an extension build, WHEN it is submitted for release, THEN release shall require "
            "passing validation against the release rules.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Extension Signing",
            "The system shall sign released extension packages with the vendor "
            "identity.",
            "Signing released extensions confirms authenticity.",
            "GIVEN a released extension package, WHEN it is published, THEN it shall carry a valid "
            "vendor signature.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Distribution Tamper Monitoring",
            "The system shall monitor distribution channels for tampered copies "
            "of released extensions.",
            "Monitoring the channel protects customers from fake extensions.",
            "GIVEN a distribution listing for an extension, WHEN the listing does not match the signed "
            "release, THEN an alert shall be raised.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A validation and signing pipeline feeding monitored distribution channels.",
        "components": [
            {"name": "Validation Pipeline", "description": "Checks extension code.", "responsibilities": ["Enforce rules", "Gate releases"]},
            {"name": "Channel Monitor", "description": "Watches distribution listings.", "responsibilities": ["Detect tampering", "Raise alerts"]},
        ],
        "data_flows": ["Developer -> validation pipeline -> browser store"],
        "deployment_notes": "Cloud CI/CD with store monitoring.",
    },
    "threats": [
        {
            "name": "Malicious Extension Copy",
            "description": "An attacker publishes a tampered extension copy.",
            "category": "Supply Chain",
            "severity": "high",
            "affected_assets": ["Distribution channel"],
            "mitigations": [{"description": "Signing and channel tamper monitoring.", "related_requirement_ids": ["SEC-002", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Validation", "Signing", "Channel monitoring"],
        "out_of_scope": ["Extension functionality", "Browser internals"],
    },
    "assumptions": ["Official browser stores are the distribution channels."],
    "testing": [
        {"description": "Submit an extension that fails validation and verify release is blocked.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Store validation rules change unexpectedly.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Monitoring of store policy changes.",
    },
    "unresolved": ["Whether enterprise self-hosting must be supported."],
}


SCN_056: dict[str, Any] = {
    "id": "SCN-056",
    "name": "Crypto Wallet Service Hardening",
    "description": (
        "A crypto wallet provider wants to harden its service. They need "
        "hardware-backed key custody, withdrawal confirmation with a second "
        "factor, and monitoring of withdrawal behaviour for anomalies."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Wallet provider", "Customers", "Asset custodians"],
        "assets": [
            "Wallet keys",
            "Customer balances",
            "Withdrawal flow",
            "Anomaly monitoring",
        ],
        "users": ["Customers", "Support agents", "Security analysts"],
        "constraints": [
            "Keys must be hardware-backed",
            "Withdrawals require second-factor confirmation",
            "Withdrawal anomalies must be monitored",
        ],
        "goals": [
            "Custody keys in hardware",
            "Confirm withdrawals with a second factor",
            "Monitor withdrawal anomalies",
        ],
        "missing_information": [
            "Customer count",
            "Withdrawal volume",
            "Hardware key architecture",
        ],
        "project_summary": (
            "Security hardening for a crypto wallet service with hardware-backed "
            "keys, second-factor withdrawal confirmation, and anomaly monitoring."
        ),
    },
    "clarifications": [
        {"question": "How many customers use the wallet?", "answer": "About 80,000 customers."},
        {"question": "What is withdrawal volume?", "answer": "About 500 withdrawals per day."},
        {"question": "How are keys stored?", "answer": "In an HSM-backed vault."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Hardware-Backed Key Custody",
            "The system shall hold wallet signing keys in hardware security "
            "modules.",
            "Hardware-backed custody is the core key-protection requirement.",
            "GIVEN a wallet signing operation, WHEN the operation is performed, THEN the key shall be "
            "used only within the hardware security module.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Second-Factor Withdrawal Confirmation",
            "The system shall require a second-factor confirmation for every "
            "withdrawal.",
            "Second-factor confirmation protects against unauthorised withdrawals.",
            "GIVEN a withdrawal request, WHEN it is submitted, THEN it shall require second-factor "
            "confirmation before execution.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Withdrawal Anomaly Monitoring",
            "The system shall monitor withdrawal behaviour and flag anomalous "
            "activity for review.",
            "Anomaly monitoring supports fraud detection on withdrawals.",
            "GIVEN a withdrawal pattern deviating from the customer's baseline, WHEN the anomaly is "
            "detected, THEN it shall be flagged for security review.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": "An HSM-backed wallet service with confirmed withdrawals and monitoring.",
        "components": [
            {"name": "Wallet Service", "description": "Manages balances and withdrawals.", "responsibilities": ["Use HSM keys", "Confirm withdrawals"]},
            {"name": "Anomaly Monitor", "description": "Flags suspicious withdrawals.", "responsibilities": ["Detect deviations", "Create review items"]},
        ],
        "data_flows": ["Customer -> wallet service -> HSM vault"],
        "deployment_notes": "Multi-region cloud with HSM clusters.",
    },
    "threats": [
        {
            "name": "Unauthorised Withdrawal",
            "description": "An attacker initiates a withdrawal from a victim account.",
            "category": "Fraud",
            "severity": "critical",
            "affected_assets": ["Customer balances"],
            "mitigations": [{"description": "Second-factor confirmation and anomaly monitoring.", "related_requirement_ids": ["SEC-002", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Key custody", "Withdrawal confirmation", "Anomaly monitoring"],
        "out_of_scope": ["Exchange trading", "Blockchain network"],
    },
    "assumptions": ["An HSM-backed vault stores all wallet keys."],
    "testing": [
        {"description": "Submit a withdrawal without second-factor confirmation and verify it is held.", "type": "security", "related_requirement_ids": ["SEC-002"]}
    ],
    "risk": {
        "description": "HSM capacity limits constrain transaction throughput.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Capacity planning and HSM scaling.",
    },
    "unresolved": ["Whether cold-storage rotation is required."],
}


SCN_057: dict[str, Any] = {
    "id": "SCN-057",
    "name": "Telemedicine Appointment Platform",
    "description": (
        "A telemedicine company schedules appointments and hosts video visits. "
        "They need to secure the video session with end-to-end encryption, "
        "control who can join a session, and record session metadata for "
        "compliance."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Telemedicine company", "Providers", "Patients"],
        "assets": [
            "Video visit sessions",
            "Appointment records",
            "Session metadata",
            "Provider and patient accounts",
        ],
        "users": ["Patients", "Providers", "Scheduling staff"],
        "constraints": [
            "Video sessions must be end-to-end encrypted",
            "Only invited participants may join",
            "Session metadata must be retained",
        ],
        "goals": [
            "Encrypt video sessions end to end",
            "Control session membership",
            "Retain session metadata",
        ],
        "missing_information": [
            "Visit volume",
            "Video platform",
            "Metadata retention",
        ],
        "project_summary": (
            "Security for a telemedicine appointment platform with end-to-end "
            "encrypted video, controlled session membership, and metadata "
            "retention."
        ),
    },
    "clarifications": [
        {"question": "What visit volume is handled?", "answer": "About 1,500 visits per week."},
        {"question": "Which video platform is used?", "answer": "An embedded WebRTC-based service."},
        {"question": "How long is metadata kept?", "answer": "Two years."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "End-to-End Video Encryption",
            "The system shall encrypt video visit media end to end between "
            "participants.",
            "End-to-end encryption is the first requirement for video visits.",
            "GIVEN a video visit session, WHEN media is exchanged, THEN it shall be encrypted end to "
            "end between participants.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Controlled Session Membership",
            "The system shall allow only invited participants to join a video "
            "session.",
            "Controlling membership prevents uninvited access to visits.",
            "GIVEN a session join request, WHEN the requester is not an invited participant, THEN the "
            "join shall be rejected.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Session Metadata Retention",
            "The system shall retain session metadata for the configured "
            "retention period.",
            "Retaining metadata supports compliance for the platform.",
            "GIVEN session metadata, WHEN the retention period passes, THEN the records shall be "
            "purged.",
            priority="should",
            numeric=[{"value": "2 years", "provenance": "USER_SPECIFIED"}],
        ),
    ],
    "architecture": {
        "overview": "A WebRTC visit platform with encrypted media and controlled access.",
        "components": [
            {"name": "Visit Service", "description": "Coordinates video visits.", "responsibilities": ["Enforce membership", "Route encrypted media"]},
            {"name": "Metadata Store", "description": "Retains session metadata.", "responsibilities": ["Store metadata", "Purge on retention"]},
        ],
        "data_flows": ["Participant -> visit service -> WebRTC media"],
        "deployment_notes": "Cloud-hosted with regional media relays.",
    },
    "threats": [
        {
            "name": "Session Eavesdropping",
            "description": "An attacker joins or intercepts a video visit.",
            "category": "Spoofing",
            "severity": "high",
            "affected_assets": ["Video visit sessions"],
            "mitigations": [{"description": "End-to-end encryption and membership control.", "related_requirement_ids": ["SEC-001", "SEC-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Encryption", "Membership control", "Metadata retention"],
        "out_of_scope": ["Provider clinical tools", "Prescriptions"],
    },
    "assumptions": ["WebRTC media is relayed without server-side decryption."],
    "testing": [
        {"description": "Attempt to join a session as an uninvited user and verify rejection.", "type": "security", "related_requirement_ids": ["SEC-002"]}
    ],
    "risk": {
        "description": "Encryption relays increase media latency.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "Regional relay placement.",
    },
    "unresolved": ["Whether visit recordings are permitted."],
}


SCN_058: dict[str, Any] = {
    "id": "SCN-058",
    "name": "Smart Meter Infrastructure Security",
    "description": (
        "A utility is rolling out smart meters and wants to secure the meter "
        "network. They need authenticated meter reads, protection against meter "
        "spoofing, and detection of tampered meters reporting unusual data."
    ),
    "categories": ["CAT-01", "CAT-03"],
    "analysis": {
        "stakeholders": ["Utility", "Metered customers", "Grid operator"],
        "assets": [
            "Smart meter fleet",
            "Meter network",
            "Usage data",
            "Meter authentication records",
        ],
        "users": ["Meter readers", "Grid operators", "Field technicians"],
        "constraints": [
            "Meter reads must be authenticated",
            "Spoofed meters must be detected",
            "Tamper indications must be monitored",
        ],
        "goals": [
            "Authenticate meter reads",
            "Detect meter spoofing",
            "Monitor tamper indications",
        ],
        "missing_information": [
            "Meter count",
            "Meter network technology",
            "Tamper sensor coverage",
        ],
        "project_summary": (
            "Security for a smart meter network with authenticated reads, spoof "
            "detection, and tamper monitoring."
        ),
    },
    "clarifications": [
        {"question": "How many meters are deployed?", "answer": "About 300,000 meters."},
        {"question": "Which network carries reads?", "answer": "A dedicated RF mesh."},
        {"question": "Do meters have tamper sensors?", "answer": "Yes, magnetic and enclosure sensors."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Authenticated Meter Reads",
            "The system shall accept usage reads only from authenticated meters.",
            "Authenticated reads prevent injection of false usage data.",
            "GIVEN a usage read from a meter, WHEN the read arrives, THEN it shall be accepted only "
            "after the meter's identity validates.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Meter Spoof Detection",
            "The system shall detect attempts to impersonate a meter identity.",
            "Detecting spoofing prevents false metering data and billing abuse.",
            "GIVEN an impersonation attempt against a meter identity, WHEN the attempt is detected, "
            "THEN it shall be flagged and investigated.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Tamper Indication Monitoring",
            "The system shall raise an alert when a meter reports a tamper "
            "sensor event or anomalous data.",
            "Monitoring tamper indications detects physical tampering.",
            "GIVEN a meter tamper sensor event, WHEN the event is received, THEN an alert shall be "
            "raised.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "An authenticated RF mesh feeding a meter data platform with tamper monitoring.",
        "components": [
            {"name": "Meter Collector", "description": "Ingests meter reads.", "responsibilities": ["Validate meter identity", "Reject spoofs"]},
            {"name": "Tamper Monitor", "description": "Tracks tamper events.", "responsibilities": ["Process sensor events", "Raise alerts"]},
        ],
        "data_flows": ["Meter -> RF mesh -> meter collector"],
        "deployment_notes": "Field-deployed collector network.",
    },
    "threats": [
        {
            "name": "Meter Spoofing for Billing Fraud",
            "description": "An attacker spoofs a meter to reduce reported usage.",
            "category": "Spoofing",
            "severity": "high",
            "affected_assets": ["Usage data"],
            "mitigations": [{"description": "Authenticated reads and spoof detection.", "related_requirement_ids": ["SEC-001", "SEC-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Authenticated reads", "Spoof detection", "Tamper monitoring"],
        "out_of_scope": ["Meter hardware design", "Billing system"],
    },
    "assumptions": ["Meters hold unique cryptographic identities."],
    "testing": [
        {"description": "Simulate a spoofed meter read and verify it is rejected.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "RF mesh congestion delays critical tamper alerts.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Priority messaging for tamper events.",
    },
    "unresolved": ["Whether hourly read cadence is sufficient."],
}


SCN_059: dict[str, Any] = {
    "id": "SCN-059",
    "name": "Air Quality Monitoring Sensor Security",
    "description": (
        "A city deploys air quality sensors across districts. They need to "
        "authenticate sensor data, prevent tampering with sensor readings, and "
        "alert when a sensor goes silent or reports implausible values."
    ),
    "categories": ["CAT-01", "CAT-03"],
    "analysis": {
        "stakeholders": ["City government", "Public health office", "Citizens"],
        "assets": [
            "Air quality sensors",
            "Sensor data feed",
            "Public dashboard",
            "Sensor identity records",
        ],
        "users": ["City analysts", "Field technicians", "Public health staff"],
        "constraints": [
            "Sensor data must be authenticated",
            "Reading tampering must be detected",
            "Silent sensors must alert",
        ],
        "goals": [
            "Authenticate sensor data",
            "Detect tampered readings",
            "Alert on silent sensors",
        ],
        "missing_information": [
            "Sensor count",
            "Sensor protocol",
            "Alert recipients",
        ],
        "project_summary": (
            "Security for a city air quality sensor network with authenticated "
            "data, tamper detection, and silent-sensor alerting."
        ),
    },
    "clarifications": [
        {"question": "How many sensors are deployed?", "answer": "About 250 sensors."},
        {"question": "What protocol do sensors use?", "answer": "MQTT over TLS."},
        {"question": "Who receives alerts?", "answer": "The public health office."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Sensor Data Authentication",
            "The system shall authenticate sensor data before accepting it into "
            "the feed.",
            "Authenticating sensor data prevents false readings entering the public feed.",
            "GIVEN a sensor data message, WHEN it arrives, THEN it shall be accepted only after "
            "sensor identity validation.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Implausible Reading Detection",
            "The system shall flag readings that are implausible for the sensor "
            "type.",
            "Detecting implausible values identifies tampered or faulty sensors.",
            "GIVEN a sensor reading outside the plausible range, WHEN it is received, THEN it shall "
            "be flagged for review.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Silent Sensor Alerting",
            "The system shall alert when a sensor stops reporting within the "
            "expected interval.",
            "Alerting on silent sensors supports availability of the network.",
            "GIVEN a sensor with no report in the expected interval, WHEN the interval elapses, THEN "
            "an alert shall be raised to the public health office.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "An authenticated MQTT ingestion with validation and silence monitoring.",
        "components": [
            {"name": "Ingestion Service", "description": "Accepts sensor data.", "responsibilities": ["Validate identity", "Check plausibility"]},
            {"name": "Silence Monitor", "description": "Tracks reporting intervals.", "responsibilities": ["Detect gaps", "Raise alerts"]},
        ],
        "data_flows": ["Sensor -> MQTT -> ingestion service -> dashboard"],
        "deployment_notes": "City-managed cloud ingestion.",
    },
    "threats": [
        {
            "name": "False Sensor Data Injection",
            "description": "An attacker injects false air quality readings.",
            "category": "Spoofing",
            "severity": "medium",
            "affected_assets": ["Sensor data feed"],
            "mitigations": [{"description": "Data authentication and plausibility checks.", "related_requirement_ids": ["SEC-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Data authentication", "Plausibility checks", "Silence alerting"],
        "out_of_scope": ["Sensor hardware", "Air quality science"],
    },
    "assumptions": ["Sensors report over MQTT with TLS."],
    "testing": [
        {"description": "Send an unauthenticated reading and verify it is rejected.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Network gaps trigger frequent silent-sensor alerts.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "Grace windows and retry logic.",
    },
    "unresolved": ["Whether public dashboard data needs provenance."],
}


SCN_060: dict[str, Any] = {
    "id": "SCN-060",
    "name": "Subway Fare System Security",
    "description": (
        "A city's subway operator runs a contactless fare system. They need to "
        "protect fare card transactions from replay, validate each card "
        "transaction with the backend, and detect unusual fare usage patterns."
    ),
    "categories": ["CAT-05", "CAT-03"],
    "analysis": {
        "stakeholders": ["Subway operator", "Commuters", "Fare revenue office"],
        "assets": [
            "Fare cards",
            "Station readers",
            "Fare backend",
            "Transaction logs",
        ],
        "users": ["Commuters", "Station staff", "Revenue analysts"],
        "constraints": [
            "Card transactions must resist replay",
            "Each transaction must be validated with the backend",
            "Unusual usage must be detected",
        ],
        "goals": [
            "Prevent transaction replay",
            "Validate transactions with the backend",
            "Detect unusual usage patterns",
        ],
        "missing_information": [
            "Card volume",
            "Reader count",
            "Detection response team",
        ],
        "project_summary": (
            "Security for a subway contactless fare system with replay "
            "protection, backend validation, and usage anomaly detection."
        ),
    },
    "clarifications": [
        {"question": "How many fare cards are active?", "answer": "About 2 million cards."},
        {"question": "How many station readers exist?", "answer": "About 4,000 readers."},
        {"question": "Who responds to usage anomalies?", "answer": "The revenue protection team."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Transaction Replay Protection",
            "The system shall reject replayed fare card transactions using "
            "unique transaction tokens.",
            "Replay protection prevents reuse of captured fare transactions.",
            "GIVEN a fare transaction token that was already used, WHEN it is presented again, THEN "
            "the transaction shall be rejected.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Backend Transaction Validation",
            "The system shall validate each fare transaction with the backend "
            "before granting passage.",
            "Backend validation confirms card status at the time of use.",
            "GIVEN a fare card presented at a reader, WHEN the transaction is initiated, THEN passage "
            "shall be granted only after backend validation succeeds.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Unusual Usage Detection",
            "The system shall detect unusual fare usage patterns and alert the "
            "revenue protection team.",
            "Detecting unusual usage supports fraud investigation.",
            "GIVEN a usage pattern matching unusual behaviour, WHEN the pattern is detected, THEN an "
            "alert shall be sent to revenue protection.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": "Station readers validating against a central fare backend with anomaly detection.",
        "components": [
            {"name": "Fare Backend", "description": "Validates transactions.", "responsibilities": ["Validate cards", "Reject replays"]},
            {"name": "Usage Analyser", "description": "Detects unusual patterns.", "responsibilities": ["Detect anomalies", "Alert revenue team"]},
        ],
        "data_flows": ["Card -> reader -> fare backend"],
        "deployment_notes": "Backend in the city data centre.",
    },
    "threats": [
        {
            "name": "Fare Transaction Replay",
            "description": "An attacker replays a captured transaction to ride free.",
            "category": "Fraud",
            "severity": "medium",
            "affected_assets": ["Fare cards"],
            "mitigations": [{"description": "Unique transaction tokens with replay rejection.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Replay protection", "Backend validation", "Usage detection"],
        "out_of_scope": ["Station hardware", "Fare pricing"],
    },
    "assumptions": ["Readers have connectivity to the fare backend."],
    "testing": [
        {"description": "Replay a captured transaction token and verify rejection.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Backend outages block passage at stations.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Short offline grace window with reconciliation.",
    },
    "unresolved": ["Whether contactless bank cards are in scope."],
}


SCENARIOS_C: list[dict[str, Any]] = [SCN_041, SCN_042, SCN_043, SCN_044, SCN_045, SCN_046, SCN_047, SCN_048, SCN_049, SCN_050, SCN_051, SCN_052, SCN_053, SCN_054, SCN_055, SCN_056, SCN_057, SCN_058, SCN_059, SCN_060]
