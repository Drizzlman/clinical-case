"""Application entry point (composition root)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes_cases import router as cases_router
from app.api.routes_health import router as health_router
from app.api.routes_submissions import router as submissions_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Clinical Case Scoring Platform", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(cases_router)
    app.include_router(submissions_router)
    return app


app = create_app()
