# backend/app/main.py — FastAPI app and WebSocket endpoint (local only)

import base64
import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.websocket.handler import handle_ws_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optional: preload models on startup (can slow start)
    yield
    # Shutdown


app = FastAPI(title="Local AI Tutor", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "tutor-backend"}


@app.get("/concepts")
def concepts():
    from app.prompts.tutoring_prompts import EXAMPLE_CONCEPTS
    return {"concepts": EXAMPLE_CONCEPTS}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    state = {}

    async def send(msg):
        try:
            if isinstance(msg, dict):
                await ws.send_text(json.dumps(msg))
            else:
                await ws.send_text(msg)
        except Exception:
            pass

    try:
        while True:
            msg = await ws.receive()
            raw = msg.get("text") or msg.get("bytes") or b""
            if isinstance(raw, bytes) and len(raw) > 0:
                # Binary audio chunk: wrap as JSON for handler
                await handle_ws_message(
                    json.dumps({"type": "audio_chunk", "data": base64.b64encode(raw).decode("ascii")}),
                    send,
                    state,
                )
            else:
                text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                await handle_ws_message(text, send, state)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await send({"type": "error", "message": str(e)})
        except Exception:
            pass


def run():
    s = get_settings()
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=s.host,
        port=s.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
