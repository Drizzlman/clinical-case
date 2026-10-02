"""CORS least-privilege: only configured origins, scoped methods/headers (no DB required)."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def test_preflight_allows_configured_origin_with_scoped_headers(
    client: AsyncClient,
) -> None:
    response = await client.options(
        "/cases",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    allowed_methods = {
        method.strip()
        for method in response.headers["access-control-allow-methods"].split(",")
    }
    assert allowed_methods == {"GET", "POST"}

    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "content-type" in allowed_headers


async def test_preflight_rejects_unknown_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/cases",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers