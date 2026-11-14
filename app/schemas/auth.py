"""Contratos de /api/v1/auth (H21, D58). La clave nunca sale en una respuesta."""

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, SecretStr, StringConstraints

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
Email = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=254,
                                         pattern=EMAIL_PATTERN)]


def _bcrypt_limit(value: SecretStr) -> SecretStr:
    if len(value.get_secret_value().encode()) > 72:
        raise ValueError("La contraseña no puede pasar de 72 bytes")
    return value


Password = Annotated[SecretStr, Field(min_length=1, max_length=72), AfterValidator(_bcrypt_limit)]
NewPassword = Annotated[SecretStr, Field(min_length=8, max_length=72), AfterValidator(_bcrypt_limit)]


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: Email
    password: Password


class RegisterIn(BaseModel):
    """Registro público: siempre crea una cuenta de visitante."""

    model_config = ConfigDict(extra="forbid")
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    email: Email
    password: NewPassword


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nombre: str
    rol: Literal["admin", "visitante"]


class SesionOut(BaseModel):
    """El token viaja solo en la cookie httpOnly; aquí va quién inició sesión y cuánto dura."""

    usuario: UsuarioOut
    expires_in: int
