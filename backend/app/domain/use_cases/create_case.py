from dataclasses import dataclass

from app.domain.entities import Case
from app.domain.ports import CaseRepository


@dataclass(slots=True)
class CreateCase:
    """Persist a new clinical case aggregate."""

    repository: CaseRepository

    async def __call__(self, case: Case) -> Case:
        return await self.repository.add(case)
