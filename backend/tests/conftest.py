"""Pytest configuration and shared fixtures."""
import os
import pytest
from fastapi.testclient import TestClient
import boto3
from moto import mock_aws
from typing import Generator, Any

from app.core.config import settings
from app.api import deps


@pytest.fixture
def client():
    """Create FastAPI test client fixture."""
    from app.main import app

    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_aws_env():
    """Setup AWS environment variables for testing with moto."""
    # Set dummy AWS credentials for testing
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    yield
    # Clean up is not necessary as these are dummy values


@pytest.fixture
def mock_aws_context():
    """Setup mock AWS context that persists for the entire test."""
    with mock_aws():
        yield


@pytest.fixture
def mock_dynamodb_resource(mock_aws_context):
    """Create a mock DynamoDB resource using boto3 (sync) for testing.

    This fixture overrides the get_dynamodb_resource dependency to use
    boto3 (synchronous) instead of aioboto3 (async), which is compatible
    with moto mocking and synchronous TestClient.
    """
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=settings.dynamodb_region
    )
    return dynamodb


@pytest.fixture
def client_with_mock_dynamodb(client, mock_dynamodb_resource, mock_aws_context):
    """Create a TestClient with mocked DynamoDB dependency."""

    async def override_get_dynamodb_resource():
        """Override dependency to return mock resource."""
        yield mock_dynamodb_resource

    from app.main import app
    app.dependency_overrides[deps.get_dynamodb_resource] = override_get_dynamodb_resource

    yield client

    # Cleanup: remove the override
    app.dependency_overrides.clear()


@pytest.fixture
def dynamodb_tables() -> Generator[tuple[dict[str, Any], Any], None, None]:
    """Create DynamoDB tables for testing using moto.

    Creates all four tables with proper schema:
    - users (PK: userId, GSI: UsersByEmail on email)
    - datasets (PK: datasetId, GSI: DatasetsByOwner on ownerId)
    - cards (PK: cardId, GSI: CardsByOwner on ownerId)
    - dashboards (PK: dashboardId, GSI: DashboardsByOwner on ownerId)

    Yields:
        Tuple of (tables dict, dynamodb resource)
    """
    with mock_aws():
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=settings.dynamodb_region
        )

        tables = {}

        # Users table
        users_table_name = f"{settings.dynamodb_table_prefix}users"
        users_table = dynamodb.create_table(
            TableName=users_table_name,
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UsersByEmail',
                    'KeySchema': [
                        {'AttributeName': 'email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        tables['users'] = users_table

        # Datasets table
        datasets_table_name = f"{settings.dynamodb_table_prefix}datasets"
        datasets_table = dynamodb.create_table(
            TableName=datasets_table_name,
            KeySchema=[
                {'AttributeName': 'datasetId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'datasetId', 'AttributeType': 'S'},
                {'AttributeName': 'ownerId', 'AttributeType': 'S'},
                {'AttributeName': 'createdAt', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DatasetsByOwner',
                    'KeySchema': [
                        {'AttributeName': 'ownerId', 'KeyType': 'HASH'},
                        {'AttributeName': 'createdAt', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        tables['datasets'] = datasets_table

        # Cards table
        cards_table_name = f"{settings.dynamodb_table_prefix}cards"
        cards_table = dynamodb.create_table(
            TableName=cards_table_name,
            KeySchema=[
                {'AttributeName': 'cardId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'cardId', 'AttributeType': 'S'},
                {'AttributeName': 'ownerId', 'AttributeType': 'S'},
                {'AttributeName': 'createdAt', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'CardsByOwner',
                    'KeySchema': [
                        {'AttributeName': 'ownerId', 'KeyType': 'HASH'},
                        {'AttributeName': 'createdAt', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        tables['cards'] = cards_table

        # Dashboards table
        dashboards_table_name = f"{settings.dynamodb_table_prefix}dashboards"
        dashboards_table = dynamodb.create_table(
            TableName=dashboards_table_name,
            KeySchema=[
                {'AttributeName': 'dashboardId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'dashboardId', 'AttributeType': 'S'},
                {'AttributeName': 'ownerId', 'AttributeType': 'S'},
                {'AttributeName': 'createdAt', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DashboardsByOwner',
                    'KeySchema': [
                        {'AttributeName': 'ownerId', 'KeyType': 'HASH'},
                        {'AttributeName': 'createdAt', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        tables['dashboards'] = dashboards_table

        yield (tables, dynamodb)


