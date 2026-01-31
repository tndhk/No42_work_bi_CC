"""Password policy validation."""
from typing import Optional, Tuple


def validate_password(password: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate password against security policy.

    Policy requirements:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)

    Args:
        password: Password string to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if not password:
        return False, "Password cannot be empty"

    if not isinstance(password, str):
        return False, "Password must be a string"

    if len(password.strip()) == 0:
        return False, "Password cannot be only whitespace"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    has_uppercase = any(c.isupper() for c in password)
    has_lowercase = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not has_uppercase:
        return False, "Password must contain at least one uppercase letter"

    if not has_lowercase:
        return False, "Password must contain at least one lowercase letter"

    if not has_digit:
        return False, "Password must contain at least one digit"

    return True, None
