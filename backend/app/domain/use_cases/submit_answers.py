from dataclasses import dataclass

from app.domain.entities import Answer, Submission
from app.domain.errors import NotFoundError
from app.domain.ports import CaseRepository, SubmissionRepository
from app.domain.scoring import ScoreResult, compute_score


@dataclass(slots=True)
class SubmitAnswers:
    """Validate and persist a case submission, returning its score."""

    case_repository: CaseRepository
    submission_repository: SubmissionRepository

    async def __call__(
        self, case_id: int, answers: tuple[Answer, ...]
    ) -> tuple[Submission, ScoreResult]:
        case = await self.case_repository.get(case_id)
        if case is None:
            raise NotFoundError(f"Case {case_id} not found")
        result = compute_score(case, answers)
        submission = await self.submission_repository.add(
            Submission(case_id=case_id, answers=answers)
        )
        return submission, result
