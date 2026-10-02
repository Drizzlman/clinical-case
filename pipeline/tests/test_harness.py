"""Harness behavior: golden loading, perfect identity, deterministic distortion."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.client.mock import MockLLMClient
from app.harness.metrics import aggregate, measure
from app.harness.normalize import normalize_text
from app.harness.runner import load_golden, main, render_table, run_harness
from app.schema.case import CaseExtraction

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def make_case(
    title: str, questions: dict[str, list[tuple[str, float]]]
) -> CaseExtraction:
    return CaseExtraction.model_validate(
        {
            "title": title,
            "questions": [
                {
                    "text": question,
                    "options": [
                        {"text": text, "score": score} for text, score in options
                    ],
                }
                for question, options in questions.items()
            ],
        }
    )


def test_normalization_folds_case_punctuation_whitespace() -> None:
    assert normalize_text("Most likely diagnosis?") == normalize_text(
        "  most   likely  diagnosis "
    )


def test_golden_fixtures_load() -> None:
    cases = load_golden(GOLDEN_DIR)

    assert len(cases) >= 5
    assert all(case.expected.questions for case in cases)


def test_identity_run_is_perfect_and_offline() -> None:
    client = MockLLMClient.from_fixtures(GOLDEN_DIR)

    report = asyncio.run(run_harness(client, GOLDEN_DIR))

    assert report.aggregate.questions.precision == 1.0
    assert report.aggregate.questions.recall == 1.0
    assert report.aggregate.questions.f1 == 1.0
    assert report.aggregate.options.f1 == 1.0
    assert report.aggregate.score_accuracy == 1.0
    assert len(report.cases) == len(load_golden(GOLDEN_DIR))


def test_distorted_output_yields_deterministic_metrics() -> None:
    expected = make_case(
        "Expected",
        {
            "A?": [("a1", 1), ("a2", 0)],
            "B?": [("b1", 1), ("b2", 0)],
        },
    )
    extracted = make_case(
        "Extracted",
        {
            "A?": [("a1", 1), ("a2", 5)],
            "C?": [("c1", 1), ("c2", 0)],
        },
    )

    measurement = measure(extracted, expected)

    assert measurement.metrics.questions.precision == 0.5
    assert measurement.metrics.questions.recall == 0.5
    assert measurement.metrics.questions.f1 == 0.5
    assert measurement.metrics.options.f1 == 0.5
    assert measurement.metrics.score_accuracy == 0.5


def test_aggregate_is_micro_average() -> None:
    expected = make_case("E", {"A?": [("a1", 1), ("a2", 0)]})
    perfect = measure(expected, expected)
    empty_like = measure(make_case("X", {"Z?": [("z1", 0), ("z2", 0)]}), expected)

    combined = aggregate([perfect, empty_like])

    assert combined.questions.precision == 0.5
    assert combined.questions.recall == 0.5


def test_render_table_has_aggregate_row() -> None:
    client = MockLLMClient.from_fixtures(GOLDEN_DIR)
    report = asyncio.run(run_harness(client, GOLDEN_DIR))

    assert "AGGREGATE" in render_table(report)


def test_cli_writes_json_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "report.json"

    exit_code = main(["--golden", str(GOLDEN_DIR), "--out", str(out)])

    assert exit_code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["aggregate"]["score_accuracy"] == 1.0
    assert "AGGREGATE" in capsys.readouterr().out
