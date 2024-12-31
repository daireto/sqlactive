# SmartQueryMixin

The `SmartQueryMixin` class provides advanced query functionality for SQLAlchemy
models, allowing you to filter, sort, and eager load data in a single query,
making it easier to retrieve specific data from the database.

It uses the [`InspectionMixin`](INSPECTION_MIXIN.md) class functionality.

!!! info

    This mixin is intended to extend the functionality of the
    [`ActiveRecordMixin`](active_record_mixin/OVERVIEW.md)
    on which the examples below are based. It is not intended to be used on its own.

**Table of Contents**

- [SmartQueryMixin](#smartquerymixin)
  - [Core Features](#core-features)
    - [Smart Queries](#smart-queries)
    - [Filtering](#filtering)
    - [Sorting](#sorting)
    - [Eager Loading](#eager-loading)
  - [API Reference](#api-reference)
    - [filter\_expr](#filter_expr)
    - [order\_expr](#order_expr)
    - [eager\_expr](#eager_expr)

## Core Features

### Smart Queries

Smart queries allow you to filter, sort, and eager load data in a single query.

```python
users = await User.smart_query(
    criterion=(User.age >= 18,),
    filters={'name__like': '%Bob%'},
    sort_columns=(User.username,),
    sort_attrs=['-created_at'],
    schema={User.posts: 'joined'}
).all()
```

### Filtering

You can filter data using native SQLAlchemy filter expressions.

```python
users = await User.smart_query(
    criterion=(User.age >= 18,)
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

### filter_expr
```python
def filter_expr(**filters: object)
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

### order_expr
```python
def order_expr(*columns: str)
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

### eager_expr
```python
def eager_expr(schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict])
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
