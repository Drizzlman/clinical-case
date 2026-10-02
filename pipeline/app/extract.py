"""Extraction orchestration: call the LLM, validate, repair, or fail typed."""

from __future__ import annotations

from app.client.base import LLMClient
from app.errors import ExtractionError, LLMResponseError
from app.schema.case import CaseExtraction

DEFAULT_MAX_REPAIRS = 1


async def extract_case(
    client: LLMClient,
    raw_text: str,
    *,
    max_repairs: int = DEFAULT_MAX_REPAIRS,
) -> CaseExtraction:
    """Extract a schema-valid case from raw text.

    On an invalid model response the client's validation error is fed back to the
    model for one repair attempt; if the response is still invalid,
    :class:`ExtractionError` is raised rather than returning a partial result.
    """

    if not raw_text.strip():
        raise ExtractionError("Raw text must not be empty")

    repair_hint: str | None = None
    attempts = max_repairs + 1
    for attempt in range(attempts):
        try:
            return await client.extract_case(raw_text, repair_hint=repair_hint)
        except LLMResponseError as exc:
            repair_hint = str(exc)
            if attempt >= attempts - 1:
                raise ExtractionError(
                    f"Extraction failed after repairs were exhausted: {exc}"
                ) from exc

    raise ExtractionError("Extraction failed")  # pragma: no cover - loop always returns