"""Runtime client for communicating with Vastar Connector Runtime."""

import json
import os
import socket
import struct
import time
from typing import Dict, Optional

import flatbuffers

from .exceptions import ConnectorException
from .types import (
    ErrorClass,
    HTTPRequest,
    HTTPResponse,
    MessageType,
    RuntimeConfig,
    FRAME_LENGTH_SIZE,
    MESSAGE_TYPE_SIZE,
    MAX_PAYLOAD_SIZE,
)

# Import FlatBuffers generated code
from .Vastar.Connector.Ipc.ExecuteRequest import (
    ExecuteRequest,
    Start as ExecuteRequestStart,
    AddRequestId,
    AddTenantId,
    AddWorkspaceId,
    AddTraceId,
    AddConnectorName,
    AddOperation,
    AddDeadlineAtMs,
    AddPayload,
    End as ExecuteRequestEnd,
)
from .Vastar.Connector.Ipc.ExecuteResponse import ExecuteResponse


class RuntimeClient:
    """
    RuntimeClient provides IPC communication with Vastar Connector Runtime.

    Features:
    - Unix Domain Socket support (Linux/macOS) for optimal performance
    - TCP fallback for Windows or network scenarios
    - FlatBuffers protocol for efficient serialization
    - HTTP connector with SSE streaming support
    - Type-safe APIs with Python type hints
    - Automatic connection management
    - Context manager support (with statement)

    Example:
        >>> with RuntimeClient() as client:
        ...     response = client.execute_http(HTTPRequest(
        ...         method="GET",
        ...         url="https://api.example.com/data"
        ...     ))
        ...     print(f"Status: {response.status_code}")
    """

    def __init__(self, config: Optional[RuntimeConfig] = None):
        """
        Initialize RuntimeClient.

        Args:
            config: Runtime configuration. If None, uses defaults.
        """
        if config is None:
            config = RuntimeConfig()

        self.config = config
        self._socket: Optional[socket.socket] = None
        self._request_id_seq = int(time.time() * 1000)  # milliseconds
        self._pending_requests: Dict[int, dict] = {}
        self._receive_buffer = bytearray()

    def connect(self) -> None:
        """Connect to Vastar Runtime."""
        if self._socket is not None:
            return  # Already connected

        if self.config.use_tcp:
            # TCP connection
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.config.tcp_host, self.config.tcp_port))
            print(f"🔌 Connected via TCP: {self.config.tcp_host}:{self.config.tcp_port}")
        else:
            # Unix socket connection
            socket_path = os.environ.get("VASTAR_SOCKET_PATH", self.config.socket_path)
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(socket_path)
            print(f"🐧 Connected via Unix Socket: {socket_path}")

        # Set socket timeout
        self._socket.settimeout(self.config.timeout_ms / 1000.0)

    def execute_http(self, request: HTTPRequest) -> HTTPResponse:
        """
        Execute HTTP request through runtime.

        Args:
            request: HTTP request configuration

        Returns:
            HTTPResponse object with status, headers, and body

        Raises:
            ConnectorException: If request fails
            ConnectionError: If not connected to runtime
        """
        if self._socket is None:
            self.connect()

        # Generate request ID
        self._request_id_seq += 1
        request_id = self._request_id_seq

        # Get tenant/workspace IDs
        tenant_id = request.tenant_id or self.config.tenant_id
        workspace_id = request.workspace_id or self.config.workspace_id
        timeout_ms = request.timeout_ms or self.config.timeout_ms
        deadline_ms = int(time.time() * 1000) + timeout_ms

        # Build HTTP payload (connector-specific data)
        http_payload = {
            "method": request.method,
            "url": request.url,
        }

        if request.headers:
            http_payload["headers"] = request.headers

        if request.body:
            http_payload["body"] = request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body

        payload_json = json.dumps(http_payload)
        payload_bytes = payload_json.encode("utf-8")

        # Build FlatBuffers ExecuteRequest
        builder = flatbuffers.Builder(4096)

        # Create strings (CRITICAL: must be before startExecuteRequest)
        tenant_id_offset = builder.CreateString(tenant_id)
        connector_name_offset = builder.CreateString("http")
        operation_offset = builder.CreateString("request")
        payload_offset = builder.CreateByteVector(payload_bytes)

        workspace_id_offset = 0
        if workspace_id:
            workspace_id_offset = builder.CreateString(workspace_id)

        trace_id_offset = 0
        if request.trace_id:
            trace_id_offset = builder.CreateString(request.trace_id)

        # Build table
        ExecuteRequestStart(builder)
        AddRequestId(builder, request_id)
        AddTenantId(builder, tenant_id_offset)
        if workspace_id_offset > 0:
            AddWorkspaceId(builder, workspace_id_offset)
        if trace_id_offset > 0:
            AddTraceId(builder, trace_id_offset)
        AddConnectorName(builder, connector_name_offset)
        AddOperation(builder, operation_offset)
        AddDeadlineAtMs(builder, deadline_ms)
        AddPayload(builder, payload_offset)

        request_offset = ExecuteRequestEnd(builder)
        builder.Finish(request_offset)

        # Get FlatBuffers bytes
        request_bytes = bytes(builder.Output())

        # Send frame
        self._send_frame(MessageType.EXECUTE_REQUEST, request_bytes)

        # Wait for response
        return self._wait_for_response(request_id, timeout_ms)

    def _send_frame(self, message_type: MessageType, payload: bytes) -> None:
        """Send frame to runtime."""
        if self._socket is None:
            raise ConnectionError("Not connected to runtime")

        total_len = MESSAGE_TYPE_SIZE + len(payload)

        # Frame: [length:4][type:1][payload:N]
        frame = bytearray()
        frame.extend(struct.pack(">I", total_len))  # Big-endian uint32
        frame.append(message_type)
        frame.extend(payload)

        self._socket.sendall(frame)

    def _wait_for_response(self, request_id: int, timeout_ms: int) -> HTTPResponse:
        """Wait for response from runtime."""
        start_time = time.time()
        timeout_s = timeout_ms / 1000.0

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_s:
                raise ConnectorException(
                    "Request timeout",
                    ErrorClass.TIMEOUT,
                    request_id
                )

            # Receive data
            try:
                data = self._socket.recv(4096)
                if not data:
                    raise ConnectionError("Connection closed by runtime")

                self._receive_buffer.extend(data)
            except socket.timeout:
                continue

            # Process frames
            while len(self._receive_buffer) >= FRAME_LENGTH_SIZE:
                # Read frame length
                frame_length = struct.unpack(">I", self._receive_buffer[:FRAME_LENGTH_SIZE])[0]

                if frame_length > MAX_PAYLOAD_SIZE:
                    raise ValueError(f"Invalid frame length: {frame_length}")

                total_frame_size = FRAME_LENGTH_SIZE + frame_length

                if len(self._receive_buffer) < total_frame_size:
                    # Wait for more data
                    break

                # Extract frame
                frame_data = bytes(self._receive_buffer[FRAME_LENGTH_SIZE:total_frame_size])
                self._receive_buffer = self._receive_buffer[total_frame_size:]

                # Process frame
                response = self._process_frame(frame_data)
                if response and response.request_id == request_id:
                    return response

    def _process_frame(self, frame_data: bytes) -> Optional[HTTPResponse]:
        """Process received frame."""
        message_type = frame_data[0]
        payload = frame_data[MESSAGE_TYPE_SIZE:]

        if message_type != MessageType.EXECUTE_RESPONSE:
            print(f"Unexpected message type: {message_type}")
            return None

        # Parse ExecuteResponse
        response = ExecuteResponse.GetRootAs(payload, 0)

        request_id = response.RequestId()
        error_class = ErrorClass(response.ErrorClass())

        if error_class != ErrorClass.SUCCESS:
            error_message = response.ErrorMessage()
            if error_message is None:
                error_message = "Unknown error"
            else:
                error_message = error_message.decode("utf-8") if isinstance(error_message, bytes) else error_message

            raise ConnectorException(error_message, error_class, request_id)

        # Parse response payload
        payload_length = response.PayloadLength()
        if payload_length == 0:
            raise ConnectorException("Empty response payload", ErrorClass.PERMANENT, request_id)

        payload_bytes = bytes(response.PayloadAsNumpy())
        payload_json = payload_bytes.decode("utf-8")

        try:
            http_response = json.loads(payload_json)

            return HTTPResponse(
                request_id=request_id,
                status_code=http_response.get("status_code") or http_response.get("statusCode") or 0,
                headers=http_response.get("headers") or {},
                body=http_response.get("body", "").encode("utf-8") if isinstance(http_response.get("body"), str) else http_response.get("body", b""),
                duration_us=response.DurationUs(),
                error_class=ErrorClass.SUCCESS,
            )
        except json.JSONDecodeError as e:
            raise ConnectorException(
                f"Failed to parse response: {e}",
                ErrorClass.PERMANENT,
                request_id
            )

    def close(self) -> None:
        """Close connection to runtime."""
        if self._socket:
            self._socket.close()
            self._socket = None
            print("✅ Connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

