"""Per-field precision/recall/F1 for questions and options, plus score accuracy."""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass

from app.harness.normalize import normalize_text
from app.schema.case import CaseExtraction


@dataclass(frozen=True, slots=True)
class TextMetrics:
    """Precision/recall/F1 for a set of normalized text fields."""

    precision: float
    recall: float
    f1: float


@dataclass(frozen=True, slots=True)
class CaseMetrics:
    """Metrics for a single case or an aggregate over a corpus."""

    questions: TextMetrics
    options: TextMetrics
    score_accuracy: float


@dataclass(frozen=True, slots=True)
class Counts:
    """Confusion counts for set matching."""

    tp: int
    fp: int
    fn: int

    def __add__(self, other: Counts) -> Counts:
        return Counts(self.tp + other.tp, self.fp + other.fp, self.fn + other.fn)


@dataclass(frozen=True, slots=True)
class Measurement:
    """Raw counts plus derived metrics for one case (used for aggregation)."""

    question_counts: Counts
    option_counts: Counts
    matched_options: int
    equal_scores: int
    metrics: CaseMetrics


def prf1(counts: Counts) -> TextMetrics:
    """Derive precision/recall/F1 from confusion counts."""

    predicted = counts.tp + counts.fp
    actual = counts.tp + counts.fn
    precision = counts.tp / predicted if predicted else 0.0
    recall = counts.tp / actual if actual else 0.0
    denominator = precision + recall
    f1 = 2 * precision * recall / denominator if denominator else 0.0
    return TextMetrics(precision=precision, recall=recall, f1=f1)


def _counts(
    extracted: AbstractSet[Hashable], expected: AbstractSet[Hashable]
) -> Counts:
    tp = sum(1 for item in extracted if item in expected)
    return Counts(tp=tp, fp=len(extracted) - tp, fn=len(expected) - tp)


def _question_set(case: CaseExtraction) -> set[str]:
    return {normalize_text(question.text) for question in case.questions}


def _option_keys(case: CaseExtraction) -> set[tuple[str, str]]:
    return {
        (normalize_text(question.text), normalize_text(option.text))
        for question in case.questions
        for option in question.options
    }


def _score_map(case: CaseExtraction) -> dict[tuple[str, str], float]:
    return {
        (normalize_text(question.text), normalize_text(option.text)): float(option.score)
        for question in case.questions
        for option in question.options
    }


def measure(extracted: CaseExtraction, expected: CaseExtraction) -> Measurement:
    """Compute per-field metrics and raw counts for one case."""

    question_counts = _counts(_question_set(extracted), _question_set(expected))
    extracted_options = _option_keys(extracted)
    expected_options = _option_keys(expected)
    option_counts = _counts(extracted_options, expected_options)

    matched = extracted_options & expected_options
    extracted_scores = _score_map(extracted)
    expected_scores = _score_map(expected)
    equal_scores = sum(
        1 for key in matched if extracted_scores[key] == expected_scores[key]
    )
    score_accuracy = equal_scores / len(matched) if matched else 0.0

    metrics = CaseMetrics(
        questions=prf1(question_counts),
        options=prf1(option_counts),
        score_accuracy=score_accuracy,
    )
    return Measurement(
        question_counts=question_counts,
        option_counts=option_counts,
        matched_options=len(matched),
        equal_scores=equal_scores,
        metrics=metrics,
    )


def evaluate_case(extracted: CaseExtraction, expected: CaseExtraction) -> CaseMetrics:
    """Convenience wrapper returning only the metrics for one case."""

    return measure(extracted, expected).metrics


def aggregate(measurements: Sequence[Measurement]) -> CaseMetrics:
    """Micro-average counts across cases, then derive metrics."""

    question_counts = Counts(0, 0, 0)
    option_counts = Counts(0, 0, 0)
    matched_options = 0
    equal_scores = 0
    for measurement in measurements:
        question_counts = question_counts + measurement.question_counts
        option_counts = option_counts + measurement.option_counts
        matched_options += measurement.matched_options
        equal_scores += measurement.equal_scores
    return CaseMetrics(
        questions=prf1(question_counts),
        options=prf1(option_counts),
        score_accuracy=equal_scores / matched_options if matched_options else 0.0,
    )
