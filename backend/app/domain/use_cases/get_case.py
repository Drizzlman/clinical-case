from dataclasses import dataclass

from app.domain.entities import Case
from app.domain.errors import NotFoundError
from app.domain.ports import CaseRepository


@dataclass(slots=True)
class GetCase:
    """Load a clinical case aggregate or raise ``NotFoundError``."""

    repository: CaseRepository

    async def __call__(self, case_id: int) -> Case:
        case = await self.repository.get(case_id)
        if case is None:
            raise NotFoundError(f"Case {case_id} not found")
        return case
