# API Reference

This is the API reference for the `ActiveRecordMixin` class.

**Table of Contents**

- [API Reference](#api-reference)
  - [Instance Methods](#instance-methods)
    - [fill](#fill)
    - [save](#save)
    - [update](#update)
    - [edit](#edit)
    - [delete](#delete)
    - [remove](#remove)
  - [Class Methods](#class-methods)
    - [create](#create)
    - [insert](#insert)
    - [add](#add)
    - [save\_all](#save_all)
    - [create\_all](#create_all)
    - [update\_all](#update_all)
    - [delete\_all](#delete_all)
    - [destroy](#destroy)
    - [get](#get)
    - [get\_or\_fail](#get_or_fail)
    - [options](#options)
    - [filter](#filter)
    - [where](#where)
    - [find](#find)
    - [find\_one](#find_one)
    - [find\_one\_or\_none](#find_one_or_none)
    - [find\_all](#find_all)
    - [order\_by](#order_by)
    - [sort](#sort)
    - [offset](#offset)
    - [skip](#skip)
    - [limit](#limit)
    - [take](#take)
    - [join](#join)
    - [with\_subquery](#with_subquery)
    - [with\_schema](#with_schema)
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
    - [smart\_query](#smart_query)

## Instance Methods

### fill
```python
def fill(**kwargs)
```

> Fills the object with values from `kwargs` without saving to the database.

> **Parameters:**

> - `kwargs`: Key-value pairs of attributes to set.

> **Returns:**

> - `self`: The instance itself for method chaining.

> **Raises:**

> - `KeyError`: If attribute doesn't exist.

> **Example:**

> ```python
> user.fill(name='Bob', age=30)
> ```

### save
```python
async def save()
```

> Saves the current row to the database.

> **Returns:**

> - `self`: The saved instance for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> user = User(name='Bob')
> await user.save()
> ```

### update
```python
async def update(**kwargs)
```

> Updates the current row with the provided values.

> **Parameters:**

> - `kwargs`: Key-value pairs of attributes to update.

> **Returns:**

> - `self`: The updated instance for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> await user.update(name='Bob2', age=31)
> ```

### edit
```python
async def edit(**kwargs)
```

> Synonym for `update()`.

### delete
```python
async def delete()
```

> Deletes the current row from the database.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> await user.delete()
> ```

### remove
```python
async def remove()
```

> Synonym for `delete()`.

## Class Methods

### create
```python
async def create(**kwargs)
```

> Creates a new row with the provided values.

> **Parameters:**

> - `kwargs`: Key-value pairs for the new instance.

> **Returns:**

> - `self`: The created instance for method chaining.

> **Raises:** Any database errors are caught and will trigger a rollback.

> **Example:**

> ```python
> user = await User.create(name='Bob', age=30)
> ```

### insert
```python
async def insert(**kwargs)
```

> Synonym for `create()`.

### add
```python
async def add(**kwargs)
```

> Synonym for `create()`.

### save_all
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

### create_all
```python
async def create_all(rows: Sequence[Self], refresh: bool = False)
```

> Synonym for `save_all()` when creating new rows.

### update_all
```python
async def update_all(rows: Sequence[Self], refresh: bool = False)
```

> Synonym for `save_all()` when updating existing rows.

### delete_all
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

### destroy
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

### get
```python
async def get(pk: object)
```

> Fetches a row by primary key.

> **Parameters:**

> - `pk`: Primary key value.

> **Returns:**

> - `self | None`: Instance for method chaining or `None` if not found.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.get(1)
> ```

### get_or_fail
```python
async def get_or_fail(pk: object)
```

> Fetches a row by primary key or raises an exception if not found.

> **Parameters:**

> - `pk`: Primary key value.

> **Returns:**

> - `self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.get_or_fail(1)  # Raises if not found
> ```

### options
```python
def options(*args: ExecutableOption)
```

> Creates a query and applies the given list of mapper options.

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
> users = await User.options(joinedload(User.posts)).unique_all()
>
> user = await User.options(joinedload(User.posts)).first()
>
> users = await User.options(subqueryload(User.posts)).all()
> ```

### filter
```python
def filter(*criterion: ColumnElement[Any], **filters: Any)
```

> Creates a filtered query using SQLAlchemy or Django-style filters.

> **Parameters:**

> - `criterion`: SQLAlchemy style filter expressions.
> - `filters`: Django-style filters.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

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

### where
```python
def where(*criterion: ColumnElement[Any], **filters: Any)
```

> Synonym for `filter()`.

### find
```python
def find(*criterion: ColumnElement[Any], **filters: Any)
```

> Synonym for `filter()`.

### find_one
```python
async def find_one(*criterion: ColumnElement[Any], **filters: Any)
```

> Finds a single row matching the criteria.

> This is same as calling `await cls.find(*criterion, **filters).one()`.

> **Returns:**

> - `self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.find_one(name='Bob')  # Raises if not found
> ```

### find_one_or_none
```python
async def find_one_or_none(*criterion: ColumnElement[Any], **filters: Any)
```

> Finds a single row matching the criteria or `None`.

> This is same as calling `await cls.find(*criterion, **filters).one_or_none()`.

> **Returns:**

> - `self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.find_one_or_none(name='Bob')  # Returns None if not found
> ```

### find_all
```python
async def find_all(*criterion: ColumnElement[Any], **filters: Any)
```

> Finds all rows matching the criteria.

> This is same as calling `await cls.find(*criterion, **filters).all()`.

> **Returns:**

> - `list[self]`: List of instances for method chaining.

> **Example:**

> ```python
> users = await User.find_all(age__gte=18)
> ```

### order_by
```python
def order_by(*columns: str | InstrumentedAttribute | UnaryExpression)
```

> Creates a query with ORDER BY clause.

> **Parameters:**

> - `columns`: Column names or SQLAlchemy column expressions.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Example:**

> ```python
> # String column names (Django style)
> users = await User.order_by('-created_at', 'name').all()
>
> # SQLAlchemy expressions
> users = await User.order_by(User.created_at.desc(), User.name).all()
> ```

### sort
```python
def sort(*columns: str | InstrumentedAttribute | UnaryExpression)
```

> Synonym for `order_by()`.

### offset
```python
def offset(offset: int)
```

> Creates a query with OFFSET clause.

> **Parameters:**

> - `offset`: Number of rows to skip.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Raises:**

> - `ValueError`: If offset is negative.

> **Example:**

> ```python
> users = await User.offset(10).all()
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

> Creates a query with LIMIT clause.

> **Parameters:**

> - `limit`: Maximum number of rows to return.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Raises:**

> - `ValueError`: If limit is negative.

> **Example:**

> ```python
> users = await User.limit(5).all()
> ```

### take
```python
def take(take: int)
```

> Synonym for `limit()`.

### join
```python
def join(*paths: QueryableAttribute | tuple[QueryableAttribute, bool])
```

> Creates a query with `LEFT OUTER JOIN` eager loading.

> When a tuple is passed, the second element must be boolean.
> If it is `True`, the join is `INNER JOIN`, otherwise `LEFT OUTER JOIN`.

> **Parameters:**

> - `paths`: Relationship attributes to join.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Example:**

> ```python
> comments = await Comment.join(
>     Comment.user,
>     (Comment.post, True)  # True means INNER JOIN
> ).all()
> ```

### with_subquery
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

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> **Example:**

> ```python
> users = await User.with_subquery(
>     User.posts,
>     (User.comments, True)  # True means selectin loading
> ).all()
> ```

### with_schema
```python
def with_schema(schema: dict)
```

> Creates a query with complex eager loading schema.

> Useful for complex cases where you need to load nested relationships in
> separate queries.

> **Parameters:**

> - `schema`: Dictionary defining the loading strategy.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

> ```python
> schema = {
>     User.posts: 'joined',
>     User.comments: ('subquery', {
>         Comment.user: 'joined'
>     })
> }
> users = await User.with_schema(schema).all()
> ```

### scalars
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

### first
```python
async def first()
```

> Fetches the first row.

> **Returns:**

> - `self | None`: Instance for method chaining or `None` if no matches.

> **Example:**

> ```python
> user = await User.first()
> ```

### one
```python
async def one()
```

> Fetches exactly one row.

> **Returns:**

> - `self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.one()  # Raises if not exactly one match
> ```

### one_or_none
```python
async def one_or_none()
```

> Fetches exactly one row or `None`.

> **Returns:**

> - `self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.one_or_none()
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

> **Returns:**

> - `list[self]`: List of instances.

> **Example:**

> ```python
> users = await User.all()
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

> **Returns:**

> - `sqlalchemy.engine.ScalarResult`: Scalars.

> **Example:**

> ```python
> result = await User.unique()
> users = result.all()
> ```

### unique_all
```python
async def unique_all()
```

> Fetches all unique rows.

> **Returns:**

> - `list[self]`: List of instances.

> **Example:**

> ```python
> users = await User.unique_all()
> ```

### unique_first
```python
async def unique_first()
```

> Fetches the first unique row.

> **Returns:**

> - `self | None`: Instance for method chaining or `None`.

> **Example:**

> ```python
> user = await User.unique_first()
> ```

### unique_one
```python
async def unique_one()
```

> Fetches exactly one unique row.

> **Returns:**

> - `self`: Instance for method chaining.

> **Raises:**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.unique_one()
> ```

### unique_one_or_none
```python
async def unique_one_or_none()
```

> Fetches exactly one unique row or `None`.

> **Returns:**

> - `self | None`: Instance for method chaining or `None`.

> **Raises:**

> - `MultipleResultsFound`: If multiple rows match.

> **Example:**

> ```python
> user = await User.unique_one_or_none()
> ```

### smart_query
```python
def smart_query(criterion=None, filters=None, sort_columns=None, sort_attrs=None, schema=None)
```

> Creates a query combining filtering, sorting, and eager loading.

> **Parameters:**

> - `criterion`: SQLAlchemy filter expressions.
> - `filters`: Django-style filters.
> - `sort_columns`: SQLAlchemy columns to sort by.
> - `sort_attrs`: String column names to sort by.
> - `schema`: Eager loading schema.

> **Returns:**

> - `AsyncQuery`: Async query instance for chaining.

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
