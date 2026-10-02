"""Deterministic in-memory LLM client used by tests and the accuracy harness."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.errors import LLMResponseError
from app.schema.case import CaseExtraction

type MockResponse = CaseExtraction | BaseException


class MockLLMClient:
    """Returns scripted responses keyed by raw text, with no network access.

    A single response is returned for every call; a sequence is consumed one item
    per call. An :class:`BaseException` entry is raised, which lets tests exercise
    the repair loop deterministically.
    """

    def __init__(
        self, responses: Mapping[str, MockResponse | Sequence[MockResponse]]
    ) -> None:
        self._responses: dict[str, list[MockResponse]] = {}
        for raw_text, value in responses.items():
            if isinstance(value, Sequence):
                self._responses[raw_text] = list(value)
            else:
                self._responses[raw_text] = [value]

    async def extract_case(
        self, raw_text: str, *, repair_hint: str | None = None
    ) -> CaseExtraction:
        queue = self._responses.get(raw_text)
        if not queue:
            raise LLMResponseError("No scripted response for the provided text")
        entry = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(entry, BaseException):
            raise entry
        return entry

    @classmethod
    def from_fixtures(cls, directory: Path) -> MockLLMClient:
        """Build a client that echoes the expected case from each golden fixture."""

        responses: dict[str, CaseExtraction] = {}
        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            responses[str(payload["raw_text"])] = CaseExtraction.model_validate(
                payload["expected"]
            )
        return cls(responses)
