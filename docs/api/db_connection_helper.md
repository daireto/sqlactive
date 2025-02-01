# DB Connection Helper

The `DBConnection` class provides functions for connecting to
a database and initializing tables.

## Usage

```python
from sqlactive import DBConnection

DATABASE_URL = 'sqlite+aiosqlite://'

db = DBConnection(DATABASE_URL, echo=False)
```

This is a shortcut:

```python
DATABASE_URL = 'sqlite+aiosqlite://'
async_engine = create_async_engine(DATABASE_URL, echo=False)
async_sessionmaker = async_sessionmaker(bind=async_engine, expire_on_commit=False)
async_scoped_session = async_scoped_session(async_sessionmaker, scopefunc=current_task)
```

Note that the keyword arguments of the `DBConnection` class are passed to
the `sqlalchemy.ext.asyncio.create_async_engine` function.

## Methods

The `DBConnection` class has the following methods:

- `init_db()`: Initialize the database tables.
- `close()`: Close the database connection.

### init_db

Initialize the database tables.
It also sets the `session` attribute of the base model to
the `async_scoped_session` async session factory:

```python
from sqlactive import DBConnection

DATABASE_URL = 'sqlite+aiosqlite://'
conn = DBConnection(DATABASE_URL, echo=True)
asyncio.run(conn.init_db()) # Initialize the database
```

If your base model is not `ActiveRecordBaseModel` you must pass
your base model class to this method in the `base_model` argument:

```python
from sqlactive import DBConnection, ActiveRecordBaseModel

# Note that it does not matter if your base model
# inherits from `ActiveRecordBaseModel`, you still
# need to pass it to this method
class BaseModel(ActiveRecordBaseModel):
    __abstract__ = True

DATABASE_URL = 'sqlite+aiosqlite://'
conn = DBConnection(DATABASE_URL, echo=True)
asyncio.run(conn.init_db(BaseModel)) # Pass your base model
```

### close

Close the database connection.
It also sets the `session` attribute of the base model to `None`:

```python
from sqlactive import DBConnection

DATABASE_URL = 'sqlite+aiosqlite://'
conn = DBConnection(DATABASE_URL, echo=True)
asyncio.run(conn.init_db())

# Perform operations...

asyncio.run(conn.close()) # Close the database connection
```

If your base model is not `ActiveRecordBaseModel` you should pass
your base model cl0ass to this method in the `base_model` argument:

```python
from sqlactive import DBConnection, ActiveRecordBaseModel

# Note that it does not matter if your base model
# inherits from `ActiveRecordBaseModel`, you still
# need to pass it to this method
class BaseModel(ActiveRecordBaseModel):
    __abstract__ = True

DATABASE_URL = 'sqlite+aiosqlite://'
conn = DBConnection(DATABASE_URL, echo=True)
asyncio.run(conn.init_db())

# Perform operations...

asyncio.run(conn.close(BaseModel)) # Pass your base model
```
