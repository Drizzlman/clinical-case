"""CLI: extraction run wiring, delivery, and harness delegation (all offline)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.cli import main, run_extract
from app.client.mock import MockLLMClient
from app.config import Settings
from app.errors import ExtractionError

RAW_TEXT = "58-year-old man with acute chest pain."


def _write_fixture(directory: Path, raw_text: str) -> None:
    payload = {
        "raw_text": raw_text,
        "expected": {
            "title": "Chest pain",
            "questions": [
                {
                    "text": "Most likely diagnosis?",
                    "options": [
                        {"text": "Myocardial infarction", "score": 1},
                        {"text": "Angina", "score": 0},
                    ],
                }
            ],
        },
    }
    (directory / "case.json").write_text(json.dumps(payload), encoding="utf-8")


class RecordingSink:
    def __init__(self) -> None:
        self.sent: list[Mapping[str, Any]] = []

    def send(self, case: Mapping[str, Any]) -> Mapping[str, Any]:
        self.sent.append(case)
        return {"id": 1, **dict(case)}


def test_run_extract_returns_backend_payload_without_posting(tmp_path: Path) -> None:
    _write_fixture(tmp_path, RAW_TEXT)
    sink = RecordingSink()

    payload = run_extract(
        raw_text=RAW_TEXT,
        client=MockLLMClient.from_fixtures(tmp_path),
        sink=sink,
        post=False,
    )

    assert payload["title"] == "Chest pain"
    assert payload["questions"][0]["position"] == 1
    assert sink.sent == []


def test_run_extract_posts_when_enabled(tmp_path: Path) -> None:
    _write_fixture(tmp_path, RAW_TEXT)
    sink = RecordingSink()

    run_extract(
        raw_text=RAW_TEXT,
        client=MockLLMClient.from_fixtures(tmp_path),
        sink=sink,
        post=True,
    )

    assert len(sink.sent) == 1
    assert sink.sent[0]["questions"][0]["options"][0]["position"] == 1


def test_run_extract_raises_typed_error_for_unknown_text() -> None:
    with pytest.raises(ExtractionError):
        run_extract(raw_text="unknown", client=MockLLMClient({}), sink=RecordingSink(), post=False)


def test_settings_require_runtime_config() -> None:
    with pytest.raises(ValidationError):
        Settings(gcp_project="", gcp_location="europe-west1", llm_model="m", _env_file=None)


def test_harness_subcommand_delegates(tmp_path: Path) -> None:
    golden = Path(__file__).resolve().parent / "golden"
    out = tmp_path / "report.json"

    code = main(["harness", "--golden", str(golden), "--out", str(out)])

    assert code == 0
    assert out.exists()


def test_main_extract_prints_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_fixture(tmp_path, RAW_TEXT)
    raw = tmp_path / "raw.txt"
    raw.write_text(RAW_TEXT, encoding="utf-8")
    settings = Settings(
        gcp_project="",
        gcp_location="europe-west1",
        llm_model="gemini-3.8-flash",
        llm_client="mock",
        backend_url="http://localhost:8000",
        _env_file=None,
    )
    monkeypatch.setattr("app.cli.get_settings", lambda: settings)

    code = main(["extract", "--input", str(raw), "--golden", str(tmp_path)])

    assert code == 0
    assert json.loads(capsys.readouterr().out)["title"] == "Chest pain"
