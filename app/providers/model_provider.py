"""Contrato común de los modelos del chat de Mini Marie (PROMPT §4.1, Strategy + Factory).

AnalyticModel, GenerativeModel y MoERouter cumplen ModelProvider y se
sustituyen sin que el agente ni la API cambien (Liskov): todos reciben una
ChatQuery y devuelven una ModelAnswer con el mismo significado.
"""

from dataclasses import dataclass, field, replace
from typing import Literal, Protocol

Language = Literal["es", "en"]
# Estados del avatar del frontend (avatarStateMachine.ts) que el chat puede pedir.
Expression = Literal["idle", "wave", "jump", "alert", "sad"]


@dataclass(frozen=True)
class ChatQuery:
    texto: str
    idioma: Language = "es"
    # Contexto que percibe el agente: página actual y ubicación (si la hay).
    ruta: str | None = None
    lon: float | None = None
    lat: float | None = None


@dataclass(frozen=True)
class ChatAction:
    """Botón de acción rápida: lleva a una ruta interna del frontend."""

    ruta: str
    etiqueta: str


@dataclass(frozen=True)
class Fact:
    """Dato del barrio que respalda la respuesta (para mostrarlo o para el LLM)."""

    nombre: str
    categoria_slug: str | None = None
    objeto_id: int | None = None
    detalle: str | None = None


@dataclass(frozen=True)
class ModelAnswer:
    intent: str
    texto: str
    expresion: Expression
    modelo: str
    experto: str | None = None
    acciones: tuple[ChatAction, ...] = ()
    sugerencias: tuple[str, ...] = ()
    datos: tuple[Fact, ...] = field(default_factory=tuple)

    def by(self, modelo: str, experto: str | None = None) -> "ModelAnswer":
        """La misma respuesta firmada por otro modelo (respaldo o enrutador)."""
        return replace(self, modelo=modelo, experto=experto if experto is not None else self.experto)


class ModelProvider(Protocol):
    name: str

    def answer(self, query: ChatQuery) -> ModelAnswer: ...
