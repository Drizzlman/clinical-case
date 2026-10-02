from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.base import Base


class Case(Base):
    """A clinical case: a titled collection of ordered, scored questions."""

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    questions: Mapped[list[Question]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="Question.position",
    )
    submissions: Mapped[list[Submission]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )


class Question(Base):
    """A question within a case, ordered by ``position``."""

    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("case_id", "position", name="uq_questions_case_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(
        String(32), default="single_choice", server_default="single_choice"
    )
    position: Mapped[int] = mapped_column(Integer)

    case: Mapped[Case] = relationship(back_populates="questions")
    options: Mapped[list[AnswerOption]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="AnswerOption.position",
    )


class AnswerOption(Base):
    """A selectable answer option carrying a non-negative score."""

    __tablename__ = "answer_options"
    __table_args__ = (
        UniqueConstraint(
            "question_id", "position", name="uq_answer_options_question_position"
        ),
        UniqueConstraint("id", "question_id", name="uq_answer_options_id_question"),
        CheckConstraint("score >= 0", name="ck_answer_options_score_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    score: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))
    position: Mapped[int] = mapped_column(Integer)

    question: Mapped[Question] = relationship(back_populates="options")


class Submission(Base):
    """A single attempt at a case: a set of selected options."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    case: Mapped[Case] = relationship(back_populates="submissions")
    answers: Mapped[list[SubmissionAnswer]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
    )


class SubmissionAnswer(Base):
    """One selected option for one question of a submission.

    A composite foreign key ``(option_id, question_id) -> answer_options(id,
    question_id)`` guarantees at the database level that the selected option
    belongs to the referenced question.
    """

    __tablename__ = "submission_answers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["option_id", "question_id"],
            ["answer_options.id", "answer_options.question_id"],
            name="fk_submission_answers_option_question",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "submission_id", "question_id", name="uq_submission_answers_submission_question"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(Integer, index=True)
    option_id: Mapped[int] = mapped_column(Integer)

    submission: Mapped[Submission] = relationship(back_populates="answers")
