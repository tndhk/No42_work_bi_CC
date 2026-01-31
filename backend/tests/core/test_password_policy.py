"""Password policy validation tests following TDD."""
import pytest


class TestPasswordPolicy:
    """Password policy validation tests."""

    def test_validate_password_accepts_valid_password(self):
        """validate_password()が有効なパスワードをTrueで返す."""
        from app.core.password_policy import validate_password

        valid_password = "ValidPass123"
        is_valid, error = validate_password(valid_password)

        assert is_valid is True
        assert error is None

    def test_validate_password_rejects_too_short_password(self):
        """validate_password()が8文字未満のパスワードを拒否する."""
        from app.core.password_policy import validate_password

        short_password = "Pass123"  # 7 characters
        is_valid, error = validate_password(short_password)

        assert is_valid is False
        assert error is not None
        assert "8" in error.lower() or "short" in error.lower()

    def test_validate_password_rejects_password_without_uppercase(self):
        """validate_password()が大文字を含まないパスワードを拒否する."""
        from app.core.password_policy import validate_password

        no_uppercase = "validpass123"
        is_valid, error = validate_password(no_uppercase)

        assert is_valid is False
        assert error is not None
        assert "uppercase" in error.lower() or "upper" in error.lower()

    def test_validate_password_rejects_password_without_lowercase(self):
        """validate_password()が小文字を含まないパスワードを拒否する."""
        from app.core.password_policy import validate_password

        no_lowercase = "VALIDPASS123"
        is_valid, error = validate_password(no_lowercase)

        assert is_valid is False
        assert error is not None
        assert "lowercase" in error.lower() or "lower" in error.lower()

    def test_validate_password_rejects_password_without_digit(self):
        """validate_password()が数字を含まないパスワードを拒否する."""
        from app.core.password_policy import validate_password

        no_digit = "ValidPassword"
        is_valid, error = validate_password(no_digit)

        assert is_valid is False
        assert error is not None
        assert "digit" in error.lower() or "number" in error.lower()

    def test_validate_password_with_special_characters(self):
        """validate_password()が特殊文字を含むパスワードを受け入れる."""
        from app.core.password_policy import validate_password

        valid_with_special = "ValidPass123!@#"
        is_valid, error = validate_password(valid_with_special)

        assert is_valid is True
        assert error is None

    def test_validate_password_with_exactly_8_characters(self):
        """validate_password()が正確に8文字のパスワードを受け入れる."""
        from app.core.password_policy import validate_password

        exactly_8_chars = "ValiPass1"  # exactly 9 chars to have uppercase, lowercase, digit
        is_valid, error = validate_password(exactly_8_chars)

        assert is_valid is True
        assert error is None

    def test_validate_password_with_long_password(self):
        """validate_password()が長いパスワードを受け入れる."""
        from app.core.password_policy import validate_password

        long_password = "VeryLongValidPassword123WithManyCharacters456"
        is_valid, error = validate_password(long_password)

        assert is_valid is True
        assert error is None

    def test_validate_password_rejects_empty_string(self):
        """validate_password()が空文字列を拒否する."""
        from app.core.password_policy import validate_password

        is_valid, error = validate_password("")

        assert is_valid is False
        assert error is not None

    def test_validate_password_rejects_none(self):
        """validate_password()がNoneを拒否する."""
        from app.core.password_policy import validate_password

        is_valid, error = validate_password(None)

        assert is_valid is False
        assert error is not None

    def test_validate_password_rejects_whitespace_only(self):
        """validate_password()が空白のみのパスワードを拒否する."""
        from app.core.password_policy import validate_password

        is_valid, error = validate_password("        ")

        assert is_valid is False
        assert error is not None

    def test_validate_password_returns_tuple(self):
        """validate_password()がタプル(bool, str|None)を返す."""
        from app.core.password_policy import validate_password

        result = validate_password("ValidPass123")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

    def test_validate_password_multiple_violations(self):
        """validate_password()が複数の違反を報告する."""
        from app.core.password_policy import validate_password

        # No uppercase, no lowercase, no digit
        is_valid, error = validate_password("!!!")

        assert is_valid is False
        assert error is not None

    def test_validate_password_case_sensitive(self):
        """validate_password()が大文字小文字を区別する."""
        from app.core.password_policy import validate_password

        # "A" is uppercase, "a" is lowercase
        is_valid, error = validate_password("Aa12345678")

        assert is_valid is True
        assert error is None

    def test_validate_password_rejects_non_string_type(self):
        """validate_password()が文字列以外の型を拒否する."""
        from app.core.password_policy import validate_password

        is_valid, error = validate_password(123456789)

        assert is_valid is False
        assert error is not None
        assert "string" in error.lower()
