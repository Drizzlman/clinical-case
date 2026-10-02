"""Unified error body (RFC 7807) across endpoints and status codes."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_case_repository, get_submission_repository
from app.main import create_app
from tests.fakes import InMemoryCaseRepository, InMemorySubmissionRepository


@pytest.fixture
def app() -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_case_repository] = InMemoryCaseRepository
    application.dependency_overrides[get_submission_repository] = InMemorySubmissionRepository
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def assert_problem(response: Any, expected_type: str) -> None:
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == expected_type
    assert "title" in body


async def test_not_found_problem(client: AsyncClient) -> None:
    assert_problem(await client.get("/cases/999"), "not_found")
    assert_problem(await client.get("/submissions/999"), "not_found")


async def test_validation_problem(client: AsyncClient) -> None:
    response = await client.post("/cases", json={"title": "", "questions": []})
    assert response.status_code == 422
    assert_problem(response, "validation_error")


async def test_domain_problem(client: AsyncClient) -> None:
    response = await client.post(
        "/cases/999/submissions", json={"answers": [{"question_id": 1, "option_id": 1}]}
    )
    assert response.status_code == 404
    assert_problem(response, "not_found")
