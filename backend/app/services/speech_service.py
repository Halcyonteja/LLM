# backend/app/services/speech_service.py — microphone input → Whisper STT (local)

import io
import os
from pathlib import Path
from typing import Optional

# Whisper is loaded lazily to avoid slow import when not used
_whisper_model = None


def _load_whisper(model_name: str = "base", device: Optional[str] = None):
    global _whisper_model
    if _whisper_model is None:
        import whisper
        dev = device or os.environ.get("TUTOR_WHISPER_DEVICE", "cuda")
        _whisper_model = whisper.load_model(model_name, device=dev)
    return _whisper_model


def transcribe_audio_bytes(audio_bytes: bytes, model_name: str = "base", device: Optional[str] = None) -> str:
    """
    Transcribe raw audio bytes (e.g. from WebSocket). Handles .webm from browser mic;
    converts to wav via pydub if needed, then runs Whisper.
    """
    import tempfile
    suffix = ".webm" if audio_bytes[:4] in (b"\x1aE\xdf\xa3", b"\x1a\x45\xdf\xa3") else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        path = f.name
    to_remove = [path]
    try:
        # Convert to wav 16k mono if input is webm (pydub needs ffmpeg)
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(path)
            seg = seg.set_frame_rate(16000).set_channels(1)
            wav_path = path + ".wav"
            seg.export(wav_path, format="wav")
            path = wav_path
            to_remove.append(wav_path)
        except Exception:
            pass
        model = _load_whisper(model_name, device)
        r = model.transcribe(path, language=None, fp16=(device == "cuda"))
        return (r.get("text") or "").strip()
    finally:
        for p in to_remove:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except Exception:
                    pass


def transcribe_file(file_path: str, model_name: str = "base", device: Optional[str] = None) -> str:
    """Convenience: transcribe from a file path."""
    model = _load_whisper(model_name, device)
    r = model.transcribe(file_path, language=None, fp16=(device == "cuda"))
    return (r.get("text") or "").strip()
