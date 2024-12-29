"""This module defines `AsyncQuery` class."""

from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression
from sqlalchemy.engine import Result, ScalarResult
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
from sqlalchemy.ext.asyncio import async_scoped_session, AsyncSession
from sqlalchemy.orm import Query, joinedload, subqueryload, selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from .exceptions import NoSessionError
from .smart_query import SmartQueryMixin


_T = TypeVar('_T')


class AsyncQuery(SmartQueryMixin, Generic[_T]):
    """Async wrapper for SQLAlchemy `Query` to
    create async smart queries.

    Example of usage:

    ```python
        query = select(User)
        async_query = AsyncQuery(query)
        async_query = async_query.filter(name__like='%John%').sort('-created_at').limit(2)
        users = await async_query.all()
        >>> users
        # [<User 1>, <User 2>]
    ```
    """

    __abstract__ = True

    _query: Query[_T]
    _session: async_scoped_session[AsyncSession] | None = None

    def __init__(self, query: Query, session: async_scoped_session[AsyncSession] | None = None) -> None:
        """Builds an async wrapper for SQLAlchemy `Query`.

        Parameters
        ----------
        query : Query
            SQLAlchemy query.
        session : async_scoped_session[AsyncSession] | None, optional
            Async session factory, by default None.

        NOTE: If no session is provided, a NoSessionError will be raised
        when attempting to execute the query. Please, provide a session
        by passing it in this constructor or by calling the `set_session`
        method.
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
    def _AsyncSession(self) -> async_scoped_session[AsyncSession]:
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

    def options(self, *args: ExecutableOption) -> 'AsyncQuery[_T]':
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
        >>> users = await async_query.options(joinedload(User.posts)).unique_all()
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

    def filter(self, *criterion: ColumnElement[Any], **filters: Any) -> 'AsyncQuery[_T]':
        """Filters the query.

        Creates the WHERE clause of the query.

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

        self._query = self._build_smart_query(query=self._query, criterion=criterion, filters=filters)
        return self

    def order_by(self, *columns: str | InstrumentedAttribute | UnaryExpression) -> 'AsyncQuery[_T]':
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
        >>> posts = await async_query.order_by(desc(Post.rating), Post.user.name).all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]
        """

        sort_columns = []
        sort_attrs = []
        for column in columns:
            if isinstance(column, str):
                sort_attrs.append(column)
            else:
                sort_columns.append(column)

        self._query = self._build_smart_query(query=self._query, sort_columns=sort_columns, sort_attrs=sort_attrs)
        return self

    def sort(self, *columns: str | InstrumentedAttribute | UnaryExpression) -> 'AsyncQuery[_T]':
        """A synonym for `order_by`.

        Example using Django-like syntax:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.sort('-created_at').all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> query = select(Post)
        >>> async_query = AsyncQuery(query)
        >>> posts = await async_query.sort('-rating', 'user___name').all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]

        Example using SQLAlchemy syntax:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.sort(User.created_at.desc()).all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> query = select(Post)
        >>> async_query = AsyncQuery(query)
        >>> posts = await async_query.sort(desc(Post.rating), Post.user.name).all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]
        """

        return self.order_by(*columns)

    def offset(self, offset: int) -> 'AsyncQuery[_T]':
        """Applies an OFFSET clause to the query.

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

    def skip(self, skip: int) -> 'AsyncQuery[_T]':
        """A synonym for `offset`.

        Parameters
        ----------
        skip : int
            Offset.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.skip(10).all()
        >>> users
        # [<User 11>, <User 12>, ...]
        """

        return self.offset(skip)

    def limit(self, limit: int) -> 'AsyncQuery[_T]':
        """Applies a LIMIT clause to the query.

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

    def take(self, take: int) -> 'AsyncQuery[_T]':
        """A synonym for `limit`.

        Parameters
        ----------
        take : int
            Limit.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.take(2).all()
        >>> users
        # [<User 1>, <User 2>]
        """

        return self.limit(take)

    def join(
        self, *paths: QueryableAttribute | tuple[QueryableAttribute, bool], model: type[_T] | None = None
    ) -> 'AsyncQuery[_T]':
        """Joined eager loading using LEFT OUTER JOIN.

        When a tuple is passed, the second element must be boolean.
        If it is `True`, the join is INNER JOIN, otherwise LEFT OUTER JOIN.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> comment = await async_query.join(Comment.user, (Comment.post, True)).first()
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
        self, *paths: QueryableAttribute | tuple[QueryableAttribute, bool], model: type[_T] | None = None
    ) -> 'AsyncQuery[_T]':
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
        self, schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
    ) -> 'AsyncQuery[_T]':
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

    async def execute(self, params: _CoreAnyExecuteParams | None = None, **kwargs) -> Result[Any]:
        """Executes the query.

        Parameters
        ----------
        params : _CoreAnyExecuteParams | None, optional
            SQLAlchemy statement execution parameters, by default None.

        Returns
        -------
        Result[Any]
            SQLAlchemy `Result` object.
        """

        async with self._AsyncSession() as session:
            return await session.execute(self._query, params, **kwargs)

    async def scalars(self) -> ScalarResult[_T]:
        """Returns an `ScalarResult` object with all rows.

        This is same as calling `(await self.execute()).scalars()`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> scalar_result = await async_query.scalars()
        >>> scalar_result
        # <sqlalchemy.engine.result.ScalarResult>
        >>> users = scalar_result.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> scalar_result = await async_query.filter(name='John Doe').scalars()
        >>> users = scalar_result.all()
        >>> users
        # [<User 2>]
        """

        return (await self.execute()).scalars()

    async def first(self) -> _T | None:
        """Fetches the first row or `None` if no results are found.

        This is same as calling `(await self.scalars()).first()`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.first()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').first()
        >>> user
        # <User 2>
        """

        self.limit(1)
        return (await self.scalars()).first()

    async def one(self) -> _T:
        """Fetches one row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        This is same as calling `(await self.scalars()).one()`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.one()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').one()
        >>> user
        # <User 2>

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        return (await self.scalars()).one()

    async def one_or_none(self) -> _T | None:
        """Fetches one row or `None` if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        This is same as calling `(await self.scalars()).one_or_none()`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.one_or_none()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').one_or_none()
        >>> user
        # <User 2>

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        return (await self.scalars()).one_or_none()

    async def fetch_one(self) -> _T:
        """A synonym for `one`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.fetch_one()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').fetch_one()
        >>> user
        # <User 2>
        """

        return await self.one()

    async def fetch_one_or_none(self) -> _T | None:
        """A synonym for `one_or_none`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.fetch_one_or_none()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').fetch_one_or_none()
        >>> user
        # <User 2>
        """

        return await self.one_or_none()

    async def all(self) -> Sequence[_T]:
        """Fetches all rows.

        This is same as calling `(await self.scalars()).all()`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        """

        return (await self.scalars()).all()

    async def fetch_all(self) -> Sequence[_T]:
        """A synonym for `all`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.fetch_all()
        >>> users
        # [<User 1>, <User 2>, ...]
        """

        return await self.all()

    async def to_list(self) -> Sequence[_T]:
        """A synonym for `all`.

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.to_list()
        >>> users
        # [<User 1>, <User 2>, ...]
        """

        return await self.all()

    async def unique(self) -> ScalarResult[_T]:
        """Returns an `ScalarResult` object with all unique rows.

        This is same as calling `(await self.scalars()).unique()`

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> scalar_result = await async_query.unique()
        >>> scalar_result
        # <sqlalchemy.engine.result.ScalarResult>
        >>> users = scalar_result.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> scalar_result = await async_query.filter(name='John Doe').unique()
        >>> users = scalar_result.all()
        >>> users
        # [<User 2>]
        """

        return (await self.scalars()).unique()

    async def unique_all(self) -> Sequence[_T]:
        """Fetches all unique rows.

        This is same as calling `(await self.unique()).all()`

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> users = await async_query.unique_all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await async_query.filter(name='John Doe').unique_all()
        >>> users
        # [<User 2>]
        """

        return (await self.unique()).all()

    async def unique_first(self) -> _T | None:
        """Fetches the first unique row or `None`
        if no results are found.

        This is same as calling `(await self.unique()).first()`

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.unique_first()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').unique_first()
        >>> user
        # <User 2>
        """

        self.limit(1)
        return (await self.unique()).first()

    async def unique_one(self) -> _T:
        """Fetches one unique row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        This is same as calling `(await self.unique()).one()`

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.unique_one()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').unique_one()
        >>> user
        # <User 2>

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        return (await self.unique()).one()

    async def unique_one_or_none(self) -> _T | None:
        """Fetches one unique row or `None`
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        This is same as calling `(await self.unique()).one_or_none()`

        Example:
        >>> query = select(User)
        >>> async_query = AsyncQuery(query)
        >>> user = await async_query.unique_one_or_none()
        >>> user
        # <User 1>
        >>> user = await async_query.filter(name='John Doe').unique_one_or_none()
        >>> user
        # <User 3>

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        return (await self.unique()).one_or_none()
