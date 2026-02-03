import asyncio
import base64
import json
import uuid
import sys
from typing import Any, Dict

from app.services.memory_service import MemoryService
from app.services.speech_service import transcribe_audio_bytes
from app.services.tts_service import piper_tts_async
from app.services.llm_service import generate_stream 
from app.services.teaching_engine import TeachingState
from app.prompts.tutoring_prompts import EXAMPLE_CONCEPTS, SYSTEM_PROMPT

async def handle_ws_message(raw: str | bytes, send_fn, state: Dict[str, Any]) -> None:
    if isinstance(raw, bytes):
        await _handle_audio(raw, send_fn, state)
        return

    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        await send_fn({"type": "error", "message": "Invalid JSON"})
        return

    msg_type = data.get("type") or ""
    
    if msg_type == "start_session":
        await _handle_start_session(send_fn, state)
    elif msg_type == "start_concept":
        concept = (data.get("concept") or "").strip() or "programming"
        print(f"DEBUG: Starting concept: {concept}")
        await _handle_start_concept(concept, send_fn, state)
    elif msg_type == "user_text":
        text = (data.get("text") or "").strip()
        if text:
            await _handle_user_text(text, send_fn, state)

def _ensure_state(state: Dict[str, Any]) -> None:
    if "session_id" not in state:
        state["session_id"] = str(uuid.uuid4())
    if "memory" not in state:
        state["memory"] = MemoryService()
    if "teaching_state" not in state:
        state["teaching_state"] = TeachingState()

async def _handle_start_session(send_fn, state: Dict[str, Any]) -> None:
    _ensure_state(state)
    await send_fn({"type": "avatar", "state": "idle"})
    await send_fn({
        "type": "ready",
        "session_id": state["session_id"],
        "example_concepts": EXAMPLE_CONCEPTS,
    })

async def _handle_start_concept(concept: str, send_fn, state: Dict[str, Any]) -> None:
    _ensure_state(state)
    ts = state["teaching_state"]
    ts.current_concept = concept
    ts.waiting_for_answer = False
    
    prompt = f"Explain {concept} in one sentence and ask me a short question."
    await _stream_assistant_response(prompt, send_fn, state)

async def _handle_user_text(text: str, send_fn, state: Dict[str, Any]) -> None:
    _ensure_state(state)
    ts = state["teaching_state"]
    prompt = f"The user said: {text}. Respond briefly."
    await _stream_assistant_response(prompt, send_fn, state)

async def _stream_assistant_response(user_prompt: str, send_fn, state: Dict[str, Any]) -> None:
    _ensure_state(state)
    mem = state["memory"]
    sid = state["session_id"]

    # 1. Show avatar talking immediately
    await send_fn({"type": "avatar", "state": "talking"})
    await send_fn({"type": "assistant_text", "text": "Thinking..."}) 

    print(f"\n[LLM] Processing: {user_prompt}")
    full_response = ""

    try:
        # We pass EMPTY history [] to speed up the i3 processor for now
        async for token in generate_stream(user_prompt, SYSTEM_PROMPT, []):
            full_response += token
            # Send word to UI
            await send_fn({"type": "token", "text": token})
            # Print to terminal so we can see progress without the browser
            print(token, end="", flush=True)
            await asyncio.sleep(0.01) 
            
    except Exception as e:
        print(f"\n[ERROR] LLM failed: {e}")
        await send_fn({"type": "error", "message": str(e)})
        return

    print("\n[LLM] Done.")

    # 2. Memory & Audio (Audio happens AFTER text to prevent CPU overload)
    await mem.append_message(sid, "assistant", full_response)
    
    try:
        print("[TTS] Generating audio...")
        audio_data = await piper_tts_async(full_response)
        wav_b64 = base64.b64encode(audio_data).decode("ascii")
        await send_fn({"type": "tts_chunk", "data": wav_b64})
        print("[TTS] Sent to frontend.")
    except Exception as e:
        print(f"[TTS] Error: {e}")

    await send_fn({"type": "avatar", "state": "idle"})