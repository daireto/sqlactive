# ActiveRecordMixin API Reference

<!-- omit in toc -->
## Table of Contents
- [ActiveRecordMixin API Reference](#activerecordmixin-api-reference)
  - [Instance Methods](#instance-methods)
    - [`fill(**kwargs)`](#fillkwargs)
    - [`save()`](#save)
    - [`update(**kwargs)`](#updatekwargs)
    - [`edit(**kwargs)`](#editkwargs)
    - [`delete()`](#delete)
    - [`remove()`](#remove)
  - [Class Methods](#class-methods)
    - [`create(**kwargs)`](#createkwargs)
    - [`insert(**kwargs)`](#insertkwargs)
    - [`add(**kwargs)`](#addkwargs)
    - [`save_all(rows: Sequence[Self], refresh: bool = False)`](#save_allrows-sequenceself-refresh-bool--false)
    - [`create_all(rows: Sequence[Self], refresh: bool = False)`](#create_allrows-sequenceself-refresh-bool--false)
    - [`update_all(rows: Sequence[Self], refresh: bool = False)`](#update_allrows-sequenceself-refresh-bool--false)
    - [`delete_all(rows: Sequence[Self])`](#delete_allrows-sequenceself)
    - [`destroy(*ids: object)`](#destroyids-object)
    - [`get(pk: object)`](#getpk-object)
    - [`get_or_fail(pk: object)`](#get_or_failpk-object)
    - [`options(*args: ExecutableOption)`](#optionsargs-executableoption)
    - [`filter(*criterion: ColumnElement[Any], **filters: Any)`](#filtercriterion-columnelementany-filters-any)
    - [`where(*criterion: ColumnElement[Any], **filters: Any)`](#wherecriterion-columnelementany-filters-any)
    - [`find(*criterion: ColumnElement[Any], **filters: Any)`](#findcriterion-columnelementany-filters-any)
    - [`find_one(*criterion: ColumnElement[Any], **filters: Any)`](#find_onecriterion-columnelementany-filters-any)
    - [`find_one_or_none(*criterion: ColumnElement[Any], **filters: Any)`](#find_one_or_nonecriterion-columnelementany-filters-any)
    - [`find_all(*criterion: ColumnElement[Any], **filters: Any)`](#find_allcriterion-columnelementany-filters-any)
    - [`order_by(*columns: str | InstrumentedAttribute | UnaryExpression)`](#order_bycolumns-str--instrumentedattribute--unaryexpression)
    - [`sort(*columns: str | InstrumentedAttribute | UnaryExpression)`](#sortcolumns-str--instrumentedattribute--unaryexpression)
    - [`offset(offset: int)`](#offsetoffset-int)
    - [`skip(skip: int)`](#skipskip-int)
    - [`limit(limit: int)`](#limitlimit-int)
    - [`take(take: int)`](#taketake-int)
    - [`join(*paths: QueryableAttribute | tuple[QueryableAttribute, bool])`](#joinpaths-queryableattribute--tuplequeryableattribute-bool)
    - [`with_subquery(*paths: QueryableAttribute | tuple[QueryableAttribute, bool])`](#with_subquerypaths-queryableattribute--tuplequeryableattribute-bool)
    - [`with_schema(schema: dict)`](#with_schemaschema-dict)
    - [`scalars()`](#scalars)
    - [`first()`](#first)
    - [`one()`](#one)
    - [`one_or_none()`](#one_or_none)
    - [`fetch_one()`](#fetch_one)
    - [`fetch_one_or_none()`](#fetch_one_or_none)
    - [`all()`](#all)
    - [`fetch_all()`](#fetch_all)
    - [`to_list()`](#to_list)
    - [`unique()`](#unique)
    - [`unique_all()`](#unique_all)
    - [`unique_first()`](#unique_first)
    - [`unique_one()`](#unique_one)
    - [`unique_one_or_none()`](#unique_one_or_none)
    - [`smart_query(criterion=None, filters=None, sort_columns=None, sort_attrs=None, schema=None)`](#smart_querycriterionnone-filtersnone-sort_columnsnone-sort_attrsnone-schemanone)

## Instance Methods

### `fill(**kwargs)`
Fills the object with values from `kwargs` without saving to the database.

**Parameters:**
- **kwargs**: Key-value pairs of attributes to set.

**Returns:** The instance itself for method chaining.

**Raises:**
- **KeyError**: If attribute doesn't exist.

```python
user.fill(name='Bob', age=30)
```

### `save()`
Saves the current row to the database.

**Returns:** The saved instance for method chaining.

**Raises:** Any database errors are caught and will trigger a rollback.

```python
user = User(name='Bob')
await user.save()
```

### `update(**kwargs)`
Updates the current row with the provided values.

**Parameters:**
- **kwargs**: Key-value pairs of attributes to update.

**Returns:** The updated instance for method chaining.

**Raises:** Any database errors are caught and will trigger a rollback.

```python
await user.update(name='Bob2', age=31)
```

### `edit(**kwargs)`
Synonym for `update()`.

### `delete()`
Deletes the current row from the database.

**Raises:** Any database errors are caught and will trigger a rollback.

```python
await user.delete()
```

### `remove()`
Synonym for `delete()`.

## Class Methods

### `create(**kwargs)`
Creates a new row with the provided values.

**Parameters:**
- **kwargs**: Key-value pairs for the new instance.

**Returns:** The created instance for method chaining.

**Raises:** Any database errors are caught and will trigger a rollback.

```python
user = await User.create(name='Bob', age=30)
```

### `insert(**kwargs)`
Synonym for `create()`.

### `add(**kwargs)`
Synonym for `create()`.

### `save_all(rows: Sequence[Self], refresh: bool = False)`
Saves multiple rows in a single transaction.

**Parameters:**
- **rows**: Sequence of model instances to save.
- **refresh**: Whether to refresh the instances after saving (default: False).

**Raises:** Any database errors are caught and will trigger a rollback.

```python
users = [User(name='Bob'), User(name='Alice')]
await User.save_all(users)
```

### `create_all(rows: Sequence[Self], refresh: bool = False)`
Synonym for `save_all()` when creating new rows.

### `update_all(rows: Sequence[Self], refresh: bool = False)`
Synonym for `save_all()` when updating existing rows.

### `delete_all(rows: Sequence[Self])`
Deletes multiple rows in a single transaction.

**Parameters:**
- **rows**: Sequence of model instances to delete.

**Raises:** Any database errors are caught and will trigger a rollback.

```python
users = await User.where(age__lt=18).all()
await User.delete_all(users)
```

### `destroy(*ids: object)`
Deletes multiple rows by their primary keys.

**Parameters:**
- **ids**: Primary key values of rows to delete.

**Raises:** Any database errors are caught and will trigger a rollback.

```python
await User.destroy(1, 2, 3)  # Deletes users with IDs 1, 2, and 3
```

### `get(pk: object)`
Fetches a row by primary key.

**Parameters:**
- **pk**: Primary key value.

**Returns:** Instance for method chaining or `None` if not found.

**Raises:**
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.get(1)
```

### `get_or_fail(pk: object)`
Fetches a row by primary key or raises an exception if not found.

**Parameters:**
- **pk**: Primary key value.

**Returns:** Instance for method chaining.

**Raises:**
- **NoResultFound**: If no row is found.
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.get_or_fail(1)  # Raises if not found
```

### `options(*args: ExecutableOption)`
Creates a query and applies the given list of mapper options.

> [!IMPORTANT]
> Quoting from https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading:
>>    When including `joinedload()` in reference to a one-to-many or
>>    many-to-many collection, the `Result.unique()` method must be
>>    applied to the returned result, which will make the incoming rows
>>    unique by primary key that otherwise are multiplied out by the join.
>>    The ORM will raise an error if this is not present.
>>
>>    This is not automatic in modern SQLAlchemy, as it changes the behavior
>>    of the result set to return fewer ORM objects than the statement would
>>    normally return in terms of number of rows. Therefore SQLAlchemy keeps
>>    the use of Result.unique() explicit, so there is no ambiguity that the
>>    returned objects are made unique on primary key.

To learn more about options, see
https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.options

**Parameters:**
- **args**: Mapper options.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

```python
users = await User.options(joinedload(User.posts)).unique_all()

user = await User.options(joinedload(User.posts)).first()

users = await User.options(subqueryload(User.posts)).all()
```

### `filter(*criterion: ColumnElement[Any], **filters: Any)`
Creates a filtered query using SQLAlchemy or Django-style filters.

**Parameters:**
- **criterion**: SQLAlchemy style filter expressions.
- **filters**: Django-style filters.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

```python
# SQLAlchemy style
users = await User.filter(User.age >= 18).all()

# Django style
users = await User.filter(age__gte=18).all()

# Mixed
users = await User.filter(User.age >= 18, name__like='%Bob%').all()
```

### `where(*criterion: ColumnElement[Any], **filters: Any)`
Synonym for `filter()`.

### `find(*criterion: ColumnElement[Any], **filters: Any)`
Synonym for `filter()`.

### `find_one(*criterion: ColumnElement[Any], **filters: Any)`
Finds a single row matching the criteria.

This is same as calling `await cls.find(*criterion, **filters).one()`.

**Returns:** Instance for method chaining.

**Raises:**
- **NoResultFound**: If no row is found.
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.find_one(name='Bob')  # Raises if not found
```

### `find_one_or_none(*criterion: ColumnElement[Any], **filters: Any)`
Finds a single row matching the criteria or `None`.

This is same as calling `await cls.find(*criterion, **filters).one_or_none()`.

**Returns:** Instance for method chaining or `None`.

**Raises:**
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.find_one_or_none(name='Bob')  # Returns None if not found
```

### `find_all(*criterion: ColumnElement[Any], **filters: Any)`
Finds all rows matching the criteria.

This is same as calling `await cls.find(*criterion, **filters).all()`.

**Returns:** List of instances for method chaining.

```python
users = await User.find_all(age__gte=18)
```

### `order_by(*columns: str | InstrumentedAttribute | UnaryExpression)`
Creates a query with ORDER BY clause.

**Parameters:**
- **columns**: Column names or SQLAlchemy column expressions.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

```python
# String column names (Django style)
users = await User.order_by('-created_at', 'name').all()

# SQLAlchemy expressions
users = await User.order_by(User.created_at.desc(), User.name).all()
```

### `sort(*columns: str | InstrumentedAttribute | UnaryExpression)`
Synonym for `order_by()`.

### `offset(offset: int)`
Creates a query with OFFSET clause.

**Parameters:**
- **offset**: Number of rows to skip.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

**Raises:**
- **ValueError**: If offset is negative.

```python
users = await User.offset(10).all()
```

### `skip(skip: int)`
Synonym for `offset()`.

### `limit(limit: int)`
Creates a query with LIMIT clause.

**Parameters:**
- **limit**: Maximum number of rows to return.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

**Raises:** ValueError if limit is negative.

```python
users = await User.limit(5).all()
```

### `take(take: int)`
Synonym for `limit()`.

### `join(*paths: QueryableAttribute | tuple[QueryableAttribute, bool])`
Creates a query with `LEFT OUTER JOIN` eager loading.

When a tuple is passed, the second element must be boolean.
If it is `True`, the join is `INNER JOIN`, otherwise `LEFT OUTER JOIN`.

**Parameters:**
- **paths**: Relationship attributes to join.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

```python
comments = await Comment.join(
    Comment.user,
    (Comment.post, True)  # True means INNER JOIN
).all()
```

### `with_subquery(*paths: QueryableAttribute | tuple[QueryableAttribute, bool])`
Creates a query with subquery or selectin loading.

Emits a second `SELECT` statement (Subqueryload) for each relationship
to be loaded, across all result objects at once.

When a tuple is passed, the second element must be boolean.
If it is `True`, the eager loading strategy is `SELECT IN` (Selectinload),
otherwise `SELECT JOIN` (Subqueryload).

> [!IMPORTANT]
> A query which makes use of `subqueryload()` in conjunction with a limiting
> modifier such as `Query.limit()` or `Query.offset()` should always include
> `Query.order_by()` against unique column(s) such as the primary key,
> so that the additional queries emitted by `subqueryload()` include the same
> ordering as used by the parent query. Without it, there is a chance that
> the inner query could return the wrong rows, as specified in
> https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering
> ```python
> # incorrect, no ORDER BY
> User.options(subqueryload(User.addresses)).first()
>
> # incorrect if User.name is not unique
> User.options(subqueryload(User.addresses)).order_by(User.name).first()
>
> # correct
> User.options(subqueryload(User.addresses)).order_by(
>     User.name, User.id
> ).first()
> ```

**Parameters:**
- **paths**: Relationship attributes to load.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

```python
users = await User.with_subquery(
    User.posts,
    (User.comments, True)  # True means selectin loading
).all()
```

### `with_schema(schema: dict)`
Creates a query with complex eager loading schema.

Useful for complex cases where you need to load nested relationships in
separate queries.

**Parameters:**
- **schema**: Dictionary defining the loading strategy.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

```python
schema = {
    User.posts: 'joined',
    User.comments: ('subquery', {
        Comment.user: 'joined'
    })
}
users = await User.with_schema(schema).all()
```

### `scalars()`
Returns a `sqlalchemy.engine.ScalarResult` object containing all rows.

**Returns:** `sqlalchemy.engine.ScalarResult` instance.

```python
result = await User.scalars()
users = result.all()
```

### `first()`
Fetches the first row.

**Returns:** Instance for method chaining or `None` if no matches.

```python
user = await User.first()
```

### `one()`
Fetches exactly one row.

**Returns:** Instance for method chaining.

**Raises:**
- **NoResultFound**: If no row is found.
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.one()  # Raises if not exactly one match
```

### `one_or_none()`
Fetches exactly one row or `None`.

**Returns:** Instance for method chaining or `None`.

**Raises:**
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.one_or_none()
```

### `fetch_one()`
Synonym for `one()`.

### `fetch_one_or_none()`
Synonym for `one_or_none()`.

### `all()`
Fetches all rows.

**Returns:** List of instances.

```python
users = await User.all()
```

### `fetch_all()`
Synonym for `all()`.

### `to_list()`
Synonym for `all()`.

### `unique()`
Returns a `sqlalchemy.engine.ScalarResult` object containing all unique rows.

**Returns:** `sqlalchemy.engine.ScalarResult` instance.

```python
result = await User.unique()
users = result.all()
```

### `unique_all()`
Fetches all unique rows.

**Returns:** List of instances.

```python
users = await User.unique_all()
```

### `unique_first()`
Fetches the first unique row.

**Returns:** Instance for method chaining or `None`.

```python
user = await User.unique_first()
```

### `unique_one()`
Fetches exactly one unique row.

**Returns:** Instance for method chaining.

**Raises:**
- **NoResultFound**: If no row is found.
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.unique_one()
```

### `unique_one_or_none()`
Fetches exactly one unique row or `None`.

**Returns:** Instance for method chaining or `None`.

**Raises:**
- **MultipleResultsFound**: If multiple rows match.

```python
user = await User.unique_one_or_none()
```

### `smart_query(criterion=None, filters=None, sort_columns=None, sort_attrs=None, schema=None)`
Creates a query combining filtering, sorting, and eager loading.

**Parameters:**
- **criterion**: SQLAlchemy filter expressions.
- **filters**: Django-style filters.
- **sort_columns**: SQLAlchemy columns to sort by.
- **sort_attrs**: String column names to sort by.
- **schema**: Eager loading schema.

**Returns:** [`AsyncQuery`](/sqlactive/async_query.py) instance for chaining.

```python
users = await User.smart_query(
    criterion=(User.age >= 18,),
    filters={'name__like': '%Bob%'},
    sort_columns=(User.username,),
    sort_attrs=['-created_at'],
    schema={User.posts: 'joined'}
).all()
```
