"""Domain entities (framework-free dataclasses).

Invariants are validated at construction time (``__post_init__``) so an invalid
aggregate cannot exist even transiently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.errors import DomainValidationError

DEFAULT_QUESTION_KIND = "single_choice"


@dataclass(slots=True)
class AnswerOption:
    """A selectable answer option with a non-negative score."""

    text: str
    score: Decimal
    position: int
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise DomainValidationError("Answer option text must not be empty")
        if self.score < 0:
            raise DomainValidationError("Answer option score must be non-negative")


@dataclass(slots=True)
class Question:
    """A question with at least two ordered options."""

    text: str
    position: int
    options: tuple[AnswerOption, ...]
    kind: str = DEFAULT_QUESTION_KIND
    id: int | None = None
    case_id: int | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise DomainValidationError("Question text must not be empty")
        if len(self.options) < 2:
            raise DomainValidationError("A question must have at least two answer options")
        positions = [option.position for option in self.options]
        if len(set(positions)) != len(positions):
            raise DomainValidationError("Answer option positions must be unique within a question")


@dataclass(slots=True)
class Case:
    """A clinical case aggregate: a titled, ordered collection of questions."""

    title: str
    questions: tuple[Question, ...]
    description: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise DomainValidationError("Case title must not be empty")
        if not self.questions:
            raise DomainValidationError("A case must have at least one question")
        positions = [question.position for question in self.questions]
        if len(set(positions)) != len(positions):
            raise DomainValidationError("Question positions must be unique within a case")


@dataclass(slots=True)
class Answer:
    """A selected option for a question."""

    question_id: int
    option_id: int


@dataclass(slots=True)
class Submission:
    """A record of answers submitted for a case."""

    case_id: int
    answers: tuple[Answer, ...]
    id: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class CaseSummary:
    """Lightweight projection of a case for listings (questions not loaded)."""

    id: int
    title: str
    description: str | None
    question_count: int
