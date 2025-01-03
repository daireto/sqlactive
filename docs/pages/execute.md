# Native SQLAlchemy queries

You can execute native SQLAlchemy queries using the `sqlactive.conn.execute` function.

## Usage

```python
    from sqlalchemy import select, func
    from sqlactive import execute

    query = select(User.age, func.count(User.id)).group_by(User.age)
    result = await execute(query)
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
    result = await execute(query, BaseModel) # or execute(query, User)
```

!!! warning

    Your base model must have a session in order to use this method.
    Otherwise, it will raise an `NoSessionError` exception.
