"""Tests for API dependency functions."""
import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.user import User
from app.api.deps import require_admin


class TestRequireAdmin:
    """Test require_admin dependency."""

    def test_require_admin_with_admin_user(self):
        """Test admin user passes the check."""
        admin_user = User(
            id="user_admin",
            email="admin@example.com",
            role="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = require_admin(admin_user)
        assert result == admin_user

    def test_require_admin_with_regular_user(self):
        """Test regular user is rejected with 403."""
        regular_user = User(
            id="user_123",
            email="user@example.com",
            role="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc_info:
            require_admin(regular_user)
        assert exc_info.value.status_code == 403
        assert "Admin" in exc_info.value.detail

    def test_require_admin_with_default_role(self):
        """Test user with default role is rejected."""
        user = User(
            id="user_123",
            email="user@example.com",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with pytest.raises(HTTPException) as exc_info:
            require_admin(user)
        assert exc_info.value.status_code == 403
