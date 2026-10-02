"""Case delivery adapters."""

from __future__ import annotations

from app.sink.base import CaseSink
from app.sink.http import HttpCaseSink
from app.sink.null import NullCaseSink

__all__ = ["CaseSink", "HttpCaseSink", "NullCaseSink"]
