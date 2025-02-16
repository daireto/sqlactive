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


class NoSessionError(SQLActiveError):
    """No session available."""

    def __init__(self) -> None:
        """No session available."""
        super().__init__('Cannot get session. Please, call SaActiveRecord.set_session()')


class RelationError(SQLActiveError):
    """Relation not found."""

    def __init__(self, relation_name: str) -> None:
        """Relation not found.

        Parameters
        ----------
        relation_name : str
            The name of the relation.
        """
        super().__init__(f"no such relation: '{relation_name}'")
