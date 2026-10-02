"""HTTP sink: POST the case to the backend ``POST /cases`` endpoint."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx


class HttpCaseSink:
    """Deliver a case over HTTP to the backend (no direct database access).

    The optional ``client`` is injected for tests; in production a short-lived
    ``httpx.Client`` is created per call.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._client = client

    def send(self, case: Mapping[str, Any]) -> Mapping[str, Any]:
        url = f"{self._base_url}/cases"
        payload = dict(case)
        if self._client is not None:
            response = self._client.post(url, json=payload)
        else:
            with httpx.Client(timeout=self._timeout_seconds) as client:
                response = client.post(url, json=payload)
        response.raise_for_status()
        created: Any = response.json()
        return dict(created)
