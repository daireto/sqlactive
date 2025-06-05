"""Custom exceptions."""


class SQLActiveError(Exception):
    """Common base class for all SQLActive errors."""

    def __init__(self, message: str, note: str = '') -> None:
        """Create a new SQLActive error.

        Parameters
        ----------
        message : str
            Error message.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(message)
        note = note.strip()
        if note:
            self.add_note(note)


class CompositePrimaryKeyError(SQLActiveError, ValueError):
    """Composite primary key."""

    def __init__(self, class_name: str, note: str = '') -> None:
        """Composite primary key.

        Parameters
        ----------
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(f'model {class_name} has a composite primary key', note)


class EagerLoadPathTupleError(SQLActiveError, ValueError):
    """Invalid eager load path tuple."""

    def __init__(self, path: tuple[object, object], note: str = '') -> None:
        """Invalid eager load path tuple.

        Parameters
        ----------
        path : str
            The invalid path.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'expected boolean for second element of tuple in {path!r}',
            note,
        )


class FilterTypeError(SQLActiveError, TypeError):
    """Invalid filter type."""

    def __init__(self, filters: object, note: str = '') -> None:
        """Invalid filter type.

        Parameters
        ----------
        filters : object
            The invalid filters.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'expected dict or list in filters'
            f', got {type(filters).__name__}: {filters!r}',
            note,
        )


class InvalidJoinMethodError(SQLActiveError, ValueError):
    """Invalid join method."""

    def __init__(self, attr_name: str, join_method: str, note: str = '') -> None:
        """Invalid join method.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        join_method : str
            The invalid join method.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(f'invalid join method {join_method!r} for {attr_name!r}', note)


class ModelAttributeError(SQLActiveError, AttributeError):
    """Attribute not found in model."""

    def __init__(self, attr_name: str, class_name: str, note: str = '') -> None:
        """Attribute not found in model.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'no such attribute: {attr_name!r} in model {class_name}',
            note,
        )


class NegativeIntegerError(SQLActiveError, ValueError):
    """Integer must be >= 0."""

    def __init__(self, name: str, value: int, note: str = '') -> None:
        """Offset must be >= 0.

        Parameters
        ----------
        name : str
            The name of the parameter.
        value : int
            The value of the parameter.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(f'{name} must be >= 0, got {value}', note)


class NoColumnOrHybridPropertyError(SQLActiveError, AttributeError):
    """Attribute is neither a column nor a hybrid property."""

    def __init__(self, attr_name: str, class_name: str, note: str = '') -> None:
        """Attribute is neither a column nor a hybrid property.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'no such column or hybrid property: {attr_name!r} in model {class_name}',
            note,
        )


class NoFilterableError(SQLActiveError, AttributeError):
    """Attribute not filterable."""

    def __init__(self, attr_name: str, class_name: str, note: str = '') -> None:
        """Attribute not filterable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'attribute not filterable: {attr_name!r} in model {class_name}',
            note,
        )


class NoSessionError(SQLActiveError, RuntimeError):
    """No session available."""

    def __init__(self, note: str = '') -> None:
        """No session available.

        Parameters
        ----------
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__('cannot get session; set_session() must be called first', note)


class NoSearchableColumnsError(SQLActiveError, RuntimeError):
    """No searchable columns in model."""

    def __init__(self, class_name: str, note: str = '') -> None:
        """No searchable columns in model.

        Parameters
        ----------
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'model {class_name} has no searchable columns',
            note,
        )


class NoSearchableError(SQLActiveError, AttributeError):
    """Attribute not searchable."""

    def __init__(self, attr_name: str, class_name: str, note: str = '') -> None:
        """Attribute not searchable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'attribute not searchable: {attr_name!r} in model {class_name}',
            note,
        )


class NoSettableError(SQLActiveError, AttributeError):
    """Attribute not settable."""

    def __init__(self, attr_name: str, class_name: str, note: str = '') -> None:
        """Attribute not settable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'attribute not settable: {attr_name!r} in model {class_name}',
            note,
        )


class NoSortableError(SQLActiveError, AttributeError):
    """Attribute not sortable."""

    def __init__(self, attr_name: str, class_name: str, note: str = '') -> None:
        """Attribute not sortable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'attribute not sortable: {attr_name!r} in model {class_name}',
            note,
        )


class OperatorError(SQLActiveError, ValueError):
    """Operator not found."""

    def __init__(self, op_name: str, note: str = '') -> None:
        """Operator not found.

        Parameters
        ----------
        op_name : str
            The name of the operator.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(f'no such operator: {op_name!r}', note)


class RelationError(SQLActiveError, AttributeError):
    """Relation not found."""

    def __init__(self, relation_name: str, class_name: str, note: str = '') -> None:
        """Relation not found.

        Parameters
        ----------
        relation_name : str
            The name of the relation.
        class_name : str
            The name of the model class.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(
            f'no such relation: {relation_name!r} in model {class_name}',
            note,
        )


class RootClassNotFoundError(SQLActiveError, ValueError):
    """Root class not found."""

    def __init__(self, query: str, note: str = '') -> None:
        """Root class not found.

        Parameters
        ----------
        query : str
            The query.
        note : str, optional
            Additional note, by default ''.

        """
        super().__init__(f'could not find root class of query: {query}', note)
