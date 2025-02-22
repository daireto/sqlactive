<p align="center">
    <img src="docs/images/logo.png" alt="SQLActive" />
</p>

<p align="center">
    <a href="https://pypi.org/project/sqlactive" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/sqlactive" alt="Supported Python versions">
    </a>
    <a href="https://pypi.org/project/sqlactive" target="_blank">
        <img src="https://img.shields.io/pypi/v/sqlactive" alt="Package version">
    </a>
    <a href="https://pypi.org/project/SQLAlchemy" target="_blank">
        <img src="https://img.shields.io/badge/SQLAlchemy-2.0%2B-orange" alt="Supported SQLAlchemy versions">
    </a>
    <a href="https://github.com/daireto/sqlactive/actions" target="_blank">
        <img src="https://github.com/daireto/sqlactive/actions/workflows/publish.yml/badge.svg" alt="Publish">
    </a>
    <a href='https://coveralls.io/github/daireto/sqlactive?branch=main'>
        <img src='https://coveralls.io/repos/github/daireto/sqlactive/badge.svg?branch=main' alt='Coverage Status' />
    </a>
    <a href="/LICENSE" target="_blank">
        <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
    </a>
</p>

<!-- omit in toc -->
# SQLActive

SQLActive is a lightweight and asynchronous ActiveRecord-style wrapper for
SQLAlchemy. Bring Django-like queries, automatic timestamps, nested eager
loading, and serialization/deserialization for SQLAlchemy models.

Heavily inspired by
[sqlalchemy-mixins](https://github.com/absent1706/sqlalchemy-mixins/).

Visit the [documentation website](https://daireto.github.io/sqlactive/).

<!-- omit in toc -->
## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [1. Define the Models](#1-define-the-models)
  - [2. Initialize the Database](#2-initialize-the-database)
  - [3. Perform CRUD Operations](#3-perform-crud-operations)
  - [4. Perform Bulk Operations](#4-perform-bulk-operations)
  - [5. Perform Queries](#5-perform-queries)
  - [6. Manage Timestamps](#6-manage-timestamps)
  - [7. Serialization and Deserialization](#7-serialization-and-deserialization)
- [Testing and Linting](#testing-and-linting)
  - [Unit Tests](#unit-tests)
  - [Coverage](#coverage)
  - [Linting](#linting)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Features

- **Asynchronous Support**: Async operations for better scalability.
- **ActiveRecord-like methods**: Perform CRUD operations with a syntax similar
  to [Peewee](https://docs.peewee-orm.com/en/latest/).
- **Django-like queries**: Perform intuitive and
  [expressive queries](https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships).
- **Nested eager loading**: Load nested relationships efficiently.
- **Automatic timestamps**: Auto-manage `created_at` and `updated_at` fields.
- **Serialization/deserialization**: Serialize and deserialize models to/from
  dict or JSON easily.

## Requirements

- Python 3.10+
- sqlalchemy 2.0+

## Installation

You can simply install sqlactive from
[PyPI](https://pypi.org/project/sqlactive/):

```bash
pip install sqlactive
```

## Usage

### 1. Define the Models

The `ActiveRecordBaseModel` class provides a base class for your models.

It inherits from:

* [`ActiveRecordMixin`](https://daireto.github.io/sqlactive/api/active-record-mixin/):
  Provides a set of ActiveRecord-like helper methods for interacting with
  the database.
* [`TimestampMixin`](https://daireto.github.io/sqlactive/api/timestamp-mixin/):
  Adds the `created_at` and `updated_at` timestamp columns.
* [`SerializationMixin`](https://daireto.github.io/sqlactive/api/serialization-mixin/):
  Provides serialization and deserialization methods.

It is recommended to define a `BaseModel` class that inherits from
`ActiveRecordBaseModel` and use it as the base class for all models
as shown in the following example:

```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlactive import ActiveRecordBaseModel


# Define a base class for your models (recommended)
class BaseModel(ActiveRecordBaseModel):
    __abstract__ = True


# Define the models
class User(BaseModel):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(18), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)

    posts: Mapped[list['Post']] = relationship(back_populates='user')
    comments: Mapped[list['Comment']] = relationship(back_populates='user')


class Post(BaseModel):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    user: Mapped['User'] = relationship(back_populates='posts')
    comments: Mapped[list['Comment']] = relationship(back_populates='post')


class Comment(BaseModel):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    body: Mapped[str] = mapped_column(nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey('posts.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    post: Mapped['Post'] = relationship(back_populates='comments')
    user: Mapped['User'] = relationship(back_populates='comments')
```

> [!WARNING]
> When defining a `BaseModel` class, don't forget to set `__abstract__` to
> `True` in the base class to avoid creating tables for the base class.

> [!TIP]
> The models can directly inherit from the `ActiveRecordBaseModel` class:
> ```python
> from sqlactive import ActiveRecordBaseModel
>
> class User(ActiveRecordBaseModel):
>     __tablename__ = 'users'
>     # ...
> ```
> However, it is recommended to define a base model class for your models and
> inherit from it.
>
> Your base model class can also inherit directly from the mixins.
> For example, if you don't want to implement automatic timestamps don't inherit
> from `ActiveRecordBaseModel` class. Instead, inherit from `ActiveRecordMixin`
> and/or `SerializationMixin`:
> ```python
> from sqlactive import ActiveRecordMixin, SerializationMixin
>
> class BaseModel(ActiveRecordMixin, SerializationMixin):
>     __abstract__ = True
> ```

### 2. Initialize the Database

```python
from asyncio import current_task
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)
from sqlactive import ActiveRecordBaseModel

# Connect to the database
DATABASE_URL = 'sqlite+aiosqlite://'
async_engine = create_async_engine(DATABASE_URL, echo=False)
async_sessionmaker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)
async_scoped_session = async_scoped_session(
    async_sessionmaker,
    scopefunc=current_task,
)

# Set the session
BaseModel.set_session(async_scoped_session)

# Initialize the tables
async with async_engine.begin() as conn:
    await conn.run_sync(BaseModel.metadata.create_all)
```

The use of the `expire_on_commit` flag is explained in the warning of
[this section](#4-perform-bulk-operations).

> [!TIP]
> Use the `DBConnection` class as a shortcut to initialize the database.
> The `DBConnection` class is a wrapper around the `async_engine`,
> `async_sessionmaker` and `async_scoped_session` objects:
> ```python
> from sqlactive import DBConnection
>
> DATABASE_URL = 'sqlite+aiosqlite://'
> conn = DBConnection(DATABASE_URL, echo=False)
> await conn.init_db(BaseModel)
> ```
> Check the documentation of
> [DB Connection Helper](https://daireto.github.io/sqlactive/api/db-connection-helper/)
> for more information.

### 3. Perform CRUD Operations

```python
user = await User.insert(username='John1234', name='John Doe', age=25)
user  # <User #1>

user.name = 'Johnny Doe'
user.age = 30
await user.save()
user.name  # Johnny Doe

user = await User.get(1)
user  # <User #1>

await user.update(name='John Doe', age=20)
user.age  # 20

await user.delete()
```

> [!CAUTION]
> The `delete()` and `remove()` methods are not soft deletes methods.
> Both of them will permanently delete the row from the database.
> So, if you want to keep the row in the database, you can implement
> a custom soft delete method, i.e. using `save()` method to update
> the row with a flag indicating if the row is deleted or not
> (i.e. a boolean `is_deleted` column).

> [!TIP]
> If you need to create a record for a short period of time, you can use the
> `with` statement:
> ```python
> with User(name='Bob', age=30) as user:
>     ...
> ```
> The `with` statement will create the record and delete it at the end of the
> block.
>
> Check the [Temporary Records documentation](https://daireto.github.io/sqlactive/api/active-record-mixin/#temporary-records)
> for more information.
>
> Also, check the [Active Record Mixin API Reference](https://daireto.github.io/sqlactive/api/active-record-mixin/#api-reference)
> to see all the available methods.

### 4. Perform Bulk Operations

```python
users = [
    User(username='John1234', name='John Doe', age=20),
    User(username='Jane1234', name='Jane Doe', age=21),
    User(username='Bob1234', name='Bob Doe', age=22),
]

await User.insert_all(users)
users = await User.find(username__endswith='Doe').all()
users  # [<User #1>, <User #2>]

await User.delete_all(users)

users = await User.find(username__endswith='Doe').all()
users  # []
```

> [!TIP]
> Check the [Active Record Mixin API Reference](https://daireto.github.io/sqlactive/api/active-record-mixin/#api-reference)
> to see all the available methods.

### 5. Perform Queries

Perform simple and complex queries with eager loading:

```python
from sqlactive import JOINED, SUBQUERY

user = await User.where(name='John Doe').first()
user  # <User #1>

posts = await Post.where(rating__in=[2, 3, 4], user___name__like='%Bi%').all()
posts  # [<Post #1>, <Post #2>, <Post #3>]

posts = await Post.sort('-rating', 'user___name').all()
posts  # [<Post #3>, <Post #1>, <Post #2>, <Post #4>, ...]

comments = await Comment.join(Comment.user, Comment.post).unique_all()
comments  # [<Comment 1>, <Comment 2>, <Comment 3>, <Comment 4>, <Comment 5>, ...]

user = await User.with_subquery(User.posts).first()
user  # <User #1>
user.posts  # [<Post #1>, <Post #2>, <Post #3>]

schema = {
    User.posts: JOINED,
    User.comments: (SUBQUERY, {
        Comment.post: SELECT_IN
    }),
}
user = await User.with_schema(schema).unique_first()
user.comments[0].post.title  # Lorem ipsum
```

> [!WARNING]
> All relations used in filtering/sorting/grouping should be explicitly set,
> not just being a `backref`.
> See the [About Relationships](https://daireto.github.io/sqlactive/api/active-record-mixin/#about-relationships) section for more information.

> [!TIP]
> Check the [Active Record Mixin API Reference](https://daireto.github.io/sqlactive/api/active-record-mixin/#api-reference)
> to see all the available methods.

For more flexibility, the low-level
[`filter_expr()`](https://daireto.github.io/sqlactive/api/smart-query-mixin/#filter_expr),
[`order_expr()`](https://daireto.github.io/sqlactive/api/smart-query-mixin/#order_expr),
[`column_expr()`](https://daireto.github.io/sqlactive/api/smart-query-mixin/#columns_expr)
and [`eager_expr()`](https://daireto.github.io/sqlactive/api/smart-query-mixin/#eager_expr)
methods can be used.

**Example of `filter_expr()` method usage**

> ```python
> Post.filter(*Post.filter_expr(rating__gt=2, body='text'))
> # or
> session.query(Post).filter(*Post.filter_expr(rating__gt=2, body='text'))
> ```

> It's like [filter in SQLALchemy](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.filter),
> but also allows magic operators like `rating__gt`.

> [!IMPORTANT]
> Low-level `filter_expr()`, `order_expr()`, `column_expr()` and
> `eager_expr()` methods are very low-level and does NOT do magic
> Django-like joins. Use `smart_query()` for that:
> ```python
> query = User.smart_query(
>     criterion=(or_(User.age == 30, User.age == 32),),
>     filters={'username__like': '%8'},
>     sort_columns=(User.username,),
>     sort_attrs=('-created_at',),
>     group_columns=(User.username,),
>     group_attrs=['age'],
>     schema={
>         User.posts: JOINED,
>         User.comments: (SUBQUERY, {
>             Comment.post: SELECT_IN
>         }),
>     },
> )
> ```

> [!TIP]
> Check the [Smart Query Mixin API Reference](https://daireto.github.io/sqlactive/api/smart-query-mixin/#api-reference)
> for more details about the `smart_query()` method and the low-level methods.

To perform native SQLAlchemy queries asynchronously,
you can use the `execute()` method:

```python
from sqlalchemy import select, func
from sqlactive import ActiveRecordBaseModel, execute

class BaseModel(ActiveRecordBaseModel):
    __abstract__ = True

class User(BaseModel):
    __tablename__ = 'users'
    # ...

query = select(User.age, func.count(User.id)).group_by(User.age)
result = await execute(query, BaseModel)
# [(20, 1), (22, 4), (25, 12)]
```

See the [Native SQLAlchemy queries](https://daireto.github.io/sqlactive/api/native-sqlalchemy-queries/)
documentation for more information.

### 6. Manage Timestamps

Timestamps (`created_at` and `updated_at`) are automatically managed:

```python
user = await User.insert(username='John1234', name='John Doe', age=25)
user.created_at  # 2024-12-28 23:00:51
user.updated_at  # 2024-12-28 23:00:51

await asyncio.sleep(1)

await user.update(name='Johnny Doe')
user.updated_at  # 2024-12-28 23:00:52
```

> [!TIP]
> Check the [`TimestampMixin`](https://daireto.github.io/sqlactive/api/timestamp-mixin/)
> class to know how to customize the timestamps behavior.

### 7. Serialization and Deserialization

Models can be serialized/deserialized to/from dictionaries using
the `to_dict()` and `from_dict()` methods:

```python
user = await User.insert(username='John1234', name='John Doe', age=25)
user_dict = user.to_dict()
user_dict  # {'id': 1, 'username': 'John1234', 'name': 'John Doe', ...}

user = User.from_dict(user_dict)
user.name  # John Doe
```

Also, models can be serialized/deserialized to/from JSON using
the `to_json()` and `from_json()` methods:

```python
user = await User.insert(username='John1234', name='John Doe', age=25)
user_json = user.to_json()
user_json  # {"id": 1, "username": "John1234", "name": "John Doe", ...}

user = User.from_json(user_json)
user.name  # John Doe
```

## Testing and Linting

### Unit Tests

To run the tests, simply run the following command from the root directory:

```bash
python -m unittest discover -s tests -t .
```

To run a specific test, use the following command:

```bash
python -m unittest tests.<test_name>
```

**Available tests**
- `test_active_record.py`
- `test_async_query.py`
- `test_db_connection.py`
- `test_execute.py`
- `test_inspection.py`
- `test_serialization.py`
- `test_smart_query.py`

### Coverage

First, install the `coverage` package:

```bash
pip install coverage
```

To check the coverage, run the following command:

```bash
python -m coverage run -m unittest discover -s tests -t .
```

To generate the coverage report, run the following command:

```bash
python -m coverage report -m
```

To generate the HTML report, run the following command:

```bash
python -m coverage html -d htmlcov
```

### Linting

First, install the `ruff` package:

```bash
pip install ruff
```

To check the code style, run the following command:

```bash
python -m ruff check .
```

## Documentation

Find the complete documentation [here](https://daireto.github.io/sqlactive/).

## Contributing

Please read the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the [MIT License](LICENSE).

## Support

If you find this project useful, give it a ⭐ on GitHub to show your support!

Also, give it a ⭐ to
[sqlalchemy-mixins](https://github.com/absent1706/sqlalchemy-mixins/)
which inspired this project!
