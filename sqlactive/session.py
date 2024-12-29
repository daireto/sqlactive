"""This module defines `SessionMixin` class."""

from sqlalchemy.ext.asyncio import async_scoped_session, AsyncSession

from .utils import classproperty
from .exceptions import NoSessionError


class SessionMixin:
    """Mixin to handle sessions."""

    _session: async_scoped_session[AsyncSession] | None = None

    @classmethod
    def set_session(cls, session: async_scoped_session[AsyncSession]) -> None:
        """Sets the async session factory to the model.

        Parameters
        ----------
        session : async_scoped_session[AsyncSession]
            Async session factory.
        """

        cls._session = session

    @classproperty
    def _AsyncSession(cls) -> async_scoped_session[AsyncSession]:
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
            raise NoSessionError('Cannot get session. Please, call SaActiveRecord.set_session()')
