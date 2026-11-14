"""/api/v1/auth: login, registro de visitantes, sesión actual y cierre (H21, D58).

El JWT viaja solo en una cookie httpOnly, SameSite=Strict y con Path=/api: el
JavaScript del frontend no puede leerlo y el navegador no lo manda desde otros
sitios. Login y registro tienen límite de intentos por IP.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.guards import SESSION_COOKIE, AuthDep, require_user
from app.core.config import get_settings
from app.core.rate_limit import AttemptLimiter
from app.core.security import create_access_token
from app.models.usuario import Usuario
from app.schemas.auth import LoginIn, RegisterIn, SesionOut, UsuarioOut
from app.services.auth_service import InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_PATH = "/api"


@lru_cache
def get_limiter() -> AttemptLimiter:
    return AttemptLimiter()


Limiter = Annotated[AttemptLimiter, Depends(get_limiter)]


def _client(request: Request) -> str:
    return request.client.host if request.client else "desconocido"


def _open_session(response: Response, user: Usuario) -> SesionOut:
    settings = get_settings()
    max_age = settings.jwt_expire_minutes * 60
    response.set_cookie(SESSION_COOKIE, create_access_token(user.id), max_age=max_age, path=COOKIE_PATH,
                        httponly=True, samesite="strict", secure=settings.environment == "production")
    return SesionOut(usuario=UsuarioOut.model_validate(user), expires_in=max_age)


@router.post("/login", response_model=SesionOut)
def login(payload: LoginIn, request: Request, response: Response, service: AuthDep,
          limiter: Limiter) -> SesionOut:
    key = f"login|{_client(request)}|{payload.email}"
    limiter.check(key)
    try:
        user = service.login(payload.email, payload.password.get_secret_value())
    except InvalidCredentialsError:
        limiter.hit(key)
        raise
    limiter.reset(key)
    return _open_session(response, user)


@router.post("/register", response_model=SesionOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, request: Request, response: Response, service: AuthDep,
             limiter: Limiter) -> SesionOut:
    key = f"register|{_client(request)}"
    limiter.check(key)
    limiter.hit(key)
    return _open_session(response, service.register(payload))


@router.get("/me", response_model=UsuarioOut)
def me(user: Annotated[Usuario, Depends(require_user)]) -> Usuario:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path=COOKIE_PATH, httponly=True, samesite="strict")
    return response
