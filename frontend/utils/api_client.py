"""Utility functions for interacting with the backend API from Streamlit pages."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import os

import requests
import streamlit as st

DEFAULT_TIMEOUT = 30


def get_api_base_url() -> str:
    """Resolve the API base URL from Streamlit secrets or environment variables."""
    return st.secrets.get("API_URL", os.getenv("API_URL", "http://127.0.0.1:8000"))


def get_auth_headers() -> Dict[str, str]:
    """Return authorization headers if an admin token is available."""
    token = st.session_state.get("admin_token") or os.getenv("DEFAULT_ADMIN_TOKEN")
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_request(
    method: str,
    endpoint: str,
    *,
    timeout: Optional[int] = None,
    **kwargs: Any,
) -> Tuple[Optional[requests.Response], Optional[str]]:
    """Make an HTTP request to the backend with consistent error handling.

    Returns a tuple of (response, error_message). When error_message is not None,
    the request either failed to send or raised an exception.
    """

    url = f"{get_api_base_url()}{endpoint}"
    headers = kwargs.pop("headers", {}) or {}
    headers.update(get_auth_headers())

    try:
        response = requests.request(
            method.upper(),
            url,
            headers=headers,
            timeout=timeout or DEFAULT_TIMEOUT,
            **kwargs,
        )
        return response, None
    except requests.RequestException as exc:  # pragma: no cover - network issues
        return None, str(exc)


def parse_response_json(response: Optional[requests.Response]) -> Optional[Any]:
    """Safely parse JSON from a response object."""
    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None
