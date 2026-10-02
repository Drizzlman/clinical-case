"""initial normalized schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-01

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "case_id",
            sa.Integer(),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "kind",
            sa.String(length=32),
            server_default="single_choice",
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("case_id", "position", name="uq_questions_case_position"),
    )
    op.create_index("ix_questions_case_id", "questions", ["case_id"])

    op.create_table(
        "answer_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("score", sa.Numeric(10, 4), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "question_id", "position", name="uq_answer_options_question_position"
        ),
        sa.UniqueConstraint("id", "question_id", name="uq_answer_options_id_question"),
        sa.CheckConstraint("score >= 0", name="ck_answer_options_score_non_negative"),
    )
    op.create_index("ix_answer_options_question_id", "answer_options", ["question_id"])

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "case_id",
            sa.Integer(),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_submissions_case_id", "submissions", ["case_id"])

    op.create_table(
        "submission_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["option_id", "question_id"],
            ["answer_options.id", "answer_options.question_id"],
            name="fk_submission_answers_option_question",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "submission_id",
            "question_id",
            name="uq_submission_answers_submission_question",
        ),
    )
    op.create_index(
        "ix_submission_answers_submission_id", "submission_answers", ["submission_id"]
    )
    op.create_index(
        "ix_submission_answers_question_id", "submission_answers", ["question_id"]
    )


def downgrade() -> None:
    op.drop_table("submission_answers")
    op.drop_table("submissions")
    op.drop_table("answer_options")
    op.drop_table("questions")
    op.drop_table("cases")
