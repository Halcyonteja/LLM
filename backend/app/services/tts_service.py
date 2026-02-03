# backend/app/services/tts_service.py — text to speech via Piper (local)

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def _default_piper_model() -> str:
    base = Path(__file__).resolve().parent.parent.parent.parent
    d = base / "models" / "piper"
    if not d.exists():
        return ""
    # Look for en_US model as fallback
    for name in ["en_US-lessac-medium", "en_US-lessac-low", "en_US"]:
        for ext in [".onnx", ".onnx.json"]:
            p = d / f"{name}{ext}" if not name.endswith(ext) else d / name
            if p.exists():
                return str(p.with_suffix("").with_suffix(".onnx")) if ext == ".onnx.json" else str(p)
    for f in d.glob("*.onnx"):
        return str(f)
    return ""


def piper_tts(
    text: str,
    out_path: Optional[str] = None,
    piper_bin: Optional[str] = None,
    model_path: Optional[str] = None,
) -> bytes:
    """
    Run Piper TTS: text -> WAV bytes.
    Piper is called as: piper --model <model> --output_file <out> [stdin with text]
    """
    piper_bin = piper_bin or os.environ.get("TUTOR_PIPER_PATH", "piper")
    model = model_path or os.environ.get("TUTOR_PIPER_MODEL_PATH") or _default_piper_model()
    if not model or not Path(model).exists():
        # Fallback: return empty and let caller handle (or use a placeholder tone)
        raise FileNotFoundError(
            "Piper model not found. Place .onnx (and .onnx.json) in models/piper/ or set TUTOR_PIPER_MODEL_PATH."
        )
    use_file = out_path
    if not use_file:
        fd, use_file = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
    try:
        proc = subprocess.run(
            [piper_bin, "--model", model, "--output_file", use_file],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=60,
            cwd=str(Path(model).parent) if Path(model).parent else None,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Piper TTS failed: {proc.stderr.decode()}")
        with open(use_file, "rb") as f:
            data = f.read()
        return data
    finally:
        if not out_path and os.path.exists(use_file):
            try:
                os.unlink(use_file)
            except Exception:
                pass


async def piper_tts_async(
    text: str,
    piper_bin: Optional[str] = None,
    model_path: Optional[str] = None,
) -> bytes:
    """Async wrapper around Piper (runs in thread)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: piper_tts(text, piper_bin=piper_bin, model_path=model_path),
    )
