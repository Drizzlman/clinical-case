"""Settings: database configuration comes from the environment, fail fast if absent."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings

_DB_ENV_KEYS = (
    "DATABASE_URL",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
)


@pytest.fixture
def no_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _DB_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_missing_database_config_raises(no_db_env: None) -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL or all POSTGRES"):
        Settings(_env_file=None)


def test_environment_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    with pytest.raises(ValidationError):
        Settings(cors_origins=["http://localhost:3000"], _env_file=None)


def test_resolved_database_url_is_assembled_from_parts() -> None:
    settings = Settings(
        environment="development",
        cors_origins=["http://localhost:3000"],
        postgres_user="user",
        postgres_password="p@ss",
        postgres_host="db",
        postgres_port=6543,
        postgres_db="clinical",
        _env_file=None,
    )

    assert (
        settings.resolved_database_url
        == "postgresql+asyncpg://user:p%40ss@db:6543/clinical"
    )


def test_explicit_database_url_is_used_without_parts() -> None:
    settings = Settings(
        environment="production",
        cors_origins=["https://example.com"],
        database_url="postgresql+asyncpg://u:p@host:5432/db",
        _env_file=None,
    )

    assert settings.resolved_database_url == "postgresql+asyncpg://u:p@host:5432/db"


def test_explicit_database_url_overrides_parts() -> None:
    settings = Settings(
        environment="production",
        cors_origins=["https://example.com"],
        database_url="postgresql+asyncpg://u:p@host:5432/db",
        postgres_user="ignored",
        postgres_password="ignored",
        postgres_host="ignored",
        postgres_port=1,
        postgres_db="ignored",
        _env_file=None,
    )

    assert settings.resolved_database_url == "postgresql+asyncpg://u:p@host:5432/db"
