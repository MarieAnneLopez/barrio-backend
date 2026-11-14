"""Configuración tipada desde variables de entorno / .env (pydantic-settings)."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


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

    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def database_url(self) -> URL:
        """URL de SQLAlchemy (driver psycopg 3); la clave queda enmascarada al imprimirla."""
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
