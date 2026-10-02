"""Case sinks: null (dry run) and HTTP (backend POST /cases)."""

from __future__ import annotations

import httpx
import pytest

from app.sink import HttpCaseSink, NullCaseSink


def test_null_sink_discards_case() -> None:
    assert NullCaseSink().send({"title": "x"}) == {}


def test_http_sink_posts_backend_payload_to_cases() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.read().decode("utf-8")
        return httpx.Response(201, json={"id": 7, "title": "x"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    sink = HttpCaseSink("http://backend:8000/", client=client)

    created = sink.send({"title": "x", "questions": []})

    assert created["id"] == 7
    assert seen["url"] == "http://backend:8000/cases"
    assert '"title"' in seen["body"]


def test_http_sink_raises_on_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"type": "validation_error"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    sink = HttpCaseSink("http://backend:8000", client=client)

    with pytest.raises(httpx.HTTPStatusError):
        sink.send({"title": "x"})
