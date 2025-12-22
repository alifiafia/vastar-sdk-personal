"""Exception classes for Vastar Connector SDK."""

from .types import ErrorClass


class ConnectorException(Exception):
    """Exception thrown by connector operations."""

    def __init__(self, message: str, error_class: ErrorClass, request_id: int):
        """
        Initialize ConnectorException.

        Args:
            message: Error message
            error_class: Error classification
            request_id: Request identifier
        """
        super().__init__(message)
        self.message = message
        self.error_class = error_class
        self.request_id = request_id

    def is_retryable(self) -> bool:
        """Check if error is retryable."""
        return self.error_class in (
            ErrorClass.TRANSIENT,
            ErrorClass.RATE_LIMITED,
            ErrorClass.TIMEOUT,
        )

    def get_error_class_name(self) -> str:
        """Get error class name as string."""
        return self.error_class.name

    def __str__(self) -> str:
        """String representation."""
        return f"ConnectorException(request_id={self.request_id}, error_class={self.get_error_class_name()}, message='{self.message}')"

    def __repr__(self) -> str:
        """Detailed representation."""
        return self.__str__()

