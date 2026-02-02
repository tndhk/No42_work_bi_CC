"""Tests for User models."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.user import User, UserCreate, UserInDB, UserUpdate


class TestUserCreate:
    """Test UserCreate model."""

    def test_user_create_valid(self):
        """Test creating UserCreate with valid data."""
        user = UserCreate(
            email="test@example.com",
            password="SecurePassword123!"
        )

        assert user.email == "test@example.com"
        assert user.password == "SecurePassword123!"

    def test_user_create_missing_email(self):
        """Test UserCreate validation fails without email."""
        with pytest.raises(ValidationError):
            UserCreate(password="SecurePassword123!")

    def test_user_create_missing_password(self):
        """Test UserCreate validation fails without password."""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")

    def test_user_create_invalid_email(self):
        """Test UserCreate validation fails with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="SecurePassword123!"
            )

    def test_user_create_empty_password(self):
        """Test UserCreate validation fails with empty password."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password=""
            )


class TestUserInDB:
    """Test UserInDB model."""

    def test_user_in_db_valid(self):
        """Test creating UserInDB with valid data."""
        user = UserInDB(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_pwd_hash",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_pwd_hash"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_in_db_missing_id(self):
        """Test UserInDB validation fails without id."""
        with pytest.raises(ValidationError):
            UserInDB(
                email="test@example.com",
                hashed_password="hashed_pwd",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

    def test_user_in_db_missing_hashed_password(self):
        """Test UserInDB validation fails without hashed_password."""
        with pytest.raises(ValidationError):
            UserInDB(
                id="user-123",
                email="test@example.com",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

    def test_user_in_db_default_role(self):
        """Test that UserInDB role defaults to 'user'."""
        user = UserInDB(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_pwd_hash",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert user.role == "user"

    def test_user_in_db_with_admin_role(self):
        """Test that UserInDB role can be set to 'admin'."""
        user = UserInDB(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_pwd_hash",
            role="admin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert user.role == "admin"

    def test_user_in_db_serialization(self):
        """Test UserInDB serialization to dict."""
        now = datetime.utcnow()
        user = UserInDB(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_pwd",
            created_at=now,
            updated_at=now
        )

        user_dict = user.model_dump()
        assert user_dict["id"] == "user-123"
        assert user_dict["email"] == "test@example.com"
        assert "hashed_password" in user_dict


class TestUser:
    """Test User (public) model."""

    def test_user_valid(self):
        """Test creating User with valid data."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert user.id == "user-123"
        assert user.email == "test@example.com"

    def test_user_no_hashed_password_in_response(self):
        """Test that User doesn't expose hashed_password."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        user_dict = user.model_dump()
        assert "hashed_password" not in user_dict

    def test_user_default_role(self):
        """Test that User role defaults to 'user'."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert user.role == "user"

    def test_user_with_admin_role(self):
        """Test that User role can be set to 'admin'."""
        user = User(
            id="user-123",
            email="test@example.com",
            role="admin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert user.role == "admin"

    def test_user_missing_email(self):
        """Test User validation fails without email."""
        with pytest.raises(ValidationError):
            User(
                id="user-123",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )


class TestUserUpdate:
    """Test UserUpdate model."""

    def test_user_update_valid(self):
        """Test creating UserUpdate with valid data."""
        update = UserUpdate(password="NewPassword123!")

        assert update.password == "NewPassword123!"

    def test_user_update_optional_fields(self):
        """Test UserUpdate with optional fields."""
        update = UserUpdate()

        assert update.password is None

    def test_user_update_empty_password(self):
        """Test UserUpdate validation fails with empty password."""
        with pytest.raises(ValidationError):
            UserUpdate(password="")
