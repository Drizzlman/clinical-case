"""Datastore readiness adapter implementing the ``HealthProbe`` port."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyHealthProbe:
    """Checks database connectivity with a lightweight ``SELECT 1``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check(self) -> bool:
        try:
            await self._session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True
