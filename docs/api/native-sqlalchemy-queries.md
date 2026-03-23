# Native SQLAlchemy queries

You can asynchronously execute native SQLAlchemy queries using the
`sqlactive.conn.execute` function. It uses a `sqlalchemy.ext.asyncio.async_scoped_session`
instance to perform the actual query.

## Usage

```python
from sqlalchemy import select, func
from sqlactive import DBConnection, execute

conn = DBConnection(DATABASE_URL, echo=True)

query = select(User.age, func.count(User.id)).group_by(User.age)
result = await execute(conn.async_scoped_session, query)
```

The `statement`, `params` and `kwargs` arguments of this function are the
same as the arguments of the `execute` method of the
`sqlalchemy.ext.asyncio.AsyncSession` class.
