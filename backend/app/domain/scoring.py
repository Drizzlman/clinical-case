"""Pure scoring rules for a clinical case (framework-free domain logic)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.domain.entities import Answer, Case
from app.domain.errors import DomainValidationError

_HUNDRED = Decimal("100")
_TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class QuestionScore:
    question_id: int
    selected_option_id: int
    score: Decimal
    max_score: Decimal


@dataclass(frozen=True, slots=True)
class ScoreResult:
    earned: Decimal
    maximum: Decimal
    percentage: Decimal
    per_question: tuple[QuestionScore, ...]


def compute_score(case: Case, answers: tuple[Answer, ...]) -> ScoreResult:
    """Compute earned/maximum/percentage for a complete submission.

    Raises ``DomainValidationError`` if answers do not cover exactly the case's
    questions or reference an option that does not belong to its question.
    """
    answer_by_question = {answer.question_id: answer.option_id for answer in answers}
    if len(answer_by_question) != len(answers):
        raise DomainValidationError("A question must not be answered more than once")

    questions_by_id = {
        question.id: question for question in case.questions if question.id is not None
    }
    if set(answer_by_question) != set(questions_by_id):
        raise DomainValidationError("Answers must cover exactly the case questions")

    per_question: list[QuestionScore] = []
    earned = Decimal("0")
    maximum = Decimal("0")
    for question_id, question in questions_by_id.items():
        selected_id = answer_by_question[question_id]
        options_by_id = {option.id: option for option in question.options}
        selected = options_by_id.get(selected_id)
        if selected is None:
            raise DomainValidationError(
                f"Option {selected_id} does not belong to question {question_id}"
            )
        question_max = max(option.score for option in question.options)
        earned += selected.score
        maximum += question_max
        per_question.append(
            QuestionScore(
                question_id=question_id,
                selected_option_id=selected_id,
                score=selected.score,
                max_score=question_max,
            )
        )

    percentage = (
        Decimal("0")
        if maximum == 0
        else (earned / maximum * _HUNDRED).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    )
    return ScoreResult(
        earned=earned,
        maximum=maximum,
        percentage=percentage,
        per_question=tuple(per_question),
    )
