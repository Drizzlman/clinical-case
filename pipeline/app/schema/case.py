"""Pydantic schema for the extracted clinical case.

The model mirrors the backend ``CaseCreate`` contract: a title, an optional
description, and at least one question with two or more scored options. It is the
single source of truth for what the LLM must return and for the JSON Schema handed
to the provider as structured output.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.errors import LLMResponseError


class ExtractedOption(BaseModel):
    """A selectable answer option with a non-negative score."""

    text: str = Field(min_length=1)
    score: float = Field(ge=0)


class ExtractedQuestion(BaseModel):
    """A question with at least two scored options."""

    text: str = Field(min_length=1)
    options: list[ExtractedOption] = Field(min_length=2)


class CaseExtraction(BaseModel):
    """The structured case the model must produce from raw clinical text."""

    title: str = Field(min_length=1)
    description: str | None = None
    questions: list[ExtractedQuestion] = Field(min_length=1)

    def to_case_create(self) -> dict[str, Any]:
        """Convert to the backend ``POST /cases`` payload, assigning positions.

        Positions are 1-based and filled in document order because the model is not
        asked to emit them; the backend accepts an explicit ``position`` field.
        """

        return {
            "title": self.title,
            "description": self.description,
            "questions": [
                {
                    "text": question.text,
                    "position": question_index,
                    "options": [
                        {
                            "text": option.text,
                            "score": float(option.score),
                            "position": option_index,
                        }
                        for option_index, option in enumerate(question.options, start=1)
                    ],
                }
                for question_index, question in enumerate(self.questions, start=1)
            ],
        }


def case_extraction_schema() -> dict[str, Any]:
    """Return the JSON Schema for :class:`CaseExtraction` (structured output)."""

    return CaseExtraction.model_json_schema()


def parse_case_extraction(text: str | None) -> CaseExtraction:
    """Validate raw model text into a :class:`CaseExtraction`.

    Raises :class:`LLMResponseError` with a message that never echoes the model
    output (it may contain untrusted content) — only the number of validation
    errors is reported.
    """

    if not text or not text.strip():
        raise LLMResponseError("Model returned an empty response")
    try:
        return CaseExtraction.model_validate_json(text)
    except ValidationError as exc:
        raise LLMResponseError(
            f"Model output failed schema validation: {exc.error_count()} error(s)"
        ) from exc
