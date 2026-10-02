"""Input sources: file, stdin, and dispatch."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.input import FileInputSource, StdinInputSource, build_input_source


def test_file_source_reads_text(tmp_path: Path) -> None:
    path = tmp_path / "raw.txt"
    path.write_text("chest pain", encoding="utf-8")

    assert build_input_source(str(path)).read() == "chest pain"


def test_build_input_source_dispatches_stdin() -> None:
    assert isinstance(build_input_source("-"), StdinInputSource)


def test_build_input_source_dispatches_file(tmp_path: Path) -> None:
    assert isinstance(build_input_source(str(tmp_path / "x.txt")), FileInputSource)


def test_stdin_source_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("vignette"))

    assert StdinInputSource().read() == "vignette"
