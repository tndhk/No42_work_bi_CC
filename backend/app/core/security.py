"""Security utilities for password hashing and JWT token management."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import jwt as jose_jwt  # type: ignore[import-untyped]
from jose import JWTError
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Bcrypt work factor (rounds) - 12 is a good balance of security and performance
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt with 12 rounds.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string (bcrypt format)
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    hashed: str = hashed_bytes.decode('utf-8')
    return hashed


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Verify a plain text password against a bcrypt hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    if hashed_password is None:
        return False

    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        verified: bool = bcrypt.checkpw(password_bytes, hashed_bytes)
        return verified
    except ValueError as e:
        logger.warning("password_verification_failed", error="invalid_hash_format", details=str(e))
        return False
    except Exception as e:
        logger.error("password_verification_error", error=type(e).__name__, details=str(e))
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Custom expiration time. If None, uses default from config

    Returns:
        JWT access token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.jwt_expiration_hours
        )

    to_encode.update({"exp": expire})

    encoded_jwt: str = jose_jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_access_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token data dictionary, or None if token is invalid/expired
    """
    if not token:
        return None

    try:
        payload: Dict[str, Any] = jose_jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_failed", error="jwt_error", details=str(e))
        return None
    except ValueError as e:
        logger.warning("jwt_decode_failed", error="invalid_value", details=str(e))
        return None
    except Exception as e:
        logger.error("jwt_decode_error", error=type(e).__name__, details=str(e))
        return None
