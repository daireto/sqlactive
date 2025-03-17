from collections.abc import Callable, Generator
from typing import Any, Generic, Literal, overload

from sqlalchemy.orm import joinedload, selectinload, subqueryload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.strategy_options import _AbstractLoad

from .definitions import JOINED, SELECT_IN, SUBQUERY
from .types import EagerSchema, Query, T


class classproperty(Generic[T]):
    """Decorator for a Class-level property.

    Usage:
    >>> class Foo:
    ...     @classproperty
    ...     def foo(cls):
    ...         return 'foo'
    >>> Foo.foo
    'foo'
    >>> Foo().foo
    'foo'
    """

    fget: Callable[[Any], T]

    def __init__(self, func: Callable[[Any], T]) -> None:
        self.fget = func

    def __get__(self, _: object, owner_cls: type | None = None) -> T:
        return self.fget(owner_cls)


@overload
def get_query_root_cls(
    query: Query[T], raise_on_none: Literal[True]
) -> type[T]: ...


@overload
def get_query_root_cls(
    query: Query[T], raise_on_none: bool = False
) -> type[T] | None: ...


def get_query_root_cls(
    query: Query[T], raise_on_none: bool = False
) -> type[T] | None:
    """Returns the root class of a query.

    Returns the class of the first column of the query, this is:
    - When selecting specific columns, returns the class of
        the first column (the same for functions like ``count()``).
    - When selecting multiple classes, returns the class of
        the first class.
    - When joining, returns the class of the first table.

    Parameters
    ----------
    query : Query[T]
        SQLAlchemy query.
    raise_on_none : bool, optional
        If True, raises an error if no root class is found,
        by default False.

    Returns
    -------
    type[T] | None
        Root class of the query.

    Raises
    ------
    ValueError
        If no root class is found and ``raise_on_none`` is True.

    Examples
    --------
    Usage:
    >>> query = select(User)
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting specific columns:
    >>> query = select(User.id)
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting specific columns with functions:
    >>> query = select(func.count(User.id))
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting multiple classes:
    >>> query = select(User, Post)
    >>> get_query_root_cls(query)
    <class 'User'>

    Selecting specific columns from multiple classes:
    >>> query = select(User.id, Post.title)
    >>> get_query_root_cls(query)
    <class 'User'>

    Joining:
    >>> query = select(User).join(Post)
    >>> get_query_root_cls(query)
    <class 'User'>
    >>> query = select(Post).join(User)
    >>> get_query_root_cls(query)
    <class 'Post'>

    No root class found:
    >>> query = select(func.count('*'))
    >>> get_query_root_cls(query)
    None
    >>> get_query_root_cls(query, raise_on_none=True)
    Traceback (most recent call last):
        ...
    ValueError: could not find root class of query: <...>
    """
    for col_desc in query.column_descriptions:
        entity = col_desc.get('entity')
        if entity is not None:
            return entity

    if raise_on_none:
        raise ValueError(f'could not find root class of query: {query}')

    return None


def flatten_nested_filter_keys(
    filters: dict | list,
) -> Generator[str, None, None]:
    """Flatten the nested filters, extracting keys where
    they correspond to Django-like query expressions.

    Takes filters like::

        {
            or_: {
                'id__gt': 1000,
                and_ : {
                    'id__lt': 500,
                    'related___property__in': (1,2,3)
                }
            }
        }

    and flattens them yielding::

        'id__gt'
        'id__lt'
        'related___property__in'

    Lists (any Sequence subclass) are also flattened to
    enable support of expressions like::

        (X OR Y) AND (W OR Z)

    So, filters like::

        {
            and_: [
                {
                    or_: {
                        'id__gt': 5,
                        'related_id__lt': 10
                    }
                },
                {
                    or_: {
                        'related_id2__gt': 1,
                        'name__like': 'Bob'
                    }
                }
            ]
        }

    are flattened yielding::

        'id__gt'
        'related_id__lt'
        'related_id2__gt'
        'name__like'

    This method is mostly used to get the aliases from filters.

    Parameters
    ----------
    filters : dict | list
        SQLAlchemy or Django-like filter expressions.

    Yields
    ------
    Generator[str, None, None]
        Flattened keys.

    Raises
    ------
    TypeError
        If ``filters`` is not a dict or list.
    """
    if isinstance(filters, dict):
        for key, value in filters.items():
            if callable(key):
                yield from flatten_nested_filter_keys(value)
            else:
                yield key
    elif isinstance(filters, list):
        for f in filters:
            yield from flatten_nested_filter_keys(f)
    else:
        raise TypeError(
            'expected dict or list in filters, '
            f'got {type(filters).__name__}: {filters!r}'
        )


def create_eager_load_option(
    attr: InstrumentedAttribute[Any], join_method: str
) -> _AbstractLoad:
    """Returns an eager loading option for the given attr.

    Parameters
    ----------
    attr : InstrumentedAttribute
        Model attribute.
    join_method : str
        Join method.

    Returns
    -------
    _AbstractLoad
        Eager load option.

    Raises
    ------
    InvalidJoinMethodError
        If join method is not supported.
    """
    if join_method == JOINED:
        return joinedload(attr)

    if join_method == SUBQUERY:
        return subqueryload(attr)

    if join_method == SELECT_IN:
        return selectinload(attr)

    raise ValueError(
        f'invalid join method: {join_method!r} for {attr.key!r}',
    )


def eager_expr_from_schema(schema: EagerSchema) -> list[_AbstractLoad]:
    """Creates eager loading expressions from
    the provided ``schema`` recursively.

    To see the example, see the
    `eager_expr() method documentation <https://daireto.github.io/sqlactive/api/smart-query-mixin/#eager_expr>`_.

    Parameters
    ----------
    schema : dict[InstrumentedAttribute[Any], str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict]
        Schema for the eager loading.

    Returns
    -------
    list[_AbstractLoad]
        Eager loading expressions.
    """
    result = []
    for path, value in schema.items():
        if isinstance(value, tuple):
            join_method, inner_schema = value
        elif isinstance(value, dict):
            join_method, inner_schema = JOINED, value
        else:
            join_method, inner_schema = value, None

        load_option = create_eager_load_option(path, join_method)
        if inner_schema:
            load_option = load_option.options(
                *eager_expr_from_schema(inner_schema)
            )

        result.append(load_option)

    return result
