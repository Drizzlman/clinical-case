"""Case delivery boundary: send an extracted case to a destination."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CaseSink(Protocol):
    """Delivers a backend-ready case payload and returns the created resource."""

    def send(self, case: Mapping[str, Any]) -> Mapping[str, Any]: ...
