"""Database connection module."""
from app.db.dynamodb import get_dynamodb_resource
from app.db.s3 import get_s3_client

__all__ = ["get_dynamodb_resource", "get_s3_client"]
