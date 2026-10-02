"""Unit tests for the pure scoring rules (no framework, no database)."""

from decimal import Decimal

import pytest

from app.domain.entities import Answer, AnswerOption, Case, Question
from app.domain.errors import DomainValidationError
from app.domain.scoring import compute_score


def option(option_id: int, score: str, position: int) -> AnswerOption:
    return AnswerOption(
        id=option_id, text=f"option-{option_id}", score=Decimal(score), position=position
    )


def case_with_ids() -> Case:
    return Case(
        id=1,
        title="MI",
        questions=(
            Question(
                id=10,
                case_id=1,
                text="Diagnosis?",
                position=0,
                options=(option(100, "2", 0), option(101, "0", 1)),
            ),
            Question(
                id=11,
                case_id=1,
                text="ECG?",
                position=1,
                options=(option(102, "1", 0), option(103, "0", 1)),
            ),
        ),
    )


def test_score_sums_selected_options() -> None:
    result = compute_score(
        case_with_ids(),
        (Answer(question_id=10, option_id=100), Answer(question_id=11, option_id=103)),
    )

    assert result.earned == Decimal("2")
    assert result.maximum == Decimal("3")
    assert result.percentage == Decimal("66.67")


def test_perfect_submission_is_one_hundred_percent() -> None:
    result = compute_score(
        case_with_ids(),
        (Answer(question_id=10, option_id=100), Answer(question_id=11, option_id=102)),
    )

    assert result.earned == result.maximum
    assert result.percentage == Decimal("100")


def test_zero_maximum_yields_zero_percentage() -> None:
    case = Case(
        id=1,
        title="Zero",
        questions=(
            Question(
                id=20,
                case_id=1,
                text="Q",
                position=0,
                options=(option(200, "0", 0), option(201, "0", 1)),
            ),
        ),
    )

    result = compute_score(case, (Answer(question_id=20, option_id=200),))

    assert result.maximum == 0
    assert result.percentage == Decimal("0")


def test_option_from_another_question_is_rejected() -> None:
    with pytest.raises(DomainValidationError):
        compute_score(
            case_with_ids(),
            (Answer(question_id=10, option_id=102), Answer(question_id=11, option_id=103)),
        )


def test_missing_answer_is_rejected() -> None:
    with pytest.raises(DomainValidationError):
        compute_score(case_with_ids(), (Answer(question_id=10, option_id=100),))


def test_duplicate_answer_is_rejected() -> None:
    with pytest.raises(DomainValidationError):
        compute_score(
            case_with_ids(),
            (
                Answer(question_id=10, option_id=100),
                Answer(question_id=10, option_id=101),
            ),
        )
