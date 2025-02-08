# Active Record Mixin

The `ActiveRecordMixin` class provides a set of ActiveRecord-like helper methods
for SQLAlchemy models, allowing for more intuitive and chainable database
operations with async/await support.

It implements the functionality of both [`Session`](session_mixin.md) and [`Smart Queries`](smart-query-mixin.md) mixins.

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

!!! tip

    You can also make your base inherit from the `ActiveRecordBaseModel` class
    which is a combination of `ActiveRecordMixin`, `SerializationMixin` and
    `TimestampMixin`.

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
# Left outer join
comment = await Comment.join(Comment.user, Comment.post).first()

comment = await Comment.join(
    Comment.user,
    (Comment.post, True)  # True means inner join
).first()

comments = await Comment.join(Comment.user, Comment.post)
    .unique_all()  # important!
```

#### Subquery Loading

```python
# Using subquery loading
users = await User.with_subquery(
    User.posts,
    (User.comments, True)  # True means selectinload
).unique_all()  # important!

# With limiting and sorting (important for correct results)
users = await User.with_subquery(User.posts)
    .limit(1)
    .sort('id')  # important!
    .unique_all()  # important!
```

#### Complex Schema Loading

```python
from sqlactive import JOINED, SUBQUERY

schema = {
    User.posts: JOINED,  # joinedload user
    User.comments: (SUBQUERY, {  # load comments in separate query
        Comment.user: JOINED  # but join user in this separate query
    })
}

user = await User.with_schema(schema).first()
```

### Smart Queries

The [`Smart Queries Mixin`](smart-query-mixin.md) provides a powerful smart query
builder that combines filtering, sorting, grouping and eager loading:

```python
# Complex query with multiple features
users = await User.smart_query(
    criterion=(User.age > 18,),
    filters={'name__like': '%John%'},
    sort_columns=(User.username,),
    sort_attrs=['-created_at'],
    group_columns=(User.username,),
    group_attrs=['age'],
    schema={User.posts: JOINED}
).all()
```

## API Reference

### Instance Methods

#### fill
```python
def fill(**kwargs)
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
> user.fill(name='Bob', age=30)
> ```

#### save
```python
async def save()
```

> Saves the current row to the database.

> **Returns:**

> - `Self`: The saved instance for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> user = User(name='Bob')
> await user.save()
> ```

#### update
```python
async def update(**kwargs)
```

> Updates the current row with the provided values.

> **Parameters:**

> - `kwargs`: Key-value pairs of attributes to update.

> **Returns:**

> - `Self`: The updated instance for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> await user.update(name='Bob2', age=31)
> ```

#### edit
```python
async def edit(**kwargs)
```

> Synonym for `update()`.

#### delete
```python
async def delete()
```

> Deletes the current row from the database.

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

#### create
```python
async def create(**kwargs)
```

> Creates a new row with the provided values.

> **Parameters:**

> - `kwargs`: Key-value pairs for the new instance.

> **Returns:**

> - `Self`: The created instance for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> user = await User.create(name='Bob', age=30)
> ```

#### insert
```python
async def insert(**kwargs)
```

> Synonym for `create()`.

#### add
```python
async def add(**kwargs)
```

> Synonym for `create()`.

#### save_all
```python
async def save_all(rows: Sequence[Self], refresh: bool = False)
```

> Saves multiple rows in a single transaction.

> **Parameters:**

> - `rows`: Sequence of model instances to save.
> - `refresh`: Whether to refresh the instances after saving (default: `False`).

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> users = [User(name='Bob'), User(name='Alice')]
> await User.save_all(users)
> ```

#### create_all
```python
async def create_all(rows: Sequence[Self], refresh: bool = False)
```

> Synonym for `save_all()` when creating new rows.

#### update_all
```python
async def update_all(rows: Sequence[Self], refresh: bool = False)
```

> Synonym for `save_all()` when updating existing rows.

#### delete_all
```python
async def delete_all(rows: Sequence[Self])
```

> Deletes multiple rows in a single transaction.

> **Parameters:**

> - `rows`: Sequence of model instances to delete.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> users = await User.where(age__lt=18).all()
> await User.delete_all(users)
> ```

#### destroy
```python
async def destroy(*ids: object)
```

> Deletes multiple rows by their primary keys.

> **Parameters:**

> - `ids`: Primary key values of rows to delete.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> await User.destroy(1, 2, 3)  # Deletes users with IDs 1, 2, and 3
> ```

#### get
```python
async def get(
    pk: object,
    join: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    subquery: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
)
```

> Fetches a row by primary key.

> **Parameters:**

> - `pk`: Primary key value.
> - `join`: Paths to join eager load. See the docs of [`join`](#join) method for details.
> - `subquery`: Paths to subquery eager load. See the docs of [`with_subquery`](#with_subquery) method for details.
> - `schema`: Schema for the eager loading. See the docs of [`with_schema`](#with_schema) method for details.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None` if not found.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.get(1)
> ```

#### get_or_fail
```python
async def get_or_fail(
    pk: object,
    join: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    subquery: list[QueryableAttribute | tuple[QueryableAttribute, bool]] | None = None,
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
)
```

> Fetches a row by primary key or raises an exception if not found.

> **Parameters:**

> - `pk`: Primary key value.
> - `join`: Paths to join eager load. See the docs of [`join`](#join) method for details.
> - `subquery`: Paths to subquery eager load. See the docs of [`with_subquery`](#with_subquery) method for details.
> - `schema`: Schema for the eager loading. See the docs of [`with_schema`](#with_schema) method for details.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.get_or_fail(1)  # Raises if not found
> ```

#### options
```python
def options(*args: ExecutableOption)
```

> Creates a query and applies the given list of mapper options.

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

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> users = await User.options(joinedload(User.posts)).unique_all()
>
> user = await User.options(joinedload(User.posts)).first()
>
> users = await User.options(subqueryload(User.posts)).all()
> ```

#### filter
```python
def filter(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Creates a filtered query using SQLAlchemy or Django-style filters.

> **Parameters:**

> - `criterion`: SQLAlchemy style filter expressions.
> - `filters`: Django-style filters.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> # SQLAlchemy style
> users = await User.filter(User.age >= 18).all()
>
> # Django style
> users = await User.filter(age__gte=18).all()
>
> # Mixed
> users = await User.filter(User.age >= 18, name__like='%Bob%').all()
> ```

#### where
```python
def where(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Synonym for `filter()`.

#### find
```python
def find(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Synonym for `filter()`.

#### find_one
```python
async def find_one(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds a single row matching the criteria.

> This is same as calling `await cls.find(*criterion, **filters).one()`.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.find_one(name='Bob')  # Raises if not found
> ```

#### find_one_or_none
```python
async def find_one_or_none(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds a single row matching the criteria or `None`.

> This is same as calling `await cls.find(*criterion, **filters).one_or_none()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.find_one_or_none(name='Bob')  # Returns None if not found
> ```

#### find_all
```python
async def find_all(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds all rows matching the criteria.

> This is same as calling `await cls.find(*criterion, **filters).all()`.

> **Returns:**

> - `list[Self]`: List of instances for method chaining.

> **Example:**

> ```python
> users = await User.find_all(age__gte=18)
> ```

#### find_first
```python
async def find_first(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds a single row matching the criteria or `None`.

> This is same as calling `await cls.find(*criterion, **filters).first()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Example:**

> ```python
> user = await User.find_first(name='Bob')
> ```

#### find_unique
```python
async def find_unique(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds all unique rows matching the criteria and
> returns an `ScalarResult` object with them.

> This is same as calling `await cls.find(*criterion, **filters).unique()`.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult`: Scalars.

> **Example:**

> ```python
> users_scalars = await User.find_unique(name__like='%John%')
> users = users_scalars.all()
> ```

#### find_unique_all
```python
async def find_unique_all(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds all unique rows matching the criteria and returns a list.

> This is same as calling `await cls.find(*criterion, **filters).unique_all()`.

> **Returns:**

> - `list[Self]`: List of instances.

> **Example:**

> ```python
> users = await User.find_unique_all(name__like='%John%')
> ```

#### find_unique_first
```python
async def find_unique_first(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds a single unique row matching the criteria or `None`.

> This is same as calling `await cls.find(*criterion, **filters).unique_first()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Example:**

> ```python
> user = await User.find_unique_first(name__like='%John%', age=30)
> ```

#### find_unique_one
```python
async def find_unique_one(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds a single unique row matching the criteria.

> This is same as calling `await cls.find(*criterion, **filters).unique_one()`.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.find_unique_one(name__like='%John%', age=30)
> ```

#### find_unique_one_or_none
```python
async def find_unique_one_or_none(*criterion: _ColumnExpressionArgument[bool], **filters: Any)
```

> Finds a single unique row matching the criteria or `None`.

> This is same as calling `await cls.find(*criterion, **filters).unique_one_or_none()`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.find_unique_one_or_none(name__like='%John%', age=30)
> ```

#### order_by
```python
def order_by(*columns: _ColumnExpressionOrStrLabelArgument[Any])
```

> Creates a query with ORDER BY clause.

> **Parameters:**

> - `columns`: Column names or SQLAlchemy column expressions.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> # String column names (Django style)
> users = await User.order_by('-created_at', 'name').all()
>
> # SQLAlchemy expressions
> users = await User.order_by(User.created_at.desc(), User.name).all()
> ```

#### sort
```python
def sort(*columns: _ColumnExpressionOrStrLabelArgument[Any])
```

> Synonym for `order_by()`.

#### offset
```python
def offset(offset: int)
```

> Creates a query with OFFSET clause.

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
def skip(skip: int)
```

> Synonym for `offset()`.

#### limit
```python
def limit(limit: int)
```

> Creates a query with LIMIT clause.

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
def take(take: int)
```

> Synonym for `limit()`.

#### join
```python
def join(*paths: QueryableAttribute | tuple[QueryableAttribute, bool])
```

> Creates a query with `LEFT OUTER JOIN` eager loading.

> When a tuple is passed, the second element must be boolean.
> If it is `True`, the join is `INNER JOIN`, otherwise `LEFT OUTER JOIN`.

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
def with_subquery(*paths: QueryableAttribute | tuple[QueryableAttribute, bool])
```

> Creates a query with subquery or selectin loading.

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
def with_schema(
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
)
```

> Creates a query with complex eager loading schema.

> Useful for complex cases where you need to load nested relationships in
> separate queries.

> **Parameters:**

> - `schema`: Dictionary defining the loading strategy.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> ```python
> from sqlactive import JOINED, SUBQUERY
> schema = {
>     User.posts: JOINED,
>     User.comments: (SUBQUERY, {
>         Comment.user: JOINED
>     })
> }
> users = await User.with_schema(schema).all()
> ```

#### scalars
```python
async def scalars()
```

> Returns a `sqlalchemy.engine.ScalarResult` object containing all rows.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult`: Scalars.

> **Example:**

> ```python
> result = await User.scalars()
> users = result.all()
> ```

#### first
```python
async def first()
```

> Fetches the first row.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None` if no matches.

> **Example:**

> ```python
> user = await User.first()
> ```

#### one
```python
async def one()
```

> Fetches exactly one row.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.one()  # Raises if not exactly one match
> ```

#### one_or_none
```python
async def one_or_none()
```

> Fetches exactly one row or `None`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.one_or_none()
> ```

#### fetch_one
```python
async def fetch_one()
```

> Synonym for `one()`.

#### fetch_one_or_none
```python
async def fetch_one_or_none()
```

> Synonym for `one_or_none()`.

#### all
```python
async def all()
```

> Fetches all rows.

> **Returns:**

> - `list[Self]`: List of instances.

> **Example:**

> ```python
> users = await User.all()
> ```

#### fetch_all
```python
async def fetch_all()
```

> Synonym for `all()`.

#### to_list
```python
async def to_list()
```

> Synonym for `all()`.

#### unique
```python
async def unique()
```

> Returns a `sqlalchemy.engine.ScalarResult` object containing all unique rows.

> **Returns:**

> - `sqlalchemy.engine.ScalarResult`: Scalars.

> **Example:**

> ```python
> result = await User.unique()
> users = result.all()
> ```

#### unique_all
```python
async def unique_all()
```

> Fetches all unique rows.

> **Returns:**

> - `list[Self]`: List of instances.

> **Example:**

> ```python
> users = await User.unique_all()
> ```

#### unique_first
```python
async def unique_first()
```

> Fetches the first unique row.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Example:**

> ```python
> user = await User.unique_first()
> ```

#### unique_one
```python
async def unique_one()
```

> Fetches exactly one unique row.

> **Returns:**

> - `Self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.unique_one()
> ```

#### unique_one_or_none
```python
async def unique_one_or_none()
```

> Fetches exactly one unique row or `None`.

> **Returns:**

> - `Self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.unique_one_or_none()
> ```

#### smart_query
```python
def smart_query(
    criterion: Sequence[_ColumnExpressionArgument[bool]] | None = None,
    filters: dict[str, Any] | dict[OperatorType, Any] | list[dict[str, Any]] | list[dict[OperatorType, Any]] | None = None,
    sort_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
    sort_attrs: Sequence[str] | None = None,
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
)
```

> Creates a query combining filtering, sorting, and eager loading.

> **Parameters:**

> - `criterion`: SQLAlchemy filter expressions.
> - `filters`: Django-style filters.
> - `sort_columns`: SQLAlchemy columns to sort by.
> - `sort_attrs`: String column names to sort by.
> - `schema`: Eager loading schema.

> **Returns:**

> - [`AsyncQuery`](async-query.md): Async query instance for chaining.

> **Example:**

> ```python
> users = await User.smart_query(
>     criterion=(User.age >= 18,),
>     filters={'name__like': '%Bob%'},
>     sort_columns=(User.username,),
>     sort_attrs=['-created_at'],
>     schema={User.posts: 'joined'}
> ).all()
> ```

## Important Notes

1. When using `subqueryload()` with limiting modifiers (`limit()`, `offset()`),
   always include `order_by()` with unique columns (like primary key) to ensure
   correct results.

2. For joined eager loading with one-to-many or many-to-many relationships,
   use the `unique()` method or unique-related methods (i.e. `unique_all()`) to
   prevent duplicate rows:
   ```python
   users = await User.options(joinedload(User.posts)).unique_all()
   ```
