import sys
from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.operators import OperatorType
from sqlalchemy.sql.selectable import Select

# ruff: noqa: F401
if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

T = TypeVar('T')

Query = Select[tuple[T, ...]]

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
