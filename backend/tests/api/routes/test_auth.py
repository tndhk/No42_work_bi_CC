"""Authentication API endpoint tests - TDD RED phase."""
import pytest
from moto import mock_aws
from unittest.mock import patch, AsyncMock, MagicMock
import boto3
from datetime import datetime

from app.core.security import hash_password, create_access_token
from app.core.config import settings


def _create_users_table(dynamodb_resource: any) -> any:
    """Helper function to create users table."""
    table_name = f"{settings.dynamodb_table_prefix}users"
    table = dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "userId", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[
            {
                "IndexName": "UsersByEmail",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )
    # Wait for table to be created
    table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
    return table


@pytest.fixture
def dynamodb_table_for_auth():
    """Create a mock DynamoDB table for auth tests."""
    with mock_aws():
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.dynamodb_region,
        )
        _create_users_table(dynamodb)
        yield dynamodb


@pytest.fixture
def test_user_data():
    """Create test user data."""
    now = datetime.utcnow().isoformat()
    return {
        'id': 'user-test-001',
        'email': 'test@example.com',
        'hashed_password': hash_password('password123'),
        'created_at': now,
        'updated_at': now,
    }


def test_login_success(client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data):
    """Test successful login with correct credentials."""
    # Create users table
    table_name = f"{settings.dynamodb_table_prefix}users"
    _create_users_table(mock_dynamodb_resource)

    # Get the users table
    users_table = mock_dynamodb_resource.Table(table_name)

    # Add user to DynamoDB
    users_table.put_item(
        Item={
            'userId': test_user_data['id'],
            'email': test_user_data['email'],
            'hashed_password': test_user_data['hashed_password'],
            'created_at': test_user_data['created_at'],
            'updated_at': test_user_data['updated_at'],
        }
    )

    response = client_with_mock_dynamodb.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "data" in response_data
    data = response_data["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "user" in data
    assert data["user"]["user_id"] == test_user_data['id']
    assert data["user"]["email"] == test_user_data['email']
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_incorrect_email(client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data):
    """Test login with non-existent email returns 401."""
    # Create users table
    table_name = f"{settings.dynamodb_table_prefix}users"
    _create_users_table(mock_dynamodb_resource)

    # Get the users table and add test user
    users_table = mock_dynamodb_resource.Table(table_name)
    users_table.put_item(
        Item={
            'userId': test_user_data['id'],
            'email': test_user_data['email'],
            'hashed_password': test_user_data['hashed_password'],
            'created_at': test_user_data['created_at'],
            'updated_at': test_user_data['updated_at'],
        }
    )

    response = client_with_mock_dynamodb.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_login_incorrect_password(client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data):
    """Test login with incorrect password returns 401."""
    # Create users table
    table_name = f"{settings.dynamodb_table_prefix}users"
    _create_users_table(mock_dynamodb_resource)

    # Get the users table and add test user
    users_table = mock_dynamodb_resource.Table(table_name)
    users_table.put_item(
        Item={
            'userId': test_user_data['id'],
            'email': test_user_data['email'],
            'hashed_password': test_user_data['hashed_password'],
            'created_at': test_user_data['created_at'],
            'updated_at': test_user_data['updated_at'],
        }
    )

    response = client_with_mock_dynamodb.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_logout_success(client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data):
    """Test successful logout with valid token."""
    # Create users table
    table_name = f"{settings.dynamodb_table_prefix}users"
    _create_users_table(mock_dynamodb_resource)

    # Get the users table and add test user
    users_table = mock_dynamodb_resource.Table(table_name)
    users_table.put_item(
        Item={
            'userId': test_user_data['id'],
            'email': test_user_data['email'],
            'hashed_password': test_user_data['hashed_password'],
            'created_at': test_user_data['created_at'],
            'updated_at': test_user_data['updated_at'],
        }
    )

    # Create access token
    token = create_access_token(data={"sub": test_user_data['id']})

    response = client_with_mock_dynamodb.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "data" in response_data
    data = response_data["data"]
    assert "message" in data


def test_logout_without_auth(client):
    """Test logout without authentication returns 401."""
    response = client.post("/api/auth/logout")

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


def test_get_me_success(client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data):
    """Test getting current user with valid token."""
    # Create users table
    table_name = f"{settings.dynamodb_table_prefix}users"
    _create_users_table(mock_dynamodb_resource)

    # Get the users table and add test user
    users_table = mock_dynamodb_resource.Table(table_name)
    users_table.put_item(
        Item={
            'userId': test_user_data['id'],
            'email': test_user_data['email'],
            'hashed_password': test_user_data['hashed_password'],
            'created_at': test_user_data['created_at'],
            'updated_at': test_user_data['updated_at'],
        }
    )

    # Create access token
    token = create_access_token(data={"sub": test_user_data['id']})

    response = client_with_mock_dynamodb.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "data" in response_data
    data = response_data["data"]
    assert data["user_id"] == test_user_data['id']
    assert data["email"] == test_user_data['email']
    assert "hashed_password" not in data


def test_get_me_without_auth(client):
    """Test getting current user without authentication returns 401."""
    response = client.get("/api/auth/me")

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


def test_get_me_invalid_token(client):
    """Test getting current user with invalid token returns 401."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"},
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@patch('app.api.routes.auth.AuditService')
def test_login_success_calls_audit_log(
    mock_audit_service_cls, client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data
):
    """Test that successful login calls AuditService().log_user_login()."""
    # Setup: create users table and add test user
    table_name = f"{settings.dynamodb_table_prefix}users"
    _create_users_table(mock_dynamodb_resource)
    users_table = mock_dynamodb_resource.Table(table_name)
    users_table.put_item(
        Item={
            'userId': test_user_data['id'],
            'email': test_user_data['email'],
            'hashed_password': test_user_data['hashed_password'],
            'created_at': test_user_data['created_at'],
            'updated_at': test_user_data['updated_at'],
        }
    )

    # Configure mock
    mock_audit_instance = MagicMock()
    mock_audit_instance.log_user_login = AsyncMock(return_value=None)
    mock_audit_service_cls.return_value = mock_audit_instance

    # Act
    response = client_with_mock_dynamodb.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    # Assert
    assert response.status_code == 200
    mock_audit_instance.log_user_login.assert_called_once_with(
        user_id=test_user_data['id'], dynamodb=mock_dynamodb_resource
    )


@patch('app.api.routes.auth.AuditService')
def test_login_failed_calls_audit_log(
    mock_audit_service_cls, client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data
):
    """Test that failed login calls AuditService().log_user_login_failed() for both user_not_found and invalid_password."""
    # Disable rate limiter for this test (2 login attempts needed)
    from app.api.routes.auth import limiter as auth_limiter
    auth_limiter.enabled = False

    try:
        # Setup: create users table and add test user
        table_name = f"{settings.dynamodb_table_prefix}users"
        _create_users_table(mock_dynamodb_resource)
        users_table = mock_dynamodb_resource.Table(table_name)
        users_table.put_item(
            Item={
                'userId': test_user_data['id'],
                'email': test_user_data['email'],
                'hashed_password': test_user_data['hashed_password'],
                'created_at': test_user_data['created_at'],
                'updated_at': test_user_data['updated_at'],
            }
        )

        # Configure mock
        mock_audit_instance = MagicMock()
        mock_audit_instance.log_user_login_failed = AsyncMock(return_value=None)
        mock_audit_service_cls.return_value = mock_audit_instance

        # Case 1: user_not_found
        response = client_with_mock_dynamodb.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )
        assert response.status_code == 401
        mock_audit_instance.log_user_login_failed.assert_called_once_with(
            email="nonexistent@example.com", reason="user_not_found", dynamodb=mock_dynamodb_resource
        )

        # Reset mock for next case
        mock_audit_instance.log_user_login_failed.reset_mock()

        # Case 2: invalid_password
        response = client_with_mock_dynamodb.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        mock_audit_instance.log_user_login_failed.assert_called_once_with(
            email="test@example.com", reason="invalid_password", dynamodb=mock_dynamodb_resource
        )
    finally:
        # Re-enable rate limiter
        auth_limiter.enabled = True


@patch('app.api.routes.auth.AuditService')
def test_logout_calls_audit_log(
    mock_audit_service_cls, client_with_mock_dynamodb, mock_dynamodb_resource, test_user_data
):
    """Test that logout calls AuditService().log_user_logout()."""
    # Setup: create users table and add test user
    table_name = f"{settings.dynamodb_table_prefix}users"
    _create_users_table(mock_dynamodb_resource)
    users_table = mock_dynamodb_resource.Table(table_name)
    users_table.put_item(
        Item={
            'userId': test_user_data['id'],
            'email': test_user_data['email'],
            'hashed_password': test_user_data['hashed_password'],
            'created_at': test_user_data['created_at'],
            'updated_at': test_user_data['updated_at'],
        }
    )

    # Configure mock
    mock_audit_instance = MagicMock()
    mock_audit_instance.log_user_logout = AsyncMock(return_value=None)
    mock_audit_service_cls.return_value = mock_audit_instance

    # Create access token
    token = create_access_token(data={"sub": test_user_data['id']})

    # Act
    response = client_with_mock_dynamodb.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Assert
    assert response.status_code == 200
    mock_audit_instance.log_user_logout.assert_called_once_with(
        user_id=test_user_data['id'], dynamodb=mock_dynamodb_resource
    )
