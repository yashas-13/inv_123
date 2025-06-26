"""Simple API key authentication for FastAPI routes.

WHY: maintain basic request authentication to ensure only authorized clients call the API.
WHAT: validates 'X-API-Key' header against the API_KEY environment variable.
HOW: adjust the API_KEY env var or extend with DB lookup; remove dependency to rollback.
Closes: #8
"""

import os
import hashlib
import secrets
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User

API_KEY = os.getenv("API_KEY", "changeme")


def verify_api_key(x_api_key: str = Header(...)):
    """Dependency to compare provided API key with expected value."""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )


# New HTTP Basic auth for endpoints
# WHY: allow authentication using username/password instead of API key (Closes: #10)
# HOW: verify credentials against users table; extend by replacing with OAuth; rollback by using verify_api_key
security = HTTPBasic()


def verify_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Validate provided credentials against stored users."""
    user = db.query(User).filter(User.username == credentials.username).first()
    hashed = hashlib.sha256(credentials.password.encode()).hexdigest()
    if not user or not secrets.compare_digest(user.password, hashed):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user

