"""This module defines ``DBConnection`` class."""

from asyncio import current_task
from typing import Any, TypeVar

from sqlalchemy.engine import Result
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql.selectable import TypedReturnsRows

from .base_model import ActiveRecordBaseModel

_T = TypeVar('_T', bound=Any)


class DBConnection:
    """Provides functions for connecting to a database
    and initializing tables.

    The ``init_db`` method can be called to initialize
    the database tables::

        from sqlactive import DBConnection

        DATABASE_URL = 'sqlite+aiosqlite://'
        conn = DBConnection(DATABASE_URL, echo=True)
        asyncio.run(conn.init_db()) # Initialize the database

    If your base model is not ``ActiveRecordBaseModel`` you must
    pass your base model class to the ``init_db`` method in the
    ``base_model`` argument::

        from sqlactive import DBConnection, ActiveRecordBaseModel

        class BaseModel(ActiveRecordBaseModel):
            __abstract__ = True

        DATABASE_URL = 'sqlite+aiosqlite://'
        conn = DBConnection(DATABASE_URL, echo=True)
        asyncio.run(conn.init_db(BaseModel)) # Pass your base model

    The ``close`` method can be called to close the database
    connection. It also sets the ``session`` attribute of
    the base model to ``None``::

        from sqlactive import DBConnection

        DATABASE_URL = 'sqlite+aiosqlite://'
        conn = DBConnection(DATABASE_URL, echo=True)

        # Perform operations...

        asyncio.run(conn.close()) # Close the connection

    If your base model is not ``ActiveRecordBaseModel``
    you should pass your base model class to the ``close`` method
    in the ``base_model`` argument::

        from sqlactive import DBConnection, ActiveRecordBaseModel

        # Note that it does not matter if your base model
        # inherits from ``ActiveRecordBaseModel``, you still
        # need to pass it to this method
        class BaseModel(ActiveRecordBaseModel):
            __abstract__ = True

        DATABASE_URL = 'sqlite+aiosqlite://'
        conn = DBConnection(DATABASE_URL, echo=True)

        # Perform operations...

        asyncio.run(conn.close(BaseModel)) # Pass your base model
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
            bind=self.async_engine, expire_on_commit=False
        )
        self.async_scoped_session = async_scoped_session(
            self.async_sessionmaker, scopefunc=current_task
        )

    async def init_db(
        self, base_model: type[ActiveRecordBaseModel] | None = None
    ) -> None:
        """Initializes the database tables.

        If your base model is not ``ActiveRecordBaseModel`` you
        must pass your base model class to this method in the
        ``base_model`` argument::

            from sqlactive import DBConnection, ActiveRecordBaseModel

            # Note that it does not matter if your base model
            # inherits from ``ActiveRecordBaseModel``, you still
            # need to pass it to this method
            class BaseModel(ActiveRecordBaseModel):
                __abstract__ = True

            DATABASE_URL = 'sqlite+aiosqlite://'
            conn = DBConnection(DATABASE_URL, echo=True)
            asyncio.run(conn.init_db(BaseModel)) # Pass your base model
        """
        if not base_model:
            base_model = ActiveRecordBaseModel

        base_model.set_session(self.async_scoped_session)

        async with self.async_engine.begin() as conn:
            await conn.run_sync(base_model.metadata.create_all)

    async def close(
        self, base_model: type[ActiveRecordBaseModel] | None = None
    ) -> None:
        """Closes the database connection and sets the ``session``
        attribute of the base model to ``None``.

        If your base model is not ``ActiveRecordBaseModel``
        you should pass your base model class to this method
        in the ``base_model`` argument::

            from sqlactive import DBConnection, ActiveRecordBaseModel

            # Note that it does not matter if your base model
            # inherits from ``ActiveRecordBaseModel``, you still
            # need to pass it to this method
            class BaseModel(ActiveRecordBaseModel):
                __abstract__ = True

            DATABASE_URL = 'sqlite+aiosqlite://'
            conn = DBConnection(DATABASE_URL, echo=True)
            asyncio.run(conn.init_db(BaseModel))

            # Perform operations...

            asyncio.run(conn.close(BaseModel))  # Pass your base model
        """
        await self.async_engine.dispose()
        if base_model:
            base_model.close_session()
        ActiveRecordBaseModel.close_session()


async def execute(
    statement: TypedReturnsRows[_T],
    base_model: type[ActiveRecordBaseModel] | None = None,
    params: _CoreAnyExecuteParams | None = None,
    **kwargs,
) -> Result[_T]:
    """Executes a statement using the ``AsyncSession``
    of the ``ActiveRecordBaseModel`` and return a buffered
    ``sqlalchemy.engine.Result`` object::

        query = select(User.age, func.count(User.id)).group_by(User.age)
        result = await execute(query)

    The ``statement``, ``params`` and ``kwargs`` arguments
    of this function are the same as the arguments
    of the ``execute`` method of the
    ``sqlalchemy.ext.asyncio.AsyncSession`` class.

    If your base model is not ``ActiveRecordBaseModel``
    you must pass your base model class to this method
    in the ``base_model`` argument::

        # Note that it does not matter if your base model
        # inherits from ``ActiveRecordBaseModel``, you still
        # need to pass it to this method
        class BaseModel(ActiveRecordBaseModel):
            __abstract__ = True

        class User(BaseModel):
            __tablename__ = 'users'
            # ...

        query = select(User.age, func.count(User.id)).group_by(User.age)
        result = await execute(query, BaseModel)  # or execute(query, User)

    .. warning::
        Your base model must have a session in order to use this method.
        Otherwise, it will raise an ``NoSessionError`` exception.
        If you are not using the ``DBConnection`` class to initialize
        your base model, you can call its ``set_session`` method
        to set the session.
    """
    if not base_model:
        base_model = ActiveRecordBaseModel
    async with base_model.AsyncSession() as session:
        return await session.execute(statement, params, **kwargs)
