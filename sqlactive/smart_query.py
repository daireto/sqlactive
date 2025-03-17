"""This module defines ``SmartQueryMixin`` class."""

from collections.abc import Generator, Sequence
from typing import Any

from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.strategy_options import _AbstractLoad
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import asc, desc, extract, operators
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.operators import OperatorType, or_

from .exceptions import (
    NoColumnOrHybridPropertyError,
    NoFilterableError,
    NoSearchableError,
    NoSortableError,
    OperatorError,
    RelationError,
)
from .inspection import InspectionMixin
from .types import (
    ColumnExpressionOrStrLabelArgument,
    DjangoFilters,
    EagerSchema,
    OperationFunction,
    Query,
    Self,
)
from .utils import (
    eager_expr_from_schema,
    flatten_nested_filter_keys,
    get_query_root_cls,
)

Aliases = dict[
    str, tuple[AliasedClass[InspectionMixin], InstrumentedAttribute[Any]]
]


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
        mapper, _class = cls._get_mapper()

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
                    op = cls._operators.get(op_name)
                    if not op:
                        raise OperatorError(
                            op_name,
                            f'expression {attr!r} has incorrect operator: '
                            f'{op_name!r}',
                        )

                # assume equality operator for other cases (say, id=1)
                else:
                    attr_name, op = attr, operators.eq

                if attr_name not in valid_attributes:
                    raise NoFilterableError(
                        attr_name,
                        _class.__name__,
                        f'expression {attr!r} has incorrect attribute: '
                        f'{attr_name!r}',
                    )

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
        mapper, _class = cls._get_mapper()

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
        mapper, _class = cls._get_mapper()

        expressions: list[ColumnElement[Any]] = []
        for attr in columns:
            if attr not in _class.sortable_attributes:
                raise NoColumnOrHybridPropertyError(attr, _class.__name__)

            expressions.append(getattr(mapper, attr))

        return expressions

    @classmethod
    def eager_expr(cls, schema: EagerSchema) -> list[_AbstractLoad]:
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
        schema : EagerSchema
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
        return eager_expr_from_schema(schema)

    @classmethod
    def smart_query(
        cls,
        query: Query,
        criteria: Sequence[ColumnElement[bool]] | None = None,
        filters: DjangoFilters | None = None,
        sort_columns: (
            Sequence[ColumnExpressionOrStrLabelArgument] | None
        ) = None,
        sort_attrs: Sequence[str] | None = None,
        group_columns: (
            Sequence[ColumnExpressionOrStrLabelArgument] | None
        ) = None,
        group_attrs: Sequence[str] | None = None,
        schema: EagerSchema | None = None,
    ) -> Query:
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
        query : Query
            Native SQLAlchemy query.
        criteria : Sequence[ColumnElement[bool]] | None, optional
            SQLAlchemy syntax filter expressions, by default None.
        filters : DjangoFilters | None, optional
            Django-like filter expressions, by default None.
        sort_columns : Sequence[ColumnExpressionOrStrLabelArgument] | None, optional
            Standalone sort columns, by default None.
        sort_attrs : Sequence[str] | None, optional
            Django-like sort expressions, by default None.
        group_columns : Sequence[ColumnExpressionOrStrLabelArgument] | None, optional
            Standalone group columns, by default None.
        group_attrs : Sequence[str] | None, optional
            Django-like group expressions, by default None.
        schema : EagerSchema | None, optional
            Schema for the eager loading, by default None.

        Returns
        -------
        Query
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
        filters = filters or {}
        sort_attrs = sort_attrs or []
        group_attrs = group_attrs or []

        root_cls = get_query_root_cls(query, raise_on_none=True)
        aliases = cls._get_aliases(root_cls, filters, sort_attrs, group_attrs)

        # Joins
        for aliased_class, attr in aliases.values():
            query = query.outerjoin(aliased_class, attr)  # type: ignore

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
            query = query.options(*eager_expr_from_schema(schema))

        return query

    @classmethod
    def apply_search_filter(
        cls,
        query: Query,
        search_term: str,
        columns: Sequence[str | InstrumentedAttribute[Any]] | None = None,
    ) -> Query:
        """Applies a search filter to the query.

        Searches for ``search_term`` in the searchable columns
        of the model. If ``columns`` are provided, searches only
        these columns.

        Parameters
        ----------
        query : Query
            Native SQLAlchemy query.
        search_term : str
            Search term.
        columns : Sequence[str  |  InstrumentedAttribute[Any]] | None, optional
            Columns to search in, by default None.

        Returns
        -------
        Query
            SQLAlchemy query with the search filter applied.

        Examples
        --------
        To learn how to use this method, see the
        ``sqlactive.active_record.ActiveRecordMixin.search`` method.
        It uses this method internally.
        """
        root_cls = get_query_root_cls(query, raise_on_none=True)

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
    def _get_mapper(cls) -> tuple[AliasedClass | type[Self], type[Self]]:
        """Returns the appropriate mapper and class
        for the current entity.
        """
        return (
            (cls, cls.__mapper__.class_)
            if isinstance(cls, AliasedClass)
            else (cls, cls)
        )

    @classmethod
    def _get_aliases(
        cls,
        root_cls: type[Self],
        filters: DjangoFilters,
        sort_attrs: Sequence[str],
        group_attrs: Sequence[str],
    ) -> Aliases:
        """Returns aliases for the query.

        Parameters
        ----------
        root_cls : type[Self]
            The root class of the query.
        filters : DjangoFilters
            Django-like filter expressions.
        sort_attrs : Sequence[str]
            Django-like sort expressions.
        group_attrs : Sequence[str]
            Django-like group expressions.

        Returns
        -------
        Aliases
            Aliases for the query.
        """
        attrs = (
            list(flatten_nested_filter_keys(filters))
            + [s.lstrip(cls._DESC_PREFIX) for s in sort_attrs]
            + list(group_attrs)
        )

        aliases = {}
        cls._make_aliases_from_attrs(root_cls, '', attrs, aliases)

        return aliases

    @staticmethod
    def _get_searchable_columns(
        root_cls: type[InspectionMixin],
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
    def _make_aliases_from_attrs(
        cls,
        entity: type[InspectionMixin] | AliasedClass[InspectionMixin],
        entity_path: str,
        attrs: list[str],
        aliases: Aliases,
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
        aliases : Aliases
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
                relations.setdefault(relation_name, []).append(nested_attr)

        for relation_name, nested_attrs in relations.items():
            path = (
                entity_path + cls._RELATION_SPLITTER + relation_name
                if entity_path
                else relation_name
            )
            if relation_name not in entity.relations:
                raise RelationError(
                    relation_name,
                    entity.__name__,
                    f'incorrect relation path: {path!r}',
                )

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
        cls, filters: DjangoFilters, root_cls: type[Self], aliases: Aliases
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
        aliases : Aliases
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
                    e.add_note(f'incorrect filter path: {attr!r}')
                    raise

        elif isinstance(filters, list):
            for f in filters:
                yield from cls._recurse_filters(f, root_cls, aliases)

    @classmethod
    def _sort_query(
        cls,
        query: Query,
        sort_attrs: Sequence[str],
        root_cls: type[Self],
        aliases: Aliases,
    ) -> Query:
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
        query : Query
            Native SQLAlchemy query.
        sort_attrs : Sequence[str]
            Sort columns.
        root_cls : type[SmartQueryMixin]
            Model class.
        aliases : Aliases
            Aliases dictionary.

        Returns
        -------
        Query
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
                e.add_note(f'incorrect order path: {attr!r}')
                raise

        return query

    @classmethod
    def _group_query(
        cls,
        query: Query,
        group_attrs: Sequence[str],
        root_cls: type[Self],
        aliases: Aliases,
    ) -> Query:
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
        query : Query
            Native SQLAlchemy query.
        group_attrs : Sequence[str]
            Group columns.
        root_cls : type[SmartQueryMixin]
            Model class.
        aliases : Aliases
            Aliases dictionary.

        Returns
        -------
        Query
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
                e.add_note(f'incorrect group path: {attr!r}')
                raise

        return query
