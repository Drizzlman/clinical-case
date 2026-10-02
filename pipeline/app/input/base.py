"""Raw-text input boundary (provider-agnostic, no network)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class InputSource(Protocol):
    """Reads the raw clinical text to extract a case from."""

    def read(self) -> str: ...
