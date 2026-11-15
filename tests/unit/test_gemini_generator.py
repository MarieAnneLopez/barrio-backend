"""GeminiTextGenerator (H36) con un transporte simulado de httpx: sin red ni clave real."""

import json
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.providers.factory import provider_name, text_generator
from app.providers.gemini_generator import GeminiTextGenerator
from app.providers.generative_model import GenerationError


def client(status: int = 200, body: dict[str, Any] | None = None, seen: list[httpx.Request] | None = None,
           fail: bool = False) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        if fail:
            raise httpx.ConnectTimeout("lento")
        return httpx.Response(status, json=body or {})
    return httpx.Client(transport=httpx.MockTransport(handler))


def reply(text: str, finish: str = "STOP") -> dict[str, Any]:
    return {"candidates": [{"finishReason": finish,
                            "content": {"parts": [{"text": "pensando", "thought": True}, {"text": text}]}}]}


def test_envia_sistema_y_mensaje_con_la_clave_en_cabecera_y_lee_solo_el_texto() -> None:
    seen: list[httpx.Request] = []
    gen = GeminiTextGenerator("clave-falsa", "gemini-x", client=client(body=reply(" Hola. "), seen=seen))
    assert gen.generate("Eres Mini Marie", "¿Colegios?") == "Hola."
    request = seen[0]
    assert request.url.path == "/v1beta/models/gemini-x:generateContent"
    assert request.headers["x-goog-api-key"] == "clave-falsa" and "clave-falsa" not in str(request.url)
    body = json.loads(request.content)
    assert body["systemInstruction"]["parts"][0]["text"] == "Eres Mini Marie"
    assert body["contents"][0]["parts"][0]["text"] == "¿Colegios?"


@pytest.mark.parametrize("gen", [
    GeminiTextGenerator("k", client=client(status=429)),
    GeminiTextGenerator("k", client=client(fail=True)),
    GeminiTextGenerator("k", client=client(body={"promptFeedback": {"blockReason": "SAFETY"}})),
    GeminiTextGenerator("k", client=client(body=reply("x", finish="SAFETY"))),
    GeminiTextGenerator("k", client=client(body=reply("   "))),
])
def test_cuota_red_bloqueo_o_vacio_son_error_de_generacion(gen: GeminiTextGenerator) -> None:
    with pytest.raises(GenerationError):
        gen.generate("s", "p")


def test_la_fabrica_prefiere_gemini_y_avisa_el_proveedor() -> None:
    both = Settings(chat_model="generativo", gemini_api_key=SecretStr("g"), anthropic_api_key=SecretStr("a"))
    assert isinstance(text_generator(both), GeminiTextGenerator)
    assert provider_name(both) == "gemini"
    assert provider_name(Settings(chat_model="analitico", gemini_api_key=SecretStr("g"))) is None
    assert provider_name(Settings(chat_model="generativo")) is None
