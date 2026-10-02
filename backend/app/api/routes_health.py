"""Liveness and readiness endpoints (no business logic)."""

from fastapi import APIRouter, Response, status

from app.api.deps import HealthProbeDep

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: the process is up, independent of dependencies."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(probe: HealthProbeDep, response: Response) -> dict[str, str]:
    """Readiness: 200 when the datastore is reachable, 503 otherwise."""
    if await probe.check():
        return {"status": "ready"}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "unavailable"}
