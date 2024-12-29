"""This module defines `ActiveRecordMixin` class."""

from typing import Any, Self, Sequence, cast

from sqlalchemy.orm import Query
from sqlalchemy.sql import FromClause, select
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression
from sqlalchemy.exc import InvalidRequestError, NoResultFound
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from .utils import classproperty
from .session import SessionMixin
from .async_query import AsyncQuery
from .smart_query import SmartQueryMixin


class ActiveRecordMixin(SessionMixin, SmartQueryMixin):
    """Mixin for ActiveRecord style models.

    Example:
    ```python
        from sqlalchemy import Mapped, mapped_column
        from sqlactive import ActiveRecordMixin

        class BaseModel(ActiveRecordMixin):
            __abstract__ = True

        class User(BaseModel):
            __tablename__ = 'users'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
    ```

    Usage:
    >>> bob = User.create(name='Bob')
    >>> bob
    # <User #1>
    >>> bob.name
    # Bob
    >>> User.where(name='Bob').all()
    # [<User #1>]
    >>> User.get(1)
    # <User #1>
    >>> bob.update(name='Bob2')
    >>> bob.name
    # Bob2
    >>> bob.delete()
    >>> User.all()
    # []

    Methods
    -------
    ### Creation, updating, and deletion

    `save()`
        Saves the row.
    `create(**kwargs)`
        Creates a new row.
    `insert(**kwargs)`
        A synonym for `create`.
    `add(**kwargs)`
        A synonym for `create`.
    `update(**kwargs)`
        Updates the row.
    `edit(**kwargs)`
        A synonym for `update`.
    `delete()`
        Deletes the row.
    `remove()`
        A synonym for `delete`.
    `save_all(rows, refresh)`
        Saves many rows.
    `create_all(rows, refresh)`
        Creates many rows.
    `update_all(rows, refresh)`
        Updates many rows.
    `delete_all(rows)`
        Deletes many rows.
    `destroy()`
        Deletes multiple rows by primary key.

    ### Query building

    `options(*args)`
        Applies the given list of mapper options.
    `filter(*criterion, **filters)`
        Creates filtered query.
    `where(*criterion, **filters)`
        A synonym for `filter`.
    `find(*criterion, **filters)`
        A synonym for `filter`.
    `order_by(*columns)`
        Applies one or more ORDER BY criteria to the query.
    `sort(*columns)`
        A synonym for `order_by`.
    `offset(offset)`
        Creates query with an OFFSET clause.
    `skip(skip)`
        A synonym for `offset`.
    `limit(limit)`
        Creates query with a LIMIT clause.
    `take(take)`
        A synonym for `limit`.
    `join(*paths)`
        Joined eager loading using LEFT OUTER JOIN.
    `with_subquery(*paths)`
        Subqueryload or Selectinload eager loading.
    `with_schema(schema)`
        Joined, subqueryload and selectinload eager loading.
    `smart_query(criterion, filters, sort_columns, sort_attrs, schema)`
        Builds a smart query.

    ### Fetching and reading

    `get(pk)`
        Fetches a row by primary key or `None` if no results are found.
    `get_or_fail(pk)`
        Fetches a row by primary key or raises an exception
        if no results are found.
    `find_one(*criterion, **filters)`
        A synonym for `filter` but returns only one row or
        raises an exception if no results are found.
    `find_one_or_none(*criterion, **filters)`
        A synonym for `filter` but returns only one row or
        `None` if no results are found.
    `find_all(*criterion, **filters)`
        A synonym for `filter` but returns all results.
    `scalars()`
        Returns an `ScalarResult` object with all rows.
    `first()`
        Fetches the first row or `None` if no results are found.
    `one()`
        Fetches one row or raises an exception if no results are found.
    `one_or_none()`
        Fetches one row or `None` if no results are found.
    `fetch_one()`
        A synonym for `one`.
    `fetch_one_or_none()`
        A synonym for `one_or_none`.
    `all()`
        Fetches all rows.
    `fetch_all()`
        A synonym for `all`.
    `to_list()`
        A synonym for `all`.
    `unique()`
        Returns an `ScalarResult` object with all unique rows.
    `unique_all()`
        Fetches all unique rows.
    `unique_first()`
        Fetches the first unique row or `None` if no results are found.
    `unique_one()`
        Fetches one unique row or raises an exception if no results are found.
    `unique_one_or_none()`
        Fetches one unique row or `None` if no results are found.

    ### Additional methods

    `fill(**kwargs)`
        Fills the object with values from `kwargs`.
    """

    __abstract__ = True

    def fill(self, **kwargs):
        """Fills the object with values from `kwargs`
        without saving to the database.

        Raises
        ------
        KeyError
            If attribute doesn't exist.
        """

        for name in kwargs.keys():
            if name in self.settable_attributes:
                setattr(self, name, kwargs[name])
            else:
                raise KeyError(f'Attribute `{name}` does not exist')
        return self

    async def save(self):
        """Saves the row."""

        async with self._AsyncSession() as session:
            try:
                session.add(self)
                await session.commit()
                await session.refresh(self)
                return self
            except Exception as error:
                await session.rollback()
                raise error

    async def update(self, **kwargs):
        """Updates the row."""

        return await self.fill(**kwargs).save()

    async def edit(self, **kwargs):
        """A synonym for `update`."""

        return await self.update(**kwargs)

    async def delete(self):
        """Deletes the row."""

        async with self._AsyncSession() as session:
            try:
                await session.delete(self)
                await session.commit()
            except Exception as error:
                await session.rollback()
                raise error

    async def remove(self):
        """A synonym for `delete`."""

        return await self.delete()

    @classmethod
    async def create(cls, **kwargs):
        """Creates a new row."""

        return await cls().fill(**kwargs).save()

    @classmethod
    async def insert(cls, **kwargs):
        """A synonym for `create`."""

        return await cls.create(**kwargs)

    @classmethod
    async def add(cls, **kwargs):
        """A synonym for `create`."""

        return await cls.create(**kwargs)

    @classmethod
    async def save_all(cls, rows: Sequence[Self], refresh: bool = False):
        """Saves many rows.

        Parameters
        ----------
        rows : Sequence[Self]
            Rows to be saved.
        refresh : bool, optional
            Whether to refresh the rows after saving, by default False.
            NOTE: Refreshing may be expensive.
        """

        async with cls._AsyncSession() as session:
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
    async def create_all(cls, rows: Sequence[Self], refresh: bool = False):
        """Creates many rows.

        This is mostly a shortcut for `save_all`
        when creating new rows.
        """

        return await cls.save_all(rows, refresh)

    @classmethod
    async def update_all(cls, rows: Sequence[Self], refresh: bool = False):
        """Updates many rows.

        This is mostly a shortcut for `save_all`
        when updating existing rows.
        """

        return await cls.save_all(rows, refresh)

    @classmethod
    async def delete_all(cls, rows: Sequence[Self]):
        """Deletes many rows.

        Parameters
        ----------
        rows : Sequence[Self]
            Rows to be deleted.
        """

        async with cls._AsyncSession() as session:
            try:
                for row in rows:
                    await session.delete(row)
                await session.commit()
            except Exception as error:
                await session.rollback()
                raise error

    @classmethod
    async def destroy(cls, *ids: object):
        """Deletes multiple rows by primary key."""

        primary_key_name = cls._get_primary_key_name()
        if not primary_key_name:
            return None
        async with cls._AsyncSession() as session:
            try:
                query = cls._build_smart_query(cls._query, filters={f'{primary_key_name}__in': ids})
                rows = (await session.execute(query)).scalars().all()
                for row in rows:
                    await session.delete(row)
                await session.commit()
            except Exception as error:
                await session.rollback()
                raise error

    @classmethod
    async def get(cls, pk: object):
        """Fetches a row by primary key or `None`
        if no results are found.

        Example:
        >>> user = await User.get(1)
        >>> user
        # <User 1>
        >>> user = await User.get(3)  # Does not exist
        >>> user
        # Traceback (most recent call last):
        #     ...
        # NoResultFound: 'User with id `3` was not found.'

        Parameters
        ----------
        pk : object
            Primary key.

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        primary_key_name = cls._get_primary_key_name()
        if not primary_key_name:
            return None
        async_query = cls._get_async_query()
        return await async_query.filter(**{primary_key_name: pk}).one_or_none()

    @classmethod
    async def get_or_fail(cls, pk: object):
        """Fetches a row by primary key or raises an exception
        if no results are found.

        Example:
        >>> user = await User.get_or_fail(1)
        >>> user
        # <User 1>
        >>> user = await User.get_or_fail(3)  # Does not exist
        >>> user
        # None

        Parameters
        ----------
        pk : object
            Primary key.

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        cursor = await cls.get(pk)
        if cursor:
            return cursor
        else:
            raise NoResultFound(f'{cls.__name__} with id `{pk}` was not found.')

    @classmethod
    def options(cls, *args: ExecutableOption):
        """Creates a query and applies the given list of mapper options.

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
        >>> users = await User.options(joinedload(User.posts)).unique_all()
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

        async_query = cls._get_async_query()
        return async_query.options(*args)

    @classmethod
    def filter(cls, *criterion: ColumnElement[Any], **filters: Any):
        """Creates a filtered query using SQLAlchemy or Django-style filters.

        Creates the WHERE clause of the query.

        It supports both Django-like syntax and SQLAlchemy syntax.

        Example using Django-like syntax:
        >>> users = await User.filter(name__like='%John%').all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.filter(name__like='%John%', age=30).all()
        >>> users
        # [<User 2>]

        Example using SQLAlchemy syntax:
        >>> users = await User.filter(User.name == 'John Doe').all()
        >>> users
        # [<User 2>]

        Example using both:
        >>> users = await User.filter(User.age == 30, name__like='%John%').all()
        >>> users
        # [<User 2>]
        """

        async_query = cls._get_async_query()
        return async_query.filter(*criterion, **filters)

    @classmethod
    def where(cls, *criterion: ColumnElement[Any], **filters: Any):
        """A synonym for `filter`.

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

        return cls.filter(*criterion, **filters)

    @classmethod
    def find(cls, *criterion: ColumnElement[Any], **filters: Any):
        """A synonym for `filter`.

        Example using Django-like syntax:
        >>> users = await User.find(name__like='%John%').all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.find(name__like='%John%', age=30).all()
        >>> users
        # [<User 2>]

        Example using SQLAlchemy syntax:
        >>> users = await User.find(User.name == 'John Doe').all()
        >>> users
        # [<User 2>]

        Example using both:
        >>> users = await User.find(User.age == 30, name__like='%John%').all()
        >>> users
        # [<User 2>]
        """

        return cls.filter(*criterion, **filters)

    @classmethod
    async def find_one(cls, *criterion: ColumnElement[Any], **filters: Any):
        """Finds a single row matching the criteria.

        If multiple results are found, raises MultipleResultsFound.

        This is same as calling `await cls.find(*criterion, **filters).one()`

        Example using Django-like syntax:
        >>> user = await User.find_one(name__like='%John%', age=30)
        >>> user
        # <User 2>
        >>> user = await User.find_one(name__like='%Jane%')  # Does not exist
        >>> user
        # Traceback (most recent call last):
        #     ...
        # NoResultFound: 'No result found.'

        Example using SQLAlchemy syntax:
        >>> user = await User.find_one(User.name == 'John Doe').all()
        >>> user
        # <User 2>

        Example using both:
        >>> user = await User.find_one(User.age == 30, name__like='%John%').all()
        >>> user
        # <User 2>

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        return await cls.find(*criterion, **filters).one()

    @classmethod
    async def find_one_or_none(cls, *criterion: ColumnElement[Any], **filters: Any):
        """Finds a single row matching the criteria or `None`.

        If multiple results are found, raises MultipleResultsFound.

        This is same as calling `await cls.find(*criterion, **filters).one_or_none()`

        Example using Django-like syntax:
        >>> user = await User.find_one_or_none(name__like='%John%', age=30)
        >>> user
        # <User 2>
        >>> user = await User.find_one_or_none(name__like='%Jane%')  # Does not exist
        >>> user
        # None

        Example using SQLAlchemy syntax:
        >>> user = await User.find_one_or_none(User.name == 'John Doe').all()
        >>> user
        # <User 2>

        Example using both:
        >>> user = await User.find_one_or_none(User.age == 30, name__like='%John%').all()
        >>> user
        # <User 2>

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        return await cls.find(*criterion, **filters).one_or_none()

    @classmethod
    async def find_all(cls, *criterion: ColumnElement[Any], **filters: Any):
        """Finds all rows matching the criteria.

        This is same as calling `await cls.find(*criterion, **filters).all()`

        Example using Django-like syntax:
        >>> users = await User.find_all(name__like='%John%')
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.find_all(name__like='%John%', age=30)
        >>> users
        # [<User 2>]

        Example using SQLAlchemy syntax:
        >>> users = await User.find_all(User.name == 'John Doe')
        >>> users
        # [<User 2>]

        Example using both:
        >>> users = await User.find_all(User.age == 30, name__like='%John%')
        >>> users
        # [<User 2>]
        """

        return await cls.find(*criterion, **filters).all()

    @classmethod
    def order_by(cls, *columns: str | InstrumentedAttribute | UnaryExpression):
        """Creates a query with ORDER BY clause.

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
        >>> posts = await Post.order_by(desc(Post.rating), Post.user.name).all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]
        """

        async_query = cls._get_async_query()
        return async_query.order_by(*columns)

    @classmethod
    def sort(cls, *columns: str | InstrumentedAttribute | UnaryExpression):
        """A synonym for `order_by`.

        Example using Django-like syntax:
        >>> users = await User.sort('-created_at').all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> posts = await Post.sort('-rating', 'user___name').all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]

        Example using SQLAlchemy syntax:
        >>> users = await User.sort(User.created_at.desc()).all()
        >>> users
        # [<User 100>, <User 99>, ...]
        >>> posts = await Post.sort(desc(Post.rating), Post.user.name).all()
        >>> posts
        # [<Post 1>, <Post 4>, ...]
        """

        return cls.order_by(*columns)

    @classmethod
    def offset(cls, offset: int):
        """Creates query with an OFFSET clause.

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

        async_query = cls._get_async_query()
        return async_query.offset(offset)

    @classmethod
    def skip(cls, skip: int):
        """A synonym for `offset`.

        Parameters
        ----------
        skip : int
            Offset.

        Example:
        >>> users = await User.skip(10).all()
        >>> users
        # [<User 11>, <User 12>, ...]
        """

        return cls.offset(skip)

    @classmethod
    def limit(cls, limit: int):
        """Creates query with a LIMIT clause.

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

        async_query = cls._get_async_query()
        return async_query.limit(limit)

    @classmethod
    def take(cls, take: int):
        """A synonym for `limit`.

        Parameters
        ----------
        take : int
            Limit.

        Example:
        >>> users = await User.take(2).all()
        >>> users
        # [<User 1>, <User 2>]
        """

        return cls.limit(take)

    @classmethod
    def join(cls, *paths: QueryableAttribute | tuple[QueryableAttribute, bool]):
        """Creates a query with LEFT OUTER JOIN eager loading.

        When a tuple is passed, the second element must be boolean.
        If it is `True`, the join is INNER JOIN, otherwise LEFT OUTER JOIN.

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
        """

        async_query = cls._get_async_query()
        return async_query.join(*paths, model=cls)

    @classmethod
    def with_subquery(cls, *paths: QueryableAttribute | tuple[QueryableAttribute, bool]):
        """Creates a query with subquery or selectin loading.

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

        async_query = cls._get_async_query()
        return async_query.with_subquery(*paths, model=cls)

    @classmethod
    def with_schema(
        cls, schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
    ):
        """Creates a query with complex eager loading schema.

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

        async_query = cls._get_async_query()
        return async_query.with_schema(schema)

    @classmethod
    async def scalars(cls):
        """Returns an `ScalarResult` object with all rows.

        Example:
        >>> scalar_result = await User.scalars()
        >>> scalar_result
        # <sqlalchemy.engine.result.ScalarResult>
        >>> users = scalar_result.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> scalar_result = await User.filter(name='John Doe').scalars()
        >>> users = scalar_result.all()
        >>> users
        # [<User 2>]
        """

        async_query = cls._get_async_query()
        return await async_query.scalars()

    @classmethod
    async def first(cls):
        """Fetches the first row or `None` if no results are found.

        Example:
        >>> user = await User.first()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').first()
        >>> user
        # <User 2>
        """

        async_query = cls._get_async_query()
        return await async_query.first()

    @classmethod
    async def one(cls):
        """Fetches one row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        Example:
        >>> user = await User.one()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').one()
        >>> user
        # <User 2>

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls._get_async_query()
        return await async_query.one()

    @classmethod
    async def one_or_none(cls):
        """Fetches one row or `None` if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        Example:
        >>> user = await User.one_or_none()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').one_or_none()
        >>> user
        # <User 2>

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls._get_async_query()
        return await async_query.one_or_none()

    @classmethod
    async def fetch_one(cls):
        """A synonym for `one`.

        Example:
        >>> user = await User.fetch_one()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').fetch_one()
        >>> user
        # <User 2>
        """

        return await cls.one()

    @classmethod
    async def fetch_one_or_none(cls):
        """A synonym for `one_or_none`.

        Example:
        >>> user = await User.fetch_one_or_none()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').fetch_one_or_none()
        >>> user
        # <User 2>
        """

        return await cls.one_or_none()

    @classmethod
    async def all(cls):
        """Fetches all rows.

        Example:
        >>> users = await User.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        """

        async_query = cls._get_async_query()
        return await async_query.all()

    @classmethod
    async def fetch_all(cls):
        """A synonym for `all`.

        Example:
        >>> users = await User.fetch_all()
        >>> users
        # [<User 1>, <User 2>, ...]
        """

        return await cls.all()

    @classmethod
    async def to_list(cls):
        """A synonym for `all`.

        Example:
        >>> users = await User.to_list()
        >>> users
        # [<User 1>, <User 2>, ...]
        """

        return await cls.all()

    @classmethod
    async def unique(cls):
        """Returns an `ScalarResult` object with all unique rows.

        Example:
        >>> scalar_result = await User.unique()
        >>> scalar_result
        # <sqlalchemy.engine.result.ScalarResult>
        >>> users = scalar_result.all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> scalar_result = await User.filter(name='John Doe').unique()
        >>> users = scalar_result.all()
        >>> users
        # [<User 2>]
        """

        async_query = cls._get_async_query()
        return await async_query.unique()

    @classmethod
    async def unique_all(cls):
        """Fetches all unique rows.

        Example:
        >>> users = await User.unique_all()
        >>> users
        # [<User 1>, <User 2>, ...]
        >>> users = await User.filter(name='John Doe').unique_all()
        >>> users
        # [<User 2>]
        """

        async_query = cls._get_async_query()
        return await async_query.unique_all()

    @classmethod
    async def unique_first(cls):
        """Fetches the first unique row or `None`
        if no results are found.

        Example:
        >>> user = await User.unique_first()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').unique_first()
        >>> user
        # <User 2>
        """

        async_query = cls._get_async_query()
        return await async_query.unique_first()

    @classmethod
    async def unique_one(cls):
        """Fetches one unique row or raises an exception
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        Example:
        >>> user = await User.unique_one()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').unique_one()
        >>> user
        # <User 2>

        Raises
        ------
        NoResultFound
            If no result is found.
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls._get_async_query()
        return await async_query.unique_one()

    @classmethod
    async def unique_one_or_none(cls):
        """Fetches one unique row or `None`
        if no results are found.

        If multiple results are found, raises `MultipleResultsFound`.

        Example:
        >>> user = await User.unique_one_or_none()
        >>> user
        # <User 1>
        >>> user = await User.filter(name='John Doe').unique_one_or_none()
        >>> user
        # <User 2>

        Raises
        ------
        MultipleResultsFound
            If multiple results are found.
        """

        async_query = cls._get_async_query()
        return await async_query.unique_one_or_none()

    @classmethod
    def smart_query(
        cls,
        criterion: tuple[ColumnElement[Any], ...] | None = None,
        filters: dict[str, Any] | list[dict[str, Any]] | None = None,
        sort_columns: Sequence[InstrumentedAttribute | UnaryExpression] | None = None,
        sort_attrs: Sequence[str] | None = None,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
    ):
        """Creates a query combining filtering, sorting, and eager loading.

        Does magic Django-like joins like `post___user___name__startswith='Bob'`
        (see https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships)

        Does filtering, sorting and eager loading at the same time.
        And if, say, filters and sorting need the same join,
        it will be done only once.

        It also supports SQLAlchemy syntax filter expressions like
        >>> db.query(User).filter(User.id == 1, User.name == 'Bob')
        >>> db.query(User).filter(or_(User.id == 1, User.name == 'Bob'))

        by passing them as `criterion` argument.

        NOTE: To get more information about the usage, see documentation of
        `filter_expr`, `order_expr` and `eager_expr` methods.

        Parameters
        ----------
        criterion : tuple[ColumnElement[Any], ...] | None, optional
            SQLAlchemy syntax filter expressions, by default None.
        filters : dict | list | None, optional
            Filter expressions, by default None.
        sort_columns : Sequence[InstrumentedAttribute | UnaryExpression] | None, optional
            Standalone sort columns, by default None.
        sort_attrs : Sequence[str] | None, optional
            Django-like sort expressions, by default None.
        schema : dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None, optional
            Schema for the eager loading, by default None.

        Returns
        -------
        AsyncQuery
            Async query object.
        """

        query = cls._build_smart_query(
            query=cls._query,
            criterion=criterion,
            filters=filters,
            sort_columns=sort_columns,
            sort_attrs=sort_attrs,
            schema=schema,
        )
        return cls._get_async_query(query)

    @classmethod
    def _get_async_query(cls, query: Query | None = None):
        """Returns an `AsyncQuery` object.

        Parameters
        ----------
        query : Query | None, optional
            SQLAlchemy query for the model, by default None.
        """

        if query is None:
            return AsyncQuery[cls](cls._query, cls._session)
        return AsyncQuery[cls](query, cls._session)

    @classmethod
    def _get_primary_key_name(cls) -> str:
        """Gets the primary key of the model.

        NOTE: This method can only be used if the model has a single primary key.

        Returns
        -------
        str
            The name of the primary key.

        Raises
        ------
        InvalidRequestError
            If the model does not have a primary key or has a composite primary key.
        """

        primary_keys = cast(FromClause, cls.__table__.primary_key).columns
        if primary_keys is None:
            raise InvalidRequestError(f'Model {cls.__name__} does not have a primary key.')
        if len(primary_keys) > 1:
            raise InvalidRequestError(f'Model {cls.__name__} has a composite primary key.')
        return primary_keys[0].name

    @classproperty
    def _query(cls) -> Query:
        """Returns a query for the model."""

        return select(cls)  # type: ignore
