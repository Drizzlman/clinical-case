"""Run extraction over a golden set and print/emit an accuracy report."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.client.base import LLMClient
from app.client.mock import MockLLMClient
from app.harness.metrics import CaseMetrics, Measurement, aggregate, measure
from app.schema.case import CaseExtraction


@dataclass(frozen=True, slots=True)
class GoldenCase:
    """A raw text paired with the expected structured case."""

    name: str
    raw_text: str
    expected: CaseExtraction


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Per-case metrics with the fixture name."""

    name: str
    metrics: CaseMetrics


@dataclass(frozen=True, slots=True)
class Report:
    """The full harness result: per-case rows plus a corpus aggregate."""

    cases: tuple[CaseResult, ...]
    aggregate: CaseMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "cases": [
                {"name": case.name, **_metrics_to_dict(case.metrics)}
                for case in self.cases
            ],
            "aggregate": _metrics_to_dict(self.aggregate),
        }


def _metrics_to_dict(metrics: CaseMetrics) -> dict[str, Any]:
    return {
        "questions": {
            "precision": metrics.questions.precision,
            "recall": metrics.questions.recall,
            "f1": metrics.questions.f1,
        },
        "options": {
            "precision": metrics.options.precision,
            "recall": metrics.options.recall,
            "f1": metrics.options.f1,
        },
        "score_accuracy": metrics.score_accuracy,
    }


def load_golden(directory: Path) -> tuple[GoldenCase, ...]:
    """Load ``*.json`` fixtures of shape ``{"raw_text": ..., "expected": {...}}``."""

    cases: list[GoldenCase] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        cases.append(
            GoldenCase(
                name=path.stem,
                raw_text=str(payload["raw_text"]),
                expected=CaseExtraction.model_validate(payload["expected"]),
            )
        )
    return tuple(cases)


async def run_harness(client: LLMClient, golden_dir: Path) -> Report:
    """Run the client over every golden case and aggregate the metrics."""

    results: list[CaseResult] = []
    measurements: list[Measurement] = []
    for golden in load_golden(golden_dir):
        extracted = await client.extract_case(golden.raw_text)
        measurement = measure(extracted, golden.expected)
        measurements.append(measurement)
        results.append(CaseResult(name=golden.name, metrics=measurement.metrics))
    return Report(cases=tuple(results), aggregate=aggregate(measurements))


def render_table(report: Report) -> str:
    """Render a fixed-width text table for stdout."""

    header = (
        f"{'case':<24}{'q_P':>7}{'q_R':>7}{'q_F1':>7}"
        f"{'o_P':>7}{'o_R':>7}{'o_F1':>7}{'score':>8}"
    )
    lines = [header, "-" * len(header)]
    for case in report.cases:
        lines.append(_row(case.name, case.metrics))
    lines.append("-" * len(header))
    lines.append(_row("AGGREGATE", report.aggregate))
    return "\n".join(lines)


def _row(label: str, metrics: CaseMetrics) -> str:
    return (
        f"{label:<24}"
        f"{metrics.questions.precision:>7.3f}"
        f"{metrics.questions.recall:>7.3f}"
        f"{metrics.questions.f1:>7.3f}"
        f"{metrics.options.precision:>7.3f}"
        f"{metrics.options.recall:>7.3f}"
        f"{metrics.options.f1:>7.3f}"
        f"{metrics.score_accuracy:>8.3f}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: ``python -m app.harness.runner --golden ... --out ...``."""

    parser = argparse.ArgumentParser(description="Extraction accuracy harness")
    parser.add_argument(
        "--golden",
        type=Path,
        default=Path("tests/golden"),
        help="Directory with golden fixtures (default: tests/golden)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write the JSON report",
    )
    args = parser.parse_args(argv)

    client = MockLLMClient.from_fixtures(args.golden)
    report = asyncio.run(run_harness(client, args.golden))
    print(render_table(report))
    if args.out is not None:
        args.out.write_text(
            json.dumps(report.to_dict(), indent=2), encoding="utf-8"
        )
        print(f"\nJSON report written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
