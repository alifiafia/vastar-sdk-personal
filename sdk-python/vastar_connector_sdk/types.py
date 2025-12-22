"""Type definitions for Vastar Connector SDK."""
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional
class ErrorClass(IntEnum):
    """Error classification for connector operations."""
    SUCCESS = 0
    TRANSIENT = 1
    PERMANENT = 2
    RATE_LIMITED = 3
    TIMEOUT = 4
    INVALID_REQUEST = 5
@dataclass
class RuntimeConfig:
    """Configuration for RuntimeClient."""
    tenant_id: str = "default"
    workspace_id: str = ""
    timeout_ms: int = 60000
    socket_path: str = "/tmp/vastar-connector-runtime.sock"
    use_tcp: bool = False
    tcp_host: str = "127.0.0.1"
    tcp_port: int = 5000
@dataclass
class HTTPRequest:
    """HTTP request configuration."""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[bytes] = None
    timeout_ms: Optional[int] = None
    tenant_id: Optional[str] = None
    workspace_id: Optional[str] = None
    trace_id: Optional[str] = None
@dataclass
class HTTPResponse:
    """HTTP response data."""
    request_id: int
    status_code: int
    headers: Dict[str, str]
    body: bytes
    duration_us: int
    error_class: ErrorClass
    error_message: Optional[str] = None
# Protocol constants
FRAME_LENGTH_SIZE = 4
MESSAGE_TYPE_SIZE = 1
MAX_PAYLOAD_SIZE = 10 * 1024 * 1024
DEFAULT_TIMEOUT_MS = 60000
DEFAULT_SOCKET_PATH = "/tmp/vastar-connector-runtime.sock"
class MessageType(IntEnum):
    """Frame message types."""
    EXECUTE_REQUEST = 0x00
    EXECUTE_RESPONSE = 0x01
