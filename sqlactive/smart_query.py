"""This module defines ``SmartQueryMixin`` class."""

from collections import OrderedDict
from collections.abc import Callable, Generator, Sequence
from typing import Any

from sqlalchemy.orm import aliased, joinedload, selectinload, subqueryload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.strategy_options import _AbstractLoad
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import Select, asc, desc, extract, operators
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.operators import OperatorType, or_
from typing_extensions import Self

from .definitions import JOINED, SELECT_IN, SUBQUERY
from .exceptions import (
    InvalidJoinMethodError,
    NoColumnOrHybridPropertyError,
    NoFilterableError,
    NoSearchableError,
    NoSortableError,
    OperatorError,
    RelationError,
)
from .inspection import InspectionMixin

ColumnElementOrAttr = ColumnElement[Any] | InstrumentedAttribute[Any]
ColumnExpressionOrStrLabelArgument = str | ColumnElementOrAttr
OperationFunction = Callable[[ColumnElementOrAttr, Any], ColumnElement[Any]]


class SmartQueryMixin(InspectionMixin):
    """Mixin for SQLAlchemy models to provide smart query methods."""

    __abstract__ = True

    _RELATION_SPLITTER = '___'
    """Separator used to split relationship name from attribute name."""

    _OPERATOR_SPLITTER = '__'
    """Separator used to split operator from attribute name."""

    _DESC_PREFIX = '-'
    """Prefix used to mark descending order."""

    _operators: dict[str, OperationFunction | OperatorType] = {
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
    def filter_expr(cls, **filters: object) -> list[ColumnElement[Any]]:
        """Transform Django-style filters into
        SQLAlchemy expressions.

        Takes keyword arguments like::

            {'rating': 5, 'user_id__in': [1,2]}

        and returns list of expressions like::

            [Post.rating == 5, Post.user_id.in_([1,2])]

        **About alias**

        When using alias, for example::

            alias = aliased(Post) # table name will be ``post_1``

        the query cannot be executed like::

            db.query(alias).filter(*Post.filter_expr(rating=5))

        because it will be compiled to::

            SELECT * FROM post_1 WHERE post.rating=5

        which is wrong. The select is made from ``post_1`` but
        filter is based on ``post``. Such filter will not work.

        A correct way to execute such query is::

            SELECT * FROM post_1 WHERE post_1.rating=5

        For such case, this method (and other methods like
        ``order_expr()`` and ``columns_expr()``) can be called ON ALIAS::

            alias = aliased(Post)
            db.query(alias).filter(*alias.filter_expr(rating=5))

        *Alias realization details:*

        When method is called on alias, it is necessary to
        generate SQL using aliased table (say, ``post_1``),
        but it is also necessary to have a real class to call
        methods on (say, ``Post.relations``). So, there will
        be a ``mapper`` variable that holds table name and a
        ``_class`` variable that holds real class.

        When this method is called ON ALIAS,
        ``mapper`` and ``_class`` will be::

            mapper = <post_1 table>
            _class = <Post>

        When this method is called ON CLASS,
        ``mapper`` and ``_class`` will be::

            mapper = <Post> # it is the same as <Post>.__mapper__.
                            # This is because when <Post>.getattr
                            # is called, SA will magically call
                            # <Post>.__mapper__.getattr()
            _class = <Post>

        .. note::
            This is a very low-level method. It is intended for more
            flexibility. It does not do magic Django-like joins.
            Use the high-level ``smart_query()`` method for that.

        Parameters
        ----------
        **filters
            Django-style filters.

        Returns
        -------
        list[ColumnElement[Any]]
            Filter expressions.

        Raises
        ------
        OperatorError
            If operator is not found.
        NoFilterableError
            If attribute is not filterable.

        Examples
        --------
        Assume a model ``Post``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Post(ActiveRecordBaseModel):
        ...     __tablename__ = 'posts'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     title: Mapped[str] = mapped_column()
        ...     rating: Mapped[int] = mapped_column()
        ...     user_id: Mapped[int] = mapped_column(
        ...         ForeignKey('users.id')
        ...     )
        ...     user: Mapped['User'] = relationship(
        ...         back_populates='posts'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='post'
        ...     )

        Usage:
        >>> Post.filter_expr(rating=5)
        [Post.rating == 5]
        >>> db.query(Post).filter(*Post.filter_expr(rating=5))
        'SELECT * FROM posts WHERE post.rating=5'
        >>> Post.filter_expr(rating=5, user_id__in=[1,2])
        [Post.rating == 5, Post.user_id.in_([1,2])]
        >>> db.query(Post).filter(
        ...     *Post.filter_expr(rating=5, user_id__in=[1,2])
        ... )
        'SELECT * FROM posts WHERE post.rating=5 AND post.user_id IN [1, 2]'

        Using alias:
        >>> alias = aliased(Post)
        >>> alias.filter_expr(rating=5)
        [Post.rating == 5]
        >>> db.query(alias).filter(*alias.filter_expr(rating=5))
        'SELECT * FROM post_1 WHERE post_1.rating=5'
        >>> alias.filter_expr(rating=5, user_id__in=[1,2])
        [Post.rating == 5, Post.user_id.in_([1,2])]
        >>> db.query(alias).filter(
        ...     *alias.filter_expr(rating=5, user_id__in=[1,2])
        ... )
        'SELECT * FROM post_1 WHERE post_1.rating=5 AND post_1.user_id IN [1, 2]'
        """
        if isinstance(cls, AliasedClass):
            mapper, _class = cls, cls.__mapper__.class_
        else:
            mapper = _class = cls

        expressions = []
        valid_attributes = _class.filterable_attributes
        for attr, value in filters.items():
            # if attribute is filtered by method, call this method
            if attr in _class.hybrid_methods:
                method = getattr(_class, attr)
                expressions.append(method(value))

            # else just add simple condition
            # (== for scalars or IN for lists)
            else:
                # determine attribute name and operator
                # if they are explicitly set (say, id__between), take them
                if cls._OPERATOR_SPLITTER in attr:
                    attr_name, op_name = attr.rsplit(cls._OPERATOR_SPLITTER, 1)
                    if op_name not in cls._operators:
                        exc = OperatorError(op_name)
                        exc.add_note(
                            f"expression '{attr}' has incorrect operator: "
                            f"'{op_name}'"
                        )
                        raise exc

                    op = cls._operators[op_name]

                # assume equality operator for other cases (say, id=1)
                else:
                    attr_name, op = attr, operators.eq

                if attr_name not in valid_attributes:
                    exc = NoFilterableError(attr_name, _class.__name__)
                    exc.add_note(
                        f"expression '{attr}' has incorrect attribute: "
                        f"'{attr_name}'"
                    )
                    raise exc

                column = getattr(mapper, attr_name)
                expressions.append(op(column, value))

        return expressions

    @classmethod
    def order_expr(cls, *columns: str) -> list[ColumnElement[Any]]:
        """Transforms Django-style order expressions into
        SQLAlchemy expressions.

        Takes list of columns to order by like::

            ['-rating', 'title']

        and returns list of expressions like::

            [desc(Post.rating), asc(Post.title)]

        **About alias**

        See the `filter_expr() method documentation <https://daireto.github.io/sqlactive/api/smart-query-mixin/#filter_expr>`_
        for more information about using alias. It also explains
        the ``cls``, ``mapper`` and ``_class`` variables used here.

        .. note::
            This is a very low-level method. It is intended for more
            flexibility. It does not do magic Django-like joins.
            Use the high-level ``smart_query()`` method for that.

        Parameters
        ----------
        *columns
            Django-style sort expressions.

        Returns
        -------
        list[ColumnElement[Any]]
            Sort expressions.

        Raises
        ------
        NoSortableError
            If attribute is not sortable.

        Examples
        --------
        Assume a model ``Post``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Post(ActiveRecordBaseModel):
        ...     __tablename__ = 'posts'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     title: Mapped[str] = mapped_column()
        ...     rating: Mapped[int] = mapped_column()
        ...     user_id: Mapped[int] = mapped_column(
        ...         ForeignKey('users.id')
        ...     )
        ...     user: Mapped['User'] = relationship(
        ...         back_populates='posts'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='post'
        ...     )

        Usage:
        >>> Post.order_expr('-rating')
        [desc(Post.rating)]
        >>> db.query(Post).order_by(*Post.order_expr('-rating'))
        'SELECT * FROM posts ORDER BY posts.rating DESC'
        >>> Post.order_expr('-rating', 'title')
        [desc(Post.rating), asc(Post.title)]
        >>> db.query(Post).order_by(
        ...     *Post.order_expr('-rating', 'title')
        ... )
        'SELECT * FROM posts ORDER BY posts.rating DESC, posts.title ASC'

        Using alias:
        >>> alias = aliased(Post)
        >>> alias.order_expr('-rating')
        [desc(Post.rating)]
        >>> db.query(alias).order_by(*alias.order_expr('-rating'))
        'SELECT * FROM posts_1 ORDER BY posts_1.rating DESC'
        >>> alias.order_expr('-rating', 'title')
        [desc(Post.rating), asc(Post.title)]
        >>> db.query(alias).order_by(*alias.order_expr('-rating', 'title'))
        'SELECT * FROM posts_1 ORDER BY posts_1.rating DESC, posts_1.title ASC'
        """
        if isinstance(cls, AliasedClass):
            mapper, _class = cls, cls.__mapper__.class_
        else:
            mapper = _class = cls

        expressions: list[ColumnElement[Any]] = []
        for attr in columns:
            fn, attr = (
                (desc, attr[1:])
                if attr.startswith(cls._DESC_PREFIX)
                else (asc, attr)
            )
            if attr not in _class.sortable_attributes:
                raise NoSortableError(attr, _class.__name__)

            expr = fn(getattr(mapper, attr))
            expressions.append(expr)

        return expressions

    @classmethod
    def columns_expr(cls, *columns: str) -> list[ColumnElement[Any]]:
        """Transforms column names into
        SQLAlchemy model attributes.

        Takes list of column names like::

            ['user_id', 'rating']

        and returns list of model attributes like::

            [Post.user_id, Post.rating]

        This method mostly used for grouping.

        **About alias**

        See the `filter_expr() method documentation <https://daireto.github.io/sqlactive/api/smart-query-mixin/#filter_expr>`_
        for more information about using alias. It also explains
        the ``cls``, ``mapper`` and ``_class`` variables used here.

        .. note::
            This is a very low-level method. It is intended for more
            flexibility. It does not do magic Django-like joins.
            Use the high-level ``smart_query()`` method for that.

        Parameters
        ----------
        *columns
            Column names.

        Returns
        -------
        list[ColumnElement[Any]]
            Model attributes.

        Raises
        ------
        NoColumnOrHybridPropertyError
            If attribute is neither a column nor a hybrid property.

        Examples
        --------
        Assume a model ``Post``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Post(ActiveRecordBaseModel):
        ...     __tablename__ = 'posts'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     title: Mapped[str] = mapped_column()
        ...     rating: Mapped[int] = mapped_column()
        ...     user_id: Mapped[int] = mapped_column(
        ...         ForeignKey('users.id')
        ...     )
        ...     user: Mapped['User'] = relationship(
        ...         back_populates='posts'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='post'
        ...     )

        Usage:
        >>> Post.columns_expr('user_id')
        [Post.user_id]
        >>> Post.columns_expr('user_id', 'rating')
        [Post.user_id, Post.rating]

        Grouping:
        >>> from sqlalchemy.sql import func
        >>> db.query(Post.user_id, func.max(Post.rating))
        ...   .group_by(*Post.columns_expr('user_id'))
        'SELECT posts.user_id, max(posts.rating) FROM posts GROUP BY posts.user_id'
        >>> db.query(Post.user_id, Post.rating)
        ...   .group_by(*Post.columns_expr('user_id', 'rating'))
        'SELECT posts.user_id, posts.rating FROM posts GROUP BY posts.user_id, posts.rating'

        Using alias:
        >>> alias = aliased(Post)
        >>> alias.columns_expr('user_id')
        [Post.user_id]
        >>> alias.columns_expr('user_id', 'rating')
        [Post.user_id, Post.rating]

        Grouping on alias:
        >>> db.query(alias.user_id, func.max(alias.rating))
        ...   .group_by(*alias.columns_expr('user_id'))
        'SELECT posts_1.user_id FROM posts_1 GROUP BY posts_1.user_id'
        >>> db.query(alias.user_id, alias.rating)
        ...   .group_by(*alias.columns_expr('user_id', 'rating'))
        'SELECT posts_1.user_id, posts_1.rating FROM posts_1 GROUP BY posts_1.user_id, posts_1.rating'
        """
        if isinstance(cls, AliasedClass):
            mapper, _class = cls, cls.__mapper__.class_
        else:
            mapper = _class = cls

        expressions: list[ColumnElement[Any]] = []
        for attr in columns:
            if attr not in _class.sortable_attributes:
                raise NoColumnOrHybridPropertyError(attr, _class.__name__)

            expressions.append(getattr(mapper, attr))

        return expressions

    @classmethod
    def eager_expr(
        cls,
        schema: dict[
            InstrumentedAttribute[Any],
            str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
        ],
    ) -> list[_AbstractLoad]:
        """Transforms an eager loading defined schema into
        SQLAlchemy eager loading expressions.

        Takes a schema like::

            schema = {
                Post.user: 'joined',           # joinedload user
                Post.comments: ('subquery', {  # load comments in separate query
                    Comment.user: 'joined'     # but, in this separate query, join user
                })
            }

        and returns eager loading expressions like::

            [
                joinedload(Post.user),
                subqueryload(Post.comments).options(
                    joinedload(Comment.user)
                )
            ]

        The supported eager loading strategies are:
        * **joined**: ``sqlalchemy.orm.joinedload()``
        * **subquery**: ``sqlalchemy.orm.subqueryload()``
        * **selectin**: ``sqlalchemy.orm.selectinload()``

        The constants ``JOINED``, ``SUBQUERY`` and ``SELECT_IN`` are
        defined in the ``sqlactive.definitions`` module and can be used
        instead of the strings:
        >>> from sqlactive.definitions import JOINED, SUBQUERY
        >>> schema = {
        ...     Post.user: JOINED,
        ...     Post.comments: (SUBQUERY, {
        ...         Comment.user: JOINED
        ...     })
        ... }

        Parameters
        ----------
        schema : dict[InstrumentedAttribute[Any], str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict]
            Schema for the eager loading.

        Returns
        -------
        list[_AbstractLoad]
            Eager loading expressions.

        Examples
        --------
        Assume a model ``Post``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Post(ActiveRecordBaseModel):
        ...     __tablename__ = 'posts'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     title: Mapped[str] = mapped_column()
        ...     rating: Mapped[int] = mapped_column()
        ...     user_id: Mapped[int] = mapped_column(
        ...         ForeignKey('users.id')
        ...     )
        ...     user: Mapped['User'] = relationship(
        ...         back_populates='posts'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='post'
        ...     )

        Usage:
        >>> schema = {
        ...     Post.user: JOINED,
        ...     Post.comments: (SUBQUERY, {Comment.user: SELECT_IN}),
        ... }
        >>> expressions = Post.eager_expr(schema)
        >>> post1 = await Post.options(*expressions).limit(1).unique_one()
        >>> post1.user.name
        'Bob Williams'
        >>> post1.comments[0].user.name
        'Bob Williams'
        """
        return cls._eager_expr_from_schema(schema)

    @classmethod
    def smart_query(
        cls,
        query: Select[tuple[Any, ...]],
        criteria: Sequence[ColumnElement[bool]] | None = None,
        filters: (
            dict[str, Any]
            | dict[OperatorType, Any]
            | list[dict[str, Any]]
            | list[dict[OperatorType, Any]]
            | None
        ) = None,
        sort_columns: (
            Sequence[ColumnExpressionOrStrLabelArgument] | None
        ) = None,
        sort_attrs: Sequence[str] | None = None,
        group_columns: (
            Sequence[ColumnExpressionOrStrLabelArgument] | None
        ) = None,
        group_attrs: Sequence[str] | None = None,
        schema: (
            dict[
                InstrumentedAttribute[Any],
                str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
            ]
            | None
        ) = None,
    ) -> Select[tuple[Any, ...]]:
        """Creates a query combining filtering, sorting, grouping
        and eager loading.

        Does magic `Django-like joins <https://docs.djangoproject.com/en/1.10/topics/db/queries/#lookups-that-span-relationships>`_
        like:
        >>> post___user___name__startswith='Bob'

        Does filtering, sorting, grouping and eager loading at the
        same time. And if, say, filters, sorting and grouping need
        the same join, it will be done only once.

        It also supports SQLAlchemy syntax like:
        >>> db.query(User).filter(User.id == 1, User.name == 'Bob')
        >>> db.query(User).filter(or_(User.id == 1, User.name == 'Bob'))
        >>> db.query(Post).order_by(Post.rating.desc())
        >>> db.query(Post).order_by(desc(Post.rating), asc(Post.user_id))

        .. note::
            For more flexibility, you can use the ``filter_expr``,
            ``order_expr``, ``columns_expr`` and ``eager_expr`` methods.
            See the `API Reference <https://daireto.github.io/sqlactive/api/smart-query-mixin/#api-reference>`_
            for more details.

        Parameters
        ----------
        query : Select[tuple[Any, ...]]
            Native SQLAlchemy query.
        criteria : Sequence[ColumnElement[bool]] | None, optional
            SQLAlchemy syntax filter expressions, by default None.
        filters : dict[str, Any] | dict[OperatorType, Any] | list[dict[str, Any]] | list[dict[OperatorType, Any]] | None, optional
            Django-like filter expressions, by default None.
        sort_columns : Sequence[ColumnExpressionOrStrLabelArgument] | None, optional
            Standalone sort columns, by default None.
        sort_attrs : Sequence[str] | None, optional
            Django-like sort expressions, by default None.
        group_columns : Sequence[ColumnExpressionOrStrLabelArgument] | None, optional
            Standalone group columns, by default None.
        group_attrs : Sequence[str] | None, optional
            Django-like group expressions, by default None.
        schema : dict[InstrumentedAttribute[Any], str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict] | None, optional
            Schema for the eager loading, by default None.

        Returns
        -------
        Select[tuple[Any, ...]]
            SQLAlchemy query with filtering, sorting, grouping and
            eager loading.

        Examples
        --------
        >>> query = User.smart_query(
        ...     criteria=(or_(User.age == 30, User.age == 32),),
        ...     filters={'username__like': '%8'},
        ...     sort_columns=(User.username,),
        ...     sort_attrs=('age',),
        ...     schema={
        ...         User.posts: JOINED,
        ...         User.comments: (SUBQUERY, {
        ...             Comment.post: SELECT_IN
        ...         })
        ...     },
        ... )
        >>> users = await query.unique_all()
        >>> [user.username for user in users]
        ['Bob28', 'Ian48', 'Jessica3248']
        >>> users[0].posts[0].title
        'Lorem ipsum'
        >>> users[0].comments[0].post.title
        'Lorem ipsum'
        """
        if not filters:
            filters = {}
        if not sort_attrs:
            sort_attrs = []
        if not group_attrs:
            group_attrs = []

        root_cls: type[Self] = query.__dict__['_propagate_attrs'][
            'plugin_subject'
        ].class_  # for example, User or Post
        attrs = (
            list(cls._flatten_filter_keys(filters))
            + list(map(lambda s: s.lstrip(cls._DESC_PREFIX), sort_attrs))
            + list(group_attrs)
        )
        aliases: OrderedDict[
            str,
            tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]],
        ] = OrderedDict({})
        cls._make_aliases_from_attrs(root_cls, '', attrs, aliases)

        loaded_paths = []
        for path, al in aliases.items():
            relationship_path = path.replace(cls._RELATION_SPLITTER, '.')
            query = query.outerjoin(al[0], al[1])  # type: ignore
            loaded_paths.append(relationship_path)

        # Filtering
        if criteria:
            query = query.filter(*criteria)

        if filters:
            query = query.filter(
                *cls._recurse_filters(filters, root_cls, aliases)
            )

        # Sorting
        if sort_columns:
            query = query.order_by(*sort_columns)

        if sort_attrs:
            query = cls._sort_query(query, sort_attrs, root_cls, aliases)

        # Grouping
        if group_columns:
            query = query.group_by(*group_columns)

        if group_attrs:
            query = cls._group_query(query, group_attrs, root_cls, aliases)

        # Eager loading
        if schema:
            query = query.options(*cls._eager_expr_from_schema(schema))

        return query

    @classmethod
    def apply_search_filter(
        cls,
        query: Select[tuple[Any, ...]],
        search_term: str,
        columns: Sequence[str | InstrumentedAttribute[Any]] | None = None,
    ) -> Select[tuple[Any, ...]]:
        """Applies a search filter to the query.

        Searches for ``search_term`` in the searchable columns
        of the model. If ``columns`` are provided, searches only
        these columns.

        Parameters
        ----------
        query : Select[tuple[Any, ...]]
            Native SQLAlchemy query.
        search_term : str
            Search term.
        columns : Sequence[str  |  InstrumentedAttribute[Any]] | None, optional
            Columns to search in, by default None.

        Returns
        -------
        Select[tuple[Any, ...]]
            SQLAlchemy query with the search filter applied.

        Examples
        --------
        To learn how to use this method, see the
        ``sqlactive.active_record.ActiveRecordMixin.search`` method.
        It uses this method internally.
        """
        root_cls: type[Self] = query.__dict__['_propagate_attrs'][
            'plugin_subject'
        ].class_  # for example, User or Post
        searchable_columns = cls._get_searchable_columns(root_cls, columns)
        if len(searchable_columns) > 1:
            criteria = or_(
                *[
                    getattr(root_cls, col).ilike(f'%{search_term}%')
                    for col in searchable_columns
                ]
            )
        else:
            criteria = getattr(root_cls, searchable_columns[0]).ilike(
                f'%{search_term}%'
            )

        query = query.filter(criteria)  # type: ignore
        return query

    @classmethod
    def _get_searchable_columns(
        cls,
        root_cls: type[Self],
        columns: Sequence[str | InstrumentedAttribute[Any]] | None = None,
    ) -> list[str]:
        """Returns a list of searchable columns.

        If ``columns`` are provided, returns only these columns.

        Parameters
        ----------
        root_cls : type[Self]
            Model class.
        columns : Sequence[str  |  InstrumentedAttribute[Any]] | None, optional
            Columns to search in, by default None.

        Returns
        -------
        list[str]
            List of searchable columns.

        Raises
        ------
        NoSearchableError
            If column is not searchable.
        """
        searchable_columns = []
        if columns:
            for col in columns:
                col_name = col if isinstance(col, str) else col.key
                if col_name not in root_cls.searchable_attributes:
                    raise NoSearchableError(col_name, root_cls.__name__)

                searchable_columns.append(col_name)

            return searchable_columns

        else:
            return root_cls.searchable_attributes

    @classmethod
    def _flatten_filter_keys(
        cls, filters: dict | list
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
                    yield from cls._flatten_filter_keys(value)
                else:
                    yield key

        elif isinstance(filters, list):
            for f in filters:
                yield from cls._flatten_filter_keys(f)

        else:
            raise TypeError(
                f"expected dict or list in filters, got '{type(filters)}'"
            )

    @classmethod
    def _make_aliases_from_attrs(
        cls,
        entity: type[InspectionMixin] | AliasedClass[InspectionMixin],
        entity_path: str,
        attrs: list[str],
        aliases: OrderedDict[
            str,
            tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]],
        ],
    ) -> None:
        """Takes a list of attributes and makes aliases from them.

        It overwrites the provided ``aliases`` dictionary.

        Sample input::

            cls._make_aliases_from_attrs(
                entity=Post,
                entity_path='',
                attrs=[
                    'post___subject_ids',
                    'user_id',
                    '-group_id',
                    'user___name',
                    'post___name'
                ],
                aliases=OrderedDict()
            )

        Sample output:
        >>> relations
        {
            'post': ['subject_ids', 'name'],
            'user': ['name']
        }
        >>> aliases
        {
            'post___subject_ids': (Post, subject_ids),
            'post___name': (Post, name),
            'user___name': (User, name)
        }

        Parameters
        ----------
        entity : type[InspectionMixin] | AliasedClass[InspectionMixin]
            Model class.
        entity_path : str
            Entity path. It should be empty for the first call.
        attrs : list[str]
            List of attributes.
        aliases : OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]]]
            Aliases dictionary. It should be empty for the first call.

        Raises
        ------
        RelationError
            If relationship is not found.
        """
        relations: dict[str, list[str]] = {}
        for attr in attrs:
            # from attr (say, 'post___subject_ids')
            # take relationship name ('post') and
            # nested attribute ('subject_ids')
            if cls._RELATION_SPLITTER in attr:
                relation_name, nested_attr = attr.split(
                    cls._RELATION_SPLITTER, 1
                )
                if relation_name in relations:
                    relations[relation_name].append(nested_attr)
                else:
                    relations[relation_name] = [nested_attr]

        for relation_name, nested_attrs in relations.items():
            path = (
                entity_path + cls._RELATION_SPLITTER + relation_name
                if entity_path
                else relation_name
            )
            if relation_name not in entity.relations:
                exc = RelationError(relation_name, entity.__name__)
                exc.add_note(f"incorrect relation path: '{path}'")
                raise exc

            relationship: InstrumentedAttribute = getattr(
                entity, relation_name
            )
            alias: AliasedClass[InspectionMixin] = aliased(
                relationship.property.mapper.class_
            )  # e.g. aliased(User) or aliased(Post)
            aliases[path] = alias, relationship
            cls._make_aliases_from_attrs(alias, path, nested_attrs, aliases)

    @classmethod
    def _recurse_filters(
        cls,
        filters: (
            dict[str, Any]
            | dict[OperatorType, Any]
            | list[dict[str, Any]]
            | list[dict[OperatorType, Any]]
        ),
        root_cls: type[Self],
        aliases: OrderedDict[
            str,
            tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]],
        ],
    ) -> Generator[Any, None, None]:
        """Parse filters recursively.

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

        and parses them into SQLAlchemy expressions like::

            [
                or_(
                    Post.id > 1000,
                    and_(
                        Post.id < 500,
                        Post.related.property.in_((1,2,3))
                    )
                )
            ]

        Parameters
        ----------
        filters : dict[str, Any] | dict[OperatorType, Any] | list[dict[str, Any]] | list[dict[OperatorType, Any]]
            Django-like filter expressions.
        root_cls : type[SmartQueryMixin]
            Model class.
        aliases : OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]]]
            Aliases dictionary.

        Yields
        ------
        Generator[object, None, None]
            Expression.
        """
        if isinstance(filters, dict):
            for attr, value in filters.items():
                if callable(attr):
                    # e.g. or_, and_, or other sqlalchemy expression
                    yield attr(*cls._recurse_filters(value, root_cls, aliases))
                    continue

                if cls._RELATION_SPLITTER in attr:
                    parts = attr.rsplit(cls._RELATION_SPLITTER, 1)
                    entity, attr_name = aliases[parts[0]][0], parts[1]
                else:
                    entity, attr_name = root_cls, attr

                try:
                    yield from entity.filter_expr(**{attr_name: value})
                except Exception as e:
                    e.add_note(f"incorrect filter path: '{attr}'")
                    raise

        elif isinstance(filters, list):
            for f in filters:
                yield from cls._recurse_filters(f, root_cls, aliases)

    @classmethod
    def _sort_query(
        cls,
        query: Select[tuple[Any, ...]],
        sort_attrs: Sequence[str],
        root_cls: type[Self],
        aliases: OrderedDict[
            str,
            tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]],
        ],
    ) -> Select[tuple[Any, ...]]:
        """Applies an ORDER BY clause to the query.

        Sample input::

            query = select(Post)
            query = cls._sort_query(
                query=query,
                sort_attrs=['-created_at', 'user___name'],
                aliases=OrderedDict({
                    'user': (aliased(User), Post.user),
                })
            )

        Sample output::

            query = query.order_by(
                desc(Post.created_at),
                asc(Post.user.name)
            )

        Parameters
        ----------
        query : Select[tuple[Any, ...]]
            Native SQLAlchemy query.
        sort_attrs : Sequence[str]
            Sort columns.
        root_cls : type[SmartQueryMixin]
            Model class.
        aliases : OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]]]
            Aliases dictionary.

        Returns
        -------
        Select[tuple[Any, ...]]
            Sorted query.
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
            except Exception as e:
                e.add_note(f"incorrect order path: '{attr}'")
                raise

        return query

    @classmethod
    def _group_query(
        cls,
        query: Select[tuple[Any, ...]],
        group_attrs: Sequence[str],
        root_cls: type[Self],
        aliases: OrderedDict[
            str,
            tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]],
        ],
    ) -> Select[tuple[Any, ...]]:
        """Applies a GROUP BY clause to the query.

        Sample input::

            query = select(Post)
            query = cls._group_query(
                query=query,
                group_attrs=['rating', 'user___name'],
                aliases=OrderedDict({
                    'user': (aliased(User), Post.user),
                })
            )

        Sample output::

            query = query.group_by(
                Post.rating,
                Post.user.name,
            )

        Parameters
        ----------
        query : Select[tuple[Any, ...]]
            Native SQLAlchemy query.
        group_attrs : Sequence[str]
            Group columns.
        root_cls : type[SmartQueryMixin]
            Model class.
        aliases : OrderedDict[str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]]]
            Aliases dictionary.

        Returns
        -------
        Select[tuple[Any, ...]]
            Grouped query.
        """
        for attr in group_attrs:
            if cls._RELATION_SPLITTER in attr:
                parts = attr.rsplit(cls._RELATION_SPLITTER, 1)
                entity, attr_name = aliases[parts[0]][0], parts[1]
            else:
                entity, attr_name = root_cls, attr

            try:
                query = query.group_by(*entity.columns_expr(attr_name))
            except Exception as e:
                e.add_note(f"incorrect group path: '{attr}'")
                raise

        return query

    @classmethod
    def _eager_expr_from_schema(
        cls,
        schema: dict[
            InstrumentedAttribute[Any],
            str | tuple[str, dict[InstrumentedAttribute[Any], Any]] | dict,
        ],
    ) -> list[_AbstractLoad]:
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
                join_method, inner_schema = value[0], value[1]
                load_option = cls._create_eager_load_option(path, join_method)
                result.append(
                    load_option.options(
                        *cls._eager_expr_from_schema(inner_schema)
                    )
                )
            elif isinstance(value, dict):
                join_method, inner_schema = JOINED, value
                load_option = cls._create_eager_load_option(path, join_method)
                result.append(
                    load_option.options(
                        *cls._eager_expr_from_schema(inner_schema)
                    )
                )
            else:
                result.append(cls._create_eager_load_option(path, value))

        return result

    @classmethod
    def _create_eager_load_option(
        cls, attr: InstrumentedAttribute[Any], join_method: str
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

        exc = InvalidJoinMethodError(join_method)
        exc.add_note(f"invalid join method: '{join_method}' for '{attr.key}'")
        raise exc
