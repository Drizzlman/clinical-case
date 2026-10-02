"""Input-source dispatch: ``-`` means stdin, anything else is a file path."""

from __future__ import annotations

from pathlib import Path

from app.input.base import InputSource
from app.input.files import FileInputSource, StdinInputSource

__all__ = ["FileInputSource", "InputSource", "StdinInputSource", "build_input_source"]


def build_input_source(reference: str) -> InputSource:
    """Return an input source for a CLI ``--input`` reference."""

    if reference == "-":
        return StdinInputSource()
    return FileInputSource(Path(reference))
