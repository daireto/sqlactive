"""This module defines `AsyncQuery` class."""

from collections.abc import Sequence
from sqlalchemy.sql import Select
from sqlalchemy.sql._typing import (
    _ColumnExpressionArgument,
    _ColumnExpressionOrStrLabelArgument,
    _ColumnsClauseArgument,
)
from sqlalchemy.engine import Result, Row, ScalarResult
from sqlalchemy.ext.asyncio import async_scoped_session, AsyncSession
from sqlalchemy.orm import joinedload, subqueryload, selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute
from sqlalchemy.sql.base import ExecutableOption
from typing import Any, Generic, Literal, TypeVar, overload

from .exceptions import NoSessionError
from .smart_query import SmartQueryMixin


_T = TypeVar('_T')


class AsyncQuery(SmartQueryMixin, Generic[_T]):
    """Async wrapper for `sqlalchemy.sql.Select`.

    Provides a set of helper methods for asynchronously executing the query.

    Example of usage:

    ```python
        query = select(User)
        async_query = AsyncQuery(query, User._session)
        async_query = async_query.filter(name__like='%John%').sort('-created_at').limit(2)
        users = await async_query.all()
        >>> users
        # [<User 1>, <User 2>]
    ```

    To get the `sqlalchemy.sql.Select` instance to use native SQLAlchemy methods
    use the `query` property:

    ```python
        query = select(User)
        async_query = AsyncQuery(query, User._session)
        async_query.query
        # <sqlalchemy.sql.Select>
    ```

    Visit the [API reference](https://daireto.github.io/sqlactive/api/async_query/#api-reference)
    for the complete list of methods.
    """

    __abstract__ = True

    _query: Select[tuple[Any, ...]]
    """The original `sqlalchemy.sql.Select` instance."""

    _session: async_scoped_session[AsyncSession] | None = None
    """Async session factory."""

    def __init__(
        self,
        query: Select[tuple[Any, ...]],
        session: async_scoped_session[AsyncSession] | None = None,
    ) -> None:
        """Builds an async wrapper for SQLAlchemy `Query`.

        Parameters
        ----------
        query : Select[tuple[Any, ...]]
            The `sqlalchemy.sql.Select` instance.
        session : async_scoped_session[AsyncSession] | None, optional
            Async session factory, by default None.

        NOTE: If no session is provided, a `NoSessionError` will be raised
        when attempting to execute the query. You must either provide
        a session by passing it in this constructor or by calling
        the `set_session` method.
        """

        self._query = query
        self._session = session

    def set_session(self, session: async_scoped_session[AsyncSession]) -> None:
        """Sets the async session factory.

        Parameters
        ----------
        session : async_scoped_session[AsyncSession]
            Async session factory.
        """

        self._session = session

    @property
    def query(self) -> Select[tuple[Any, ...]]:
        """Returns the original `sqlalchemy.sql.Select` instance."""

        return self._query

    @query.setter
    def query(self, query: Select[tuple[Any, ...]]) -> None:
        """Sets the original `sqlalchemy.sql.Select` instance."""

        self._query = query

    @property
    def AsyncSession(self) -> async_scoped_session[AsyncSession]:
        """Async session factory.

        Usage:

        ```python
            async with self.AsyncSession() as session:
                await session.execute(query)
        ```

        Raises
        ------
        NoSessionError
            If no session is available.
        """

        if self._session is not None:
            return self._session
        else:
            raise NoSessionError('Cannot get session. Please, call self.set_session()')

    def select(self, *entities: _ColumnsClauseArgument[Any]):
        """Replaces the original `sqlalchemy.sql.Select` instance with a new one.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> str(async_query)
        # SELECT users.id, users.username, ... FROM users
        >>> async_query.select(User.name, User.age)
        >>> str(async_query)
        # SELECT users.name, users.age FROM users
        >>> async_query.select(User.age, func.max(User.age))
        >>> str(async_query)
        # SELECT users.age, max(users.age) AS max_1 FROM users

        Raises
        ------
        ValueError
            If no entities are selected.
        """

        if len(entities) == 0:
            raise ValueError('At least one column must be selected.')

        self._query._set_entities(entities)
        return self

    def options(self, *args: ExecutableOption):
        """Applies the given list of mapper options.

        Quoting from https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading:

            When including `joinedload()` in reference to a one-to-many or
            many-to-many collection, the `Result.unique()` method must be
            applied to the returned result, which will make the incoming rows
            unique by primary key that otherwise are multiplied out by the join.
            The ORM will raise an error if this is not present.

            This is not automatic in modern SQLAlchemy, as it changes the behavior
            of the result set to return fewer ORM objects than the statement would
            normally return in terms of number of rows. Therefore SQLAlchemy keeps
            the use of Result.unique() explicit, so there is no ambiguity that the
            returned objects are made unique on primary key.

            To learn more about options, see
            https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.options

        Example 1:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.options(joinedload(User.posts)).all_unique()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users[0].posts
        # [<Post 1>, <Post 2>, ...]

        Example 2:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.options(joinedload(User.posts)).first()
        >>> user
        # <User 1>
        >>> user.posts
        # [<Post 1>, <Post 2>, ...]

        Example 3:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.options(subqueryload(User.posts)).all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users[0].posts
        # [<Post 1>, <Post 2>, ...]

        Example 4:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.options(joinedload(User.posts)).all()
        # Traceback (most recent call last):
        #     ...
        # InvalidRequestError: 'The unique() method must be invoked...'
        """

        self._query = self._query.options(*args)
        return self

    def where(self, *criteria: _ColumnExpressionArgument[bool], **filters: Any):
        """Applies one or more WHERE criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Example using Django-like syntax:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.filter(name__like='%John%').all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await async_query.filter(name__like='%John%', age=30).all()
        >>> users
        # [<User 2>]

        Example using SQLAlchemy syntax:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.filter(User.name == 'John Doe').all()
        >>> users
        # [<User 2>]

        Example using both:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.filter(User.age == 30, name__like='%John%').all()
        >>> users
        # [<User 2>]
        """

        self._query = self.smart_query(query=self._query, criteria=criteria, filters=filters)
        return self

    def filter(self, *criteria: _ColumnExpressionArgument[bool], **filters: Any):
        """Synonym for `where()`."""

        return self.where(*criteria, **filters)

    def find(self, *criteria: _ColumnExpressionArgument[bool], **filters: Any):
        """Synonym for `where()`."""

        return self.where(*criteria, **filters)

    def order_by(self, *columns: _ColumnExpressionOrStrLabelArgument[Any]):
        """Applies one or more ORDER BY criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Example using Django-like syntax:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.order_by('-created_at').all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> query = select(Post)
        >>> async_query = AsyncQuery(query)
        >>> posts = await async_query.order_by('-rating', 'user___name').all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]

        Example using SQLAlchemy syntax:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.order_by(User.created_at.desc()).all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> query = select(Post)
        >>> async_query = AsyncQuery(query)
        >>> posts = await async_query.order_by(desc(Post.rating)).all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]
        """

        sort_columns, sort_attrs = self._split_columns_and_attrs(columns)
        self._query = self.smart_query(query=self._query, sort_columns=sort_columns, sort_attrs=sort_attrs)
        return self

    def sort(self, *columns: _ColumnExpressionOrStrLabelArgument[Any]):
        """Synonym for `order_by()`."""

        return self.order_by(*columns)

    def group_by(self, *columns: _ColumnExpressionOrStrLabelArgument[Any]):
        """Applies one or more GROUP BY criteria to the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        NOTE: It is recommended to select specific columns (e.g. `select(User.id, User.name)`)
        instead of all columns of a model (e.g. `select(User)`). You can call `select()` again
        if you want to select specific columns.

        Example using Django-like syntax:
        >>> query = select(User.age, func.count(User.name))
        >>> async_query = AsyncQuery(query)
        >>> rows = await async_query.group_by('age').fetch_rows()
        >>> rows
        # [(30, 2), (32, 1), ...]
        >>> query = select(Post.rating, Post.user.name, func.count(Post.title))
        >>> async_query = AsyncQuery(query)
        >>> rows = await async_query.group_by('rating', 'user___name').fetch_rows()
        >>> rows
        # [(4, 'John Doe', 1), (5, 'Jane Doe', 1), ...]

        Example using SQLAlchemy syntax:
        >>> query = select(User.age, func.count(User.name))
        >>> async_query = AsyncQuery(query)
        >>> rows = await async_query.group_by(User.age).fetch_rows()
        >>> rows
        # [(30, 2), (32, 1), ...]
        >>> query = select(Post.rating, Post.user.name, func.count(Post.title))
        >>> async_query = AsyncQuery(query)
        >>> rows = await async_query.group_by(Post.rating, Post.user.name).fetch_rows()
        >>> rows
        # [(4, 'John Doe', 1), (5, 'Jane Doe', 1), ...]
        """

        group_columns, group_attrs = self._split_columns_and_attrs(columns)
        self._query = self.smart_query(query=self._query, group_columns=group_columns, group_attrs=group_attrs)
        return self

    def offset(self, offset: int):
        """Applies one OFFSET criteria to the query.

        Parameters
        ----------
        offset : int
            Offset.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.offset(10).all()
        >>> users
        # [<User 11>, <User 12>, ...]

        Raises
        ------
        ValueError
            If offset is negative.
        """

        if offset < 0:
            raise ValueError('Offset must be positive.')

        self._query = self._query.offset(offset)
        return self

    def skip(self, skip: int):
        """Synonym for `offset()`."""

        return self.offset(skip)

    def limit(self, limit: int):
        """Applies one LIMIT criteria to the query.

        Parameters
        ----------
        limit : int
            Limit.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.limit(2).all()
        >>> users
        # [<User 1>, <User 2>]

        Raises
        ------
        ValueError
            If limit is negative.
        """

        if limit < 0:
            raise ValueError('Limit must be positive.')

        self._query = self._query.limit(limit)
        return self

    def take(self, take: int):
        """Synonym for `limit()`."""

        return self.limit(take)

    def join(self, *paths: QueryableAttribute | tuple[QueryableAttribute, bool], model: type[_T] | None = None):
        """Joined eager loading using LEFT OUTER JOIN.

        When a tuple is passed, the second element must be boolean.
        If it is `True`, the join is INNER JOIN, otherwise LEFT OUTER JOIN.

        Example:
        >>> query = select(Comment)
        >>> async_query = AsyncQuery(query)
        >>> comment = await async_query.join(Comment.user, (Comment.post, True), model=Comment).first()
        >>> comment
        # <Comment 1>
        >>> comment.user # LEFT OUTER JOIN
        # <User 1>
        >>> comment.post # INNER JOIN
        # <Post 1>

        Parameters
        ----------
        paths : *List[QueryableAttribute | tuple[QueryableAttribute, bool]
            Paths to eager load.
        model : type[_T] | None
            If given, checks that each path belongs to this model.

        Raises
        ------
        ValueError
            If the second element of tuple is not boolean.
        KeyError
            If path is not a relationship of `model`.
        """

        options = []
        for path in paths:
            if isinstance(path, tuple):
                if not isinstance(path[1], bool):
                    raise ValueError(f'The second element of tuple `{path[1]}` is not boolean.')
                if model and path[0].class_ != model:
                    raise KeyError(
                        f'Incorrect path `{path[0]}`: {model.__name__} does not have `{path[0].key}` relationship.'
                    )
                options.append(joinedload(path[0], innerjoin=path[1]))
            else:
                if model and path.class_ != model:
                    raise KeyError(
                        f'Incorrect path `{path}`: {model.__name__} does not have `{path.key}` relationship.'
                    )
                options.append(joinedload(path))

        return self.options(*options)

    def with_subquery(
        self,
        *paths: QueryableAttribute | tuple[QueryableAttribute, bool],
        model: type[_T] | None = None,
    ):
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
            async_query = AsyncQuery(query)

            # incorrect, no ORDER BY
            async_query.options(subqueryload(User.addresses)).first()

            # incorrect if User.name is not unique
            async_query.options(subqueryload(User.addresses)).order_by(User.name).first()

            # correct
            async_query.options(subqueryload(User.addresses)).order_by(
                User.name, User.id
            ).first()
        ```

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.with_subquery(User.posts, (User.comments, True)).all()
        >>> users[0]
        # <User 1>
        >>> users[0].posts  # Loaded in a separate query using SELECT JOIN
        # [<Post 1>, <Post 2>, ...]
        >>> users[0].posts[0].comments  # Loaded in a separate query using SELECT IN
        # [<Comment 1>, <Comment 2>, ...]

        Example using a limiting modifier:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.with_subquery(User.posts, (User.comments, True))
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.with_subquery(User.posts, (User.comments, True))
        ... .first()  # No recommended because it calls `limit(1)`
        ...           # and does not sort by any primary key.
        ...           # Use `limit(1).sort('id').first()` instead:
        >>> user = await async_query.with_subquery(User.posts, (User.comments, True))
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
        model : type[_T] | None
            If given, checks that each path belongs to this model.

        Raises
        ------
        KeyError
            If path is not a relationship of `model`.
        """

        options = []
        for path in paths:
            if isinstance(path, tuple):
                if not isinstance(path[1], bool):
                    raise ValueError(f'The second element of tuple `{path[1]}` is not boolean.')
                if model and path[0].class_ != model:
                    raise KeyError(
                        f'Incorrect path `{path[0]}`: {model.__name__} does not have `{path[0].key}` relationship.'
                    )
                options.append(selectinload(path[0]) if path[1] else subqueryload(path[0]))
            else:
                if model and path.class_ != model:
                    raise KeyError(
                        f'Incorrect path `{path}`: {model.__name__} does not have `{path.key}` relationship.'
                    )
                options.append(subqueryload(path))

        return self.options(*options)

    def with_schema(
        self,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict],
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
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.first()
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

        return self.options(*self.eager_expr(schema or {}))

    async def execute(self) -> Result[Any]:
        """Executes the query and returns a `sqlalchemy.engine.Result`
        instance containing the results.
        """

        async with self.AsyncSession() as session:
            return await session.execute(self._query)

    async def scalars(self) -> ScalarResult[_T]:
        """Returns a `sqlalchemy.engine.ScalarResult` instance
        containing all results.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> scalar_result = await async_query.scalars()
        >>> scalar_result
        # <sqlalchemy.engine.ScalarResult>
        >>> users = scalar_result.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> scalar_result = await async_query.filter(name='John Doe').scalars()
        >>> users = scalar_result.all()
        >>> users
        # [<User 2>]
        """

        return (await self.execute()).scalars()

    @overload
    async def first(self) -> _T | None: ...

    @overload
    async def first(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def first(self, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def first(self, scalar: bool) -> _T | Row[tuple[Any, ...]] | None: ...

    async def first(self, scalar: bool = True):
        """Fetches the first row or `None` if no results are found.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.first()
        >>> user
        # <User 1>
        >>> user = await async_query.first(scalar=False)
        >>> user
        # (<User 1>,)
        """

        self.limit(1)

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
        """Fetches one row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.filter(name='John Doe').one()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').one(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await async_query.filter(name='Unknown').one()
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

        if scalar:
            return (await self.scalars()).one()

        return (await self.execute()).one()

    @overload
    async def one_or_none(self) -> _T | None: ...

    @overload
    async def one_or_none(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def one_or_none(self, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def one_or_none(self, scalar: bool) -> _T | Row[tuple[Any, ...]] | None: ...

    async def one_or_none(self, scalar: bool = True):
        """Fetches one row or `None` if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.filter(name='John Doe').one_or_none()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').one_or_none(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await async_query.filter(name='Unknown').one_or_none()
        >>> user
        # None

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        if scalar:
            return (await self.scalars()).one_or_none()

        return (await self.execute()).one_or_none()

    @overload
    async def all(self) -> Sequence[_T]: ...

    @overload
    async def all(self, scalars: Literal[True]) -> Sequence[_T]: ...

    @overload
    async def all(self, scalars: Literal[False]) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    async def all(self, scalars: bool) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]: ...

    async def all(self, scalars: bool = True):
        """Fetches all rows.

        If `scalars` is `True`, returns scalar values.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await async_query.all(scalars=False)
        >>> users
        # [(<User 1>,), (<User 2>,), ...]
        """

        if scalars:
            return (await self.scalars()).all()

        return (await self.execute()).all()

    @overload
    async def unique(self) -> ScalarResult[_T]: ...

    @overload
    async def unique(self, scalars: Literal[True]) -> ScalarResult[_T]: ...

    @overload
    async def unique(self, scalars: Literal[False]) -> Result[tuple[Any, ...]]: ...

    @overload
    async def unique(self, scalars: bool) -> ScalarResult[_T] | Result[tuple[Any, ...]]: ...

    async def unique(self, scalars: bool = True):
        """Apply unique filtering to the objects returned
        in the result instance.

        If `scalars` is `True`, returns a `sqlalchemy.engine.ScalarResult`
        instance. Otherwise, returns a `sqlalchemy.engine.Result` instance.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> scalar_result = await User.unique()
        >>> users = scalar_result.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> scalar_result = await User.unique(scalars=False)
        >>> users = scalar_result.all()
        >>> users
        # [(<User 1>,), (<User 2>,), ...]
        """

        if scalars:
            return (await self.scalars()).unique()

        return (await self.execute()).unique()

    @overload
    async def unique_first(self) -> _T | None: ...

    @overload
    async def unique_first(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def unique_first(self, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def unique_first(self, scalar: bool) -> _T | Row[tuple[Any, ...]] | None: ...

    async def unique_first(self, scalar: bool = True):
        """Fetches the first unique row or `None` if no results are found.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.unique_first()
        >>> user
        # <User 1>
        >>> user = await async_query.unique_first(scalar=False)
        >>> user
        # (<User 1>,)
        """

        self.limit(1)
        return (await self.unique(scalar)).first()

    @overload
    async def unique_one(self) -> _T: ...

    @overload
    async def unique_one(self, scalar: Literal[True]) -> _T: ...

    @overload
    async def unique_one(self, scalar: Literal[False]) -> Row[tuple[Any, ...]]: ...

    @overload
    async def unique_one(self, scalar: bool) -> _T | Row[tuple[Any, ...]]: ...

    async def unique_one(self, scalar: bool = True):
        """Fetches one unique row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.filter(name='John Doe').unique_one()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').unique_one(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await async_query.filter(name='Unknown').unique_one()
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

        return (await self.unique(scalar)).one()

    @overload
    async def unique_one_or_none(self) -> _T | None: ...

    @overload
    async def unique_one_or_none(self, scalar: Literal[True]) -> _T | None: ...

    @overload
    async def unique_one_or_none(self, scalar: Literal[False]) -> Row[tuple[Any, ...]] | None: ...

    @overload
    async def unique_one_or_none(self, scalar: bool) -> _T | Row[tuple[Any, ...]] | None: ...

    async def unique_one_or_none(self, scalar: bool = True):
        """Fetches one unique row or `None` if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        If `scalar` is `True`, returns a scalar value.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.filter(name='John Doe').unique_one_or_none()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').unique_one_or_none(scalar=False)
        >>> user
        # (<User 1>,)
        >>> user = await async_query.filter(name='Unknown').unique_one_or_none()
        >>> user
        # None

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        return (await self.unique(scalar)).one_or_none()

    @overload
    async def unique_all(self) -> Sequence[_T]: ...

    @overload
    async def unique_all(self, scalars: Literal[True]) -> Sequence[_T]: ...

    @overload
    async def unique_all(self, scalars: Literal[False]) -> Sequence[Row[tuple[Any, ...]]]: ...

    @overload
    async def unique_all(self, scalars: bool) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]: ...

    async def unique_all(self, scalars: bool = True):
        """Fetches all unique rows.

        If `scalars` is `True`, returns scalar values.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.unique_all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await async_query.unique_all(scalars=False)
        >>> users
        # [(<User 1>,), (<User 2>,), ...]
        """

        return (await self.unique(scalars)).all()

    def __str__(self) -> str:
        """Returns the raw SQL query."""

        return str(self._query)

    def _split_columns_and_attrs(
        self,
        columns_and_attrs: Sequence[_ColumnExpressionOrStrLabelArgument[Any]],
    ) -> tuple[list[str], list[str]]:
        """Splits columns and attrs.

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
