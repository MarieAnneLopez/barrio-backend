"""Usuarios de prueba creados directo en barrio_test (sin pasar por la API)."""

from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import SqlUsuarioRepository

PASSWORD = "clave-de-prueba-123"


def make_user(session: Session, email: str, rol: str = "visitante", activo: bool = True) -> Usuario:
    user = Usuario(email=email, nombre=f"Prueba {rol}", rol=rol, activo=activo,
                   password_hash=hash_password(PASSWORD))
    return SqlUsuarioRepository(session).add(user)


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> int:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return response.status_code
