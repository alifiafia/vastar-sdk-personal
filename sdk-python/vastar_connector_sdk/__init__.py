"""
Vastar Connector SDK for Python
A powerful SDK for building connectors that communicate with external APIs
through the Vastar Connector Runtime via IPC (Inter-Process Communication).
"""
from .runtime_client import RuntimeClient
from .exceptions import ConnectorException
from .types import (
    ErrorClass,
    HTTPRequest,
    HTTPResponse,
    RuntimeConfig,
)
from .utils import (
    HTTPResponseHelper,
    SSEParser,
    retry_with_backoff,
)
__version__ = "0.1.0"
__all__ = [
    "RuntimeClient",
    "ConnectorException",
    "ErrorClass",
    "HTTPRequest",
    "HTTPResponse",
    "RuntimeConfig",
    "HTTPResponseHelper",
    "SSEParser",
    "retry_with_backoff",
]
