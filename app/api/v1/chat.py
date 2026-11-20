"""POST /api/v1/chat: Mini Marie responde con el ModelProvider elegido en CHAT_MODEL (D59).

Abierto a visitantes sin sesión. Límites por visitante (D62), configurables en
.env: CHAT_MESSAGES_PER_MINUTE (30) y CHAT_MESSAGES_PER_HOUR (120, la
«sesión»), porque en ambiente Nube cada mensaje puede ser una llamada pagada.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import SessionDep, get_barrio_repository
from app.core.client_ip import client_key
from app.core.config import get_settings
from app.core.exceptions import DatabaseUnavailableError
from app.core.rate_limit import AttemptLimiter
from app.providers.factory import build_provider, provider_name
from app.repositories.barrio_tools import SqlBarrioTools
from app.repositories.interfaces import BarrioRepository
from app.repositories.named_chat_places import SqlNamedPlaces
from app.schemas.chat import ChatEstadoOut, ChatIn, ChatOut
from app.services.chat_agent import ChatAgent

router = APIRouter(tags=["chat"])


@lru_cache
def get_chat_limiter() -> AttemptLimiter:
    return AttemptLimiter(max_attempts=get_settings().chat_messages_per_minute, window_s=60)


@lru_cache
def get_chat_session_limiter() -> AttemptLimiter:
    return AttemptLimiter(max_attempts=get_settings().chat_messages_per_hour, window_s=3600)


def center_of(barrio: BarrioRepository) -> tuple[float, float]:
    try:
        west, south, east, north = (float(number) for number in barrio.polygon_feature()["bbox"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DatabaseUnavailableError() from exc
    return (west + east) / 2, (south + north) / 2


def get_chat_agent(session: SessionDep,
                   barrio: Annotated[BarrioRepository, Depends(get_barrio_repository)]) -> ChatAgent:
    tools = SqlBarrioTools(session, lambda: center_of(barrio))
    return ChatAgent(build_provider(get_settings(), tools), SqlNamedPlaces(session).find)


@router.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn, request: Request, agent: Annotated[ChatAgent, Depends(get_chat_agent)],
         limiter: Annotated[AttemptLimiter, Depends(get_chat_limiter)],
         session_limiter: Annotated[AttemptLimiter, Depends(get_chat_session_limiter)]) -> ChatOut:
    key = f"chat|{client_key(request)}"
    for current in (limiter, session_limiter):
        current.check(key)
    for current in (limiter, session_limiter):
        current.hit(key)
    return agent.reply(payload)


@router.get("/chat/estado", response_model=ChatEstadoOut)
def chat_estado() -> ChatEstadoOut:
    """Si el chat usa un proveedor externo (Gemini), el frontend avisa antes del primer mensaje."""
    return ChatEstadoOut(proveedor=provider_name(get_settings()))
