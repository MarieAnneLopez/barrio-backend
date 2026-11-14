"""Inicio de sesión, registro de visitantes y usuario actual (H21, D58)."""

from typing import Protocol

from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import EmailTakenError
from app.schemas.auth import RegisterIn


class InvalidCredentialsError(AppError):
    def __init__(self) -> None:
        # Mismo mensaje para correo desconocido, clave errada o cuenta inactiva.
        super().__init__("INVALID_CREDENTIALS", "Correo o contraseña incorrectos", 401)


class EmailInUseError(AppError):
    def __init__(self) -> None:
        super().__init__("EMAIL_TAKEN", "Ya existe una cuenta con ese correo", 409)


class UsuarioStore(Protocol):
    def by_email(self, email: str) -> Usuario | None: ...
    def get(self, user_id: int) -> Usuario | None: ...
    def add(self, usuario: Usuario) -> Usuario: ...


class AuthService:
    def __init__(self, store: UsuarioStore) -> None:
        self._store = store

    def login(self, email: str, password: str) -> Usuario:
        user = self._store.by_email(email)
        valid = verify_password(password, user.password_hash if user else None)
        if user is None or not valid or not user.activo:
            raise InvalidCredentialsError()
        return user

    def register(self, data: RegisterIn) -> Usuario:
        if self._store.by_email(data.email):
            raise EmailInUseError()
        user = Usuario(email=data.email, nombre=data.nombre, rol="visitante", activo=True,
                       password_hash=hash_password(data.password.get_secret_value()))
        try:
            return self._store.add(user)
        except EmailTakenError as exc:
            raise EmailInUseError() from exc

    def current(self, user_id: int) -> Usuario | None:
        user = self._store.get(user_id)
        return user if user is not None and user.activo else None
