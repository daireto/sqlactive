# Session Mixin

the `SessionMixin` class provides functions for handling asynchronous
scoped sessions.

## API Reference

### Class Methods

#### set_session
```python
@classmethod
def set_session(session: async_scoped_session[AsyncSession])
```

> Sets the async session factory.

> **Parameters:**

> - `session`: Async session factory.

> **Example:**

> ```python
> from asyncio import current_task
> from sqlalchemy.ext.asyncio import (
>     ...,
>     async_scoped_session,
> )
>
> from sqlactive import ActiveRecordBaseModel
>
> class MyModel(ActiveRecordBaseModel):
>     __abstract__ = True
>
> ...  # other code
> async_scoped_session = async_scoped_session(
>   async_sessionmaker,
>   scopefunc=current_task
> )
>
> # Set the session
> ActiveRecordBaseModel.set_session(async_scoped_session(AsyncSession))
> ```

#### close_session
```python
@classmethod
def close_session()
```

> Closes the async session.

> **Example:**

> ```python
> ActiveRecordBaseModel.close_session()
> ```

### Class Properties

#### AsyncSession
```python
@classproperty
def AsyncSession() -> async_scoped_session[AsyncSession]
```

> Async session factory.

> **Raises:**

> - `NoSessionError`: If no session is available.

> **Example:**

> ```python
> async with SaActiveRecord.AsyncSession() as session:
>     session.add(model)
>     await session.commit()
> ```
