"""This module defines `SmartQueryMixin` class."""

from collections import OrderedDict
from typing import Any, Callable, Sequence, Generator

from sqlalchemy.inspection import inspect
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.orm.strategy_options import _AbstractLoad
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import asc, desc, operators, extract
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression
from sqlalchemy.orm import Query, aliased, joinedload, subqueryload, selectinload

from .inspection import InspectionMixin
from .definitions import JOINED, SUBQUERY, SELECT_IN


class SmartQueryMixin(InspectionMixin):
    """Mixin for SQLAlchemy models to provide smart query methods."""

    __abstract__ = True

    _RELATION_SPLITTER = '___'
    """Separator used to split relationship name from attribute name."""

    _OPERATOR_SPLITTER = '__'
    """Separator used to split operator from attribute name."""

    _DESC_PREFIX = '-'
    """Prefix used to mark descending order."""

    _operators: dict[str, Callable] = {
        'isnull': lambda c, v: (c == None) if v else (c != None),  # noqa: E711
        'exact': operators.eq,
        'eq': operators.eq,  # equal
        'ne': operators.ne,  # not equal or is not (for None)
        'gt': operators.gt,  # greater than , >
        'ge': operators.ge,  # greater than or equal, >=
        'lt': operators.lt,  # lower than, <
        'le': operators.le,  # lower than or equal, <=
        'in': operators.in_op,
        'notin': operators.notin_op,
        'between': lambda c, v: c.between(v[0], v[1]),
        'like': operators.like_op,
        'ilike': operators.ilike_op,
        'startswith': operators.startswith_op,
        'istartswith': lambda c, v: c.ilike(v + '%'),
        'endswith': operators.endswith_op,
        'iendswith': lambda c, v: c.ilike('%' + v),
        'contains': lambda c, v: c.ilike(f'%{v}%'),
        'year': lambda c, v: extract('year', c) == v,
        'year_ne': lambda c, v: extract('year', c) != v,
        'year_gt': lambda c, v: extract('year', c) > v,
        'year_ge': lambda c, v: extract('year', c) >= v,
        'year_lt': lambda c, v: extract('year', c) < v,
        'year_le': lambda c, v: extract('year', c) <= v,
        'month': lambda c, v: extract('month', c) == v,
        'month_ne': lambda c, v: extract('month', c) != v,
        'month_gt': lambda c, v: extract('month', c) > v,
        'month_ge': lambda c, v: extract('month', c) >= v,
        'month_lt': lambda c, v: extract('month', c) < v,
        'month_le': lambda c, v: extract('month', c) <= v,
        'day': lambda c, v: extract('day', c) == v,
        'day_ne': lambda c, v: extract('day', c) != v,
        'day_gt': lambda c, v: extract('day', c) > v,
        'day_ge': lambda c, v: extract('day', c) >= v,
        'day_lt': lambda c, v: extract('day', c) < v,
        'day_le': lambda c, v: extract('day', c) <= v,
    }
    """Django-like operators mapping."""

    @classmethod
    def filter_expr(cls, **filters: object) -> list:
        """Takes keyword arguments like
        ```python
            {'age_from': 5, 'subject_ids__in': [1,2]}
        ```
        and returns list of expressions like
        ```python
            [Product.age_from == 5, Product.subject_ids.in_([1,2])]
        ```

        Example 1:
        ```python
            db.query(Product).filter(
                *Product.filter_expr(age_from=5, subject_ids__in=[1, 2]))
            # will compile to WHERE age_from = 5 AND subject_ids IN [1, 2]
        ```

        Example 2:
        ```python
            filters = {'age_from': 5, 'subject_ids__in': [1,2]}
            db.query(Product).filter(*Product.filter_expr(**filters))
            # will compile to WHERE age_from = 5 AND subject_ids IN [1, 2]
        ```

        ### About alias:
        When using alias, for example:
            >>> alias = aliased(Product) # table name will be `product_1`
        the query cannot be executed like
            >>> db.query(alias).filter(*Product.filter_expr(age_from=5))
        because it will be compiled to
            >>> SELECT * FROM product_1 WHERE product.age_from=5
        which is wrong.
        The select is made from `product_1` but filter is based on `product`.
        Such filter will not work.

        A correct way to execute such query is
            >>> SELECT * FROM product_1 WHERE product_1.age_from=5
        For such case, `filter_expr` can be called ON ALIAS:
            >>> alias = aliased(Product)
            >>> db.query(alias).filter(*alias.filter_expr(age_from=5))

        Alias realization details:
          * This method can be called either ON ALIAS (say, `alias.filter_expr()`)
            or on class (Product.filter_expr())
          * When method is called on alias, it is necessary to generate SQL using
            aliased table (say, `product_1`), but it is also necessary to have a
            real class to call methods on (say, `Product.relations`).
          * So, there will be a `mapper` variable that holds table name
            and a `_class` variable that holds real class

            When this method is called ON ALIAS, `mapper` and `_class` will be:
            ```txt
                mapper = <product_1 table>
                _class = <Product>
            ```
            When this method is called ON CLASS, `mapper` and `_class` will be:
            ```txt
                mapper = <Product> (it is the same as <Product>.__mapper__.
                                    This is because when <Product>.getattr
                                    is called, SA will magically call
                                    <Product>.__mapper__.getattr())
                _class = <Product>
            ```

        Returns
        -------
        list
            List of filter expressions.

        Raises
        ------
        KeyError
            - If operator is not found in `_operators`.
            - If attribute is not found in `filterable_attributes` property.
        """

        if isinstance(cls, AliasedClass):
            mapper, _class = cls, inspect(cls).mapper.class_
        else:
            mapper = _class = cls

        expressions = []
        valid_attributes = _class.filterable_attributes
        for attr, value in filters.items():
            # if attribute is filtered by method, call this method
            if attr in _class.hybrid_methods:
                method = getattr(_class, attr)
                expressions.append(method(value, mapper=mapper))
            # else just add simple condition (== for scalars or IN for lists)
            else:
                # determine attribute name and operator
                # if they are explicitly set (say, id__between), take them
                if cls._OPERATOR_SPLITTER in attr:
                    attr_name, op_name = attr.rsplit(cls._OPERATOR_SPLITTER, 1)
                    if op_name not in cls._operators:
                        raise KeyError(f'Expression `{attr}` has incorrect operator `{op_name}`')
                    op = cls._operators[op_name]
                # assume equality operator for other cases (say, id=1)
                else:
                    attr_name, op = attr, operators.eq

                if attr_name not in valid_attributes:
                    raise KeyError(f'Expression `{attr}` has incorrect attribute `{attr_name}`')

                column = getattr(mapper, attr_name)
                expressions.append(op(column, value))

        return expressions

    @classmethod
    def order_expr(cls, *columns: str) -> list[UnaryExpression]:
        """Takes list of columns to order by like
        ```python
            ['-first_name', 'phone']
        ```
        and returns list of expressions like
        ```python
            [desc(User.first_name), asc(User.phone)]
        ```

        Example for 1 column:
        ```python
            db.query(User).order_by(*User.order_expr('-first_name'))
            # will compile to ORDER BY user.first_name DESC
        ```

        Example for multiple columns:
        ```python
            columns = ['-first_name', 'phone']
            db.query(User).order_by(*User.order_expr(*columns))
            # will compile to ORDER BY user.first_name DESC, user.phone ASC
        ```

        NOTE: To get more information about `cls`, `mapper` and `_class`, see
        `filter_expr` method documentation.

        Returns
        -------
        list[UnaryExpression]
            List of sort expressions.

        Raises
        ------
        KeyError
            If attribute is not sortable.
        """

        if isinstance(cls, AliasedClass):
            mapper, _class = cls, inspect(cls).mapper.class_
        else:
            mapper = _class = cls

        expressions: list[UnaryExpression] = []
        for attr in columns:
            fn, attr = (desc, attr[1:]) if attr.startswith(cls._DESC_PREFIX) else (asc, attr)
            if attr not in _class.sortable_attributes:
                raise KeyError(f'Cannot order {_class} by {attr}')
            expr = fn(getattr(mapper, attr))
            expressions.append(expr)
        return expressions

    @classmethod
    def eager_expr(
        cls,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict],
    ) -> list[_AbstractLoad]:
        """Creates eager loading expressions from schema.

        Example:
        ```python
            schema = {
                Post.user: JOINED,  # joinedload user
                Post.comments: (SUBQUERY, {  # load comments in separate query
                    Comment.user: JOINED  # but, in this separate query, join user
                })
            }
        ```

        Generates:
        ```python
            [joinedload(Post.user), subqueryload(Post.comments).options(joinedload(Comment.user))]
        ```

        Parameters
        ----------
        schema : dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
            Schema for the eager loading.

        Returns
        -------
        list[_AbstractLoad]
            Eager loading expressions.
        """

        return cls._eager_expr_from_schema(schema)

    @classmethod
    def _build_smart_query(
        cls,
        query: Query,
        criterion: tuple[ColumnElement[Any], ...] | None = None,
        filters: dict[str, Any] | list[dict[str, Any]] | None = None,
        sort_columns: Sequence[InstrumentedAttribute | UnaryExpression] | None = None,
        sort_attrs: Sequence[str] | None = None,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None = None,
    ) -> Query:
        """Builds a smart query.

        Does magic Django-like joins like `post___user___name__startswith='Bob'`
        (see https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships)

        Does filtering, sorting and eager loading at the same time.
        And if, say, filters and sorting need the same join,
        it will be done only once.

        It also supports SQLAlchemy syntax filter expressions like
        >>> db.query(User).filter(User.id == 1, User.name == 'Bob')
        >>> db.query(User).filter(or_(User.id == 1, User.name == 'Bob'))

        by passing them as `binary_exprs` argument.

        NOTE: To get more information about the usage, see documentation of
        `filter_expr`, `order_expr` and `eager_expr` methods.

        Parameters
        ----------
        query : Query
            Query for the model.
        criterion : tuple[ColumnElement[Any], ...] | None, optional
            SQLAlchemy syntax filter expressions, by default None.
        filters : dict[str, Any] | list[dict[str, Any]] | None, optional
            Django-like filter expressions, by default None.
        sort_columns : Sequence[InstrumentedAttribute | UnaryExpression] | None, optional
            Standalone sort columns, by default None.
        sort_attrs : Sequence[str] | None, optional
            Django-like sort expressions, by default None.
        schema : dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict] | None, optional
            Schema for the eager loading, by default None.

        Returns
        -------
        Query
            Smart query.

        Raises
        ------
        KeyError
            If filter or sort path is incorrect.
        """

        if not filters:
            filters = {}
        if not sort_attrs:
            sort_attrs = []

        root_cls = cls._get_root_cls(query)  # for example, User or Post
        attrs = list(cls._flatten_filter_keys(filters)) + list(map(lambda s: s.lstrip(cls._DESC_PREFIX), sort_attrs))
        aliases: OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute]] = OrderedDict({})
        cls._parse_path_and_make_aliases(root_cls, '', attrs, aliases)

        loaded_paths = []
        for path, al in aliases.items():
            relationship_path = path.replace(cls._RELATION_SPLITTER, '.')
            query = query.outerjoin(al[0], al[1])  # type: ignore
            loaded_paths.append(relationship_path)

        if criterion:
            query = query.filter(*criterion)

        if filters:
            query = query.filter(*cls._recurse_filters(filters, root_cls, aliases))

        if sort_columns:
            query = query.order_by(*sort_columns)

        if sort_attrs:
            query = cls._sort_query(query, sort_attrs, root_cls, aliases)

        if schema:
            query = query.options(*cls._eager_expr_from_schema(schema))

        return query

    @classmethod
    def _get_root_cls(cls, query: Query) -> type['SmartQueryMixin']:
        """Gets the root class for query.

        Parameters
        ----------
        query : Query
            Query for the model.

        Returns
        -------
        SessionMixin
            Root class.

        Raises
        ------
        KeyError
            If root class is not found.
        """

        try:
            return query.__dict__['_propagate_attrs']['plugin_subject'].class_
        except KeyError as e:
            raise KeyError(f'Could not find root class for query: {e}')

    @classmethod
    def _flatten_filter_keys(cls, filters: dict | list) -> Generator[str, None, None]:
        """Flatten the nested filters, extracting keys where they correspond
        to Django-like query expressions, e.g:

        Example:
        ```
            {or_: {'id__gt': 1000, and_ : {
                'id__lt': 500,
                'related___property__in': (1,2,3)
            }}}
        ```
        Would be flattened to:
        ```
            'id__gt', 'id__lt', 'related___property__in'
        ```

        Lists (any Sequence subclass) are also flattened to enable support
        of expressions like:

        (X OR Y) AND (W OR Z)

        Example:
        ```
            { and_: [
                {or_: {'id__gt': 5, 'related_id__lt': 10}},
                {or_: {'related_id2__gt': 1, 'name__like': 'Bob' }}
            ]}
        ```
        Would be flattened to:
        ```
            'id__gt', 'related_id__lt', 'related_id2__gt', 'name__like'
        ```

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
            If filters is not a dict or list.
        """

        if isinstance(filters, dict):
            for key, value in filters.items():
                if callable(key):
                    yield from cls._flatten_filter_keys(value)
                else:
                    yield key
        elif isinstance(filters, list):
            for f in filters:
                yield from cls._flatten_filter_keys(f)
        else:
            raise TypeError(f'Unsupported type ({type(filters)}) in filters: {filters}')

    @classmethod
    def _parse_path_and_make_aliases(
        cls,
        entity: type[InspectionMixin] | AliasedClass[InspectionMixin],
        entity_path: str,
        attrs: list[str],
        aliases: OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute]],
    ) -> None:
        """Parse path and make aliases.

        Sample variables:
            ```
            entity: Product
            entity_path: ''
            attrs: ['product___subject_ids', 'user_id', '-group_id',
                    'user___name', 'product___name']
            aliases: {}
            ```

        Sample results:
            ```
            relations: {'product': ['subject_ids', 'name'], 'user': ['name']}
            aliases: {'product___subject_ids': (Product, subject_ids),
                    'product___name': (Product, name),
                    'user___name': (User, name)}
            ```

        Parameters
        ----------
        entity : type[InspectionMixin] | AliasedClass[InspectionMixin]
            Model class.
        entity_path : str
            Entity path. It should be empty for the first call.
        attrs : list[str]
            List of attributes.
        aliases : OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute]]
            Aliases dictionary. It should be empty for the first call.

        Raises
        ------
        KeyError
            If relationship is not found.
        """

        relations: dict[str, list[str]] = {}
        for attr in attrs:
            # from attr (say, 'product___subject_ids')  take
            # relationship name ('product') and nested attribute ('subject_ids')
            if cls._RELATION_SPLITTER in attr:
                relation_name, nested_attr = attr.split(cls._RELATION_SPLITTER, 1)
                if relation_name in relations:
                    relations[relation_name].append(nested_attr)
                else:
                    relations[relation_name] = [nested_attr]

        for relation_name, nested_attrs in relations.items():
            path = entity_path + cls._RELATION_SPLITTER + relation_name if entity_path else relation_name
            if relation_name not in entity.relations:
                raise KeyError(f'Incorrect path `{path}`: {entity} does not have `{relation_name}` relationship.')

            relationship: InstrumentedAttribute = getattr(entity, relation_name)
            alias: AliasedClass[InspectionMixin] = aliased(
                relationship.property.mapper.class_
            )  # e.g. aliased(User) or aliased(Product)
            aliases[path] = alias, relationship
            cls._parse_path_and_make_aliases(alias, path, nested_attrs, aliases)

    @classmethod
    def _recurse_filters(
        cls,
        filters: dict[str, Any] | list[dict[str, Any]],
        root_cls: type['SmartQueryMixin'],
        aliases: OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute]],
    ) -> Generator[Any, None, None]:
        """Parse filters recursively.

        Example:
        ```python
            {
                or_: {
                    'id__gt': 1000,
                    and_ : {
                        'id__lt': 500,
                        'related___property__in': (1,2,3)
                    }
                }
            }
        ```

        Parsed to:
        ```python
            [
                or_(
                    Product.id > 1000,
                    and_(
                        Product.id < 500,
                        Product.related.property.in_((1,2,3))
                    )
                )
            ]
        ```

        Parameters
        ----------
        filters : dict | list
            Django-like filter expressions.
        root_cls : type[SmartQueryMixin]
            Model class.
        aliases : OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute]]
            Aliases dictionary.

        Yields
        ------
        Generator[object, None, None]
            Expression.

        Raises
        ------
        KeyError
            If filter path is incorrect.
        """

        if isinstance(filters, dict):
            for attr, value in filters.items():
                if callable(attr):
                    # E.g. or_, and_, or other sqlalchemy expression
                    yield attr(*cls._recurse_filters(value, root_cls, aliases))
                    continue
                if cls._RELATION_SPLITTER in attr:
                    parts = attr.rsplit(cls._RELATION_SPLITTER, 1)
                    entity, attr_name = aliases[parts[0]][0], parts[1]
                else:
                    entity, attr_name = root_cls, attr
                try:
                    yield from entity.filter_expr(**{attr_name: value})
                except KeyError as e:
                    raise KeyError(f'Incorrect filter path `{attr}`: {e}')
        elif isinstance(filters, list):
            for f in filters:
                yield from cls._recurse_filters(f, root_cls, aliases)

    @classmethod
    def _sort_query(
        cls,
        query: Query,
        sort_attrs: Sequence[str],
        root_cls: type['SmartQueryMixin'],
        aliases: OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute]],
    ) -> Query:
        """Sorts the query.

        Example:
        ```python
            sort_attrs = ['-created_at', 'user___name']
            aliases = OrderedDict({
                'user': (aliased(User), User.name),
            })
        ```

        Generates:
        ```python
            query = query.order_by(
                desc(Product.created_at),
                asc(User.name),
            )
        ```

        Parameters
        ----------
        query : Query
            Query for the model.
        sort_attrs : Sequence[str]
            Sort columns.
        root_cls : type[SmartQueryMixin]
            Model class.
        aliases : OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute]]
            Aliases dictionary.

        Returns
        -------
        Query
            Sorted query.

        Raises
        ------
        KeyError
            If order path is incorrect.
        """

        for attr in sort_attrs:
            if cls._RELATION_SPLITTER in attr:
                prefix = ''
                if attr.startswith(cls._DESC_PREFIX):
                    prefix = cls._DESC_PREFIX
                    attr = attr.lstrip(cls._DESC_PREFIX)
                parts = attr.rsplit(cls._RELATION_SPLITTER, 1)
                entity, attr_name = aliases[parts[0]][0], prefix + parts[1]
            else:
                entity, attr_name = root_cls, attr
            try:
                query = query.order_by(*entity.order_expr(attr_name))
            except KeyError as e:
                raise KeyError(f'Incorrect order path `{attr}`: {e}')

        return query

    @classmethod
    def _eager_expr_from_schema(
        cls,
        schema: dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict],
    ) -> list[_AbstractLoad]:
        """Creates eager loading expressions from schema recursively.

        To see the example, see the `eager_expr` method.

        Parameters
        ----------
        schema : dict[InstrumentedAttribute, str | tuple[str, dict[InstrumentedAttribute, Any]] | dict]
            Schema for the eager loading.

        Returns
        -------
        list[_AbstractLoad]
            Eager loading expressions.
        """

        result = []
        for path, value in schema.items():
            if isinstance(value, tuple):
                join_method, inner_schema = value[0], value[1]
                load_option = cls._create_eager_load_option(path, join_method)
                result.append(load_option.options(*cls._eager_expr_from_schema(inner_schema)))
            elif isinstance(value, dict):
                join_method, inner_schema = JOINED, value
                load_option = cls._create_eager_load_option(path, join_method)
                result.append(load_option.options(*cls._eager_expr_from_schema(inner_schema)))
            else:
                result.append(cls._create_eager_load_option(path, value))

        return result

    @classmethod
    def _create_eager_load_option(cls, path: InstrumentedAttribute, join_method: str) -> _AbstractLoad:
        """Creates eager load option.

        Parameters
        ----------
        path : InstrumentedAttribute
            Model attribute.
        join_method : str
            Join method.

        Returns
        -------
        _AbstractLoad
            Eager load option.

        Raises
        ------
        ValueError
            If join method is incorrect.
        """

        if join_method == JOINED:
            return joinedload(path)
        elif join_method == SUBQUERY:
            return subqueryload(path)
        elif join_method == SELECT_IN:
            return selectinload(path)
        else:
            raise ValueError(f'Bad join method `{join_method}` in `{path}`.')
