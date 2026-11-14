"""Guardas de autorización (H21, D58): sesión por cookie httpOnly con JWT.

require_user: cualquier cuenta activa (calificar). require_admin: rol admin
(escrituras del CRUD y de la galería). Sin sesión válida responden 401; un
visitante que intenta una escritura de admin recibe 403.
"""

from typing import Annotated

from fastapi import Depends, Request

from app.api.deps import SessionDep
from app.core.exceptions import AppError
from app.core.security import user_id_from_token
from app.models.usuario import Usuario
from app.repositories.usuario_repository import SqlUsuarioRepository
from app.services.auth_service import AuthService

SESSION_COOKIE = "mm_session"


class AuthRequiredError(AppError):
    def __init__(self, message: str = "Inicia sesión con una cuenta de administración") -> None:
        super().__init__("AUTH_REQUIRED", message, 401)


class ForbiddenError(AppError):
    def __init__(self) -> None:
        super().__init__("FORBIDDEN", "Esta acción es solo para la cuenta de administración", 403)


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(SqlUsuarioRepository(session))


AuthDep = Annotated[AuthService, Depends(get_auth_service)]


def current_user(request: Request, service: AuthDep) -> Usuario | None:
    token = request.cookies.get(SESSION_COOKIE)
    user_id = user_id_from_token(token) if token else None
    return service.current(user_id) if user_id is not None else None


MaybeUser = Annotated[Usuario | None, Depends(current_user)]


def require_user(user: MaybeUser) -> Usuario:
    """Calificar exige sesión (visitante o admin)."""
    if user is None:
        raise AuthRequiredError("Inicia sesión para calificar")
    return user


def require_admin(user: MaybeUser) -> Usuario:
    if user is None:
        raise AuthRequiredError()
    if user.rol != "admin":
        raise ForbiddenError()
    return user
