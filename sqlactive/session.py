"""This module defines `SessionMixin` class."""

from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from .exceptions import NoSessionError
from .utils import classproperty


class SessionMixin:
    """Mixin to handle sessions."""

    _session: async_scoped_session[AsyncSession] | None = None

    @classmethod
    def set_session(cls, session: async_scoped_session[AsyncSession]) -> None:
        """Sets the async session factory.

        Parameters
        ----------
        session : async_scoped_session[AsyncSession]
            Async session factory.
        """

        cls._session = session

    @classmethod
    def close_session(cls) -> None:
        """Closes the session."""

        cls._session = None

    @classproperty
    def AsyncSession(cls) -> async_scoped_session[AsyncSession]:
        """Async session factory.

        Usage:

        ```python
            async with SaActiveRecord.AsyncSession() as session:
                session.add(model)
                await session.commit()
        ```

        Raises
        ------
        NoSessionError
            If no session is available.
        """

        if cls._session is not None:
            return cls._session
        else:
            raise NoSessionError()
