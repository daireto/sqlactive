# AsyncQuery

This class is an Async wrapper for `sqlalchemy.sql.Select`.

**Table of Contents**

- [AsyncQuery](#asyncquery)
  - [Usage](#usage)
  - [API Reference](#api-reference)
    - [options](#options)
    - [filter](#filter)
    - [order\_by](#order_by)
    - [sort](#sort)
    - [offset](#offset)
    - [skip](#skip)
    - [limit](#limit)
    - [take](#take)
    - [join](#join)
    - [with\_subquery](#with_subquery)
    - [with\_schema](#with_schema)
    - [execute](#execute)
    - [scalars](#scalars)
    - [first](#first)
    - [one](#one)
    - [one\_or\_none](#one_or_none)
    - [fetch\_one](#fetch_one)
    - [fetch\_one\_or\_none](#fetch_one_or_none)
    - [all](#all)
    - [fetch\_all](#fetch_all)
    - [to\_list](#to_list)
    - [unique](#unique)
    - [unique\_all](#unique_all)
    - [unique\_first](#unique_first)
    - [unique\_one](#unique_one)
    - [unique\_one\_or\_none](#unique_one_or_none)
  - [Access the Native Query Object](#access-the-native-query-object)

## Usage

The `AsyncQuery` class provides a set of helper methods for asynchronously executing the query.

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
    # <sqlalchemy.sql.Select object at 0x7f7f7f7f7f7f7f7f>
```

!!! warning

    If no session is provided, a `NoSessionError` will be raised
    when attempting to execute the query. You must either provide
    a session by passing it in this constructor or by calling
    the `set_session` method.

    In the constructor:

    ```python
    query = select(User)
    async_query = AsyncQuery(query, User._session)
    ```

    Calling the `set_session` method:

    ```python
    query = select(User)
    async_query = AsyncQuery(query)
    async_query.set_session(User._session)
    ```

## API Reference

### options
```python
def options(*args: ExecutableOption)
```

> Applies the given list of mapper options.

> !!! warning
>
>     Quoting from https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading:
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
>     https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.options

> **Parameters:**

> - `args`: Mapper options.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> users = await async_query.options(joinedload(User.posts)).unique_all()
>
> user = await async_query.options(joinedload(User.posts)).first()
>
> users = await async_query.options(subqueryload(User.posts)).all()
> ```

### filter
```python
def filter(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Filters the query.

> Creates the WHERE clause of the query.

> **Parameters:**

> - `criterion`: SQLAlchemy style filter expressions.
> - `filters`: Django-style filters.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> # SQLAlchemy style
> users = await async_query.filter(User.age >= 18).all()
>
> # Django style
> users = await async_query.filter(age__gte=18).all()
>
> # Mixed
> users = await async_query.filter(User.age >= 18, name__like='%Bob%').all()
> ```

### order_by
```python
def order_by(*columns: _ColumnExpressionOrStrLabelArgument[Any])
```

> Applies one or more ORDER BY criteria to the query.

> **Parameters:**

> - `columns`: Column names or SQLAlchemy column expressions.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> # String column names (Django style)
> users = await async_query.order_by('-created_at', 'name').all()
>
> # SQLAlchemy expressions
> users = await async_query.order_by(User.created_at.desc(), User.name).all()
> ```

### sort
```python
def sort(*columns: _ColumnExpressionOrStrLabelArgument[Any])
```

> Synonym for `order_by()`.

### offset
```python
def offset(offset: int)
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
> async_query = AsyncQuery(query)
>
> users = await async_query.offset(10).all()
> ```

### skip
```python
def skip(skip: int)
```

> Synonym for `offset()`.

### limit
```python
def limit(limit: int)
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
> async_query = AsyncQuery(query)
>
> users = await async_query.limit(5).all()
> ```

### take
```python
def take(take: int)
```

> Synonym for `limit()`.

### join
```python
def join(
    *paths: QueryableAttribute | tuple[QueryableAttribute, bool],
    model: type[_T] | None = None
)
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
> query = select(comments)
> async_query = AsyncQuery(query)
>
> comments = await async_query.join(
>     Comment.user,
>     (Comment.post, True),  # True means INNER JOIN
>     model=Comment   # Checks that Comment.user and Comment.post belongs to Comment
> ).all()
> ```

> ```python
> comments = await async_query.join(
>     Post.user,
>     model=Comment   # Post.user does not belong to Comment, so it will raise an error
> ).all()
> ```

### with_subquery
```python
def with_subquery(
    *paths: QueryableAttribute | tuple[QueryableAttribute, bool],
    model: type[_T] | None = None
)
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
>     https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering
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

### with_schema
```python
def with_schema(
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
)
```

> Joined, subqueryload and selectinload eager loading.

> Useful for complex cases where you need to load nested relationships in
> separate queries.

> **Parameters:**

> - `schema`: Dictionary defining the loading strategy.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> from sqlactive import JOINED, SUBQUERY
> schema = {
>     User.posts: JOINED,
>     User.comments: (SUBQUERY, {
>         Comment.user: JOINED
>     })
> }
> users = await async_query.with_schema(schema).all()
> ```

### execute
```python
async def execute(self, params: _CoreAnyExecuteParams | None = None, **kwargs)
```

> Executes the query.

> **Parameters:**

> - `params`: SQLAlchemy statement execution parameters.

> **Returns:**

> - `sqlalchemy.engine.Result[Any]`: Result of the query.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> result = await async_query.execute()
> users = result.scalars().all()
> ```

### scalars
```python
async def scalars()
```

> Returns a `sqlalchemy.engine.ScalarResult` object containing all rows.

> This is same as calling `(await self.execute()).scalars()`.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult`: Scalars.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> result = await async_query.scalars()
> users = result.all()
> ```

### first
```python
async def first()
```

> Fetches the first row or `None` if no results are found.

> This is same as calling `(await self.scalars()).first()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None` if no matches.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> user = await async_query.first()
> ```

### one
```python
async def one()
```

> Fetches one row or raises an exception if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> This is same as calling `(await self.scalars()).one()`.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> user = await async_query.one()  # Raises if not exactly one match
> ```

### one_or_none
```python
async def one_or_none()
```

> Fetches one row or `None` if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> This is same as calling `(await self.scalars()).one_or_none()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> user = await async_query.one_or_none()
> ```

### fetch_one
```python
async def fetch_one()
```

> Synonym for `one()`.

### fetch_one_or_none
```python
async def fetch_one_or_none()
```

> Synonym for `one_or_none()`.

### all
```python
async def all()
```

> Fetches all rows.

> This is same as calling `(await self.scalars()).all()`.

> **Returns:**

> - `list[Self]`: List of instances.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> users = await async_query.all()
> ```

### fetch_all
```python
async def fetch_all()
```

> Synonym for `all()`.

### to_list
```python
async def to_list()
```

> Synonym for `all()`.

### unique
```python
async def unique()
```

> Returns a `sqlalchemy.engine.ScalarResult` object containing all unique rows.

> This is same as calling `(await self.scalars()).unique()`.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult`: Scalars.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> result = await async_query.unique()
> users = result.all()
> ```

### unique_all
```python
async def unique_all()
```

> Fetches all unique rows.

> This is same as calling `(await self.unique()).all()`.

> **Returns:**

> - `list[Self]`: List of instances.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> users = await async_query.unique_all()
> ```

### unique_first
```python
async def unique_first()
```

> Fetches the first unique row or `None` if no results are found.

> This is same as calling `(await self.unique()).first()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> user = await async_query.unique_first()
> ```

### unique_one
```python
async def unique_one()
```

> Fetches one unique row or raises an exception if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> This is same as calling `(await self.unique()).one()`.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> user = await async_query.unique_one()
> ```

### unique_one_or_none
```python
async def unique_one_or_none()
```

> Fetches one unique row or `None` if no results are found.

> If multiple results are found, raises `MultipleResultsFound`.

> This is same as calling `(await self.unique()).one_or_none()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> query = select(User)
> async_query = AsyncQuery(query)
>
> user = await async_query.unique_one_or_none()
> ```

## Access the Native Query Object

The native SQLAlchemy query object can be accessed via the `query` property.

```python
query = select(User)
async_query = AsyncQuery(query)
async_query.query
# <sqlalchemy.sql.Select object at 0x7f7f7f7f7f7f7f7f>

async_query.query = async_query.query.limit(10).order_by(User.age.desc())
users = await async_query.all()
```
