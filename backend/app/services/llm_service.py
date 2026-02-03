import os
import asyncio
from pathlib import Path
from typing import List, Optional, Tuple, AsyncGenerator

_llm = None

def _default_model_path() -> str:
    base = Path(__file__).resolve().parent.parent.parent.parent
    candidates = list((base / "models" / "llama").glob("*.gguf")) if (base / "models" / "llama").exists() else []
    if candidates:
        return str(candidates[0])
    return ""

def get_llm(model_path: Optional[str] = None, n_ctx: int = 512):
    global _llm
    path = model_path or os.environ.get("TUTOR_LLAMA_MODEL_PATH") or _default_model_path()
    
    if not path or not Path(path).exists():
        raise FileNotFoundError(f"GGUF model not found at {path}")

    if _llm is None:
        from llama_cpp import Llama
        _llm = Llama(
            model_path=path,
            n_ctx=2048,
            n_threads=6,       # i3 Dual Core Optimization
            n_gpu_layers=33,    # CPU only
            n_batch=512,         # Low RAM optimization
            verbose=False,
        )
    return _llm

def build_messages(system: str, history: List[Tuple[str, str]]) -> List[dict]:
    """Organizes conversation roles."""
    out = [{"role": "system", "content": system}]
    for r, c in history:
        out.append({"role": "user" if r == "user" else "assistant", "content": c})
    return out

def format_for_llama(messages: List[dict]) -> str:
    """Formats text for Llama-2-Chat (using [INST] tags)."""
    prompt = ""
    system_content = messages[0]["content"]
    
    # Llama-2 specific formatting
    prompt += f"<s>[INST] <<SYS>>\n{system_content}\n<</SYS>>\n\n"
    
    for m in messages[1:]:
        if m["role"] == "user":
            prompt += f"{m['content']} [/INST] "
        else:
            prompt += f"{m['content']} </s><s>[INST] "
    
    return prompt

async def generate_stream(
    prompt: str,
    system: str,
    history: List[Tuple[str, str]],
    max_tokens: int = 128,
    temperature: float = 0.7,
    model_path: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    
    hist = list(history)
    full_history = hist + [("user", prompt)]
    messages = build_messages(system, full_history)
    text = format_for_llama(messages)

    llm = get_llm(model_path=model_path)
    
    # Create the generator
    response_iterator = llm(
        text,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["[/INST]", "</s>"],
        echo=False,
        stream=True
    )

    for chunk in response_iterator:
        token = chunk["choices"][0].get("text", "")
        if token:
            yield token
            await asyncio.sleep(0) # Let the server send the packet