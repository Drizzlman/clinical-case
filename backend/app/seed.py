"""Default clinical cases and idempotent database seeding.

The dataset is expressed as framework-free domain aggregates and persisted through
the ``CaseRepository`` port, so the domain (not SQL) owns validation. Seeding is
idempotent: a case whose title already exists is skipped, making the command safe
to re-run after every migration or container restart.

Usage (from ``backend/``):

    backend/.venv/Scripts/python -m app.seed
"""

from __future__ import annotations

import asyncio
from collections.abc import Collection
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Case as CaseModel
from app.data.repositories import SqlAlchemyCaseRepository
from app.data.session import get_session_factory
from app.domain.entities import AnswerOption, Case, Question
from app.domain.ports import CaseRepository


def _option(text: str, score: str, position: int) -> AnswerOption:
    return AnswerOption(text=text, score=Decimal(score), position=position)


def default_cases() -> tuple[Case, ...]:
    """Return the built-in demonstration dataset as domain aggregates."""
    return (
        Case(
            title="Acute Chest Pain - 58M",
            description=(
                "58-year-old man with sudden retrosternal chest pain radiating to the "
                "left arm and diaphoresis, onset 40 minutes ago."
            ),
            questions=(
                Question(
                    text="Which is the most likely diagnosis?",
                    position=0,
                    options=(
                        _option("Acute ST-elevation myocardial infarction", "10", 1),
                        _option("Unstable angina", "6", 2),
                        _option("Pulmonary embolism", "2", 3),
                        _option("Gastroesophageal reflux", "0", 4),
                    ),
                ),
                Question(
                    text="Which initial investigation is most appropriate?",
                    position=1,
                    options=(
                        _option("12-lead ECG within 10 minutes", "10", 1),
                        _option("Chest X-ray", "3", 2),
                        _option("D-dimer", "1", 3),
                    ),
                ),
                Question(
                    text="Which immediate therapy is indicated?",
                    position=2,
                    options=(
                        _option("Aspirin plus urgent reperfusion", "10", 1),
                        _option("Nitroglycerin only", "4", 2),
                        _option("Oral antacid", "0", 3),
                    ),
                ),
            ),
        ),
        Case(
            title="Pediatric Fever - 3Y",
            description=(
                "3-year-old child with fever 39.2 C for two days, irritability, and "
                "reduced oral intake."
            ),
            questions=(
                Question(
                    text="What is the most appropriate first step?",
                    position=0,
                    options=(
                        _option("Assess red flags and vital signs", "10", 1),
                        _option("Recommend tepid sponging only", "2", 2),
                        _option("Prescribe antibiotics immediately", "0", 3),
                    ),
                ),
                Question(
                    text="Which finding warrants urgent referral?",
                    position=1,
                    options=(
                        _option("Non-blanching petechial rash", "10", 1),
                        _option("Fever of 38.5 C", "1", 2),
                        _option("Mild nasal congestion", "0", 3),
                    ),
                ),
                Question(
                    text="Which antipyretic is first-line?",
                    position=2,
                    options=(
                        _option("Weight-based paracetamol (acetaminophen)", "10", 1),
                        _option("Acetylsalicylic acid (aspirin)", "0", 2),
                        _option("Ibuprofen for a dehydrated child", "2", 3),
                    ),
                ),
            ),
        ),
    )


async def seed_default_cases(repository: CaseRepository, existing_titles: Collection[str]) -> int:
    """Persist default cases that are not already present; return the count added."""
    known = set(existing_titles)
    created = 0
    for case in default_cases():
        if case.title in known:
            continue
        await repository.add(case)
        known.add(case.title)
        created += 1
    return created


async def _run(session: AsyncSession) -> tuple[int, int]:
    result = await session.scalars(select(CaseModel.title))
    existing_titles: set[str] = set(result.all())
    created = await seed_default_cases(SqlAlchemyCaseRepository(session), existing_titles)
    return created, len(existing_titles)


def main() -> None:
    async def _main() -> None:
        async with get_session_factory()() as session:
            created, existing = await _run(session)
        print(f"seed: created {created} case(s), skipped {existing} existing")

    asyncio.run(_main())


if __name__ == "__main__":
    main()
