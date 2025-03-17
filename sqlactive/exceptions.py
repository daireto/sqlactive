"""Custom exceptions."""


class SQLActiveError(Exception):
    """Common base class for all SQLActive errors."""

    def __init__(self, message: str, note: str = '') -> None:
        """Creates a new SQLActive error.

        Parameters
        ----------
        message : str
            Error message.
        """
        super().__init__(message)
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
        super().__init__(
            f'model {class_name} has a composite primary key', note
        )


class ModelAttributeError(SQLActiveError, AttributeError):
    """Attribute not found in model."""

    def __init__(
        self, attr_name: str, class_name: str, note: str = ''
    ) -> None:
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
            f'no such attribute: {attr_name!r} in model {class_name}', note
        )


class NoColumnOrHybridPropertyError(SQLActiveError, AttributeError):
    """Attribute is neither a column nor a hybrid property."""

    def __init__(
        self, attr_name: str, class_name: str, note: str = ''
    ) -> None:
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
            f'no such column or hybrid property: {attr_name!r} in '
            f'model {class_name}',
            note,
        )


class NoFilterableError(SQLActiveError, AttributeError):
    """Attribute not filterable."""

    def __init__(
        self, attr_name: str, class_name: str, note: str = ''
    ) -> None:
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
        super().__init__(
            'cannot get session; set_session() must be called first', note
        )


class NoSearchableError(SQLActiveError, AttributeError):
    """Attribute not searchable."""

    def __init__(
        self, attr_name: str, class_name: str, note: str = ''
    ) -> None:
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

    def __init__(
        self, attr_name: str, class_name: str, note: str = ''
    ) -> None:
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

    def __init__(
        self, attr_name: str, class_name: str, note: str = ''
    ) -> None:
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

    def __init__(
        self, relation_name: str, class_name: str, note: str = ''
    ) -> None:
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
            f'no such relation: {relation_name!r} in model {class_name}', note
        )
