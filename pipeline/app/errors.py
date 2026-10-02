"""Typed errors for the extraction pipeline boundary."""

from __future__ import annotations


class PipelineError(Exception):
    """Base class for pipeline failures."""


class LLMResponseError(PipelineError):
    """A single provider response could not be parsed or validated against the schema."""


class ExtractionError(PipelineError):
    """Extraction failed after the repair budget was exhausted (no partial result)."""
