"""Submission API tests through httpx ASGI transport with in-memory adapters (no DB)."""

import asyncio
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
    cases = InMemoryCaseRepository()
    submissions = InMemorySubmissionRepository()
    application.dependency_overrides[get_case_repository] = lambda: cases
    application.dependency_overrides[get_submission_repository] = lambda: submissions
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def case_payload() -> dict[str, Any]:
    return {
        "title": "Myocardial infarction",
        "questions": [
            {
                "text": "Diagnosis?",
                "options": [{"text": "MI", "score": 2}, {"text": "Angina", "score": 0}],
            },
            {
                "text": "ECG?",
                "options": [{"text": "STEMI", "score": 1}, {"text": "Normal", "score": 0}],
            },
        ],
    }


async def create_case(client: AsyncClient) -> dict[str, Any]:
    response = await client.post("/cases", json=case_payload())
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


async def test_submit_full_score_and_read_back(client: AsyncClient) -> None:
    case = await create_case(client)
    questions = case["questions"]
    answers = [
        {"question_id": questions[0]["id"], "option_id": questions[0]["options"][0]["id"]},
        {"question_id": questions[1]["id"], "option_id": questions[1]["options"][0]["id"]},
    ]

    response = await client.post(f"/cases/{case['id']}/submissions", json={"answers": answers})

    assert response.status_code == 201
    result = response.json()
    assert result["earned"] == "3"
    assert result["maximum"] == "3"
    assert result["percentage"] == "100.00"

    fetched = await client.get(f"/submissions/{result['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["percentage"] == "100.00"


async def test_submission_missing_question_returns_422(client: AsyncClient) -> None:
    case = await create_case(client)
    question = case["questions"][0]

    response = await client.post(
        f"/cases/{case['id']}/submissions",
        json={
            "answers": [
                {"question_id": question["id"], "option_id": question["options"][0]["id"]}
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["type"] == "domain_validation_error"


async def test_submission_option_from_other_question_returns_422(client: AsyncClient) -> None:
    case = await create_case(client)
    first, second = case["questions"]

    response = await client.post(
        f"/cases/{case['id']}/submissions",
        json={
            "answers": [
                {"question_id": first["id"], "option_id": second["options"][0]["id"]},
                {"question_id": second["id"], "option_id": second["options"][0]["id"]},
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["type"] == "domain_validation_error"


async def test_submission_for_unknown_case_returns_404(client: AsyncClient) -> None:
    response = await client.post(
        "/cases/999/submissions",
        json={"answers": [{"question_id": 1, "option_id": 1}]},
    )

    assert response.status_code == 404
    assert response.json()["type"] == "not_found"


async def test_get_unknown_submission_returns_404(client: AsyncClient) -> None:
    response = await client.get("/submissions/123")

    assert response.status_code == 404
    assert response.json()["type"] == "not_found"


async def test_concurrent_submissions_all_succeed(client: AsyncClient) -> None:
    case = await create_case(client)
    questions = case["questions"]
    answers = [
        {"question_id": questions[0]["id"], "option_id": questions[0]["options"][0]["id"]},
        {"question_id": questions[1]["id"], "option_id": questions[1]["options"][0]["id"]},
    ]

    responses = await asyncio.gather(
        *(
            client.post(f"/cases/{case['id']}/submissions", json={"answers": answers})
            for _ in range(20)
        )
    )

    assert all(response.status_code == 201 for response in responses)
