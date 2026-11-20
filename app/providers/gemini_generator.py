"""TextGenerator sobre la API de Gemini (REST con httpx, ya en el stack), H36.

Solo se construye si hay GEMINI_API_KEY (variable de entorno del backend; nunca
llega al frontend). Formato tomado de la referencia oficial:
https://ai.google.dev/api/generate-content (POST /v1beta/models/{model}:generateContent,
systemInstruction, generationConfig.thinkingConfig.thinkingLevel). Timeout de 12 s y
sin reintentos, para responder antes de que el frontend se rinda (15 s); ante
cualquier fallo (red, 4xx/5xx, 429 por cuota, bloqueo) responde el modelo analítico.
"""

from typing import Any

import httpx

from app.providers.generative_model import GenerationError

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Medido el 2026-11-15: 3.5 Flash-Lite responde en ~1,3 s; 3.8 Flash superó 30 s.
DEFAULT_MODEL = "gemini-3.5-flash-lite"
OK_FINISH = {"STOP", "MAX_TOKENS"}


class GeminiTextGenerator:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout_s: float = 12.0,
                 client: httpx.Client | None = None) -> None:
        self._key = api_key
        self._url = API.format(model=model)
        self._client = client or httpx.Client(timeout=timeout_s)

    def generate(self, system: str, prompt: str) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 400, "temperature": 0.3,
                                 "thinkingConfig": {"thinkingLevel": "MINIMAL"}},
        }
        try:
            response = self._client.post(self._url, headers={"x-goog-api-key": self._key}, json=body)
        except httpx.HTTPError as exc:  # red o timeout
            raise GenerationError(type(exc).__name__) from exc
        if response.status_code != 200:
            raise GenerationError(f"http {response.status_code}")
        try:
            return _text(response.json())
        except (ValueError, AttributeError, TypeError, KeyError, IndexError) as exc:
            raise GenerationError("invalid response") from exc


def _text(data: dict[str, Any]) -> str:
    if data.get("promptFeedback", {}).get("blockReason"):
        raise GenerationError("blocked")
    candidates = data.get("candidates") or []
    if not candidates or candidates[0].get("finishReason") not in OK_FINISH:
        raise GenerationError("finish")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    if not text:
        raise GenerationError("empty")
    return text
