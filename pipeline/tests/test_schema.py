"""Schema contract: backend payload mapping and JSON Schema for structured output."""

from __future__ import annotations

import pytest

from app.errors import LLMResponseError
from app.schema.case import CaseExtraction, case_extraction_schema, parse_case_extraction


def sample_case() -> CaseExtraction:
    return CaseExtraction.model_validate(
        {
            "title": "Chest pain",
            "description": "58-year-old with chest pain",
            "questions": [
                {
                    "text": "Most likely diagnosis?",
                    "options": [
                        {"text": "Myocardial infarction", "score": 1},
                        {"text": "Angina", "score": 0},
                    ],
                },
                {
                    "text": "Next best step?",
                    "options": [
                        {"text": "ECG", "score": 1},
                        {"text": "CT", "score": 0},
                    ],
                },
            ],
        }
    )


def test_to_case_create_assigns_one_based_positions() -> None:
    payload = sample_case().to_case_create()

    assert payload["title"] == "Chest pain"
    assert [question["position"] for question in payload["questions"]] == [1, 2]
    assert [option["position"] for option in payload["questions"][0]["options"]] == [1, 2]
    assert payload["questions"][0]["options"][0]["score"] == 1.0


def test_json_schema_requires_title_and_questions() -> None:
    schema = case_extraction_schema()

    assert "title" in schema["required"]
    assert "questions" in schema["required"]
    assert "description" not in schema["required"]


def test_parse_rejects_empty_text() -> None:
    with pytest.raises(LLMResponseError):
        parse_case_extraction("   ")


def test_parse_error_does_not_echo_payload() -> None:
    secret_payload = '{"title": "leak", "questions": "not-a-list"}'

    with pytest.raises(LLMResponseError) as excinfo:
        parse_case_extraction(secret_payload)

    assert "leak" not in str(excinfo.value)


def test_min_two_options_enforced() -> None:
    with pytest.raises(LLMResponseError):
        parse_case_extraction(
            '{"title": "x", "questions": [{"text": "q", "options": [{"text": "a", "score": 0}]}]}'
        )
