"""One place that talks to OpenRouter."""
import re
from openai import OpenAI
from . import config

_client = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        # OpenRouter requires HTTP-Referer and X-Title headers for free models
        _client = OpenAI(
            api_key=config.OPENROUTER_API_KEY or "missing",
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "UK Visa Auditor"
            }
        )
    return _client

def redact(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    text = re.sub(r"\b[A-Z]{1,2}\d{7}\b", "[id]", text)
    text = re.sub(r"\d[\d\- ]{7,}\d", "[number]", text)
    return text

def chat(messages: list, max_tokens: int = 400, temperature: float = 0.3, model: str = None):
    if not config.OPENROUTER_API_KEY:
        print("[LLM DEBUG] No API key found in .env file!")
        return None
        
    candidates = [model] if model else [config.CHAT_MODEL] + config.FALLBACK_MODELS
    for name in candidates:
        try:
            print(f"[LLM DEBUG] Trying model: {name}...")
            resp = get_client().chat.completions.create(
                model=name, 
                messages=messages, 
                max_tokens=max_tokens, 
                temperature=temperature
            )
            text = (resp.choices[0].message.content or "").strip()
            if text:
                print(f"[LLM DEBUG] Success with {name}!")
                return text
            else:
                print(f"[LLM DEBUG] Model {name} returned empty text.")
        except Exception as e:
            print(f"[LLM DEBUG] Model {name} FAILED. Error: {str(e)}")
            continue
    return None