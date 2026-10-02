from functools import lru_cache
from pathlib import Path
from typing import Self
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path (not CWD-relative) so each service owns its own `.env`.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from the environment (and backend/.env).

    Every value comes from the environment; nothing is hardcoded here. The only
    optional field is ``database_url`` — an explicit override for production
    (Cloud Run Secret Manager) that takes precedence over the ``POSTGRES_*``
    parts used locally.
    """

    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_prefix="", extra="ignore")

    environment: str
    cors_origins: list[str]

    database_url: str | None = None

    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    postgres_db: str | None = None

    @model_validator(mode="after")
    def _require_database_config(self) -> Self:
        """Fail fast unless a full ``DATABASE_URL`` or all ``POSTGRES_*`` are set."""

        if self.database_url:
            return self
        parts = {
            "POSTGRES_USER": self.postgres_user,
            "POSTGRES_PASSWORD": self.postgres_password,
            "POSTGRES_HOST": self.postgres_host,
            "POSTGRES_PORT": self.postgres_port,
            "POSTGRES_DB": self.postgres_db,
        }
        missing = [name for name, value in parts.items() if value is None or value == ""]
        if missing:
            raise ValueError(
                "Set DATABASE_URL or all POSTGRES_* variables; missing: " + ", ".join(missing)
            )
        return self

    @property
    def resolved_database_url(self) -> str:
        """Return the effective SQLAlchemy URL (explicit URL wins over parts)."""

        if self.database_url:
            return self.database_url
        user, password = self.postgres_user, self.postgres_password
        host, port, db = self.postgres_host, self.postgres_port, self.postgres_db
        if user is None or password is None or host is None or port is None or db is None:
            raise RuntimeError("database configuration is incomplete")
        return f"postgresql+asyncpg://{user}:{quote_plus(password)}@{host}:{port}/{db}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the settings, constructed and cached on first use (not at import)."""

    return Settings()
