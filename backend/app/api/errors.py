"""Unified error handling: RFC 7807-style problem details for 422/404."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain.errors import DomainValidationError, NotFoundError

PROBLEM_MEDIA_TYPE = "application/problem+json"


class ProblemDetail(BaseModel):
    type: str
    title: str
    detail: str | None = None
    errors: list[dict[str, Any]] | None = None


def _problem(status_code: int, problem: ProblemDetail) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(exclude_none=True),
        media_type=PROBLEM_MEDIA_TYPE,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _problem(
            422,
            ProblemDetail(
                type="validation_error",
                title="Request validation failed",
                errors=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(DomainValidationError)
    async def _handle_domain_validation(
        _request: Request, exc: DomainValidationError
    ) -> JSONResponse:
        return _problem(
            422,
            ProblemDetail(
                type="domain_validation_error",
                title="Invalid clinical case",
                detail=exc.message,
            ),
        )

    @app.exception_handler(NotFoundError)
    async def _handle_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
        return _problem(
            404,
            ProblemDetail(type="not_found", title="Resource not found", detail=exc.message),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_request: Request, _exc: Exception) -> JSONResponse:
        return _problem(
            500,
            ProblemDetail(type="internal_error", title="Internal server error"),
        )
