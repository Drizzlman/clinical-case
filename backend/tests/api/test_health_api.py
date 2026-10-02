"""Health/readiness tests (probe is replaced by a fake — no database)."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_health_probe
from app.main import create_app


class FakeHealthProbe:
    def __init__(self, ok: bool) -> None:
        self.ok = ok

    async def check(self) -> bool:
        return self.ok


@pytest.fixture
def probe() -> FakeHealthProbe:
    return FakeHealthProbe(ok=True)


@pytest.fixture
def app(probe: FakeHealthProbe) -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_health_probe] = lambda: probe
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def test_health_is_always_ok(client: AsyncClient, probe: FakeHealthProbe) -> None:
    probe.ok = False
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_when_database_reachable(client: AsyncClient, probe: FakeHealthProbe) -> None:
    probe.ok = True
    response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_ready_returns_503_when_database_down(
    client: AsyncClient, probe: FakeHealthProbe
) -> None:
    probe.ok = False
    response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
