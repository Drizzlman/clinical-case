"""Public API contract (Pydantic v2). Invariant INV-2 lives here."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnswerOptionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    score: Decimal = Field(ge=0)
    position: int | None = None


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    kind: str = "single_choice"
    position: int | None = None
    options: list[AnswerOptionCreate] = Field(min_length=2, max_length=50)


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=5000)
    questions: list[QuestionCreate] = Field(min_length=1, max_length=100)


class AnswerOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    score: Decimal
    position: int


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    kind: str
    position: int
    options: list[AnswerOptionRead]


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    questions: list[QuestionRead]


class CaseSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    question_count: int


class AnswerCreate(BaseModel):
    question_id: int
    option_id: int


class SubmissionCreate(BaseModel):
    answers: list[AnswerCreate] = Field(min_length=1, max_length=100)

    @field_validator("answers")
    @classmethod
    def _unique_questions(cls, answers: list[AnswerCreate]) -> list[AnswerCreate]:
        question_ids = [answer.question_id for answer in answers]
        if len(set(question_ids)) != len(question_ids):
            raise ValueError("Each question must be answered at most once")
        return answers


class QuestionScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    selected_option_id: int
    score: Decimal
    max_score: Decimal


class SubmissionResult(BaseModel):
    id: int
    case_id: int
    earned: Decimal
    maximum: Decimal
    percentage: Decimal
    per_question: list[QuestionScoreRead]
