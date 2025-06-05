"""Session mixin for SQLAlchemy models.

Provides functions for handling asynchronous scoped sessions.

The base model must have a session in order to perform any database
operation. Always call the ``set_session`` method before performing
any operation.
"""

from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession
from sqlalchemy.ext.asyncio import async_scoped_session

from .exceptions import NoSessionError
from .utils import classproperty


class SessionMixin:
    """Mixin to handle sessions."""

    _session: async_scoped_session[SQLAlchemyAsyncSession] | None = None

    @classmethod
    def set_session(cls, session: async_scoped_session[SQLAlchemyAsyncSession]) -> None:
        """Set the async session factory.

        Parameters
        ----------
        session : async_scoped_session[AsyncSession]
            Async session factory.

        """
        cls._session = session

    @classmethod
    def close_session(cls) -> None:
        """Close the async session."""
        cls._session = None

    @classproperty
    def AsyncSession(cls) -> async_scoped_session[SQLAlchemyAsyncSession]:  # noqa: N802
        """Async session factory.

        Usage::

            async with SaActiveRecord.AsyncSession() as session:
                session.add(model)
                await session.commit()

        Raises
        ------
        NoSessionError
            If no session is available.

        """
        if cls._session is not None:
            return cls._session
        raise NoSessionError
