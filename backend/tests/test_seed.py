"""Tests for the built-in dataset and idempotent seeding (no database required)."""

from __future__ import annotations

from app.domain.entities import Case
from app.seed import default_cases, seed_default_cases
from tests.fakes import InMemoryCaseRepository


def test_default_cases_are_valid_and_uniquely_titled() -> None:
    cases = default_cases()
    assert cases
    titles = [case.title for case in cases]
    assert len(set(titles)) == len(titles)
    for case in cases:
        assert isinstance(case, Case)
        assert case.questions
        for question in case.questions:
            assert len(question.options) >= 2


async def test_seed_creates_every_case_on_empty_database() -> None:
    repository = InMemoryCaseRepository()

    created = await seed_default_cases(repository, set())

    assert created == len(default_cases())
    stored = await repository.get(1)
    assert stored is not None
    assert stored.title == default_cases()[0].title
    assert len(stored.questions) == len(default_cases()[0].questions)


async def test_seed_is_idempotent() -> None:
    repository = InMemoryCaseRepository()
    await seed_default_cases(repository, set())
    titles = {case.title for case in default_cases()}

    created_again = await seed_default_cases(repository, titles)

    assert created_again == 0


async def test_seed_only_creates_missing_titles() -> None:
    repository = InMemoryCaseRepository()
    existing_title = default_cases()[0].title

    created = await seed_default_cases(repository, {existing_title})

    assert created == len(default_cases()) - 1
