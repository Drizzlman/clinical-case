"""Schema-level tests over the ORM metadata (no database connection required)."""

from sqlalchemy import CheckConstraint, UniqueConstraint

import app.data.models  # noqa: F401  (register models on metadata)
from app.data.base import Base

EXPECTED_TABLES = {
    "cases",
    "questions",
    "answer_options",
    "submissions",
    "submission_answers",
}


def test_all_tables_present() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_answer_option_score_check_constraint() -> None:
    table = Base.metadata.tables["answer_options"]
    checks = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    assert any("score >= 0" in str(c.sqltext) for c in checks)


def test_option_belongs_to_question_composite_fk() -> None:
    table = Base.metadata.tables["submission_answers"]
    composites = [fk for fk in table.foreign_key_constraints if len(fk.columns) == 2]
    assert any(
        {col.name for col in fk.columns} == {"option_id", "question_id"}
        for fk in composites
    )


def test_question_position_unique_per_case() -> None:
    table = Base.metadata.tables["questions"]
    uniques = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert any(
        {col.name for col in u.columns} == {"case_id", "position"} for u in uniques
    )


def test_foreign_keys_cascade_on_delete() -> None:
    for table_name in ("questions", "answer_options", "submissions"):
        table = Base.metadata.tables[table_name]
        assert all(fk.ondelete == "CASCADE" for fk in table.foreign_keys)
