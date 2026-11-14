"""POST /api/v1/chat: Mini Marie responde con el ModelProvider elegido en CHAT_MODEL (D59).

Abierto a visitantes sin sesión; 30 mensajes por minuto por IP, porque en
ambiente Nube cada mensaje puede ser una llamada pagada al LLM.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.deps import SessionDep, get_barrio_repository
from app.core.config import get_settings
from app.core.rate_limit import AttemptLimiter
from app.providers.factory import build_provider
from app.repositories.barrio_tools import SqlBarrioTools
from app.repositories.interfaces import BarrioRepository
from app.schemas.chat import ChatIn, ChatOut
from app.services.chat_agent import ChatAgent

router = APIRouter(tags=["chat"])


@lru_cache
def get_chat_limiter() -> AttemptLimiter:
    return AttemptLimiter(max_attempts=30, window_s=60)


def center_of(barrio: BarrioRepository) -> tuple[float, float]:
    west, south, east, north = barrio.polygon_feature()["bbox"]
    return (west + east) / 2, (south + north) / 2


def get_chat_agent(session: SessionDep,
                   barrio: Annotated[BarrioRepository, Depends(get_barrio_repository)]) -> ChatAgent:
    tools = SqlBarrioTools(session, center_of(barrio))
    return ChatAgent(build_provider(get_settings(), tools))


@router.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn, request: Request, agent: Annotated[ChatAgent, Depends(get_chat_agent)],
         limiter: Annotated[AttemptLimiter, Depends(get_chat_limiter)]) -> ChatOut:
    key = f"chat|{request.client.host if request.client else 'desconocido'}"
    limiter.check(key)
    limiter.hit(key)
    return agent.reply(payload)
