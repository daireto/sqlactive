# Documentation

This is the documentation for `sqlactive` library.

<!-- omit in toc -->
## Table of Contents
- [Documentation](#documentation)
  - [Base Model and Mixins](#base-model-and-mixins)
    - [`ActiveRecordBaseModel`](#activerecordbasemodel)
    - [Mixins](#mixins)
  - [Database Connection helper](#database-connection-helper)

## Base Model and Mixins

This library provides a base model and mixins for SQLAlchemy models.

### `ActiveRecordBaseModel`

The [`ActiveRecordBaseModel`](/sqlactive/base_model.py) class provides a base class for your models.
It inherits from [`ActiveRecordMixin`](/docs/ACTIVE_RECORD.md)
and [`TimestampMixin`](/docs/TIMESTAMP.md).

```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlactive import ActiveRecordBaseModel

# Define the BaseModel class
class BaseModel(ActiveRecordBaseModel):
    __abstract__ = True

# Define the models
class User(BaseModel):
    __tablename__ = 'users'

    # ...

class Post(BaseModel):
    __tablename__ = 'posts'

    # ...

class Comment(BaseModel):
    __tablename__ = 'comments'

    # ...
```

It also provides a custom `__repr__` for a better model representation and a `to_dict` method to serialize the model:

```python
user = await User.create(username='John1234', name='John Doe', age=25)
print(user)
# <User #1>
print(user.to_dict())
# {'id': 1, 'username': 'John1234', 'name': 'John Doe', ...}
```

> [!NOTE]
> The models can directly inherit from the `ActiveRecordBaseModel` class:
> ```python
> from sqlactive import ActiveRecordBaseModel
>
> class User(ActiveRecordBaseModel):
>     __tablename__ = 'users'
>     # ...
> ```
> However. it is recommended to declare a `BaseModel` class as a base class
> for your models.

> [!TIP]
> If you don't want to implement automatic timestamps, your base model can inherit
> from [`ActiveRecordMixin`](/docs/ACTIVE_RECORD.md) directly:
> ```python
> from sqlactive import ActiveRecordMixin
>
> class BaseModel(ActiveRecordMixin):
>     __abstract__ = True
> ```

### Mixins

- [`ActiveRecordMixin`](/docs/ACTIVE_RECORD.md): Provides ActiveRecord-like
    methods for your models.
    - [`API Reference`](/docs/ACTIVE_RECORD_API.md): The full list of available methods.
    - [`SmartQueryMixin`](/docs/SMART_QUERY.md): Adds smart query capabilities.
    - [`InspectionMixin`](/docs/INSPECTION.md): Adds model inspection capabilities.
- [`TimestampMixin`](/docs/TIMESTAMP.md): Manages timestamps for your models.

## Database Connection helper

This library provides a `DBConnection` helper class to connect to a database.

```python
from sqlactive import ActiveRecordBaseModel, DBConnection

class BaseModel(ActiveRecordBaseModel):
    __abstract__ = True

# Models defined here...

DATABASE_URL = 'sqlite+aiosqlite://'
db = DBConnection(DATABASE_URL, echo=False)
await db.init_db(BaseModel)
```

Using the `DBConnection` and the `init_db` method is the same as following:

```python
from asyncio import current_task
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)

DATABASE_URL = 'sqlite+aiosqlite://'

async_engine = create_async_engine(DATABASE_URL, echo=False)
async_sessionmaker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False, # Explained in the warning below
)
async_scoped_session = async_scoped_session(
    async_sessionmaker,
    scopefunc=current_task,
)

# Set the session
BaseModel.set_session(async_scoped_session)
```

The use of the `expire_on_commit` flag is explained in the warning of
[this section](/README.md#4-perform-bulk-operations).
