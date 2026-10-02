"""Provider-agnostic LLM boundary (INV-6)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.errors import ExtractionError, LLMResponseError, PipelineError
from app.schema.case import CaseExtraction

__all__ = [
    "ExtractionError",
    "LLMClient",
    "LLMResponseError",
    "PipelineError",
]


@runtime_checkable
class LLMClient(Protocol):
    """The only way callers reach an LLM (INV-6).

    Implementations return a schema-valid :class:`CaseExtraction` or raise
    :class:`LLMResponseError` when a single response cannot be parsed/validated. On
    a retry the caller passes ``repair_hint`` describing what was wrong, so the
    adapter can ask the model to fix it.
    """

    async def extract_case(
        self, raw_text: str, *, repair_hint: str | None = None
    ) -> CaseExtraction: ...
