"""Custom exceptions."""


class SQLActiveError(Exception):
    """Common base class for all SQLActive errors."""


class CompositePrimaryKeyError(SQLActiveError):
    """Composite primary key."""

    def __init__(self, class_name: str) -> None:
        """Composite primary key.

        Parameters
        ----------
        class_name : str
            The name of the model class.
        """
        super().__init__(f"model '{class_name}' has a composite primary key")


class InvalidJoinMethodError(SQLActiveError):
    """Invalid join method."""

    def __init__(self, join_method: str) -> None:
        """Invalid join method.

        Parameters
        ----------
        join_method : str
            Join method.
        """
        super().__init__(f"no such join method: '{join_method}'")


class OperatorError(SQLActiveError):
    """Operator not found."""

    def __init__(self, op_name: str) -> None:
        """Operator not found.

        Parameters
        ----------
        op_name : str
            The name of the operator.
        """
        super().__init__(f"no such operator: '{op_name}'")


class ModelAttributeError(SQLActiveError):
    """Attribute not found in model."""

    def __init__(self, attr_name: str, class_name: str) -> None:
        """Attribute not found in model.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        """
        super().__init__(
            f"no such attribute: '{attr_name}' in "
            f"model '{class_name}'"
        )


class NoColumnOrHybridPropertyError(SQLActiveError):
    """Attribute is neither a column nor a hybrid property."""

    def __init__(self, attr_name: str, class_name: str) -> None:
        """Attribute is neither a column nor a hybrid property.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        """
        super().__init__(
            f"no such column or hybrid property: '{attr_name}' in "
            f"model '{class_name}'"
        )


class NoFilterableError(SQLActiveError):
    """Attribute not filterable."""

    def __init__(self, attr_name: str, class_name: str) -> None:
        """Attribute not filterable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        """
        super().__init__(
            f"attribute not filterable: '{attr_name}' in model '{class_name}'"
        )


class NoSessionError(SQLActiveError):
    """No session available."""

    def __init__(self) -> None:
        """No session available."""
        super().__init__(
            'cannot get session: set_session() must be called first'
        )


class NoSearchableError(SQLActiveError):
    """Attribute not searchable."""

    def __init__(self, attr_name: str, class_name: str) -> None:
        """Attribute not searchable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        """
        super().__init__(
            f"attribute not searchable: '{attr_name}' in model '{class_name}'"
        )


class NoSettableError(SQLActiveError):
    """Attribute not settable."""

    def __init__(self, attr_name: str, class_name: str) -> None:
        """Attribute not settable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        """
        super().__init__(
            f"attribute not settable: '{attr_name}' in model '{class_name}'"
        )


class NoSortableError(SQLActiveError):
    """Attribute not sortable."""

    def __init__(self, attr_name: str, class_name: str) -> None:
        """Attribute not sortable.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        class_name : str
            The name of the model class.
        """
        super().__init__(
            f"attribute not sortable: '{attr_name}' in model '{class_name}'"
        )


class RelationError(SQLActiveError):
    """Relation not found."""

    def __init__(self, relation_name: str, class_name: str) -> None:
        """Relation not found.

        Parameters
        ----------
        relation_name : str
            The name of the relation.
        class_name : str
            The name of the model class.
        """
        super().__init__(
            f"no such relation: '{relation_name}' in model '{class_name}'"
        )
