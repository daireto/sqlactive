"""Custom exceptions."""

class SQLActiveError(Exception):
    """Common base class for all SQLActive errors."""


class NoSettableError(SQLActiveError):
    """Attribute not settable."""

    def __init__(self, class_name: str, attribute_name: str) -> None:
        """Attribute not settable.

        Parameters
        ----------
        class_name : str
            The name of the model class.
        attribute_name : str
            The name of the attribute.
        """
        super().__init__(f"attribute not settable: '{attribute_name}' in model '{class_name}'")


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


class NoSessionError(SQLActiveError):
    """No session available."""

    def __init__(self) -> None:
        """No session available."""
        super().__init__('Cannot get session. Please, call SaActiveRecord.set_session()')


class RelationError(SQLActiveError):
    """Relation not found."""

    def __init__(self, class_name: str, relation_name: str) -> None:
        """Relation not found.

        Parameters
        ----------
        class_name : str
            The name of the model class.
        relation_name : str
            The name of the relation.
        """
        super().__init__(f"no such relation: '{relation_name}' in model '{class_name}'")
