"""Vertex adapter behaviour, exercised offline with an injected fake SDK client."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from app.client.vertex import VertexLLMClient
from app.config import Settings
from app.errors import LLMResponseError

RAW = "58-year-old man with chest pain radiating to the left arm."


def _settings(**overrides: Any) -> Settings:
    defaults: dict[str, Any] = {
        "gcp_project": "test-project",
        "gcp_location": "europe-west1",
        "llm_model": "gemini-3.8-flash",
        "llm_client": "vertex",
        "backend_url": "http://localhost:8000",
        "_env_file": None,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _valid_json() -> str:
    return json.dumps(
        {
            "title": "Chest pain",
            "questions": [
                {
                    "text": "Most likely diagnosis?",
                    "options": [
                        {"text": "Myocardial infarction", "score": 1},
                        {"text": "Angina", "score": 0},
                    ],
                }
            ],
        }
    )


class _Response:
    def __init__(self, text: str | None) -> None:
        self.text = text


class _Models:
    def __init__(self, script: list[Any]) -> None:
        self._script = script

    async def generate_content(self, **kwargs: Any) -> _Response:
        item = self._script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return _Response(item)


class _Aio:
    def __init__(self, script: list[Any]) -> None:
        self.models = _Models(script)


class FakeGenaiClient:
    def __init__(self, script: list[Any]) -> None:
        self.aio = _Aio(script)


def _client(script: list[Any], *, retries: int = 0) -> VertexLLMClient:
    return VertexLLMClient(
        _settings(),
        genai_client=FakeGenaiClient(script),
        max_transport_retries=retries,
        backoff_seconds=0.0,
    )


def test_valid_response_is_parsed() -> None:
    result = asyncio.run(_client([_valid_json()]).extract_case(RAW))

    assert result.title == "Chest pain"
    assert result.questions[0].options[0].text == "Myocardial infarction"


def test_transient_error_is_retried() -> None:
    client = _client([RuntimeError("boom"), _valid_json()], retries=1)

    result = asyncio.run(client.extract_case(RAW))

    assert result.questions[0].options[0].text == "Myocardial infarction"


def test_transport_error_after_retries_is_typed() -> None:
    client = _client([RuntimeError("a"), RuntimeError("b")], retries=1)

    with pytest.raises(LLMResponseError, match="failed after retries"):
        asyncio.run(client.extract_case(RAW))


def test_invalid_output_raises_without_echoing_input() -> None:
    with pytest.raises(LLMResponseError) as excinfo:
        asyncio.run(_client(["not json"]).extract_case(RAW))

    assert RAW not in str(excinfo.value)


def test_api_key_selects_developer_api_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    import google.genai

    captured: dict[str, Any] = {}

    class _CapturingClient:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(google.genai, "Client", _CapturingClient)
    client = VertexLLMClient(
        _settings(gemini_api_key="key-123"), backoff_seconds=0.0
    )
    client._client_instance()

    assert captured["api_key"] == "key-123"
    assert "vertexai" not in captured


def test_missing_api_key_selects_vertex_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    import google.genai

    captured: dict[str, Any] = {}

    class _CapturingClient:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(google.genai, "Client", _CapturingClient)
    client = VertexLLMClient(_settings(), backoff_seconds=0.0)
    client._client_instance()

    assert captured["vertexai"] is True
    assert captured["project"] == "test-project"
    assert "api_key" not in captured