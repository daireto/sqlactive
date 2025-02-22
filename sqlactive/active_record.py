"""This module defines ``ActiveRecordMixin`` class."""

from collections.abc import Sequence
from typing import Any, Literal, overload

from sqlalchemy.engine import Result, Row, ScalarResult
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import Select, select
from sqlalchemy.sql._typing import _ColumnsClauseArgument
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.operators import OperatorType
from typing_extensions import Self, deprecated

from .async_query import AsyncQuery
from .exceptions import ModelAttributeError, NoSettableError
from .session import SessionMixin
from .smart_query import ColumnExpressionOrStrLabelArgument, SmartQueryMixin
from .utils import classproperty


class ActiveRecordMixin(SessionMixin, SmartQueryMixin):
    """Mixin for Active Record style models.

    Provides a set of ActiveRecord-like helper methods for SQLAlchemy
    models, allowing for more intuitive and chainable database
    operations with async/await support.

    Define a base model class that inherits from this class:
    >>> from sqlalchemy import String
    >>> from sqlalchemy import Mapped, mapped_column
    >>> from sqlactive import ActiveRecordMixin
    >>> class BaseModel(ActiveRecordMixin):
    ...     __abstract__ = True

    You can also make your base inherit from the
    ``ActiveRecordBaseModel`` class which is a combination of
    ``ActiveRecordMixin``, ``SerializationMixin`` and
    ``TimestampMixin``. This is the recommended way to use this library:
    >>> from sqlactive import ActiveRecordBaseModel
    >>> class BaseModel(ActiveRecordBaseModel):
    ...     __abstract__ = True

    Define your model classes that inherit from ``BaseModel``:
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
        All relations used in filtering/sorting/grouping should be
        explicitly set, not just being a ``backref``. This is because
        SQLActive does not know the relation direction and cannot infer
        it. So, when defining a relationship like::

            class User(BaseModel):
                # ...
                posts: Mapped[list['Post']] = relationship(
                    back_populates='user'
                )

        It is required to define the reverse relationship::

            class Post(BaseModel):
                # ...
                user: Mapped['User'] = relationship(
                    back_populates='posts'
                )

    Visit the `API Reference <https://daireto.github.io/sqlactive/api/active-record-mixin/#api-reference>`_
    for the full list of available methods.
    """

    __abstract__ = True

    @classproperty
    def query(cls) -> Select[tuple[Self]]:
        """Returns a new ``sqlalchemy.sql.Select`` instance
        for the model.

        This is a shortcut for ``select(cls)``.

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
        """Fills the object with values from ``kwargs``
        without saving to the database.

        Returns
        -------
        Self
            The instance itself for method chaining.

        Raises
        ------
        ModelAttributeError
            If attribute does not exist in the model.
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
                raise ModelAttributeError(name, self.__class__.__name__)

            if name in self.settable_attributes:
                setattr(self, name, kwargs[name])
            else:
                raise NoSettableError(name, self.__class__.__name__)

        return self

    async def save(self) -> Self:
        """Saves the current row.

        .. note::
            All database errors will trigger a rollback and be raised.

        Returns
        -------
        Self
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

        This is the same as calling ``self.fill(**kwargs).save()``.

        Returns
        -------
        Self
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
            This is not a soft delete method. It will permanently delete
            the row from the database. So, if you want to keep the row
            in the database, you can implement a custom soft delete
            method, i.e. using ``save()`` method to update the row with a
            flag indicating if the row is deleted or not (i.e. a boolean
            ``is_deleted`` column).

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
        """Synonym for ``delete()``."""
        return await self.delete()

    @classmethod
    async def insert(cls, **kwargs) -> Self:
        """Inserts a new row and returns the saved instance.

        Returns
        -------
        Self
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
        """Synonym for ``insert()``."""
        return await cls.insert(**kwargs)

    @classmethod
    async def save_all(
        cls, rows: Sequence[Self], refresh: bool = False
    ) -> None:
        """Saves multiple rows in a single transaction.

        When using this method to update existing rows, instances are
        not refreshed after commit by default. Accessing the attributes
        of the updated rows without refreshing them after commit will
        raise an ``sqlalchemy.orm.exc.DetachedInstanceError``.

        To access the attributes of updated rows, the ``refresh`` flag
        must be set to ``True`` in order to refresh them after commit.

        .. warning::
            Refreshing multiple instances may be expensive,
            which may lead to a higher latency due to additional
            database queries.

        .. note::
            When inserting new rows, refreshing the instances after
            commit is not necessary. The instances are already available
            after commit, but you still can use the ``refresh`` flag to
            refresh them if needed.

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
        DetachedInstanceError: Instance User(id=at)0x...> is not bound to a Session...
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
    async def insert_all(
        cls, rows: Sequence[Self], refresh: bool = False
    ) -> None:
        """Inserts multiple rows in a single transaction.

        This is mostly a shortcut for ``save_all()``
        when inserting new rows.

        .. note::
            When inserting new rows, refreshing the instances after
            commit is not necessary. The instances are already available
            after commit, but you still can use the ``refresh`` flag to
            refresh them if needed.

        See the ``save_all()`` method for more details.
        """
        return await cls.save_all(rows, refresh)

    @classmethod
    async def update_all(
        cls, rows: Sequence[Self], refresh: bool = False
    ) -> None:
        """Updates multiple rows in a single transaction.

        This is mostly a shortcut for ``save_all()``
        when updating existing rows.

        If you are planning to access the attributes of the updated
        instances after commit, you must set the ``refresh`` flag to
        ``True`` in order to refresh them. Accessing the attributes of
        the updated instances without refreshing them after commit
        will raise an ``sqlalchemy.orm.exc.DetachedInstanceError``.

        .. warning::
            Refreshing multiple instances may be expensive,
            which may lead to a higher latency due to additional
            database queries.

        See the ``save_all()`` method for more details.
        """
        return await cls.save_all(rows, refresh)

    @classmethod
    async def delete_all(cls, rows: Sequence[Self]) -> None:
        """Deletes multiple rows in a single transaction.

        .. warning::
            This is not a soft delete method. It will permanently delete
            the row from the database. So, if you want to keep the row
            in the database, you can implement a custom soft delete
            method, i.e. using ``save()`` method to update the row with a
            flag indicating if the row is deleted or not (i.e. a boolean
            ``is_deleted`` column).

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

        This method can only be used if the model has a single primary
        key. Otherwise, it will raise a ``CompositePrimaryKeyError``
        exception.

        .. warning::
            This is not a soft delete method. It will permanently delete
            the row from the database. So, if you want to keep the row
            in the database, you can implement a custom soft delete
            method, i.e. using ``save()`` method to update the row with a
            flag indicating if the row is deleted or not (i.e. a boolean
            ``is_deleted`` column).

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
                query = cls.smart_query(
                    filters={f'{cls.primary_key_name}__in': ids}
                ).query
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
        join: (
            Sequence[
                InstrumentedAttribute[Any]
                | tuple[InstrumentedAttribute[Any], bool]
            ]
            | None
        ) = None,
        subquery: (
            Sequence[
                InstrumentedAttribute[Any]
                | tuple[InstrumentedAttribute[Any], bool]
            ]
            | None
        ) = None,
        schema: (
            dict[
                InstrumentedAttribute[Any],
                str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
            ]
            | None
        ) = None,
    ) -> Self | None:
        """Fetches a row by primary key or ``None`` if no result is found.

        If multiple results are found, it will raise a
        ``sqlalchemy.exc.MultipleResultsFound`` exception.

        Parameters
        ----------
        pk : object
            Primary key value. It can also be a dict of composite
            primary key values.
        join : Sequence[InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]], optional
            Paths to join eager load, by default None.
            IMPORTANT: See the documentation of ``join()`` method for
            details.
        subquery : Sequence[InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]], optional
            Paths to subquery eager load, by default None.
            IMPORTANT: See the documentation of ``with_subquery()`` method
            for details.
        schema : dict[InstrumentedAttribute[Any], str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict], optional
            Schema for the eager loading, by default None.
            IMPORTANT: See the documentation of ``with_schema()`` method
            for details.

        Returns
        -------
        Self
            The instance for method chaining if found.
        None
            If no result is found.

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.

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
        >>> user = await User.get(1)
        >>> user
        User(id=1)
        >>> user = await User.get(100)  # does not exist
        >>> user
        None
        """
        if isinstance(pk, dict):
            criteria = pk
        else:
            criteria = {cls.primary_key_name: pk}

        async_query = cls.get_async_query()
        async_query.where(**criteria)
        if join:
            async_query.join(*join)
        if subquery:
            async_query.with_subquery(*subquery)
        if schema:
            async_query.with_schema(schema)
        return await async_query.unique_one_or_none()

    @classmethod
    async def get_or_fail(
        cls,
        pk: object,
        join: (
            Sequence[
                InstrumentedAttribute[Any]
                | tuple[InstrumentedAttribute[Any], bool]
            ]
            | None
        ) = None,
        subquery: (
            Sequence[
                InstrumentedAttribute[Any]
                | tuple[InstrumentedAttribute[Any], bool]
            ]
            | None
        ) = None,
        schema: (
            dict[
                InstrumentedAttribute[Any],
                str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
            ]
            | None
        ) = None,
    ) -> Self:
        """Fetches a row by primary key or raises a
        ``sqlalchemy.exc.NoResultFound`` exception
        if no result is found.

        If multiple results are found, it will raise a
        ``sqlalchemy.exc.MultipleResultsFound`` exception.

        Parameters
        ----------
        pk : object
            Primary key value. It can also be a dict of composite
            primary key values.
        join : Sequence[InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]], optional
            Paths to join eager load, by default None.
            IMPORTANT: See the documentation of ``join()`` method for
            details.
        subquery : Sequence[InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]], optional
            Paths to subquery eager load, by default None.
            IMPORTANT: See the documentation of ``with_subquery()`` method
            for details.
        schema : dict[InstrumentedAttribute[Any], str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict], optional
            Schema for the eager loading, by default None.
            IMPORTANT: See the documentation of ``with_schema()`` method
            for details.

        Returns
        -------
        Self
            The instance for method chaining.

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.

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
        >>> user = await User.get_or_fail(1)
        >>> user
        User(id=1)
        >>> user = await User.get_or_fail(100)  # does not exist
        Traceback (most recent call last):
            ...
        sqlalchemy.exc.NoResultFound: User with id '100' was not found
        """
        cursor = await cls.get(pk, join=join, subquery=subquery, schema=schema)
        if cursor:
            return cursor
        else:
            raise NoResultFound(f"{cls.__name__} with id '{pk}' was not found")

    @classmethod
    async def scalars(cls) -> ScalarResult[Self]:
        """Returns a ``sqlalchemy.engine.ScalarResult`` instance
        containing all results.

        Returns
        -------
        ScalarResult[Self]
            Result instance containing all scalars.

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
        >>> result = await User.scalars()
        >>> result
        <sqlalchemy.engine.result.ScalarResult object at 0x...>
        >>> users = result.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> result = await User.where(name='John Doe').scalars()
        >>> users = result.all()
        >>> users
        [User(id=2)]
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
    async def first(
        cls, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def first(
        cls, scalar: bool
    ) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def first(cls, scalar: bool = True):
        """Fetches the first row or ``None`` if no results are found.

        If ``scalar`` is ``True``, returns a scalar value (default).

        Parameters
        ----------
        scalar : bool, optional
            If ``True``, returns a scalar value (default).
            If ``False``, returns a row.

        Returns
        -------
        Self
            The instance for method chaining if found.
        Row[tuple[Any, ...]]
            The row if found.
        None
            If no result is found.

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
        >>> user = await User.first()
        >>> user
        User(id=1)
        >>> user = await User.first(scalar=False)
        >>> user
        (User(id=1),)

        Selecting specific columns:
        >>> user = await User.select(User.name, User.age).first()
        >>> user
        'Bob Williams'
        >>> user = await User.select(User.name, User.age)
        ...                  .first(scalar=False)
        >>> user
        ('Bob Williams', 30)
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
        """Fetches one row or raises a ``sqlalchemy.exc.NoResultFound``
        exception if no results are found.

        If multiple results are found, it will raise a
        ``sqlalchemy.exc.MultipleResultsFound`` exception.

        If ``scalar`` is ``True``, returns a scalar value (default).

        Parameters
        ----------
        scalar : bool, optional
            If ``True``, returns a scalar value (default).
            If ``False``, returns a row.

        Returns
        -------
        Self
            The instance for method chaining if found.
        Row[tuple[Any, ...]]
            The row if found.

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.

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
        >>> user = await User.where(name='John Doe').one()
        >>> user
        User(id=1)
        >>> user = await User.where(name='John Doe').one(scalar=False)
        >>> user
        (User(id=1),)
        >>> user = await User.where(name='Unknown').one()
        Traceback (most recent call last):
            ...
        sqlalchemy.exc.NoResultFound: No row was found when one was required
        >>> user = await User.one()
        Traceback (most recent call last):
            ...
        sqlalchemy.exc.MultipleResultsFound: Multiple rows were found when one was required

        Selecting specific columns:
        >>> user = await User.where(name='John Doe')
        ...                  .select(User.name, User.age)
        ...                  .one()
        >>> user
        'John Doe'
        >>> user = await User.where(name='John Doe')
        ...                  .select(User.name, User.age)
        ...                  .one(scalar=False)
        >>> user
        ('John Doe', 30)
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
    async def one_or_none(
        cls, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def one_or_none(
        cls, scalar: bool
    ) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def one_or_none(cls, scalar: bool = True):
        """Fetches one row or ``None`` if no results are found.

        If multiple results are found, it will raise a
        ``sqlalchemy.exc.MultipleResultsFound`` exception.

        If ``scalar`` is ``True``, returns a scalar value (default).

        Parameters
        ----------
        scalar : bool, optional
            If ``True``, returns a scalar value (default).
            If ``False``, returns a row.

        Returns
        -------
        Self
            The instance for method chaining if found.
        Row[tuple[Any, ...]]
            The row if found.
        None
            If no result is found.

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.

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
        >>> user = await User.where(name='John Doe').one_or_none()
        >>> user
        User(id=1)
        >>> user = await User.where(name='John Doe')
        ...                  .one_or_none(scalar=False)
        >>> user
        (User(id=1),)
        >>> user = await User.where(name='Unknown').one_or_none()
        >>> user
        None
        >>> user = await User.one_or_none()
        Traceback (most recent call last):
            ...
        sqlalchemy.exc.MultipleResultsFound: Multiple rows were found when one was required

        Selecting specific columns:
        >>> user = await User.where(name='John Doe')
        ...                  .select(User.name, User.age)
        ...                  .one_or_none()
        >>> user
        'John Doe'
        >>> user = await User.where(name='John Doe')
        ...                  .select(User.name, User.age)
        ...                  .one_or_none(scalar=False)
        >>> user
        ('John Doe', 30)
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
    async def all(
        cls, scalars: Literal[False]
    ) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    @classmethod
    async def all(
        cls, scalars: bool
    ) -> Sequence[Self] | Sequence[Row[tuple[Any, ...]]]: ...

    @classmethod
    async def all(cls, scalars: bool = True):
        """Fetches all rows.

        If ``scalars`` is ``True``, returns scalar values (default).

        Parameters
        ----------
        scalars : bool, optional
            If ``True``, returns scalar values (default).
            If ``False``, returns rows.

        Returns
        -------
        Sequence[Self]
            Instances (scalars).
        Sequence[Row[tuple[Any, ...]]]
            Rows.

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
        >>> users = await User.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await User.all(scalars=False)
        >>> users
        [(User(id=1),), (User(id=2),), ...]

        Selecting specific columns:
        >>> users = await User.select(User.name, User.age).all()
        >>> users
        ['John Doe', 'Jane Doe', ...]
        >>> users = await User.select(User.name, User.age)
        ...                   .all(scalars=False)
        >>> users
        [('John Doe', 30), ('Jane Doe', 32), ...]
        """
        async_query = cls.get_async_query()
        return await async_query.all(scalars)

    @classmethod
    async def count(cls) -> int:
        """Fetches the number of rows.

        Returns
        -------
        int
            The number of rows.

        Examples
        --------
        Assume a model ``User`` with 34 rows in the database:
        >>> count = await User.count()
        >>> count
        34
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
    async def unique(
        cls, scalars: Literal[False]
    ) -> Result[tuple[Any, ...]]: ...

    @overload
    @classmethod
    async def unique(
        cls, scalars: bool
    ) -> ScalarResult[Self] | Result[tuple[Any, ...]]: ...

    @classmethod
    async def unique(cls, scalars: bool = True):
        """Similar to ``scalars()`` but applies unique filtering
        to the objects returned in the result instance.

        If ``scalars`` is ``False``, returns
        a ``sqlalchemy.engine.Result`` instance instead of
        a ``sqlalchemy.engine.ScalarResult`` instance.

        .. note::
            This method is different from ``distinct()`` in that it
            applies unique filtering to the objects returned in the
            result instance. If you need to apply unique filtering on
            the query (a DISTINCT clause), use ``distinct()`` instead.

        Parameters
        ----------
        scalars : bool, optional
            If ``True``, returns a ``sqlalchemy.engine.ScalarResult``
            instance (default). If ``False``, returns a
            ``sqlalchemy.engine.Result`` instance.

        Returns
        -------
        ScalarResult[Self]
            Result instance containing all scalars.
        Result[tuple[Any, ...]]
            Result instance containing all rows.

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
        >>> users = await User.unique()
        >>> users
        <sqlalchemy.engine.result.ScalarResult object at 0x...>
        >>> users = await User.unique(scalars=False)
        >>> users
        <sqlalchemy.engine.result.Result object at 0x...>
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
    async def unique_first(
        cls, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def unique_first(
        cls, scalar: bool
    ) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def unique_first(cls, scalar: bool = True):
        """Similar to ``first()`` but applies unique filtering to the
        objects returned by either ``sqlalchemy.engine.ScalarResult``
        or ``sqlalchemy.engine.Result`` depending on the value
        of ``scalar``.

        .. note::
            This method is different from ``distinct()`` in that it
            applies unique filtering to the objects returned in the
            result instance. If you need to apply unique filtering on
            the query (a DISTINCT clause), use ``distinct()`` instead.

        See ``unique()`` and ``first()`` for more details.
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
    async def unique_one(
        cls, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]]: ...

    @overload
    @classmethod
    async def unique_one(cls, scalar: bool) -> Self | Row[tuple[Any, ...]]: ...

    @classmethod
    async def unique_one(cls, scalar: bool = True):
        """Similar to ``one()`` but applies unique filtering to the
        objects returned by either ``sqlalchemy.engine.ScalarResult``
        or ``sqlalchemy.engine.Result`` depending on the value
        of ``scalar``.

        .. note::
            This method is different from ``distinct()`` in that it
            applies unique filtering to the objects returned in the
            result instance. If you need to apply unique filtering on
            the query (a DISTINCT clause), use ``distinct()`` instead.

        See ``unique()`` and ``one()`` for more details.
        """
        async_query = cls.get_async_query()
        return await async_query.unique_one(scalar)

    @overload
    @classmethod
    async def unique_one_or_none(cls) -> Self | None: ...

    @overload
    @classmethod
    async def unique_one_or_none(
        cls, scalar: Literal[True]
    ) -> Self | None: ...

    @overload
    @classmethod
    async def unique_one_or_none(
        cls, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    @classmethod
    async def unique_one_or_none(
        cls, scalar: bool
    ) -> Self | Row[tuple[Any, ...]] | None: ...

    @classmethod
    async def unique_one_or_none(cls, scalar: bool = True):
        """Similar to ``one_or_none()`` but applies
        unique filtering to the objects returned by either
        ``sqlalchemy.engine.ScalarResult`` or
        ``sqlalchemy.engine.Result`` depending on the value
        of ``scalar``.

        .. note::
            This method is different from ``distinct()`` in that it
            applies unique filtering to the objects returned in the
            result instance. If you need to apply unique filtering on
            the query (a DISTINCT clause), use ``distinct()`` instead.

        See ``unique()`` and ``one_or_none()`` for more details.
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
    async def unique_all(
        cls, scalars: Literal[False]
    ) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    @classmethod
    async def unique_all(
        cls, scalars: bool
    ) -> Sequence[Self] | Sequence[Row[tuple[Any, ...]]]: ...

    @classmethod
    async def unique_all(cls, scalars: bool = True):
        """Similar to ``all()`` but applies unique filtering to the
        objects returned by either ``sqlalchemy.engine.ScalarResult``
        or ``sqlalchemy.engine.Result`` depending on the value
        of ``scalars``.

        .. note::
            This method is different from ``distinct()`` in that it
            applies unique filtering to the objects returned in the
            result instance. If you need to apply unique filtering on
            the query (a DISTINCT clause), use ``distinct()`` instead.

        See ``unique()`` and ``all()`` for more details.
        """
        async_query = cls.get_async_query()
        return await async_query.unique_all(scalars)

    @classmethod
    async def unique_count(cls) -> int:
        """Similar to ``count()`` but applies unique filtering to the
        objects returned by ``sqlalchemy.engine.ScalarResult``.

        .. note::
            This method is different from ``distinct()`` in that it
            applies unique filtering to the objects returned in the
            result instance. If you need to apply unique filtering on
            the query (a DISTINCT clause), use ``distinct()`` instead.

        See ``unique()`` and ``count()`` for more details.
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

        Parameters
        ----------
        *entities : _ColumnsClauseArgument[Any]
            The entities to select.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

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
        >>> async_query = User.order_by('-created_at')
        >>> async_query
        'SELECT users.id, users.username, users.name, ... FROM users ORDER BY users.created_at DESC'
        >>> async_query.select(User.name, User.age)
        >>> async_query
        'SELECT users.name, users.age FROM users ORDER BY users.created_at DESC'
        """
        async_query = cls.get_async_query()
        return async_query.select(*entities)

    @classmethod
    def distinct(cls) -> AsyncQuery[Self]:
        """Applies DISTINCT to the SELECT statement overall.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

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
        >>> User.query
        'SELECT users.id, users.username, users.name, ... FROM users'
        >>> User.distinct()
        'SELECT DISTINCT users.id, users.username, users.name, ... FROM users'
        """
        async_query = cls.get_async_query()
        return async_query.distinct()

    @classmethod
    def options(cls, *args: ExecutableOption) -> AsyncQuery[Self]:
        """Applies the given list of mapper options.

        .. warning::
            Quoting from the `joined eager loading docs <https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading>`_:

                When including ``joinedload()`` in reference
                to a one-to-many or many-to-many collection,
                the ``Result.unique()`` method must be applied
                to the returned result, which will uniquify the
                incoming rows by primary key that otherwise are
                multiplied out by the join. The ORM will raise
                an error if this is not present.

                This is not automatic in modern SQLAlchemy, as it
                changes the behavior of the result set to return
                fewer ORM objects than the statement would normally
                return in terms of number of rows. Therefore SQLAlchemy
                keeps the use of ``Result.unique()`` explicit,
                so there is no ambiguity that the returned objects
                are being uniquified on primary key.

            This is, when fetching many rows and using joined eager
            loading, the ``unique()`` method or related
            (i.e. ``unique_all()``) must be called to ensure that
            the rows are unique on primary key (see the examples below).

            To learn more about options, see the
            `Query.options docs <https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.options>`_.

        Parameters
        ----------
        *args : ExecutableOption
            The options to apply.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

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

        Joined eager loading:
        >>> users = await User.options(joinedload(User.posts))
        ...                   .unique_all()  # required for joinedload()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users[0].posts
        [Post(id=1), Post(id=2), ...]
        >>> user = await User.options(joinedload(User.posts)).first()
        >>> user
        User(id=1)
        >>> users.posts
        [Post(id=1), Post(id=2), ...]

        Subquery eager loading:
        >>> users = await User.options(subqueryload(User.posts)).all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users[0].posts
        [Post(id=1), Post(id=2), ...]

        Eager loading without calling unique() before all():
        >>> users = await User.options(joinedload(User.posts)).all()
        Traceback (most recent call last):
            ...
        InvalidRequestError: The unique() method must be invoked on this Result...
        """
        async_query = cls.get_async_query()
        return async_query.options(*args)

    @classmethod
    def where(
        cls, *criteria: ColumnElement[bool], **filters: Any
    ) -> AsyncQuery[Self]:
        """Applies one or more WHERE criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Parameters
        ----------
        *criteria : ColumnElement[bool]
            SQLAlchemy style filter expressions.
        **filters : Any
            Django-style filters.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

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

        Using Django-like syntax:
        >>> users = await User.where(age__gte=18).all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await User.where(name__like='%John%', age=30).all()
        >>> users
        [User(id=2)]

        Using SQLAlchemy syntax:
        >>> users = await User.where(User.age >= 18).all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await User.where(
        ...     User.name == 'John Doe',
        ...     User.age == 30
        ... ).all()
        >>> users
        [User(id=2)]

        Using both syntaxes:
        >>> users = await User.where(
        ...     User.age == 30,
        ...     name__like='%John%'
        ... ).all()
        >>> users
        [User(id=2)]
        """
        async_query = cls.get_async_query()
        return async_query.where(*criteria, **filters)

    @classmethod
    def filter(
        cls, *criteria: ColumnElement[bool], **filters: Any
    ) -> AsyncQuery[Self]:
        """Synonym for ``where()``."""
        return cls.where(*criteria, **filters)

    @classmethod
    def find(
        cls, *criteria: ColumnElement[bool], **filters: Any
    ) -> AsyncQuery[Self]:
        """Synonym for ``where()``."""
        return cls.where(*criteria, **filters)

    @classmethod
    def search(
        cls,
        search_term: str,
        columns: Sequence[str | InstrumentedAttribute[Any]] | None = None,
    ) -> AsyncQuery[Self]:
        """Applies a search filter to the query.

        Searches for ``search_term`` in the searchable columns of
        the model. If ``columns`` are provided, searches only these
        columns.

        Parameters
        ----------
        search_term : str
            Search term.
        columns : Sequence[str | InstrumentedAttribute[Any]] | None, optional
            Columns to search in, by default None.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

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
        >>> users = await User.search(search_term='John').all()
        >>> users
        [User(id=2), User(id=6)]
        >>> users[0].name
        'John Doe'
        >>> users[0].username
        'John321'
        >>> users[1].name
        'Diana Johnson'
        >>> users[1].username
        'Diana84'

        Searching specific columns:
        >>> users = await User.search(
        ...     search_term='John',
        ...     columns=[User.name, User.username]
        ... ).all()
        >>> users
        [User(id=2), User(id=6)]
        >>> users = await User.search(
        ...     search_term='John',
        ...     columns=[User.username]  # or 'username'
        ... ).all()
        >>> users
        [User(id=2)]
        """
        async_query = cls.get_async_query()
        return async_query.search(search_term=search_term, columns=columns)

    @classmethod
    def order_by(
        cls, *columns: ColumnExpressionOrStrLabelArgument
    ) -> AsyncQuery[Self]:
        """Applies one or more ORDER BY criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Parameters
        ----------
        *columns : ColumnExpressionOrStrLabelArgument
            Django-like or SQLAlchemy sort expressions.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

        Examples
        --------
        Assume a model ``Post``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Post(ActiveRecordBaseModel):
        ...     __tablename__ = 'posts'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     title: Mapped[str] = mapped_column()
        ...     rating: Mapped[int] = mapped_column()
        ...     user_id: Mapped[int] = mapped_column(
        ...         ForeignKey('users.id')
        ...     )
        ...     user: Mapped['User'] = relationship(
        ...         back_populates='posts'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='post'
        ...     )

        Using Django-like syntax:
        >>> posts = await Post.order_by('-rating', 'user___name').all()
        >>> posts
        [Post(id=1), Post(id=4), ...]

        Using SQLAlchemy syntax:
        >>> posts = await Post.order_by(Post.rating.desc()).all()
        >>> posts
        [Post(id=1), Post(id=4), ...]

        Using both syntaxes:
        >>> posts = await Post.order_by(
        ...     Post.rating.desc(),
        ...     'user___name'
        ... ).all()
        >>> posts
        [Post(id=1), Post(id=4), ...]
        """
        async_query = cls.get_async_query()
        return async_query.order_by(*columns)

    @classmethod
    def sort(
        cls, *columns: ColumnExpressionOrStrLabelArgument
    ) -> AsyncQuery[Self]:
        """Synonym for ``order_by()``."""
        return cls.order_by(*columns)

    @classmethod
    def group_by(
        cls,
        *columns: ColumnExpressionOrStrLabelArgument,
        select_columns: Sequence[_ColumnsClauseArgument[Any]] | None = None,
    ) -> AsyncQuery[Self]:
        """Applies one or more GROUP BY criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        It is recommended to select specific columns. You can use
        the ``select_columns`` parameter to select specific columns.

        Parameters
        ----------
        *columns : ColumnExpressionOrStrLabelArgument
            Django-like or SQLAlchemy columns.
        select_columns : Sequence[_ColumnsClauseArgument[Any]] | None, optional
            Columns to be selected (recommended), by default None.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

        Examples
        --------
        Assume two models ``User`` and ``Post``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        >>> class Post(ActiveRecordBaseModel):
        ...     __tablename__ = 'posts'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     rating: Mapped[int] = mapped_column()
        ...     title: Mapped[str] = mapped_column()
        ...     user_id: Mapped[int] = mapped_column(
        ...         ForeignKey('users.id')
        ...     )
        ...     user: Mapped['User'] = relationship(
        ...         back_populates='posts'
        ...     )

        Usage:
        >>> from sqlalchemy.sql.functions import func
        >>> columns = (User.age, func.count(User.name))
        >>> async_query = User.group_by(
        ...     User.age, select_columns=columns
        ... )
        >>> rows = await async_query.all(scalars=False)
        [(30, 2), (32, 1), ...]

        You can also call ``select()`` before calling ``group_by()``:
        >>> from sqlalchemy.sql import text, func
        >>> async_query = Post.select(
        ...     Post.rating,
        ...     text('users_1.name'),
        ...     func.count(Post.title)
        ... )
        >>> async_query.group_by('rating', 'user___name')
        >>> rows = async_query.all(scalars=False)
        >>> rows
        [(4, 'John Doe', 1), (5, 'Jane Doe', 1), ...]
        """
        async_query = cls.get_async_query()
        return async_query.group_by(*columns, select_columns=select_columns)

    @classmethod
    def offset(cls, offset: int) -> AsyncQuery[Self]:
        """Applies one OFFSET criteria to the query.

        Parameters
        ----------
        offset : int
            Number of rows to skip.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

        Raises
        ------
        ValueError
            If ``offset`` is negative.

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
        >>> users = await User.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await User.offset(10).all()
        >>> users
        [User(id=11), User(id=12), ...]
        >>> User.offset(-1)
        Traceback (most recent call last):
            ...
        ValueError: offset must be >= 0
        """
        async_query = cls.get_async_query()
        return async_query.offset(offset)

    @classmethod
    def skip(cls, skip: int) -> AsyncQuery[Self]:
        """Synonym for ``offset()``."""
        return cls.offset(skip)

    @classmethod
    def limit(cls, limit: int) -> AsyncQuery[Self]:
        """Applies one LIMIT criteria to the query.

        Parameters
        ----------
        limit : int
            Maximum number of rows to return.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

        Raises
        ------
        ValueError
            If ``limit`` is negative.

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
        >>> users = await User.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await User.limit(2).all()
        >>> users
        [User(id=1), User(id=2)]
        >>> User.limit(-1)
        Traceback (most recent call last):
            ...
        ValueError: limit must be >= 0
        """
        async_query = cls.get_async_query()
        return async_query.limit(limit)

    @classmethod
    def take(cls, take: int) -> AsyncQuery[Self]:
        """Synonym for ``limit()``."""
        return cls.limit(take)

    @classmethod
    def top(cls, top: int) -> AsyncQuery[Self]:
        """Synonym for ``limit()``."""
        return cls.limit(top)

    @classmethod
    def join(
        cls,
        *paths: InstrumentedAttribute[Any]
        | tuple[InstrumentedAttribute[Any], bool],
    ) -> AsyncQuery[Self]:
        """Joined eager loading using LEFT OUTER JOIN.

        When a tuple is passed, the second element must be boolean, and
        if ``True``, the join is INNER JOIN, otherwise LEFT OUTER JOIN.

        .. note::
            Only direct relationships can be loaded.

        Parameters
        ----------
        paths : *InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]
            Relationship attributes to join.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

        Raises
        ------
        ValueError
            If the second element of tuple is not boolean.

        Examples
        --------
        Assume a model ``Comment``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Comment(ActiveRecordBaseModel):
        ...     __tablename__ = 'comments'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     body: Mapped[str] = mapped_column(nullable=False)
        ...     post_id: Mapped[int] = mapped_column(
        ...         ForeignKey('posts.id')
        ...     )
        ...     user_id: Mapped[int] = mapped_column(
        ...         ForeignKey('users.id')
        ...     )
        ...     post: Mapped['Post'] = relationship(
        ...         back_populates='comments'
        ...     )
        ...     user: Mapped['User'] = relationship(
        ...         back_populates='comments'
        ...     )

        Usage:
        >>> comment = await Comment.join(
        ...     Comment.user,         # LEFT OUTER JOIN
        ...     (Comment.post, True)  # True = INNER JOIN
        ... ).first()
        >>> comment
        Comment(id=1)
        >>> comment.user
        User(id=1)
        >>> comment.post
        Post(id=1)
        >>> Comment.join(
        ...     Comment.user,
        ...     (Comment.post, 'inner')  # invalid argument
        ... )
        Traceback (most recent call last):
            ...
        ValueError: expected boolean for second element of tuple, got str: 'inner'
        """
        async_query = cls.get_async_query()
        return async_query.join(*paths, model=cls)

    @classmethod
    def with_subquery(
        cls,
        *paths: InstrumentedAttribute[Any]
        | tuple[InstrumentedAttribute[Any], bool],
    ) -> AsyncQuery[Self]:
        """Subqueryload or Selectinload eager loading.

        Emits a second SELECT statement (Subqueryload) for each
        relationship to be loaded, across all result objects at once.

        When a tuple is passed, the second element must be boolean.
        If it is ``True``, the eager loading strategy is SELECT IN
        (Selectinload), otherwise SELECT JOIN (Subqueryload).

        .. warning::
            A query which makes use of ``subqueryload()`` in
            conjunction with a limiting modifier such as
            ``Query.limit()`` or ``Query.offset()`` should always
            include ``Query.order_by()`` against unique column(s)
            such as the primary key, so that the additional queries
            emitted by ``subqueryload()`` include the same ordering
            as used by the parent query. Without it, there is a chance
            that the inner query could return the wrong rows, as
            specified in `The importance of ordering <https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering>`_.

            Incorrect, LIMIT without ORDER BY::

                User.options(subqueryload(User.posts))
                    .first()

            Incorrect if User.name is not unique::

                User.options(subqueryload(User.posts))
                    .order_by(User.name)
                    .first()

            Correct::

                User.options(subqueryload(User.posts))
                    .order_by(User.name, User.id)
                    .first()

            To get more information about SELECT IN and SELECT JOIN
            strategies, see the `loading relationships docs <https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html>`_.

        .. note::
            Only direct relationships can be loaded.

        Parameters
        ----------
        paths : *InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]
            Relationship attributes to load.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

        Raises
        ------
        ValueError
            If the second element of tuple is not boolean.

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
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )

        Usage:
        >>> users = await User.with_subquery(
        ...     User.posts,            # SELECT JOIN
        ...     (User.comments, True)  # True = SELECT IN
        ... ).all()
        >>> users[0]
        User(id=1)
        >>> users[0].posts              # loaded using SELECT JOIN
        [Post(id=1), Post(id=2), ...]
        >>> users[0].posts[0].comments  # loaded using SELECT IN
        [Comment(id=1), Comment(id=2), ...]
        >>> User.with_subquery(
        ...     User.posts,
        ...     (User.comments, 'selectin')  # invalid argument
        ... )
        Traceback (most recent call last):
            ...
        ValueError: expected boolean for second element of tuple, got str: 'selectin'

        Using a limiting modifier:
        >>> user = await User.with_subquery(
        ...     User.posts,            # SELECT JOIN
        ...     (User.comments, True)  # True = SELECT IN
        ... ).sort('id')  # sorting modifier (Important!!!)
        ...  .first()     # limiting modifier
        >>> user = await User.with_subquery(
        ...     User.posts,            # SELECT JOIN
        ...     (User.comments, True)  # True = SELECT IN
        ... ).limit(1)    # limiting modifier
        ...  .sort('id')  # sorting modifier (Important!!!)
        ...  .all()[0]
        >>> user
        User(id=1)
        >>> user.posts              # loaded using SELECT JOIN
        [Post(id=1), Post(id=2), ...]
        >>> user.posts[0].comments  # loaded using SELECT IN
        [Comment(id=1), Comment(id=2), ...]
        """
        async_query = cls.get_async_query()
        return async_query.with_subquery(*paths, model=cls)

    @classmethod
    def with_schema(
        cls,
        schema: dict[
            InstrumentedAttribute[Any],
            str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
        ],
    ) -> AsyncQuery[Self]:
        """Joined, subqueryload and selectinload eager loading.

        Useful for complex cases where you need to load
        nested relationships in separate queries.

        .. warning::
            A query which makes use of ``subqueryload()`` in
            conjunction with a limiting modifier such as
            ``Query.limit()`` or ``Query.offset()`` should always
            include ``Query.order_by()`` against unique column(s)
            such as the primary key, so that the additional queries
            emitted by ``subqueryload()`` include the same ordering
            as used by the parent query. Without it, there is a chance
            that the inner query could return the wrong rows, as
            specified in `The importance of ordering <https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering>`_.

            Incorrect, LIMIT without ORDER BY::

                User.options(subqueryload(User.posts))
                    .first()

            Incorrect if User.name is not unique::

                User.options(subqueryload(User.posts))
                    .order_by(User.name)
                    .first()

            Correct::

                User.options(subqueryload(User.posts))
                    .order_by(User.name, User.id)
                    .first()

            To get more information about SELECT IN and SELECT JOIN
            strategies, see the `loading relationships docs <https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html>`_.

        Parameters
        ----------
        schema : dict[InstrumentedAttribute[Any], str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict]
            Dictionary defining the loading strategy.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance for chaining.

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
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )

        Usage:
        >>> from sqlactive import JOINED, SUBQUERY
        >>> schema = {
        ...     User.posts: JOINED,          # joinedload user
        ...     User.comments: (SUBQUERY, {  # load comments in separate query
        ...         Comment.user: JOINED     # but, in this separate query, join user
        ...     })
        ... }
        >>> user = await User.with_schema(schema)
        ...                  .order_by(User.id)  # important when limiting
        ...                  .first()            # limiting modifier
        >>> user
        User(id=1)
        >>> user.posts
        [Post(id=1), Post(id=2), ...]
        >>> user.posts[0].comments
        [Comment(id=1), Comment(id=2), ...]
        >>> user.posts[0].comments[0].user
        User(id=1)
        """
        async_query = cls.get_async_query()
        return async_query.with_schema(schema)

    @classmethod
    def smart_query(
        cls,
        criteria: Sequence[ColumnElement[bool]] | None = None,
        filters: (
            dict[str, Any]
            | dict[OperatorType, Any]
            | list[dict[str, Any]]
            | list[dict[OperatorType, Any]]
            | None
        ) = None,
        sort_columns: (
            Sequence[ColumnExpressionOrStrLabelArgument] | None
        ) = None,
        sort_attrs: Sequence[str] | None = None,
        group_columns: (
            Sequence[ColumnExpressionOrStrLabelArgument] | None
        ) = None,
        group_attrs: Sequence[str] | None = None,
        schema: (
            dict[
                InstrumentedAttribute[Any],
                str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
            ]
            | None
        ) = None,
    ) -> AsyncQuery[Self]:
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
    def get_async_query(
        cls, query: Select[tuple[Any, ...]] | None = None
    ) -> AsyncQuery[Self]:
        """Returns an ``AsyncQuery`` instance with
        the provided ``sqlalchemy.sql.Select`` instance.

        If no ``sqlalchemy.sql.Select`` instance is provided,
        it uses the ``query`` property of the model.

        Parameters
        ----------
        query : Select[tuple[Any, ...]] | None, optional
            SQLAlchemy query, by default None.

        Returns
        -------
        AsyncQuery[Self]
            Async query instance.

        Examples
        --------
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> async_query = User.get_async_query()
        >>> bob = await async_query.where(name__like='Bob%').first()
        >>> bob.name
        'Bob Williams'
        >>> bob.age
        30
        """
        if query is None:
            return AsyncQuery[cls](cls.query)
        return AsyncQuery[cls](query)

    @classmethod
    @deprecated(
        "Deprecated since version 0.2: "
        "Use 'primary_key_name' property instead.",
        stacklevel=2,
    )
    def get_primary_key_name(cls) -> str:
        """Gets the primary key name of the model.

        .. deprecated:: 0.2
            This method will be removed in future versions.
            Use ``primary_key_name`` property instead.

        .. warning::
            This method can only be used if the model has a single
            primary key. If the model has a composite primary key,
            an ``CompositePrimaryKeyError`` is raised.

        Returns
        -------
        str
            The name of the primary key.

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
        >>> User.get_primary_key_name()
        'id'
        """
        return cls.primary_key_name

    @classmethod
    def set_session(cls, session: async_scoped_session[AsyncSession]) -> None:
        super().set_session(session)
        AsyncQuery.set_session(session)

    async def __aenter__(self) -> Self:
        """Saves the instance to the database temporarily.
        The instance will be deleted on exit.
        """
        return await self.save()

    async def __aexit__(self, *_) -> None:
        """Deletes the instance saved on entry."""
        await self.delete()
