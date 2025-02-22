"""This module defines ``AsyncQuery`` class."""

from collections.abc import Sequence
from typing import Any, Generic, Literal, TypeVar, overload

from sqlalchemy.engine import Result, Row, ScalarResult
from sqlalchemy.orm import joinedload, selectinload, subqueryload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import Select
from sqlalchemy.sql._typing import _ColumnsClauseArgument
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import func
from typing_extensions import Self

from .exceptions import RelationError
from .session import SessionMixin
from .smart_query import ColumnExpressionOrStrLabelArgument, SmartQueryMixin

_T = TypeVar('_T')


class AsyncQuery(SessionMixin, SmartQueryMixin, Generic[_T]):
    """Async wrapper for ``sqlalchemy.sql.Select``.

    Provides a set of helper methods for
    asynchronously executing the query.

    This class needs an ``sqlalchemy.ext.asyncio.async_scoped_session``
    instance to perform the actual query. The ``set_session`` class
    method must be called before using this class.

    When calling the ``set_session`` method from a base model
    (either ``ActiveRecordBaseModel``, a subclass of it or a model,
    i.e. ``User``), the session will be set automatically.

    Calling ``set_session`` from either a base model or a model::

        # from your base model class (recommended)
        YourBaseModel.set_session(session)

        # from the ActiveRecordBaseModel class
        ActiveRecordBaseModel.set_session(session)

        # from your model
        User.set_session(session)

        # create a instance
        query = select(User)
        async_query = AsyncQuery(query)

    Calling ``set_session`` from the ``AsyncQuery`` instance::

        # create a instance
        query = select(User)
        async_query = AsyncQuery(query)

        # set the session from the base model
        async_query.set_session(BaseModel._session)

        # set the session from the model
        async_query.set_session(User._session)

    Example of usage (assume a model ``User``):
    >>> query = select(User)
    >>> async_query = AsyncQuery(query)
    >>> async_query.where(name__like='%John%')
    ...            .sort('-created_at')
    ...            .limit(2)
    >>> users = await async_query.all()
    >>> users
    [User(id=1), User(id=2)]

    To get the ``sqlalchemy.sql.Select`` instance to use native
    SQLAlchemy methods refer to the ``query`` attribute:
    >>> query = select(User)
    >>> async_query = AsyncQuery(query)
    >>> async_query.query
    <sqlalchemy.sql.Select at 0x...>

    Visit the [API reference](https://daireto.github.io/sqlactive/api/async-query/#api-reference)
    for the complete list of methods.
    """

    __abstract__ = True

    query: Select[tuple[Any, ...]]
    """The wrapped ``sqlalchemy.sql.Select`` instance."""

    def __init__(self, query: Select[tuple[Any, ...]]) -> None:
        """Builds an async wrapper for SQLAlchemy ``Query``.

        .. warning::
            You must provide a session by calling
            the ``set_session`` method.

        Parameters
        ----------
        query : Select[tuple[Any, ...]]
            The ``sqlalchemy.sql.Select`` instance.
        """
        self.query = query

    async def execute(self) -> Result[Any]:
        """Executes the query and returns a ``sqlalchemy.engine.Result``
        instance containing the results.

        Returns
        -------
        Result[Any]
            Result of the query.
        """
        async with self.AsyncSession() as session:
            return await session.execute(self.query)

    async def scalars(self) -> ScalarResult[_T]:
        """Returns a ``sqlalchemy.engine.ScalarResult`` instance
        containing all results.

        Returns
        -------
        ScalarResult[_T]
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> result = await async_query.scalars()
        >>> result
        <sqlalchemy.engine.result.ScalarResult object at 0x...>
        >>> users = result.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> result = await async_query.where(name='John Doe').scalars()
        >>> users = result.all()
        >>> users
        [User(id=2)]
        """
        return (await self.execute()).scalars()

    @overload
    async def first(self) -> _T | None: ...

    @overload
    async def first(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def first(
        self, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def first(
        self, scalar: bool
    ) -> _T | Row[tuple[Any, ...]] | None: ...

    async def first(self, scalar: bool = True):
        """Fetches the first row or ``None`` if no results are found.

        If ``scalar`` is ``True``, returns a scalar value (default).

        Parameters
        ----------
        scalar : bool, optional
            If ``True``, returns a scalar value (default).
            If ``False``, returns a row.

        Returns
        -------
        _T
            The scalar if found.
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.first()
        >>> user
        User(id=1)
        >>> user = await async_query.first(scalar=False)
        >>> user
        (User(id=1),)

        Selecting specific columns:
        >>> user = await async_query.select(User.name, User.age).first()
        >>> user
        'Bob Williams'
        >>> user = await async_query.select(User.name, User.age)
        ...                         .first(scalar=False)
        >>> user
        ('Bob Williams', 30)
        """
        if scalar:
            return (await self.scalars()).first()

        return (await self.execute()).first()

    @overload
    async def one(self) -> _T: ...

    @overload
    async def one(self, scalar: Literal[True]) -> _T: ...

    @overload
    async def one(self, scalar: Literal[False]) -> Row[tuple[Any, ...]]: ...

    @overload
    async def one(self, scalar: bool) -> _T | Row[tuple[Any, ...]]: ...

    async def one(self, scalar: bool = True):
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
        _T
            The scalar if found.
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.where(name='John Doe').one()
        >>> user
        User(id=1)
        >>> user = await async_query.where(name='John Doe')
        ...                         .one(scalar=False)
        >>> user
        (User(id=1),)
        >>> user = await async_query.where(name='Unknown').one()
        Traceback (most recent call last):
            ...
        sqlalchemy.exc.NoResultFound: No row was found when one was required
        >>> user = await async_query.one()
        Traceback (most recent call last):
            ...
        sqlalchemy.exc.MultipleResultsFound: Multiple rows were found when one was required

        Selecting specific columns:
        >>> user = await async_query.where(name='John Doe')
        ...                  .select(User.name, User.age)
        ...                  .one()
        >>> user
        'John Doe'
        >>> user = await async_query.where(name='John Doe')
        ...                  .select(User.name, User.age)
        ...                  .one(scalar=False)
        >>> user
        ('John Doe', 30)
        """
        if scalar:
            return (await self.scalars()).one()

        return (await self.execute()).one()

    @overload
    async def one_or_none(self) -> _T | None: ...

    @overload
    async def one_or_none(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def one_or_none(
        self, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def one_or_none(
        self, scalar: bool
    ) -> _T | Row[tuple[Any, ...]] | None: ...

    async def one_or_none(self, scalar: bool = True):
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
        _T
            The scalar if found.
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.where(name='John Doe')
        ...                         .one_or_none()
        >>> user
        User(id=1)
        >>> user = await async_query.where(name='John Doe')
        ...                         .one_or_none(scalar=False)
        >>> user
        (User(id=1),)
        >>> user = await async_query.where(name='Unknown')
        ...                         .one_or_none()
        >>> user
        None
        >>> user = await async_query.one_or_none()
        Traceback (most recent call last):
            ...
        sqlalchemy.exc.MultipleResultsFound: Multiple rows were found when one was required

        Selecting specific columns:
        >>> user = await async_query.where(name='John Doe')
        ...                         .select(User.name, User.age)
        ...                         .one_or_none()
        >>> user
        'John Doe'
        >>> user = await async_query.where(name='John Doe')
        ...                         .select(User.name, User.age)
        ...                         .one_or_none(scalar=False)
        >>> user
        ('John Doe', 30)
        """
        if scalar:
            return (await self.scalars()).one_or_none()

        return (await self.execute()).one_or_none()

    @overload
    async def all(self) -> Sequence[_T]: ...

    @overload
    async def all(self, scalars: Literal[True]) -> Sequence[_T]: ...

    @overload
    async def all(
        self, scalars: Literal[False]
    ) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    async def all(
        self, scalars: bool
    ) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]: ...

    async def all(self, scalars: bool = True):
        """Fetches all rows.

        If ``scalars`` is ``True``, returns scalar values (default).

        Parameters
        ----------
        scalars : bool, optional
            If ``True``, returns scalar values (default).
            If ``False``, returns rows.

        Returns
        -------
        Sequence[_T]
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await async_query.all(scalars=False)
        >>> users
        [(User(id=1),), (User(id=2),), ...]

        Selecting specific columns:
        >>> users = await async_query.select(User.name, User.age).all()
        >>> users
        ['John Doe', 'Jane Doe', ...]
        >>> users = await async_query.select(User.name, User.age)
        ...                          .all(scalars=False)
        >>> users
        [('John Doe', 30), ('Jane Doe', 32), ...]
        """
        if scalars:
            return (await self.scalars()).all()

        return (await self.execute()).all()

    async def count(self) -> int:
        """Fetches the number of rows.

        Returns
        -------
        int
            The number of rows.

        Examples
        --------
        Assume a model ``User`` with 34 rows in the database:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> count = await async_query.count()
        >>> count
        34
        """
        self._set_count_query()
        return (await self.execute()).scalars().one()

    @overload
    async def unique(self) -> ScalarResult[_T]: ...

    @overload
    async def unique(self, scalars: Literal[True]) -> ScalarResult[_T]: ...

    @overload
    async def unique(
        self, scalars: Literal[False]
    ) -> Result[tuple[Any, ...]]: ...

    @overload
    async def unique(
        self, scalars: bool
    ) -> ScalarResult[_T] | Result[tuple[Any, ...]]: ...

    async def unique(self, scalars: bool = True):
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
        ScalarResult[_T]
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.unique()
        >>> users
        <sqlalchemy.engine.result.ScalarResult object at 0x...>
        >>> users = await async_query.unique(scalars=False)
        >>> users
        <sqlalchemy.engine.result.Result object at 0x...>
        """
        if scalars:
            return (await self.scalars()).unique()

        return (await self.execute()).unique()

    @overload
    async def unique_first(self) -> _T | None: ...

    @overload
    async def unique_first(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def unique_first(
        self, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def unique_first(
        self, scalar: bool
    ) -> _T | Row[tuple[Any, ...]] | None: ...

    async def unique_first(self, scalar: bool = True):
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
        return (await self.unique(scalar)).first()

    @overload
    async def unique_one(self) -> _T: ...

    @overload
    async def unique_one(self, scalar: Literal[True]) -> _T: ...

    @overload
    async def unique_one(
        self, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]]: ...

    @overload
    async def unique_one(self, scalar: bool) -> _T | Row[tuple[Any, ...]]: ...

    async def unique_one(self, scalar: bool = True):
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
        return (await self.unique(scalar)).one()

    @overload
    async def unique_one_or_none(self) -> _T | None: ...

    @overload
    async def unique_one_or_none(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def unique_one_or_none(
        self, scalar: Literal[False]
    ) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def unique_one_or_none(
        self, scalar: bool
    ) -> _T | Row[tuple[Any, ...]] | None: ...

    async def unique_one_or_none(self, scalar: bool = True):
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
        return (await self.unique(scalar)).one_or_none()

    @overload
    async def unique_all(self) -> Sequence[_T]: ...

    @overload
    async def unique_all(self, scalars: Literal[True]) -> Sequence[_T]: ...

    @overload
    async def unique_all(
        self, scalars: Literal[False]
    ) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    async def unique_all(
        self, scalars: bool
    ) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]: ...

    async def unique_all(self, scalars: bool = True):
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
        return (await self.unique(scalars)).all()

    async def unique_count(self) -> int:
        """Similar to ``count()`` but applies unique filtering to the
        objects returned by ``sqlalchemy.engine.ScalarResult``.

        .. note::
            This method is different from ``distinct()`` in that it
            applies unique filtering to the objects returned in the
            result instance. If you need to apply unique filtering on
            the query (a DISTINCT clause), use ``distinct()`` instead.

        See ``unique()`` and ``count()`` for more details.
        """
        self._set_count_query()
        return (await self.execute()).scalars().unique().one()

    def select(self, *entities: _ColumnsClauseArgument[Any]) -> Self:
        """Replaces the columns clause with the given entities.

        The existing set of FROMs are maintained, including those
        implied by the current columns clause.

        Parameters
        ----------
        *entities : _ColumnsClauseArgument[Any]
            The entities to select.

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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> async_query.order_by('-created_at')
        >>> async_query
        'SELECT users.id, users.username, users.name, ... FROM users ORDER BY users.created_at DESC'
        >>> async_query.select(User.name, User.age)
        >>> async_query
        'SELECT users.name, users.age FROM users ORDER BY users.created_at DESC'
        """
        if not entities:
            return self

        self.query = self.query.with_only_columns(
            *entities, maintain_column_froms=True
        )
        return self

    def distinct(self) -> Self:
        """Applies DISTINCT to the SELECT statement overall.

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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> async_query.query
        'SELECT users.id, users.username, users.name, ... FROM users'
        >>> async_query.distinct()
        'SELECT DISTINCT users.id, users.username, users.name, ... FROM users'
        """
        self.query = self.query.distinct()
        return self

    def options(self, *args: ExecutableOption) -> Self:
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

        Joined eager loading:
        >>> query = select(User)
        >>> aq = AsyncQuery(query)
        >>> users = await aq.options(joinedload(User.posts))
        ...                 .unique_all()  # required for joinedload()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users[0].posts
        [Post(id=1), Post(id=2), ...]
        >>> user = await aq.options(joinedload(User.posts)).first()
        >>> user
        User(id=1)
        >>> users.posts
        [Post(id=1), Post(id=2), ...]

        Subquery eager loading:
        >>> users = await aq.options(subqueryload(User.posts)).all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users[0].posts
        [Post(id=1), Post(id=2), ...]

        Eager loading without calling unique() before all():
        >>> users = await aq.options(joinedload(User.posts)).all()
        Traceback (most recent call last):
            ...
        InvalidRequestError: The unique() method must be invoked on this Result...
        """
        self.query = self.query.options(*args)
        return self

    def where(self, *criteria: ColumnElement[bool], **filters: Any) -> Self:
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

        Using Django-like syntax:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.where(age__gte=18).all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await async_query.where(
        ...     name__like='%John%',
        ...     age=30
        ... ).all()
        >>> users
        [User(id=2)]

        Using SQLAlchemy syntax:
        >>> users = await async_query.where(User.age >= 18).all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await async_query.where(
        ...     User.name == 'John Doe',
        ...     User.age == 30
        ... ).all()
        >>> users
        [User(id=2)]

        Using both syntaxes:
        >>> users = await async_query.where(
        ...     User.age == 30,
        ...     name__like='%John%'
        ... ).all()
        >>> users
        [User(id=2)]
        """
        self.query = self.smart_query(
            query=self.query, criteria=criteria, filters=filters
        )
        return self

    def filter(self, *criteria: ColumnElement[bool], **filters: Any) -> Self:
        """Synonym for ``where()``."""
        return self.where(*criteria, **filters)

    def find(self, *criteria: ColumnElement[bool], **filters: Any) -> Self:
        """Synonym for ``where()``."""
        return self.where(*criteria, **filters)

    def search(
        self,
        search_term: str,
        columns: Sequence[str | InstrumentedAttribute[Any]] | None = None,
    ) -> Self:
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.search(search_term='John').all()
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
        >>> users = await async_query.search(
        ...     search_term='John',
        ...     columns=[User.name, User.username]
        ... ).all()
        >>> users
        [User(id=2), User(id=6)]
        >>> users = await async_query.search(
        ...     search_term='John',
        ...     columns=[User.username]  # or 'username'
        ... ).all()
        >>> users
        [User(id=2)]
        """
        self.query = self.apply_search_filter(
            query=self.query, search_term=search_term, columns=columns
        )
        return self

    def order_by(self, *columns: ColumnExpressionOrStrLabelArgument) -> Self:
        """Applies one or more ORDER BY criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Parameters
        ----------
        *columns : ColumnExpressionOrStrLabelArgument
            Django-like or SQLAlchemy sort expressions.

        Returns
        -------
        Self
            The instance itself for method chaining.

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
        >>> query = select(Post)
        >>> async_query = AsyncQuery(query)
        >>> posts = await async_query.order_by('-rating', 'user___name').all()
        >>> posts
        [Post(id=1), Post(id=4), ...]

        Using SQLAlchemy syntax:
        >>> posts = await async_query.order_by(Post.rating.desc()).all()
        >>> posts
        [Post(id=1), Post(id=4), ...]

        Using both syntaxes:
        >>> posts = await async_query.order_by(
        ...     Post.rating.desc(),
        ...     'user___name'
        ... ).all()
        >>> posts
        [Post(id=1), Post(id=4), ...]
        """
        sort_columns, sort_attrs = self._split_columns_and_attrs(columns)
        self.query = self.smart_query(
            query=self.query, sort_columns=sort_columns, sort_attrs=sort_attrs
        )
        return self

    def sort(self, *columns: ColumnExpressionOrStrLabelArgument) -> Self:
        """Synonym for ``order_by()``."""
        return self.order_by(*columns)

    def group_by(
        self,
        *columns: ColumnExpressionOrStrLabelArgument,
        select_columns: Sequence[_ColumnsClauseArgument[Any]] | None = None,
    ) -> Self:
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
        Self
            The instance itself for method chaining.

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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> columns = (User.age, func.count(User.name))
        >>> async_query.group_by(
        ...     User.age, select_columns=columns
        ... )
        >>> rows = await async_query.all(scalars=False)
        [(30, 2), (32, 1), ...]

        You can also call ``select()`` before calling ``group_by()``:
        >>> from sqlalchemy.sql import text, func
        >>> query = select(Post)
        >>> async_query = AsyncQuery(query)
        >>> async_query.select(
        ...     Post.rating,
        ...     text('users_1.name'),
        ...     func.count(Post.title)
        ... )
        >>> async_query.group_by('rating', 'user___name')
        >>> rows = async_query.all(scalars=False)
        >>> rows
        [(4, 'John Doe', 1), (5, 'Jane Doe', 1), ...]
        """
        if select_columns:
            self.select(*select_columns)

        group_columns, group_attrs = self._split_columns_and_attrs(columns)
        self.query = self.smart_query(
            query=self.query,
            group_columns=group_columns,
            group_attrs=group_attrs,
        )
        return self

    def offset(self, offset: int) -> Self:
        """Applies one OFFSET criteria to the query.

        Parameters
        ----------
        offset : int
            Number of rows to skip.

        Returns
        -------
        Self
            The instance itself for method chaining.

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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await async_query.offset(10).all()
        >>> users
        [User(id=11), User(id=12), ...]
        >>> async_query.offset(-1)
        Traceback (most recent call last):
            ...
        ValueError: offset must be >= 0
        """
        if offset < 0:
            raise ValueError('offset must be >= 0')

        self.query = self.query.offset(offset)
        return self

    def skip(self, skip: int) -> Self:
        """Synonym for ``offset()``."""
        return self.offset(skip)

    def limit(self, limit: int) -> Self:
        """Applies one LIMIT criteria to the query.

        Parameters
        ----------
        limit : int
            Maximum number of rows to return.

        Returns
        -------
        Self
            The instance itself for method chaining.

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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.all()
        >>> users
        [User(id=1), User(id=2), ...]
        >>> users = await async_query.limit(2).all()
        >>> users
        [User(id=1), User(id=2)]
        >>> async_query.limit(-1)
        Traceback (most recent call last):
            ...
        ValueError: limit must be >= 0
        """
        if limit < 0:
            raise ValueError('limit must be >= 0')

        self.query = self.query.limit(limit)
        return self

    def take(self, take: int) -> Self:
        """Synonym for ``limit()``."""
        return self.limit(take)

    def top(self, top: int) -> Self:
        """Synonym for ``limit()``."""
        return self.limit(top)

    def join(
        self,
        *paths: InstrumentedAttribute[Any]
        | tuple[InstrumentedAttribute[Any], bool],
        model: type[_T] | None = None,
    ) -> Self:
        """Joined eager loading using LEFT OUTER JOIN.

        When a tuple is passed, the second element must be boolean, and
        if ``True``, the join is INNER JOIN, otherwise LEFT OUTER JOIN.

        .. note::
            Only direct relationships can be loaded.

        Parameters
        ----------
        *paths : InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]
            Relationship attributes to join.
        model : type[_T] | None, optional
            If given, checks that each path belongs to this model,
            by default None.

        Returns
        -------
        Self
            The instance itself for method chaining.

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
        >>> query = select(Comment)
        >>> async_query = AsyncQuery(query)
        >>> comment = await async_query.join(
        ...     Comment.user,         # LEFT OUTER JOIN
        ...     (Comment.post, True)  # True = INNER JOIN
        ... ).first()
        >>> comment
        Comment(id=1)
        >>> comment.user
        User(id=1)
        >>> comment.post
        Post(id=1)
        >>> async_query.join(
        ...     Comment.user,
        ...     (Comment.post, 'inner')  # invalid argument
        ... )
        Traceback (most recent call last):
            ...
        ValueError: expected boolean for second element of tuple, got str: 'inner'
        """
        return self._apply_eager_loading_options(
            *paths, joined=True, model=model
        )

    def with_subquery(
        self,
        *paths: InstrumentedAttribute[Any]
        | tuple[InstrumentedAttribute[Any], bool],
        model: type[_T] | None = None,
    ) -> Self:
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
        *paths : InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]
            Relationship attributes to load.
        model : type[_T] | None, optional
            If given, checks that each path belongs to this model,
            by default None.

        Returns
        -------
        Self
            The instance itself for method chaining.

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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.with_subquery(
        ...     User.posts,            # SELECT JOIN
        ...     (User.comments, True)  # True = SELECT IN
        ... ).all()
        >>> users[0]
        User(id=1)
        >>> users[0].posts              # loaded using SELECT JOIN
        [Post(id=1), Post(id=2), ...]
        >>> users[0].posts[0].comments  # loaded using SELECT IN
        [Comment(id=1), Comment(id=2), ...]
        >>> async_query.with_subquery(
        ...     User.posts,
        ...     (User.comments, 'selectin')  # invalid argument
        ... )
        Traceback (most recent call last):
            ...
        ValueError: expected boolean for second element of tuple, got str: 'selectin'

        Using a limiting modifier:
        >>> user = await async_query.with_subquery(
        ...     User.posts,            # SELECT JOIN
        ...     (User.comments, True)  # True = SELECT IN
        ... ).sort('id')  # sorting modifier (Important!!!)
        ...  .first()     # limiting modifier
        >>> user = await async_query.with_subquery(
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
        return self._apply_eager_loading_options(*paths, model=model)

    def with_schema(
        self,
        schema: dict[
            InstrumentedAttribute[Any],
            str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
        ],
    ) -> Self:
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
        >>> query = select(User)
        >>> aq = AsyncQuery(query)
        >>> user = await aq.with_schema(schema)
        ...                .order_by(User.id)  # important when limiting
        ...                .first()            # limiting modifier
        >>> user
        User(id=1)
        >>> user.posts
        [Post(id=1), Post(id=2), ...]
        >>> user.posts[0].comments
        [Comment(id=1), Comment(id=2), ...]
        >>> user.posts[0].comments[0].user
        User(id=1)
        """
        return self.options(*self.eager_expr(schema or {}))

    def __str__(self) -> str:
        """Returns the raw SQL query."""
        return str(self.query)

    def __repr__(self) -> str:
        """Returns the raw SQL query."""
        return str(self)

    def _split_columns_and_attrs(
        self,
        columns_and_attrs: Sequence[ColumnExpressionOrStrLabelArgument],
    ) -> tuple[list[str], list[str]]:
        """Splits columns and attrs.

        Parameters
        ----------
        columns_and_attrs : Sequence[ColumnExpressionOrStrLabelArgument]
            Columns and attrs.

        Returns
        -------
        tuple[list[str], list[str]]
            A tuple of columns and attrs.
        """
        columns = []
        attrs = []
        for column in columns_and_attrs:
            if isinstance(column, str):
                attrs.append(column)
            else:
                columns.append(column)

        return columns, attrs

    def _apply_eager_loading_options(
        self,
        *paths: InstrumentedAttribute[Any]
        | tuple[InstrumentedAttribute[Any], bool],
        joined: bool = False,
        model: type[_T] | None = None,
    ) -> Self:
        """Applies the eager loading options from the given paths.

        Takes paths like::

            (User.posts, (User.comments, True))

        and applies options like::

            (subqueryload(User.posts), selectinload(User.comments))

        The ``joined`` flag is used for joined eager loading.

        Parameters
        ----------
        *paths : InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]
            Eager loading paths.
        joined : bool, optional
            Whether to use joined eager loading, by default False.
        model : type[_T] | None, optional
            If given, checks that each path belongs to this model,
            by default None.

        Returns
        -------
        Self
            The instance itself for method chaining.

        Raises
        ------
        TypeError
            If the second element of tuple is not boolean.
        RelationError
            If relationship does not exist.
        """
        options = []
        for path in paths:
            # if path is like (User.comments, True)
            if isinstance(path, tuple):
                if not isinstance(path[1], bool):
                    raise TypeError(
                        f"expected boolean for second element of tuple, "
                        f"got {type(path[1])}: '{path[1]}'"
                    )

                # raise error if, i.e., model is User
                # and path is Post.comments
                if model and path[0].class_ != model:
                    raise RelationError(path[0].key, model.__name__)

                if joined:
                    options.append(joinedload(path[0], innerjoin=path[1]))
                    continue

                options.append(
                    selectinload(path[0]) if path[1] else subqueryload(path[0])
                )

            # simple paths like User.posts, User.comments
            else:
                if model and path.class_ != model:
                    raise RelationError(path.key, model.__name__)

                if joined:
                    options.append(joinedload(path))
                    continue

                options.append(subqueryload(path))

        return self.options(*options)

    def _set_count_query(self) -> None:
        """Sets the count aggregate function to the query."""
        self.query = self.query.with_only_columns(
            func.count(), maintain_column_froms=True
        ).order_by(None)
