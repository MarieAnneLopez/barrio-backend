"""Contraseñas (bcrypt) y token de sesión (JWT HS256), H21 y D58.

El token solo lleva el id del usuario (`sub`) y su vencimiento: el rol se lee
de la base en cada petición, así que quitar el rol o desactivar la cuenta surte
efecto de inmediato.
"""

import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"
ROUNDS = 12
MIN_SECRET = 32
# Hash de relleno: el login con un correo desconocido tarda lo mismo que con uno real.
_DUMMY_HASH = bcrypt.hashpw(b"relleno-sin-uso", bcrypt.gensalt(ROUNDS)).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(ROUNDS)).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    """False ante hash ausente, inválido o clave de más de 72 bytes (bcrypt 5 los rechaza)."""
    try:
        return bcrypt.checkpw(password.encode(), (hashed or _DUMMY_HASH).encode()) and hashed is not None
    except ValueError:
        return False


@lru_cache
def signing_key() -> str:
    settings = get_settings()
    key = settings.jwt_secret.get_secret_value()
    if key:
        if len(key) < MIN_SECRET:
            raise RuntimeError(f"JWT_SECRET debe tener al menos {MIN_SECRET} caracteres")
        return key
    if settings.environment == "production":
        raise RuntimeError("JWT_SECRET es obligatorio en producción")
    return secrets.token_urlsafe(MIN_SECRET)


def create_access_token(user_id: int, now: datetime | None = None) -> str:
    issued = now or datetime.now(UTC)
    expires = issued + timedelta(minutes=get_settings().jwt_expire_minutes)
    claims = {"sub": str(user_id), "iat": issued, "exp": expires}
    return jwt.encode(claims, signing_key(), algorithm=ALGORITHM)


def user_id_from_token(token: str) -> int | None:
    """Id del usuario si el token es válido y vigente; None en cualquier otro caso."""
    try:
        claims = jwt.decode(token, signing_key(), algorithms=[ALGORITHM],
                            options={"require": ["exp", "iat", "sub"]})
        return int(claims["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None
