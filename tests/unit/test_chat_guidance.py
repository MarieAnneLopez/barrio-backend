"""Orientación local y consultas acotadas de Mini Marie."""

import httpx
import pytest

from app.providers import official_chat, official_reader
from app.providers.analytic_model import AnalyticModel
from app.providers.model_provider import ChatQuery
from app.schemas.chat import ChatIn
from app.services.chat_agent import ChatAgent
from tests.unit.chat_fakes import FakeTools


def test_followup_checks_only_the_official_library_page(monkeypatch: pytest.MonkeyPatch) -> None:
    page = '<div class="node-field-field-horario-string-long"><div>Horario</div><div>'
    page += '<p>Martes a sábado, 8:00 a. m.</p></div></div>'
    calls = []

    def response(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, text=page, headers={"content-type": "text/html"})

    monkeypatch.setattr(official_reader, "_transport", httpx.MockTransport(response))
    agent = ChatAgent(AnalyticModel(FakeTools()))
    first = agent.reply(ChatIn(mensaje="¿Dónde está la Biblioteca El Tintal?"))
    followup = agent.reply(ChatIn(mensaje="And the opening hours?", idioma="en", contexto_lugar=first.lugar))
    assert "published hours" in followup.texto
    assert followup.lugar == first.lugar == official_chat.LIBRARY
    assert followup.fuentes[0].url == official_chat.LIBRARY_URL
    assert followup.fuentes[0].consultado_en is not None
    assert calls == [official_chat.LIBRARY_URL]


def test_safe_guidance_precedes_database_or_cloud() -> None:
    class BrokenProvider:
        def answer(self, query: ChatQuery):
            raise AssertionError("Emergency must be handled before any provider")

    reply = ChatAgent(BrokenProvider()).reply(ChatIn(mensaje="Me están robando ahora"))  # type: ignore[arg-type]
    assert "123" in reply.texto and reply.expresion == "alert"


def test_contact_for_hospital_does_not_send_user_to_creator() -> None:
    agent = ChatAgent(AnalyticModel(FakeTools()))
    reply = agent.reply(ChatIn(mensaje="¿Cuál es el teléfono del hospital?"))
    assert reply.acciones[0].ruta == "/categorias/atencion-inmediata"


def test_library_contact_includes_verified_number_and_source() -> None:
    agent = ChatAgent(AnalyticModel(FakeTools()))
    reply = agent.reply(ChatIn(mensaje="Busco el teléfono de la biblioteca"))
    assert "(601) 5803060" in reply.texto and "1000" in reply.texto
    assert reply.fuentes[0].url == official_chat.LIBRARY_URL
    assert reply.lugar == official_chat.LIBRARY


def test_database_failure_returns_local_guidance_in_user_language() -> None:
    from sqlalchemy.exc import OperationalError

    def offline(query: ChatQuery):
        raise OperationalError("lookup", {}, RuntimeError())

    agent = ChatAgent(AnalyticModel(FakeTools()), offline)
    reply = agent.reply(ChatIn(mensaje="Which bookstores are there?", idioma="en"))
    assert "Bookstores" in reply.texto and reply.acciones[0].ruta == "/categorias/librerias"
