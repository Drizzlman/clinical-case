"""Concrete input sources: a local file or standard input."""

from __future__ import annotations

import sys
from pathlib import Path


class FileInputSource:
    """Read raw text from a local file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> str:
        return self._path.read_text(encoding="utf-8")


class StdinInputSource:
    """Read raw text from standard input (``-``)."""

    def read(self) -> str:
        return sys.stdin.read()
