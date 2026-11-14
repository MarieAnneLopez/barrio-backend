"""Crea o actualiza la cuenta de administración desde ADMIN_EMAIL y ADMIN_PASSWORD (H21, D58).

Uso (desde barrio-backend/): python -m etl.runner --solo admin
Idempotente: si la cuenta existe, renueva su clave y la deja activa con rol admin.
Sin las dos variables no hace nada. La clave nunca se imprime.
"""

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import SqlUsuarioRepository
from app.schemas.auth import RegisterIn

MIN_ADMIN_PASSWORD = 12


def run(engine: Engine, settings: Settings | None = None) -> dict[str, str]:
    settings = settings or get_settings()
    password = settings.admin_password.get_secret_value()
    if not settings.admin_email or not password:
        return {"admin": "omitido: faltan ADMIN_EMAIL o ADMIN_PASSWORD"}
    if len(password) < MIN_ADMIN_PASSWORD:
        raise ValueError(f"ADMIN_PASSWORD debe tener al menos {MIN_ADMIN_PASSWORD} caracteres")
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
