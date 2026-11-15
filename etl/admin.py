"""Crea o actualiza la cuenta de administración desde ADMIN_EMAIL y ADMIN_PASSWORD (H21, D58).

Uso (desde barrio-backend/): python -m etl.runner --solo admin
Idempotente: si la cuenta existe, renueva su clave y la deja activa con rol admin.
Sin las dos variables no hace nada. La clave nunca se imprime. En producción
se rechaza la clave de demostración de .env.example (D62).
"""

from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import SqlUsuarioRepository
from app.schemas.auth import RegisterIn

MIN_ADMIN_PASSWORD = 12
EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"


def demo_password(example: Path = EXAMPLE) -> str | None:
    """La clave de demostración documentada en .env.example (para no repetirla en código)."""
    if not example.exists():
        return None
    for line in example.read_text(encoding="utf-8").splitlines():
        if line.startswith("ADMIN_PASSWORD="):
            return line.split("=", 1)[1].strip() or None
    return None


def check(settings: Settings) -> str | None:
    """Valida la clave configurada; None si no hay cuenta que crear. Falla antes de tocar la base."""
    password = settings.admin_password.get_secret_value()
    if not settings.admin_email or not password:
        return None
    if len(password) < MIN_ADMIN_PASSWORD:
        raise ValueError(f"ADMIN_PASSWORD debe tener al menos {MIN_ADMIN_PASSWORD} caracteres")
    if settings.environment == "production" and password == demo_password():
        raise ValueError("En producción ADMIN_PASSWORD no puede ser la clave de demostración de .env.example")
    return password


def run(engine: Engine, settings: Settings | None = None) -> dict[str, str]:
    settings = settings or get_settings()
    password = check(settings)
    if password is None:
        return {"admin": "omitido: faltan ADMIN_EMAIL o ADMIN_PASSWORD"}
    data = RegisterIn.model_validate({"nombre": settings.admin_nombre, "email": settings.admin_email,
                                      "password": password})
    with Session(engine) as session:
        repo = SqlUsuarioRepository(session)
        user = repo.by_email(data.email)
        if user is None:
            repo.add(Usuario(email=data.email, nombre=data.nombre, rol="admin", activo=True,
                             password_hash=hash_password(password)))
            return {"admin": f"creada {data.email}"}
        user.rol, user.activo, user.nombre = "admin", True, data.nombre
        user.password_hash = hash_password(password)
        session.commit()
        return {"admin": f"actualizada {data.email}"}
