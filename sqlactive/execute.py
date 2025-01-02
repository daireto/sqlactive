"""This module defines `execute` function."""

from typing import Any, TypeVar

from sqlalchemy.sql.selectable import TypedReturnsRows
from sqlalchemy.engine import Result
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams

from .base_model import ActiveRecordBaseModel


_T = TypeVar('_T', bound=Any)


async def execute(statement: TypedReturnsRows[_T], base_model: type[ActiveRecordBaseModel] | None = ActiveRecordBaseModel, params: _CoreAnyExecuteParams | None = None, **kwargs) -> Result[_T]:
    """Executes a statement using the `AsyncSession`
    of the `ActiveRecordBaseModel` and return a buffered
    `sqlalchemy.engine.Result` object.

    ```python
    query = select(User.age, func.count(User.id)).group_by(User.age)
    result = await execute(query)
    ```

    The `statement`, `params` and `kwargs` arguments
    of this function are the same as the arguments
    of the `execute` method of the
    `sqlalchemy.ext.asyncio.AsyncSession` class.

    If your base model is not `ActiveRecordBaseModel`,
    you must pass your base model class to this method
    in the `base_model` argument:

    ```python
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
    ```

    NOTE: Your base model must have a session in order to use
    this method. Otherwise, it will raise
    an `NoSessionError` exception.
    """

    if not base_model:
        base_model = ActiveRecordBaseModel
    async with base_model._AsyncSession() as session:
        return await session.execute(statement, params, **kwargs)
