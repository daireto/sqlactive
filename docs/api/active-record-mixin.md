# Active Record Mixin

The `ActiveRecordMixin` class provides a set of ActiveRecord-like helper methods
for SQLAlchemy models, allowing for more intuitive and chainable database
operations with async/await support.

It implements the functionality of both [`Session`](session-mixin.md) and [`Smart Queries`](smart-query-mixin.md) mixins.

## Usage

To use the `ActiveRecordMixin`, create a base model class that inherits from it
and set the `__abstract__` attribute to `True`:

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

???+ tip

    You can also make your base inherit from the `ActiveRecordBaseModel` class
    which is a combination of `ActiveRecordMixin`, `SerializationMixin` and
    `TimestampMixin`.

???+ warning

    All relations used in filtering/sorting/grouping should be explicitly set,
    not just being a `backref`.
    This is because `sqlactive` does not know the relation direction and cannot
    infer it.
    So, when defining a relationship like:

    ```python
    class User(BaseModel):
        # ...
        posts: Mapped[list['Post']] = relationship(back_populates='user')
    ```

    It is required to define the reverse relationship:

    ```python
    class Post(BaseModel):
        # ...
        user: Mapped['User'] = relationship(back_populates='posts')
    ```

## Core Features

### Creation, Updating, and Deletion

#### Creating Records

```python
# Create a single record
bob = await User.insert(name='Bob')
joe = await User.create(name='Joe')  # Synonym for insert()

# Create multiple records
users = [User(name='Alice'), User(name='Bob')]
await User.insert_all(users)  # Shortcut for save_all()
```

#### Updating Records

```python
# Update a single record
await user.update(name='Bob2')

# Update multiple records
users = await User.where(age=25).all()
for user in users:
    user.name = f"{user.name} Jr."
await User.update_all(users)  # Shortcut for save_all()
```

#### Deleting Records

```python
# Delete a single record
await user.delete()
await user.remove()  # Synonym for delete()

# Delete multiple records
users = await User.where(age=25).all()
await User.delete_all(users)

# Delete by primary keys
await User.destroy(1, 2, 3)  # Deletes users with IDs 1, 2, and 3
```

### Querying

#### Basic Queries

```python
# Get all records
users = await User.all()

# Get first record
user = await User.first()        # None if no results found

# Get one record
user = await User.one()          # Raises if no results found
user = await User.one_or_none()  # Returns None if no results found
```

#### Filtering

The mixin supports both Django-like syntax and SQLAlchemy syntax for filtering:

```python
# Django-like syntax
users = await User.where(name__like='%John%').all()
users = await User.where(name__like='%John%', age=30).all()

# SQLAlchemy syntax
users = await User.where(User.name == 'John Doe').all()

# Mixed syntax
users = await User.where(User.age == 30, name__like='%John%').all()

# Synonyms
users = await User.filter(name__like='%John%').all()
user = await User.find(name__like='%John%', age=30).one()
```

#### Sorting and Pagination

```python
from sqlalchemy.sql import asc, desc

# Sorting (Django-like syntax)
users = await User.order_by('-created_at').all()          # Descending order
users = await User.order_by('name').all()                 # Ascending order
users = await User.order_by('-created_at', 'name').all()  # Multiple columns

# Sorting (SQLAlchemy syntax)
users = await User.sort(User.created_at.desc()).all()     # Synonym for order_by()
users = await User.sort(asc(User.name)).all()

# Sorting (mixed syntax)
users = await User.order_by('-created_at', User.name.asc()).all()
users = await User.sort('-age', asc(User.name)).all()

# Pagination
users = await User.offset(10).limit(5).all()  # Skip 10, take 5
users = await User.skip(10).take(5).all()     # Same as above
```

#### Grouping

```python
# Grouping (Django-like syntax)
users = await User.group_by(User.age).all()
users = await User.group_by(User.age, User.name).all()

# Grouping (SQLAlchemy syntax)
users = await User.group_by('age').all()
users = await User.group_by('age', 'name').all()

# Grouping (mixed syntax)
users = await User.group_by(User.age, 'name').all()
```

### Eager Loading

#### Join Loading

```python
comment = await Comment.join(Comment.user, Comment.post).first()  # Left outer join

comment = await Comment.join(
    Comment.user,
    (Comment.post, True)  # True means inner join
).first()

comments = await Comment.join(Comment.user, Comment.post)
    .unique_all()  # important!
```

#### Subquery Loading

```python
users = await User.with_subquery(
    User.posts,            # subquery loading
    (User.comments, True)  # True means selectinload
).unique_all()     # important!

# With limiting and sorting (important for correct results)
users = await User.with_subquery(User.posts)
    .limit(1)
    .sort('id')    # important!
    .unique_all()  # important!
```

#### Complex Schema Loading

```python
from sqlactive import JOINED, SUBQUERY

schema = {
    User.posts: JOINED,          # joinedload user
    User.comments: (SUBQUERY, {  # load comments in separate query
        Comment.user: JOINED     # but join user in this separate query
    })
}

user = await User.with_schema(schema).first()
```

### Smart Queries

The [`Smart Query Mixin`](smart-query-mixin.md) provides a powerful smart query
builder that combines filtering, sorting, grouping and eager loading:

```python
from sqlactive import JOINED

# Complex query with multiple features
users = await User.smart_query(
    criterion=(User.age >= 18,),
    filters={'name__like': '%John%'},
    sort_columns=(User.username,),
    sort_attrs=['-created_at'],
    group_columns=(User.username,),
    group_attrs=['age'],
    schema={User.posts: JOINED}
).all()
```

## API Reference

### Class Properties

Most of class properties are inherited from [`InspectionMixin`](inspection-mixin.md).

#### query
```python
@classproperty
def query() -> Select[tuple[Self]]
```

> Returns a new `sqlalchemy.sql.Select` instance for the model.

> This is a shortcut for `select(cls)`.

> **Example:**

> ```python
> from sqlalchemy import select
>
> User.query    # SELECT * FROM users
> select(User)  # SELECT * FROM users
> ```

### Instance Methods

#### fill
```python
def fill(**kwargs) -> Self
```

> Fills the object with values from `kwargs` without saving to the database.

> **Parameters:**

> - `kwargs`: Key-value pairs of attributes to set.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Raises:**

> - `KeyError`: If attribute doesn't exist.

> **Example:**

> ```python
> user = User()
> user.fill(name='Bob Williams', age=30)
> ```

#### save
```python
async def save() -> Self
```

> Saves the current row.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> user = User(name='Bob')
> await user.save()
> ```

#### update
```python
async def update(**kwargs) -> Self
```

> Updates the current row with the provided values.

> This is the same as calling `self.fill(**kwargs).save()`.

> **Parameters:**

> - `kwargs`: Key-value pairs of attributes to update.

> **Returns:**

> - `Self`: The instance itself for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> user = User(name='Bob', age=30)
> await user.update(name='Bob Williams', age=31)
> ```

#### delete
```python
async def delete()
```

> Deletes the current row.

> ???+ danger
>
>     This is not a soft delete method. It will permanently delete the row from
>     the database. So, if you want to keep the row in the database, you can implement
>     a custom soft delete method, i.e. using `save()` method to update the row with a
>     flag indicating if the row is deleted or not (i.e. a boolean `is_deleted` column).

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> await user.delete()
> ```

#### remove
```python
async def remove()
```

> Synonym for `delete()`.

### Class Methods

#### insert
```python
@classmethod
async def insert(**kwargs) -> Self
```

> Inserts a new row.

> **Parameters:**

> - `kwargs`: Key-value pairs for the new instance.

> **Returns:**

> - `Self`: The created instance for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> user = await User.insert(name='Bob Williams', age=30)
> ```

#### create
```python
@classmethod
async def create(**kwargs)
```

> Synonym for `insert()`.

#### save_all
```python
@classmethod
async def save_all(rows: Sequence[Self], refresh: bool = False)
```

> Saves multiple rows in a single transaction.

> **Parameters:**

> - `rows`: Sequence of rows to be saved.
> - `refresh`: Whether to refresh the rows after saving (default: `False`).

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> users = [User(name='Bob'), User(name='Alice')]
> await User.save_all(users, refresh=True)
> ```

#### insert_all
```python
@classmethod
async def insert_all(rows: Sequence[Self], refresh: bool = False)
```

> Inserts multiple rows in a single transaction.

> This is mostly a shortcut for `save_all()` when inserting new rows.

#### update_all
```python
@classmethod
async def update_all(rows: Sequence[Self], refresh: bool = False)
```

> Updates multiple rows in a single transaction.

> This is mostly a shortcut for `save_all()` when updating existing rows.

#### delete_all
```python
@classmethod
async def delete_all(rows: Sequence[Self])
```

> Deletes multiple rows in a single transaction.

> **Parameters:**

> - `rows`: Sequence of rows to be deleted.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> users = await User.where(age__lt=18).all()
> await User.delete_all(users)
> ```

#### destroy
```python
@classmethod
async def destroy(*ids: object)
```

> Deletes multiple rows by their primary key.

> If rows have a composite primary key, this method will raise `InvalidRequestError`.

> **Parameters:**

> - `ids`: Primary key values of rows to delete.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> await User.destroy(1, 2, 3)  # Deletes users with IDs 1, 2, and 3
> ```

#### get
```python
@classmethod
async def get(
    pk: object,
    join: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    subquery: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
) -> Self | None
```

> Fetches a row by primary key or `None` if no result is found.

> **Parameters:**

> - `pk`: Primary key value.
> - `join`: Paths to join eager load.
> **IMPORTANT:** See the docs of [`join`](#join) method for details.
> - `subquery`: Paths to subquery eager load.
> **IMPORTANT:** See the docs of [`with_subquery`](#with_subquery) method for details.
> - `schema`: Schema for the eager loading.
> **IMPORTANT:** See the docs of [`with_schema`](#with_schema) method for details.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.get(1)
> ```

#### get_or_fail
```python
@classmethod
async def get_or_fail(
    pk: object,
    join: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    subquery: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
) -> Self
```

> Fetches a row by primary key or raises an exception if no result is found.

> **Parameters:**

> - `pk`: Primary key value.
> - `join`: Paths to join eager load.
> **IMPORTANT:** See the docs of [`join`](#join) method for details.
> - `subquery`: Paths to subquery eager load.
> **IMPORTANT:** See the docs of [`with_subquery`](#with_subquery) method for details.
> - `schema`: Schema for the eager loading.
> **IMPORTANT:** See the docs of [`with_schema`](#with_schema) method for details.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no result is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.get_or_fail(1)  # Raises if not found
> ```

#### scalars
```python
@classmethod
async def scalars() -> ScalarResult[Self]
```

> Returns a `sqlalchemy.engine.ScalarResult` instance containing all rows.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult[Self]`: Scalars.

> **Example:**

> ```python
> result = await User.scalars()  # <sqlalchemy.engine.result.ScalarResult>
> users = result.all()           # [<User 1>, <User 2>, ...]
> ```

#### first
```python
@classmethod
async def first(scalar: bool = True) -> Self | Row[tuple[Any, ...]] | None
```

> Fetches the first row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`Self`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `Self`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Example:**

> ```python
> user = await User.first()             # <User 1>
> row = await User.first(scalar=False)  # (<User 1>,)
> ```

#### one
```python
@classmethod
async def one(scalar: bool = True) -> Self | Row[tuple[Any, ...]]
```

> Fetches one row or raises an exception if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`Self`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `Self`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.one()             # <User 1>
> row = await User.one(scalar=False)  # (<User 1>,)
> ```

#### one_or_none
```python
@classmethod
async def one_or_none(scalar: bool = True) -> Self | Row[tuple[Any, ...]] | None
```

> Fetches one row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`Self`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `Self`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.one_or_none()             # <User 1>
> row = await User.one_or_none(scalar=False)  # (<User 1>,)
> ```

#### all
```python
@classmethod
async def all(scalars: bool = True) -> Sequence[Self] | Sequence[Row[tuple[Any, ...]]]
```

> Fetches all rows.

> **Parameters:**

> - `scalars`: If `True`, returns scalar values (`Sequence[Self]`),
> otherwise returns rows (default: `True`).

> **Returns:**

> - `Sequence[Self]`: Sequence of instances (scalars).
> - `Sequence[sqlalchemy.engine.Row[tuple[Any, ...]]]`: Sequence of rows.

> **Example:**

> ```python
> users = await User.all()              # [<User 1>, <User 2>, ...]
> rows = await User.all(scalars=False)  # [(<User 1>,), (<User 2>,), ...]
> ```

#### count
```python
@classmethod
async def count() -> int
```

> Fetches the number of rows.

> **Returns:**

> - `int`: Number of rows.

> **Example:**

> ```python
> count = await User.count()  # 34
> ```

#### unique
```python
@classmethod
async def unique(scalars: bool = True) -> ScalarResult[Self] | Result[tuple[Any, ...]]
```

> Apply unique filtering to the objects returned in the result instance.

> **Parameters:**

> - `scalars`: If `True`, returns a `sqlalchemy.engine.ScalarResult`
> instance. Otherwise, returns a `sqlalchemy.engine.Result` instance.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult[Self]`: Scalars.
> - `sqlalchemy.engine.Result[tuple[Any, ...]]`: Rows.

> **Example:**

> ```python
> result = await User.unique()
> users = result.all()  # [<User 1>, <User 2>, ...]
> result = await User.unique(scalars=False)
> rows = result.all()  # [(<User 1>,), (<User 2>,), ...]
> ```

#### unique_first
```python
@classmethod
async def unique_first(scalar: bool = True) -> Self | Row[tuple[Any, ...]] | None
```

> Fetches the first unique row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`Self`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `Self`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Example:**

> ```python
> user = await User.unique_first()             # <User 1>
> row = await User.unique_first(scalar=False)  # (<User 1>,)
> ```

#### unique_one
```python
@classmethod
async def unique_one(scalar: bool = True) -> Self | Row[tuple[Any, ...]]
```

> Fetches one unique row or raises an exception if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`Self`),
> otherwise returns a row (default: `True`).

> **Returns:**

> - `Self`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.unique_one()             # <User 1>
> row = await User.unique_one(scalar=False)  # (<User 1>,)
> ```

#### unique_one_or_none
```python
@classmethod
async def unique_one_or_none(scalar: bool = True) -> Self | Row[tuple[Any, ...]] | None
```

> Fetches one unique row or `None` if no results are found.

> **Parameters:**

> - `scalar`: If `True`, returns a scalar value (`Self`), otherwise returns a row (default: `True`).

> **Returns:**

> - `Self`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.unique_one_or_none()             # <User 1>
> row = await User.unique_one_or_none(scalar=False)  # (<User 1>,)
> ```

#### unique_all
```python
@classmethod
async def unique_all(scalars: bool = True) -> Sequence[Self] | Sequence[Row[tuple[Any, ...]]]
```

> Fetches all unique rows.

> **Parameters:**

> - `scalars`: If `True`, returns scalar values (`Sequence[Self]`),
> otherwise returns rows (default: `True`).

> **Returns:**

> - `Sequence[Self]`: Sequence of instances (scalars).
> - `Sequence[sqlalchemy.engine.Row[tuple[Any, ...]]]`: Sequence of rows.

> **Example:**

> ```python
> users = await User.unique_all()              # [<User 1>, <User 2>, ...]
> rows = await User.unique_all(scalars=False)  # [(<User 1>,), (<User 2>,), ...]
> ```

#### unique_count
```python
@classmethod
async def unique_count() -> int
```

> Fetches the number of unique rows.

> **Returns:**

> - `int`: Number of unique rows.

> **Example:**

> ```python
> unique_count = await User.unique_count()  # 34
> ```

#### select
```python
@classmethod
def select(*entities: _ColumnsClauseArgument[Any]) -> AsyncQuery
```

> Replaces the columns clause with the given entities.

> The existing set of FROMs are maintained, including those
> implied by the current columns clause.

> **Parameters:**

> - `entities`: Entities to be selected.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> async_query = User.order_by('-created_at')
> # SELECT users.id, users.username, users.name, ... FROM users ORDER BY users.created_at DESC
>
> async_query.select(User.name, User.age)
> # SELECT users.name, users.age FROM users ORDER BY users.created_at DESC
> ```

#### options
```python
@classmethod
def options(*args: ExecutableOption) -> AsyncQuery
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

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> users = await User.options(joinedload(User.posts)).unique_all()
> user = await User.options(joinedload(User.posts)).first()
> users = await User.options(subqueryload(User.posts)).all()
> ```

#### where
```python
@classmethod
def where(*criteria: _ColumnExpressionArgument[bool], **filters: Any) -> AsyncQuery
```

> Applies one or more WHERE criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters:**

> - `criteria`: SQLAlchemy style filter expressions.
> - `filters`: Django-style filters.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> # SQLAlchemy style
> users = await User.where(User.age >= 18).all()
>
> # Django style
> users = await User.where(age__gte=18).all()
>
> # Mixed
> users = await User.where(User.age >= 18, name__like='%Bob%').all()
> ```

#### filter
```python
@classmethod
def filter(*criterion: _ColumnExpressionArgument[bool], **filters: Any) -> AsyncQuery
```

> Synonym for `where()`.

#### find
```python
@classmethod
def find(*criterion: _ColumnExpressionArgument[bool], **filters: Any) -> AsyncQuery
```

> Synonym for `where()`.

#### order_by
```python
@classmethod
def order_by(*columns: _ColumnExpressionOrStrLabelArgument[Any]) -> AsyncQuery
```

> Applies one or more ORDER BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters:**

> - `columns`: Django-like or SQLAlchemy sort expressions.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> # SQLAlchemy style
> users = await User.order_by(User.created_at.desc(), User.name).all()
>
> # Django style
> users = await User.order_by('-created_at', 'name').all()
>
> # Mixed
> users = await User.order_by('-created_at', User.name.asc()).all()
> ```

#### sort
```python
@classmethod
def sort(*columns: _ColumnExpressionOrStrLabelArgument[Any]) -> AsyncQuery
```

> Synonym for `order_by()`.

#### group_by
```python
@classmethod
def group_by(
    *columns: _ColumnExpressionOrStrLabelArgument[Any],
    select_columns: Sequence[_ColumnsClauseArgument[Any]] | None = None,
) -> AsyncQuery
```

> Applies one or more GROUP BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> It is recommended to select specific columns. You can use
> the `select_columns` parameter to select specific columns.

> **Parameters:**

> - `columns`: Django-like or SQLAlchemy columns.
> - `select_columns`: Columns to be selected.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> from sqlalchemy.sql import text
> from sqlalchemy.sql.functions import func
>
> # Using the `select_columns` parameter
> columns = (User.age, func.count(User.age))
> async_query = User.group_by(User.age, select_columns=columns)
> rows = await async_query.all(scalars=False)
>
> # Calling `select()` before (and with relations)
> async_query = Post.select(Post.rating, text('users_1.name'), func.count(Post.title))
> async_query = async_query.group_by('rating', 'user___name')
> rows = async_query.all(scalars=False)
> ```

#### offset
```python
@classmethod
def offset(offset: int) -> AsyncQuery
```

> Applies an OFFSET clause to the query.

> **Parameters:**

> - `offset`: Number of rows to skip.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Raises:**

> - `ValueError`: If offset is negative.

> **Example:**

> ```python
> users = await User.offset(10).all()
> ```

#### skip
```python
@classmethod
def skip(skip: int) -> AsyncQuery
```

> Synonym for `offset()`.

#### limit
```python
@classmethod
def limit(limit: int) -> AsyncQuery
```

> Applies a LIMIT clause to the query.

> **Parameters:**

> - `limit`: Maximum number of rows to return.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Raises:**

> - `ValueError`: If limit is negative.

> **Example:**

> ```python
> users = await User.limit(5).all()
> ```

#### take
```python
@classmethod
def take(take: int) -> AsyncQuery
```

> Synonym for `limit()`.

#### top
```python
@classmethod
def top(top: int) -> AsyncQuery
```

> Synonym for `limit()`.

#### join
```python
@classmethod
def join(*paths: QueryableAttribute | tuple[QueryableAttribute, bool]) -> AsyncQuery
```

> Joined eager loading using LEFT OUTER JOIN.

> When a tuple is passed, the second element must be boolean, and
> if `True`, the join is `INNER JOIN`, otherwise `LEFT OUTER JOIN`.

> **Parameters:**

> - `paths`: Relationship attributes to join.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> comments = await Comment.join(
>     Comment.user,
>     (Comment.post, True)  # True means INNER JOIN
> ).all()
> ```

#### with_subquery
```python
@classmethod
def with_subquery(*paths: QueryableAttribute | tuple[QueryableAttribute, bool]) -> AsyncQuery
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

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> users = await User.with_subquery(
>     User.posts,
>     (User.comments, True)  # True means selectin loading
> ).all()
> ```

#### with_schema
```python
@classmethod
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

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> ```python
> from sqlactive import JOINED, SUBQUERY
>
> schema = {
>     User.posts: JOINED,
>     User.comments: (SUBQUERY, {
>         Comment.user: JOINED
>     })
> }
> users = await User.with_schema(schema).all()
> ```

#### smart_query
```python
@classmethod
def smart_query(
    criteria: Sequence[_ColumnExpressionArgument[bool]] | None = None,
    filters: (
        dict[str, Any] | dict[OperatorType, Any] | list[dict[str, Any]] | list[dict[OperatorType, Any]] | None
    ) = None,
    sort_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
    sort_attrs: Sequence[str] | None = None,
    group_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
    group_attrs: Sequence[str] | None = None,
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
) -> AsyncQuery
```

> Creates a query combining filtering, sorting, grouping and eager loading.

> Does magic Django-like joins like `post___user___name__startswith='Bob'`
> (see https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships)

> Does filtering, sorting and eager loading at the same time.
> And if, say, filters, sorting and grouping need the same join,
> it will be done only once.

> It also supports SQLAlchemy syntax filter expressions like
> ```python
> db.query(User).filter(User.id == 1, User.name == 'Bob')
> db.query(User).filter(or_(User.id == 1, User.name == 'Bob'))
> ```

> ???+ note
>
>     To get more information about the usage, see the documentation of
>     [`filter_expr`](smart-query-mixin.md#filter_expr),
>     [`order_expr`](smart-query-mixin.md#order_expr),
>     [`columns_expr`](smart-query-mixin.md#columns_expr) and
>     [`eager_expr`](smart-query-mixin.md#eager_expr) methods of the
>     [`Smart Query Mixin`](smart-query-mixin.md).

> **Parameters:**

> - `criteria`: SQLAlchemy syntax filter expressions.
> - `filters`: Django-like filter expressions.
> - `sort_columns`: Standalone sort columns.
> - `sort_attrs`: Django-like sort expressions.
> - `group_columns`: Standalone group columns.
> - `group_attrs`: Django-like group expressions.
> - `schema`: Schema for the eager loading.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> from sqlactive import JOINED
>
> users = await User.smart_query(
>     criterion=(User.age >= 18,),
>     filters={'name__like': '%John%'},
>     sort_columns=(User.username,),
>     sort_attrs=['-created_at'],
>     group_columns=(User.username,),
>     group_attrs=['age'],
>     schema={User.posts: JOINED}
> ).all()
> ```

#### get_async_query
```python
@classmethod
def get_async_query(query: Select[tuple[Any, ...]] | None = None) -> AsyncQuery
```

> Returns an `AsyncQuery` instance with the provided
> `sqlalchemy.sql.Select` instance.

> If no `sqlalchemy.sql.Select` instance is provided,
> it uses the `query` property of the model.

> **Parameters:**

> - `query`: SQLAlchemy query.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> async_query = User.get_async_query()
> first_bob = await async_query.where(name__startswith='Bob').first()
> first_bob.name  # 'Bob Williams'
> first_bob.age   # 30
> ```

#### get_primary_key_name
```python
@classmethod
def get_primary_key_name() -> str
```

> ???+ warning
>
>     _Deprecated since version 0.2: Use `primary_key_name` property instead._

> Gets the primary key name of the model.

> This method can only be used if the model has a single primary key.

> **Returns:**

> - `str`: Primary key name.

> **Raises:**

> - `InvalidRequestError`: If the model has a composite primary key.

> **Example:**

> ```python
> User.get_primary_key_name()  # 'id'
> ```

## Important Notes

1. When using `subqueryload()` with limiting modifiers (`limit()`, `offset()`),
   always include `order_by()` with unique columns (like primary key) to ensure
   correct results.

2. For joined eager loading with one-to-many or many-to-many relationships,
   use the `unique()` method or related (i.e. `unique_all()`) to
   prevent duplicate rows:
   ```python
   users = await User.options(joinedload(User.posts)).unique_all()
   ```
