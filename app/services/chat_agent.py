"""ChatAgent: Mini Marie como agente del sistema (PROMPT §4.1).

Percibe (mensaje, idioma, página y ubicación), razona con el ModelProvider
activo, que consulta las herramientas del barrio, y devuelve acciones para el
frontend: expresión del avatar, botones a módulos o al mapa y sugerencias.
"""

from dataclasses import asdict

from app.providers.model_provider import ChatQuery, ModelProvider
from app.schemas.chat import ChatIn, ChatOut


class ChatAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    def reply(self, payload: ChatIn) -> ChatOut:
        query = ChatQuery(payload.mensaje, payload.idioma, payload.ruta, payload.lon, payload.lat)
        answer = self._provider.answer(query)
        data = asdict(answer)
        # Un botón que lleva a la página donde ya está la persona no ayuda.
        data["acciones"] = [a for a in data["acciones"] if a["ruta"] != payload.ruta]
        return ChatOut.model_validate(data)
