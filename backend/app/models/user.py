"""User models."""
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """User creation request model."""

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")

        return v


class UserInDB(BaseModel):
    """User model stored in database."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime


class User(BaseModel):
    """Public user model (excludes sensitive fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """User update request model."""

    model_config = ConfigDict(from_attributes=True)

    password: Optional[str] = Field(None, min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password meets security requirements if provided.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if v is None:
            return v

        if not v or not v.strip():
            raise ValueError("Password cannot be empty")

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")

        return v
