"""HTTP security-control helpers.

Implements the SEC-011 request-body-size check. The pure helper is exposed
here so it can be unit-tested; the FastAPI dependency wiring lives in
``src/api/dependencies.py``.
"""


def body_exceeds_limit(body: bytes, max_bytes: int) -> bool:
    """Return True if the request body is larger than ``max_bytes`` (SEC-011).

    Args:
        body: The raw request body.
        max_bytes: Maximum allowed body size in bytes.

    Returns:
        True when ``len(body) > max_bytes``, otherwise False.
    """
    return len(body) > max_bytes
