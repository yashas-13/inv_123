"""Simple API key authentication for FastAPI routes.

WHY: maintain basic request authentication to ensure only authorized clients call the API.
WHAT: validates 'X-API-Key' header against the API_KEY environment variable.
HOW: adjust the API_KEY env var or extend with DB lookup; remove dependency to rollback.
Closes: #8
"""

import os
from fastapi import Header, HTTPException, status

API_KEY = os.getenv("API_KEY", "changeme")


def verify_api_key(x_api_key: str = Header(...)):
    """Dependency to compare provided API key with expected value."""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

