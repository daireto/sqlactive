# Smart Queries Mixin

The `SmartQueryMixin` class provides advanced query functionality for SQLAlchemy
models, allowing you to filter, sort, and eager load data in a single query,
making it easier to retrieve specific data from the database.

It uses the [`InspectionMixin`](inspection-mixin.md) class functionality.

!!! info

    This mixin is intended to extend the functionality of the
    [`ActiveRecordMixin`](active-record-mixin.md)
    on which the examples below are based. It is not intended to be used on its own.

## Core Features

### Smart Queries

Smart queries allow you to filter, sort, group and eager load data in a single query.

```python
users = await User.smart_query(
    criteria=(User.age >= 18,),
    filters={'name__like': '%Bob%'},
    sort_columns=(User.username,),
    sort_attrs=['-created_at'],
    group_columns=(User.username,),
    group_attrs=['age'],
    schema={User.posts: 'joined'}
).all()
```

### Filtering

You can filter data using native SQLAlchemy filter expressions.

```python
users = await User.smart_query(
    criteria=(User.age >= 18,)
).all()
```

Also, you can filter data using Django-like filter expressions.

```python
users = await User.smart_query(
    filters={'name__like': '%Bob%'}
).all()
```

### Sorting

You can sort data using native SQLAlchemy sort expressions with
the `sort_columns` parameter.

```python
users = await User.smart_query(
    sort_columns=(User.username,)
).all()
```

Also, you can sort data using Django-like sort expressions with
the `sort_attrs` parameter.

```python
users = await User.smart_query(
    sort_attrs=['-created_at']
).all()
```

### Grouping

You can group data using native SQLAlchemy group expressions with
the `group_columns` parameter.

```python
users = await User.smart_query(
    group_columns=(User.username,)
).all()
```

Also, you can group data using Django-like group expressions with
the `group_attrs` parameter.

```python
users = await User.smart_query(
    group_attrs=['age']
).all()
```

### Eager Loading

You can eager load relationships using various loading strategies
with the `schema` parameter.

```python
users = await User.smart_query(
    schema={User.posts: 'joined'}
).all()
```

## API Reference

The `SmartQueryMixin` class provides three low-level methods for building filter, sort
and eager load expressions:

* `filter_expr`: Builds filter expressions.
* `order_expr`: Builds order expressions.
* `eager_expr`: Builds eager load expressions.

!!! warning

    All relations used in filtering/sorting should be explicitly set,
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

### Methods

#### filter_expr
```python
@classmethod
def filter_expr(**filters: object) -> list
```

> Takes keyword arguments like
> ```python
> {'age_from': 5, 'subject_ids__in': [1,2]}
> ```
> and returns list of expressions like
> ```python
> [Product.age_from == 5, Product.subject_ids.in_([1,2])]
> ```

> !!! info
>
>     When using alias, for example:
>
>     ```python
>     alias = aliased(Product) # table name will be `product_1`
>     ```
>
>     the query cannot be executed like
>
>     ```python
>     db.query(alias).filter(*Product.filter_expr(age_from=5))
>     ```
>
>     because it will be compiled to
>
>     ```sql
>     SELECT * FROM product_1 WHERE product.age_from=5
>     ```
>
>     which is wrong. The select is made from `product_1` but filter is based on `product`.
>     Such filter will not work.<br><br>
>     A correct way to execute such query is
>
>     ```sql
>     SELECT * FROM product_1 WHERE product_1.age_from=5
>     ```
>
>     For such case, `filter_expr` can be called ON ALIAS:
>
>     ```python
>     alias = aliased(Product)
>     db.query(alias).filter(*alias.filter_expr(age_from=5))
>     ```

> **Parameters:**
> - `filters`: Django-style filters.

> **Returns:**
> - `list[sqlalchemy.sql.elements.BinaryExpression]`: List of filter expressions.

> **Raises:**
> - `KeyError`:
>     - If operator is not found in `_operators`.
>     - If attribute is not found in `filterable_attributes` property.

> **Example:**
> ```python
> db.query(Product).filter(
>     *Product.filter_expr(age_from=5, subject_ids__in=[1, 2]))
> # will compile to WHERE age_from = 5 AND subject_ids IN [1, 2]
>
> filters = {'age_from': 5, 'subject_ids__in': [1,2]}
> db.query(Product).filter(*Product.filter_expr(**filters))
> # will compile to WHERE age_from = 5 AND subject_ids IN [1, 2]
> ```

#### order_expr
```python
@classmethod
def order_expr(*columns: str) -> list[UnaryExpression]
```

> Takes list of columns to order by like
> ```python
> ['-first_name', 'phone']
> ```
> and returns list of expressions like
> ```python
> [desc(User.first_name), asc(User.phone)]
> ```

> **Parameters:**
> - `columns`: Django-style columns.

> **Returns:**
> - `list[sqlalchemy.sql.elements.UnaryExpression]`: List of sort expressions.

> **Raises:**
> - `KeyError`: If attribute is not sortable.

> **Example:**
> ```python
> db.query(User).order_by(*User.order_expr('-first_name'))
> # will compile to ORDER BY user.first_name DESC
>
> columns = ['-first_name', 'phone']
> db.query(User).order_by(*User.order_expr(*columns))
> # will compile to ORDER BY user.first_name DESC, user.phone ASC
> ```

#### columns_expr
```python
@classmethod
def columns_expr(*columns: str) -> list[UnaryExpression]
```

> Takes list of columns like
> ```python
> ['first_name', 'age']
> ```
> and returns list of expressions like
> ```python
> [User.first_name, User.age]
> ```

> **Parameters:**
> - `columns`: Django-style columns.

> **Returns:**
> - `list[sqlalchemy.sql.elements.UnaryExpression]`: List of column expressions.

> **Raises:**
> - `KeyError`: If attribute is not found.

> **Example:**
> ```python
> db.query(User).group_by(*User.columns_expr('first_name'))
> # will compile to GROUP BY user.first_name
>
> columns = ['first_name', 'age']
> db.query(User).group_by(*User.columns_expr(*columns))
> # will compile to GROUP BY user.first_name, user.age
> ```

#### eager_expr
```python
@classmethod
def eager_expr(
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
) -> list[_AbstractLoad]
```

> Takes schema like
> ```python
> schema = {
>     Post.user: JOINED,  # joinedload user
>     Post.comments: (SUBQUERY, {  # load comments in separate query
>         Comment.user: JOINED  # but, in this separate query, join user
>     })
> }
> ```
> and returns eager loading expressions like
> ```python
> [joinedload(Post.user), subqueryload(Post.comments).options(joinedload(Comment.user))]
> ```

> **Parameters:**
> - `schema`: Eager loading schema.

> **Returns:**
> - `list[sqlalchemy.orm.strategy_options._AbstractLoad]`: List of eager loading expressions.

> **Example:**
> ```python
> schema = {
>     User.posts: JOINED,
>     User.comments: (SUBQUERY, {Comment.post: SELECT_IN}),
> }
> users = await User.options(*User.eager_expr(schema)).unique_all()
> ```

#### smart_query
```python
@classmethod
def smart_query(
    cls,
    query: Select[tuple[Any, ...]],
    criteria: Sequence[_ColumnExpressionArgument[bool]] | None = None,
    filters: (
        dict[str, Any] | dict[OperatorType, Any] | list[dict[str, Any]] | list[dict[OperatorType, Any]] | None
    ) = None,
    sort_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
    sort_attrs: Sequence[str] | None = None,
    group_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
    group_attrs: Sequence[str] | None = None,
    schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
) -> Select[tuple[Any, ...]]:
```

> Creates a query combining filtering, sorting, grouping and eager loading.

> Does magic Django-like joins like `post___user___name__startswith='Bob'`
> (see https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships)

> Does filtering, sorting and eager loading at the same time.
> And if, say, filters and sorting need the same join,
> it will be done only once.

> It also supports SQLAlchemy syntax filter expressions like
> >>> db.query(User).filter(User.id == 1, User.name == 'Bob')
> >>> db.query(User).filter(or_(User.id == 1, User.name == 'Bob'))

> **Parameters:**
> - `query`: Query for the model.
> - `criteria`: SQLAlchemy syntax filter expressions.
> - `filters`: Django-like filter expressions.
> - `sort_columns`: Standalone sort columns.
> - `sort_attrs`: Django-like sort expressions.
> - `group_columns`: Standalone group columns.
> - `group_attrs`: Django-like group expressions.
> - `schema`: Schema for the eager loading.

> **Returns:**
> - `Select[tuple[Any, ...]]`: Smart query.

> **Raises:**
> - `KeyError`: If filter, sort or group path is incorrect.

> **Example:**
> ```python
> users = await User.smart_query(
>     criteria=[User.id == 1, User.name == 'Bob'],
>     filters={'name__startswith': 'Bob'},
>     sort_columns=[User.name],
>     group_columns=[User.name],
> ).all()
> ```
