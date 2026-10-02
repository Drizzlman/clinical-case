"""Unit tests for domain entity invariants (no framework, no database)."""

from decimal import Decimal

import pytest

from app.domain.entities import AnswerOption, Case, Question
from app.domain.errors import DomainValidationError


def option(score: str, position: int = 0) -> AnswerOption:
    return AnswerOption(text="option", score=Decimal(score), position=position)


def test_case_requires_at_least_one_question() -> None:
    with pytest.raises(DomainValidationError):
        Case(title="Case", questions=())


def test_case_title_must_not_be_empty() -> None:
    question = Question(text="q", position=0, options=(option("1"), option("0", 1)))
    with pytest.raises(DomainValidationError):
        Case(title="   ", questions=(question,))


def test_question_requires_two_options() -> None:
    with pytest.raises(DomainValidationError):
        Question(text="q", position=0, options=(option("1"),))


def test_option_score_must_be_non_negative() -> None:
    with pytest.raises(DomainValidationError):
        option("-0.5")


def test_question_positions_must_be_unique() -> None:
    with pytest.raises(DomainValidationError):
        Case(
            title="Case",
            questions=(
                Question(text="a", position=0, options=(option("1"), option("0", 1))),
                Question(text="b", position=0, options=(option("1"), option("0", 1))),
            ),
        )
