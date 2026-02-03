# Local AI Tutor MVP

Fully local, API-free human-like AI tutor with voice input, voice output, and a simple animated avatar.

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Electron + React)                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐│
│  │ Avatar       │  │ Voice Input  │  │ Teaching UI (explain /   ││
│  │ (2D canvas,  │  │ (mic → WS   │  │ question / feedback)     ││
│  │ idle/talk/   │  │ chunks)     │  │                          ││
│  │ listen)      │  └──────┬───────┘  └────────────┬─────────────┘│
│  └──────┬───────┘         │                       │              │
│         │                 └───────────────────────┼──────────────┤
│         │                                         │              │
│         │              WebSocket (ws://localhost)  │              │
└─────────┼─────────────────────────────────────────┼──────────────┘
          │                                         │
          ▼                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI)                                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ WebSocket handler: route messages, emit avatar state,        │ │
│  │ transcript, TTS audio chunks, teaching turns                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ LLM Service │ │ Memory Svc  │ │ Speech Svc  │ │ TTS Service │ │
│  │ (llama.cpp) │ │ (SQLite +  │ │ (Whisper)   │ │ (Piper)     │ │
│  │             │ │  FAISS)     │ │             │ │             │ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ │
│         │               │               │               │        │
│         └───────────────┴───────┬───────┴───────────────┘        │
│                                 ▼                                │
│                    ┌─────────────────────────┐                   │
│                    │ Teaching Engine         │                   │
│                    │ (explain → ask →        │                   │
│                    │  correct loop)          │                   │
│                    └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

- **Frontend**: Renders avatar, captures mic, sends audio/text over WebSocket, plays TTS, shows teaching flow.
- **Backend**: Receives audio → Whisper STT → Teaching Engine (uses LLM, Memory) → TTS → streams state + audio back.
- **Avatar state**: `idle` | `listening` | `talking` — driven by backend so lip-sync can be timed to TTS.

## 2. Folder Structure

```
LLM/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, WebSocket routes
│   │   ├── config.py            # Paths, model names (env / defaults)
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   └── tutoring_prompts.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py
│   │   │   ├── memory_service.py
│   │   │   ├── speech_service.py
│   │   │   ├── tts_service.py
│   │   │   └── teaching_engine.py
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── handler.py       # WS message routing
│   ├── scripts/
│   │   └── init_db.py
│   ├── schemas/
│   │   └── schema.sql           # SQLite DDL
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── electron/
│   │   └── main.js
│   ├── public/
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── components/
│       │   ├── Avatar.jsx
│       │   ├── VoiceInput.jsx
│       │   └── TeachingPanel.jsx
│       ├── hooks/
│       │   └── useWebSocket.js
│       └── styles/
│           └── App.css
├── data/                        # SQLite DB (created at run)
├── models/                      # Place GGUF, Piper here
│   └── .gitkeep
└── README.md
```

## 3. Backend Implementation

- **LLM**: `llama-cpp-python` loads a GGUF model from `models/llama/*.gguf` or `TUTOR_LLAMA_MODEL_PATH`.
- **Memory**: `MemoryService` uses `data/tutor.db` (SQLite), schema in `backend/schemas/schema.sql`. Conversation and teaching turns are stored.
- **Speech**: `openai-whisper` transcribes audio; browser sends WebM, converted with pydub/ffmpeg when needed.
- **TTS**: Piper CLI (`piper --model <path> --output_file <out>`); model in `models/piper/*.onnx` or `TUTOR_PIPER_MODEL_PATH`.
- **Teaching Engine**: `start_explanation` → user answer → `check_answer` → optional `do_correction`. Prompts in `app/prompts/tutoring_prompts.py`.
- **WebSocket**: Messages `start_session`, `start_concept`, `user_text`, `audio_chunk`; server sends `avatar`, `assistant_text`, `tts_chunk`, `ready`, `error`.

## 4. Frontend Implementation

- **Electron** loads the React app (dev: `http://localhost:5173`, prod: `dist/index.html`).
- **useWebSocket** connects to `ws://127.0.0.1:8765/ws`, sends JSON and binary audio, exposes `lastMessage` and `send`/`sendAudio`.
- **App** processes `lastMessage` to update `avatarState`, `assistantText`, `concepts`, and plays TTS via Web Audio when `tts_chunk` arrives.
- **TeachingPanel** shows assistant text and example concepts; **VoiceInput** is text + optional “Voice input” mic (sends one blob when stopped).

## 5. Avatar Logic

- **State**: `idle` | `listening` | `talking` from backend (`type: "avatar", state: "…"`).
- **Rendering**: 2D canvas; head circle, eyes (blink when idle), mouth ellipse. When `talking`, mouth openness is driven by `0.3 + mouth * 0.25` with `mouth = 0.5 + 0.5 * sin(t*8)` for simple lip sync. No live audio analysis; sync is heuristic from backend “talking” duration.
- **Listening**: Slightly open mouth; **idle**: minimal open, occasional blink.

## 6. How to Run Locally

**Prerequisites**

- Python 3.10+, Node 18+
- GGUF model (e.g. LLaMA/Mistral) in `models/llama/` or `TUTOR_LLAMA_MODEL_PATH`
- Piper binary on PATH and a Piper `.onnx` model in `models/piper/` or `TUTOR_PIPER_MODEL_PATH`
- FFmpeg on PATH (for pydub/Whisper when converting browser WebM)
- (Optional) GPU: set `TUTOR_WHISPER_DEVICE=cuda`, llama-cpp-python built with CUDA

**Backend**

```bash
cd "c:\Users\coole\Downloads\AI App\LLM"
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r backend/requirements.txt
# From project root (app loads from backend/):
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765
```

Or use the helper script: `python run_backend.py`

**Frontend (web)**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Ensure backend is running on 8765.

**Frontend (Electron)**

```bash
cd frontend
npm run dev        # Vite dev server
# In another terminal:
npm run electron   # Or "npm run electron:dev" to start both
```

**Initialize DB (optional)**  
Schema is created on first use. To pre-create:

```bash
cd backend && python scripts/init_db.py
```

(Use same `PYTHONPATH` / working dir as backend so `app` resolves.)

## 7. Known Limitations

- **STT**: Browser sends one WebM blob per “press and speak”; no streaming. Whisper runs on full blob; latency scales with length. WebM→WAV needs ffmpeg.
- **TTS**: Piper runs per reply (no chunked streaming in this MVP). Large replies can feel slow.
- **Lip sync**: Avatar “talking” is time-based, not driven by phonemes or audio peaks.
- **LLM**: Single GPU process; no speculative decoding or batching. Context is last N turns only.
- **FAISS**: Schema and MemoryService support topics; no vector indexing or retrieval implemented in this MVP (left for later).
- **Single user**: No auth; one DB, one logical user.
- **Electron**: Dev mode loads localhost:5173; prod must run `npm run build` then `npm run electron` so `dist/index.html` exists.
