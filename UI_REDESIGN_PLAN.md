# CyberSRS UI Redesign Plan

Review status: draft for approval before implementation.

This plan is only for the React/Vite frontend. It must preserve the existing FastAPI backend, Ollama/Qwen configuration, RAG pipeline, ChromaDB index, evaluation artifacts, and API contracts.

## 1. Goal

Redesign CyberSRS into a polished chatbot-style product for cybersecurity SRS generation.

The final UI should feel like a serious university/research software product: calm, modern, readable, accessible, and clearly cybersecurity-oriented. It should preserve the current workflow:

```text
Project description
-> project creation
-> analysis
-> clarification questions
-> clarification answer submission
-> SRS generation
-> SRS viewing/editing
-> citations and generation metadata
```

## 2. Non-Goals

Do not do any of the following during this UI work:

- Rebuild RAG.
- Rerun real-model evaluations unless a UI bug requires a very small manual smoke.
- Modify Qwen/Ollama model settings.
- Modify embedding, ChromaDB, retrieval, citation validation, or SRS generation logic.
- Change backend API behavior unless a tiny frontend compatibility fix is unavoidable.
- Implement QLoRA or any fine-tuning work.
- Mock AI output or hard-code project analysis/SRS data.
- Replace Vite with Next.js.
- Replace FastAPI.

## 3. Current Frontend Inventory

The repository already contains much of the intended redesign scaffold. The old plan was too greenfield.

Current stack:

- React 18
- TypeScript
- Vite 6
- Tailwind CSS
- CSS variable theme tokens
- Zustand
- Lucide React
- Framer Motion
- Vitest, jsdom, React Testing Library

Current package scripts:

```text
npm run dev
npm run build
npm run test
npm run typecheck
npm run lint
```

Current frontend structure already present:

```text
frontend/src/
  api/
    client.tsx
    types.tsx
  components/
    chat/
    layout/
    rag/
    settings/
    srs/
    ui/
  hooks/
  stores/
  test/
  App.tsx
  index.css
```

Important existing files to preserve and improve:

- `frontend/src/api/client.tsx`: single typed API client. Components should not bypass it with raw fetch calls.
- `frontend/src/hooks/useChat.ts`: current workflow orchestration.
- `frontend/src/hooks/useProjects.ts`: project list/selection integration.
- `frontend/src/stores/chatStore.tsx`: chat-stage state.
- `frontend/src/stores/projectStore.tsx`: project history state.
- `frontend/src/stores/themeStore.tsx`: theme state.
- `frontend/src/components/layout/AppShell.tsx`: app shell entry point.
- `frontend/src/components/chat/*`: conversational UI components.
- `frontend/src/components/srs/*`: SRS workspace components.
- `frontend/src/components/rag/*`: source/citation display components.
- `frontend/src/components/settings/*`: settings and theme UI.
- `frontend/src/components/ui/*`: local shadcn-like primitives.

## 4. Current Risks Found During Plan Audit

These are review items before any visual polish:

1. `App.tsx` has basic chat flow, but stage rendering appears inconsistent:
   - `ProjectAnalysisCard` is shown during `analyzing`, even analysis may still be null.
   - Analysis and clarification also appear as chat messages, so duplication risk exists.
   - `showSRSWorkspace` exists but no visible path in the inspected `App.tsx` sets it to true.

2. Project restoration needs careful review:
   - `loadExistingProject` currently reruns analysis instead of restoring latest known state from existing context/SRS where possible.
   - The sidebar should not create fake examples when real projects exist.

3. Composer behavior needs review:
   - New project creation from suggested prompts immediately starts the backend workflow.
   - Requirement says suggested prompts should populate the composer first, not necessarily auto-submit.

4. RAG/source UI likely needs data mapping verification:
   - SRS `generation_metadata` and requirement `source_references` must be displayed without exposing noisy chunk internals by default.

5. Theme system exists, but must be verified for:
   - light/dark/system behavior,
   - localStorage persistence,
   - no flash on load,
   - accessible contrast.

6. Accessibility needs explicit pass:
   - icon-only button labels,
   - focus states,
   - dialog focus behavior,
   - keyboard navigation,
   - mobile drawer behavior.

## 5. Design Direction

Use the supplied palette as identity, not as full-page pastel decoration.

Primary palette:

```text
#141414
#FFFFFF
#DCF0FF
#F0F0FF
#C8DCF0
#DCF0F0
```

Light theme:

- background: `#F8FAFC`
- primary surface: `#FFFFFF`
- text: `#141414`
- secondary text: `#5F6873`
- muted text: `#7B8490`
- border: `#DCE4EA`
- primary action: `#3B6F9E`
- primary hover: `#315F88`
- selected nav: `#DCF0FF`
- assistant surfaces: soft blue/cyan tones
- user messages: strong blue with white text

Dark theme:

- background: `#141414`
- sidebar: `#181818`
- primary surface: `#1D1E20`
- elevated surface: `#242629`
- text: `#F7F9FB`
- secondary text: `#C7CDD4`
- muted text: `#9199A3`
- border: `#34383D`
- accent: `#9BC7E8`
- user messages: `#315F88`
- assistant messages: `#1D2328`

Style rules:

- Use semantic tokens, not scattered hex values.
- Keep radius around 10-14px.
- Avoid giant nested cards.
- Avoid neon hacker styling, matrix effects, decorative blobs, and excessive gradients.
- Use Lucide icons for controls.
- Use subtle motion only where it improves comprehension.

## 6. Target Information Architecture

Desktop:

```text
AppShell
  Sidebar
    Brand
    New Project
    Project history
    Settings / theme
  Main Workspace
    Chat thread or welcome state
    Sticky composer
    Optional SRS workspace panel/route
```

Mobile:

```text
Top bar
Sidebar drawer
Full-width chat
Sticky composer
SRS workspace full-screen or stacked below chat
```

## 7. Desired User Workflow

### 7.1 Empty State

When no project is active:

- Show CyberSRS brand.
- Show concise tagline:
  - "Turn cybersecurity ideas into complete software requirements."
- Show short explanation.
- Show suggested prompts.
- Clicking a suggested prompt should populate the composer first. Auto-submit should only happen if we explicitly approve that behavior.

### 7.2 Project Start

User submits a cybersecurity project description.

UI should:

- Create the project using the existing API.
- Add the user prompt to the chat thread.
- Show a non-fake status such as "Analyzing project...".
- Call the existing analysis endpoint.

### 7.3 Analysis Result

Assistant displays a structured Project Analysis card:

- inferred categories as badges,
- summary,
- stakeholders,
- assets,
- user roles,
- constraints,
- goals,
- missing information.

Do not display raw JSON.

### 7.4 Clarifications

If clarifications exist:

- Display compact question cards inside the conversation.
- Show Required/Optional badges.
- Show "Why I am asking" text.
- Allow answering multiple questions and submitting together, matching the current backend API.

### 7.5 SRS Generation

During generation:

- Show one honest generic state if backend progress is not exposed.
- Do not show fake percentages.
- Suggested text:
  - "Generating your SRS with Qwen and the security knowledge base..."

### 7.6 Completion

After SRS generation:

- Show a completion card with counts:
  - functional requirements,
  - security requirements,
  - non-functional requirements,
  - threats,
  - cited sources if available.
- Provide:
  - View SRS,
  - Edit Requirements,
  - Export PDF disabled if not supported.

### 7.7 SRS Workspace

The SRS workspace should use tabs:

- Overview
- Functional
- Security
- Non-Functional
- Data/Network
- Threats
- Sources

Each requirement should show:

- ID,
- priority,
- statement,
- rationale,
- acceptance criteria,
- citations.

Editing should preserve:

- requirement ID,
- category,
- priority,
- statement,
- rationale,
- acceptance criteria,
- citations unless backend intentionally changes them.

## 8. Implementation Phases After Approval

Do not start these until this plan is reviewed.

### Phase A: Validation Audit

Purpose: understand what currently works before changing visuals.

Tasks:

- Run `npm run typecheck`.
- Run `npm run lint`.
- Run `npm run test`.
- Run `npm run build`.
- Inspect browser in light and dark mode.
- Record current UI issues in a short checklist.

Exit criteria:

- Known current failures are documented.
- No backend code is changed.

### Phase B: Design System Hardening

Purpose: make existing primitives consistent before rewriting screens.

Tasks:

- Audit `frontend/src/components/ui/*`.
- Standardize button, card, input, textarea, badge, dialog, tabs, toast, skeleton, tooltip, and theme toggle variants.
- Confirm all components use CSS variables/Tailwind semantic classes.
- Remove hard-coded colors from React components where practical.
- Verify theme persistence and system mode.

Exit criteria:

- Light/dark/system theme works.
- No theme flash or obvious contrast issues.
- UI primitives are reusable and documented by examples or tests.

### Phase C: App Shell and Project History

Purpose: stabilize navigation and project lifecycle.

Tasks:

- Improve `AppShell`.
- Verify sidebar collapse/drawer behavior.
- Load real project history from API/store.
- Support selecting a project without unintentionally rerunning analysis if a generated SRS already exists.
- Add polished settings dialog entry points.
- Ensure mobile drawer has proper labels and focus behavior.

Exit criteria:

- Desktop sidebar works at 1024px and 1440px.
- Mobile drawer works at 375px and 768px.
- Project selection restores the best available project state.

### Phase D: Chat Workflow Polish

Purpose: make the existing backend workflow feel conversational.

Tasks:

- Clean up stage rendering in `App.tsx` and `useChat`.
- Avoid duplicated analysis/clarification displays.
- Make suggested prompts populate the composer unless auto-submit is approved.
- Improve user message and assistant message layouts.
- Add honest loading states and useful error messages.
- Add clarifications as compact cards inside the chat thread.

Exit criteria:

- Project creation -> analysis -> clarification -> generation -> SRS completion works through the UI.
- No fake AI data is introduced.
- Error messages are user-friendly and do not expose stack traces.

### Phase E: SRS Workspace Polish

Purpose: make generated SRS documents readable and editable.

Tasks:

- Improve `frontend/src/components/srs/*`.
- Add/verify SRS workspace entry from completion card.
- Add requirement tabs and source/citation display.
- Improve requirement editing presentation.
- Keep PDF export disabled if backend export is unavailable.
- Add generation details disclosure:
  - model,
  - RAG enabled,
  - retrieved chunks,
  - embedding model,
  - generation time if available.

Exit criteria:

- SRS can be opened from chat.
- Requirements are grouped and readable.
- Citations are visible as chips and expandable into source details.

### Phase F: RAG and Source UI

Purpose: make RAG visible without overwhelming normal users.

Tasks:

- Display source chips for requirement citations.
- Add source drawer/popover using available metadata.
- Show technical chunk IDs only inside a disclosure.
- Show retrieval summary from generation metadata where available.

Exit criteria:

- Users can see that trusted sources informed requirements.
- Internal chunk details are hidden by default.

### Phase G: Responsive and Accessibility Pass

Purpose: final UI quality pass.

Tasks:

- Test 375px, 768px, 1024px, and 1440px.
- Check no horizontal overflow.
- Check keyboard navigation.
- Check visible focus states.
- Check labels for icon-only buttons.
- Check dialog focus handling.
- Check contrast in light and dark themes.
- Respect `prefers-reduced-motion`.

Exit criteria:

- No obvious mobile layout breakage.
- App is usable with keyboard.
- Focus states are visible.

### Phase H: Tests and Build

Purpose: prove the UI changes did not break the workflow.

Required commands:

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

Python regression tests are only required if shared backend/API files are touched:

```bash
python -m pytest -q --basetemp .pytest-tmp-ui
```

Recommended frontend tests:

- theme switching,
- theme persistence,
- suggested prompt fills composer,
- project creation happy path with mocked fetch,
- clarification form rendering and submission,
- generation loading state,
- SRS completion card rendering,
- SRS workspace rendering,
- citation/source chip rendering,
- user-friendly error rendering.

## 9. Dependency Policy

Already present dependencies should be reused:

- Tailwind CSS
- Zustand
- Lucide React
- Framer Motion
- clsx
- tailwind-merge
- cmdk

Do not add new dependencies unless a specific gap is proven.

Do not add assistant-ui unless we first confirm it fits the custom FastAPI workflow without forcing a rewrite.

## 10. File Ownership

Frontend files allowed for this UI redesign:

```text
frontend/package.json
frontend/package-lock.json
frontend/index.html
frontend/vite.config.ts
frontend/tsconfig.json
frontend/tailwind.config.*
frontend/postcss.config.*
frontend/src/**
```

Documentation files allowed:

```text
UI_REDESIGN_PLAN.md
docs/*UI* or docs/*FRONTEND* if needed
```

Avoid backend files unless a tiny API compatibility issue is discovered and approved.

Do not modify:

```text
src/llm/**
src/rag/**
src/services/**
src/db/**
src/prompts/**
ai/evaluation/results/eval-20260809-204147-548eb018/**
```

## 11. Review Questions Before Implementation

Please review and decide:

1. Should suggested prompt clicks only fill the composer, or should they auto-create a project?
2. Should SRS open as a right-side workspace panel or a dedicated full-screen workspace?
3. Should project selection restore latest generated SRS first, instead of rerunning analysis?
4. Should PDF export remain disabled until backend export is confirmed?
5. Should the UI keep Framer Motion, or avoid animation except CSS transitions?
6. Should we add assistant-ui later, or keep the current custom chat components?

## 12. Final Acceptance Checklist

Implementation is complete only when:

- Existing backend workflow still works.
- No backend AI/RAG/evaluation logic is changed.
- Light, dark, and system themes work and persist.
- Chat workflow is clear and non-duplicative.
- Clarification UI supports current backend multi-answer submission.
- SRS workspace opens and displays grouped requirements.
- Requirement editing preserves citations unless backend changes them.
- RAG/source citations are visible and expandable.
- UI is usable at 375px, 768px, 1024px, and 1440px.
- Icon-only buttons have accessible labels.
- Loading and error states are user-friendly.
- `npm run typecheck` passes.
- `npm run lint` passes.
- `npm run test` passes.
- `npm run build` passes.

## 13. Recommended Next Step

After this plan is approved, start with Phase A only: run the frontend validation audit and produce a short issue list. Do not jump directly into broad redesign edits until the current scaffold is verified.
