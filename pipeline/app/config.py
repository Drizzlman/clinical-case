"""Pipeline settings loaded from the environment (no secrets in code, INV-3)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Runtime configuration for the extraction pipeline.

    Credentials are never read here: the Vertex adapter relies on Application
    Default Credentials (ADC). Only non-secret configuration is modelled, except
    for the optional Developer API key used for local prototyping.
    """

    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_prefix="", extra="ignore")

    gcp_project: str
    gcp_location: str
    llm_model: str

    # Which LLM adapter to use: ``mock`` (offline) or ``vertex`` (production).
    llm_client: str
    # Backend base URL, used by the HTTP case sink (``POST /cases``).
    backend_url: str

    # Optional Gemini Developer API key. When set, the ``vertex`` adapter talks to
    # the Developer API (``generativelanguage.googleapis.com``) instead of Vertex AI,
    # so no ADC/project/billing is required (local prototyping only).
    gemini_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings parsed from the environment."""

    return Settings()