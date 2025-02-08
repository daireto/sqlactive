# Getting started

## Installing sqlactive

You can simply install sqlactive from the [PyPI](https://pypi.org/project/sqlactive/):

```bash
pip install sqlactive
```

## Tutorial

### 1. Define the Models

The `ActiveRecordBaseModel` class provides a base class for your models.

It inherits from:

* [`ActiveRecordMixin`](api/active-record-mixin.md): Provides a set of ActiveRecord-like
    helper methods for interacting with the database.
* [`TimestampMixin`](api/timestamp-mixin.md): Adds the `created_at` and `updated_at` timestamp columns.
* [`SerializationMixin`](api/serialization-mixin.md): Provides serialization and deserialization methods.

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

!!! warning

    When defining a `BaseModel` class, don't forget to set `__abstract__` to `True`
    in the base class to avoid creating tables for the base class.

!!! note

    The models can directly inherit from the `ActiveRecordBaseModel` class:

    ```python
    from sqlactive import ActiveRecordBaseModel
    class User(ActiveRecordBaseModel):
        __tablename__ = 'users'
        # ...
    ```

    However, it is recommended to create a base class for your models and
    inherit from it.

!!! tip

    Your `BaseModel` class can also inherit directly from the mixins.
    For example, if you don't want to implement automatic timestamps don't inherit
    from `ActiveRecordBaseModel` class. Instead, inherit from `ActiveRecordMixin`
    and/or `SerializationMixin`:

    ```python
    from sqlactive import ActiveRecordMixin, SerializationMixin
    class BaseModel(ActiveRecordMixin, SerializationMixin):
        __abstract__ = True
    ```

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

The use of the `expire_on_commit` flag is explained in the warning of [this section](#4-perform-bulk-operations).

!!! tip

    Use the `DBConnection` class as a shortcut to initialize the database.
    The `DBConnection` class is a wrapper around the `async_engine`, `async_sessionmaker`
    and `async_scoped_session` objects:

    ```python
    from sqlactive import DBConnection

    DATABASE_URL = 'sqlite+aiosqlite://'
    conn = DBConnection(DATABASE_URL, echo=False)
    await conn.init_db(BaseModel)
    ```

    See the [DB Connection Helper](api/db-connection-helper.md) section for more information.

### 3. Perform CRUD Operations

```python
user = await User.create(username='John1234', name='John Doe', age=25)
print(user)
# <User #1>

user.name = 'Johnny Doe'
user.age = 30
await user.save()
print(user.name)
# Johnny Doe

user = await User.get(1)
print(user)
# <User #1>

await user.update(name='John Doe', age=20)
print(user.age)
# 20

await user.delete()
```

!!! danger

    The `delete` and `remove` methods are not soft deletes.
    Both of them permanently delete the row from the database.
    So, if you want to keep the row in the database, implement
    a custom delete method and use `save` method instead (i.e. a `is_deleted` column).

!!! tip

    Check the [`ActiveRecordMixin` API Reference](api/active-record-mixin.md)
    class to see all the available methods.

### 4. Perform Bulk Operations

```python
users = [
    User(username='John1234', name='John Doe', age=20),
    User(username='Jane1234', name='Jane Doe', age=21),
    User(username='Bob1234', name='Bob Doe', age=22),
]

await User.create_all(users, refresh=True)
users = await User.find(username__endswith='Doe').all()
print(users)
# [<User #1>, <User #2>]

await User.delete_all(users)

users = await User.find(username__endswith='Doe').all()
print(users)
# []
```

!!! warning

    When calling bulk operation methods, i.e. `save_all`, `create_all`, `update_all`
    and `delete_all`, the `refresh` flag must be set to `True` in order to access
    the updated attributes of the affected rows.
    <br>**NOTE**: This may lead to a higher latency due to additional database queries.

    ```python
    users = [
        User(username='John1234', name='John Doe', age=20),
        User(username='Jane1234', name='Jane Doe', age=21),
        # ...,
    ]
    await User.save_all(users, refresh=True)
    print(users[0].updated_at)
    # 2024-12-28 23:00:51
    ```

    If `refresh` is not set to `True`, a `sqlalchemy.orm.exc.DetachedInstanceError`
    may be raised when trying to access the updated attributes because the instances
    are detached (unavailable after commit).

    ```python
    users = [
        User(username='John1234', name='John Doe', age=20),
        User(username='Jane1234', name='Jane Doe', age=21),
        # ...,
    ]
    await User.save_all(users)
    print(users[0].updated_at)
    # Traceback (most recent call last):
    #     ...
    # sqlalchemy.orm.exc.DetachedInstanceError: Instance <User ...> is not bound
    # to a Session; attribute refresh operation cannot proceed
    # (Background on this error at: https://sqlalche.me/e/20/bhk3)
    ```

    Another option is to set the `expire_on_commit` flag to `False` in the
    `async_sessionmaker` when initializing the database. However, **this does not update the instances after commit**.
    It just keeps the instances available after commit.

    ```python
    async_sessionmaker = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
    )
    ```

!!! tip

    Check the [`ActiveRecordMixin` API Reference](api/active-record-mixin.md)
    class to see all the available methods.

### 5. Perform Queries

Perform simple and complex queries, eager loading, and dictionary serialization:

```python
from sqlactive import JOINED, SUBQUERY

user = await User.filter(name='John Doe').first()
print(user)
# <User #1>

posts = await Post.filter(rating__in=[2, 3, 4], user___name__like='%Bi%').all()
print(posts)
# [<Post #1>, <Post #2>, <Post #3>]

posts = await Post.sort('-rating', 'user___name').all()
print(posts)
# [<Post #3>, <Post #1>, <Post #2>, <Post #4>, ...]

comments = await Comment.join(Comment.user, Comment.post).unique_all()
print(comments)
# [<Comment 1>, <Comment 2>, <Comment 3>, <Comment 4>, <Comment 5>, ...]

user = await User.with_subquery(User.posts).first()
print(user)
# <User #1>
print(user.posts)
# [<Post #1>, <Post #2>, <Post #3>]

schema = {
    User.posts: JOINED,
    User.comments: (SUBQUERY, {
        Comment.post: SELECT_IN
    }),
}
user = await User.with_schema(schema).unique_first()
print(user.comments[0].post.title)
# Lorem ipsum
```

For more flexibility, the low-level `filter_expr` method can be used:

```python
Post.filter(*Post.filter_expr(rating__gt=2, body='text'))
# or
session.query(Post).filter(*Post.filter_expr(rating__gt=2, body='text'))
```

It's like [filter_by in SQLALchemy](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.filter),
but also allows magic operators like `rating__gt`.

See the [low-level SmartQueryMixin methods](api/smart-query-mixin.md#api-reference) for more details.

!!! note

    `filter_expr` method is very low-level and does NOT do magic Django-like joins. Use `smart_query` for that:

    ```python
    query = User.smart_query(
        criterion=(or_(User.age == 30, User.age == 32),),
        filters={'username__like': '%8'},
        sort_columns=(User.username,),
        sort_attrs=('age',),
        schema={
            User.posts: JOINED,
            User.comments: (SUBQUERY, {
                Comment.post: SELECT_IN
            }),
        },
    )
    users = await query.unique_all()
    print(users)
    # [<User #1>, <User #3>]
    ```

!!! tip

    Check the [`ActiveRecordMixin` API Reference](api/active-record-mixin.md)
    class to see all the available methods.

### 6. Perform Native Queries

Perform native SQLAlchemy queries using the `execute` method:

```python
    from sqlalchemy import select, func
    from sqlactive import execute

    query = select(User.age, func.count(User.id)).group_by(User.age)
    result = await execute(query)
    # [(20, 1), (22, 4), (25, 12)]
```

If your base model is not `ActiveRecordBaseModel` you must pass your base
model class to the `base_model` argument of the `execute` method:

```python
    from sqlalchemy import select, func
    from sqlactive import ActiveRecordBaseModel, execute

    # Note that it does not matter if your base model
    # inherits from `ActiveRecordBaseModel`, you still
    # need to pass it to this method
    class BaseModel(ActiveRecordBaseModel):
        __abstract__ = True

    class User(BaseModel):
        __tablename__ = 'users'
        # ...

    query = select(User.age, func.count(User.id)).group_by(User.age)
    result = await execute(query, BaseModel)
    # [(20, 1), (22, 4), (25, 12)]
```

### 7. Manage Timestamps

Timestamps (`created_at` and `updated_at`) are automatically managed:

```python
user = await User.create(username='John1234', name='John Doe', age=25)
print(user.created_at)
# 2024-12-28 23:00:51
print(user.updated_at)
# 2024-12-28 23:00:51

await asyncio.sleep(1)

await user.update(name='Johnny Doe')
print(user.updated_at)
# 2024-12-28 23:00:52
```

!!! tip

    Check the [`TimestampMixin`](api/timestamp-mixin.md) class to know how to customize the timestamps behavior.

### 8. Serialization and Deserialization

Models can be serialized and deserialized using the `to_dict` and `from_dict` methods:

```python
user = await User.create(username='John1234', name='John Doe', age=25)
user_dict = user.to_dict()
print(user_dict)
# {'id': 1, 'username': 'John1234', 'name': 'John Doe', ...}

user = User.from_dict(user_dict)
print(user.name)
# John Doe
```

Also, models can be serialized and deserialized using the `to_json` and `from_json` methods:

```python
user = await User.create(username='John1234', name='John Doe', age=25)
user_json = user.to_json()
print(user_json)
# {"id": 1, "username": "John1234", "name": "John Doe", ...}

user = User.from_json(user_json)
print(user.name)
# John Doe
```
