"""MoERouter: Mixture of Experts que despacha cada consulta al experto de su dominio.

Ambiente Híbrido (PROMPT §4.1): lo espacial y catastral va al experto analítico
(local, sobre PostGIS), la historia y la localidad al experto documental (local)
y la conversación abierta al experto generativo (nube, con respaldo local).
"""

from app.providers.intents import DOMAINS, classify
from app.providers.model_provider import ChatQuery, ModelAnswer, ModelProvider

EXPERTS = ("espacial", "documental", "conversacional")


class MoERouter:
    name = "moe"

    def __init__(self, experts: dict[str, ModelProvider]) -> None:
        missing = set(EXPERTS) - set(experts)
        if missing:
            raise ValueError(f"Faltan expertos: {', '.join(sorted(missing))}")
        self._experts = experts

    def route(self, query: ChatQuery) -> str:
        return DOMAINS[classify(query).name]

    def answer(self, query: ChatQuery) -> ModelAnswer:
        domain = self.route(query)
        answer = self._experts[domain].answer(query)
        return answer.by(f"{self.name}:{answer.modelo}", domain)
