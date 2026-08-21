# Scope Definition — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07
**Status:** Phase 0 — Planning

---

## 1. MVP Scope

The Minimum Viable Product delivers a locally deployable, end-to-end workflow where a single user can produce a professional SRS document for a cybersecurity project.

### 1.1 Included in MVP

| Area | What is included |
|---|---|
| **Project management** | Create, list, open, update, and delete projects. |
| **Description analysis** | Accept an informal description; analyse it with the main LLM; infer cybersecurity subdomain(s) automatically. |
| **Information extraction** | Extract stakeholders, assets, users, constraints, and goals from the description. |
| **Missing-information detection** | Identify gaps in the description and generate clarification questions. |
| **Clarification workflow** | Present questions to the user; accept answers; incorporate answers into the project context. |
| **RAG retrieval** | Ingest cybersecurity documents into ChromaDB; retrieve top-k relevant chunks during generation; preserve source metadata. |
| **SRS generation** | Generate functional requirements, non-functional requirements, cybersecurity requirements, high-level architecture, threat model, acceptance criteria, and testing recommendations — all as validated JSON. |
| **Requirement validation** | Validate completeness, testability, and basic consistency of generated requirements. |
| **Review and editing** | Display the SRS in a section-by-section UI; allow inline editing; allow section-level regeneration. |
| **Source references** | Display which retrieved chunks informed each generated section. |
| **PDF export** | Generate a professional PDF from the validated JSON structure. |
| **Fine-tuning** | Prepare a dataset; perform QLoRA fine-tuning of the main LLM; load the adapter at inference time. |
| **Evaluation** | Compare base-model output against fine-tuned output on a reference dataset. |
| **Local-first deployment** | All components (frontend, backend, LLM, ChromaDB, SQLite) run on a single machine. |
| **Conversational assistant** | General cybersecurity questions, RAG-grounded answers with citations, and explicit handoff from a preserved project description into the SRS workflow. |
| **Task-aware model routing** | Use the base Qwen model for general chat and the configured base/fine-tuned Qwen variant only for requirements-engineering tasks. |
| **Project reference documents** | Upload, parse, list, use, and delete project-scoped PDF, Markdown, text, and CSV files within local safety limits. |

### 1.2 MVP Technical Boundaries

| Constraint | Detail |
|---|---|
| Single user | No authentication, no multi-tenancy. |
| SQLite | No migration to PostgreSQL in MVP. |
| Single LLM | Qwen/Qwen3-4B-Instruct-2507 only. |
| Ollama | Local model serving via Ollama behind a provider-independent interface. |
| Single embedding model | One embedding model for ChromaDB (to be selected). |
| English only | All prompts, knowledge base, and generated output are in English. |
| Consumer hardware | Must run on a machine with ≥ 8 GB RAM; GPU recommended but not required. |

---

## 2. Post-MVP Scope

These features are planned for future phases but are **not** part of the MVP.

| ID | Feature | Rationale for deferral |
|---|---|---|
| POST-01 | Multi-user collaboration and role-based access | Requires authentication and conflict resolution |
| POST-02 | PostgreSQL or other production database | SQLite is sufficient for single-user MVP |
| POST-03 | Additional cybersecurity project categories | Focus on the initial eight categories first |
| POST-04 | Non-cybersecurity project domains | Out of project scope; CyberSRS is cybersecurity-focused |
| POST-05 | Cloud-hosted deployment | Contradicts local-first principle for MVP |
| POST-06 | Multi-language SRS generation | English is sufficient for MVP |
| POST-07 | Integration with issue trackers (Jira, GitHub Issues) | Adds external dependencies |
| POST-08 | Interactive threat-model diagram editor | Visual tooling is complex; defer |
| POST-09 | Compliance mapping to specific standards | Requires extensive curated data |
| POST-10 | Version-diff visualisation | Nice-to-have; defer |
| POST-11 | Automated requirement-priority suggestions | Research-intensive; defer |
| POST-12 | Multiple LLM provider support | Interface is designed for it, but only Ollama is implemented in MVP |

---

## 3. Explicitly Out of Scope

The following are **permanently** out of scope for CyberSRS and must not be implemented in any phase.

### 3.1 Dangerous Cybersecurity Functionality

| Exclusion | Rationale |
|---|---|
| Active penetration testing | Safety risk; legal liability |
| Exploit execution | Safety risk; legal liability |
| Malware execution or analysis in a sandbox | Safety risk; out of project purpose |
| Automatic network modification (firewall rules, routing, ACLs) | Safety risk; potential for damage |
| Generation of executable attack code | Safety risk |
| Vulnerability scanning of live systems | Requires authorised access; out of scope |

### 3.2 Operational Security Functions

| Exclusion | Rationale |
|---|---|
| Real-time network monitoring | CyberSRS generates *requirements* for such systems; it does not *implement* them |
| Security-incident response automation | Same as above |
| SIEM integration | Same as above |

### 3.3 General Exclusions

| Exclusion | Rationale |
|---|---|
| Automated code generation from requirements | Out of scope; CyberSRS produces documentation, not code |
| Formal verification of requirements | Requires specialised solvers; not feasible in MVP |
| Training-data collection from user projects | Privacy concern; all training data must be prepared separately |
| Model training on user data without explicit consent | Privacy concern |

---

## 4. Supported Cybersecurity Project Categories

These categories are **inferred** from the user's informal description. The user never manually selects a category.

| ID | Category | Example descriptions |
|---|---|---|
| CAT-01 | Network security systems | "Build a system to monitor and secure a corporate network" |
| CAT-02 | Firewalls and network access control | "Design a firewall for a university campus" |
| CAT-03 | Intrusion detection and security monitoring | "Create an IDS for our data-centre traffic" |
| CAT-04 | Identity and access management (IAM) | "Build a single sign-on and role-based access system" |
| CAT-05 | Secure web applications and APIs | "Develop a secure REST API with OWASP compliance" |
| CAT-06 | VPN and secure remote-access systems | "Set up a VPN solution for remote employees" |
| CAT-07 | Security logging and alerting | "Build a log aggregation and alerting platform" |
| CAT-08 | Network segmentation and zero-trust-oriented systems | "Implement zero-trust network segmentation for our office" |

### Descriptions spanning multiple categories

When a user's description spans multiple categories (e.g., "firewall and IDS"), the system shall infer all relevant categories and generate requirements covering each.

---

## 5. Unsupported Project Categories (MVP)

| Category | Status |
|---|---|
| Cryptography libraries | Unsupported — not in initial category list |
| IoT security | Unsupported — deferred to post-MVP |
| Cloud-native security (CSPM, CWPP) | Unsupported — deferred |
| Mobile-application security | Unsupported — deferred |
| Operational technology (OT/SCADA) security | Unsupported — deferred |
| Physical security systems | Unsupported — out of scope (not software) |
| Non-cybersecurity software projects | Permanently unsupported |

When the system detects an unsupported category, it shall inform the user and explain which categories are supported.

---

## 6. Technical Boundaries

| Boundary | Detail |
|---|---|
| No microservices | The MVP is a modular monolith. |
| No external API calls | Except to the locally hosted Ollama instance. |
| No Docker requirement | Docker may be documented as optional for convenience but must not be required. |
| No GPU requirement | GPU is recommended but the application must function on CPU-only machines. |
| No custom model training from scratch | Only QLoRA fine-tuning of the pre-trained Qwen model. |
| No real-time streaming UI in MVP | Streaming may be added post-MVP; MVP uses polling or simple progress indicators. |

## 7. Safety Boundaries

1. The application must never generate content that could be used to attack or compromise a system.
2. The application must never access the user's network, file system (beyond its own data directory), or operating-system configuration.
3. All LLM output is advisory — the application must not present generated requirements as certified or formally verified.
4. The application must include a disclaimer in the generated PDF stating that the document is AI-generated and should be reviewed by a qualified professional.

## 8. Academic-Project Boundaries

CyberSRS is initially developed as a student academic project. This means:

| Constraint | Implication |
|---|---|
| Single developer | Scope must be achievable by one person within a semester. |
| Academic evaluation | The project must demonstrate research contributions (fine-tuning, evaluation, RAG for RE). |
| Dataset size | The fine-tuning dataset may be small (hundreds of examples); this is acceptable for the MVP. |
| Evaluation rigour | Comparative evaluation must be documented but need not match industry benchmarks. |
| Documentation emphasis | Thorough documentation is a deliverable, not an afterthought. |
