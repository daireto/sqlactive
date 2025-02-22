# Native SQLAlchemy queries

You can asynchronously execute native SQLAlchemy queries using the
`sqlactive.conn.execute` function. It uses the
[`AsyncSession`](session-mixin.md) of the `ActiveRecordBaseModel` class and
return a buffered `sqlalchemy.engine.Result` object.

## Usage

```python
from sqlalchemy import select, func
from sqlactive import execute

query = select(User.age, func.count(User.id)).group_by(User.age)
result = await execute(query)
```

The `statement`, `params` and `kwargs` arguments of this function are the
same as the arguments of the `execute` method of the
`sqlalchemy.ext.asyncio.AsyncSession` class.

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
result = await execute(query, BaseModel)  # or execute(query, User)
```

???+ warning

    Your base model must have a session in order to use this method.
    Otherwise, it will raise an `NoSessionError` exception.
    If you are not using the `DBConnection` class to initialize
    your base model, you can call its `set_session` method
    to set the session.
