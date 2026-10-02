from dataclasses import dataclass

from app.domain.entities import CaseSummary
from app.domain.ports import CaseRepository


@dataclass(slots=True)
class ListCases:
    """Return lightweight summaries of every clinical case for listings."""

    repository: CaseRepository

    async def __call__(self) -> tuple[CaseSummary, ...]:
        return await self.repository.list_summaries()
