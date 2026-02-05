"""Configuration management using pydantic-settings."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env")

    env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # JWT
    jwt_secret_key: str = "dev-secret-key-please-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # DynamoDB
    dynamodb_endpoint: str | None = None
    dynamodb_region: str = "ap-northeast-1"
    dynamodb_table_prefix: str = "bi_"

    # S3
    s3_endpoint: str | None = None
    s3_region: str = "ap-northeast-1"
    s3_bucket_datasets: str = "bi-datasets"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # File upload
    max_upload_size_bytes: int = 104857600  # 100MB

    # Executor
    executor_url: str = "http://localhost:8001"
    executor_timeout_seconds: int = 10
    transform_timeout_seconds: int = 300  # 5分（Transform処理用）

    # Cache
    cache_ttl_seconds: int = 3600

    # Scheduler
    scheduler_enabled: bool = False
    scheduler_interval_seconds: int = 60

    # Rate Limiting
    rate_limit_enabled: bool = True

    # Vertex AI / Chatbot
    vertex_ai_project_id: str = ""
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-1.5-pro"
    chatbot_rate_limit_user: int = 5
    chatbot_rate_limit_dashboard: int = 10
    chatbot_max_history_messages: int = 5
    chatbot_max_output_tokens: int = 1024
    chatbot_temperature: float = Field(default=0.7, ge=0.0, le=2.0)


settings = Settings()
