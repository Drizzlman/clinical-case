"""Extraction orchestration: valid output, repair, and typed failure."""

from __future__ import annotations

import asyncio

import pytest

from app.client.mock import MockLLMClient
from app.errors import ExtractionError, LLMResponseError
from app.extract import extract_case
from app.schema.case import CaseExtraction
from tests.test_schema import sample_case

RAW_TEXT = "58-year-old man with acute chest pain radiating to the left arm."


def test_valid_response_is_returned() -> None:
    client = MockLLMClient({RAW_TEXT: sample_case()})

    result = asyncio.run(extract_case(client, RAW_TEXT))

    assert result.title == "Chest pain"


def test_invalid_response_is_repaired() -> None:
    client = MockLLMClient(
        {RAW_TEXT: [LLMResponseError("Model output failed schema validation"), sample_case()]}
    )

    result = asyncio.run(extract_case(client, RAW_TEXT, max_repairs=1))

    assert result.questions[0].options[0].text == "Myocardial infarction"


def test_unrecoverable_invalid_response_raises_extraction_error() -> None:
    client = MockLLMClient({RAW_TEXT: LLMResponseError("bad")})

    with pytest.raises(ExtractionError):
        asyncio.run(extract_case(client, RAW_TEXT, max_repairs=1))


def test_blank_raw_text_is_rejected() -> None:
    client = MockLLMClient({})

    with pytest.raises(ExtractionError):
        asyncio.run(extract_case(client, "   "))


def test_error_does_not_echo_raw_text() -> None:
    client = MockLLMClient({RAW_TEXT: LLMResponseError("provider unreachable")})

    with pytest.raises(ExtractionError) as excinfo:
        asyncio.run(extract_case(client, RAW_TEXT, max_repairs=0))

    assert RAW_TEXT not in str(excinfo.value)


def test_mock_returns_case_extraction_instance() -> None:
    client = MockLLMClient({RAW_TEXT: sample_case()})

    result = asyncio.run(client.extract_case(RAW_TEXT))

    assert isinstance(result, CaseExtraction)


def test_extraction_error_includes_last_cause() -> None:
    client = MockLLMClient({RAW_TEXT: LLMResponseError("provider unreachable")})

    with pytest.raises(ExtractionError, match="provider unreachable"):
        asyncio.run(extract_case(client, RAW_TEXT, max_repairs=0))
