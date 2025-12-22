"""Utility functions and helpers for Vastar Connector SDK."""

import json
import time
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar

from .exceptions import ConnectorException
from .types import HTTPResponse, ErrorClass


T = TypeVar('T')


class HTTPResponseHelper:
    """Utility methods for working with HTTP responses."""

    @staticmethod
    def is_2xx(response: HTTPResponse) -> bool:
        """Check if response status is 2xx (success)."""
        return 200 <= response.status_code < 300

    @staticmethod
    def is_3xx(response: HTTPResponse) -> bool:
        """Check if response status is 3xx (redirect)."""
        return 300 <= response.status_code < 400

    @staticmethod
    def is_4xx(response: HTTPResponse) -> bool:
        """Check if response status is 4xx (client error)."""
        return 400 <= response.status_code < 500

    @staticmethod
    def is_5xx(response: HTTPResponse) -> bool:
        """Check if response status is 5xx (server error)."""
        return 500 <= response.status_code < 600

    @staticmethod
    def get_body_as_string(response: HTTPResponse, encoding: str = "utf-8") -> str:
        """Get response body as string."""
        return response.body.decode(encoding)

    @staticmethod
    def get_body_as_json(response: HTTPResponse) -> Any:
        """Get response body as parsed JSON."""
        body_str = HTTPResponseHelper.get_body_as_string(response)
        return json.loads(body_str)

    @staticmethod
    def get_header(response: HTTPResponse, name: str) -> Optional[str]:
        """
        Get header value (case-insensitive).

        Args:
            response: HTTP response
            name: Header name

        Returns:
            Header value or None if not found
        """
        name_lower = name.lower()
        for key, value in response.headers.items():
            if key.lower() == name_lower:
                return value
        return None


class SSEParser:
    """Parser for Server-Sent Events (SSE) streams."""

    @staticmethod
    def parse_stream(sse_data: str) -> str:
        """
        Parse SSE stream and extract content.

        Args:
            sse_data: Complete SSE stream data

        Returns:
            Concatenated content from all chunks
        """
        chunks = sse_data.split("\n\n")
        full_content = ""

        for chunk in chunks:
            if not chunk.startswith("data: "):
                continue

            content = SSEParser.parse_chunk(chunk)
            if content:
                full_content += content

        return full_content

    @staticmethod
    def parse_chunk(sse_chunk: str) -> Optional[str]:
        """
        Parse single SSE chunk.

        Args:
            sse_chunk: Single SSE chunk (e.g., "data: {...}")

        Returns:
            Extracted content or None
        """
        json_str = sse_chunk[6:]  # Remove "data: " prefix

        if json_str.strip() == "[DONE]":
            return None

        try:
            data = json.loads(json_str)
            choices = data.get("choices", [])

            if choices and len(choices) > 0:
                delta = choices[0].get("delta", {})
                if "content" in delta:
                    return delta["content"]
        except (json.JSONDecodeError, KeyError, IndexError):
            # Ignore parse errors
            pass

        return None

    @staticmethod
    def parse_stream_generator(sse_data: str) -> Generator[str, None, None]:
        """
        Parse SSE stream as generator.

        Args:
            sse_data: Complete SSE stream data

        Yields:
            Content chunks
        """
        chunks = sse_data.split("\n\n")

        for chunk in chunks:
            if not chunk.startswith("data: "):
                continue

            content = SSEParser.parse_chunk(chunk)
            if content:
                yield content


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_backoff_ms: int = 1000,
    max_backoff_ms: int = 30000,
    retryable_errors: Optional[List[str]] = None,
) -> T:
    """
    Execute function with retry logic and exponential backoff.

    Args:
        func: Function to execute
        max_retries: Maximum number of retries
        initial_backoff_ms: Initial backoff in milliseconds
        max_backoff_ms: Maximum backoff in milliseconds
        retryable_errors: List of retryable error class names

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    if retryable_errors is None:
        retryable_errors = ["TRANSIENT", "RATE_LIMITED", "TIMEOUT"]

    last_error = None
    backoff_ms = initial_backoff_ms

    for attempt in range(max_retries + 1):
        try:
            return func()
        except ConnectorException as e:
            last_error = e

            # Check if retryable
            if e.get_error_class_name() not in retryable_errors:
                raise  # Not retryable

            if attempt == max_retries:
                raise  # Max retries reached

            # Wait before retry
            print(f"Retry attempt {attempt + 1}/{max_retries} after {backoff_ms}ms")
            time.sleep(backoff_ms / 1000.0)

            # Exponential backoff
            backoff_ms = min(backoff_ms * 2, max_backoff_ms)
        except Exception as e:
            # Non-connector exceptions
            raise

    if last_error:
        raise last_error

    raise RuntimeError("Unexpected retry loop exit")


def sleep(seconds: float) -> None:
    """Sleep for specified seconds."""
    time.sleep(seconds)

