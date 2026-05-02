# AutoFlow — Team Context Document

> **Version:** 1.0.0 · **Last updated:** 2026-05-02 · **Status:** Active development
>
> This document is the single source of truth for all four teammates. Read it fully before writing any code.
> Update it when decisions change — a stale context doc is worse than none.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Feature List](#2-feature-list)
3. [Voice Feature Spec](#3-voice-feature-spec) ← new core feature
4. [Tech Stack](#4-tech-stack)
5. [Canonical Workflow Schema](#5-canonical-workflow-schema)
6. [File & Folder Structure](#6-file--folder-structure)
7. [FastAPI Endpoint Contracts](#7-fastapi-endpoint-contracts)
8. [LangGraph Agent Nodes](#8-langgraph-agent-nodes)
9. [Team Assignments](#9-team-assignments)
10. [Coding Conventions](#10-coding-conventions)
11. [Build & Run Instructions](#11-build--run-instructions)
12. [Git Workflow](#12-git-workflow)
13. [UX Design Principles](#13-ux-design-principles)
14. [Open Questions](#14-open-questions)

---

## 1. Project Overview

**AutoFlow** is a local-first desktop automation platform for non-technical users. A user describes a task in plain English (or by speaking it) — the tool executes it using browser control, desktop control, or terminal commands — asks for human confirmation at key moments — and saves the entire workflow so it can be rerun or shared with a single click.

### Core Philosophy

- **Local first.** Everything runs on the user's machine. No account needed, no data leaves unless the user explicitly shares a workflow.
- **Workflow library is the product.** The automation engine exists to populate and run a personal library of saved tasks.
- **Non-technical audience.** Every decision — naming, layout, error messages, feature design — must pass the test: "Can a 60-year-old who has never used automation software use this without reading a manual?"
- **Voice as a first-class input.** Users should be able to speak their task instead of typing it. This reduces friction especially for the target demographic.

---

## 2. Feature List

| # | Feature | Priority | Owner |
|---|---------|----------|-------|
| 1 | Browser control via `browser-use` | P0 | Person 1 |
| 2 | Desktop control via PyAutoGUI + Agent-S | P0 | Person 1 |
| 3 | Terminal execution | P0 | Person 1 |
| 4 | **Workflow saving, running, and sharing** | P0 — main theme | Person 2 + 4 |
| 5 | **Voice input + output** | P0 | Person 1 + 3 |
| 6 | Human-in-the-loop (HITL) approval dialogs | P0 | Person 1 + 3 |
| 7 | Browser extension workflow recorder | P1 | Person 4 |
| 8 | JSON export / import | P0 | Person 4 |
| 9 | Link-based workflow sharing | P1 | Person 4 |
| 10 | Reusable workflow inputs (variables) | P1 | Person 2 |

---

## 3. Voice Feature Spec

Voice is a **P0 feature**, not an add-on. It has two directions: input (user speaks a task) and output (tool speaks status back to the user).

### 3.1 Voice Input

The user presses a microphone button and speaks their task. The spoken text is transcribed and fed into the agent exactly as if the user had typed it.

**How it works:**

```
User presses mic button
  → Frontend captures audio via Web Speech API (SpeechRecognition) or Whisper
  → Transcribed text is shown in the task input field (editable before submitting)
  → User confirms or edits
  → Submitted to FastAPI → LangGraph as normal task text
```

**Implementation decision — two options, pick one early:**

| Option | Library | Runs where | Accuracy | Requires internet |
|--------|---------|-----------|----------|-------------------|
| A — Web Speech API | Browser built-in | Electron renderer | Medium | Yes (Chrome sends to Google) |
| B — Whisper (local) | `openai-whisper` Python | FastAPI backend | High | No |

**Recommended: Option B (Whisper).** Fits the local-first philosophy. Use the `base` model for speed on consumer hardware. The Electron frontend records audio and sends a WAV blob to `POST /voice/transcribe`. FastAPI runs Whisper and returns the text.

**Fallback:** If Whisper is too slow on the user's machine (>3s for short phrases), fall back to Option A for MVP and add a settings toggle.

**Frontend contract:**

```
User holds mic button → record audio (MediaRecorder API, WAV)
On release → POST /voice/transcribe with audio blob
Response: { "text": "Book me a flight to Mumbai on Friday" }
Insert text into task input field
```

### 3.2 Voice Output

The tool reads status updates and HITL prompts aloud so the user does not have to watch the screen during long-running tasks.

**Scope — what gets spoken:**

- Task start confirmation: `"Starting: Book a flight to Mumbai."`
- Step completions (summarised, not every action): `"I've opened the flights page and found three options."`
- HITL prompts: `"I need your help. Which flight should I book — the 6am or the 2pm?"`
- Task completion: `"Done. I've saved this as a workflow called Book a Flight."`
- Errors: `"Something went wrong on step 3. Please check the screen."`

**What does NOT get spoken:**

- Internal agent reasoning
- Raw error stack traces
- Every micro-action (clicking buttons, filling fields)

**Implementation:**

```python
# server/voice/speaker.py
# FastAPI sends speech events over the existing WS /ws/execution/{id}
# Event type: "speech"

{
  "type": "speech",
  "text": "I need your help. Which flight should I book?",
  "priority": "high"   # high = interrupt current speech, normal = queue
}
```

```typescript
// app/src/hooks/useVoice.ts
// Frontend listens for "speech" events on the execution WebSocket
// Uses Web Speech API (SpeechSynthesis) to speak — no external dependency needed for output

const synth = window.speechSynthesis;

function speak(text: string, priority: "high" | "normal") {
  if (priority === "high") synth.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = userSettings.speechRate; // configurable: 0.8–1.4
  synth.speak(utterance);
}
```

**User settings for voice (in Settings panel):**

| Setting | Default | Options |
|---------|---------|---------|
| Voice input method | Whisper (local) | Whisper / Browser |
| Voice output enabled | On | On / Off |
| Speech rate | 1.0 | 0.8 / 1.0 / 1.2 / 1.4 |
| Speak HITL prompts | On | On / Off |
| Speak step summaries | On | On / Off |

### 3.3 Voice + HITL Integration

When the agent hits a HITL pause and voice output is enabled, the tool does three things simultaneously:
1. Speaks the prompt aloud
2. Shows the HITL dialog on screen
3. Optionally activates the microphone for a voice response

Voice responses to HITL are transcribed and submitted the same way as task input. The agent receives plain text — it does not need to know the input came from voice.

### 3.4 Whisper Setup

```bash
pip install openai-whisper
# Downloads ~140MB base model on first use (cached locally after)
# Model is stored in ~/.cache/whisper/
```

```python
# server/voice/transcribe.py
import whisper
model = whisper.load_model("base")   # load once at startup

def transcribe(audio_path: str) -> str:
    result = model.transcribe(audio_path)
    return result["text"].strip()
```

Endpoint:

```
POST /voice/transcribe
Content-Type: multipart/form-data
Body: audio (WAV file, max 30s)

Response: { "text": "Book me a flight to Mumbai" }
```

---

## 4. Tech Stack

### Full list with rationale

| Layer | Technology | Why |
|-------|-----------|-----|
| Desktop shell | Electron + React (Vite) | Cross-platform (Mac + Windows), native file system access, standard installer, no CLI for users |
| Backend | FastAPI (Python) | Async, fast, great WebSocket support; Python is home for all automation libs |
| Agent | LangGraph | Stateful graph, native HITL pause/resume, checkpoint/replay built in |
| Browser automation | `browser-use` (Playwright) | High-level browser agent API over Playwright |
| Desktop automation | PyAutoGUI + Agent-S | PyAutoGUI for simple actions, Agent-S for complex multi-step desktop tasks |
| Terminal execution | `subprocess` + `pty` (Python) | PTY gives interactive terminal support (sudo prompts, etc.) |
| Voice input | OpenAI Whisper (local) | Offline, accurate, no API key needed |
| Voice output | Web Speech API — SpeechSynthesis | Built into Electron's Chromium, no dependency |
| Local storage | SQLite via SQLModel | Zero-config, embedded, Pydantic models double as API validators |
| Sharing relay | Supabase free tier | One-table hosted DB for storing workflow JSON blobs behind short links |
| Packaging | electron-builder | Mac `.dmg` + Windows `.exe` installer, auto-update support |

### What we are NOT using and why

- **LangChain (without Graph):** No native stateful graph or HITL pause.
- **Docker:** Adds complexity and a learning curve for non-technical users who also install the app.
- **Cloud backend:** Goes against local-first principle. Only the sharing relay is remote.
- **REST for HITL:** HITL requires push (server → client). WebSocket is the right tool.

---

## 5. Canonical Workflow Schema

> **Note:** This schema is currently a draft and is subject to change as the project evolves. Similarly, all code snippets provided in this document are illustrative and not final.

**This schema is the initial contract between all four teammates.** The backend stores it, the agent executes it, the frontend renders it, and Person 4 validates it. Change it only with full team alignment.

```json
{
  "id": "wf_abc123",
  "name": "Book a hotel room",
  "description": "Searches Booking.com and asks for confirmation before reserving.",
  "inputs": [
    {
      "name": "destination",
      "label": "Where are you going?",
      "type": "text",
      "required": true
    },
    {
      "name": "check_in",
      "label": "Check-in date",
      "type": "date",
      "required": true
    }
  ],
  "steps": [
    {
      "id": "step_1",
      "type": "browser",
      "action": "navigate",
      "params": { "url": "https://booking.com" },
      "description": "Open Booking.com"
    },
    {
      "id": "step_2",
      "type": "browser",
      "action": "fill",
      "params": { "selector": "#destination", "value": "{{destination}}" },
      "description": "Enter destination"
    },
    {
      "id": "step_3",
      "type": "hitl",
      "prompt": "I found three hotels. Which one should I book?",
      "voice_prompt": "I found three hotels. Which one should I book?",
      "timeout_seconds": 300
    },
    {
      "id": "step_4",
      "type": "desktop",
      "action": "screenshot",
      "params": {},
      "description": "Capture confirmation screen"
    },
    {
      "id": "step_5",
      "type": "terminal",
      "command": "echo 'Booking complete for {{destination}}'",
      "description": "Log completion"
    }
  ],
  "metadata": {
    "tags": ["travel", "booking"],
    "version": 1,
    "created_at": "2026-05-02T10:00:00Z",
    "updated_at": "2026-05-02T10:00:00Z",
    "run_count": 0,
    "last_run_at": null,
    "source": "manual"
  }
}
```

### Step `type` values

| type | Handled by | Description |
|------|-----------|-------------|
| `browser` | browser-use / Playwright | Any web browser action |
| `desktop` | PyAutoGUI / Agent-S | Keyboard, mouse, screen actions |
| `terminal` | subprocess / pty | Shell commands |
| `hitl` | LangGraph interrupt + WS | Pause and ask the human |
| `voice_speak` | Voice output system | Speak a message without pausing |
| `delay` | Agent | Wait N seconds |

### `{{variable}}` interpolation

Any `param` value or `command` string may include `{{input_name}}` tokens. They are resolved at execution time by substituting the user-provided input values. The backend handles interpolation before passing steps to the agent.

### Extension Telemetry Mapping

The Chrome extension records raw user interactions. Person 4 will map these flat telemetry events into the canonical step array:
- `event: 'click'` → `type: 'browser', action: 'click', params: { selector: xpath }`
- `event: 'input'` → `type: 'browser', action: 'fill', params: { selector: xpath, value: ... }`
- Consecutive identical actions are combined directly via the extension's onboard noise reducer.

---

## 6. File & Folder Structure

```
autoflow/
│
├── extension/                       # Task Mining Chrome Extension (Recorder)
│   ├── manifest.json                # V3 manifest for Chrome
│   ├── src/
│   │   ├── background/              # IndexedDB telemetry persistence
│   │   ├── content/                 # DOM event capture & noise reduction
│   │   └── ui/                      # Dashboard and settings popup
│   └── utils/                       # Noise reduction, CSV exports
│
├── app/                             # Electron + React frontend (Person 3)
│   ├── electron/
│   │   ├── main.js                  # Electron main process
│   │   └── preload.js               # Context bridge (IPC)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── WorkflowLibrary.tsx  # Home screen
│   │   │   ├── RunView.tsx          # Live execution view
│   │   │   ├── WorkflowEditor.tsx   # Create / edit workflow
│   │   │   └── Settings.tsx         # LLM key, voice settings
│   │   ├── components/
│   │   │   ├── WorkflowCard.tsx
│   │   │   ├── HITLDialog.tsx       # Full-screen approval modal
│   │   │   ├── StatusBar.tsx        # Real-time step progress
│   │   │   ├── MicButton.tsx        # Voice input trigger
│   │   │   └── VoiceIndicator.tsx   # Speaking state indicator
│   │   ├── hooks/
│   │   │   ├── useWorkflow.ts
│   │   │   ├── useExecution.ts
│   │   │   ├── useSocket.ts
│   │   │   └── useVoice.ts          # SpeechSynthesis + mic
│   │   └── lib/
│   │       ├── api.ts               # HTTP client (axios)
│   │       └── socket.ts            # WebSocket client
│   ├── package.json
│   └── vite.config.ts
│
├── server/                          # FastAPI backend (Person 2)
│   ├── routers/
│   │   ├── workflows.py             # CRUD
│   │   ├── executions.py            # Start/stop/status/respond
│   │   ├── voice.py                 # POST /voice/transcribe
│   │   ├── sharing.py               # Export + relay link
│   │   └── extension.py             # WS extension bridge
│   ├── models/
│   │   ├── workflow.py              # SQLModel table + Pydantic schema
│   │   └── execution.py             # Execution log table
│   ├── agent/                       # LangGraph agent (Person 1)
│   │   ├── graph.py                 # Graph definition + compile
│   │   ├── nodes/
│   │   │   ├── planner.py
│   │   │   ├── router.py
│   │   │   ├── executor.py
│   │   │   ├── hitl_gate.py
│   │   │   └── logger.py
│   │   └── tools/
│   │       ├── browser_tool.py      # browser-use wrapper
│   │       ├── desktop_tool.py      # PyAutoGUI / Agent-S wrapper
│   │       └── terminal_tool.py     # subprocess / pty wrapper
│   ├── voice/
│   │   ├── transcribe.py            # Whisper wrapper (Person 1)
│   │   └── speaker.py               # Speech event emitter (Person 1)
│   ├── db.py                        # SQLite engine + session
│   └── main.py                      # FastAPI app + startup
│
├── shared/                          # Shared definitions (Person 4)
│   ├── workflow_schema.json         # JSON Schema for validation
│   └── types.ts                     # TypeScript types mirroring Python models
│
├── relay/                           # Cloud sharing relay (Person 4)
│   └── README.md                    # Supabase table setup instructions
│
├── scripts/                         # Dev tooling (Person 4)
│   ├── build_mac.sh
│   ├── build_windows.sh
│   └── seed_workflows.py            # Seed demo workflows on first launch
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 7. FastAPI Endpoint Contracts

The backend runs on `http://localhost:8765` by default. Electron hardcodes this port; it is configurable in `.env`.

### Workflows

```
GET    /workflows                    → WorkflowSummary[]
POST   /workflows                    → Workflow           body: WorkflowCreate
GET    /workflows/{id}               → Workflow
PUT    /workflows/{id}               → Workflow           body: WorkflowUpdate
DELETE /workflows/{id}               → { ok: true }
POST   /workflows/import             → Workflow           body: JSON file upload
GET    /workflows/{id}/export        → JSON file download
```

### Executions

```
POST   /executions                   → Execution          body: { workflow_id, inputs }
GET    /executions/{id}/status       → ExecutionStatus
POST   /executions/{id}/respond      → { ok: true }       body: { response: string }
POST   /executions/{id}/cancel       → { ok: true }
```

### Voice

```
POST   /voice/transcribe             → { text: string }   body: audio WAV (multipart)
```

### Sharing

```
POST   /sharing/link                 → { url: string }    body: { workflow_id }
GET    /sharing/{slug}               → Workflow JSON      (relay fetch + return)
```

### WebSocket channels

```
WS  /ws/execution/{id}    Real-time execution events (see event types below)
WS  /ws/extension         Browser extension workflow recorder
```

### WebSocket event types (`/ws/execution/{id}`)

```json
{ "type": "step_start",    "step_id": "step_2", "description": "Enter destination" }
{ "type": "step_done",     "step_id": "step_2", "result": "filled" }
{ "type": "step_error",    "step_id": "step_2", "error": "Element not found" }
{ "type": "hitl_request",  "step_id": "step_3", "prompt": "Which hotel?", "voice_prompt": "..." }
{ "type": "hitl_resolved", "step_id": "step_3", "response": "The first one" }
{ "type": "speech",        "text": "Opening Booking.com now.", "priority": "normal" }
{ "type": "complete",      "summary": "Booked Hotel Taj, Mumbai" }
{ "type": "cancelled" }
```

---

## 8. LangGraph Agent Nodes

The graph has one linear happy path with a conditional branch to HITL.

```
START → planner → router → executor → logger → [router (next step) | END]
                                   ↓
                              hitl_gate (on hitl step type)
                                   ↓
                           waits for /executions/{id}/respond
                                   ↓
                              logger → router (next step)
```

### Node responsibilities

**`planner`**
- Input: `user_input: str`, `workflow: Workflow | None`
- Uses the **Antigravity** prompt to classify tasks as `os` or `browser`.
- Returns a structured `TaskPlan` with plain-English steps.
- Output: `TaskPlan` (category, sub_category, action_params, plain_english_plan)

**`os_executor`**
- **Direct Model**: Bypasses LLM tool-calling to ensure zero-latency.
- Uses a **Smart Task Parser** (Regex/Keyword) to match intents directly to OS tools.
- Executes: `launch_app`, `open_folder`, `compute_in_calculator`, `check_disk_space`, `get_battery_status`, `check_wifi`, `open_settings`.
- Emits real-time status updates and final textual results.

**`router`**
- Input: `step_queue`
- Pops the next step
- Routes to executor (browser/desktop/terminal) or hitl_gate (hitl/voice_speak)
- Output: `current_step: Step`, `remaining_steps: list[Step]`

**`executor`**
- Input: `current_step`
- Calls the appropriate tool wrapper (browser_tool / desktop_tool / terminal_tool)
- Emits `step_start` and `step_done` / `step_error` WS events
- Output: `step_result: str`

**`hitl_gate`**
- Input: `current_step` (type = `hitl`)
- Emits `hitl_request` WS event (including `voice_prompt` field for voice output)
- Calls `graph.interrupt()` — LangGraph pauses the graph here
- Resumes when `POST /executions/{id}/respond` is called
- Output: `hitl_response: str`

**`logger`**
- Input: all state
- Writes current step + result to `execution_logs` SQLite table
- Emits `speech` WS event with a short summary (used by voice output)
- Output: pass-through

---

## 9. Team Assignments

Every file in the repo should have a clear owner. When you need to touch someone else's area, talk to them first.

### Person 1 — Agent core + voice backend

**Owns:**
- `server/agent/` — entire LangGraph graph, all nodes, all tool wrappers
- `server/voice/` — Whisper transcription, speech event emitter
- Voice input backend (`POST /voice/transcribe` implementation)
- Voice output event design (what gets spoken, when, and at what priority)

**Does not own:** FastAPI routing, frontend, packaging.

**Parallel Timeline (Phase 1) goal:** LangGraph graph executes a hardcoded 3-step workflow (browser → hitl → browser) end-to-end in a Python script, no FastAPI yet.

### Person 2 — Backend + API

**Owns:**
- `server/routers/` — all HTTP and WebSocket endpoints
- `server/models/` — SQLModel schemas, migrations
- `server/db.py` — database engine and session management
- `server/main.py` — FastAPI app config, startup events
- Execution session state (tracking running graphs, mapping WS connections to execution IDs)
- WS extension bridge (`/ws/extension`)

**Does not own:** Agent internals, frontend, sharing relay, packaging.

**Parallel Timeline (Phase 1) goal:** FastAPI running with `GET /workflows` and `POST /executions` returning mock data. WebSocket `/ws/execution/{id}` emitting fake events every 2 seconds.

### Person 3 — Frontend (Electron + React)

**Owns:**
- `app/` — entire Electron + React app
- Workflow library home screen
- Run view with real-time step progress
- HITL dialog (full-screen, large text, clear CTA)
- Voice UI: `MicButton`, `VoiceIndicator`, `useVoice` hook
- Settings panel (LLM key, voice preferences)
- Electron shell: `main.js`, `preload.js`, build config

**Does not own:** Backend endpoints, agent logic, packaging scripts.

**Parallel Timeline (Phase 1) goal:** Workflow library renders from mock JSON data. Run view shows fake step progression via a mock WebSocket. HITL dialog opens and closes.

**UX rule for this person:** Before shipping any screen, test it with someone non-technical. If they hesitate for more than 3 seconds, redesign.

### Person 4 — Schema + sharing + DevOps

**Owns:**
- `shared/workflow_schema.json` — canonical JSON Schema, Pydantic validators
- `shared/types.ts` — TypeScript types
- `server/routers/sharing.py` — export/import/link endpoints
- `relay/` — Supabase table setup, relay API
- `scripts/` — build scripts for Mac and Windows
- Browser extension integration (mapping extension event format → Workflow schema)
- `electron-builder` config for distributable installers
- End-to-end testing and QA

**Does not own:** Agent internals, main frontend components, core backend endpoints.

**Parallel Timeline (Phase 1) goal:** Workflow JSON schema agreed and documented. JSON import/export endpoints working. electron-builder producing a working unsigned `.dmg` on Mac.

---

## 10. Coding Conventions

### Python

- **Formatter:** Black (`line-length = 88`). Run before every commit.
- **Type hints:** Required on all function signatures. No bare `dict` or `list` — use `dict[str, Any]` or a typed model.
- **Models:** Use Pydantic/SQLModel for all data in and out of the API. No raw dicts at API boundaries.
- **Async:** All I/O is async. No `time.sleep()` — use `asyncio.sleep()`.
- **Error handling:** Raise typed exceptions. Never swallow with `except Exception: pass`. FastAPI handlers convert exceptions to HTTP error responses with user-friendly messages.
- **Imports:** Absolute imports only. Group: stdlib → third-party → local.

```python
# Good
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)) -> Workflow:
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
```

### TypeScript / React

- **Strict mode on.** `"strict": true` in `tsconfig.json`. No `any` without a comment explaining why.
- **Function components only.** No class components.
- **Hooks for state.** No prop-drilling beyond 2 levels — use context or a hook.
- **No inline styles.** Use Tailwind utility classes or CSS modules.
- **API calls in hooks only.** No `fetch()` calls inside components directly.
- **Error states required.** Every component that fetches data must handle loading, success, and error states explicitly.

```typescript
// Good
const { data: workflows, isLoading, error } = useWorkflows();
if (isLoading) return <LoadingSpinner />;
if (error) return <ErrorMessage message="Could not load workflows" />;
```

### General

- **Commit format:** [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` new feature
  - `fix:` bug fix
  - `refactor:` no behaviour change
  - `docs:` documentation only
  - `chore:` tooling, deps, config
- **No commented-out code** in commits. Delete it; git history is the undo button.
- **Every PR needs a description** saying what changed and why, not just what files were touched.
- **Test before you PR.** Run the server and the Electron app and manually verify your change works.

---

## 11. Build & Run Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+
- `ffmpeg` (required by Whisper for audio processing)

```bash
# Install ffmpeg
brew install ffmpeg         # macOS
choco install ffmpeg        # Windows (via Chocolatey)
```

### Backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# First run only — Whisper downloads the base model (~140MB)
python -c "import whisper; whisper.load_model('base')"

# Start the server
uvicorn main:app --port 8765 --reload
```

The API is now at `http://localhost:8765`. Docs at `http://localhost:8765/docs`.

### Frontend

```bash
cd app
npm install

# Development (connects to localhost:8765)
npm run dev

# Build for distribution
npm run build
npm run dist:mac     # produces dist/AutoFlow.dmg
npm run dist:win     # produces dist/AutoFlow Setup.exe
```

### Environment variables

Copy `.env.example` to `.env` in the `server/` directory:

```bash
# server/.env
AUTOFLOW_PORT=8765
LLM_PROVIDER=gemini             # Use Gemini (no ChatGPT)
LLM_API_KEYS=key1,key2,key3     # Comma-separated list of 3-5 Gemini api keys for rate limit rotation
LLM_MODEL=gemini-1.5-pro        # Gemini model 
WHISPER_MODEL=base              # base | small | medium
SHARING_RELAY_URL=https://...   # Supabase relay endpoint
SHARING_RELAY_KEY=...           # Supabase anon key
```

### Running both together (dev)

```bash
# Terminal 1
cd server && uvicorn main:app --port 8765 --reload

# Terminal 2
cd app && npm run dev
```

Electron will open automatically pointing to `localhost:8765`.

---

## 12. Git Workflow

### Branch naming

```
feat/person-1/browser-use-integration
feat/person-3/hitl-dialog
fix/person-2/websocket-reconnect
docs/person-4/update-schema
```

### Rules

1. **Never commit directly to `main`.** All changes go through a PR.
2. **One PR per feature.** Don't bundle unrelated changes.
3. **PRs need at least one approval** before merging.
4. **Squash and merge** — keeps `main` history clean and readable.
5. **Delete branch after merge.**
6. **`main` must always build.** If your PR breaks the build, it doesn't merge.

### Suggested weekly rhythm

| Day | Activity |
|-----|----------|
| Monday | Sync meeting — share blockers, align on that week's goals |
| Wednesday | Optional mid-week check-in (async in chat is fine) |
| Friday | PR reviews done. Merge what's ready. Update this doc if anything changed. |

---

## 13. UX Design Principles

These apply to every screen Person 3 builds and every error message Person 2 writes.

1. **If a user has to read instructions, the UI is wrong.** Redesign it.
2. **Minimum font size: 16px.** Many of our users have reduced vision.
3. **Plain English only.** No technical terms visible to users.
   - ✅ "Something went wrong. Try again."
   - ❌ "LangGraph executor raised ToolExecutionError at step 3"
4. **Every error has a recovery action.** A "Try again" or "Get help" button, always.
5. **Loading states must be visible.** Never leave a blank screen.
6. **HITL dialogs are full-screen and unmissable.** Not a small toast. A modal with large text, a clear question, and obvious Yes/No or text input. If voice output is on, the question is also spoken.
7. **The mic button is large and obvious.** 52×52px minimum tap target. Shows clear recording state (idle / recording / processing).
8. **Workflow cards show only what matters.** Name, one-line description, last run date, and a Run button. Nothing else.
9. **Undo before delete.** Deleting a workflow shows a confirmation. No instant deletion.
10. **Never show JSON to users.** Import/export works through file dialogs, not text areas.

---

## 14.~~Browser extension output format~~ [RESOLVED] Uses flat event objects (`event`: 'click', `xpath`/`css_selector`) + noise reduction logic. Person 4 to map this telemetry to our `browser` actions

Track these here until resolved. Assign a person and a resolution date.

| # | Question | Owner | Due |
|---|---------|-------|-----|
| 1 | Which Whisper model for MVP — `base` or `small`? `base` is faster but `small` is more accurate for accented English. | Person 1 | Week 1 |
| 2 | Browser extension output format — what JSON does it currently produce? Person 4 needs this to map it to our schema. | Person 4 | Week 1 |
| 3 | Sharing relay — do we self-host a tiny FastAPI on a VPS, or use Supabase? Decision affects Person 4's work. | Person 4 | Week 1 |
| 4 | Gemini API Key Rotation — Implement robust round-robin or rate-limit-aware rotation for the 3-5 Gemini API keys to avoid hitting usage limits. | Person 1 + 2 | Phase 1 |
| 5 | Voice HITL response — should users be able to speak their HITL answer, or text only for now? | Person 1 + 3 | Week 2 |
| 6 | Agent-S licensing and Python version compatibility — verify before using in production. | Person 1 | Week 1 |

---

*AutoFlow Team Context v1.0 — update this document when decisions change. Last edited by: [your name] on [date].*