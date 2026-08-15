# Glossary — CyberSRS

**Version:** 0.1.0-draft
**Date:** 2026-08-07

---

## Software Engineering Terms

| Term | Definition |
|---|---|
| **SRS** | Software Requirements Specification — a structured document describing what a software system must do (functional requirements) and how well it must perform (non-functional requirements). |
| **Functional requirement (FR)** | A requirement that specifies a behaviour or function the system must provide. Example: "The system shall allow the user to create a project." |
| **Non-functional requirement (NFR)** | A requirement that specifies a quality attribute such as performance, usability, reliability, or maintainability. Example: "The system shall respond within 500 ms." |
| **Security requirement (SEC)** | A requirement that specifies how the system must protect data, users, and infrastructure from threats. |
| **Acceptance criterion** | A testable condition that must be satisfied for a requirement to be considered met. |
| **Stakeholder** | Any person or group with an interest in the system being developed (e.g., end users, administrators, sponsors). |
| **Use case** | A description of how a user interacts with the system to achieve a specific goal. |
| **Traceability** | The ability to link each requirement to its origin, test cases, and implementation. |
| **Requirement traceability matrix (RTM)** | A table mapping requirements to their test cases, design elements, or source documents. |
| **MVP** | Minimum Viable Product — the smallest version of the product that delivers core value. |
| **Modular monolith** | An architectural pattern where all components run in a single deployable unit but are internally separated into distinct modules with clear interfaces. |

## Cybersecurity Terms

| Term | Definition |
|---|---|
| **Threat** | A potential event or action that could exploit a vulnerability and cause harm to an asset. |
| **Threat model** | A structured analysis of potential threats to a system, including their likelihood, impact, and mitigations. |
| **Mitigation** | A countermeasure or control that reduces the risk posed by a threat. |
| **STRIDE** | A threat-classification model: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege. |
| **Zero trust** | A security model that requires strict identity verification for every person and device attempting to access resources, regardless of network location. |
| **Network segmentation** | Dividing a network into smaller, isolated segments to limit the blast radius of security incidents. |
| **IDS** | Intrusion Detection System — monitors network traffic for suspicious activity. |
| **IPS** | Intrusion Prevention System — monitors and actively blocks suspicious traffic. |
| **IAM** | Identity and Access Management — systems for managing user identities and controlling access to resources. |
| **VPN** | Virtual Private Network — creates an encrypted tunnel between a user's device and a network. |
| **Firewall** | A network security device or software that monitors and controls incoming and outgoing traffic based on predefined rules. |
| **ACL** | Access Control List — a set of rules that specifies which users or system processes are granted access to objects or resources. |
| **NIST** | National Institute of Standards and Technology — US agency that publishes cybersecurity frameworks and guidelines. |
| **OWASP** | Open Web Application Security Project — a community producing tools, documentation, and standards for web application security. |
| **CIS** | Center for Internet Security — publishes security benchmarks and best practices. |
| **Penetration testing** | Authorised simulated attacks on a system to evaluate its security. CyberSRS does **not** perform penetration testing. |
| **Exploit** | Code or technique that takes advantage of a vulnerability. CyberSRS does **not** execute or generate exploits. |
| **Prompt injection** | An attack where a user crafts input designed to manipulate the behaviour of an LLM beyond its intended instructions. |

## AI, LLM, and RAG Terms

| Term | Definition |
|---|---|
| **LLM** | Large Language Model — a deep-learning model trained on large text corpora to generate and understand natural language. |
| **Qwen3-4B** | The specific LLM used in CyberSRS: Qwen/Qwen3-4B-Instruct-2507, a 4-billion-parameter instruction-tuned model. |
| **Ollama** | A tool for running LLMs locally via a simple CLI and HTTP API. |
| **Inference** | The process of using a trained model to generate predictions or text from input. |
| **Structured output** | LLM output that conforms to a predefined format (e.g., JSON schema) rather than free-form text. |
| **RAG** | Retrieval-Augmented Generation — a technique where relevant information is retrieved from a knowledge base and provided as context to the LLM during generation. |
| **Embedding** | A dense vector representation of text that captures semantic meaning; used for similarity search. |
| **Embedding model** | A model specifically designed to produce embeddings from text. Used for the retrieval step in RAG. Not the main LLM. |
| **Vector database** | A database optimised for storing and querying high-dimensional vectors (embeddings). CyberSRS uses ChromaDB. |
| **ChromaDB** | An open-source, embeddable vector database for building AI applications. |
| **Chunk** | A segment of a larger document, created during ingestion, that is individually embedded and stored for retrieval. |
| **Top-k retrieval** | Retrieving the k most relevant chunks from the vector database based on similarity to a query. |
| **Relevance score** | A numeric score (typically 0–1) indicating how similar a retrieved chunk is to the query. |

## Fine-Tuning Terms

| Term | Definition |
|---|---|
| **Fine-tuning** | The process of further training a pre-trained model on a task-specific dataset to improve its performance on that task. |
| **QLoRA** | Quantised Low-Rank Adaptation — a parameter-efficient fine-tuning technique that uses quantised base weights and trainable low-rank adapter matrices. Reduces memory requirements significantly. |
| **LoRA** | Low-Rank Adaptation — a fine-tuning technique that adds small trainable matrices (adapters) to a frozen pre-trained model. |
| **Adapter** | A small set of trainable parameters added to a pre-trained model during fine-tuning. The base model weights are frozen. |
| **PEFT** | Parameter-Efficient Fine-Tuning — Hugging Face library implementing LoRA, QLoRA, and other efficient fine-tuning methods. |
| **TRL** | Transformer Reinforcement Learning — Hugging Face library for training LLMs with supervised fine-tuning and RLHF. |
| **LoRA rank** | The dimensionality of the low-rank matrices in LoRA. Higher rank = more parameters = more capacity but more compute. |
| **Quantisation** | Reducing model precision (e.g., from float32 to int4) to reduce memory usage and increase inference speed, with some accuracy trade-off. |

## Evaluation Terms

| Term | Definition |
|---|---|
| **Comparative evaluation** | Comparing outputs from two or more models (or configurations) on the same inputs using defined metrics. |
| **Completeness score** | A metric measuring whether all expected SRS sections and fields are present. |
| **Consistency score** | A metric measuring whether generated requirements are internally consistent (no contradictions). |
| **Testability score** | A metric measuring whether generated requirements are verifiable and include measurable criteria. |
| **Schema compliance** | Whether the generated JSON output conforms to the predefined Pydantic or JSON Schema. |
| **BLEU** | Bilingual Evaluation Understudy — an automated metric for evaluating generated text by comparing n-gram overlap with reference text. |
| **ROUGE** | Recall-Oriented Understudy for Gisting Evaluation — an automated metric focusing on recall of n-grams from reference text. |
| **BERTScore** | A metric that uses BERT embeddings to compute similarity between generated and reference text at the token level. |
| **Human evaluation rubric** | A scoring guide used by human evaluators to rate generated output on defined dimensions (e.g., relevance, quality, safety). |

## Project-Specific Terms

| Term | Definition |
|---|---|
| **CyberSRS** | The name of this project — an AI-assisted SRS generation platform for cybersecurity projects. |
| **Project context** | The enriched representation of a user's project after description analysis and clarification. Includes stakeholders, assets, users, constraints, goals, and inferred categories. |
| **Inferred category** | A cybersecurity subdomain (CAT-01 through CAT-08) that the system automatically determines from the user's description. |
| **Clarification question** | A question generated by the system to fill information gaps detected during description analysis. |
| **Generation run** | A single execution of the SRS-generation pipeline, including metadata such as model version, adapter, and timing. |
| **SRS version** | A snapshot of the generated SRS at a point in time. New versions are created on regeneration. |
| **Knowledge ingestion** | The process of parsing, chunking, embedding, and storing cybersecurity documents in ChromaDB. |
| **Provider interface** | An abstract Python class that defines the contract for LLM communication. Concrete implementations (e.g., Ollama) implement this interface. |
| **Corrective prompt** | A follow-up prompt sent to the LLM when its previous output failed schema validation, including the error details and the expected schema. |
