"""AnalyticModel: clasifica la intención, extrae el módulo y responde con datos reales.

Ambiente Local (PROMPT §4.1): no usa internet ni claves. Es el modelo por
defecto y el respaldo determinista de GenerativeModel.
"""

from collections.abc import Callable

from app.providers import analytic_handlers as spatial
from app.providers import documental_handlers as documental
from app.providers.intents import Intent, classify
from app.providers.model_provider import ChatQuery, ModelAnswer
from app.providers.tools import BarrioTools

Handler = Callable[[Intent, ChatQuery, BarrioTools], ModelAnswer]

HANDLERS: dict[str, Handler] = {
    "categoria": spatial.category,
    "robos": spatial.category,
    "mejor_calificado": spatial.best,
    "cercania": spatial.nearby,
    "estadisticas": spatial.stats,
    "historia": documental.history,
    "localidad": documental.locality,
}


class AnalyticModel:
    name = "analitico"

    def __init__(self, tools: BarrioTools, experto: str | None = None) -> None:
        self._tools = tools
        self._experto = experto

    def answer(self, query: ChatQuery) -> ModelAnswer:
        intent = classify(query)
        handler = HANDLERS.get(intent.name, documental.conversation)
        return handler(intent, query, self._tools).by(self.name, self._experto)
