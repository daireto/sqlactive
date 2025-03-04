# Smart Query Mixin

The `SmartQueryMixin` class provides advanced query functionality for SQLAlchemy
models, allowing you to filter, sort, group and eager load data in a single
query, making it easier to retrieve specific data from the database.

It uses the functionality of the [`Inspection Mixin`](inspection-mixin.md).

???+ info

    This mixin is intended to extend the functionality of the
    [`Active Record Mixin`](active-record-mixin.md) which the
    examples below are based on. It also extends the functionality
    of the [`Async Query`](async-query.md) wrapper. It is not
    intended to be used on its own.

???+ warning

    All relations used in filtering/sorting/grouping should be explicitly set,
    not just being a `backref`. See the
    [About Relationships](active-record-mixin.md#about-relationships) section
    for more information.

???+ info

    The examples below assume the following models:

    ```python
    from sqlalchemy import ForeignKey, String
    from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from sqlactive.base_model import ActiveRecordBaseModel


    class BaseModel(ActiveRecordBaseModel):
        __abstract__ = True


    class User(BaseModel):
        __tablename__ = 'users'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        username: Mapped[str] = mapped_column(
            String(18), nullable=False, unique=True
        )
        name: Mapped[str] = mapped_column(String(50), nullable=False)
        age: Mapped[int] = mapped_column(nullable=False)

        posts: Mapped[list['Post']] = relationship(back_populates='user')
        comments: Mapped[list['Comment']] = relationship(back_populates='user')

        @hybrid_property
        def is_adult(self) -> int:
            return self.age > 18

        @hybrid_method
        def older_than(self, other: 'User') -> bool:
            return self.age > other.age


    class Post(BaseModel):
        __tablename__ = 'posts'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        title: Mapped[str] = mapped_column(String(100), nullable=False)
        body: Mapped[str] = mapped_column(nullable=False)
        rating: Mapped[int] = mapped_column(nullable=False)
        user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

        user: Mapped['User'] = relationship(back_populates='posts')
        comments: Mapped[list['Comment']] = relationship(back_populates='post')


    class Comment(BaseModel):
        __tablename__ = 'comments'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        body: Mapped[str] = mapped_column(nullable=False)
        post_id: Mapped[int] = mapped_column(ForeignKey('posts.id'))
        user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

        post: Mapped['Post'] = relationship(back_populates='comments')
        user: Mapped['User'] = relationship(back_populates='comments')


    class Product(BaseModel):
        __tablename__ = 'products'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        description: Mapped[str] = mapped_column(String(100), nullable=False)
        price: Mapped[float] = mapped_column(nullable=False)

        sells: Mapped[list['Sell']] = relationship(
            back_populates='product', viewonly=True
        )


    class Sell(BaseModel):
        __tablename__ = 'sells'

        id: Mapped[int] = mapped_column(primary_key=True)
        product_id: Mapped[int] = mapped_column(
            ForeignKey('products.id'), primary_key=True
        )
        quantity: Mapped[int] = mapped_column(nullable=False)

        product: Mapped['Product'] = relationship(back_populates='sells')
    ```

## Core Features

### Smart Queries

Smart queries allow you to filter, sort, group and eager load data
in a single query.

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

### Searching

You can search data using the `search` method.

```python
users = await User.search(
    query=User.query,
    search_term='Bob',
    columns=(User.name, User.username),
).all()
```

## API Reference

The `SmartQueryMixin` class provides three low-level methods for building
filter, sort, group and eager load expressions:

* `filter_expr`: Builds filter expressions.
* `order_expr`: Builds order expressions.
* `columns_expr`: Builds column expressions.
* `eager_expr`: Builds eager load expressions.
* `smart_query`: Builds a smart query (filter, sort, group and eager load).
* `apply_search_filter`: Applies a search filter to the query.

### Filter Operators

The `SmartQueryMixin` class provides a set of Django-like filter operators
for building filter expressions.

#### isnull

> Whether the value is null.

> ```pycon
> >>> posts = await Post.where(topic__isnull=True).all()
> >>> post.topic is None for post in posts
> True
> >>> posts = await Post.where(topic__isnull=False).all()
> >>> post.topic is not None for post in posts
> True
> ```

#### exact

> Equal to.

> ```pycon
> >>> users = await User.where(age__exact=25).all()
> >>> all([user.age == 25 for user in users])
> True
> ```

#### eq

> Same as [`exact`](#exact).

> ```pycon
> >>> users = await User.where(age__eq=25).all()
> >>> all([user.age == 25 for user in users])
> True
> ```

#### ne

> Not equal to.

> ```pycon
> >>> users = await User.where(age__ne=25).all()
> >>> all([user.age != 25 for user in users])
> True
> ```

#### gt

> Greater than.

> ```pycon
> >>> users = await User.where(age__gt=25).all()
> >>> all([user.age > 25 for user in users])
> True
> ```

#### ge

> Greater than or equal to.

> ```pycon
> >>> users = await User.where(age__ge=25).all()
> >>> all([user.age >= 25 for user in users])
> True
> ```

#### lt

> Less than.

> ```pycon
> >>> users = await User.where(age__lt=25).all()
> >>> all([user.age < 25 for user in users])
> True
> ```

#### le

> Less than or equal to.

> ```pycon
> >>> users = await User.where(age__le=25).all()
> >>> all([user.age <= 25 for user in users])
> True
> ```

#### in

> Included in.

> ```pycon
> >>> users = await User.where(age__in=[20, 30]).all()
> >>> all([user.age == 20 or user.age == 30 for user in users])
> True
> ```

#### notin

> Not included in.

> ```pycon
> >>> users = await User.where(age__notin=[20, 30]).all()
> >>> all([user.age != 20 and user.age != 30 for user in users])
> True
> ```

#### between

> Inside a range.

> ```pycon
> >>> await User.where(age__between=[20, 30]).all()
> >>> all([user.age >= 20 and user.age <= 30 for user in users])
> True
> ```

#### like

> SQL `LIKE` clause.

> ```pycon
> >>> await User.where(username__like='Ji%').all()
> >>> all([user.username.startswith('Ji') for user in users])
> True
> ```

#### ilike

> Case-insensitive SQL `LIKE` clause for PostgreSQL.

> When used with other backends, such as MySQL, is the same as [`like`](#like).

> ```pycon
> >>> await User.where(username__ilike='ji%').all()
> >>> all([user.username.startswith('Ji') for user in users])
> True
> ```

#### startswith

> Start with.

> ```pycon
> >>> await User.where(username__startswith='Ji').all()
> >>> all([user.username.startswith('Ji') for user in users])
> True
> ```

#### istartswith

> Case-insensitive start with.

> ```pycon
> >>> await User.where(username__istartswith='ji').all()
> >>> all([user.username.startswith('Ji') for user in users])
> True
> ```

#### endswith

> End with.

> ```pycon
> >>> await User.where(name__endswith='Anderson').all()
> >>> all([user.name.endswith('Anderson') for user in users])
> True
> ```

#### iendswith

> Case-insensitive end with.

> ```pycon
> >>> await User.where(name__iendswith='anderson').all()
> >>> all([user.name.endswith('Anderson') for user in users])
> True
> ```

#### contains

> Contains a substring (case-insensitive).

> ```pycon
> >>> await User.where(name__contains='Wa').all()
> >>> all(['wa' in user.name.lower() for user in users])
> True
> ```

#### year

> Date year is equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__year=today.year).all()
> >>> all([user.created_at.year == today.year for user in users])
> True
> ```

#### year_ne

> Date year is not equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__year_ne=today.year).all()
> >>> all([user.created_at.year != (today.year - 1) for user in users])
> True
> ```

#### year_gt

> Date year is greater than.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__year_gt=today.year).all()
> >>> all([user.created_at.year > (today.year - 1) for user in users])
> True
> ```

#### year_ge

> Date year is greater than or equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__year_ge=today.year).all()
> >>> all([user.created_at.year >= (today.year - 1) for user in users])
> True
> ```

#### year_lt

> Date year is less than.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__year_lt=today.year).all()
> >>> all([user.created_at.year < (today.year + 1) for user in users])
> True
> ```

#### year_le

> Date year is less than or equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__year_le=today.year).all()
> >>> all([user.created_at.year <= (today.year + 1) for user in users])
> True
> ```

#### month

> Date month is equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__month=today.month).all()
> >>> all([user.created_at.month == today.month for user in users])
> True
> ```

#### month_ne

> Date month is not equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__month_ne=today.month).all()
> >>> all([user.created_at.month != (today.month - 1) for user in users])
> True
> ```

#### month_gt

> Date month is greater than.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__month_gt=today.month).all()
> >>> all([user.created_at.month > (today.month - 1) for user in users])
> True
> ```

#### month_ge

> Date month is greater than or equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__month_ge=today.month).all()
> >>> all([user.created_at.month >= (today.month - 1) for user in users])
> True
> ```

#### month_lt

> Date month is less than.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__month_lt=today.month).all()
> >>> all([user.created_at.month < (today.month + 1) for user in users])
> True
> ```

#### month_le

> Date month is less than or equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__month_le=today.month).all()
> >>> all([user.created_at.month <= (today.month + 1) for user in users])
> True
> ```

#### day

> Date day is equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__day=today.day).all()
> >>> all([user.created_at.day == today.day for user in users])
> True
> ```

#### day_ne

> Date day is not equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__day_ne=today.day).all()
> >>> all([user.created_at.day != (today.day - 1) for user in users])
> True
> ```

#### day_gt

> Date day is greater than.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__day_gt=today.day).all()
> >>> all([user.created_at.day > (today.day - 1) for user in users])
> True
> ```

#### day_ge

> Date day is greater than or equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__day_ge=today.day).all()
> >>> all([user.created_at.day >= (today.day - 1) for user in users])
> True
> ```

#### day_lt

> Date day is less than.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__day_lt=today.day).all()
> >>> all([user.created_at.day < (today.day + 1) for user in users])
> True
> ```

#### day_le

> Date day is less than or equal to.

> ```pycon
> >>> from datetime import datetime
> >>> today = datetime.today()
> >>> await User.where(created_at__day_le=today.day).all()
> >>> all([user.created_at.day <= (today.day + 1) for user in users])
> True
> ```

### Methods

#### filter_expr

```python
@classmethod
def filter_expr(**filters: object) -> list[ColumnElement[Any]]
```

> Transform Django-style filters into SQLAlchemy expressions.
>
> Takes keyword arguments like:
> ```python
> {'rating': 5, 'user_id__in': [1,2]}
> ```
> and returns list of expressions like:
> ```python
> [Post.rating == 5, Post.user_id.in_([1,2])]
> ```

> ???+ info "About alias"
>
>     When using alias, for example:
>
>     ```python
>     alias = aliased(Post) # table name will be `post_1`
>     ```
>
>     the query cannot be executed like
>
>     ```python
>     db.query(alias).filter(*Post.filter_expr(rating=5))
>     ```
>
>     because it will be compiled to
>
>     ```sql
>     SELECT * FROM post_1 WHERE post.rating=5
>     ```
>
>     which is wrong. The select is made from `post_1` but filter is based
>     on `post`. Such filter will not work.
>
>     A correct way to execute such query is
>
>     ```sql
>     SELECT * FROM post_1 WHERE post_1.rating=5
>     ```
>
>     For such case, this method (and other methods like
>     [`order_expr()`](#order_expr) and [`columns_expr()`](#columns_expr))
>     can be called ON ALIAS:
>
>     ```python
>     alias = aliased(Post)
>     db.query(alias).filter(*alias.filter_expr(rating=5))
>     ```

> ???+ note
>
>     This is a very low-level method. It is intended for more
>     flexibility. It does not do magic Django-like joins.
>     Use the high-level [`smart_query()`](#smart_query) method for that.

> **Parameters**

> - `filters`: Django-style filters.

> **Returns**

> - `list[sqlalchemy.sql.elements.ColumnElement[Any]]`: Filter expressions.

> **Raises**

> - `OperatorError`: If operator is not found.
> - `NoFilterableError`: If attribute is not filterable.

> **Examples**

> Usage:
> ```pycon
> >>> Post.filter_expr(rating=5)
> [Post.rating == 5]
> >>> db.query(Post).filter(*Post.filter_expr(rating=5))
> SELECT * FROM posts WHERE post.rating=5
> >>> Post.filter_expr(rating=5, user_id__in=[1,2])
> [Post.rating == 5, Post.user_id.in_([1,2])]
> >>> db.query(Post).filter(
> ...     *Post.filter_expr(rating=5, user_id__in=[1,2])
> ... )
> SELECT * FROM posts WHERE post.rating=5 AND post.user_id IN [1, 2]
> ```

> Using alias:
> ```pycon
> >>> alias = aliased(Post)
> >>> alias.filter_expr(rating=5)
> [Post.rating == 5]
> >>> db.query(alias).filter(*alias.filter_expr(rating=5))
> SELECT * FROM post_1 WHERE post_1.rating=5
> >>> alias.filter_expr(rating=5, user_id__in=[1,2])
> [Post.rating == 5, Post.user_id.in_([1,2])]
> >>> db.query(alias).filter(
> ...     *alias.filter_expr(rating=5, user_id__in=[1,2])
> ... )
> SELECT * FROM post_1 WHERE post_1.rating=5 AND post_1.user_id IN [1, 2]
> ```

#### order_expr

```python
@classmethod
def order_expr(*columns: str) -> list[ColumnElement[Any]]
```

> Transforms Django-style order expressions into SQLAlchemy expressions.
>
> Takes list of columns to order by like:
> ```python
> ['-rating', 'title']
> ```
> and returns list of expressions like:
> ```python
> [desc(Post.rating), asc(Post.title)]
> ```

> ???+ info "About alias"
>
>     See the [`filter_expr()`](#filter_expr) method documentation for more
>     information about using alias.

> ???+ note
>
>     This is a very low-level method. It is intended for more
>     flexibility. It does not do magic Django-like joins.
>     Use the high-level [`smart_query()`](#smart_query) method for that.

> **Parameters**

> - `columns`: Django-style sort expressions.

> **Returns**

> - `list[sqlalchemy.sql.elements.ColumnElement[Any]]`: Sort expressions.

> **Raises**

> - `NoSortableError`: If attribute is not sortable.

> **Examples**

> Usage:
> ```pycon
> >>> Post.order_expr('-rating')
> [desc(Post.rating)]
> >>> db.query(Post).order_by(*Post.order_expr('-rating'))
> SELECT * FROM posts ORDER BY posts.rating DESC
> >>> Post.order_expr('-rating', 'title')
> [desc(Post.rating), asc(Post.title)]
> >>> db.query(Post).order_by(
> ...     *Post.order_expr('-rating', 'title')
> ... )
> SELECT * FROM posts ORDER BY posts.rating DESC, posts.title ASC
> ```

> Using alias:
> ```pycon
> >>> alias = aliased(Post)
> >>> alias.order_expr('-rating')
> [desc(Post.rating)]
> >>> db.query(alias).order_by(*alias.order_expr('-rating'))
> SELECT * FROM posts_1 ORDER BY posts_1.rating DESC
> >>> alias.order_expr('-rating', 'title')
> [desc(Post.rating), asc(Post.title)]
> >>> db.query(alias).order_by(*alias.order_expr('-rating', 'title'))
> SELECT * FROM posts_1 ORDER BY posts_1.rating DESC, posts_1.title ASC
> ```

#### columns_expr

```python
@classmethod
def columns_expr(*columns: str) -> list[ColumnElement[Any]]
```

> Transforms column names into SQLAlchemy model attributes.
>
> Takes list of column names like:
> ```python
> ['user_id', 'rating']
> ```
> and returns list of model attributes like:
> ```python
> [Post.user_id, Post.rating]
> ```
> This method mostly used for grouping.

> ???+ info "About alias"
>
>     See the [`filter_expr()`](#filter_expr) method documentation for more
>     information about using alias.

> ???+ note
>
>     This is a very low-level method. It is intended for more
>     flexibility. It does not do magic Django-like joins.
>     Use the high-level [`smart_query()`](#smart_query) method for that.

> **Parameters**

> - `columns`: Column names.

> **Returns**

> - `list[sqlalchemy.sql.elements.ColumnElement[Any]]`: Model attributes.

> **Raises**

> - `NoColumnOrHybridPropertyError`: If attribute is neither a column nor a
> hybrid property.

> **Examples**

> Usage:
> ```pycon
> >>> Post.columns_expr('user_id')
> [Post.user_id]
> >>> Post.columns_expr('user_id', 'rating')
> [Post.user_id, Post.rating]
> ```

> Grouping:
> ```pycon
> >>> from sqlalchemy.sql import func
> >>> db.query(Post.user_id, func.max(Post.rating))
> ...   .group_by(*Post.columns_expr('user_id'))
> SELECT posts.user_id, max(posts.rating) FROM posts GROUP BY posts.user_id
> >>> db.query(Post.user_id, Post.rating)
> ...   .group_by(*Post.columns_expr('user_id', 'rating'))
> SELECT posts.user_id, posts.rating FROM posts GROUP BY posts.user_id, posts.rating
> ```

> Using alias:
> ```pycon
> >>> alias = aliased(Post)
> >>> alias.columns_expr('user_id')
> [Post.user_id]
> >>> alias.columns_expr('user_id', 'rating')
> [Post.user_id, Post.rating]
> ```

> Grouping on alias:
> ```pycon
> >>> db.query(alias.user_id, func.max(alias.rating))
> ...   .group_by(*alias.columns_expr('user_id'))
> SELECT posts_1.user_id FROM posts_1 GROUP BY posts_1.user_id
> >>> db.query(alias.user_id, alias.rating)
> ...   .group_by(*alias.columns_expr('user_id', 'rating'))
> SELECT posts_1.user_id, posts_1.rating FROM posts_1 GROUP BY posts_1.user_id, posts_1.rating
> ```

#### eager_expr

```python
@classmethod
def eager_expr(schema: EagerSchema) -> list[_AbstractLoad]
```

> Transforms an eager loading defined schema into SQLAlchemy
> eager loading expressions.
>
> Takes a schema like:
> ```python
> schema = {
>     Post.user: 'joined',           # joinedload user
>     Post.comments: ('subquery', {  # load comments in separate query
>         Comment.user: 'joined'     # but, in this separate query, join user
>     })
> }
> ```
> and returns eager loading expressions like:
> ```python
> [
>     joinedload(Post.user),
>     subqueryload(Post.comments).options(
>         joinedload(Comment.user)
>     )
> ]
> ```

> The supported eager loading strategies are:
> - `'joined'`: `sqlalchemy.orm.joinedload()`
> - `'subquery'`: `sqlalchemy.orm.subqueryload()`
> - `'selectin'`: `sqlalchemy.orm.selectinload()`

> The constants `JOINED`, `SUBQUERY` and `SELECT_IN` are defined in the
> `sqlactive.definitions` module and can be used instead of the strings:
> ```pycon
> >>> from sqlactive.definitions import JOINED, SUBQUERY
> >>> schema = {
> ...     Post.user: JOINED,
> ...     Post.comments: (SUBQUERY, {
> ...         Comment.user: JOINED
> ...     })
> ... }
> ```

> **Parameters**

> - `schema`: Schema for the eager loading.

> **Returns**

> - `list[sqlalchemy.orm.strategy_options._AbstractLoad]`: Eager loading
> expressions.

> **Examples**

> ```pycon
> >>> schema = {
> ...     Post.user: JOINED,
> ...     Post.comments: (SUBQUERY, {Comment.user: SELECT_IN}),
> ... }
> >>> expressions = Post.eager_expr(schema)
> >>> post1 = await Post.options(*expressions).limit(1).unique_one()
> >>> post1.user.name
> Bob Williams
> >>> post1.comments[0].user.name
> Bob Williams
> ```

#### smart_query

```python
@classmethod
def smart_query(
    cls,
    query: Select[tuple[Any, ...]],
    criteria: Sequence[_ColumnExpressionArgument[bool]] | None = None,
    filters: DjangoFilters | None = None,
    sort_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
    sort_attrs: Sequence[str] | None = None,
    group_columns: Sequence[_ColumnExpressionOrStrLabelArgument[Any]] | None = None,
    group_attrs: Sequence[str] | None = None,
    schema: EagerSchema | None = None,
) -> Select[tuple[Any, ...]]:
```

> Creates a query combining filtering, sorting, grouping and eager loading.

> Does magic [`Django-like joins`](https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships)
> like:
> ```python
> post___user___name__startswith='Bob'
> ```

> Does filtering, sorting, grouping and eager loading at the same time.
> And if, say, filters, sorting and grouping need the same join, it will
> be done only once.

> It also supports SQLAlchemy syntax like:
> ```pycon
> >>> db.query(User).filter(User.id == 1, User.name == 'Bob')
> >>> db.query(User).filter(or_(User.id == 1, User.name == 'Bob'))
> >>> db.query(Post).order_by(Post.rating.desc())
> >>> db.query(Post).order_by(desc(Post.rating), asc(Post.user_id))
> ```

> ???+ note
>
> For more flexibility, you can use the [`filter_expr()`](#filter_expr),
> [`order_expr()`](#order_expr), [`columns_expr()`](#columns_expr) and
> [`eager_expr()`](#eager_expr) methods.

> **Parameters**

> - `query`: Native SQLAlchemy query.
> - `criteria`: SQLAlchemy syntax filter expressions.
> - `filters`: Django-like filter expressions.
> - `sort_columns`: Standalone sort columns.
> - `sort_attrs`: Django-like sort expressions.
> - `group_columns`: Standalone group columns.
> - `group_attrs`: Django-like group expressions.
> - `schema`: Schema for the eager loading.

> **Returns**

> - `Select[tuple[Any, ...]]`: SQLAlchemy query with filtering, sorting,
> grouping and eager loading, that is to say, a beautiful smart query.

> **Examples**

> ```pycon
> >>> query = User.smart_query(
> ...     criteria=(or_(User.age == 30, User.age == 32),),
> ...     filters={'username__like': '%8'},
> ...     sort_columns=(User.username,),
> ...     sort_attrs=('age',),
> ...     schema={
> ...         User.posts: JOINED,
> ...         User.comments: (SUBQUERY, {
> ...             Comment.post: SELECT_IN
> ...         })
> ...     },
> ... )
> >>> users = await query.unique_all()
> >>> [user.username for user in users]
> ['Bob28', 'Ian48', 'Jessica3248']
> >>> users[0].posts[0].title
> Lorem ipsum
> >>> users[0].comments[0].post.title
> Lorem ipsum
> ```

#### apply_search_filter

```python
@classmethod
def apply_search_filter(
    query: Select[tuple[Any, ...]],
    search_term: str,
    columns: Sequence[str | InstrumentedAttribute[Any]] | None = None,
) -> Select[tuple[Any, ...]]
```

> Applies a search filter to the query.

> Searches for `search_term` in the [searchable columns](inspection-mixin.md#searchable_attributes)
> of the model. If `columns` are provided, searches only these columns.

> **Parameters**

> - `query`: Native SQLAlchemy query.
> - `search_term`: Search term.
> - `columns`: Columns to search in.

> **Returns**

> - `Select[tuple[Any, ...]]`: SQLAlchemy query with the search filter applied.

> **Examples**

To learn how to use this method, see the [`search()`](active-record-mixin.md#search) method. It uses this method internally.
