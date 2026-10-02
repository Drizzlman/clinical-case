"""Select the LLM adapter from configuration (no provider SDK at import time)."""

from __future__ import annotations

from pathlib import Path

from app.client.base import LLMClient
from app.client.mock import MockLLMClient
from app.client.vertex import VertexLLMClient
from app.config import Settings

__all__ = ["build_llm_client"]


def build_llm_client(settings: Settings, *, name: str, golden_dir: Path) -> LLMClient:
    """Return the configured LLM client.

    ``mock`` reads deterministic fixtures from ``golden_dir`` (offline);
    ``vertex`` builds the real Vertex/Gemini adapter (ADC, no keys in code).
    """

    if name == "mock":
        return MockLLMClient.from_fixtures(golden_dir)
    if name == "vertex":
        return VertexLLMClient(settings)
    raise ValueError(f"Unknown LLM client {name!r}; expected 'mock' or 'vertex'")
