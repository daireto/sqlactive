# Async Query

The `AsyncQuery` class is an Async wrapper for `sqlalchemy.sql.Select`.

It implements the functionality of both [`Session`](session-mixin.md) and [`Smart Queries`](smart-query-mixin.md) mixins.

## Usage

The `AsyncQuery` class provides a set of helper methods for asynchronously executing the query.

Example of usage:

```python
    query = select(User)
    async_query = AsyncQuery(query)
    async_query = async_query.where(name__like='%John%').sort('-created_at').limit(2)
    users = await async_query.all()
    >>> users
    # [<User 1>, <User 2>]
```

To get the `sqlalchemy.sql.Select` instance to use native SQLAlchemy methods
use the `query` property:

```python
    query = select(User)
    async_query = AsyncQuery(query)
    async_query.query
    # <sqlalchemy.sql.Select>
```

???+ warning

    If a `NoSessionError` is raised, it means that there is no session
    associated with the `AsyncQuery` instance. This can happen
    if the `set_session` method of the base model has not been called
    or if the model has not been initialized with a session.

    In this case, you must provide a session by calling the `set_session`
    either from the model or the `AsyncQuery` instance.

    Calling `set_session` from the model:

    ```python
    User.set_session(session)
    query = select(User)
    async_query = AsyncQuery(query)
    ```

    Calling `set_session` from the `AsyncQuery` instance:

    ```python
    query = select(User)
    async_query = AsyncQuery(query)
    async_query.set_session(User._session)
    ```

## API Reference

### Attributes

#### query
```python
query: Select[tuple[Any, ...]]
```

> The wrapped `sqlalchemy.sql.Select` instance.

> **Example:**
```python
query = select(User)
async_query = AsyncQuery(query)
async_query.query
# <sqlalchemy.sql.Select>

async_query.query = async_query.query.limit(10).order_by(User.age.desc())
users = await async_query.all()
```

### Class Methods

#### select
```python
@classmethod
def select(cls, *entities: _ColumnsClauseArgument[Any]) -> Self
```

> Replaces the columns clause with the given entities.

> The existing set of FROMs are maintained, including those
> implied by the current columns clause.

> **Parameters:**

> - `entities`: Entities to be selected.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> async_query.order_by('-created_at')
> # SELECT users.id, users.username, users.name, ... FROM users ORDER BY users.created_at DESC
>
> async_query.select(User.name, User.age)
> # SELECT users.name, users.age FROM users ORDER BY users.created_at DESC
> ```

### Instance Methods

#### options
```python
def options(*args: ExecutableOption) -> Self
```

> Applies the given list of mapper options.

> ???+ warning
>
>     Quoting from [SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading):
>
>         When including `joinedload()` in reference to a one-to-many or
>         many-to-many collection, the `Result.unique()` method or related
>         (i.e. `unique_all()`) must be applied to the returned result, which
>         will make the incoming rows unique by primary key that otherwise are
>         multiplied out by the join.
>         SQLAlchemy will raise an error if this is not present.
>
>         This is not automatic in modern SQLAlchemy, as it changes the behavior
>         of the result set to return fewer ORM objects than the statement would
>         normally return in terms of number of rows. Therefore SQLAlchemy keeps
>         the use of Result.unique() explicit, so there is no ambiguity that the
>         returned objects are made unique on primary key.
>
>     To learn more about options, see
>     [`sqlalchemy.orm.Query.options`](https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.options) docs.

> **Parameters:**

> - `args`: Mapper options.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> users = await async_query.options(joinedload(User.posts)).unique_all()
> user = await async_query.options(joinedload(User.posts)).first()
> users = await async_query.options(subqueryload(User.posts)).all()
> ```

#### where
```python
def where(*criteria: _ColumnExpressionArgument[bool], **filters: Any) -> Self
```

> Applies one or more WHERE criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters:**

> - `criteria`: SQLAlchemy style filter expressions.
> - `filters`: Django-style filters.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> # SQLAlchemy style
> users = await async_query.where(User.age >= 18).all()
>
> # Django style
> users = await async_query.where(age__gte=18).all()
>
> # Mixed
> users = await async_query.where(User.age >= 18, name__like='%Bob%').all()
> ```

#### filter
```python
def filter(*criterion: _ColumnExpressionArgument[bool], **filters: Any) -> Self
```

> Synonym for `where()`.

#### find
```python
def find(*criterion: _ColumnExpressionArgument[bool], **filters: Any) -> Self
```

> Synonym for `where()`.

#### order_by
```python
def order_by(*columns: _ColumnExpressionOrStrLabelArgument[Any]) -> Self
```

> Applies one or more ORDER BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters:**

> - `columns`: Django-like or SQLAlchemy sort expressions.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> # SQLAlchemy style
> users = await async_query.order_by(User.created_at.desc(), User.name).all()
>
> # Django style
> users = await async_query.order_by('-created_at', 'name').all()
>
> # Mixed
> users = await async_query.order_by('-created_at', User.name.asc()).all()
> ```

#### sort
```python
def sort(*columns: _ColumnExpressionOrStrLabelArgument[Any]) -> Self
```

> Synonym for `order_by()`.

#### group_by
```python
def group_by(
    *columns: _ColumnExpressionOrStrLabelArgument[Any],
    select_columns: Sequence[_ColumnsClauseArgument[Any]] | None = None,
) -> Self
```

> Applies one or more GROUP BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> It is recommended to select specific columns. You can use
> the `select_columns` parameter to select specific columns.

> ???+ danger
>
>     When selecting specific columns with the `select_columns` parameter,
>     the query will be completely reset and overwritten with a new query.
>     Every WHERE, ORDER BY, GROUP BY, LIMIT, OFFSET, etc. will be cancelled.
>     So, make sure to call this method before calling any other method when
>     using `select_columns` parameter to select specific columns.

> **Parameters:**

> - `columns`: Django-like or SQLAlchemy columns.
> - `select_columns`: Columns to be selected.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> from sqlalchemy.sql import text
> from sqlalchemy.sql.functions import func
>
> query = select(User)
> async_query = AsyncQuery(query)
>
> columns = (User.age, func.count(User.age))
> async_query = async_query.group_by(User.age, select_columns=columns)
> rows = await async_query.all(scalars=False)
>
> # Group by with relations
> query = select(Post)
> async_query = AsyncQuery(query)
> columns = (Post.rating, text('users_1.name'), func.count(Post.title))
> async_query = async_query.group_by('rating', 'user___name', select_columns=columns)
> rows = async_query.all(scalars=False)
> ```

#### offset
```python
def offset(offset: int) -> Self
```

> Applies an OFFSET clause to the query.

> **Parameters:**

> - `offset`: Number of rows to skip.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Raises:**

> - `ValueError`: If offset is negative.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> users = await async_query.offset(10).all()
> ```

#### skip
```python
def skip(skip: int) -> Self
```

> Synonym for `offset()`.

#### limit
```python
def limit(limit: int) -> Self
```

> Applies a LIMIT clause to the query.

> **Parameters:**

> - `limit`: Maximum number of rows to return.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Raises:**

> - `ValueError`: If limit is negative.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> users = await async_query.limit(5).all()
> ```

#### take
```python
def take(take: int) -> Self
```

> Synonym for `limit()`.

#### top
```python
def top(top: int) -> Self
```

> Synonym for `limit()`.

#### join
```python
def join(
    *paths: QueryableAttribute | tuple[QueryableAttribute, bool],
    model: type[_T] | None = None
) -> Self
```

> Joined eager loading using LEFT OUTER JOIN.

> When a tuple is passed, the second element must be boolean, and
> if `True`, the join is `INNER JOIN`, otherwise `LEFT OUTER JOIN`.

> **Parameters:**

> - `paths`: Relationship attributes to join.
> - `model`: If given, checks that each path belongs to this model.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> query = select(Comment)
> async_query = AsyncQuery(query)
>
> comments = await async_query.join(
>     Comment.user,
>     (Comment.post, True),  # True means INNER JOIN
>     model=Comment   # Checks that Comment.user and Comment.post belongs to Comment
> ).all()
>
> comments = await async_query.join(
>     Post.user,
>     model=Comment   # Post.user does not belong to Comment, so it will raise an error
> ).all()
> ```

#### with_subquery
```python
def with_subquery(
    *paths: QueryableAttribute | tuple[QueryableAttribute, bool],
    model: type[_T] | None = None
) -> Self
```

> Subqueryload or Selectinload eager loading.

> Emits a second `SELECT` statement (Subqueryload) for each relationship
> to be loaded, across all result objects at once.

> When a tuple is passed, the second element must be boolean.
> If it is `True`, the eager loading strategy is `SELECT IN` (Selectinload),
> otherwise `SELECT JOIN` (Subqueryload).

> ???+ warning
>
>     A query which makes use of `subqueryload()` in conjunction with a limiting
>     modifier such as `Query.limit()` or `Query.offset()` should always include
>     `Query.order_by()` against unique column(s) such as the primary key,
>     so that the additional queries emitted by `subqueryload()` include the same
>     ordering as used by the parent query. Without it, there is a chance that
>     the inner query could return the wrong rows, as specified in
>     [SQLAlchemy docs](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering).
>
>     ```python
>     query = select(User)
>     async_query = AsyncQuery(query)
>
>     # incorrect, no ORDER BY
>     async_query.options(subqueryload(User.addresses)).first()
>     # incorrect if User.name is not unique
>     async_query.options(subqueryload(User.addresses)).order_by(User.name).first()
>     # correct
>     async_query.options(subqueryload(User.addresses)).order_by(
>         User.name, User.id
>     ).first()
>     ```

> **Parameters:**

> - `paths`: Relationship attributes to load.
> - `model`: If given, checks that each path belongs to this model.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> users = await async_query.with_subquery(
>     User.posts,
>     (User.comments, True)  # True means selectin loading
>     model=User   # Checks that User.posts and User.comments belongs to User
> ).all()
> ```

> ```python
> users = await async_query.with_subquery(
>     Comment.posts,
>     model=User   # Comment.posts does not belong to User, so it will raise an error
> ).all()
> ```

#### with_schema
```python
def with_schema(
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
) -> Self
```

> Joined, subqueryload and selectinload eager loading.

> Useful for complex cases where you need to load nested relationships in
> separate queries.

> **Parameters:**

> - `schema`: Dictionary defining the loading strategy.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Example:**

> ```python
> from sqlactive import JOINED, SUBQUERY
>
> query = select(User)
> async_query = AsyncQuery(query)
>
> schema = {
>     User.posts: JOINED,
>     User.comments: (SUBQUERY, {
>         Comment.user: JOINED
>     })
> }
> users = await async_query.with_schema(schema).all()
> ```

#### execute
```python
async def execute() -> Result[Any]
```

> Executes the query and returns a `sqlalchemy.engine.Result`
> instance containing the results.

> **Parameters:**

> - `params`: SQLAlchemy statement execution parameters.

> **Returns:**

> - `sqlalchemy.engine.Result[Any]`: Result of the query.

#### scalars
```python
async def scalars() -> ScalarResult[_T]
```

> Returns a `sqlalchemy.engine.ScalarResult` instance containing all results.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult[_T]`: Scalars.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> result = await async_query.scalars()  # <sqlalchemy.engine.result.ScalarResult>
> users = result.all()                  # [<User 1>, <User 2>, ...]
> ```

#### first
```python
async def first(scalar: bool = True) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches the first row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`_T`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `_T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> user = await async_query.first()             # <User 1>
> row = await async_query.first(scalar=False)  # (<User 1>,)
> ```

#### one
```python
async def one(scalar: bool = True) -> _T | Row[tuple[Any, ...]]
```

> Fetches one row or raises an exception if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`_T`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `_T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> user = await async_query.one()             # <User 1>
> row = await async_query.one(scalar=False)  # (<User 1>,)
> ```

#### one_or_none
```python
async def one_or_none(scalar: bool = True) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches one row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`_T`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `_T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> user = await async_query.one_or_none()             # <User 1>
> row = await async_query.one_or_none(scalar=False)  # (<User 1>,)
> ```

#### all
```python
async def all(scalars: bool = True) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]
```

> Fetches all rows.

> **Parameters:**

> - `scalars`: If `True`, returns scalar values (`Sequence[_T]`),
> otherwise returns rows (default: `True`).

> **Returns:**

> - `Sequence[_T]`: Sequence of instances (scalars).
> - `Sequence[sqlalchemy.engine.Row[tuple[Any, ...]]]`: Sequence of rows.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> users = await async_query.all()              # [<User 1>, <User 2>, ...]
> rows = await async_query.all(scalars=False)  # [(<User 1>,), (<User 2>,), ...]
> ```

#### count
```python
async def count() -> int
```

> Fetches the number of rows.

> **Returns:**

> - `int`: Number of rows.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> count = await async_query.count()  # 34
> ```

#### unique
```python
async def unique(scalars: bool = True) -> ScalarResult[_T] | Result[tuple[Any, ...]]
```

> Apply unique filtering to the objects returned in the result instance.

> **Parameters:**

> - `scalars`: If `True`, returns a `sqlalchemy.engine.ScalarResult`
> instance. Otherwise, returns a `sqlalchemy.engine.Result` instance.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult[_T]`: Scalars.
> - `sqlalchemy.engine.Result[tuple[Any, ...]]`: Rows.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> result = await async_query.unique()
> users = result.all()  # [<User 1>, <User 2>, ...]
> result = await async_query.unique(scalars=False)
> rows = result.all()   # [(<User 1>,), (<User 2>,), ...]
> ```

#### unique_first
```python
async def unique_first(scalar: bool = True) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches the first unique row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`_T`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `_T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> user = await async_query.unique_first()             # <User 1>
> row = await async_query.unique_first(scalar=False)  # (<User 1>,)
> ```

#### unique_one
```python
async def unique_one(scalar: bool) -> _T | Row[tuple[Any, ...]]
```

> Fetches one unique row or raises an exception if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`_T`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `_T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> user = await async_query.unique_one()             # <User 1>
> row = await async_query.unique_one(scalar=False)  # (<User 1>,)
> ```

#### unique_one_or_none
```python
async def unique_one_or_none(scalar: bool) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches one unique row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`_T`), otherwise returns a row (default: `True`).

> **Returns:**

> - `_T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> user = await async_query.unique_one_or_none()             # <User 1>
> row = await async_query.unique_one_or_none(scalar=False)  # (<User 1>,)
> ```

#### unique_all
```python
async def unique_all(scalars: bool) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]
```

> Fetches all unique rows.

> **Parameters:**

> - `scalars`: If `True`, returns scalar values (`Sequence[_T]`),
> otherwise returns rows (default: `True`).

> **Returns:**

> - `Sequence[_T]`: Sequence of instances (scalars).
> - `Sequence[sqlalchemy.engine.Row[tuple[Any, ...]]]`: Sequence of rows.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> users = await async_query.unique_all()              # [<User 1>, <User 2>, ...]
> rows = await async_query.unique_all(scalars=False)  # [(<User 1>,), (<User 2>,), ...]
> ```

#### unique_count
```python
async def unique_count() -> int
```

> Fetches the number of unique rows.

> **Returns:**

> - `int`: Number of unique rows.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
> unique_count = await async_query.unique_count()  # 34
> ```
