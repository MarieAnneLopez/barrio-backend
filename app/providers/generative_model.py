"""GenerativeModel: redacta la respuesta con un LLM sobre el contenido público del sitio.

Ambiente Nube (PROMPT §4.1, H36). Primero pide al modelo analítico la respuesta con
datos reales (intención, acciones, hechos); el LLM redacta con esos DATOS y con el
CONTEXTO público de la plataforma (site_context), sin inventar lugares ni rutas.
Sin credencial, o si el LLM falla o se niega, entrega la respuesta analítica tal
cual (respaldo determinista).
"""

from collections.abc import Callable
from typing import Protocol

from app.providers.model_provider import ChatQuery, Language, ModelAnswer, ModelProvider
from app.providers.prompts import SYSTEM

MAX_REPLY_CHARS = 700
ContextSource = Callable[[Language], str]


class GenerationError(Exception):
    """El proveedor del LLM no respondió, se negó o devolvió texto vacío."""


class TextGenerator(Protocol):
    def generate(self, system: str, prompt: str) -> str: ...


def grounding(query: ChatQuery, base: ModelAnswer, context: str = "") -> str:
    facts = "\n".join(f"- {f.nombre} ({f.categoria_slug or '-'}; {f.detalle or ''})" for f in base.datos)
    es = query.idioma == "es"
    label, ctx = ("DATOS", "CONTEXTO") if es else ("DATA", "CONTEXT")
    block = f"{ctx}:\n{context}\n\n" if context else ""
    return (f"{block}{label}:\nRespuesta verificada: {base.texto}\n{facts}\n\n"
            f"Mensaje de la persona:\n<<<{query.texto}>>>")


class GenerativeModel:
    name = "generativo"

    def __init__(self, grounding_model: ModelProvider, generator: TextGenerator | None = None,
                 context: ContextSource | None = None) -> None:
        self._base = grounding_model
        self._generator = generator
        self._context = context

    @property
    def configured(self) -> bool:
        return self._generator is not None

    def answer(self, query: ChatQuery) -> ModelAnswer:
        base = self._base.answer(query)
        if self._generator is None:
            return base.by("generativo:respaldo")
        context = self._context(query.idioma) if self._context else ""
        try:
            text = self._generator.generate(SYSTEM[query.idioma], grounding(query, base, context)).strip()
        except GenerationError:
            return base.by("generativo:respaldo")
        if not text:
            return base.by("generativo:respaldo")
        return ModelAnswer(base.intent, text[:MAX_REPLY_CHARS], base.expresion, self.name, base.experto,
                           base.acciones, base.sugerencias, base.datos)
