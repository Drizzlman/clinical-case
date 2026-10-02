"""Translate between the HTTP contract (Pydantic) and domain entities.

Kept thin: parsing/formatting only, no business rules (those live in the domain).
"""

from app.api.schemas import (
    AnswerOptionRead,
    CaseCreate,
    CaseRead,
    CaseSummaryRead,
    QuestionRead,
    QuestionScoreRead,
    SubmissionCreate,
    SubmissionResult,
)
from app.domain.entities import (
    Answer,
    AnswerOption,
    Case,
    CaseSummary,
    Question,
    Submission,
)
from app.domain.scoring import ScoreResult


def to_domain(payload: CaseCreate) -> Case:
    """Build a domain aggregate from a create payload, defaulting positions to list order."""
    questions = tuple(
        Question(
            text=question.text,
            kind=question.kind,
            position=question.position if question.position is not None else q_index,
            options=tuple(
                AnswerOption(
                    text=option.text,
                    score=option.score,
                    position=option.position if option.position is not None else o_index,
                )
                for o_index, option in enumerate(question.options)
            ),
        )
        for q_index, question in enumerate(payload.questions)
    )
    return Case(title=payload.title, description=payload.description, questions=questions)


def to_read(case: Case) -> CaseRead:
    """Serialize a domain aggregate to the public read schema."""
    return CaseRead.model_validate(case)


def to_summary_read(summary: CaseSummary) -> CaseSummaryRead:
    """Serialize a case listing projection to the public read schema."""
    return CaseSummaryRead.model_validate(summary)


def answers_to_domain(payload: SubmissionCreate) -> tuple[Answer, ...]:
    """Build domain answers from a submission payload."""
    return tuple(
        Answer(question_id=answer.question_id, option_id=answer.option_id)
        for answer in payload.answers
    )


def to_submission_read(submission: Submission, result: ScoreResult) -> SubmissionResult:
    """Serialize a submission and its computed score."""
    if submission.id is None:
        raise ValueError("Submission id must be assigned before serialization")
    return SubmissionResult(
        id=submission.id,
        case_id=submission.case_id,
        earned=result.earned,
        maximum=result.maximum,
        percentage=result.percentage,
        per_question=[QuestionScoreRead.model_validate(item) for item in result.per_question],
    )


__all__ = [
    "AnswerOptionRead",
    "QuestionRead",
    "answers_to_domain",
    "to_domain",
    "to_read",
    "to_submission_read",
    "to_summary_read",
]
