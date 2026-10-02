"""Vertex AI / Gemini adapter (the only place provider SDKs are imported, INV-6)."""

from __future__ import annotations

import asyncio
from typing import Any

from app.config import Settings
from app.errors import LLMResponseError
from app.schema.case import CaseExtraction, parse_case_extraction

_SYSTEM_INSTRUCTION = (
    "You extract a structured clinical multiple-choice case from raw text. "
    "Return only JSON that conforms to the provided schema: a title, an optional "
    "description, and one or more questions, each with at least two answer options "
    "and a non-negative numeric score per option."
)
_MAX_BACKOFF_SECONDS = 8.0


class VertexLLMClient:
    """LLMClient backed by Google Gen AI.

    Two transports are supported, selected by configuration:

    * **Vertex AI** (default) -- ``vertexai=True`` with project/location; auth via
      Application Default Credentials. This is the production path.
    * **Gemini Developer API** -- when ``GEMINI_API_KEY`` is set, the client uses
      API-key auth instead, so no ADC/project/billing is needed (local prototyping).

    The SDK is imported lazily so importing this module never touches GCP; errors are
    re-wrapped without echoing provider payloads, so credentials never reach logs.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        timeout_seconds: float = 30.0,
        max_transport_retries: int = 2,
        backoff_seconds: float = 1.0,
        genai_client: Any | None = None,
    ) -> None:
        self._settings = settings
        self._timeout_seconds = timeout_seconds
        self._max_transport_retries = max_transport_retries
        self._backoff_seconds = backoff_seconds
        # SDK client is injected in tests; otherwise created lazily below.
        self._client: Any | None = genai_client

    async def extract_case(
        self, raw_text: str, *, repair_hint: str | None = None
    ) -> CaseExtraction:
        client = self._client_instance()
        config = self._generation_config()
        prompt = self._build_prompt(raw_text, repair_hint)

        attempt = 0
        while True:
            try:
                response = await client.aio.models.generate_content(
                    model=self._settings.llm_model,
                    contents=prompt,
                    config=config,
                )
            except Exception as exc:  # noqa: BLE001 - provider-specific error surface
                if attempt >= self._max_transport_retries:
                    raise LLMResponseError(
                        "LLM provider call failed after retries"
                    ) from exc
                delay = min(
                    self._backoff_seconds * (2**attempt), _MAX_BACKOFF_SECONDS
                )
                await asyncio.sleep(delay)
                attempt += 1
                continue
            return parse_case_extraction(response.text)

    def _client_instance(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depends on install extra
            raise LLMResponseError(
                "google-genai is not installed; install the pipeline dependencies"
            ) from exc
        http_options = types.HttpOptions(timeout=int(self._timeout_seconds * 1000))
        api_key = self._settings.gemini_api_key
        if api_key:
            # Developer API transport: API-key auth, no ADC/project required.
            self._client = genai.Client(api_key=api_key, http_options=http_options)
        else:
            self._client = genai.Client(
                vertexai=True,
                project=self._settings.gcp_project or None,
                location=self._settings.gcp_location or None,
                http_options=http_options,
            )
        return self._client

    def _generation_config(self) -> Any:
        from google.genai import types

        return types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CaseExtraction,
            temperature=0.0,
            # No tools are declared, so AFC only emits a spurious warning; disable it.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

    def _build_prompt(self, raw_text: str, repair_hint: str | None) -> str:
        parts = [_SYSTEM_INSTRUCTION, "", "Raw clinical text:", raw_text.strip()]
        if repair_hint:
            parts.extend(
                [
                    "",
                    f"The previous attempt was invalid: {repair_hint}.",
                    "Return a corrected JSON document that satisfies the schema.",
                ]
            )
        return "\n".join(parts)