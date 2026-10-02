"""Offline migration test: the initial revision must render valid PostgreSQL DDL
without connecting to a database."""

import io
from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _offline_sql() -> str:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url", "postgresql+asyncpg://user:pass@localhost/clinical"
    )
    buffer = io.StringIO()
    config.output_buffer = buffer
    command.upgrade(config, "head", sql=True)
    return buffer.getvalue()


def test_initial_migration_renders_ddl() -> None:
    sql = _offline_sql()
    assert "CREATE TABLE cases" in sql
    assert "CREATE TABLE answer_options" in sql
    assert "CREATE TABLE submission_answers" in sql


def test_migration_enforces_non_negative_score() -> None:
    sql = _offline_sql()
    assert "score >= 0" in sql


def test_migration_has_composite_foreign_key() -> None:
    sql = _offline_sql()
    assert "fk_submission_answers_option_question" in sql
