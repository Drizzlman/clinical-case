"""API tests through httpx ASGI transport with an in-memory repository (no DB)."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_case_repository
from app.main import create_app
from tests.fakes import InMemoryCaseRepository


@pytest.fixture
def app() -> FastAPI:
    application = create_app()
    repository = InMemoryCaseRepository()
    application.dependency_overrides[get_case_repository] = lambda: repository
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def valid_payload() -> dict[str, Any]:
    return {
        "title": "Myocardial infarction",
        "description": "58-year-old with chest pain",
        "questions": [
            {
                "text": "Most likely diagnosis?",
                "options": [
                    {"text": "MI", "score": 1},
                    {"text": "Angina", "score": 0},
                ],
            }
        ],
    }


async def test_create_case_returns_201_with_identifiers(client: AsyncClient) -> None:
    response = await client.post("/cases", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Myocardial infarction"
    assert body["questions"][0]["id"] == 1
    assert body["questions"][0]["options"][0]["text"] == "MI"


async def test_get_case_returns_stored_case(client: AsyncClient) -> None:
    created = await client.post("/cases", json=valid_payload())
    case_id = created.json()["id"]

    response = await client.get(f"/cases/{case_id}")

    assert response.status_code == 200
    assert response.json()["questions"][0]["options"][1]["text"] == "Angina"


async def test_invalid_payload_returns_422_problem(client: AsyncClient) -> None:
    response = await client.post(
        "/cases", json={"title": "", "questions": []}
    )

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["type"] == "validation_error"


async def test_domain_invariant_violation_returns_422(client: AsyncClient) -> None:
    payload = valid_payload()
    payload["questions"].append(payload["questions"][0] | {"position": 0})
    payload["questions"][0]["position"] = 0

    response = await client.post("/cases", json=payload)

    assert response.status_code == 422
    assert response.json()["type"] == "domain_validation_error"


async def test_get_missing_case_returns_404_problem(client: AsyncClient) -> None:
    response = await client.get("/cases/123")

    assert response.status_code == 404
    assert response.json()["type"] == "not_found"


async def test_list_cases_empty_returns_empty_collection(client: AsyncClient) -> None:
    response = await client.get("/cases")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_cases_returns_summaries(client: AsyncClient) -> None:
    created = await client.post("/cases", json=valid_payload())
    case_id = created.json()["id"]

    response = await client.get("/cases")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": case_id,
            "title": "Myocardial infarction",
            "description": "58-year-old with chest pain",
            "question_count": 1,
        }
    ]
