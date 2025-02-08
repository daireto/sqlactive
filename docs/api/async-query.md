# Async Query

The `AsyncQuery` class is an Async wrapper for `sqlalchemy.sql.Select`.

It implements the functionality of both [`Session`](session_mixin.md) and [`Smart Queries`](smart-query-mixin.md) mixins.

## Usage

The `AsyncQuery` class provides a set of helper methods for asynchronously executing the query.

Example of usage:

```python
    query = select(User)
    async-query = AsyncQuery(query)
    async-query = async-query.filter(name__like='%John%').sort('-created_at').limit(2)
    users = await async-query.all()
    >>> users
    # [<User 1>, <User 2>]
```

To get the `sqlalchemy.sql.Select` instance to use native SQLAlchemy methods
use the `query` property:

```python
    query = select(User)
    async-query = AsyncQuery(query)
    async-query.query
    # <sqlalchemy.sql.Select>
```

!!! warning

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
    async-query = AsyncQuery(query)
    ```

    Calling `set_session` from the `AsyncQuery` instance:

    ```python
    query = select(User)
    async-query = AsyncQuery(query)
    async-query.set_session(User._session)
    ```

## API Reference

### Properties

#### query
```python
@property
def query(query: Select[tuple[Any, ...]]) -> Select[tuple[Any, ...]]
```

> Sets and returns the original `sqlalchemy.sql.Select` instance.

> **Example:**
```python
query = select(User)
async-query = AsyncQuery(query)
async-query.query
# <sqlalchemy.sql.Select>

async-query.query = async-query.query.limit(10).order_by(User.age.desc())
users = await async-query.all()
```

### class Methods

#### select
```python
@classmethod
def select(cls, *entities: _ColumnsClauseArgument[Any]) -> AsyncQuery
```

> Creates a brand new `AsyncQuery` instance with the specified entities selected.

> This method is intended to be used at the beginning of the query build process.
> You should not call it more than once on the same `AsyncQuery` instance.

> If you call this method on an already existing `AsyncQuery` instance,
> it will return a new instance with a new query. This is different from
> calling `select()` on a `sqlalchemy.sql.Select` instance. Every filter,
> group_by, order_by, limit, offset, etc. will be reset in the new instance.

> **Parameters:**
> - `entities`: Column names or SQLAlchemy column expressions.

> **Returns:**
> - `AsyncQuery`: Async query instance.

> **Example:**
> ```python
> async-query = AsyncQuery.select(User)
> async-query
> # SELECT users.id, users.username, ... FROM users
>
> async-query = AsyncQuery.select(User.name, User.age)
> async-query
> # SELECT users.name, users.age FROM users
>
> async-query = AsyncQuery.select(User.name, func.max(User.age))
> async-query
> # SELECT users.name, max(users.age) AS max_1 FROM users
> ```

### Instance Methods

#### options
```python
def options(*args: ExecutableOption) -> AsyncQuery
```

> Applies the given list of mapper options.

> !!! warning
>
>     Quoting from [SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading):
>
>         When including `joinedload()` in reference to a one-to-many or
>         many-to-many collection, the `Result.unique()` method must be
>         applied to the returned result, which will make the incoming rows
>         unique by primary key that otherwise are multiplied out by the join.
>         The ORM will raise an error if this is not present.
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
> - `AsyncQuery`: Async query instance for chaining.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> users = await async-query.options(joinedload(User.posts)).unique_all()
>
> user = await async-query.options(joinedload(User.posts)).first()
>
> users = await async-query.options(subqueryload(User.posts)).all()
> ```

#### where
```python
def where(*criteria: _ColumnExpressionArgument[bool], **filters: Any) -> AsyncQuery
```

> Applies one or more WHERE criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters:**
> - `criteria`: SQLAlchemy style filter expressions.
> - `filters`: Django-style filters.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> # SQLAlchemy style
> users = await async-query.filter(User.age >= 18).all()
>
> # Django style
> users = await async-query.filter(age__gte=18).all()
>
> # Mixed
> users = await async-query.filter(User.age >= 18, name__like='%Bob%').all()
> ```

#### filter
```python
def filter(*criterion: _ColumnExpressionArgument[bool], **filters: Any) -> AsyncQuery
```

> Synonym for `where()`.

#### find
```python
def find(*criterion: _ColumnExpressionArgument[bool], **filters: Any) -> AsyncQuery
```

> Synonym for `where()`.

#### order_by
```python
def order_by(*columns: _ColumnExpressionOrStrLabelArgument[Any]) -> AsyncQuery
```

> Applies one or more ORDER BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters:**
> - `columns`: Column names or SQLAlchemy column expressions.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> # String column names (Django style)
> users = await async-query.order_by('-created_at', 'name').all()
>
> # SQLAlchemy expressions
> users = await async-query.order_by(User.created_at.desc(), User.name).all()
> ```

#### sort
```python
def sort(*columns: _ColumnExpressionOrStrLabelArgument[Any]) -> AsyncQuery
```

> Synonym for `order_by()`.

#### group_by
```python
def group_by(*columns: _ColumnExpressionOrStrLabelArgument[Any]) -> AsyncQuery
```

> Applies one or more GROUP BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters:**
> - `columns`: Column names or SQLAlchemy column expressions.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> # String column names (Django style)
> users = await async-query.group_by('name').all(scalars=False)
>
> # SQLAlchemy expressions
> users = await async-query.group_by(User.name).all(scalars=False)
> ```

#### offset
```python
def offset(offset: int) -> AsyncQuery
```

> Applies an OFFSET clause to the query.

> **Parameters:**
> - `offset`: Number of rows to skip.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Raises:**
> - `ValueError`: If offset is negative.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> users = await async-query.offset(10).all()
> ```

#### skip
```python
def skip(skip: int) -> AsyncQuery
```

> Synonym for `offset()`.

#### limit
```python
def limit(limit: int) -> AsyncQuery
```

> Applies a LIMIT clause to the query.

> **Parameters:**
> - `limit`: Maximum number of rows to return.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Raises:**
> - `ValueError`: If limit is negative.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> users = await async-query.limit(5).all()
> ```

#### take
```python
def take(take: int) -> AsyncQuery
```

> Synonym for `limit()`.

#### join
```python
def join(
    *paths: QueryableAttribute | tuple[QueryableAttribute, bool],
    model: type[_T] | None = None
) -> AsyncQuery
```

> Joined eager loading using LEFT OUTER JOIN.

> When a tuple is passed, the second element must be boolean.
> If it is `True`, the join is `INNER JOIN`, otherwise `LEFT OUTER JOIN`.

> **Parameters:**
> - `paths`: Relationship attributes to join.
> - `model`: If given, checks that each path belongs to this model.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Example:**
> ```python
> query = select(Comment)
> async-query = AsyncQuery(query)
>
> comments = await async-query.join(
>     Comment.user,
>     (Comment.post, True),  # True means INNER JOIN
>     model=Comment   # Checks that Comment.user and Comment.post belongs to Comment
> ).all()
> ```

> ```python
> comments = await async-query.join(
>     Post.user,
>     model=Comment   # Post.user does not belong to Comment, so it will raise an error
> ).all()
> ```

#### with_subquery
```python
def with_subquery(
    *paths: QueryableAttribute | tuple[QueryableAttribute, bool],
    model: type[_T] | None = None
) -> AsyncQuery
```

> Subqueryload or Selectinload eager loading.

> Emits a second `SELECT` statement (Subqueryload) for each relationship
> to be loaded, across all result objects at once.

> When a tuple is passed, the second element must be boolean.
> If it is `True`, the eager loading strategy is `SELECT IN` (Selectinload),
> otherwise `SELECT JOIN` (Subqueryload).

> !!! warning
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
>     # incorrect, no ORDER BY
>     User.options(subqueryload(User.addresses)).first()
>     # incorrect if User.name is not unique
>     User.options(subqueryload(User.addresses)).order_by(User.name).first()
>     # correct
>     User.options(subqueryload(User.addresses)).order_by(
>         User.name, User.id
>     ).first()
>     ```

> **Parameters:**
> - `paths`: Relationship attributes to load.
> - `model`: If given, checks that each path belongs to this model.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> users = await async-query.with_subquery(
>     User.posts,
>     (User.comments, True)  # True means selectin loading
>     model=User   # Checks that User.posts and User.comments belongs to User
> ).all()
> ```

> ```python
> users = await async-query.with_subquery(
>     Comment.posts,
>     model=User   # Comment.posts does not belong to User, so it will raise an error
> ).all()
> ```

#### with_schema
```python
def with_schema(
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
) -> AsyncQuery
```

> Joined, subqueryload and selectinload eager loading.

> Useful for complex cases where you need to load nested relationships in
> separate queries.

> **Parameters:**
> - `schema`: Dictionary defining the loading strategy.

> **Returns:**
> - `AsyncQuery`: Async query instance for chaining.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> from sqlactive import JOINED, SUBQUERY
> schema = {
>     User.posts: JOINED,
>     User.comments: (SUBQUERY, {
>         Comment.user: JOINED
>     })
> }
> users = await async-query.with_schema(schema).all()
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

> Returns a `sqlalchemy.engine.ScalarResult` instance
> containing all results.

> **Returns:**
> - `sqlalchemy.engine.ScalarResult[_T]`: Scalars.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> scalar_result = await async-query.scalars()
> ```

#### first
```python
async def first(scalar: bool = True) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches the first row or `None` if no results are found.

> **Parameters:**
> - `scalar`: If `True`, returns a scalar value.

> **Returns:**
> - `_T`: Found scalar value.
> - `Row[tuple[Any, ...]]`: Found row.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> user = await async-query.first()
>
> row = await async-query.first(scalar=False)
> ```

#### one
```python
async def one(scalar: bool = True) -> _T | Row[tuple[Any, ...]]
```

> Fetches one row or raises an exception if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> **Parameters:**
> - `scalar`: If `True`, returns a scalar value.

> **Returns:**
> - `_T`: Found scalar value.
> - `Row[tuple[Any, ...]]`: Found row.

> **Raises:**
> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> user = await async-query.one()  # Raises if not exactly one match
>
> row = await async-query.one(scalar=False)
> ```

#### one_or_none
```python
async def one_or_none(scalar: bool = True) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches one row or `None` if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> **Parameters:**
> - `scalar`: If `True`, returns a scalar value.

> **Returns:**
> - `_T`: Found scalar value.
> - `Row[tuple[Any, ...]]`: Found row.

> **Raises:**
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> user = await async-query.one_or_none()
>
> row = await async-query.one_or_none(scalar=False)
> ```

#### all
```python
async def all(scalars: bool = True) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]
```

> Fetches all rows.

> **Parameters:**
> - `scalars`: If `True`, returns scalar values.

> **Returns:**
> - `Sequence[_T]`: List of scalars.
> - `Sequence[Row[tuple[Any, ...]]]`: List of rows.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> users = await async-query.all()
>
> rows = await async-query.all(scalars=False)
> ```

#### unique
```python
async def unique(scalars: bool = True) -> ScalarResult[_T] | Result[tuple[Any, ...]]
```

> Apply unique filtering to the objects returned
> in the result instance.

> **Parameters:**
> - `scalars`: If `True`, returns a scalar result.

> **Returns:**
> - `sqlalchemy.engine.ScalarResult[_T]`: Scalars.
> - `sqlalchemy.engine.Result[tuple[Any, ...]]`: Rows.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> result = await async-query.unique()
> users = result.all()
>
> result = await async-query.unique(scalars=False)
> rows = result.all()
> ```

#### unique_first
```python
async def unique_first(scalar: bool = True) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches the first unique row or `None` if no results are found.

> **Parameters:**
> - `scalar`: If `True`, returns a scalar value.

> **Returns:**
> - `_T`: Found scalar value.
> - `Row[tuple[Any, ...]]`: Found row.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> user = await async-query.unique_first()
>
> row = await async-query.unique_first(scalar=False)
> ```

#### unique_one
```python
async def unique_one(scalar: bool) -> _T | Row[tuple[Any, ...]]
```

> Fetches one unique row or raises an exception if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> **Parameters:**
> - `scalar`: If `True`, returns a scalar value.

> **Returns:**
> - `_T`: Found scalar value.
> - `Row[tuple[Any, ...]]`: Found row.

> **Raises:**
> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> user = await async-query.unique_one()
>
> row = await async-query.unique_one(scalar=False)
> ```

#### unique_one_or_none
```python
async def unique_one_or_none(scalar: bool) -> _T | Row[tuple[Any, ...]] | None
```

> Fetches one unique row or `None` if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> **Parameters:**
> - `scalar`: If `True`, returns a scalar value.

> **Returns:**
> - `_T`: Found scalar value.
> - `Row[tuple[Any, ...]]`: Found row.

> **Raises:**
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> user = await async-query.unique_one_or_none()
>
> row = await async-query.unique_one_or_none(scalar=False)
> ```

#### unique_all
```python
async def unique_all(scalars: bool) -> Sequence[_T] | Sequence[Row[tuple[Any, ...]]]
```

> Fetches all unique rows.

> **Parameters:**
> - `scalars`: If `True`, returns scalar values.

> **Returns:**
> - `Sequence[_T]`: List of scalars.
> - `Sequence[Row[tuple[Any, ...]]]`: List of rows.

> **Example:**
> ```python
> query = select(User)
> async-query = AsyncQuery(query)
>
> users = await async-query.unique_all()
>
> rows = await async-query.unique_all(scalars=False)
> ```
