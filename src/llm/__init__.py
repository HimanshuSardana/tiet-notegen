"""Shared LLM helpers backed by the opencode Go inference API."""

from .client import (
    DEFAULT_MODEL,
    generate_text,
    get_api_key,
    get_base_url,
    get_client,
    get_default_headers,
    get_session_id,
)

__all__ = [
    "DEFAULT_MODEL",
    "generate_text",
    "get_api_key",
    "get_base_url",
    "get_client",
    "get_default_headers",
    "get_session_id",
]
