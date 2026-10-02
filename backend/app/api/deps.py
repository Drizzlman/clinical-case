"""Composition of dependencies: wire concrete adapters to domain ports/use cases."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.health import SqlAlchemyHealthProbe
from app.data.repositories import (
    SqlAlchemyCaseRepository,
    SqlAlchemySubmissionRepository,
)
from app.data.session import get_session
from app.domain.ports import CaseRepository, HealthProbe, SubmissionRepository
from app.domain.use_cases.create_case import CreateCase
from app.domain.use_cases.get_case import GetCase
from app.domain.use_cases.get_submission import GetSubmission
from app.domain.use_cases.list_cases import ListCases
from app.domain.use_cases.submit_answers import SubmitAnswers

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_case_repository(session: SessionDep) -> CaseRepository:
    return SqlAlchemyCaseRepository(session)


def get_submission_repository(session: SessionDep) -> SubmissionRepository:
    return SqlAlchemySubmissionRepository(session)


def get_health_probe(session: SessionDep) -> HealthProbe:
    return SqlAlchemyHealthProbe(session)


CaseRepositoryDep = Annotated[CaseRepository, Depends(get_case_repository)]
SubmissionRepositoryDep = Annotated[SubmissionRepository, Depends(get_submission_repository)]
HealthProbeDep = Annotated[HealthProbe, Depends(get_health_probe)]


def get_create_case(repository: CaseRepositoryDep) -> CreateCase:
    return CreateCase(repository=repository)


def get_get_case(repository: CaseRepositoryDep) -> GetCase:
    return GetCase(repository=repository)


def get_list_cases(repository: CaseRepositoryDep) -> ListCases:
    return ListCases(repository=repository)


def get_submit_answers(
    case_repository: CaseRepositoryDep,
    submission_repository: SubmissionRepositoryDep,
) -> SubmitAnswers:
    return SubmitAnswers(
        case_repository=case_repository,
        submission_repository=submission_repository,
    )


def get_get_submission(
    case_repository: CaseRepositoryDep,
    submission_repository: SubmissionRepositoryDep,
) -> GetSubmission:
    return GetSubmission(
        case_repository=case_repository,
        submission_repository=submission_repository,
    )


CreateCaseDep = Annotated[CreateCase, Depends(get_create_case)]
GetCaseDep = Annotated[GetCase, Depends(get_get_case)]
ListCasesDep = Annotated[ListCases, Depends(get_list_cases)]
SubmitAnswersDep = Annotated[SubmitAnswers, Depends(get_submit_answers)]
GetSubmissionDep = Annotated[GetSubmission, Depends(get_get_submission)]
