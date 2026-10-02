"""Case routes: each operation parses input, calls a use case, maps the response."""

from fastapi import APIRouter, status

from app.api.deps import CreateCaseDep, GetCaseDep, ListCasesDep
from app.api.mappers import to_domain, to_read, to_summary_read
from app.api.schemas import CaseCreate, CaseRead, CaseSummaryRead

router = APIRouter(prefix="/cases", tags=["clinical-cases"])


@router.get("")
async def list_cases(use_case: ListCasesDep) -> list[CaseSummaryRead]:
    return [to_summary_read(summary) for summary in await use_case()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case(payload: CaseCreate, use_case: CreateCaseDep) -> CaseRead:
    case = await use_case(to_domain(payload))
    return to_read(case)


@router.get("/{case_id}")
async def get_case(case_id: int, use_case: GetCaseDep) -> CaseRead:
    case = await use_case(case_id)
    return to_read(case)
