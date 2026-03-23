"""Database connection helper."""

from asyncio import current_task
from typing import Any

from sqlalchemy.engine import Result
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql.selectable import TypedReturnsRows

from .base_model import ActiveRecordBaseModel
from .types import RowType


class DBConnection:
    """Database connection helper.

    Provides functions for connecting to a database
    and initializing tables.

    The ``init_db`` method can be called to initialize
    the database tables::

        from sqlactive import DBConnection

        DATABASE_URL = 'sqlite+aiosqlite://'
        conn = DBConnection(DATABASE_URL, echo=True)
        asyncio.run(conn.init_db()) # Initialize the database

    If your base model is not ``ActiveRecordBaseModel`` you must
    pass your base model class to the ``init_db`` method::

        from sqlactive import DBConnection, ActiveRecordBaseModel

        class BaseModel(ActiveRecordBaseModel):
            __abstract__ = True

        DATABASE_URL = 'sqlite+aiosqlite://'
        conn = DBConnection(DATABASE_URL, echo=True)
        asyncio.run(conn.init_db(BaseModel)) # Pass your base model

    You can also initialize multiple base models at once::

        asyncio.run(conn.init_db(BaseModel, AnotherBaseModel))

    The ``close`` method can be called to close the database
    connection::

        from sqlactive import DBConnection

        DATABASE_URL = 'sqlite+aiosqlite://'
        conn = DBConnection(DATABASE_URL, echo=True)

        # Perform operations...

        asyncio.run(conn.close()) # Close the connection
    """

    def __init__(self, url: str | URL, **kw: Any) -> None:
        """Create a new async database connection object.

        Calls the ``sqlalchemy.ext.asyncio.create_async_engine``
        function to create an async engine instance.

        Also, calls the ``sqlalchemy.ext.asyncio.async_sessionmaker``
        function to create an async sessionmaker instance passing
        the async engine and the ``expire_on_commit`` parameter set to
        ``False``.

        Then, calls the ``sqlalchemy.ext.asyncio.async_scoped_session``
        function to create an async scoped session instance which scope
        function is ``current_task`` from the ``asyncio`` module.

        Parameters
        ----------
        url : str | URL
            Database URL.
        **kw : Any
            Keyword arguments to be passed to the
            ``sqlalchemy.ext.asyncio.create_async_engine`` function.

        """
        self.async_engine = create_async_engine(url, **kw)
        self.async_sessionmaker = async_sessionmaker(
            bind=self.async_engine,
            expire_on_commit=False,
        )
        self.async_scoped_session = async_scoped_session(
            self.async_sessionmaker,
            scopefunc=current_task,
        )

    async def init_db(
        self,
        *base_models: type[ActiveRecordBaseModel],
    ) -> None:
        """Initialize the database tables for the given base models."""
        for base_model in base_models or [ActiveRecordBaseModel]:
            base_model.set_session(self.async_scoped_session)
            async with self.async_engine.begin() as conn:
                await conn.run_sync(base_model.metadata.create_all)

    async def close(self) -> None:
        """Close the database connection and remove the session."""
        await self.async_scoped_session.remove()
        self.async_sessionmaker.configure(bind=None)
        await self.async_engine.dispose()


async def execute(
    async_scoped_session: async_scoped_session[AsyncSession],
    statement: TypedReturnsRows[RowType],
    params: _CoreAnyExecuteParams | None = None,
    **kwargs,
) -> Result[RowType]:
    """Execute a native SQLAlchemy statement.

    The ``statement``, ``params`` and ``kwargs`` arguments
    of this function are the same as the arguments
    of the ``execute`` method of the
    ``sqlalchemy.ext.asyncio.AsyncSession`` class.

    Examples
    --------
    >>> from sqlactive import DBConnection
    >>> conn = DBConnection(DATABASE_URL, echo=True)
    >>> query = select(User.age, func.count(User.id)).group_by(User.age)
    >>> result = await execute(conn.async_scoped_session, query)
    >>> result
    <sqlalchemy.engine.result.Result object at 0x...>
    >>> users = result.all()
    >>> users
    [(20, 1), (22, 4), (25, 12)]

    """
    async with async_scoped_session() as session:
        return await session.execute(statement, params, **kwargs)
