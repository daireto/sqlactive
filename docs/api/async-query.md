# Async Query

The `AsyncQuery` class is an Async wrapper for `sqlalchemy.sql.Select`.

It implements the functionality of both [`Session`](session-mixin.md)
and [`Smart Queries`](smart-query-mixin.md) mixins.

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

## Usage

The `AsyncQuery` class provides a set of helper methods for asynchronously
executing the query.

### Setting the Session

This class needs an `sqlalchemy.ext.asyncio.async_scoped_session`
instance to perform the actual query. The `set_session` class
method must be called before using this class.

When calling the `set_session` method from a base model
(either `ActiveRecordBaseModel`, a subclass of it or a model,
i.e. `User`), the session will be set automatically.

> Calling `set_session` from either a base model or a model:
>
> ```python
> # from your base model class (recommended)
> YourBaseModel.set_session(session)
>
> # from the ActiveRecordBaseModel class
> ActiveRecordBaseModel.set_session(session)
>
> # from your model
> User.set_session(session)
>
> # create a instance
> query = select(User)
> async_query = AsyncQuery(query)
> ```
>
> Calling `set_session` from the `AsyncQuery` instance:
>
> ```python
> # create a instance
> query = select(User)
> async_query = AsyncQuery(query)
>
> # set the session from the base model
> async_query.set_session(BaseModel._session)
>
> # set the session from the model
> async_query.set_session(User._session)
> ```

### Performing Queries

Example of usage:

```python
query = select(User)
async_query = AsyncQuery(query)
async_query = async_query.where(name__like='%John%').sort('-created_at')
async_query = async_query.limit(2)
users = await async_query.all()
```

To get the `sqlalchemy.sql.Select` instance to use native SQLAlchemy methods
use the `query` property:

```python
query = select(User)
async_query = AsyncQuery(query)
async_query.query  # <sqlalchemy.sql.Select at 0x...>
```

???+ warning

    If a `NoSessionError` is raised, it means that there is no session
    associated with the `AsyncQuery` instance. This can happen
    if the `set_session` method of the base model has not been called
    or if the model has not been initialized with a session.

    In this case, you must provide a session by calling the `set_session`
    either from the model or the `AsyncQuery` instance as described above.

## API Reference

### Attributes

#### query

```python
query: Select[tuple[Any, ...]]
```

> The wrapped `sqlalchemy.sql.Select` instance.

> **Examples**
```python
query = select(User)
async_query = AsyncQuery(query)
async_query.query
# <sqlalchemy.sql.Select at 0x...>

async_query.query = async_query.query.limit(10).order_by(User.age.desc())
users = await async_query.all()
```

### Instance Methods

#### execute

```python
async def execute() -> Result[Any]
```

> Executes the query and returns a `sqlalchemy.engine.Result`
> instance containing the results.

> **Returns**

> - `sqlalchemy.engine.Result[Any]`: Result of the query.

#### scalars

```python
async def scalars() -> ScalarResult[T]
```

> Returns a `sqlalchemy.engine.ScalarResult` instance containing all rows.

> **Returns**

> - `sqlalchemy.engine.ScalarResult[T]`: Result instance containing
> all scalars.

> **Examples**

> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> result = await async_query.scalars()
> >>> result
> <sqlalchemy.engine.result.ScalarResult object at 0x...>
> >>> users = result.all()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> result = await async_query.where(name='John Doe').scalars()
> >>> users = result.all()
> >>> users
> [User(id=2)]
> ```

#### first

```python
async def first(scalar: bool = True) -> T | Row[tuple[Any, ...]] | None
```

> Fetches the first row or `None` if no results are found.

> If `scalar` is `True`, returns a scalar value (default).

> **Parameters**

> - `scalar`: If `True`, returns a scalar value (`T`),
> otherwise returns a row (default: `True`).

> **Returns**

> - `T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.
> - `None`: If no result is found.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> user = await async_query.first()
> >>> user
> User(id=1)
> >>> user = await async_query.first(scalar=False)
> >>> user
> (User(id=1),)
> ```

> Selecting specific columns:
> ```pycon
> >>> user = await async_query.select(User.name, User.age).first()
> >>> user
> Bob Williams
> >>> user = await async_query.select(User.name, User.age)
> ...                         .first(scalar=False)
> >>> user
> ('Bob Williams', 30)
> ```

#### one

```python
async def one(scalar: bool = True) -> T | Row[tuple[Any, ...]]
```

> Fetches one row or raises a `sqlalchemy.exc.NoResultFound` exception
> if no results are found.

> If multiple results are found, it will raise a
> `sqlalchemy.exc.MultipleResultsFound` exception.

> If `scalar` is `True`, returns a scalar value (default).

> **Parameters**

> - `scalar`: If `True`, returns a scalar value (`T`),
> otherwise returns a row (default: `True`).

> **Returns**

> - `T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.

> **Raises**

> - `NoResultFound`: If no row is found.
> - `MultipleResultsFound`: If multiple rows match.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> user = await async_query.where(name='John Doe').one()
> >>> user
> User(id=1)
> >>> user = await async_query.where(name='John Doe')
> ...                         .one(scalar=False)
> >>> user
> (User(id=1),)
> >>> user = await async_query.where(name='Unknown').one()
> Traceback (most recent call last):
>     ...
> sqlalchemy.exc.NoResultFound: No row was found when one was required
> >>> user = await async_query.one()
> Traceback (most recent call last):
>     ...
> sqlalchemy.exc.MultipleResultsFound: Multiple rows were found when one was required
> ```

> Selecting specific columns:
> ```pycon
> >>> user = await async_query.where(name='John Doe')
> ...                  .select(User.name, User.age)
> ...                  .one()
> >>> user
> John Doe
> >>> user = await async_query.where(name='John Doe')
> ...                  .select(User.name, User.age)
> ...                  .one(scalar=False)
> >>> user
> ('John Doe', 30)
> ```

#### one_or_none

```python
async def one_or_none(scalar: bool = True) -> T | Row[tuple[Any, ...]] | None
```

> Fetches one row or `None` if no results are found.

> If multiple results are found, it will raise a
> `sqlalchemy.exc.MultipleResultsFound` exception.

> If `scalar` is `True`, returns a scalar value (default).

> **Parameters**

> - `scalar`: If `True`, returns a scalar value (`T`),
> otherwise returns a row (default: `True`).

> **Returns**

> - `T`: Instance for method chaining (scalar).
> - `sqlalchemy.engine.Row[tuple[Any, ...]]`: Row.
> - `None`: If no result is found.

> **Raises**

> - `MultipleResultsFound`: If multiple rows match.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> user = await async_query.where(name='John Doe')
> ...                         .one_or_none()
> >>> user
> User(id=1)
> >>> user = await async_query.where(name='John Doe')
> ...                         .one_or_none(scalar=False)
> >>> user
> (User(id=1),)
> >>> user = await async_query.where(name='Unknown')
> ...                         .one_or_none()
> >>> user
> None
> >>> user = await async_query.one_or_none()
> Traceback (most recent call last):
>     ...
> sqlalchemy.exc.MultipleResultsFound: Multiple rows were found when one was required
> ```

> Selecting specific columns:
> ```pycon
> >>> user = await async_query.where(name='John Doe')
> ...                         .select(User.name, User.age)
> ...                         .one_or_none()
> >>> user
> John Doe
> >>> user = await async_query.where(name='John Doe')
> ...                         .select(User.name, User.age)
> ...                         .one_or_none(scalar=False)
> >>> user
> ('John Doe', 30)
> ```

#### all

```python
async def all(scalars: bool = True) -> Sequence[T] | Sequence[Row[tuple[Any, ...]]]
```

> Fetches all rows.

> If `scalars` is `True`, returns scalar values (default).

> **Parameters**

> - `scalars`: If `True`, returns scalar values (`Sequence[T]`),
> otherwise returns rows (default: `True`).

> **Returns**

> - `Sequence[T]`: Instances (scalars).
> - `Sequence[sqlalchemy.engine.Row[tuple[Any, ...]]]`: Rows.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> users = await async_query.all()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> users = await async_query.all(scalars=False)
> >>> users
> [(User(id=1),), (User(id=2),), ...]
> ```

> Selecting specific columns:
> ```pycon
> >>> users = await async_query.select(User.name, User.age).all()
> >>> users
> ['John Doe', 'Jane Doe', ...]
> >>> users = await async_query.select(User.name, User.age)
> ...                          .all(scalars=False)
> >>> users
> [('John Doe', 30), ('Jane Doe', 32), ...]
> ```

#### count

```python
async def count() -> int
```

> Fetches the number of rows.

> **Returns**

> - `int`: The number of rows.

> **Examples**

> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> count = await async_query.count()
> >>> count
> 34
> ```

#### unique

```python
async def unique(scalars: bool = True) -> ScalarResult[T] | Result[tuple[Any, ...]]
```

> Similar to [`scalars()`](#scalars) but applies unique filtering to
> the objects returned in the result instance.

> If `scalars` is `False`, returns a `sqlalchemy.engine.Result` instance
> instead of a `sqlalchemy.engine.ScalarResult` instance.

> ???+ note
>
>     This method is different from `distinct()` in that it applies unique
>     filtering to the objects returned in the result instance. If you need
>     to apply unique filtering on the query (a DISTINCT clause), use
>     `distinct()` instead.

> **Parameters**

> - `scalars`: If `True`, returns a `sqlalchemy.engine.ScalarResult`
> instance. Otherwise, returns a `sqlalchemy.engine.Result` instance
> (default: `True`).

> **Returns**

> - `sqlalchemy.engine.ScalarResult[T]`: Result instance containing
> all scalars.
> - `sqlalchemy.engine.Result[tuple[Any, ...]]`: Result instance containing
> all rows.

> **Examples**

> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> users = await async_query.unique()
> >>> users
> <sqlalchemy.engine.result.ScalarResult object at 0x...>
> >>> users = await async_query.unique(scalars=False)
> >>> users
> <sqlalchemy.engine.result.Result object at 0x...>
> ```

#### unique_first

```python
async def unique_first(scalar: bool = True) -> T | Row[tuple[Any, ...]] | None
```

> Similar to [`first()`](#first) but applies unique filtering to
> the objects returned by either `sqlalchemy.engine.ScalarResult`
> or `sqlalchemy.engine.Result` depending on the value of `scalar`.

> ???+ note
>
>     This method is different from `distinct()` in that it applies unique
>     filtering to the objects returned in the result instance. If you need
>     to apply unique filtering on the query (a DISTINCT clause), use
>     `distinct()` instead.

> See [`unique()`](#unique) and [`first()`](#first) for more details.

#### unique_one

```python
async def unique_one(scalar: bool) -> T | Row[tuple[Any, ...]]
```

> Similar to [`one()`](#one) but applies unique filtering to
> the objects returned by either `sqlalchemy.engine.ScalarResult`
> or `sqlalchemy.engine.Result` depending on the value of `scalar`.

> ???+ note
>
>     This method is different from `distinct()` in that it applies unique
>     filtering to the objects returned in the result instance. If you need
>     to apply unique filtering on the query (a DISTINCT clause), use
>     `distinct()` instead.

> See [`unique()`](#unique) and [`one()`](#one) for more details.

#### unique_one_or_none

```python
async def unique_one_or_none(scalar: bool) -> T | Row[tuple[Any, ...]] | None
```

> Similar to [`one_or_none()`](#one_or_none) but applies unique filtering to
> the objects returned by either `sqlalchemy.engine.ScalarResult`
> or `sqlalchemy.engine.Result` depending on the value of `scalar`.

> ???+ note
>
>     This method is different from `distinct()` in that it applies unique
>     filtering to the objects returned in the result instance. If you need
>     to apply unique filtering on the query (a DISTINCT clause), use
>     `distinct()` instead.

> See [`unique()`](#unique) and [`one_or_none()`](#one_or_none) for
> more details.

#### unique_all

```python
async def unique_all(scalars: bool) -> Sequence[T] | Sequence[Row[tuple[Any, ...]]]
```

> Similar to [`all()`](#all) but applies unique filtering to
> the objects returned by either `sqlalchemy.engine.ScalarResult`
> or `sqlalchemy.engine.Result` depending on the value of `scalars`.

> ???+ note
>
>     This method is different from `distinct()` in that it applies unique
>     filtering to the objects returned in the result instance. If you need
>     to apply unique filtering on the query (a DISTINCT clause), use
>     `distinct()` instead.

> See [`unique()`](#unique) and [`all()`](#all) for more details.

#### unique_count

```python
async def unique_count() -> int
```

> Similar to [`count()`](#count) but applies unique filtering to
> the objects returned by `sqlalchemy.engine.ScalarResult`.

> ???+ note
>
>     This method is different from `distinct()` in that it applies unique
>     filtering to the objects returned in the result instance. If you need
>     to apply unique filtering on the query (a DISTINCT clause), use
>     `distinct()` instead.

> See [`unique()`](#unique) and [`count()`](#count) for more details.

#### select

```python
def select(*entities: _ColumnsClauseArgument[Any]) -> Self
```

> Replaces the columns clause with the given entities.

> The existing set of FROMs are maintained, including those implied by
> the current columns clause.

> **Parameters**

> - `entities`: The entities to select.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Examples**

> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> async_query.order_by('-created_at')
> >>> async_query
> SELECT users.id, users.username, users.name, ... FROM users ORDER BY users.created_at DESC
> >>> async_query.select(User.name, User.age)
> >>> async_query
> SELECT users.name, users.age FROM users ORDER BY users.created_at DESC
> ```

#### distinct

```python
def distinct() -> Self
```

> Applies DISTINCT to the SELECT statement overall.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Examples**

> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> async_query.query
> SELECT users.id, users.username, users.name, ... FROM users
> >>> async_query.distinct()
> SELECT DISTINCT users.id, users.username, users.name, ... FROM users
> ```

#### options

```python
def options(*args: ExecutableOption) -> Self
```

> Applies the given list of mapper options.

> ???+ warning
>
>     Quoting from the [joined eager loading docs](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading){:target="_blank"}:
>
>         When including `joinedload()` in reference to a one-to-many or
>         many-to-many collection, the `Result.unique()` method must be
>         applied to the returned result, which will uniquify the incoming
>         rows by primary key that otherwise are multiplied out by the join.
>         The ORM will raise an error if this is not present.
>
>         This is not automatic in modern SQLAlchemy, as it changes the behavior
>         of the result set to return fewer ORM objects than the statement would
>         normally return in terms of number of rows. Therefore SQLAlchemy keeps
>         the use of `Result.unique()` explicit, so there is no ambiguity that
>         the returned objects are being uniquified on primary key.
>
>     This is, when fetching many rows and using joined eager loading,
>     the `unique()` method or related (i.e. `unique_all()`) must be
>     called to ensure that the rows are unique on primary key
>     (see the examples below).
>
>     To learn more about options, see the
>     [Query.options docs](https://docs.sqlalchemy.org/en/14/orm/query.html#sqlalchemy.orm.Query.options){:target="_blank"}.

> **Parameters**

> - `args`: The options to apply.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Examples**

> Joined eager loading:
> ```pycon
> >>> query = select(User)
> >>> aq = AsyncQuery(query)
> >>> users = await aq.options(joinedload(User.posts))
> ...                 .unique_all()  # required for joinedload()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> users[0].posts
> [Post(id=1), Post(id=2), ...]
> >>> user = await aq.options(joinedload(User.posts)).first()
> >>> user
> User(id=1)
> >>> users.posts
> [Post(id=1), Post(id=2), ...]
> ```

> Subquery eager loading:
> ```pycon
> >>> users = await aq.options(subqueryload(User.posts)).all()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> users[0].posts
> [Post(id=1), Post(id=2), ...]
> ```

> Eager loading without calling unique() before all():
> ```pycon
> >>> users = await aq.options(joinedload(User.posts)).all()
> Traceback (most recent call last):
>     ...
> InvalidRequestError: The unique() method must be invoked on this Result...
> ```

#### where

```python
def where(*criteria: ColumnElement[bool], **filters: Any) -> Self
```

> Applies one or more WHERE criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters**

> - `criteria`: SQLAlchemy style filter expressions.
> - `filters`: Django-style filters.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Examples**

> Using Django-like syntax:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> users = await async_query.where(age__gte=18).all()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> users = await async_query.where(
> ...     name__like='%John%',
> ...     age=30
> ... ).all()
> >>> users
> [User(id=2)]
> ```

> Using SQLAlchemy syntax:
> ```pycon
> >>> users = await async_query.where(User.age >= 18).all()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> users = await async_query.where(
> ...     User.name == 'John Doe',
> ...     User.age == 30
> ... ).all()
> >>> users
> [User(id=2)]
> ```

> Using both syntaxes:
> ```pycon
> >>> users = await async_query.where(
> ...     User.age == 30,
> ...     name__like='%John%'
> ... ).all()
> >>> users
> [User(id=2)]
> ```

#### filter

```python
def filter(*criterion: ColumnElement[bool], **filters: Any) -> Self
```

> Synonym for [`where()`](#where).

#### find

```python
def find(*criterion: ColumnElement[bool], **filters: Any) -> Self
```

> Synonym for [`where()`](#where).

#### search

```python
def search(
    search_term: str,
    columns: Sequence[str | InstrumentedAttribute[Any]] | None = None,
) -> Self
```

> Applies a search filter to the query.

> Searches for `search_term` in the
> [searchable columns](inspection-mixin.md#searchable_attributes) of the model.
> If `columns` are provided, searches only these columns.

> **Parameters**

> - `search_term`: Search term.
> - `columns`: Columns to search in.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> users = await async_query.search(search_term='John').all()
> >>> users
> [User(id=2), User(id=6)]
> >>> users[0].name
> John Doe
> >>> users[0].username
> John321
> >>> users[1].name
> Diana Johnson
> >>> users[1].username
> Diana84
> ```

> Searching specific columns:
> ```pycon
> >>> users = await async_query.search(
> ...     search_term='John',
> ...     columns=[User.name, User.username]
> ... ).all()
> >>> users
> [User(id=2), User(id=6)]
> >>> users = await async_query.search(
> ...     search_term='John',
> ...     columns=[User.username]  # or 'username'
> ... ).all()
> >>> users
> [User(id=2)]
> ```

#### order_by

```python
def order_by(*columns: ColumnExpressionOrStrLabelArgument) -> Self
```

> Applies one or more ORDER BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> **Parameters**

> - `columns`: Django-like or SQLAlchemy sort expressions.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Examples**

> Using Django-like syntax:
> ```pycon
> >>> query = select(Post)
> >>> async_query = AsyncQuery(query)
> >>> posts = await async_query.order_by('-rating', 'user___name').all()
> >>> posts
> [Post(id=1), Post(id=4), ...]
> ```

> Using SQLAlchemy syntax:
> ```pycon
> >>> posts = await async_query.order_by(Post.rating.desc()).all()
> >>> posts
> [Post(id=1), Post(id=4), ...]
> ```

Using both syntaxes:
> ```pycon
> >>> posts = await async_query.order_by(
> ...     Post.rating.desc(),
> ...     'user___name'
> ... ).all()
> >>> posts
> [Post(id=1), Post(id=4), ...]
> ```

#### sort

```python
def sort(*columns: ColumnExpressionOrStrLabelArgument) -> Self
```

> Synonym for [`order_by()`](#order_by).

#### group_by

```python
def group_by(
    *columns: ColumnExpressionOrStrLabelArgument,
    select_columns: Sequence[_ColumnsClauseArgument[Any]] | None = None,
) -> Self
```

> Applies one or more GROUP BY criteria to the query.

> It supports both Django-like syntax and SQLAlchemy syntax.

> It is recommended to select specific columns. You can use
> the `select_columns` parameter to select specific columns.

> **Parameters**

> - `columns`: Django-like or SQLAlchemy columns.
> - `select_columns`: Columns to be selected (recommended).

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Examples**

> Usage:
> ```pycon
> >>> from sqlalchemy.sql.functions import func
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> columns = (User.age, func.count(User.name))
> >>> async_query.group_by(
> ...     User.age, select_columns=columns
> ... )
> >>> rows = await async_query.all(scalars=False)
> [(30, 2), (32, 1), ...]
> ```

> You can also call `select()` before calling `group_by()`:
> ```pycon
> >>> from sqlalchemy.sql import text, func
> >>> query = select(Post)
> >>> async_query = AsyncQuery(query)
> >>> async_query.select(
> ...     Post.rating,
> ...     text('users_1.name'),
> ...     func.count(Post.title)
> ... )
> >>> async_query.group_by('rating', 'user___name')
> >>> rows = async_query.all(scalars=False)
> >>> rows
> [(4, 'John Doe', 1), (5, 'Jane Doe', 1), ...]
> ```

#### offset

```python
def offset(offset: int) -> Self
```

> Applies an OFFSET clause to the query.

> **Parameters**

> - `offset`: Number of rows to skip.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Raises**

> - `ValueError`: If `offset` is negative.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> users = await async_query.all()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> users = await async_query.offset(10).all()
> >>> users
> [User(id=11), User(id=12), ...]
> >>> async_query.offset(-1)
> Traceback (most recent call last):
>     ...
> ValueError: offset must be >= 0
> ```

#### skip

```python
def skip(skip: int) -> Self
```

> Synonym for [`offset()`](#offset).

#### limit

```python
def limit(limit: int) -> Self
```

> Applies a LIMIT clause to the query.

> **Parameters**

> - `limit`: Maximum number of rows to return.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Raises**

> - `ValueError`: If `limit` is negative.

> **Examples**

> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> users = await async_query.all()
> >>> users
> [User(id=1), User(id=2), ...]
> >>> users = await async_query.limit(2).all()
> >>> users
> [User(id=1), User(id=2)]
> >>> async_query.limit(-1)
> Traceback (most recent call last):
>     ...
> ValueError: limit must be >= 0
> ```

#### take

```python
def take(take: int) -> Self
```

> Synonym for [`limit()`](#limit).

#### top

```python
def top(top: int) -> Self
```

> Synonym for [`limit()`](#limit).

#### join

```python
def join(
    *paths: EagerLoadPath, model: type[T] | None = None
) -> Self
```

> Joined eager loading using LEFT OUTER JOIN.

> When a tuple is passed, the second element must be boolean, and
> if `True`, the join is `INNER JOIN`, otherwise `LEFT OUTER JOIN`.

> ???+ note
>
>     Only direct relationships can be loaded.

> **Parameters**

> - `paths`: Relationship attributes to join.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Raises**

> - `ValueError`: If the second element of tuple is not boolean.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(Comment)
> >>> async_query = AsyncQuery(query)
> >>> comment = await async_query.join(
> ...     Comment.user,         # LEFT OUTER JOIN
> ...     (Comment.post, True)  # True = INNER JOIN
> ... ).first()
> >>> comment
> Comment(id=1)
> >>> comment.user
> User(id=1)
> >>> comment.post
> Post(id=1)
> >>> async_query.join(
> ...     Comment.user,
> ...     (Comment.post, 'inner')  # invalid argument
> ... )
> Traceback (most recent call last):
>     ...
> ValueError: expected boolean for second element of tuple, got str: 'inner'
> ```

#### with_subquery

```python
def with_subquery(
    *paths: EagerLoadPath, model: type[T] | None = None
) -> Self
```

> Subqueryload or Selectinload eager loading.

> Emits a second SELECT statement (Subqueryload) for each relationship
> to be loaded, across all result objects at once.

> When a tuple is passed, the second element must be boolean.
> If it is `True`, the eager loading strategy is SELECT IN (Selectinload),
> otherwise SELECT JOIN (Subqueryload).

> ???+ warning
>
>     A query which makes use of `subqueryload()` in conjunction with a limiting
>     modifier such as `Query.limit()` or `Query.offset()` should always include
>     `Query.order_by()` against unique column(s) such as the primary key,
>     so that the additional queries emitted by `subqueryload()` include the
>     same ordering as used by the parent query. Without it, there is a chance
>     that the inner query could return the wrong rows, as specified in
>     [The importance of ordering](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering){:target="_blank"}.
>
>     Incorrect, LIMIT without ORDER BY:
>     ```python
>     User.options(subqueryload(User.posts)).first()
>     ```
>
>     Incorrect if User.name is not unique:
>     ```python
>     User.options(subqueryload(User.posts)).order_by(User.name).first()
>     ```
>
>     Correct:
>     ```python
>     User.options(subqueryload(User.posts)).order_by(User.name, User.id).first()
>     ```
>
>     To get more information about SELECT IN and SELECT JOIN strategies,
>     , see the [`loading relationships docs`](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html){:target="_blank"}.

> ???+ note
>
>     Only direct relationships can be loaded.

> **Parameters**

> - `paths`: Relationship attributes to load.

> **Returns**

> - `Self`: The instance itself for method chaining.

> **Raises**

> - `ValueError`: If the second element of tuple is not boolean.

> **Examples**

> Usage:
> ```pycon
> >>> query = select(User)
> >>> async_query = AsyncQuery(query)
> >>> users = await async_query.with_subquery(
> ...     User.posts,            # SELECT JOIN
> ...     (User.comments, True)  # True = SELECT IN
> ... ).all()
> >>> users[0]
> User(id=1)
> >>> users[0].posts              # loaded using SELECT JOIN
> [Post(id=1), Post(id=2), ...]
> >>> users[0].posts[0].comments  # loaded using SELECT IN
> [Comment(id=1), Comment(id=2), ...]
> >>> async_query.with_subquery(
> ...     User.posts,
> ...     (User.comments, 'selectin')  # invalid argument
> ... )
> Traceback (most recent call last):
>     ...
> ValueError: expected boolean for second element of tuple, got str: 'selectin'
> ```

> Using a limiting modifier:
> ```pycon
> >>> user = await async_query.with_subquery(
> ...     User.posts,            # SELECT JOIN
> ...     (User.comments, True)  # True = SELECT IN
> ... ).sort('id')  # sorting modifier (Important!!!)
> ...  .first()     # limiting modifier
> >>> user = await async_query.with_subquery(
> ...     User.posts,            # SELECT JOIN
> ...     (User.comments, True)  # True = SELECT IN
> ... ).limit(1)    # limiting modifier
> ...  .sort('id')  # sorting modifier (Important!!!)
> ...  .all()[0]
> >>> user
> User(id=1)
> >>> user.posts              # loaded using SELECT JOIN
> [Post(id=1), Post(id=2), ...]
> >>> user.posts[0].comments  # loaded using SELECT IN
> [Comment(id=1), Comment(id=2), ...]
> ```

#### with_schema

```python
def with_schema(schema: EagerSchema) -> Self
```

> Joined, subqueryload and selectinload eager loading.

> Useful for complex cases where you need to load nested relationships in
> separate queries.

> ???+ warning
>
>     A query which makes use of `subqueryload()` in conjunction with a limiting
>     modifier such as `Query.limit()` or `Query.offset()` should always include
>     `Query.order_by()` against unique column(s) such as the primary key,
>     so that the additional queries emitted by `subqueryload()` include the
>     same ordering as used by the parent query. Without it, there is a chance
>     that the inner query could return the wrong rows, as specified in
>     [The importance of ordering](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#the-importance-of-ordering){:target="_blank"}.
>
>     Incorrect, LIMIT without ORDER BY:
>     ```python
>     User.options(subqueryload(User.posts)).first()
>     ```
>
>     Incorrect if User.name is not unique:
>     ```python
>     User.options(subqueryload(User.posts)).order_by(User.name).first()
>     ```
>
>     Correct:
>     ```python
>     User.options(subqueryload(User.posts)).order_by(User.name, User.id).first()
>     ```
>
>     To get more information about SELECT IN and SELECT JOIN strategies,
>     , see the [`loading relationships docs`](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html){:target="_blank"}.

> **Parameters**

> - `schema`: Dictionary defining the loading strategy.

> **Returns**

> - `Self`: The instance itself for method chaining.

> ```pycon
> >>> from sqlactive import JOINED, SUBQUERY
> >>> schema = {
> ...     User.posts: JOINED,          # joinedload user
> ...     User.comments: (SUBQUERY, {  # load comments in separate query
> ...         Comment.user: JOINED     # but, in this separate query, join user
> ...     })
> ... }
> >>> query = select(User)
> >>> aq = AsyncQuery(query)
> >>> user = await aq.with_schema(schema)
> ...                .order_by(User.id)  # important when limiting
> ...                .first()            # limiting modifier
> >>> user
> User(id=1)
> >>> user.posts
> [Post(id=1), Post(id=2), ...]
> >>> user.posts[0].comments
> [Comment(id=1), Comment(id=2), ...]
> >>> user.posts[0].comments[0].user
> User(id=1)
> ```
