"""ChatAgent: Mini Marie como agente del sistema (PROMPT §4.1).

Percibe (mensaje, idioma, página y ubicación), razona con el ModelProvider
activo, que consulta las herramientas del barrio, y devuelve acciones para el
frontend: expresión del avatar, botones a módulos o al mapa y sugerencias.
"""

from dataclasses import asdict
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseUnavailableError
from app.providers.chat_guidance import safety_answer, static_reply
from app.providers.model_provider import ChatQuery, ModelProvider
from app.providers.named_place import PlaceLookup, answer_about_place
from app.providers.official_chat import official_answer
from app.repositories.barrio_repository import SeedUnavailableError
from app.schemas.chat import ChatIn, ChatOut

logger = logging.getLogger(__name__)


class ChatAgent:
    def __init__(self, provider: ModelProvider, find_place: PlaceLookup | None = None) -> None:
        self._provider = provider
        self._find_place = find_place

    def reply(self, payload: ChatIn) -> ChatOut:
        query = ChatQuery(payload.mensaje, payload.idioma, payload.ruta, payload.lon, payload.lat, payload.contexto_lugar)
        answer = safety_answer(query) or official_answer(query)
        if answer is None:
            try:
                place = self._find_place(query) if self._find_place else None
                answer = answer_about_place(place, query) if place else self._provider.answer(query)
            except (SQLAlchemyError, DatabaseUnavailableError, SeedUnavailableError):
                logger.warning("El chat usa orientación local por un fallo de datos", exc_info=False)
                answer = static_reply(query)
        data = asdict(answer)
        # Un botón que lleva a la página donde ya está la persona no ayuda.
        data["acciones"] = [a for a in data["acciones"] if a["ruta"] != payload.ruta]
        return ChatOut.model_validate(data)
