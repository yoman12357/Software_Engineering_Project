# Demonstration Plan — CyberSRS

**Version:** 0.1.0
**Date:** 2026-08-21
**Status:** Executable MVP demonstration

---

## 1. Overview

The demonstration validates CyberSRS end-to-end using three projects from different cybersecurity categories. Each demo runs the full workflow: project creation → description analysis → clarification → RAG retrieval → SRS generation → validation → review → PDF export.

---

## 2. Demo Projects

### 2.1 Demo 1 — College Network Firewall and Monitoring System

| Attribute | Value |
|---|---|
| **Input description** | "I want to build a firewall and network-monitoring system for a college campus. The system should protect approximately 500 nodes across three buildings, monitor traffic for suspicious activity, and alert the IT security team when threats are detected." |
| **Expected inferred subdomain** | CAT-02 (Firewalls and network access control), CAT-03 (Intrusion detection and security monitoring) |
| **Expected clarification questions** | What compliance standards apply? What is the budget? What existing network infrastructure exists? Are there specific traffic types to prioritise? What is the expected bandwidth? Who are the network administrators? |
| **Expected RAG source categories** | NIST SP 800-41 (firewall policy), NIST SP 800-94 (IDS/IPS), CIS Controls (network monitoring), OWASP (if web-based dashboard) |
| **Important generated requirements** | Firewall rule management, traffic monitoring, alert generation, log retention, role-based access to the management console, network segmentation between buildings, reporting dashboard |
| **Expected threat categories** | Spoofing (IP spoofing past firewall), Tampering (rule modification), Information Disclosure (traffic leakage), Denial of Service (firewall bypass/overload) |
| **Success conditions** | (1) Both CAT-02 and CAT-03 inferred. (2) ≥ 3 clarification questions generated. (3) Generated SRS contains FR, NFR, SEC, architecture, threat model, and acceptance criteria. (4) ≥ 1 citation to a retrieved source. (5) PDF exports without errors. (6) All generated JSON passes schema validation. |

### 2.2 Demo 2 — Secure API Gateway

| Attribute | Value |
|---|---|
| **Input description** | "Design a secure API gateway for a fintech startup. The gateway must handle authentication, rate limiting, input validation, and protect against OWASP API Top 10 risks. It should support OAuth 2.0 and API key management." |
| **Expected inferred subdomain** | CAT-05 (Secure web applications and APIs) |
| **Expected clarification questions** | Expected number of API consumers? Internal or external APIs? What backend services are behind the gateway? What data sensitivity level (PCI-DSS)? What performance requirements (requests/second)? |
| **Expected RAG source categories** | OWASP API Security Top 10, OWASP ASVS (authentication, input validation), NIST CSF (Protect function) |
| **Important generated requirements** | OAuth 2.0 implementation, API key lifecycle management, rate limiting per consumer, input validation (schema enforcement), TLS termination, request/response logging, abuse detection, API versioning |
| **Expected threat categories** | Spoofing (stolen API keys), Tampering (request manipulation), Information Disclosure (sensitive data in responses), Elevation of Privilege (broken authorisation), Denial of Service (rate-limiting bypass) |
| **Success conditions** | (1) CAT-05 inferred. (2) ≥ 3 clarification questions. (3) Security requirements reference OWASP API Top 10 risks. (4) Threat model covers at least 3 STRIDE categories. (5) ≥ 1 citation to OWASP source. (6) PDF exports without errors. |

### 2.3 Demo 3 — Identity and Access Management Portal

| Attribute | Value |
|---|---|
| **Input description** | "Build a centralised identity and access management portal for a medium-sized enterprise with 2,000 employees. The system needs single sign-on, multi-factor authentication, role-based access control, user provisioning, and an audit trail." |
| **Expected inferred subdomain** | CAT-04 (Identity and access management) |
| **Expected clarification questions** | Which identity providers to integrate with? What MFA methods? What compliance requirements (SOC 2, ISO 27001)? What existing directory services (LDAP, AD)? Self-service password reset? |
| **Expected RAG source categories** | NIST SP 800-63 (Digital Identity Guidelines), OWASP ASVS (authentication, session management), CIS Controls (account management) |
| **Important generated requirements** | SSO integration, MFA enforcement, RBAC with granular permissions, user provisioning/deprovisioning workflows, audit logging, session management, password policy enforcement, directory integration |
| **Expected threat categories** | Spoofing (credential theft, session hijacking), Repudiation (insufficient audit logging), Information Disclosure (user data leakage), Elevation of Privilege (privilege escalation, insecure direct object reference) |
| **Success conditions** | (1) CAT-04 inferred. (2) ≥ 3 clarification questions. (3) Requirements cover SSO, MFA, RBAC, and audit. (4) Threat model covers credential-based threats. (5) ≥ 1 citation to NIST SP 800-63. (6) PDF exports without errors. |

---

## 3. Demo Execution Procedure

For each demo project:

1. **Create project** — Enter the project name and description.
2. **Verify analysis** — Confirm the inferred subdomain matches expectations.
3. **Answer clarifications** — Provide reasonable answers to critical questions; skip non-critical ones.
4. **Trigger generation** — Start SRS generation and observe progress indicators.
5. **Review SRS** — Verify all sections are present and populated.
6. **Check citations** — Verify source references are displayed.
7. **Edit one requirement** — Modify a requirement inline.
8. **Regenerate one section** — Regenerate the security requirements section.
9. **Validate** — Check validation report and quality score.
10. **Export PDF** — Download and inspect the PDF visually.
11. **Record results** — Document pass/fail for each success condition.

---

## 4. Four-Configuration Demo

For the final evaluation demonstration, each demo project is run in all four configurations:

| Run | Config | Description |
|---|---|---|
| Run A | C1: Base model, no RAG | Baseline quality |
| Run B | C2: Base model + RAG | Impact of retrieved knowledge |
| Run C | C3: Fine-tuned model, no RAG | Impact of fine-tuning |
| Run D | C4: Fine-tuned model + RAG | Full system |

This produces 3 projects × 4 configurations = 12 SRS outputs for comparative evaluation.

---

## 5. Backup Offline Demo Plan

If Ollama or the LLM is unavailable during the demonstration:

### 5.1 Pre-Generated Outputs

Before the demo, generate and save:

1. Complete SRS JSON for all 3 demo projects in all 4 configurations (12 files).
2. Exported PDFs for all 12 runs.
3. Validation reports for all 12 runs.
4. Screenshots of the UI at each workflow step.

### 5.2 Offline Demo Procedure

1. **Show the pre-generated outputs** — Walk through the saved SRS JSON and PDFs.
2. **Show the UI** — Use mocked API responses to demonstrate the UI flow (the frontend can display pre-loaded data even without a live LLM).
3. **Show the evaluation results** — Present the comparison tables from EVALUATION_PLAN.md.
4. **Explain the workflow** — Use USER_WORKFLOW.md diagrams.

### 5.3 Offline Demo Requirements

- Pre-generated SRS JSON files stored in `./data/demo/`.
- Pre-generated PDFs stored in `./data/demo/exports/`.
- Screenshots stored in `./data/demo/screenshots/`.
- The deterministic built-in provider selected with `CYBERSRS_LLM_PROVIDER=mock`.

---

## 6. Demo Success Criteria (Overall)

| Criterion | Requirement |
|---|---|
| All 3 projects complete the full workflow | Mandatory |
| No manual domain selection at any point | Mandatory |
| Generated SRS passes schema validation | Mandatory |
| PDF exports without errors | Mandatory |
| At least 1 citation per project (C2 and C4) | Mandatory |
| Comparative evaluation shows measurable differences between configurations | Mandatory |
| Total demo time per project (with live LLM) | < 15 minutes |
| Backup offline demo is functional | Mandatory |
