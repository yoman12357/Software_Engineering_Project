"""Scenario bank B (SCN-021..SCN-040) for the CyberSRS QLoRA training dataset.

Hand-authored, genuinely distinct synthetic cybersecurity project scenarios.
See scenario_bank_a.py for schema conventions.
"""

from __future__ import annotations

from typing import Any

from .scenario_bank_a import req


SCN_021: dict[str, Any] = {
    "id": "SCN-021",
    "name": "Bank Branch Network Monitoring",
    "description": (
        "A regional bank wants to monitor the networks in its branch offices. "
        "We need to spot rogue devices plugged into branch switches, detect "
        "traffic to unexpected external hosts, and centralise branch monitoring "
        "alerts at head office."
    ),
    "categories": ["CAT-03", "CAT-07"],
    "analysis": {
        "stakeholders": ["Regional bank IT", "Branch managers", "Bank security team"],
        "assets": [
            "Branch office switches",
            "Branch workstations and cash machines",
            "Central alerting platform",
        ],
        "users": ["Branch support staff", "Head-office security analysts", "Field technicians"],
        "constraints": [
            "Monitoring must be centralised at head office",
            "Branch device inventory must be accurate",
            "Alerts must not require branch staff action",
        ],
        "goals": [
            "Detect rogue devices on branch networks",
            "Detect unexpected external traffic",
            "Centralise branch monitoring alerts",
        ],
        "missing_information": [
            "Number of branch offices",
            "Existing monitoring tooling",
            "Branch network device types",
        ],
        "project_summary": (
            "Centralised network monitoring for a regional bank's branch offices "
            "to detect rogue devices, unexpected external traffic, and consolidate "
            "alerts at head office."
        ),
    },
    "clarifications": [
        {"question": "How many branch offices are in scope?", "answer": "38 branch offices."},
        {"question": "Is there existing monitoring tooling?", "answer": "A legacy SNMP collector at head office."},
        {"question": "What device types exist in branches?", "answer": "Switches, routers, workstations, and cash machines."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Rogue Device Detection",
            "The system shall detect devices connected to branch switches that are "
            "not part of the approved device inventory.",
            "Detecting rogue devices is the first monitoring goal named by the bank.",
            "GIVEN a device connecting to a branch switch, WHEN the device is not in the approved inventory, "
            "THEN the system shall raise an alert at head office within 15 minutes.",
            priority="must",
            numeric=[{"value": "15 minutes", "provenance": "ASSUMPTION_REQUIRING_CONFIRMATION"}],
        ),
        req(
            "FR-002",
            "functional",
            "Unexpected External Traffic Detection",
            "The system shall detect branch traffic to external hosts outside an "
            "approved destination list.",
            "Detecting unexpected external traffic is an explicit requirement of the bank.",
            "GIVEN branch traffic to an external host, WHEN the host is not in the approved list, THEN the "
            "system shall flag the traffic for review.",
            priority="must",
        ),
        req(
            "NFR-001",
            "non_functional",
            "Centralised Alert Delivery",
            "The system shall deliver all branch alerts to the head-office "
            "platform without requiring action from branch staff.",
            "Centralising alerts is the stated operational goal of the bank.",
            "GIVEN a branch monitoring alert, WHEN the alert is generated, THEN it shall appear on the "
            "head-office platform automatically.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "Branch sensors forward to a head-office monitoring service.",
        "components": [
            {"name": "Branch Sensor", "description": "Local traffic and device visibility.", "responsibilities": ["Detect rogue devices", "Detect external traffic"]},
            {"name": "Head-Office Console", "description": "Central alert aggregation.", "responsibilities": ["Aggregate alerts", "Route to analysts"]},
        ],
        "data_flows": ["Branch sensor -> head-office console"],
        "deployment_notes": "Branch sensor deployed per office; console at head office.",
    },
    "threats": [
        {
            "name": "Rogue Branch Device",
            "description": "An attacker connects an unauthorised device to a branch switch.",
            "category": "Lateral Movement",
            "severity": "high",
            "affected_assets": ["Branch office switches"],
            "mitigations": [{"description": "Rogue device detection with head-office alerting.", "related_requirement_ids": ["FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Branch network monitoring", "Rogue device detection"],
        "out_of_scope": ["Cash machine hardware", "Internet banking"],
    },
    "assumptions": ["Approved device inventory is maintained centrally."],
    "testing": [
        {"description": "Connect an unapproved device and verify the alert appears at head office.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Inventory drift causes false rogue-device alerts.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Quarterly inventory reconciliation.",
    },
    "unresolved": ["Whether branch VPN tunnels must be monitored."],
}


SCN_022: dict[str, Any] = {
    "id": "SCN-022",
    "name": "Defense Contractor Export-Control File Access",
    "description": (
        "A defence contractor stores export-controlled technical documents. They "
        "need to control who can open them, watermark copies with the viewer's "
        "identity, and block downloads outside approved locations."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Defence contractor", "Export compliance office", "Government customer"],
        "assets": [
            "Export-controlled technical documents",
            "Document management system",
            "Watermarking service",
        ],
        "users": ["Engineers", "Program managers", "Compliance officers"],
        "constraints": [
            "Access must follow export-control classifications",
            "Copies must identify the viewer",
            "Downloads must be restricted to approved locations",
        ],
        "goals": [
            "Control access to export-controlled documents",
            "Watermark document copies",
            "Restrict downloads to approved locations",
        ],
        "missing_information": [
            "Document classification scheme",
            "Identity directory",
            "Approved location policy",
        ],
        "project_summary": (
            "Access control and watermarking for export-controlled technical "
            "documents at a defence contractor, including location-restricted "
            "downloads."
        ),
    },
    "clarifications": [
        {"question": "What classification scheme is used?", "answer": "US export-control categories."},
        {"question": "Where are identities managed?", "answer": "The corporate identity directory."},
        {"question": "What counts as an approved location?", "answer": "Company sites and approved remote zones."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Export-Control Access Enforcement",
            "The system shall enforce export-control classifications when granting "
            "access to technical documents.",
            "Access control based on export classifications is the core compliance requirement.",
            "GIVEN a user requesting a classified document, WHEN the request is evaluated, THEN access "
            "shall be granted only if the user's clearances match the classification.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Viewer Watermarking",
            "The system shall watermark every displayed copy with the viewing "
            "user's identity.",
            "Watermarking is required to attribute any copy back to the viewer.",
            "GIVEN a user opening a document, WHEN the document is rendered, THEN a watermark with the "
            "user's identity shall be embedded.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Location-Restricted Downloads",
            "The system shall block document downloads outside approved locations "
            "and log each blocked attempt.",
            "Restricting downloads to approved locations is an explicit requirement.",
            "GIVEN a download attempt from an unapproved location, WHEN the request is evaluated, THEN "
            "the download shall be blocked and the attempt logged.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A classification-aware document service with watermarking and location checks.",
        "components": [
            {"name": "Document Service", "description": "Enforces classification access.", "responsibilities": ["Evaluate clearances", "Enforce location policy"]},
            {"name": "Watermark Service", "description": "Embeds viewer identity.", "responsibilities": ["Render watermarked copies"]},
        ],
        "data_flows": ["User -> document service -> watermark service"],
        "deployment_notes": "Deployed on-premise at the contractor.",
    },
    "threats": [
        {
            "name": "Unauthorised Export-Control Access",
            "description": "A user without clearance opens a classified document.",
            "category": "Broken Access Control",
            "severity": "critical",
            "affected_assets": ["Export-controlled technical documents"],
            "mitigations": [{"description": "Clearance-based access enforcement.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Access control", "Watermarking", "Location-restricted downloads"],
        "out_of_scope": ["Physical document control", "Crypto management"],
    },
    "assumptions": ["Clearances are held in the corporate identity directory."],
    "testing": [
        {"description": "Attempt a download from an unapproved location and verify the block.", "type": "security", "related_requirement_ids": ["SEC-002"]}
    ],
    "risk": {
        "description": "Location-based blocks interrupt legitimate remote work.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Approved remote zone policy with periodic review.",
    },
    "unresolved": ["Whether printing must be controlled."],
}


SCN_023: dict[str, Any] = {
    "id": "SCN-023",
    "name": "Solar Farm Remote Monitoring Security",
    "description": (
        "A solar farm operator wants to secure the remote monitoring link from "
        "its generation sites to the control centre. We need encrypted "
        "telemetry, authentication of site devices, and alerts when a site "
        "drops offline unexpectedly."
    ),
    "categories": ["CAT-06", "CAT-03"],
    "analysis": {
        "stakeholders": ["Solar farm operator", "Grid operations", "Maintenance contractors"],
        "assets": [
            "Solar generation sites",
            "Telemetry links",
            "Control centre",
            "Site device identities",
        ],
        "users": ["Control-centre operators", "Maintenance technicians", "Grid operators"],
        "constraints": [
            "Telemetry must be encrypted in transit",
            "Site devices must be authenticated",
            "Unexpected offline events must alert",
        ],
        "goals": [
            "Encrypt site telemetry",
            "Authenticate site devices",
            "Alert on unexpected site disconnects",
        ],
        "missing_information": [
            "Number of generation sites",
            "Transport technology",
            "Alerting channel",
        ],
        "project_summary": (
            "Security for solar farm remote monitoring with encrypted telemetry, "
            "site device authentication, and unexpected-offline alerting."
        ),
    },
    "clarifications": [
        {"question": "How many generation sites are monitored?", "answer": "27 sites."},
        {"question": "What transport carries the links?", "answer": "Cellular with site VPN endpoints."},
        {"question": "Where should offline alerts go?", "answer": "To the control-centre operator console."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Encrypted Telemetry Transport",
            "The system shall encrypt all site telemetry in transit between "
            "generation sites and the control centre.",
            "Encryption of the monitoring link is the first security requirement named.",
            "GIVEN telemetry from a site, WHEN it transits the network, THEN it shall be transported "
            "only over an encrypted channel.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Site Device Authentication",
            "The system shall authenticate each site device before accepting its "
            "telemetry.",
            "Authenticating site devices prevents spoofed telemetry.",
            "GIVEN a site device connecting, WHEN the connection is established, THEN the device shall "
            "be authenticated with its unique identity before telemetry is accepted.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Unexpected Offline Alerting",
            "The system shall raise an alert when a site drops offline outside a "
            "planned maintenance window.",
            "Alerting on unexpected disconnects is an explicit monitoring requirement.",
            "GIVEN a site that stops reporting, WHEN no maintenance window is active, THEN the control "
            "centre shall receive an offline alert within 10 minutes.",
            priority="must",
            numeric=[{"value": "10 minutes", "provenance": "ASSUMPTION_REQUIRING_CONFIRMATION"}],
        ),
    ],
    "architecture": {
        "overview": "Site VPN gateways feeding an encrypted telemetry pipeline to the control centre.",
        "components": [
            {"name": "Site Gateway", "description": "Authenticated, encrypted site termination.", "responsibilities": ["Authenticate devices", "Encrypt telemetry"]},
            {"name": "Control-Centre Collector", "description": "Ingests telemetry and monitors connectivity.", "responsibilities": ["Validate sources", "Detect offline sites"]},
        ],
        "data_flows": ["Site -> site gateway -> control-centre collector"],
        "deployment_notes": "Cellular backhaul per site; collector at control centre.",
    },
    "threats": [
        {
            "name": "Telemetry Spoofing",
            "description": "An attacker injects false site telemetry.",
            "category": "Spoofing",
            "severity": "high",
            "affected_assets": ["Telemetry links"],
            "mitigations": [{"description": "Site device authentication on every connection.", "related_requirement_ids": ["FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Encrypted telemetry", "Device authentication", "Offline alerting"],
        "out_of_scope": ["Solar inverter control", "Grid dispatch"],
    },
    "assumptions": ["Each site terminates its own VPN endpoint."],
    "testing": [
        {"description": "Drop a site's connection and verify the offline alert arrives.", "type": "security", "related_requirement_ids": ["FR-002"]}
    ],
    "risk": {
        "description": "Cellular outages cause spurious offline alerts.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "Grace periods and maintenance-window integration.",
    },
    "unresolved": ["Whether contractor access to sites must be monitored."],
}


SCN_024: dict[str, Any] = {
    "id": "SCN-024",
    "name": "Healthcare Claims Processing API",
    "description": (
        "A healthcare administrator processes insurance claims through a set of "
        "APIs. They need request signing between partners, protection of patient "
        "data in API responses, and a complete record of every claims call."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Healthcare administrator", "Insurance partners", "Patient data stewards"],
        "assets": [
            "Claims API",
            "Patient data records",
            "Partner credentials",
            "API call log",
        ],
        "users": ["Partner systems", "Claims analysts", "API administrators"],
        "constraints": [
            "Partner requests must be authenticated and signed",
            "Patient data must be protected in responses",
            "Every claims call must be recorded",
        ],
        "goals": [
            "Authenticate partner API requests",
            "Protect patient data in responses",
            "Record all claims API calls",
        ],
        "missing_information": [
            "Partner count",
            "Claims volume",
            "Data minimisation requirements",
        ],
        "project_summary": (
            "A hardened claims processing API for a healthcare administrator with "
            "partner request signing, patient data protection, and complete call "
            "recording."
        ),
    },
    "clarifications": [
        {"question": "How many partners integrate with the API?", "answer": "Around 40 partner organisations."},
        {"question": "What claims volume is expected?", "answer": "About 2,000 claims per day."},
        {"question": "Is data minimisation required?", "answer": "Yes, return only requested fields."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Partner Request Signing",
            "The system shall require a digital signature on every partner API "
            "request before processing.",
            "Request signing between partners is the primary authentication requirement.",
            "GIVEN a partner API request, WHEN the request arrives, THEN processing shall occur only "
            "after the request signature validates.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Patient Data Protection in Responses",
            "The system shall return only the patient data fields requested by "
            "the partner and never full records.",
            "Data minimisation for patient data is required by the administrator.",
            "GIVEN a partner request for a claim, WHEN the response is built, THEN only the requested "
            "patient data fields shall be included.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Claims Call Recording",
            "The system shall record every claims API call with partner, "
            "timestamp, and response status.",
            "Complete call recording is a stated requirement for traceability.",
            "GIVEN any claims API call, WHEN the call completes, THEN a record with partner, timestamp, "
            "and status shall be persisted.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A signed-request API gateway in front of the claims service with a call log.",
        "components": [
            {"name": "API Gateway", "description": "Validates partner signatures.", "responsibilities": ["Verify signatures", "Enforce field scoping"]},
            {"name": "Call Logger", "description": "Records every request.", "responsibilities": ["Log calls", "Store response status"]},
        ],
        "data_flows": ["Partner -> API gateway -> claims service"],
        "deployment_notes": "Deployed in the administrator's cloud.",
    },
    "threats": [
        {
            "name": "Fake Partner Request",
            "description": "An attacker sends an unsigned or forged claims request.",
            "category": "Spoofing",
            "severity": "high",
            "affected_assets": ["Claims API"],
            "mitigations": [{"description": "Mandatory request signatures.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Request signing", "Response field scoping", "Call recording"],
        "out_of_scope": ["Claim adjudication logic", "Payer systems"],
    },
    "assumptions": ["Partners manage their own signing credentials."],
    "testing": [
        {"description": "Submit an unsigned request and verify rejection.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Signature key rotation breaks partner integrations.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Overlapping key rotation windows.",
    },
    "unresolved": ["Whether audit of data field access is needed."],
}


SCN_025: dict[str, Any] = {
    "id": "SCN-025",
    "name": "Public Library Network Guest Access",
    "description": (
        "A public library system provides free internet to visitors. They want "
        "to stop guests from abusing the network for large downloads, block "
        "known malicious sites, and keep only the minimum session data needed "
        "for troubleshooting."
    ),
    "categories": ["CAT-02", "CAT-07"],
    "analysis": {
        "stakeholders": ["Library system", "Visitors", "Internet provider"],
        "assets": [
            "Guest access points",
            "Content filtering service",
            "Session logs",
        ],
        "users": ["Library visitors", "Library IT staff", "Reference librarians"],
        "constraints": [
            "Session data must be minimised",
            "Large downloads must be throttled",
            "Known malicious sites must be blocked",
        ],
        "goals": [
            "Throttle large downloads",
            "Block known malicious sites",
            "Minimise stored session data",
        ],
        "missing_information": [
            "Number of branches",
            "Downstream bandwidth",
            "Session retention period",
        ],
        "project_summary": (
            "Guest internet access for a public library system with download "
            "throttling, malicious-site blocking, and minimal session data "
            "retention."
        ),
    },
    "clarifications": [
        {"question": "How many branches provide guest access?", "answer": "14 branches."},
        {"question": "What downstream bandwidth is available?", "answer": "1 Gbps shared per branch."},
        {"question": "How long are session logs kept?", "answer": "No longer than 30 days."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Large Download Throttling",
            "The system shall throttle guest sessions that exceed a configured "
            "download threshold.",
            "Throttling large downloads is an explicit abuse-control requirement.",
            "GIVEN a guest session exceeding the download threshold, WHEN the threshold is crossed, THEN "
            "the session throughput shall be throttled.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Malicious Site Blocking",
            "The system shall block access to known malicious domains and "
            "categories configured by the library.",
            "Blocking known malicious sites is a stated safety requirement.",
            "GIVEN a guest request to a blocked domain, WHEN the filter evaluates the URL, THEN the "
            "request shall be denied and a block page shown.",
            priority="must",
        ),
        req(
            "DATA-001",
            "data",
            "Minimal Session Data",
            "The system shall store only the minimum session data needed for "
            "troubleshooting and purge it after the configured retention period.",
            "Minimising stored session data respects visitor privacy and the "
            "confirmed 30-day retention.",
            "GIVEN session records older than the 30-day retention window, WHEN the purge job runs, "
            "THEN those records shall be deleted.",
            priority="must",
            numeric=[{"value": "30 days", "provenance": "USER_SPECIFIED"}],
        ),
    ],
    "architecture": {
        "overview": "Library access points with filtering and throttling, plus a short-retention log.",
        "components": [
            {"name": "Filtering Gateway", "description": "Blocks malicious sites.", "responsibilities": ["Evaluate URLs", "Show block pages"]},
            {"name": "Shaping Service", "description": "Throttles heavy sessions.", "responsibilities": ["Track usage", "Enforce caps"]},
        ],
        "data_flows": ["Guest -> access point -> filtering gateway -> internet"],
        "deployment_notes": "Gateway per branch; policy centrally managed.",
    },
    "threats": [
        {
            "name": "Malware Delivery",
            "description": "A visitor downloads malware through the guest network.",
            "category": "Malware",
            "severity": "medium",
            "affected_assets": ["Guest access points"],
            "mitigations": [{"description": "Malicious-site filtering at the gateway.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Throttling", "Site filtering", "Session retention"],
        "out_of_scope": ["Patron accounts", "Staff networks"],
    },
    "assumptions": ["A 30-day session retention window is acceptable."],
    "testing": [
        {"description": "Attempt access to a blocked domain and verify the block page.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Over-filtering blocks legitimate educational content.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Category review and opt-out for approved patrons.",
    },
    "unresolved": ["Whether patrons require authenticated access."],
}


SCN_026: dict[str, Any] = {
    "id": "SCN-026",
    "name": "Food Delivery Account Security",
    "description": (
        "A food delivery platform keeps having accounts taken over. They want "
        "risk-based login checks, device fingerprinting for repeat customers, "
        "and alerts when an account logs in from a new city."
    ),
    "categories": ["CAT-04", "CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Food delivery platform", "Customers", "Restaurant partners"],
        "assets": [
            "Customer accounts",
            "Order history",
            "Payment methods on file",
            "Risk engine",
        ],
        "users": ["Customers", "Support agents", "Fraud analysts"],
        "constraints": [
            "Risk checks must not add friction for trusted customers",
            "Device fingerprinting must be privacy-aware",
            "New-location logins must alert",
        ],
        "goals": [
            "Apply risk-based login checks",
            "Fingerprint customer devices",
            "Alert on new-city logins",
        ],
        "missing_information": [
            "Customer base size",
            "Existing fraud tooling",
            "Alert response owner",
        ],
        "project_summary": (
            "Account takeover protection for a food delivery platform with "
            "risk-based login checks, device fingerprinting, and new-city login "
            "alerts."
        ),
    },
    "clarifications": [
        {"question": "How large is the customer base?", "answer": "About 900,000 customers."},
        {"question": "Is there existing fraud tooling?", "answer": "A basic rules engine only."},
        {"question": "Who responds to login alerts?", "answer": "The fraud analyst team."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Risk-Based Login Checks",
            "The system shall evaluate login risk signals and require additional "
            "verification when risk is elevated.",
            "Risk-based login is the primary anti-takeover mechanism requested.",
            "GIVEN a login attempt with elevated risk signals, WHEN the risk score exceeds the "
            "threshold, THEN additional verification shall be required before access is granted.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Device Fingerprinting",
            "The system shall maintain privacy-aware device fingerprints for "
            "repeat customers.",
            "Device fingerprinting is requested to recognise trusted customer devices.",
            "GIVEN a repeat customer login, WHEN the device is matched to a known fingerprint, THEN the "
            "login shall use the trusted-device signal in risk scoring.",
            priority="should",
        ),
        req(
            "FR-003",
            "functional",
            "New-City Login Alerting",
            "The system shall alert the fraud team when an account logs in from "
            "a city not previously used by that account.",
            "New-city login alerts are an explicit requirement for takeover "
            "detection.",
            "GIVEN a login from a new city for an account, WHEN the login completes, THEN a fraud-team "
            "alert shall be created.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A risk engine in front of the login flow with device fingerprinting and alerts.",
        "components": [
            {"name": "Risk Engine", "description": "Scores login attempts.", "responsibilities": ["Evaluate signals", "Require verification"]},
            {"name": "Fingerprint Service", "description": "Tracks device signals.", "responsibilities": ["Create fingerprints", "Match returning devices"]},
        ],
        "data_flows": ["Customer -> login -> risk engine"],
        "deployment_notes": "Cloud-hosted with regional replication.",
    },
    "threats": [
        {
            "name": "Account Takeover",
            "description": "An attacker takes over a customer account using stolen credentials.",
            "category": "Credential Abuse",
            "severity": "high",
            "affected_assets": ["Customer accounts"],
            "mitigations": [{"description": "Risk-based login checks and alerting.", "related_requirement_ids": ["FR-001", "FR-003"]}],
        }
    ],
    "scope": {
        "in_scope": ["Risk-based login", "Device fingerprinting", "New-city alerts"],
        "out_of_scope": ["Payment processing", "Restaurant-side systems"],
    },
    "assumptions": ["Fraud analysts respond to alerts during business hours."],
    "testing": [
        {"description": "Simulate a login from a new city and verify the alert.", "type": "security", "related_requirement_ids": ["FR-003"]}
    ],
    "risk": {
        "description": "Friction from risk checks drives customers away.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Tiered verification for trusted devices.",
    },
    "unresolved": ["Whether SMS OTP is acceptable as a verification channel."],
}


SCN_027: dict[str, Any] = {
    "id": "SCN-027",
    "name": "Payment Gateway Tokenization",
    "description": (
        "A payment gateway wants to tokenize stored card data so that merchant "
        "systems never handle raw card numbers. Tokens must be bound to one "
        "merchant, raw numbers must be unrecoverable from tokens, and token "
        "usage must be audited."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Payment gateway", "Merchants", "Card networks"],
        "assets": [
            "Card data",
            "Token vault",
            "Merchant tokens",
            "Token usage audit log",
        ],
        "users": ["Merchant systems", "Payment operators", "Compliance team"],
        "constraints": [
            "Raw card numbers must never reach merchants",
            "Tokens must be merchant-bound",
            "Token usage must be auditable",
        ],
        "goals": [
            "Tokenize stored card data",
            "Bind tokens to a single merchant",
            "Audit token usage",
        ],
        "missing_information": [
            "Tokenisation standard",
            "Merchant count",
            "Token rotation requirements",
        ],
        "project_summary": (
            "Card tokenisation for a payment gateway that binds tokens to a "
            "single merchant, prevents recovery of raw numbers, and audits token "
            "usage."
        ),
    },
    "clarifications": [
        {"question": "Which tokenisation standard applies?", "answer": "Vault-based proprietary tokens, not network tokens."},
        {"question": "How many merchants are served?", "answer": "Around 1,500 merchants."},
        {"question": "Are token rotations required?", "answer": "Only on compromise events."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Card Data Tokenization",
            "The system shall replace stored card numbers with tokens so that "
            "merchant systems never receive raw card data.",
            "Tokenisation is the core requirement preventing merchant exposure of card data.",
            "GIVEN a card stored in the vault, WHEN a merchant requests card data, THEN only a token "
            "shall be returned, never the raw number.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Merchant-Bound Tokens",
            "The system shall bind every token to a single merchant and reject "
            "its use by any other merchant.",
            "Merchant binding is the stated isolation requirement for tokens.",
            "GIVEN a token bound to merchant A, WHEN merchant B attempts to use it, THEN the use shall "
            "be rejected and logged.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Token Usage Auditing",
            "The system shall record every token use with merchant, time, and "
            "operation.",
            "Auditing token usage is required for compliance.",
            "GIVEN any token operation, WHEN the operation completes, THEN an audit record with "
            "merchant, time, and operation shall be stored.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A token vault with an issuing service and per-merchant scoping.",
        "components": [
            {"name": "Token Vault", "description": "Stores card data and tokens.", "responsibilities": ["Issue tokens", "Prevent raw-number exposure"]},
            {"name": "Audit Logger", "description": "Records token usage.", "responsibilities": ["Log operations", "Support compliance queries"]},
        ],
        "data_flows": ["Merchant -> token service -> vault"],
        "deployment_notes": "Hardened PCI environment.",
    },
    "threats": [
        {
            "name": "Token Misuse Across Merchants",
            "description": "A merchant uses another merchant's token.",
            "category": "Broken Access Control",
            "severity": "high",
            "affected_assets": ["Merchant tokens"],
            "mitigations": [{"description": "Single-merchant token binding.", "related_requirement_ids": ["SEC-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Tokenisation", "Merchant binding", "Usage auditing"],
        "out_of_scope": ["Payment authorisation", "Card scheme processing"],
    },
    "assumptions": ["Vault-based proprietary tokens are acceptable."],
    "testing": [
        {"description": "Attempt cross-merchant token use and verify rejection.", "type": "security", "related_requirement_ids": ["SEC-002"]}
    ],
    "risk": {
        "description": "Vault compromise would expose raw card numbers.",
        "likelihood": "low",
        "impact": "critical",
        "mitigation": "HSM-backed encryption and strict access control.",
    },
    "unresolved": ["Whether merchants require token detokenisation services."],
}


SCN_028: dict[str, Any] = {
    "id": "SCN-028",
    "name": "Autonomous Vehicle Data Logging Security",
    "description": (
        "An autonomous vehicle company logs sensor data from its test fleet. "
        "They need to protect the log files from tampering, control who can "
        "access the data, and verify the origin of each log file."
    ),
    "categories": ["CAT-07", "CAT-05"],
    "analysis": {
        "stakeholders": ["AV company", "Test fleet operators", "Safety reviewers"],
        "assets": [
            "Sensor log files",
            "Test vehicle fleet",
            "Log storage platform",
            "Access control records",
        ],
        "users": ["Data engineers", "Safety reviewers", "Fleet operators"],
        "constraints": [
            "Logs must be tamper-evident",
            "Access must be role-based",
            "Log origin must be verifiable",
        ],
        "goals": [
            "Protect log files from tampering",
            "Control log access",
            "Verify log file origin",
        ],
        "missing_information": [
            "Fleet size",
            "Log volume",
            "Reviewer roles",
        ],
        "project_summary": (
            "Security for autonomous vehicle sensor log data with tamper-evident "
            "storage, role-based access, and origin verification."
        ),
    },
    "clarifications": [
        {"question": "How large is the test fleet?", "answer": "90 test vehicles."},
        {"question": "What log volume is generated?", "answer": "About 3 TB per day across the fleet."},
        {"question": "Who reviews the logs?", "answer": "Safety reviewers and data engineers."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Tamper-Evident Log Storage",
            "The system shall store sensor logs so that any modification is "
            "detectable.",
            "Tamper-evidence is the first integrity requirement for test logs.",
            "GIVEN a modification to any stored sensor log, WHEN the integrity check runs, THEN the "
            "modification shall be detected and reported.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Role-Based Log Access",
            "The system shall grant access to sensor logs only according to the "
            "requesting user's role.",
            "Role-based access to logs is an explicit requirement.",
            "GIVEN a user requesting a sensor log, WHEN the request is evaluated, THEN access shall be "
            "granted only if the user's role permits it.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Log Origin Verification",
            "The system shall verify the origin identity of each uploaded log "
            "file from the test fleet.",
            "Verifying log origin prevents forged or misattributed logs.",
            "GIVEN a log file upload, WHEN the file arrives, THEN the origin vehicle identity shall be "
            "verified before the file is accepted.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "Vehicle-attested log uploads into a tamper-evident object store with role-based access.",
        "components": [
            {"name": "Ingestion Service", "description": "Verifies log origins.", "responsibilities": ["Verify vehicle attestation", "Accept uploads"]},
            {"name": "Log Store", "description": "Tamper-evident storage.", "responsibilities": ["Detect modification", "Enforce role access"]},
        ],
        "data_flows": ["Vehicle -> ingestion service -> log store"],
        "deployment_notes": "Cloud object storage with regional redundancy.",
    },
    "threats": [
        {
            "name": "Log Tampering",
            "description": "A reviewer alters logs to hide an incident.",
            "category": "Repudiation",
            "severity": "high",
            "affected_assets": ["Sensor log files"],
            "mitigations": [{"description": "Tamper-evident storage with integrity checks.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Tamper-evidence", "Role access", "Origin verification"],
        "out_of_scope": ["Vehicle controls", "Public road deployment"],
    },
    "assumptions": ["Each vehicle holds an attestation identity."],
    "testing": [
        {"description": "Alter a test log and verify the integrity check reports it.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Log volume strains ingestion and storage capacity.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Tiered storage and retention policies.",
    },
    "unresolved": ["Whether real-time telemetry must also be secured."],
}


SCN_029: dict[str, Any] = {
    "id": "SCN-029",
    "name": "Drone Fleet Command Security",
    "description": (
        "A drone inspection company operates a fleet of drones for infrastructure "
        "surveys. They need to secure the command channel to each drone, "
        "authenticate operators, and block drones from flying into restricted "
        "zones."
    ),
    "categories": ["CAT-06", "CAT-03", "CAT-08"],
    "analysis": {
        "stakeholders": ["Drone company", "Aviation regulator", "Client sites"],
        "assets": [
            "Drone fleet",
            "Command and control links",
            "Operator credentials",
            "Geofence data",
        ],
        "users": ["Drone pilots", "Mission planners", "Safety officers"],
        "constraints": [
            "Command channels must be encrypted and authenticated",
            "Only authorised operators may control drones",
            "Restricted zones must never be entered",
        ],
        "goals": [
            "Secure drone command channels",
            "Authenticate operators",
            "Enforce geofences",
        ],
        "missing_information": [
            "Fleet size",
            "Command link technology",
            "Restricted zone data source",
        ],
        "project_summary": (
            "Security for a drone inspection fleet's command channel with "
            "operator authentication and geofence enforcement."
        ),
    },
    "clarifications": [
        {"question": "How many drones are in the fleet?", "answer": "22 drones."},
        {"question": "What command link is used?", "answer": "4G/LTE with encrypted telemetry."},
        {"question": "Where do geofence data come from?", "answer": "The national airspace database."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Encrypted Command Channel",
            "The system shall encrypt and authenticate the command channel to "
            "every drone.",
            "Securing the command channel is the primary requirement for drone control.",
            "GIVEN a command message to a drone, WHEN the message is transmitted, THEN it shall be "
            "delivered only over an encrypted, authenticated channel.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Operator Authentication",
            "The system shall require authentication of the operator before "
            "granting control of any drone.",
            "Authenticating operators prevents unauthorised drone control.",
            "GIVEN an operator requesting drone control, WHEN the request is made, THEN control shall "
            "be granted only after operator authentication succeeds.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Geofence Enforcement",
            "The system shall prevent drones from entering restricted zones using "
            "current airspace data.",
            "Geofence enforcement is required for safe and legal operation.",
            "GIVEN a drone approaching a restricted zone, WHEN the flight path intersects the zone, "
            "THEN the system shall divert the drone before entry.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "An encrypted command gateway with operator auth and geofence logic.",
        "components": [
            {"name": "Command Gateway", "description": "Terminates drone links.", "responsibilities": ["Encrypt channels", "Validate operators"]},
            {"name": "Geofence Engine", "description": "Prevents restricted-zone entry.", "responsibilities": ["Evaluate flight paths", "Issue diversions"]},
        ],
        "data_flows": ["Operator -> command gateway -> drone"],
        "deployment_notes": "Cloud command service with cellular links.",
    },
    "threats": [
        {
            "name": "Drone Hijacking",
            "description": "An attacker takes control of a drone via a forged command link.",
            "category": "Spoofing",
            "severity": "critical",
            "affected_assets": ["Drone fleet"],
            "mitigations": [{"description": "Encrypted, authenticated command channels.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Command channel security", "Operator auth", "Geofences"],
        "out_of_scope": ["Drone hardware design", "Camera payloads"],
    },
    "assumptions": ["National airspace data is authoritative for geofences."],
    "testing": [
        {"description": "Plot a flight path through a restricted zone and verify the diversion.", "type": "security", "related_requirement_ids": ["SEC-002"]}
    ],
    "risk": {
        "description": "Cellular link loss during flights could strand drones.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Return-to-base fallback on link loss.",
    },
    "unresolved": ["Whether operator MFA is required."],
}


SCN_030: dict[str, Any] = {
    "id": "SCN-030",
    "name": "Smart Grid Substation Firewall",
    "description": (
        "An energy utility wants to firewall its smart-grid substation networks "
        "to protect against attacks on grid automation. Only authorised protocol "
        "traffic should pass, firmware updates must come from a signed source, "
        "and every policy change must be reviewed."
    ),
    "categories": ["CAT-02", "CAT-01"],
    "analysis": {
        "stakeholders": ["Energy utility", "Grid operations", "Regulator"],
        "assets": [
            "Substation automation networks",
            "Grid control devices",
            "Firewall policy store",
            "Firmware update source",
        ],
        "users": ["Substation technicians", "Grid operators", "Security administrators"],
        "constraints": [
            "Only authorised protocol traffic may pass",
            "Firmware updates must be from a signed source",
            "Policy changes must be reviewed",
        ],
        "goals": [
            "Filter substation traffic to authorised protocols",
            "Require signed firmware updates",
            "Review all policy changes",
        ],
        "missing_information": [
            "Number of substations",
            "Protocol list",
            "Policy review process",
        ],
        "project_summary": (
            "Smart-grid substation network protection with protocol filtering, "
            "signed firmware updates, and reviewed policy changes."
        ),
    },
    "clarifications": [
        {"question": "How many substations are in scope?", "answer": "75 substations."},
        {"question": "Which protocols must pass?", "answer": "IEC 61850 and Modbus only."},
        {"question": "How are policy changes reviewed?", "answer": "Two-person review before deployment."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Protocol Filtering",
            "The system shall allow only IEC 61850 and Modbus traffic to pass "
            "substation boundaries.",
            "Protocol allowlisting is the primary protection requirement for substation networks.",
            "GIVEN traffic at a substation boundary, WHEN the protocol is not IEC 61850 or Modbus, "
            "THEN the traffic shall be dropped and logged.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Signed Firmware Updates",
            "The system shall accept firmware updates only when signed by an "
            "authorised source.",
            "Signed firmware is required to prevent malicious updates to grid devices.",
            "GIVEN a firmware update to a grid device, WHEN the update signature is invalid, THEN the "
            "update shall be rejected.",
            priority="must",
        ),
        req(
            "NFR-001",
            "non_functional",
            "Reviewed Policy Changes",
            "The system shall require two-person review before a firewall policy "
            "change is deployed.",
            "Policy change review is the stated change-control requirement.",
            "GIVEN a proposed policy change, WHEN the change is submitted, THEN deployment shall be "
            "blocked until two reviewers approve it.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "Substation firewalls with a central, reviewed policy management plane.",
        "components": [
            {"name": "Substation Firewall", "description": "Enforces protocol allowlist.", "responsibilities": ["Filter traffic", "Log drops"]},
            {"name": "Policy Manager", "description": "Controls policy changes.", "responsibilities": ["Enforce two-person review", "Deploy policies"]},
        ],
        "data_flows": ["Control network -> substation firewall -> grid devices"],
        "deployment_notes": "Per-substation deployment with central policy management.",
    },
    "threats": [
        {
            "name": "Grid Automation Attack",
            "description": "An attacker sends malicious traffic into the substation network.",
            "category": "Lateral Movement",
            "severity": "critical",
            "affected_assets": ["Substation automation networks"],
            "mitigations": [{"description": "Protocol filtering and reviewed policies.", "related_requirement_ids": ["FR-001", "NFR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Protocol filtering", "Signed firmware", "Policy review"],
        "out_of_scope": ["Generation control", "Market systems"],
    },
    "assumptions": ["IEC 61850 and Modbus are the only authorised protocols."],
    "testing": [
        {"description": "Send a non-allowlisted protocol and verify it is dropped.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Policy review delays slow legitimate grid changes.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Streamlined emergency-change path.",
    },
    "unresolved": ["Whether remote access to substations is required."],
}


SCN_031: dict[str, Any] = {
    "id": "SCN-031",
    "name": "Call Centre Voice Recording Security",
    "description": (
        "A call centre operator records customer calls for quality and "
        "compliance. They need to encrypt recordings at rest, restrict playback "
        "to authorised reviewers, and redact payment card data from the "
        "recordings."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Call centre operator", "Clients", "Compliance officers"],
        "assets": [
            "Voice recordings",
            "Redaction engine",
            "Playback access controls",
            "Recording index",
        ],
        "users": ["Quality reviewers", "Team leads", "Compliance staff"],
        "constraints": [
            "Recordings must be encrypted at rest",
            "Playback must be restricted by role",
            "Card data must be redacted",
        ],
        "goals": [
            "Encrypt recordings at rest",
            "Restrict playback to authorised reviewers",
            "Redact card data from recordings",
        ],
        "missing_information": [
            "Recording volume",
            "Retention period",
            "Playback roles",
        ],
        "project_summary": (
            "Security for call centre voice recordings with at-rest encryption, "
            "role-restricted playback, and card data redaction."
        ),
    },
    "clarifications": [
        {"question": "What recording volume is produced?", "answer": "About 120 hours per day."},
        {"question": "How long are recordings kept?", "answer": "Two years."},
        {"question": "Which roles may play back?", "answer": "Quality reviewers and compliance only."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Recording Encryption at Rest",
            "The system shall encrypt all voice recordings at rest.",
            "Encryption of recordings at rest is the first security requirement.",
            "GIVEN a stored voice recording, WHEN the storage layer is inspected, THEN the recording "
            "shall be found encrypted.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Role-Restricted Playback",
            "The system shall restrict recording playback to users in the "
            "reviewer or compliance roles.",
            "Restricting playback to authorised reviewers is an explicit access requirement.",
            "GIVEN a user requesting playback, WHEN the user is not in a permitted role, THEN playback "
            "shall be denied.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Card Data Redaction",
            "The system shall redact payment card data from recordings before "
            "they become available for review.",
            "Redacting card data is required for payment compliance.",
            "GIVEN a recording containing card data, WHEN the recording is processed, THEN the card "
            "data shall be redacted before review access is granted.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A recording pipeline with encryption, redaction, and role-based access.",
        "components": [
            {"name": "Recording Pipeline", "description": "Ingests and redacts calls.", "responsibilities": ["Encrypt at rest", "Redact card data"]},
            {"name": "Review Portal", "description": "Playback for authorised roles.", "responsibilities": ["Enforce roles", "Serve recordings"]},
        ],
        "data_flows": ["Call -> recording pipeline -> review portal"],
        "deployment_notes": "Cloud-hosted with regional storage.",
    },
    "threats": [
        {
            "name": "Recording Disclosure",
            "description": "An unauthorised employee plays back a sensitive recording.",
            "category": "Privacy Breach",
            "severity": "high",
            "affected_assets": ["Voice recordings"],
            "mitigations": [{"description": "Role-restricted playback and encryption.", "related_requirement_ids": ["SEC-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Encryption", "Playback control", "Redaction"],
        "out_of_scope": ["Live call handling", "Workforce management"],
    },
    "assumptions": ["Quality reviewers and compliance are the only playback roles."],
    "testing": [
        {"description": "Attempt playback with a non-permitted role and verify denial.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Redaction failures expose card data in reviews.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Automated redaction verification checks.",
    },
    "unresolved": ["Whether call metadata requires separate protection."],
}


SCN_032: dict[str, Any] = {
    "id": "SCN-032",
    "name": "Real Estate Platform Tenant Data Access",
    "description": (
        "A real estate platform manages rental listings and tenant applications. "
        "They want tenants to control which documents they share, restrict "
        "agents to data for their own listings, and record every data access by "
        "an agent."
    ),
    "categories": ["CAT-05", "CAT-07", "CAT-04"],
    "analysis": {
        "stakeholders": ["Real estate platform", "Tenants", "Listing agents"],
        "assets": [
            "Tenant applications",
            "Rental listings",
            "Document sharing records",
            "Agent access log",
        ],
        "users": ["Tenants", "Listing agents", "Platform admins"],
        "constraints": [
            "Tenant document sharing must be consent-based",
            "Agents may only access their own listings",
            "Agent data access must be logged",
        ],
        "goals": [
            "Enable consent-based document sharing",
            "Restrict agents to their listings",
            "Log agent data access",
        ],
        "missing_information": [
            "Platform size",
            "Document types",
            "Access log retention",
        ],
        "project_summary": (
            "Data access controls for a real estate platform with tenant-controlled "
            "document sharing, listing-scoped agent access, and access logging."
        ),
    },
    "clarifications": [
        {"question": "How large is the platform?", "answer": "About 20,000 listings."},
        {"question": "Which documents do tenants share?", "answer": "Income proof and references."},
        {"question": "How long are access logs kept?", "answer": "Three years."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Consent-Based Document Sharing",
            "The system shall share tenant documents only with agents the tenant "
            "explicitly consents to share with.",
            "Consent-based sharing is the explicit privacy requirement.",
            "GIVEN an agent requesting a tenant document, WHEN the tenant has not consented to that "
            "agent, THEN the request shall be denied.",
            priority="must",
        ),
        req(
            "SEC-002",
            "security",
            "Listing-Scoped Agent Access",
            "The system shall restrict agents to data for listings they manage.",
            "Scoping agents to their own listings prevents cross-listing data exposure.",
            "GIVEN an agent accessing data for a listing they do not manage, WHEN the access is "
            "attempted, THEN it shall be denied and logged.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Agent Access Logging",
            "The system shall record every agent access to listing or tenant data "
            "with agent, listing, and timestamp.",
            "Logging agent data access is required for accountability.",
            "GIVEN an agent accessing listing or tenant data, WHEN the access occurs, THEN a log "
            "record with agent, listing, and timestamp shall be created.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A consent and access-control layer over listing and tenant data.",
        "components": [
            {"name": "Consent Service", "description": "Tracks tenant sharing consent.", "responsibilities": ["Evaluate consent", "Enforce scoping"]},
            {"name": "Access Log", "description": "Records agent access.", "responsibilities": ["Log accesses", "Support audits"]},
        ],
        "data_flows": ["Agent -> access-control layer -> listing data"],
        "deployment_notes": "Cloud-hosted web platform.",
    },
    "threats": [
        {
            "name": "Cross-Listing Data Exposure",
            "description": "An agent views another agent's listing data.",
            "category": "Broken Access Control",
            "severity": "high",
            "affected_assets": ["Rental listings"],
            "mitigations": [{"description": "Listing-scoped access with full logging.", "related_requirement_ids": ["SEC-002", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Consent-based sharing", "Listing scoping", "Access logging"],
        "out_of_scope": ["Property management", "Payments"],
    },
    "assumptions": ["Tenant consent is recorded per agent."],
    "testing": [
        {"description": "Attempt cross-listing access and verify denial plus log entry.", "type": "security", "related_requirement_ids": ["SEC-002"]}
    ],
    "risk": {
        "description": "Complex consent rules confuse tenants and agents.",
        "likelihood": "medium",
        "impact": "low",
        "mitigation": "Clear consent UX and help documentation.",
    },
    "unresolved": ["Whether tenants can revoke consent after sharing."],
}


SCN_033: dict[str, Any] = {
    "id": "SCN-033",
    "name": "e-Learning Assessment Integrity",
    "description": (
        "An e-learning provider wants to protect online exams from cheating. "
        "We need to lock down exam browsers, detect suspicious activity during "
        "tests, and ensure submitted answers can be attributed to the right "
        "student."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["e-Learning provider", "Students", "Educational institutions"],
        "assets": [
            "Exam content",
            "Student answer submissions",
            "Lockdown browser",
            "Activity monitoring logs",
        ],
        "users": ["Students", "Invigilators", "Exam administrators"],
        "constraints": [
            "Exam browsers must limit navigation",
            "Suspicious activity must be flagged",
            "Answer attribution must be verifiable",
        ],
        "goals": [
            "Lock down exam browsers",
            "Detect suspicious exam activity",
            "Attribute answers reliably",
        ],
        "missing_information": [
            "Student count",
            "Exam proctoring requirements",
            "Device support",
        ],
        "project_summary": (
            "Assessment integrity for an e-learning platform with locked exam "
            "browsers, suspicious-activity detection, and reliable answer "
            "attribution."
        ),
    },
    "clarifications": [
        {"question": "How many students take online exams?", "answer": "About 30,000 per year."},
        {"question": "Is live proctoring required?", "answer": "No, recorded session review is enough."},
        {"question": "Which devices are supported?", "answer": "Windows and macOS only."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Lockdown Browser Enforcement",
            "The system shall restrict the exam environment so students cannot "
            "navigate to unauthorised resources during an exam.",
            "Locking down the exam browser is the core anti-cheating mechanism requested.",
            "GIVEN a student in an active exam, WHEN the student attempts to navigate to an "
            "unauthorised resource, THEN the attempt shall be blocked and recorded.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Suspicious Activity Detection",
            "The system shall flag recorded sessions showing suspicious activity "
            "for review.",
            "Flagging suspicious activity supports recorded-session review.",
            "GIVEN an exam session with suspicious activity indicators, WHEN the session is analysed, "
            "THEN it shall be flagged for invigilator review.",
            priority="should",
        ),
        req(
            "SEC-001",
            "security",
            "Answer Attribution",
            "The system shall bind each submitted answer to the authenticated "
            "student identity.",
            "Reliable attribution of answers is required to prevent impersonation.",
            "GIVEN an answer submission, WHEN the submission is stored, THEN it shall be bound to the "
            "authenticated student identity.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A lockdown exam client with session recording and attribution.",
        "components": [
            {"name": "Lockdown Client", "description": "Restricts exam environment.", "responsibilities": ["Block navigation", "Record sessions"]},
            {"name": "Review Service", "description": "Flags suspicious sessions.", "responsibilities": ["Analyse sessions", "Bind submissions"]},
        ],
        "data_flows": ["Student -> lockdown client -> exam service"],
        "deployment_notes": "Cloud exam service with desktop clients.",
    },
    "threats": [
        {
            "name": "Cheating via Secondary Device",
            "description": "A student uses a second device to look up answers.",
            "category": "Fraud",
            "severity": "medium",
            "affected_assets": ["Exam content"],
            "mitigations": [{"description": "Session recording and suspicious-activity flagging.", "related_requirement_ids": ["FR-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Lockdown browser", "Activity flagging", "Attribution"],
        "out_of_scope": ["Live proctoring", "Course content delivery"],
    },
    "assumptions": ["Recorded-session review replaces live proctoring."],
    "testing": [
        {"description": "Attempt navigation to an external site during an exam and verify the block.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Lockdown issues disadvantage students on supported platforms.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Device compatibility testing and support desk.",
    },
    "unresolved": ["Whether mobile exam delivery is required."],
}


SCN_034: dict[str, Any] = {
    "id": "SCN-034",
    "name": "Museum Digital Exhibit Network Segmentation",
    "description": (
        "A museum runs interactive digital exhibits on a guest-facing network. "
        "They need to separate exhibit kiosks from the ticketing system, allow "
        "content updates only from a management console, and monitor the kiosks "
        "for tampering."
    ),
    "categories": ["CAT-08", "CAT-02", "CAT-03"],
    "analysis": {
        "stakeholders": ["Museum", "Exhibit designers", "IT support"],
        "assets": [
            "Exhibit kiosks",
            "Ticketing system",
            "Content management console",
            "Kiosk monitoring",
        ],
        "users": ["Exhibit visitors", "Exhibit technicians", "Museum IT"],
        "constraints": [
            "Kiosk traffic must be separated from ticketing",
            "Content updates must come from the management console",
            "Kiosk tampering must be monitored",
        ],
        "goals": [
            "Segment exhibit kiosks from ticketing",
            "Restrict content updates to the console",
            "Monitor kiosks for tampering",
        ],
        "missing_information": [
            "Kiosk count",
            "Content update frequency",
            "Monitoring tooling",
        ],
        "project_summary": (
            "Network segmentation for a museum's digital exhibits that isolates "
            "kiosks from ticketing, restricts content updates, and monitors for "
            "tampering."
        ),
    },
    "clarifications": [
        {"question": "How many exhibit kiosks are deployed?", "answer": "About 60 kiosks."},
        {"question": "How often is content updated?", "answer": "Monthly and for special exhibits."},
        {"question": "Is there existing monitoring?", "answer": "No dedicated monitoring today."},
    ],
    "requirements": [
        req(
            "NET-001",
            "network",
            "Kiosk and Ticketing Separation",
            "The system shall isolate exhibit kiosk traffic from the ticketing "
            "system network.",
            "Separating kiosks from ticketing is the primary segmentation requirement.",
            "GIVEN a kiosk attempting to reach the ticketing network, WHEN the attempt is made, THEN it "
            "shall be blocked at the segment boundary.",
            priority="must",
        ),
        req(
            "NET-002",
            "network",
            "Console-Only Content Updates",
            "The system shall accept kiosk content updates only from the "
            "management console.",
            "Restricting content updates to the console is a stated security requirement.",
            "GIVEN a content update attempt from a non-console source, WHEN the attempt is detected, "
            "THEN it shall be blocked and logged.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Kiosk Tamper Monitoring",
            "The system shall monitor kiosks for signs of tampering and alert "
            "support.",
            "Monitoring for kiosk tampering is an explicit requirement.",
            "GIVEN a tampering indicator on a kiosk, WHEN the indicator is detected, THEN support "
            "shall be alerted.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": "Segmented kiosk network with a management console and monitoring.",
        "components": [
            {"name": "Kiosk Segment", "description": "Isolated exhibit network.", "responsibilities": ["Isolate kiosks", "Block cross-segment access"]},
            {"name": "Management Console", "description": "Publishes content.", "responsibilities": ["Push content", "Monitor kiosks"]},
        ],
        "data_flows": ["Management console -> kiosk segment"],
        "deployment_notes": "On-premise museum network.",
    },
    "threats": [
        {
            "name": "Kiosk Pivoting to Ticketing",
            "description": "An attacker uses a compromised kiosk to reach the ticketing system.",
            "category": "Lateral Movement",
            "severity": "high",
            "affected_assets": ["Ticketing system"],
            "mitigations": [{"description": "Segment isolation with tamper monitoring.", "related_requirement_ids": ["NET-001", "FR-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Kiosk segmentation", "Console updates", "Tamper monitoring"],
        "out_of_scope": ["Exhibit hardware", "Online ticketing"],
    },
    "assumptions": ["Kiosks are the only devices on the exhibit segment."],
    "testing": [
        {"description": "Attempt kiosk-to-ticketing access and verify the block.", "type": "security", "related_requirement_ids": ["NET-001"]}
    ],
    "risk": {
        "description": "Content update failures during special exhibits disrupt visitors.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Staged content rollout and rollback.",
    },
    "unresolved": ["Whether visitor BYOD networks are in scope."],
}


SCN_035: dict[str, Any] = {
    "id": "SCN-035",
    "name": "Cruise Ship Onboard Network Security",
    "description": (
        "A cruise line wants to secure the onboard guest and crew networks on "
        "its ships. Guest traffic must be isolated from ship operations, crew "
        "access must be role-based, and satellite uplink usage must be "
        "monitored."
    ),
    "categories": ["CAT-08", "CAT-02", "CAT-07"],
    "analysis": {
        "stakeholders": ["Cruise line", "Ship crews", "Passengers"],
        "assets": [
            "Guest network",
            "Ship operations network",
            "Satellite uplink",
            "Crew access records",
        ],
        "users": ["Passengers", "Crew members", "Ship IT officers"],
        "constraints": [
            "Guest and operations networks must be isolated",
            "Crew access must be role-based",
            "Satellite uplink usage must be monitored",
        ],
        "goals": [
            "Isolate guest and operations networks",
            "Enforce role-based crew access",
            "Monitor satellite usage",
        ],
        "missing_information": [
            "Fleet size",
            "Passenger device count",
            "Uplink budget",
        ],
        "project_summary": (
            "Onboard network security for a cruise line with guest/operations "
            "isolation, role-based crew access, and satellite usage monitoring."
        ),
    },
    "clarifications": [
        {"question": "How many ships are in the fleet?", "answer": "Nine ships."},
        {"question": "How many passenger devices connect?", "answer": "Up to 3,000 per ship."},
        {"question": "What is the satellite budget?", "answer": "1 Gbps shared per ship."},
    ],
    "requirements": [
        req(
            "NET-001",
            "network",
            "Guest and Operations Isolation",
            "The system shall isolate the guest network from the ship operations "
            "network.",
            "Isolation of guest traffic from operations is the primary security requirement.",
            "GIVEN guest traffic attempting to reach the operations network, WHEN the attempt is made, "
            "THEN it shall be blocked.",
            priority="must",
        ),
        req(
            "SEC-001",
            "security",
            "Role-Based Crew Access",
            "The system shall grant crew members access to ship systems only "
            "according to their role.",
            "Role-based crew access is the stated access-control requirement.",
            "GIVEN a crew member requesting a ship system, WHEN the request is evaluated, THEN access "
            "shall be granted only for the member's role.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Satellite Usage Monitoring",
            "The system shall monitor satellite uplink usage and alert when "
            "utilisation approaches the ship budget.",
            "Monitoring satellite usage is required to manage the limited uplink.",
            "GIVEN satellite utilisation nearing the configured budget, WHEN the threshold is crossed, "
            "THEN ship IT shall receive an alert.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": "Shipboard segmentation with role-based access and uplink monitoring.",
        "components": [
            {"name": "Onboard Gateway", "description": "Enforces guest/operations isolation.", "responsibilities": ["Segment traffic", "Enforce roles"]},
            {"name": "Uplink Monitor", "description": "Tracks satellite usage.", "responsibilities": ["Measure utilisation", "Alert on threshold"]},
        ],
        "data_flows": ["Guest -> onboard gateway -> satellite uplink"],
        "deployment_notes": "Per-ship deployment with fleet policy.",
    },
    "threats": [
        {
            "name": "Guest-to-Operations Pivot",
            "description": "A passenger reaches the ship operations network.",
            "category": "Lateral Movement",
            "severity": "high",
            "affected_assets": ["Ship operations network"],
            "mitigations": [{"description": "Network isolation with monitoring.", "related_requirement_ids": ["NET-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Network isolation", "Role access", "Uplink monitoring"],
        "out_of_scope": ["Ship propulsion systems", "Crew payroll"],
    },
    "assumptions": ["Satellite uplink is the only external connection."],
    "testing": [
        {"description": "Attempt guest access to operations and verify the block.", "type": "security", "related_requirement_ids": ["NET-001"]}
    ],
    "risk": {
        "description": "Satellite bandwidth contention degrades guest experience.",
        "likelihood": "high",
        "impact": "low",
        "mitigation": "Per-guest bandwidth shaping.",
    },
    "unresolved": ["Whether crew BYOD is permitted on guest networks."],
}


SCN_036: dict[str, Any] = {
    "id": "SCN-036",
    "name": "Stadium Ticketing Platform Protection",
    "description": (
        "A stadium ticketing platform is hit by bot-driven ticket buying. They "
        "want bot detection on the purchase flow, device-level abuse controls, "
        "and rate limiting on the ticketing API."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Stadium operator", "Ticket sellers", "Fans"],
        "assets": [
            "Ticketing platform",
            "Ticket inventory",
            "Purchase API",
            "Bot detection engine",
        ],
        "users": ["Fans", "Ticket sellers", "Platform admins"],
        "constraints": [
            "Bot detection must not block genuine fans",
            "Abuse controls must work at peak sale times",
            "Rate limiting must apply to the purchase API",
        ],
        "goals": [
            "Detect bots in the purchase flow",
            "Apply device-level abuse controls",
            "Rate-limit the ticketing API",
        ],
        "missing_information": [
            "Peak sale volume",
            "Current bot detection",
            "Event ticket inventory size",
        ],
        "project_summary": (
            "Protection for a stadium ticketing platform against bot-driven buying "
            "with bot detection, device-level abuse controls, and API rate limiting."
        ),
    },
    "clarifications": [
        {"question": "What is peak sale volume?", "answer": "About 20,000 tickets per event sale."},
        {"question": "Is there existing bot detection?", "answer": "No dedicated bot detection."},
        {"question": "How many events per year?", "answer": "Around 120 events."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Bot Detection in Purchase Flow",
            "The system shall identify bot-driven purchase behaviour and challenge "
            "suspected sessions.",
            "Bot detection is the first requirement for protecting the purchase flow.",
            "GIVEN a purchase session with bot-like signals, WHEN the detection engine evaluates the "
            "session, THEN the session shall be challenged before purchase completes.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Device-Level Abuse Controls",
            "The system shall limit purchases per device to the configured "
            "allowance.",
            "Device-level abuse controls limit bulk buying from a single source.",
            "GIVEN a device exceeding its purchase allowance, WHEN another purchase is attempted, THEN "
            "the purchase shall be blocked.",
            priority="must",
        ),
        req(
            "FR-003",
            "functional",
            "Purchase API Rate Limiting",
            "The system shall rate-limit requests to the ticketing purchase API "
            "per client.",
            "Rate limiting on the ticketing API is an explicit requirement.",
            "GIVEN a client exceeding the API rate limit, WHEN further requests are made, THEN the "
            "system shall return a rate-limit response.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A purchase-flow protection layer with bot detection and per-device limits.",
        "components": [
            {"name": "Bot Detection Engine", "description": "Scores purchase sessions.", "responsibilities": ["Detect bot signals", "Challenge sessions"]},
            {"name": "Rate Limiter", "description": "Controls API and device usage.", "responsibilities": ["Enforce device limits", "Limit API calls"]},
        ],
        "data_flows": ["Fan -> ticketing platform -> bot detection"],
        "deployment_notes": "Cloud platform with elastic scaling.",
    },
    "threats": [
        {
            "name": "Ticket Scalping",
            "description": "Bots bulk-buy tickets for resale.",
            "category": "Fraud",
            "severity": "high",
            "affected_assets": ["Ticket inventory"],
            "mitigations": [{"description": "Bot detection and device purchase limits.", "related_requirement_ids": ["FR-001", "FR-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Bot detection", "Device controls", "API rate limiting"],
        "out_of_scope": ["Payment processing", "Venue access control"],
    },
    "assumptions": ["Fans use individual devices for purchases."],
    "testing": [
        {"description": "Simulate bot-driven purchase behaviour and verify the challenge.", "type": "security", "related_requirement_ids": ["FR-001"]}
    ],
    "risk": {
        "description": "Aggressive bot controls block fans during on-sale windows.",
        "likelihood": "medium",
        "impact": "high",
        "mitigation": "Challenge-and-verify rather than hard blocks.",
    },
    "unresolved": ["Whether resale platforms should be integrated."],
}


SCN_037: dict[str, Any] = {
    "id": "SCN-037",
    "name": "Stock Trading Bot API Security",
    "description": (
        "A trading firm offers an API for its algorithmic trading clients. They "
        "need mutual TLS between client and server, order size limits per key, "
        "and monitoring of API behaviour for market-abuse signals."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Trading firm", "Algo trading clients", "Market regulator"],
        "assets": [
            "Trading API",
            "Client certificates",
            "Order flow",
            "API behaviour log",
        ],
        "users": ["Client trading systems", "Compliance team", "Platform engineers"],
        "constraints": [
            "Connections must use mutual TLS",
            "Order sizes must be limited per key",
            "API behaviour must be monitored",
        ],
        "goals": [
            "Require mutual TLS",
            "Limit order size per key",
            "Monitor for market-abuse signals",
        ],
        "missing_information": [
            "Client count",
            "Order volume",
            "Monitoring response workflow",
        ],
        "project_summary": (
            "Security hardening for a trading firm's algo-trading API with mutual "
            "TLS, per-key order limits, and market-abuse behaviour monitoring."
        ),
    },
    "clarifications": [
        {"question": "How many clients use the API?", "answer": "Approximately 60 clients."},
        {"question": "What order volume is expected?", "answer": "About 5,000 orders per day."},
        {"question": "Who reviews abuse signals?", "answer": "The compliance team."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Mutual TLS Enforcement",
            "The system shall require mutual TLS between client trading systems "
            "and the API.",
            "Mutual TLS is the explicit connection-security requirement.",
            "GIVEN a client connecting to the API, WHEN the handshake occurs, THEN a client certificate "
            "shall be required for the connection.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Per-Key Order Size Limits",
            "The system shall enforce configurable order size limits for each "
            "API key.",
            "Per-key order limits constrain exposure from any single client key.",
            "GIVEN an order exceeding the key's configured size limit, WHEN the order is submitted, "
            "THEN it shall be rejected.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Market-Abuse Behaviour Monitoring",
            "The system shall flag API behaviour that matches market-abuse "
            "patterns for compliance review.",
            "Monitoring for market-abuse signals is a compliance requirement.",
            "GIVEN API behaviour matching an abuse pattern, WHEN the monitor detects it, THEN a "
            "compliance review ticket shall be created.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": "An mTLS-terminated API gateway with order limits and behaviour monitoring.",
        "components": [
            {"name": "API Gateway", "description": "Terminates mTLS connections.", "responsibilities": ["Verify client certificates", "Enforce order limits"]},
            {"name": "Behaviour Monitor", "description": "Detects abuse patterns.", "responsibilities": ["Flag patterns", "Create tickets"]},
        ],
        "data_flows": ["Client -> API gateway -> order service"],
        "deployment_notes": "Low-latency hosting near the exchange.",
    },
    "threats": [
        {
            "name": "Unauthorised Order Submission",
            "description": "A party without valid certificates submits orders.",
            "category": "Spoofing",
            "severity": "high",
            "affected_assets": ["Order flow"],
            "mitigations": [{"description": "Mutual TLS with certificate verification.", "related_requirement_ids": ["SEC-001"]}],
        }
    ],
    "scope": {
        "in_scope": ["Mutual TLS", "Order limits", "Behaviour monitoring"],
        "out_of_scope": ["Market making", "Order routing to venues"],
    },
    "assumptions": ["Clients manage their own certificates."],
    "testing": [
        {"description": "Attempt a connection without a client certificate and verify refusal.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Order limit misconfiguration blocks legitimate strategies.",
        "likelihood": "low",
        "impact": "high",
        "mitigation": "Limit changes require compliance sign-off.",
    },
    "unresolved": ["Whether latency SLAs must be defined."],
}


SCN_038: dict[str, Any] = {
    "id": "SCN-038",
    "name": "Charity Donation Platform Security",
    "description": (
        "A charity processes online donations and needs to protect donor data. "
        "They want encryption of donor details, protection against payment form "
        "fraud, and a clear record of who accessed donor records."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Charity", "Donors", "Payment partners"],
        "assets": [
            "Donor data",
            "Donation form",
            "Payment gateway integration",
            "Donor access log",
        ],
        "users": ["Donors", "Fundraising staff", "Donor data admins"],
        "constraints": [
            "Donor details must be encrypted",
            "Payment forms must resist fraud",
            "Donor record access must be logged",
        ],
        "goals": [
            "Encrypt donor data",
            "Protect payment forms from fraud",
            "Log donor record access",
        ],
        "missing_information": [
            "Donor base size",
            "Payment gateway",
            "Data sharing policies",
        ],
        "project_summary": (
            "Security for a charity donation platform with encrypted donor data, "
            "payment form fraud protection, and donor access logging."
        ),
    },
    "clarifications": [
        {"question": "How many donors are on record?", "answer": "About 150,000 donors."},
        {"question": "Which payment gateway is used?", "answer": "A hosted card payment gateway."},
        {"question": "Is donor data shared with partners?", "answer": "No sharing without consent."},
    ],
    "requirements": [
        req(
            "SEC-001",
            "security",
            "Donor Data Encryption",
            "The system shall encrypt donor personal details at rest.",
            "Encrypting donor details is the primary data protection requirement.",
            "GIVEN stored donor details, WHEN the storage layer is inspected, THEN the details shall "
            "be found encrypted.",
            priority="must",
        ),
        req(
            "FR-001",
            "functional",
            "Payment Form Fraud Protection",
            "The system shall apply fraud checks to donation form submissions "
            "before processing.",
            "Fraud protection on the payment form is an explicit requirement.",
            "GIVEN a donation form submission with fraud indicators, WHEN the fraud check evaluates "
            "it, THEN processing shall be held pending review.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Donor Access Logging",
            "The system shall log every access to donor records by staff with "
            "user and reason.",
            "Logging staff access to donor records is required for accountability.",
            "GIVEN a staff member accessing a donor record, WHEN the access occurs, THEN a log with "
            "user and reason shall be recorded.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A donation platform with encrypted storage and a fraud-checked payment flow.",
        "components": [
            {"name": "Donation Service", "description": "Processes donations.", "responsibilities": ["Encrypt donor data", "Apply fraud checks"]},
            {"name": "Access Log", "description": "Records donor record access.", "responsibilities": ["Log accesses", "Support audits"]},
        ],
        "data_flows": ["Donor -> donation service -> payment gateway"],
        "deployment_notes": "Cloud-hosted.",
    },
    "threats": [
        {
            "name": "Donor Data Theft",
            "description": "An attacker steals donor personal data.",
            "category": "Data Breach",
            "severity": "high",
            "affected_assets": ["Donor data"],
            "mitigations": [{"description": "Encryption at rest and access logging.", "related_requirement_ids": ["SEC-001", "FR-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Encryption", "Fraud protection", "Access logging"],
        "out_of_scope": ["Card processing", "Fund accounting"],
    },
    "assumptions": ["A hosted gateway handles card data."],
    "testing": [
        {"description": "Verify donor details are encrypted at rest.", "type": "security", "related_requirement_ids": ["SEC-001"]}
    ],
    "risk": {
        "description": "Fraud checks delay legitimate donations during campaigns.",
        "likelihood": "low",
        "impact": "medium",
        "mitigation": "Risk-based hold durations.",
    },
    "unresolved": ["Whether donor consent records are required."],
}


SCN_039: dict[str, Any] = {
    "id": "SCN-039",
    "name": "Hotel Booking Fraud Prevention",
    "description": (
        "A hotel group's booking platform suffers from reservation fraud. They "
        "want risk scoring on bookings, verification of high-risk reservations, "
        "and a fraud review queue for staff."
    ),
    "categories": ["CAT-05", "CAT-07"],
    "analysis": {
        "stakeholders": ["Hotel group", "Guests", "Revenue management"],
        "assets": [
            "Booking platform",
            "Reservation data",
            "Risk engine",
            "Fraud review queue",
        ],
        "users": ["Guests", "Reservations staff", "Fraud analysts"],
        "constraints": [
            "Risk scoring must not reject genuine bookings",
            "High-risk reservations need verification",
            "Fraud reviews must be queue-based",
        ],
        "goals": [
            "Score booking risk",
            "Verify high-risk reservations",
            "Provide a fraud review queue",
        ],
        "missing_information": [
            "Booking volume",
            "Current fraud rate",
            "Verification channel",
        ],
        "project_summary": (
            "Fraud prevention for a hotel booking platform with risk scoring, "
            "verification of high-risk reservations, and a staff review queue."
        ),
    },
    "clarifications": [
        {"question": "What booking volume is processed?", "answer": "About 25,000 bookings per month."},
        {"question": "What is the current fraud rate?", "answer": "Roughly 0.5 percent of bookings."},
        {"question": "How should verification work?", "answer": "Email or SMS confirmation code."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Booking Risk Scoring",
            "The system shall score each booking for fraud risk before "
            "confirmation.",
            "Risk scoring is the core fraud-prevention mechanism requested.",
            "GIVEN a booking submission, WHEN the risk score is computed, THEN the booking shall be "
            "held, confirmed, or queued based on the score.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "High-Risk Reservation Verification",
            "The system shall require verification of high-risk reservations via "
            "a confirmation code before confirmation.",
            "Verification of high-risk reservations is an explicit requirement.",
            "GIVEN a high-risk reservation, WHEN it is submitted, THEN confirmation shall require a "
            "valid verification code.",
            priority="must",
        ),
        req(
            "FR-003",
            "functional",
            "Fraud Review Queue",
            "The system shall present flagged reservations to fraud analysts in "
            "a review queue.",
            "A staff review queue is the stated workflow requirement.",
            "GIVEN a flagged reservation, WHEN it enters the queue, THEN a fraud analyst shall be able "
            "to review and disposition it.",
            priority="must",
        ),
    ],
    "architecture": {
        "overview": "A risk engine in the booking flow with a verification step and review queue.",
        "components": [
            {"name": "Risk Engine", "description": "Scores bookings.", "responsibilities": ["Compute risk", "Route decisions"]},
            {"name": "Verification Service", "description": "Sends confirmation codes.", "responsibilities": ["Issue codes", "Validate submissions"]},
        ],
        "data_flows": ["Guest -> booking platform -> risk engine"],
        "deployment_notes": "Cloud-hosted booking platform.",
    },
    "threats": [
        {
            "name": "Reservation Fraud",
            "description": "Fraudsters book using stolen payment details.",
            "category": "Fraud",
            "severity": "high",
            "affected_assets": ["Reservation data"],
            "mitigations": [{"description": "Risk scoring and verification of high-risk bookings.", "related_requirement_ids": ["FR-001", "FR-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Risk scoring", "Verification", "Review queue"],
        "out_of_scope": ["Payment authorisation", "Property management"],
    },
    "assumptions": ["Email or SMS codes are acceptable verification."],
    "testing": [
        {"description": "Submit a high-risk booking and verify the verification step.", "type": "security", "related_requirement_ids": ["FR-002"]}
    ],
    "risk": {
        "description": "Over-verification creates friction for genuine guests.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Targeted verification only for high-risk scores.",
    },
    "unresolved": ["Whether chargeback signals should feed risk scoring."],
}


SCN_040: dict[str, Any] = {
    "id": "SCN-040",
    "name": "Supply-Chain ERP Access Governance",
    "description": (
        "A manufacturer uses an ERP to run its supply chain. They want automated "
        "review of user access rights, alerts when a user gains unusual "
        "privileges, and clean-up of accounts that are no longer needed."
    ),
    "categories": ["CAT-04", "CAT-07"],
    "analysis": {
        "stakeholders": ["Manufacturer", "ERP administrators", "Internal audit"],
        "assets": [
            "ERP system",
            "User access rights",
            "Role definitions",
            "Access review records",
        ],
        "users": ["ERP users", "Access administrators", "Internal auditors"],
        "constraints": [
            "Access rights must be reviewed automatically",
            "Unusual privilege changes must alert",
            "Obsolete accounts must be cleaned up",
        ],
        "goals": [
            "Automate access-right reviews",
            "Alert on unusual privilege changes",
            "Remove obsolete accounts",
        ],
        "missing_information": [
            "ERP user count",
            "Role model complexity",
            "Review cadence",
        ],
        "project_summary": (
            "Access governance for a manufacturer's supply-chain ERP with "
            "automated reviews, unusual-privilege alerts, and obsolete-account "
            "clean-up."
        ),
    },
    "clarifications": [
        {"question": "How many ERP users are there?", "answer": "About 4,000 users."},
        {"question": "How complex is the role model?", "answer": "Moderately complex with regional roles."},
        {"question": "What review cadence is needed?", "answer": "Quarterly reviews."},
    ],
    "requirements": [
        req(
            "FR-001",
            "functional",
            "Automated Access Review",
            "The system shall run automated access reviews on the configured "
            "cadence and surface discrepancies.",
            "Automated access review is the first governance requirement.",
            "GIVEN the review cadence due, WHEN the review runs, THEN discrepancies shall be presented "
            "for resolution.",
            priority="must",
        ),
        req(
            "FR-002",
            "functional",
            "Unusual Privilege Change Alerts",
            "The system shall alert when a user gains privileges outside their "
            "role pattern.",
            "Alerting on unusual privilege changes is an explicit requirement.",
            "GIVEN a privilege change outside the user's role pattern, WHEN the change is detected, "
            "THEN an alert shall be raised.",
            priority="must",
        ),
        req(
            "FR-003",
            "functional",
            "Obsolete Account Clean-Up",
            "The system shall identify accounts without activity or authorisation "
            "for the configured period and propose removal.",
            "Clean-up of obsolete accounts is the stated governance goal.",
            "GIVEN an account inactive for the configured period, WHEN the clean-up scan runs, THEN the "
            "account shall be proposed for removal.",
            priority="should",
        ),
    ],
    "architecture": {
        "overview": "An access-governance service that consumes ERP role data and drives reviews.",
        "components": [
            {"name": "Governance Engine", "description": "Runs reviews and detects changes.", "responsibilities": ["Run cadenced reviews", "Detect privilege changes"]},
            {"name": "Review Console", "description": "Presents findings to auditors.", "responsibilities": ["Surface discrepancies", "Manage clean-up"]},
        ],
        "data_flows": ["ERP -> governance engine -> review console"],
        "deployment_notes": "Deployed alongside the ERP.",
    },
    "threats": [
        {
            "name": "Privilege Creep",
            "description": "Users accumulate unnecessary ERP privileges over time.",
            "category": "Broken Access Control",
            "severity": "medium",
            "affected_assets": ["User access rights"],
            "mitigations": [{"description": "Automated reviews and unusual-change alerts.", "related_requirement_ids": ["FR-001", "FR-002"]}],
        }
    ],
    "scope": {
        "in_scope": ["Access reviews", "Privilege alerts", "Account clean-up"],
        "out_of_scope": ["ERP application code", "Manufacturing execution systems"],
    },
    "assumptions": ["Quarterly review cadence is appropriate."],
    "testing": [
        {"description": "Create an unusual privilege change and verify the alert.", "type": "security", "related_requirement_ids": ["FR-002"]}
    ],
    "risk": {
        "description": "Review fatigue reduces attention to discrepancies.",
        "likelihood": "medium",
        "impact": "medium",
        "mitigation": "Risk-ranked review queues.",
    },
    "unresolved": ["Whether role changes require two-person approval."],
}


SCENARIOS_B: list[dict[str, Any]] = [SCN_021, SCN_022, SCN_023, SCN_024, SCN_025, SCN_026, SCN_027, SCN_028, SCN_029, SCN_030, SCN_031, SCN_032, SCN_033, SCN_034, SCN_035, SCN_036, SCN_037, SCN_038, SCN_039, SCN_040]
