"""This module defines `DBConnection` class."""

from typing import Any
from asyncio import current_task

from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, async_scoped_session

from .base_model import ActiveRecordBaseModel


class DBConnection:
    """Provides functions for connecting to a database
    and initializing tables.
    """

    def __init__(self, url: str | URL, **kw: Any) -> None:
        """Create a new async database connection object.

        Calls the `sqlalchemy.ext.asyncio.create_async_engine` function
        to create an async engine instance.

        Also, calls the `sqlalchemy.ext.asyncio.async_sessionmaker` function
        to create an async sessionmaker instance passing the async engine and
        the `expire_on_commit` parameter set to `False`. Then, calls the
        `sqlalchemy.ext.asyncio.async_scoped_session` function to create
        an async scoped session instance which scope function is `current_task`
        from the `asyncio` module.

        Example:

        ```python
            from sqlactive import DBConnection

            DATABASE_URL = 'sqlite+aiosqlite://'
            conn = DBConnection(DATABASE_URL, echo=True)
        ```

        After that, the `init_db` method can be called to initialize the
        database tables, as shown in the following example:

        ```python
            from sqlactive import ActiveRecordBaseModel, DBConnection

            class BaseModel(ActiveRecordBaseModel):
                __abstract__ = True

            DATABASE_URL = 'sqlite+aiosqlite://'
            conn = DBConnection(DATABASE_URL, echo=True)
            asyncio.run(conn.init_db(BaseModel))
        ```

        If no base model is provided, the `ActiveRecordBaseModel` class will
        be used as the base model:

        ```python
            from sqlactive import DBConnection

            DATABASE_URL = 'sqlite+aiosqlite://'
            conn = DBConnection(DATABASE_URL, echo=True)
            asyncio.run(conn.init_db())
        ```

        Finally, the `close` method can be called to close the database
        connection, as shown in the following example:

        ```python
            from sqlactive import DBConnection

            DATABASE_URL = 'sqlite+aiosqlite://'
            conn = DBConnection(DATABASE_URL, echo=True)
            ... # Perform operations
            asyncio.run(conn.close())
        ```

        Parameters
        ----------
        url : str | URL
            Database URL.
        **kw : Any
            Keyword arguments to be passed to the
            `sqlalchemy.ext.asyncio.create_async_engine` function.
        """

        self.async_engine = create_async_engine(url, **kw)
        self.async_sessionmaker = async_sessionmaker(bind=self.async_engine, expire_on_commit=False)
        self.async_scoped_session = async_scoped_session(self.async_sessionmaker, scopefunc=current_task)

    async def init_db(self, base_model: type[ActiveRecordBaseModel] | None = ActiveRecordBaseModel) -> None:
        """Initializes the database tables.

        Parameters
        ----------
        base_model : type[ActiveRecordBaseModel] | None, optional
            Base model class, by default `ActiveRecordBaseModel`.
        """

        if not base_model:
            base_model = ActiveRecordBaseModel

        base_model.set_session(self.async_scoped_session)

        async with self.async_engine.begin() as conn:
            await conn.run_sync(base_model.metadata.create_all)

    async def close(self) -> None:
        """Closes the database connection."""

        await self.async_engine.dispose()
