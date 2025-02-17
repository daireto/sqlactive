"""This module defines `ActiveRecordMixin` class."""

from collections.abc import Sequence
from typing import Any, Literal, overload

from sqlalchemy.engine import Result, Row, ScalarResult
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute
from sqlalchemy.sql import Select, select
from sqlalchemy.sql._typing import (
    _ColumnExpressionArgument,
    _ColumnExpressionOrStrLabelArgument,
    _ColumnsClauseArgument,
)
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.operators import OperatorType
from typing_extensions import Self, deprecated

from .async_query import AsyncQuery
from .exceptions import NoSettableError
from .session import SessionMixin
from .smart_query import SmartQueryMixin
from .utils import classproperty


class ActiveRecordMixin(SessionMixin, SmartQueryMixin):
    """Mixin for Active Record style models.

    Provides a set of ActiveRecord-like helper methods for SQLAlchemy models,
    allowing for more intuitive and chainable database operations with async/await support.

    Define a base model class that inherits from this class:
    >>> from sqlalchemy import String
    >>> from sqlalchemy import Mapped, mapped_column
    >>> from sqlactive import ActiveRecordMixin
    >>> class BaseModel(ActiveRecordMixin):
    ...     __abstract__ = True

    You can also make your base inherit from the ``ActiveRecordBaseModel``
    class which is a combination of ``ActiveRecordMixin``, ``SerializationMixin``
    and ``TimestampMixin`` (this is the recommended way to use this library):
    >>> from sqlactive import ActiveRecordBaseModel
    >>> class BaseModel(ActiveRecordBaseModel):
    ...     __abstract__ = True

    Define your model classes that inherit from `BaseModel`:
    >>> class User(BaseModel):
    ...     __tablename__ = 'users'
    ...     id: Mapped[int] = mapped_column(primary_key=True)
    ...     name: Mapped[str] = mapped_column(String(100))
    ...     # ...and more

    Enjoy the power of Active Record!
    >>> user = User.insert(name='Bob Williams', age=30)
    >>> user
    User(id=6)
    >>> user.name
    'Bob Williams'
    >>> User.where(name__startswith='Bob').all()
    [User(id=3), User(id=6)]
    >>> joe = User.get(1)
    >>> joe.name
    'Joe Harris'
    >>> joe.update(name='Joe Smith')
    >>> joe.name
    'Joe Smith'
    >>> joe.delete()
    >>> User.get(1)
    None
    >>> User.all()
    [User(id=2), User(id=3), User(id=4), User(id=5), User(id=6)]

    .. warning::
        All relations used in filtering/sorting/grouping should be explicitly set,
        not just being a `backref`. This is because SQLActive does not know the
        relation direction and cannot infer it. So, when defining a relationship like::

            class User(BaseModel):
                # ...
                posts: Mapped[list['Post']] = relationship(back_populates='user')

        It is required to define the reverse relationship::

            class Post(BaseModel):
                # ...
                user: Mapped['User'] = relationship(back_populates='posts')

    Visit the `API Reference <https://daireto.github.io/sqlactive/api/active-record-mixin/#api-reference>`_
    for the full list of available methods.
    """

    __abstract__ = True

    @classproperty
    def query(cls) -> Select[tuple[Self]]:
        """Returns a new `sqlalchemy.sql.Select` instance
        for the model.

        This is a shortcut for `select(cls)`.

        Examples
        --------
        Assume a model ``User``:
        >>> User.query
        'SELECT * FROM users'

        Is equivalent to:
        >>> from sqlalchemy import select
        >>> select(User)
        'SELECT * FROM users'
        """
        return select(cls)  # type: ignore

    def fill(self, **kwargs) -> Self:
        """Fills the object with values from `kwargs`
        without saving to the database.

        Returns
        -------
        self
            The instance itself for method chaining.

        Raises
        ------
        AttributeError
            If attribute does not exist.
        NoSettableError
            If attribute is not settable.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> user = User(name='Bob')
        >>> user.name
        'Bob'
        >>> user.fill(name='Bob Williams', age=30)
        >>> user.name
        'Bob Williams'
        >>> user.age
        30
        """
        for name in kwargs.keys():
            if not hasattr(self, name):
                raise AttributeError(f"no such attribute: '{name}' in model '{self.__class__.__name__}'")
            if name in self.settable_attributes:
                setattr(self, name, kwargs[name])
            else:
                raise NoSettableError(self.__class__.__name__, name)

        return self

    async def save(self) -> Self:
        """Saves the current row.

        .. note::
            All database errors will trigger a rollback and be raised.

        Returns
        -------
        self
            The instance itself for method chaining.

        Raises
        ------
        Exception
            If saving fails.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> user = User(name='Bob Williams', age=30)
        >>> await user.save()
        """
        async with self.AsyncSession() as session:
            try:
                session.add(self)
                await session.commit()
                await session.refresh(self)
                return self
            except Exception as error:
                await session.rollback()
                raise error

    async def update(self, **kwargs) -> Self:
        """Updates the current row with the provided values.

        This is the same as calling `self.fill(**kwargs).save()`.

        Returns
        -------
        self
            The instance itself for method chaining.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> user = User(name='Bob', age=30)
        >>> user.name
        'Bob'
        >>> await user.update(name='Bob Williams', age=31)
        >>> user.name
        'Bob Williams'
        """
        return await self.fill(**kwargs).save()

    async def delete(self) -> None:
        """Deletes the current row.

        .. warning::
            This is not a soft delete method. It will permanently delete the row from
            the database. So, if you want to keep the row in the database, you can implement
            a custom soft delete method, i.e. using `save()` method to update the row with a
            flag indicating if the row is deleted or not (i.e. a boolean `is_deleted` column).

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> user = await User.find(username='Bob324').one_or_none()
        >>> user.name
        'Bob Williams'
        >>> await user.delete()
        >>> await User.find(username='Bob324').one_or_none()
        None
        """
        async with self.AsyncSession() as session:
            try:
                await session.delete(self)
                await session.commit()
            except Exception as error:
                await session.rollback()
                raise error

    async def remove(self) -> None:
        """Synonym for `delete()`."""
        return await self.delete()

    @classmethod
    async def insert(cls, **kwargs) -> Self:
        """Inserts a new row and returns the saved instance.

        Returns
        -------
        self
            The created instance for method chaining.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> user = await User.insert(name='Bob Williams', age=30)
        >>> user.name
        'Bob Williams'
        """
        return await cls().fill(**kwargs).save()

    @classmethod
    async def create(cls, **kwargs) -> Self:
        """Synonym for `insert()`."""
        return await cls.insert(**kwargs)

    @classmethod
    async def save_all(cls, rows: Sequence[Self], refresh: bool = False) -> None:
        """Saves multiple rows in a single transaction.

        When using this method to update existing rows, instances are not refreshed after
        commit by default. Accessing the attributes of the updated rows without refreshing
        them after commit will raise an ``sqlalchemy.orm.exc.DetachedInstanceError``.

        To access the attributes of updated rows, the ``refresh`` flag must be set to
        ``True`` in order to refresh them after commit.

        .. warning::
            Refreshing multiple instances may be expensive,
            which may lead to a higher latency due to additional database queries.

        .. note::
            When inserting new rows, refreshing the instances after commit is not necessary.
            The instances are already available after commit, but you still can use the
            ``refresh`` flag to refresh them if needed.

        Parameters
        ----------
        rows : Sequence[Self]
            Rows to be saved.
        refresh : bool, optional
            Whether to refresh the rows after commit, by default False.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Inserting new rows:
        >>> users = [
        ...     User(name='Bob Williams', age=30),
        ...     User(name='Jane Doe', age=31),
        ...     User(name='John Doe', age=32),
        ... ]
        >>> await User.save_all(users)
        >>> users[0].name
        'Bob Williams'
        >>> users[1].age
        31

        Updating existing rows (with refreshing after commit):
        >>> users = User.where(name__endswith='Doe').all()
        >>> for user in users:
        ...     user.name = user.name.replace('Doe', 'Smith')
        >>> await User.save_all(users, refresh=True)
        >>> users[0].name
        'Jane Smith'
        >>> users[1].name
        'John Smith'

        Updating existing rows (without refreshing after commit):
        >>> users = User.where(name__endswith='Doe').all()
        >>> for user in users:
        ...     user.name = user.name.replace('Doe', 'Smith')
        >>> await User.save_all(users)
        >>> users[0].name
        Traceback (most recent call last):
            ...
        DetachedInstanceError: Instance <User at 0x...> is not bound to a Session...
        """
        async with cls.AsyncSession() as session:
            try:
                session.add_all(rows)
                await session.commit()
                if refresh:
                    for row in rows:
                        await session.refresh(row)
            except Exception as error:
                await session.rollback()
                raise error

    @classmethod
    async def insert_all(cls, rows: Sequence[Self], refresh: bool = False) -> None:
        """Inserts multiple rows in a single transaction.

        This is mostly a shortcut for ``save_all()`` when inserting new rows.

        .. note::
            When inserting new rows, refreshing the instances after commit is not necessary.
            The instances are already available after commit, but you still can use the
            ``refresh`` flag to refresh them if needed.

        See the ``save_all()`` method for more details.
        """
        return await cls.save_all(rows, refresh)

    @classmethod
    async def update_all(cls, rows: Sequence[Self], refresh: bool = False) -> None:
        """Updates multiple rows in a single transaction.

        This is mostly a shortcut for ``save_all()`` when updating existing rows.

        If you are planning to access the attributes of the updated instances after commit,
        you must set the ``refresh`` flag to ``True`` in order to refresh them. Accessing
        the attributes of the updated instances without refreshing them after commit
        will raise an ``sqlalchemy.orm.exc.DetachedInstanceError``.

        .. warning::
            Refreshing multiple instances may be expensive,
            which may lead to a higher latency due to additional database queries.

        See the ``save_all()`` method for more details.
        """
        return await cls.save_all(rows, refresh)

    @classmethod
    async def delete_all(cls, rows: Sequence[Self]) -> None:
        """Deletes multiple rows in a single transaction.

        .. warning::
            This is not a soft delete method. It will permanently delete the row from
            the database. So, if you want to keep the row in the database, you can implement
            a custom soft delete method, i.e. using `save()` method to update the row with a
            flag indicating if the row is deleted or not (i.e. a boolean `is_deleted` column).

        Parameters
        ----------
        rows : Sequence[Self]
            Rows to be deleted.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> users = await User.where(name__endswith='Doe').all()
        >>> users
        [User(id=1), User(id=2)]
        >>> await User.delete_all(users)
        >>> await User.where(name__endswith='Doe').all()
        []
        """
        async with cls.AsyncSession() as session:
            try:
                for row in rows:
                    await session.delete(row)
                await session.commit()
            except Exception as error:
                await session.rollback()
                raise error

    @classmethod
    async def destroy(cls, *ids: object) -> None:
        """Deletes multiple rows by their primary key.

        This method can only be used if the model has a single primary key.
        Otherwise, it will raise a ``CompositePrimaryKeyError``.

        .. warning::
            This is not a soft delete method. It will permanently delete the row from
            the database. So, if you want to keep the row in the database, you can implement
            a custom soft delete method, i.e. using `save()` method to update the row with a
            flag indicating if the row is deleted or not (i.e. a boolean `is_deleted` column).

        Parameters
        ----------
        *ids : object
            Primary keys of the rows to be deleted.

        Raises
        ------
        CompositePrimaryKeyError
            If the model has a composite primary key.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> users = await User.where(name__endswith='Doe').all()
        >>> [user.id for user in users]
        [1, 2]
        >>> await User.destroy(1, 2)
        >>> await User.where(name__endswith='Doe').all()
        []
        """
        async with cls.AsyncSession() as session:
            try:
                query = cls.smart_query(filters={f'{cls.primary_key_name}__in': ids}).query
                rows = (await session.execute(query)).scalars().all()
                for row in rows:
                    await session.delete(row)
                await session.commit()
            except Exception as error:
                await session.rollback()
                raise error

    @classmethod
    async def get(
        cls,
        pk: object,
        join: Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
        subquery: Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
    ):
        """Fetches a row by primary key or `None`
        if no result is found.

        Example:
        >>> user = await User.get(1)
        >>> user
        # <User 1>
        >>> user = await User.get(3)  # Does not exist
        >>> user
        # None

        Parameters
        ----------
        pk : object
            Primary key value. It can also be a dict of composite primary key values.
        join : Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]], optional
            Paths to join eager load, by default None.
            IMPORTANT: See the documentation of `join()` method for details.
        subquery : Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]], optional
            Paths to subquery eager load, by default None.
            IMPORTANT: See the documentation of `with_subquery()` method for details.
        schema : dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict], optional
            Schema for the eager loading, by default None.
            IMPORTANT: See the documentation of `with_schema()` method for details.

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """
        if isinstance(pk, dict):
            criteria = pk
        else:
            criteria = {cls.primary_key_name: pk}

        async_query = cls.get_async_query()
        async_query = async_query.where(**criteria)
        if join:
            async_query = async_query.join(*join)
        if subquery:
            async_query = async_query.with_subquery(*subquery)
        if schema:
            async_query = async_query.with_schema(schema)
        return await async_query.unique_one_or_none()

    @classmethod
    async def get_or_fail(
        cls,
        pk: object,
        join: Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
        subquery: Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
    ):
        """Fetches a row by primary key or raises an exception
        if no result is found.

        Example:
        >>> user = await User.get_or_fail(1)
        >>> user
        # <User 1>
        >>> user = await User.get_or_fail(3)  # Does not exist
        >>> user
        # Traceback (most recent call last):
        #     ...
        # NoResultFound: 'User with id `3` was not found.'

        Parameters
        ----------
        pk : object
            Primary key value. It can also be a dict of composite primary key values.
        join : Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]], optional
            Paths to join eager load, by default None.
            IMPORTANT: See the documentation of `join()` method for details.
        subquery : Sequence[QueryableAttribute | tuple[QueryableAttribute, bool]], optional
            Paths to subquery eager load, by default None.
            IMPORTANT: See the documentation of `with_subquery()` method for details.
        schema : dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict], optional
            Schema for the eager loading, by default None.
            IMPORTANT: See the documentation of `with_schema()` method for details.

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """
        cursor = await cls.get(pk, join=join, subquery=subquery, schema=schema)
        if cursor:
            return cursor
        else:
            raise NoResultFound(f'{cls.__name__} with id `{pk}` was not found.')

    @classmethod
    async def scalars(cls):
        """Returns a `sqlalchemy.engine.ScalarResult` instance
        containing all results.

        Example:
        >>> scalar_result = await User.scalars()
        >>> scalar_result
        # <sqlalchemy.engine.result.ScalarResult>
        >>> users = scalar_result.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> scalar_result = await User.where(name='John Doe').scalars()
        >>> users = scalar_result.all()
        >>> users
        # [<User 2>]
        """

        async_query = cls.get_async_query()
        return await async_query.scalars()

    @overload
    @classmethod
    async def first(cls) -> Self | None: ...

    @overload
    @classmethod
    async def first(cls, scalar: Literal[True]) -> Self | None: ...

    @overload
    @classmethod
    async def first(cls, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def first(cls, scalar: bool) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def first(cls, scalar: bool = True):
        """Fetches the first row or `None` if no results are found.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> user = await User.first()
        >>> user
        # <User 1>
        >>> user = await User.first(scalar=False)
        >>> user
        # (<User 1>,)
        """

        async_query = cls.get_async_query()
        return await async_query.first(scalar)

    @overload
    @classmethod
    async def one(cls) -> Self: ...

    @overload
    @classmethod
    async def one(cls, scalar: Literal[True]) -> Self: ...

    @overload
    @classmethod
    async def one(cls, scalar: Literal[False]) -> Row[tuple[Any, ...]]: ...

    @overload
    @classmethod
    async def one(cls, scalar: bool) -> Self | Row[tuple[Any, ...]]: ...

    @classmethod
    async def one(cls, scalar: bool = True):
        """Fetches one row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> user = await User.where(name='John Doe').one()
        >>> user
        # <User 1>
        >>> user = await User.where(name='John Doe').one(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await User.where(name='Unknown').one()
        # Traceback (most recent call last):
        #     ...
        # NoResultFound: 'No result found.'

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls.get_async_query()
        return await async_query.one(scalar)

    @overload
    @classmethod
    async def one_or_none(cls) -> Self | None: ...

    @overload
    @classmethod
    async def one_or_none(cls, scalar: Literal[True]) -> Self | None: ...

    @overload
    @classmethod
    async def one_or_none(cls, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def one_or_none(cls, scalar: bool) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def one_or_none(cls, scalar: bool = True):
        """Fetches one row or `None` if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> user = await User.where(name='John Doe').one_or_none()
        >>> user
        # <User 1>
        >>> user = await User.where(name='John Doe').one_or_none(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await User.where(name='Unknown').one_or_none()
        >>> user
        # None

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls.get_async_query()
        return await async_query.one_or_none(scalar)

    @overload
    @classmethod
    async def all(cls) -> Sequence[Self]: ...

    @overload
    @classmethod
    async def all(cls, scalars: Literal[True]) -> Sequence[Self]: ...

    @overload
    @classmethod
    async def all(cls, scalars: Literal[False]) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    @classmethod
    async def all(cls, scalars: bool) -> Sequence[Self] | Sequence[Row[tuple[Any, ...]]]: ...

    @classmethod
    async def all(cls, scalars: bool = True):
        """Fetches all rows.

        If `scalars` is `True`, returns scalar values.

        Example:
        >>> users = await User.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.all(scalars=False)
        >>> users
        # [(<User 1>,), (<User 2>,), ...]
        """

        async_query = cls.get_async_query()
        return await async_query.all(scalars)

    @classmethod
    async def count(cls) -> int:
        """Fetches the number of rows.

        Example:
        >>> count = await User.count()
        >>> count
        # 34
        """

        async_query = cls.get_async_query()
        return await async_query.count()

    @overload
    @classmethod
    async def unique(cls) -> ScalarResult[Self]: ...

    @overload
    @classmethod
    async def unique(cls, scalars: Literal[True]) -> ScalarResult[Self]: ...

    @overload
    @classmethod
    async def unique(cls, scalars: Literal[False]) -> Result[tuple[Any, ...]]: ...

    @overload
    @classmethod
    async def unique(cls, scalars: bool) -> ScalarResult[Self] | Result[tuple[Any, ...]]: ...

    @classmethod
    async def unique(cls, scalars: bool = True):
        """Apply unique filtering to the objects returned
        in the result instance.

        If `scalars` is `True`, returns a `sqlalchemy.engine.ScalarResult`
        instance. Otherwise, returns a `sqlalchemy.engine.Result` instance.

        Example:
        >>> users = await User.unique()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.unique(scalars=False)
        >>> users
        # [(<User 1>,), (<User 2>,), ...]
        """

        async_query = cls.get_async_query()
        return await async_query.unique(scalars)

    @overload
    @classmethod
    async def unique_first(cls) -> Self | None: ...

    @overload
    @classmethod
    async def unique_first(cls, scalar: Literal[True]) -> Self | None: ...

    @overload
    @classmethod
    async def unique_first(cls, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def unique_first(cls, scalar: bool) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def unique_first(cls, scalar: bool = True):
        """Fetches the first unique row or `None` if no results are found.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> user = await User.unique_first()
        >>> user
        # <User 1>
        >>> user = await User.unique_first(scalar=False)
        >>> user
        # (<User 1>,)
        """

        async_query = cls.get_async_query()
        return await async_query.unique_first(scalar)

    @overload
    @classmethod
    async def unique_one(cls) -> Self: ...

    @overload
    @classmethod
    async def unique_one(cls, scalar: Literal[True]) -> Self: ...

    @overload
    @classmethod
    async def unique_one(cls, scalar: Literal[False]) -> Row[tuple[Any, ...]]: ...

    @overload
    @classmethod
    async def unique_one(cls, scalar: bool) -> Self | Row[tuple[Any, ...]]: ...

    @classmethod
    async def unique_one(cls, scalar: bool = True):
        """Fetches one unique row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> user = await User.where(name='John Doe').unique_one()
        >>> user
        # <User 1>
        >>> user = await User.where(name='John Doe').unique_one(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await User.where(name='Unknown').unique_one()
        # Traceback (most recent call last):
        #     ...
        # NoResultFound: 'No result found.'

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls.get_async_query()
        return await async_query.unique_one(scalar)

    @overload
    @classmethod
    async def unique_one_or_none(cls) -> Self | None: ...

    @overload
    @classmethod
    async def unique_one_or_none(cls, scalar: Literal[True]) -> Self | None: ...

    @overload
    @classmethod
    async def unique_one_or_none(cls, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def unique_one_or_none(cls, scalar: bool) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def unique_one_or_none(cls, scalar: bool = True):
        """Fetches one unique row or `None` if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> user = await User.where(name='John Doe').unique_one_or_none()
        >>> user
        # <User 1>
        >>> user = await User.where(name='John Doe').unique_one_or_none(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await User.where(name='Unknown').unique_one_or_none()
        >>> user
        # None

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls.get_async_query()
        return await async_query.unique_one_or_none(scalar)

    @overload
    @classmethod
    async def unique_all(cls) -> Sequence[Self]: ...

    @overload
    @classmethod
    async def unique_all(cls, scalars: Literal[True]) -> Sequence[Self]: ...

    @overload
    @classmethod
    async def unique_all(cls, scalars: Literal[False]) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    @classmethod
    async def unique_all(cls, scalars: bool) -> Sequence[Self] | Sequence[Row[tuple[Any, ...]]]: ...

    @classmethod
    async def unique_all(cls, scalars: bool = True):
        """Fetches all unique rows.

        If `scalars` is `True`, returns scalar values.

        Example:
        >>> users = await User.unique_all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.unique_all(scalars=False)
        >>> users
        # [(<User 1>,), (<User 2>,), ...]
        """

        async_query = cls.get_async_query()
        return await async_query.unique_all(scalars)

    @classmethod
    async def unique_count(cls) -> int:
        """Fetches the number of unique rows.

        Example:
        >>> count = await User.unique_count()
        >>> count
        # 34
        """

        async_query = cls.get_async_query()
        return await async_query.unique_count()

    @overload
    @classmethod
    def select(cls) -> AsyncQuery[Self]: ...

    @overload
    @classmethod
    def select(cls, *entities: _ColumnsClauseArgument[Any]) -> AsyncQuery: ...

    @classmethod
    def select(cls, *entities: _ColumnsClauseArgument[Any]):
        """Replaces the columns clause with the given entities.

        The existing set of FROMs are maintained, including those
        implied by the current columns clause.

        Example:
        >>> async_query = User.order_by('-created_at')
        >>> async_query
        # SELECT users.id, users.username, users.name, ... FROM users ORDER BY users.created_at DESC
        >>> async_query.select(User.name, User.age)
        >>> async_query
        # SELECT users.name, users.age FROM users ORDER BY users.created_at DESC
        """

        async_query = cls.get_async_query()
        return async_query.select(*entities)

    @classmethod
    def options(cls, *args: ExecutableOption):
        """Applies the given list of mapper options.

        Quoting from https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading:

            When including `joinedload()` in reference to a one-to-many or
            many-to-many collection, the `Result.unique()` method or related
            (i.e. `unique_all()`) must be applied to the returned result, which
            will make the incoming rows unique by primary key that otherwise are
            multiplied out by the join.
            SQLAlchemy will raise an error if this is not present.

            This is not automatic in modern SQLAlchemy, as it changes the behavior
            of the result set to return fewer ORM objects than the statement would
            normally return in terms of number of rows. Therefore SQLAlchemy keeps
            the use of Result.unique() explicit, so there is no ambiguity that the
            returned objects are made unique on primary key.

            To learn more about options, see
            https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.options

        Example 1:
        >>> users = await User.options(joinedload(User.posts)).unique()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users[0].posts
        # [<Post 1>, <Post 2>, ...]

        Example 2:
        >>> user = await User.options(joinedload(User.posts)).first()
        >>> user
        # <User 1>
        >>> users.posts
        # [<Post 1>, <Post 2>, ...]

        Example 3:
        >>> users = await User.options(subqueryload(User.posts)).all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users[0].posts
        # [<Post 1>, <Post 2>, ...]

        Example 4:
        >>> users = await User.options(joinedload(User.posts)).all()
        # Traceback (most recent call last):
        #     ...
        # InvalidRequestError: 'The unique() method must be invoked...'
        """

        async_query = cls.get_async_query()
        return async_query.options(*args)

    @classmethod
    def where(cls, *criteria: _ColumnExpressionArgument[bool], **filters: Any):
        """Applies one or more WHERE criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Example using Django-like syntax:
        >>> users = await User.where(name__like='%John%').all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.where(name__like='%John%', age=30).all()
        >>> users
        # [<User 2>]

        Example using SQLAlchemy syntax:
        >>> users = await User.where(User.name == 'John Doe').all()
        >>> users
        # [<User 2>]

        Example using both:
        >>> users = await User.where(User.age == 30, name__like='%John%').all()
        >>> users
        # [<User 2>]
        """

        async_query = cls.get_async_query()
        return async_query.where(*criteria, **filters)

    @classmethod
    def filter(cls, *criteria: _ColumnExpressionArgument[bool], **filters: Any):
        """Synonym for `where()`."""

        return cls.where(*criteria, **filters)

    @classmethod
    def find(cls, *criteria: _ColumnExpressionArgument[bool], **filters: Any):
        """Synonym for `where()`."""

        return cls.where(*criteria, **filters)

    @classmethod
    def search(
        cls,
        search_term: str,
        columns: Sequence[str | InstrumentedAttribute] | None = None,
    ):
        """Applies a search filter to the query.

        Searches for `search_term` in the searchable columns of the model.
        If `columns` are provided, searches only these columns.

        Parameters
        ----------
        search_term : str
            Search term.
        columns : Sequence[str | InstrumentedAttribute] | None, optional
            Columns to search in, by default None.

        Example:
        >>> users = await User.search(search_term='John').all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users[0].name
        # John Doe
        >>> users[1].name
        # Diana Johnson
        >>> users[1].username
        # Diana84
        """

        async_query = cls.get_async_query()
        return async_query.search(search_term=search_term, columns=columns)

    @classmethod
    def order_by(cls, *columns: _ColumnExpressionOrStrLabelArgument[Any]):
        """Applies one or more ORDER BY criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Example using Django-like syntax:
        >>> users = await User.order_by('-created_at').all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> posts = await Post.order_by('-rating', 'user___name').all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]

        Example using SQLAlchemy syntax:
        >>> users = await User.order_by(User.created_at.desc()).all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> posts = await Post.order_by(desc(Post.rating)).all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]
        """

        async_query = cls.get_async_query()
        return async_query.order_by(*columns)

    @classmethod
    def sort(cls, *columns: _ColumnExpressionOrStrLabelArgument[Any]):
        """Synonym for `order_by()`."""

        return cls.order_by(*columns)

    @classmethod
    def group_by(
        cls,
        *columns: _ColumnExpressionOrStrLabelArgument[Any],
        select_columns: Sequence[_ColumnsClauseArgument[Any]] | None = None,
    ):
        """Applies one or more GROUP BY criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        It is recommended to select specific columns. You can use
        the `select_columns` parameter to select specific columns.

        Example:
        >>> from sqlalchemy.sql.functions import func
        >>> columns = (User.age, func.count(User.name))
        >>> async_query = User.group_by(User.age, select_columns=columns)
        >>> rows = await async_query.all(scalars=False)
        # [(30, 2), (32, 1), ...]

        You can also call `select()` before calling `group_by()`:
        >>> from sqlalchemy.sql import text
        >>> async_query = Post.select(Post.rating, text('users_1.name'), func.count(Post.title))
        >>> async_query = async_query.group_by('rating', 'user___name')
        >>> rows = async_query.all(scalars=False)
        >>> rows
        # [(4, 'John Doe', 1), (5, 'Jane Doe', 1), ...]
        """

        async_query = cls.get_async_query()
        return async_query.group_by(*columns, select_columns=select_columns)

    @classmethod
    def offset(cls, offset: int):
        """Applies one OFFSET criteria to the query.

        Parameters
        ----------
        offset : int
            Offset.

        Example:
        >>> users = await User.offset(10).all()
        >>> users
        # [<User 11>, <User 12>, ...]

        Raises
        ------
        ValueError
            If offset is negative.
        """

        async_query = cls.get_async_query()
        return async_query.offset(offset)

    @classmethod
    def skip(cls, skip: int):
        """Synonym for `offset()`."""

        return cls.offset(skip)

    @classmethod
    def limit(cls, limit: int):
        """Applies one LIMIT criteria to the query.

        Parameters
        ----------
        limit : int
            Limit.

        Example:
        >>> users = await User.limit(2).all()
        >>> users
        # [<User 1>, <User 2>]

        Raises
        ------
        ValueError
            If limit is negative.
        """

        async_query = cls.get_async_query()
        return async_query.limit(limit)

    @classmethod
    def take(cls, take: int):
        """Synonym for `limit()`."""

        return cls.limit(take)

    @classmethod
    def top(cls, top: int):
        """Synonym for `limit()`."""

        return cls.limit(top)

    @classmethod
    def join(cls, *paths: QueryableAttribute | tuple[QueryableAttribute, bool]):
        """Joined eager loading using LEFT OUTER JOIN.

        When a tuple is passed, the second element must be boolean, and
        if `True`, the join is INNER JOIN, otherwise LEFT OUTER JOIN.

        NOTE: Only direct relationships can be loaded.

        Example:
        >>> comment = await Comment.join(Comment.user, (Comment.post, True)).first()
        >>> comment
        # <Comment 1>
        >>> comment.user # LEFT OUTER JOIN
        # <User 1>
        >>> comment.post # INNER JOIN
        # <Post 1>

        Parameters
        ----------
        paths : *QueryableAttribute | tuple[QueryableAttribute, bool]
            Paths to eager load.

        Raises
        ------
        ValueError
            If the second element of tuple is not boolean.
        """

        async_query = cls.get_async_query()
        return async_query.join(*paths, model=cls)

    @classmethod
    def with_subquery(cls, *paths: QueryableAttribute | tuple[QueryableAttribute, bool]):
        """Subqueryload or Selectinload eager loading.

        Emits a second `SELECT` statement (Subqueryload) for each relationship
        to be loaded, across all result objects at once.

        When a tuple is passed, the second element must be boolean.
        If it is `True`, the eager loading strategy is `SELECT IN` (Selectinload),
        otherwise `SELECT JOIN` (Subqueryload).

        ### IMPORTANT
        A query which makes use of `subqueryload()` in conjunction with a limiting
        modifier such as `Query.limit()` or `Query.offset()` should always include
        `Query.order_by()` against unique column(s) such as the primary key,
        so that the additional queries emitted by `subqueryload()` include the same
        ordering as used by the parent query. Without it, there is a chance that
        the inner query could return the wrong rows, as specified in
        https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering

        ```python
            # incorrect, no ORDER BY
            User.options(subqueryload(User.addresses)).first()

            # incorrect if User.name is not unique
            User.options(subqueryload(User.addresses)).order_by(User.name).first()

            # correct
            User.options(subqueryload(User.addresses)).order_by(
                User.name, User.id
            ).first()
        ```

        Example:
        >>> users = await User.with_subquery(User.posts, (User.comments, True)).all()
        >>> users[0]
        # <User 1>
        >>> users[0].posts  # Loaded in a separate query using SELECT JOIN
        # [<Post 1>, <Post 2>, ...]
        >>> users[0].posts[0].comments  # Loaded in a separate query using SELECT IN
        # [<Comment 1>, <Comment 2>, ...]

        Example using a limiting modifier:
        >>> users = await User.with_subquery(User.posts, (User.comments, True))
        ... .limit(1)  # Limiting modifier
        ... .sort('id')  # Sorting modifier (Important!!!)
        ... .all()
        >>> users[0]
        # <User 1>
        >>> users[0].posts  # Loaded in a separate query using SELECT JOIN
        # [<Post 1>, <Post 2>, ...]
        >>> users[0].posts[0].comments  # Loaded in a separate query using SELECT IN
        # [<Comment 1>, <Comment 2>, ...]

        Example using `first()`:
        >>> user = await User.with_subquery(User.posts, (User.comments, True))
        ... .first()  # No recommended because it calls `limit(1)`
        ...           # and does not sort by any primary key.
        ...           # Use `limit(1).sort('id').first()` instead:
        >>> user = await User.with_subquery(User.posts, (User.comments, True))
        ... .limit(1)
        ... .sort('id')  # Sorting modifier (This is the correct way)
        ... .first()
        >>> user
        # <User 1>
        >>> user.posts  # Loaded in a separate query using SELECT JOIN
        # [<Post 1>, <Post 2>, ...]
        >>> user.posts[0].comments  # Loaded in a separate query using SELECT IN
        # [<Comment 1>, <Comment 2>, ...]

        To get more information about `SELECT IN` and `SELECT JOIN` strategies,
        see https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html

        Parameters
        ----------
        paths : *List[QueryableAttribute | tuple[QueryableAttribute, bool]]
            Paths to eager load.
        """

        async_query = cls.get_async_query()
        return async_query.with_subquery(*paths, model=cls)

    @classmethod
    def with_schema(
        cls, schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
    ):
        """Joined, subqueryload and selectinload eager loading.

        Useful for complex cases where you need to load
        nested relationships in separate queries.

        Example:
        >>> from sqlactive import JOINED, SUBQUERY
        >>> schema = {
        ...     User.posts: JOINED,  # joinedload user
        ...     User.comments: (SUBQUERY, { # load comments in separate query
        ...         Comment.user: JOINED  # but, in this separate query, join user
        ...     })
        ... }
        >>> user = await User.with_schema(schema).first()
        >>> user
        # <User 1>
        >>> user.posts
        # [<Post 1>, <Post 2>, ...]
        >>> user.posts[0].comments
        # [<Comment 1>, <Comment 2>, ...]
        >>> user.posts[0].comments[0].user
        # <User 1>

        Parameters
        ----------
        schema : dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
            Schema for the eager loading.
        """

        async_query = cls.get_async_query()
        return async_query.with_schema(schema)

    @classmethod
    def smart_query(
        cls,
        criteria: Sequence[_ColumnExpressionArgument[bool]] | None = None,
        filters: (
            dict[str, Any] | dict[OperatorType, Any] | list[dict[str, Any]] | list[dict[OperatorType, Any]] | None
        ) = None,
        sort_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
        sort_attrs: Sequence[str] | None = None,
        group_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
        group_attrs: Sequence[str] | None = None,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
    ):
        smart_query = super().smart_query(
            query=cls.query,
            criteria=criteria,
            filters=filters,
            sort_columns=sort_columns,
            sort_attrs=sort_attrs,
            group_columns=group_columns,
            group_attrs=group_attrs,
            schema=schema,
        )
        return cls.get_async_query(smart_query)

    @classmethod
    def get_async_query(cls, query: Select[tuple[Any, ...]] | None = None):
        """Returns an `AsyncQuery` instance with
        the provided `sqlalchemy.sql.Select` instance.

        If no `sqlalchemy.sql.Select` instance is provided,
        it uses the `query` property of the model.

        Parameters
        ----------
        query : Select[tuple[Any, ...]] | None, optional
            SQLAlchemy query, by default None.
        """

        if query is None:
            return AsyncQuery[cls](cls.query)
        return AsyncQuery[cls](query)

    @classmethod
    @deprecated(
        'Deprecated since version 0.2: Use `primary_key_name` property instead.',
        stacklevel=2,
    )
    def get_primary_key_name(cls) -> str:
        """Gets the primary key name of the model.

        .. deprecated:: 0.2.0
            This method will be removed in SQLActive 1.0.0.
            Use `primary_key_name` property instead.

        .. warning::
            This method can only be used if the model has a single primary key.
            If the model has a composite primary key, an ``CompositePrimaryKeyError`` is raised.

        Returns
        -------
        str
            The name of the primary key.

        Raises
        ------
        CompositePrimaryKeyError
            If the model has a composite primary key.
        """
        return cls.primary_key_name

    @classmethod
    def set_session(cls, session: async_scoped_session[AsyncSession]) -> None:
        super().set_session(session)
        AsyncQuery.set_session(session)
