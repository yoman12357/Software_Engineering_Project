# CyberSRS

CyberSRS is a local-first AI chat and Software Requirements Specification (SRS) workspace for cybersecurity and network-infrastructure projects. It uses one provider-independent Qwen model interface for ordinary chat and SRS work, with local ChromaDB retrieval when project or domain context is relevant.

## Current capabilities

- General-purpose local chat, including explanations, coding questions, and calculations.
- Intent-aware SRS workflow: project analysis, targeted clarification questions, answer collection, RAG retrieval, validated JSON generation, and deterministic validation.
- Project reference uploads for PDF, Markdown, text, and CSV files.
- Persistent chat history backed by SQLite, including search, rename, pin, delete, and exact session restoration.
- Streaming generation progress with UI cancellation and retry. Cancellation stops client delivery; a synchronous provider call already running on the backend may finish in the background.
- SRS version history, inline requirement editing, deterministic validation, and single-section regeneration into a new version.
- Requirement citations and model-run provenance.
- PDF preview/download plus Markdown and JSON export.
- Local runtime status in Settings for the backend, configured model, RAG, embedding model, and knowledge-base version.

All LLM-generated application artefacts are parsed and validated before they are displayed or persisted. SQLite and ChromaDB data remain local.

## Architecture

| Layer | Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Zustand |
| Backend | Python 3.11+, FastAPI |
| Main LLM | Qwen/Qwen3-4B-Instruct-2507 through an `LLMProvider` interface |
| Local serving | Ollama |
| Database | SQLite |
| Retrieval | ChromaDB with local Ollama embeddings |
| Canonical SRS format | Validated structured JSON |
| Documents | Deterministic JSON-to-PDF/Markdown/JSON export |

QLoRA/fine-tuned model support is configuration-ready through `CYBERSRS_MODEL_VARIANT` and the fine-tuned model name. Training and selecting a production adapter remain separate evaluation/deployment tasks.

## Quick start

### 1. Install dependencies

```powershell
python -m pip install -e ".[dev]"
Copy-Item .env.example .env

Set-Location frontend
npm install
Set-Location ..
```

### 2. Configure the local model

For deterministic development without Ollama, keep:

```text
CYBERSRS_LLM_PROVIDER=mock
```

For the real local model, set these values in `.env`:

```text
CYBERSRS_LLM_PROVIDER=ollama
CYBERSRS_MODEL_VARIANT=base
CYBERSRS_BASE_MODEL_NAME=qwen3:4b-instruct-2507-q4_K_M
CYBERSRS_OLLAMA_BASE_URL=http://localhost:11434
```

Install and start the configured Ollama models:

```powershell
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama pull nomic-embed-text
ollama serve
```

If Ollama is already running as a Windows service, `ollama serve` is not needed.

### 3. Start Ollama, the backend, and the frontend

From the repository root, the combined Windows launcher starts only the services
that are not already running:

```powershell
.\dev.cmd
```

It writes development logs under `data/dev-runtime/logs`. To stop only the
processes that this launcher started:

```powershell
.\dev.cmd -Stop
```

Alternatively, start the applications separately as follows.

Backend, from the repository root:

```powershell
python -m uvicorn src.main:app --reload --port 8000
```

Frontend, in another terminal:

```powershell
Set-Location frontend
npm run dev
```

Open `http://localhost:5173`. The Vite development server proxies `/api` to `http://127.0.0.1:8000`.

Useful checks:

- API health: `http://127.0.0.1:8000/api/v1/health`
- API documentation: `http://127.0.0.1:8000/docs`
- In the application: **Settings → General** shows backend and configured model/RAG status.

ChromaDB telemetry errors from incompatible PostHog packages do not prevent local retrieval, but no project telemetry is intentionally configured or sent by CyberSRS.

## Using the SRS workflow

Enter a detailed request such as:

> Generate an SRS for a zero-trust VPN gateway for a 500-person company. It needs Azure AD, MFA, device posture checks, application-level access policies, 99.9% availability, and GDPR-aligned audit retention.

CyberSRS analyses the statement and asks clarification questions. Answer all questions in the rendered form, or answer in one message using numbered lines:

```text
1. Azure AD is the only identity provider.
2. Support Windows 11 and macOS 15 managed devices.
3. Retain audit logs for 365 days.
4. Target 100 concurrent sessions and 99.9% monthly uptime.
5. Deployment is on-premises with two active nodes.
```

After submission, generation streams progress into the workspace. Validate, edit, regenerate a selected section, inspect sources, switch versions, or export the result.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl/Cmd+N` | New chat |
| `Ctrl/Cmd+K` | Open/focus chat search |
| `Ctrl/Cmd+E` | Export the open SRS as PDF |
| `Ctrl/Cmd+Shift+R` | Regenerate the active SRS section |
| `Ctrl/Cmd+B` | Toggle the sidebar |
| `Escape` | Close the active dialog/workspace state |

## Verification

```powershell
# Backend
python -m pytest -q

# Python lint check
python -m ruff check src tests

# Frontend
Set-Location frontend
npm test -- --run
npm run typecheck
npm run lint
npm run build
```

## Documentation

- [Agent/contributor rules](AGENTS.md)
- [Product requirements](docs/PRD.md)
- [Scope](docs/SCOPE.md)
- [User workflow](docs/USER_WORKFLOW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract](docs/API_CONTRACT.md)
- [Requirements catalogue](docs/REQUIREMENTS_CATALOG.md)
- [Demonstration plan](docs/DEMO_PLAN.md)
- [Roadmap](docs/ROADMAP.md)

## Troubleshooting

- **“Backend could not be reached”**: start Uvicorn on port 8000 and confirm `/api/v1/health` responds.
- **Ollama/model error**: run `ollama list`, verify the tag matches `.env`, and restart the backend after changing configuration.
- **General questions are answered only from RAG**: restart the backend/frontend with the current code; general chat does not require retrieved context, while SRS/domain requests use the SRS workflow and RAG where available.
- **Uploaded file is ignored**: attach it before submitting the project request. Supported files are PDF, Markdown, text, and CSV, subject to the configured local size/count limits.
