"""Use-case tests for submissions against in-memory adapters (no database)."""

from decimal import Decimal

import pytest

from app.domain.entities import Answer, AnswerOption, Case, Question
from app.domain.errors import DomainValidationError, NotFoundError
from app.domain.use_cases.get_submission import GetSubmission
from app.domain.use_cases.submit_answers import SubmitAnswers
from tests.fakes import InMemoryCaseRepository, InMemorySubmissionRepository


async def seed_case(repository: InMemoryCaseRepository) -> int:
    case = Case(
        title="MI",
        questions=(
            Question(
                text="Diagnosis?",
                position=0,
                options=(
                    AnswerOption(text="MI", score=Decimal("2"), position=0),
                    AnswerOption(text="Angina", score=Decimal("0"), position=1),
                ),
            ),
        ),
    )
    created = await repository.add(case)
    assert created.id is not None
    return created.id


async def test_submit_answers_scores_and_persists() -> None:
    cases = InMemoryCaseRepository()
    submissions = InMemorySubmissionRepository()
    case_id = await seed_case(cases)
    case = await cases.get(case_id)
    assert case is not None
    question = case.questions[0]
    assert question.id is not None
    correct_option = question.options[0]
    assert correct_option.id is not None

    submission, result = await SubmitAnswers(cases, submissions)(
        case_id, (Answer(question_id=question.id, option_id=correct_option.id),)
    )

    assert submission.id == 1
    assert result.earned == Decimal("2")
    assert result.percentage == Decimal("100")


async def test_submit_answers_missing_case_raises_not_found() -> None:
    cases = InMemoryCaseRepository()
    submissions = InMemorySubmissionRepository()

    with pytest.raises(NotFoundError):
        await SubmitAnswers(cases, submissions)(999, ())


async def test_submit_answers_rejects_incomplete_submission() -> None:
    cases = InMemoryCaseRepository()
    submissions = InMemorySubmissionRepository()
    case_id = await seed_case(cases)

    with pytest.raises(DomainValidationError):
        await SubmitAnswers(cases, submissions)(case_id, ())


async def test_get_submission_recomputes_score() -> None:
    cases = InMemoryCaseRepository()
    submissions = InMemorySubmissionRepository()
    case_id = await seed_case(cases)
    case = await cases.get(case_id)
    assert case is not None
    question = case.questions[0]
    assert question.id is not None
    wrong_option = question.options[1]
    assert wrong_option.id is not None
    submission, _ = await SubmitAnswers(cases, submissions)(
        case_id, (Answer(question_id=question.id, option_id=wrong_option.id),)
    )

    loaded, result = await GetSubmission(cases, submissions)(submission.id or 0)

    assert loaded.id == submission.id
    assert result.percentage == Decimal("0")


async def test_get_submission_missing_raises_not_found() -> None:
    cases = InMemoryCaseRepository()
    submissions = InMemorySubmissionRepository()

    with pytest.raises(NotFoundError):
        await GetSubmission(cases, submissions)(404)
