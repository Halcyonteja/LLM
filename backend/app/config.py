# backend/app/config.py — paths and model config (no cloud APIs)
import os
from pathlib import Path
from types import SimpleNamespace

# Project root: parent of backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"


def get_settings() -> SimpleNamespace:
    def env(key: str, default: str = "") -> str:
        return os.environ.get(f"TUTOR_{key}", default)

    llama_path = env("LLAMA_MODEL_PATH")
    if not llama_path and (MODELS_DIR / "llama").exists():
        candidates = list((MODELS_DIR / "llama").glob("*.gguf"))
        if candidates:
            llama_path = str(candidates[0])

    piper_path = env("PIPER_MODEL_PATH")
    if not piper_path and (MODELS_DIR / "piper").exists():
        candidates = list((MODELS_DIR / "piper").glob("*.onnx"))
        if candidates:
            piper_path = str(candidates[0])

    db_path = env("DB_PATH")
    if not db_path:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_path = str(DATA_DIR / "tutor.db")

    return SimpleNamespace(
        llama_model_path=llama_path,
        llama_n_ctx=int(env("LLAMA_N_CTX", "2048")),
        llama_n_gpu_layers=int(env("LLAMA_N_GPU_LAYERS", "-1")),
        whisper_model=env("WHISPER_MODEL", "base"),
        whisper_device=env("WHISPER_DEVICE", "cuda"),
        piper_bin=env("PIPER_PATH", "piper"),
        piper_model_path=piper_path,
        db_path=db_path,
        host=env("HOST", "127.0.0.1"),
        port=int(env("PORT", "8765")),
    )
