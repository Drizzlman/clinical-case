from dataclasses import dataclass

from app.domain.entities import Submission
from app.domain.errors import NotFoundError
from app.domain.ports import CaseRepository, SubmissionRepository
from app.domain.scoring import ScoreResult, compute_score


@dataclass(slots=True)
class GetSubmission:
    """Load a submission and recompute its score."""

    case_repository: CaseRepository
    submission_repository: SubmissionRepository

    async def __call__(self, submission_id: int) -> tuple[Submission, ScoreResult]:
        submission = await self.submission_repository.get(submission_id)
        if submission is None:
            raise NotFoundError(f"Submission {submission_id} not found")
        case = await self.case_repository.get(submission.case_id)
        if case is None:
            raise NotFoundError(f"Case {submission.case_id} not found")
        return submission, compute_score(case, submission.answers)
