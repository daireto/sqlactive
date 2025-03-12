import sys
from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.operators import OperatorType

if sys.version_info >= (3, 11):
    from typing import Self  # noqa: F401
else:
    from typing_extensions import Self  # noqa: F401

T = TypeVar('T')

EagerLoadPath = (
    InstrumentedAttribute[Any] | tuple[InstrumentedAttribute[Any], bool]
)

ColumnElementOrAttr = ColumnElement[Any] | InstrumentedAttribute[Any]

ColumnExpressionOrStrLabelArgument = str | ColumnElementOrAttr

DjangoFilters = (
    dict[str, Any]
    | dict[OperatorType, Any]
    | list[dict[str, Any]]
    | list[dict[OperatorType, Any]]
)

EagerSchema = dict[
    InstrumentedAttribute[Any],
    str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
]

OperationFunction = Callable[[ColumnElementOrAttr, Any], ColumnElement[Any]]

RowType = TypeVar('RowType', bound=Any)
