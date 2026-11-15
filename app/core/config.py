"""Configuración tipada desde variables de entorno / .env (pydantic-settings)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    """Valores de la API. La clave de la base nunca se imprime (SecretStr)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Reconoce tu Barrio: El Tintal API"
    environment: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api/v1"

    postgres_user: str = "barrio"
    postgres_password: SecretStr = SecretStr("")
    postgres_db: str = "barrio"
    # 127.0.0.1 y no "localhost": en Windows este resuelve primero a ::1, donde
    # Docker Desktop no publica el puerto y la conexión espera hasta el timeout.
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    db_connect_timeout_s: int = 3
    # Producción (D62): cadena completa del proveedor (p. ej. Neon, con sslmode=require).
    database_url_override: SecretStr = Field(SecretStr(""), validation_alias="DATABASE_URL")

    cors_origins: list[str] = ["http://localhost:5173"]
    seed_dir: Path = Path(__file__).resolve().parents[2] / "seed"

    # Sesión (H21, D58). Sin JWT_SECRET, fuera de producción se usa una clave
    # aleatoria por proceso (las sesiones caen al reiniciar); en producción es obligatoria.
    jwt_secret: SecretStr = SecretStr("")
    jwt_expire_minutes: int = 60
    admin_email: str = ""
    admin_password: SecretStr = SecretStr("")
    admin_nombre: str = "Administración"

    # Chat (H22, D59): analitico = Local (por defecto), generativo = Nube, moe = Híbrido.
    chat_model: Literal["analitico", "generativo", "moe"] = "analitico"
    anthropic_api_key: SecretStr = SecretStr("")
    chat_llm_model: str = "claude-opus-5-5"
    # Límites del chat por visitante (D62): por minuto y por sesión de una hora.
    chat_messages_per_minute: int = 30
    chat_messages_per_hour: int = 120
    # Proxy del frontend publicado (D62): solo con esta clave se cree la IP que reenvía.
    proxy_secret: SecretStr = SecretStr("")

    @property
    def database_url(self) -> URL:
        """URL de SQLAlchemy (driver psycopg 3); la clave queda enmascarada al imprimirla."""
        override = self.database_url_override.get_secret_value()
        if override:
            return make_url(override).set(drivername="postgresql+psycopg")
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def docs_enabled(self) -> bool:
        return self.environment != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
