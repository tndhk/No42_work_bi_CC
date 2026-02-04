"""Config tests following TDD."""


def test_settings_default_values():
    """デフォルト値が正しく設定される."""
    from app.core.config import Settings

    settings = Settings()

    assert settings.env == "local"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000


def test_settings_can_be_overridden():
    """環境変数で設定値を上書きできる."""
    from app.core.config import Settings

    settings = Settings(env="production", api_host="127.0.0.1", api_port=9000)

    assert settings.env == "production"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 9000
