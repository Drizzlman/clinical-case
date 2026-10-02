"""A sink that discards the case (dry runs / local mode)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class NullCaseSink:
    """Do nothing with the case and report an empty result."""

    def send(self, case: Mapping[str, Any]) -> Mapping[str, Any]:
        return {}
