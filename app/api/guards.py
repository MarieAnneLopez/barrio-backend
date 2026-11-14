"""Guardas de autorización de las escrituras del CRUD.

Seguro por defecto: hasta que exista la autenticación JWT (H21), toda
escritura responde 401. H21 reemplaza esta dependencia por la verificación
real del rol admin; los routers no cambian.
"""

from app.core.exceptions import AppError


class AuthRequiredError(AppError):
    def __init__(self) -> None:
        super().__init__("AUTH_REQUIRED", "Inicia sesión con una cuenta de administración", 401)


def require_admin() -> None:
    raise AuthRequiredError()
