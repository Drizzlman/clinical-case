"""Driven ports: abstract interfaces the domain depends on (implemented by adapters)."""

from typing import Protocol

from app.domain.entities import Case, CaseSummary, Submission


class CaseRepository(Protocol):
    """Persistence port for the Case aggregate."""

    async def add(self, case: Case) -> Case: ...

    async def get(self, case_id: int) -> Case | None: ...

    async def list_summaries(self) -> tuple[CaseSummary, ...]: ...


class SubmissionRepository(Protocol):
    """Persistence port for the Submission aggregate."""

    async def add(self, submission: Submission) -> Submission: ...

    async def get(self, submission_id: int) -> Submission | None: ...


class HealthProbe(Protocol):
    """Readiness port: reports whether the underlying datastore is reachable."""

    async def check(self) -> bool: ...
