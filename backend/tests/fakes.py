"""In-memory adapter for the CaseRepository port (no database, no Docker)."""

from __future__ import annotations

from dataclasses import replace

from app.domain.entities import Case, CaseSummary, Submission


class InMemoryCaseRepository:
    """Dict-backed test double mirroring the persistence port."""

    def __init__(self) -> None:
        self._store: dict[int, Case] = {}
        self._next_id = 1

    async def add(self, case: Case) -> Case:
        case_id = self._next_id
        self._next_id += 1
        stored = self._with_ids(case, case_id)
        self._store[case_id] = stored
        return stored

    async def get(self, case_id: int) -> Case | None:
        return self._store.get(case_id)

    async def list_summaries(self) -> tuple[CaseSummary, ...]:
        return tuple(
            CaseSummary(
                id=case_id,
                title=case.title,
                description=case.description,
                question_count=len(case.questions),
            )
            for case_id, case in sorted(self._store.items())
        )

    @staticmethod
    def _with_ids(case: Case, case_id: int) -> Case:
        questions = []
        option_id = 1
        for question_index, question in enumerate(case.questions, start=1):
            options = []
            for option in question.options:
                options.append(replace(option, id=option_id))
                option_id += 1
            questions.append(
                replace(question, id=question_index, case_id=case_id, options=tuple(options))
            )
        return replace(case, id=case_id, questions=tuple(questions))


class InMemorySubmissionRepository:
    """Dict-backed test double mirroring the submission persistence port."""

    def __init__(self) -> None:
        self._store: dict[int, Submission] = {}
        self._next_id = 1

    async def add(self, submission: Submission) -> Submission:
        submission_id = self._next_id
        self._next_id += 1
        stored = replace(submission, id=submission_id)
        self._store[submission_id] = stored
        return stored

    async def get(self, submission_id: int) -> Submission | None:
        return self._store.get(submission_id)
