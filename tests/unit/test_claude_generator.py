"""ClaudeTextGenerator con un cliente falso: petición enviada y manejo de errores (sin red)."""

from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest

from app.providers.claude_generator import DEFAULT_MODEL, FALLBACK_BETA, ClaudeTextGenerator
from app.providers.generative_model import GenerationError


class FakeMessages:
    def __init__(self, result: Any) -> None:
        self.result, self.kwargs = result, {}

    def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def generator(result: Any) -> tuple[ClaudeTextGenerator, FakeMessages]:
    messages = FakeMessages(result)
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return ClaudeTextGenerator("sk-ant-prueba", client=client), messages


def response(stop: str = "end_turn", *texts: str) -> SimpleNamespace:
    blocks = [SimpleNamespace(type="thinking", thinking="")] + [SimpleNamespace(type="text", text=t) for t in texts]
    return SimpleNamespace(stop_reason=stop, content=blocks)


def test_envia_la_peticion_esperada_y_une_los_textos() -> None:
    gen, messages = generator(response("end_turn", "Hola ", "vecina."))
    assert gen.generate("sistema", "datos") == "Hola vecina."
    sent = messages.kwargs
    assert (sent["model"], sent["system"], sent["fallbacks"]) == (DEFAULT_MODEL, "sistema", "default")
    assert sent["betas"] == [FALLBACK_BETA] and sent["output_config"] == {"effort": "low"}
    assert sent["messages"] == [{"role": "user", "content": "datos"}] and "thinking" not in sent


@pytest.mark.parametrize("result, reason", [
    (response("refusal"), "refusal"),
    (response("end_turn", "  "), "empty"),
    (anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com")),
     "APIConnectionError"),
])
def test_errores_se_vuelven_generation_error(result: Any, reason: str) -> None:
    gen, _ = generator(result)
    with pytest.raises(GenerationError, match=reason):
        gen.generate("s", "p")


def test_construye_el_cliente_real_sin_llamar() -> None:
    gen = ClaudeTextGenerator("sk-ant-prueba", model="claude-sonnet-5-5", timeout_s=5)
    assert gen._model == "claude-sonnet-5-5"  # noqa: SLF001
