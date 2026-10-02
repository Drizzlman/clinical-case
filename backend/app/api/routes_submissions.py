"""Submission routes: each operation parses input, calls a use case, maps the response."""

from fastapi import APIRouter, status

from app.api.deps import GetSubmissionDep, SubmitAnswersDep
from app.api.mappers import answers_to_domain, to_submission_read
from app.api.schemas import SubmissionCreate, SubmissionResult

router = APIRouter(tags=["case-scoring"])


@router.post("/cases/{case_id}/submissions", status_code=status.HTTP_201_CREATED)
async def submit_answers(
    case_id: int, payload: SubmissionCreate, use_case: SubmitAnswersDep
) -> SubmissionResult:
    submission, result = await use_case(case_id, answers_to_domain(payload))
    return to_submission_read(submission, result)


@router.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: int, use_case: GetSubmissionDep
) -> SubmissionResult:
    submission, result = await use_case(submission_id)
    return to_submission_read(submission, result)
