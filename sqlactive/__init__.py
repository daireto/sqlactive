"""
**SQLActive**

SQLActive is a lightweight and asynchronous ActiveRecord-style wrapper
for SQLAlchemy. Bring Django-like queries, automatic timestamps, nested
eager loading, and serialization/deserialization for SQLAlchemy models.

Documentation: https://daireto.github.io/sqlactive/

**Overview**

This package provides a set of mixins for SQLAlchemy models
and a base class for all models.

The CRUD methods are defined in the ``ActiveRecordMixin`` class which
provides ActiveRecord-like behavior. It also inherits from
``SessionMixin`` and ``SmartQueryMixin`` classes:

- ``SessionMixin`` class provides a session handler.
- ``SmartQueryMixin`` class adds smart query capabilities. It also
inherits from ``InspectionMixin`` class which provides helper methods
for inspecting the model.

The ``ActiveRecordBaseModel`` class is a base class for all models
that inherits from ``ActiveRecordMixin`` class which provides the set
of ActiveRecord-like helper methods for interacting with the database,
``TimestampMixin`` class which adds the ``created_at`` and
``updated_at`` timestamp columns, and ``SerializationMixin`` class which
provides serialization and deserialization methods.

It is recommended to define a ``BaseModel`` class that inherits from
``ActiveRecordBaseModel`` and use it as the base class for all models
as shown in the following example::

    from sqlalchemy import Mapped, mapped_column
    from sqlactive import ActiveRecordBaseModel

    class BaseModel(ActiveRecordBaseModel):
        __abstract__ = True

    class User(BaseModel):
        __tablename__ = 'users'
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

    # Create engine
    DATABASE_URL = 'sqlite+aiosqlite://'
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False
    )

    # Create session
    session = async_scoped_session(
        async_session_factory, scopefunc=asyncio.current_task
    )
    BaseModel.set_session(session)

    # Create tables
    BaseModel.metadata.create_all(engine)

``TimestampMixin`` class defines the ``created_at`` and ``updated_at``
columns with default values and onupdate behavior. To know how to
customize the timestamps behavior, check the
`TimestampMixin documentation <https://daireto.github.io/sqlactive/api/timestamp-mixin/>`_.

Your ``BaseModel`` class can also inherit directly from the mixins. For
example, if you don't want to implement automatic timestamps don't
inherit from ``ActiveRecordBaseModel`` class. Instead, inherit from
``ActiveRecordMixin`` and/or ``SerializationMixin`` as shown in the
following example::

    from sqlalchemy import Mapped, mapped_column
    from sqlactive import ActiveRecordMixin, SerializationMixin

    class BaseModel(ActiveRecordMixin, SerializationMixin):
        __abstract__ = True

    class User(BaseModel):
        __tablename__ = 'users'
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

.. note::
    When defining a ``BaseModel`` class, don't forget to set
    ``__abstract__`` to ``True`` in the base class to avoid
    creating tables for the base class.

**ActiveRecord-like methods**

The following methods are defined in the ``ActiveRecordMixin`` class:
>>> bob = User.insert(name='Bob')
>>> bob
# <User #1>
>>> bob.name
# Bob
>>> User.where(name='Bob').all()
# [<User #1>]
>>> User.get(1)
# <User #1>
>>> bob.update(name='Bob2')
>>> bob.name
# Bob2
>>> bob.to_dict()
# {'id': 2, 'name': 'Bob2'}
>>> bob.delete()
>>> User.all()
# []

.. warning::
    All relations used in filtering/sorting/grouping should be
    explicitly set, not just being a ``backref``. This is because
    SQLActive does not know the relation direction and cannot infer it.
    So, when defining a relationship like::

        class User(BaseModel):
            # ...
            posts: Mapped[list['Post']] = relationship(
                back_populates='user'
            )

    It is required to define the reverse relationship::

        class Post(BaseModel):
            # ...
            user: Mapped['User'] = relationship(
                back_populates='posts'
            )

**DBConnection helper**

To create a DB connection, create an instance of the ``DBConnection``
class and call the ``init_db`` method::

    from sqlactive import ActiveRecordBaseModel, DBConnection

    DATABASE_URL = 'sqlite+aiosqlite://'
    conn = DBConnection(DATABASE_URL, echo=True)
    asyncio.run(conn.init_db())

To close the connection, call the ``close`` method::

    from sqlactive import ActiveRecordBaseModel, DBConnection

    DATABASE_URL = 'sqlite+aiosqlite://'
    conn = DBConnection(DATABASE_URL, echo=True)
    asyncio.run(conn.init_db())

    # Perform operations...

    asyncio.run(conn.close())

If your base model is not ``ActiveRecordBaseModel`` you must pass your
base model class to the ``base_model`` argument of the ``init_db`` and
``close`` methods::

    from sqlactive import DBConnection, ActiveRecordBaseModel

    # Note that it does not matter if your base model
    # inherits from ``ActiveRecordBaseModel``, you still
    # need to pass it to this method
    class BaseModel(ActiveRecordBaseModel):
        __abstract__ = True

    DATABASE_URL = 'sqlite+aiosqlite://'
    conn = DBConnection(DATABASE_URL, echo=True)
    asyncio.run(conn.init_db(BaseModel)) # Pass your base model

    # Perform operations...

    asyncio.run(conn.close(BaseModel))  # Pass your base model

**Execute native SQLAlchemy queries**

You can execute native SQLAlchemy queries using the ``execute`` method::

    from sqlalchemy import select, func
    from sqlactive import execute

    query = select(User.age, func.count(User.id)).group_by(User.age)
    result = await execute(query)

If your base model is not ``ActiveRecordBaseModel`` you
must pass your base model class to the ``base_model`` argument
of the ``execute`` method::

    from sqlalchemy import select, func
    from sqlactive import ActiveRecordBaseModel, execute

    # Note that it does not matter if your base model
    # inherits from ``ActiveRecordBaseModel``, you still
    # need to pass it to this method
    class BaseModel(ActiveRecordBaseModel):
        __abstract__ = True

    class User(BaseModel):
        __tablename__ = 'users'
        # ...

    query = select(User.age, func.count(User.id)).group_by(User.age)
    result = await execute(query, BaseModel)

.. warning::
    Your base model must have a session in order to use this method.
    Otherwise, it will raise an ``NoSessionError`` exception.
    If you are not using the ``DBConnection`` class to initialize
    your base model, you can call its ``set_session`` method
    to set the session::

        from sqlactive import ActiveRecordBaseModel

        class BaseModel(ActiveRecordBaseModel):
            __abstract__ = True

        session = async_scoped_session(
            async_session_factory, scopefunc=asyncio.current_task
        )
        BaseModel.set_session(session)  # Set the session

        query = select(User.age, func.count(User.id)).group_by(User.age)
        result = await execute(query, BaseModel)
"""

from .active_record import ActiveRecordMixin
from .base_model import ActiveRecordBaseModel
from .conn import DBConnection, execute
from .definitions import JOINED, SELECT_IN, SUBQUERY
from .serialization import SerializationMixin
from .timestamp import TimestampMixin

__all__ = [
    'ActiveRecordBaseModel',
    'ActiveRecordMixin',
    'SerializationMixin',
    'TimestampMixin',
    'JOINED',
    'SUBQUERY',
    'SELECT_IN',
    'DBConnection',
    'execute',
]


__version__ = '0.3.0'
