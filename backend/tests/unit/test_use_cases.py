"""Use-case tests against an in-memory adapter (no database, no Docker)."""

from decimal import Decimal

import pytest

from app.domain.entities import AnswerOption, Case, Question
from app.domain.errors import NotFoundError
from app.domain.use_cases.create_case import CreateCase
from app.domain.use_cases.get_case import GetCase
from app.domain.use_cases.list_cases import ListCases
from tests.fakes import InMemoryCaseRepository


def sample_case() -> Case:
    return Case(
        title="Myocardial infarction",
        description="58-year-old with chest pain",
        questions=(
            Question(
                text="Most likely diagnosis?",
                position=0,
                options=(
                    AnswerOption(text="MI", score=Decimal("1"), position=0),
                    AnswerOption(text="Angina", score=Decimal("0"), position=1),
                ),
            ),
        ),
    )


async def test_create_case_persists_and_assigns_id() -> None:
    repository = InMemoryCaseRepository()

    created = await CreateCase(repository)(sample_case())

    assert created.id == 1
    assert created.questions[0].id == 1
    assert created.questions[0].options[0].id == 1
    assert await repository.get(1) is not None


async def test_get_case_returns_stored_aggregate() -> None:
    repository = InMemoryCaseRepository()
    await CreateCase(repository)(sample_case())

    loaded = await GetCase(repository)(1)

    assert loaded.title == "Myocardial infarction"
    assert loaded.questions[0].options[1].text == "Angina"


async def test_get_case_missing_raises_not_found() -> None:
    repository = InMemoryCaseRepository()

    with pytest.raises(NotFoundError):
        await GetCase(repository)(999)


async def test_list_cases_returns_summaries() -> None:
    repository = InMemoryCaseRepository()
    await CreateCase(repository)(sample_case())

    summaries = await ListCases(repository)()

    assert len(summaries) == 1
    assert summaries[0].id == 1
    assert summaries[0].title == "Myocardial infarction"
    assert summaries[0].question_count == 1


async def test_list_cases_empty_returns_empty_tuple() -> None:
    repository = InMemoryCaseRepository()

    assert await ListCases(repository)() == ()
