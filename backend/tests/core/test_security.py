"""Security tests following TDD."""
import pytest
from datetime import timedelta
from jose import jwt as jose_jwt


class TestPasswordHashing:
    """Password hashing and verification tests."""

    def test_hash_password_returns_hashed_string(self):
        """hash_password()がハッシュ化されたパスワード文字列を返す."""
        from app.core.security import hash_password

        plain_password = "MySecurePassword123!"
        hashed = hash_password(plain_password)

        assert isinstance(hashed, str)
        assert hashed != plain_password
        assert len(hashed) > len(plain_password)

    def test_hash_password_produces_different_hash_each_time(self):
        """hash_password()が毎回異なるハッシュを生成する."""
        from app.core.security import hash_password

        plain_password = "MySecurePassword123!"
        hashed1 = hash_password(plain_password)
        hashed2 = hash_password(plain_password)

        assert hashed1 != hashed2

    def test_verify_password_returns_true_for_correct_password(self):
        """verify_password()が正しいパスワードでTrueを返す."""
        from app.core.security import hash_password, verify_password

        plain_password = "MySecurePassword123!"
        hashed = hash_password(plain_password)

        result = verify_password(plain_password, hashed)
        assert result is True

    def test_verify_password_returns_false_for_incorrect_password(self):
        """verify_password()が間違ったパスワードでFalseを返す."""
        from app.core.security import hash_password, verify_password

        plain_password = "MySecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(plain_password)

        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_password_returns_false_for_empty_password(self):
        """verify_password()が空のパスワードでFalseを返す."""
        from app.core.security import hash_password, verify_password

        plain_password = "MySecurePassword123!"
        hashed = hash_password(plain_password)

        result = verify_password("", hashed)
        assert result is False

    def test_verify_password_handles_none_gracefully(self):
        """verify_password()がNoneハッシュで例外を発生させない."""
        from app.core.security import verify_password

        try:
            result = verify_password("password", None)
            assert result is False
        except Exception:
            pytest.fail("verify_password should not raise exception for None hashed_password")


class TestJWTToken:
    """JWT token creation and verification tests."""

    def test_create_access_token_returns_string(self):
        """create_access_token()がJWTトークン文字列を返す."""
        from app.core.security import create_access_token

        data = {"sub": "user@example.com", "user_id": 123}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiration(self):
        """create_access_token()がカスタム有効期限でトークンを生成する."""
        from app.core.security import create_access_token
        from app.core.config import settings

        data = {"sub": "user@example.com", "user_id": 123}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta)

        # Decode and verify expiration time
        decoded = jose_jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert "exp" in decoded
        assert decoded["sub"] == "user@example.com"
        assert decoded["user_id"] == 123

    def test_decode_access_token_returns_data_dict(self):
        """decode_access_token()がデータを含む辞書を返す."""
        from app.core.security import create_access_token, decode_access_token

        data = {"sub": "user@example.com", "user_id": 456}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user@example.com"
        assert decoded["user_id"] == 456

    def test_decode_access_token_returns_none_for_invalid_token(self):
        """decode_access_token()が無効なトークンでNoneを返す."""
        from app.core.security import decode_access_token

        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_decode_access_token_returns_none_for_expired_token(self):
        """decode_access_token()が期限切れトークンでNoneを返す."""
        from app.core.security import create_access_token, decode_access_token

        data = {"sub": "user@example.com"}
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        token = create_access_token(data, expires_delta)

        decoded = decode_access_token(token)
        assert decoded is None

    def test_decode_access_token_returns_none_for_malformed_token(self):
        """decode_access_token()が不正なトークンでNoneを返す."""
        from app.core.security import decode_access_token

        malformed_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid"
        decoded = decode_access_token(malformed_token)

        assert decoded is None

    def test_decode_access_token_returns_none_for_empty_string(self):
        """decode_access_token()が空文字列でNoneを返す."""
        from app.core.security import decode_access_token

        decoded = decode_access_token("")
        assert decoded is None

    def test_decode_access_token_returns_none_for_none_token(self):
        """decode_access_token()がNoneトークンでNoneを返す."""
        from app.core.security import decode_access_token

        decoded = decode_access_token(None)
        assert decoded is None

    def test_create_and_decode_roundtrip(self):
        """create_access_token()とdecode_access_token()がラウンドトリップで一致."""
        from app.core.security import create_access_token, decode_access_token

        original_data = {"sub": "user@example.com", "user_id": 789, "role": "admin"}
        token = create_access_token(original_data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == original_data["sub"]
        assert decoded["user_id"] == original_data["user_id"]
        assert decoded["role"] == original_data["role"]
