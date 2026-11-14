"""TextGenerator sobre la API de Claude (SDK oficial `anthropic`), D59.

Solo se construye si hay ANTHROPIC_API_KEY. Respuesta corta de chat: esfuerzo
`low`, timeout de 12 s y sin reintentos, para responder antes de que el
frontend se rinda (15 s); ante cualquier fallo responde el modelo analítico.
Con los respaldos del servidor (`fallbacks: "default"`), si el modelo declina
por política la API reintenta en otro modelo dentro de la misma llamada; si
toda la cadena declina (`stop_reason == "refusal"`), GenerativeModel usa la
respuesta analítica.
"""

from typing import Any

import anthropic

from app.providers.generative_model import GenerationError

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class ClaudeTextGenerator:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout_s: float = 12.0,
                 client: Any | None = None) -> None:
        self._model = model
        self._client = client or anthropic.Anthropic(api_key=api_key, timeout=timeout_s, max_retries=0)

    def generate(self, system: str, prompt: str) -> str:
        try:
            response = self._client.beta.messages.create(
                model=self._model,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_config={"effort": "low"},
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.APIError as exc:  # estado HTTP, red, timeout o respuesta inválida
            raise GenerationError(type(exc).__name__) from exc
        if response.stop_reason == "refusal":
            raise GenerationError("refusal")
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if not text:
            raise GenerationError("empty")
        return text
