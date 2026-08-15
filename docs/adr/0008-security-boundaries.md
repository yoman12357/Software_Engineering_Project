# ADR-0008: Cybersecurity Safety Boundaries

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Project Architect

---

## Context

CyberSRS generates requirements for cybersecurity projects. This creates a tension:

- The system must **understand** cybersecurity threats, attack patterns, and vulnerabilities to produce meaningful threat models and security requirements.
- The system must **never** produce executable attack tools, exploit code, malware, or active offensive capabilities.

Without explicit boundaries, a requirements-generation system could:
1. Generate requirements that describe how to build attack tools (misuse of the SRS format).
2. Include working exploit code in requirement descriptions or acceptance criteria.
3. Suggest active penetration testing, vulnerability scanning, or attack execution as part of the generated system.
4. Be used by a malicious user to systematically enumerate attack techniques under the guise of "requirements."

## Decision

CyberSRS enforces the following **hard safety boundaries**:

### Hard Prohibitions — The System Shall Never:

| ID | Prohibition | Enforcement Mechanism |
|---|---|---|
| SB-01 | Perform active penetration testing or vulnerability scanning against live systems. | Not implemented in code; not suggested in generated requirements. |
| SB-02 | Execute exploits, malware, or attack payloads. | No code execution capability; no shell access. |
| SB-03 | Generate executable exploit code in requirements, acceptance criteria, or any output. | SEC-025 exploit-pattern scanning; validation report flags. |
| SB-04 | Modify network configurations, firewall rules, or system settings automatically. | No network or system-management capabilities. |
| SB-05 | Store or transmit credentials, API keys, or secrets in plain text within the codebase. | SEC-029, SEC-030; `.env` file in `.gitignore`. |
| SB-06 | Suggest executable attack code in generated requirements. | SEC-025 pattern scanning; prompt instructions prohibit offensive output. |
| SB-07 | Transmit any data to external services. | SEC-008, SEC-009; localhost-only binding; no external network calls. |

### Allowed — The System May:

| ID | Permission | Rationale |
|---|---|---|
| SA-01 | Describe threats using STRIDE categories. | Threat modelling requires describing *what* could go wrong. |
| SA-02 | Reference ATT&CK techniques by name and ID. | Citing known techniques is standard practice in threat modelling. |
| SA-03 | Generate defensive security requirements (authentication, encryption, logging, access control). | This is the core purpose of the system. |
| SA-04 | Describe mitigations for identified threats. | Defensive guidance is always permitted. |
| SA-05 | Cite OWASP, NIST, CIS, and MITRE publications. | Public reference material for security guidance. |
| SA-06 | Describe attack scenarios at a conceptual level in the threat model. | Threat descriptions like "An attacker could exploit SQL injection" are informational, not actionable exploits. |

### Boundary Test — How to Distinguish Allowed vs. Prohibited:

| Question | If Yes → | If No → |
|---|---|---|
| Does the output describe *how to defend* against a threat? | Allowed (SA-03, SA-04) | Check next |
| Does the output describe *what* a threat is (conceptually)? | Allowed (SA-01, SA-06) | Check next |
| Does the output provide *working code* to exploit a vulnerability? | **Prohibited (SB-03, SB-06)** | Allowed |
| Does the output instruct the user to *execute an attack*? | **Prohibited (SB-01, SB-02)** | Allowed |
| Does the output suggest *building an offensive tool*? | **Prohibited (SB-03)** | Allowed |

## Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| **No safety boundaries (trust the user)** | Irresponsible. The system should not produce weaponisable output regardless of user intent. |
| **Block all threat descriptions** | Overly restrictive. Threat modelling is a core feature and requires describing threats. |
| **LLM-based safety filter** | Adds latency and another failure mode. Not reliable enough for safety-critical filtering. Better to use deterministic pattern scanning + prompt design. |
| **Allow offensive requirements for "red team" projects** | Exceeds MVP scope and creates ambiguity about what is permitted. |

## Consequences

### Positive
- **Clear safety posture.** Every contributor (human or AI agent) knows exactly what is prohibited.
- **Deterministic enforcement.** SEC-025 pattern scanning is a rule-based check, not an LLM judgment.
- **Academic integrity.** The project can be presented without concern about producing harmful output.
- **User trust.** Users know the tool produces defensive guidance, not offensive capabilities.

### Negative
- **False positives.** The exploit-pattern scanner (SEC-025) may flag legitimate defensive requirements that use terms like "injection" or "exploit." Mitigated by flagging (not blocking) and allowing user review.
- **Subtle misuse.** A determined user could rephrase an offensive goal as a defensive one. Mitigated by the fact that the output is requirements text, not executable code.

### Neutral
- These boundaries apply to the MVP. Post-MVP could add a supervised "red team requirements" mode with explicit warnings and additional safeguards, but this is not planned.
