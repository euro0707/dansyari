"""Utility functions for LINE bot webhook verification and configuration.

Keeping utilities small and focused helps follow KISS / DRY principles
so they can be reused both in production code and unit tests.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Union

__all__ = [
    "calc_line_signature",
    "verify_line_signature",
]


def calc_line_signature(channel_secret: str, body: Union[str, bytes]) -> str:
    """Return Base64‐encoded HMAC-SHA256 of *body* using *channel_secret*.

    This is the exact algorithm LINE uses to compute the `X-Line-Signature`
    header.  It is exposed separately so it can be unit-tested or reused by
    CLI/debug helpers without importing Web frameworks.
    """
    if isinstance(body, str):
        body = body.encode()
    mac = hmac.new(channel_secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode()


def verify_line_signature(channel_secret: str, body: Union[str, bytes], signature_header: str | None) -> bool:
    """Constant-time comparison between expected and received signature."""
    if not signature_header:
        return False
    expected = calc_line_signature(channel_secret, body)
    # Use hmac.compare_digest for timing-attack safety
    return hmac.compare_digest(expected, signature_header)
