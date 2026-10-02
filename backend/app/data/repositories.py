"""SQLAlchemy adapter implementing the domain ``CaseRepository`` port.

Maps between ORM models (``app.data.models``) and framework-free domain entities.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.data import models
from app.domain.entities import Answer as DomainAnswer
from app.domain.entities import AnswerOption as DomainAnswerOption
from app.domain.entities import Case as DomainCase
from app.domain.entities import CaseSummary as DomainCaseSummary
from app.domain.entities import Question as DomainQuestion
from app.domain.entities import Submission as DomainSubmission


class SqlAlchemyCaseRepository:
    """Persist and load ``Case`` aggregates using an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, case: DomainCase) -> DomainCase:
        model = self._to_model(case)
        self._session.add(model)
        await self._session.commit()
        return self._to_domain(model)

    async def get(self, case_id: int) -> DomainCase | None:
        statement = (
            select(models.Case)
            .where(models.Case.id == case_id)
            .options(selectinload(models.Case.questions).selectinload(models.Question.options))
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def list_summaries(self) -> tuple[DomainCaseSummary, ...]:
        """Return one row per case with its question count (single aggregate query)."""
        statement = (
            select(
                models.Case.id,
                models.Case.title,
                models.Case.description,
                func.count(models.Question.id).label("question_count"),
            )
            .outerjoin(models.Question, models.Question.case_id == models.Case.id)
            .group_by(models.Case.id, models.Case.title, models.Case.description)
            .order_by(models.Case.id)
        )
        rows = (await self._session.execute(statement)).all()
        return tuple(
            DomainCaseSummary(
                id=row.id,
                title=row.title,
                description=row.description,
                question_count=row.question_count,
            )
            for row in rows
        )

    @staticmethod
    def _to_model(case: DomainCase) -> models.Case:
        return models.Case(
            title=case.title,
            description=case.description,
            questions=[
                models.Question(
                    text=question.text,
                    kind=question.kind,
                    position=question.position,
                    options=[
                        models.AnswerOption(
                            text=option.text,
                            score=option.score,
                            position=option.position,
                        )
                        for option in question.options
                    ],
                )
                for question in case.questions
            ],
        )

    @staticmethod
    def _to_domain(model: models.Case) -> DomainCase:
        return DomainCase(
            id=model.id,
            title=model.title,
            description=model.description,
            questions=tuple(
                DomainQuestion(
                    id=question.id,
                    case_id=question.case_id,
                    text=question.text,
                    kind=question.kind,
                    position=question.position,
                    options=tuple(
                        DomainAnswerOption(
                            id=option.id,
                            text=option.text,
                            score=option.score,
                            position=option.position,
                        )
                        for option in question.options
                    ),
                )
                for question in model.questions
            ),
        )


class SqlAlchemySubmissionRepository:
    """Persist and load ``Submission`` aggregates using an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, submission: DomainSubmission) -> DomainSubmission:
        model = models.Submission(
            case_id=submission.case_id,
            answers=[
                models.SubmissionAnswer(
                    question_id=answer.question_id,
                    option_id=answer.option_id,
                )
                for answer in submission.answers
            ],
        )
        self._session.add(model)
        await self._session.commit()
        return self._to_domain(model)

    async def get(self, submission_id: int) -> DomainSubmission | None:
        statement = (
            select(models.Submission)
            .where(models.Submission.id == submission_id)
            .options(selectinload(models.Submission.answers))
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    @staticmethod
    def _to_domain(model: models.Submission) -> DomainSubmission:
        return DomainSubmission(
            id=model.id,
            case_id=model.case_id,
            created_at=model.created_at,
            answers=tuple(
                DomainAnswer(question_id=answer.question_id, option_id=answer.option_id)
                for answer in model.answers
            ),
        )
