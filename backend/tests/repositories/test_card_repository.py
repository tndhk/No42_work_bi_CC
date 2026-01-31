"""Tests for CardRepository."""
import pytest
from datetime import datetime
from typing import Any

from app.core.config import settings


@pytest.mark.asyncio
class TestCardRepository:
    """Test suite for CardRepository."""

    async def test_create_card(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test creating a card with automatic timestamp setting."""
        from app.repositories.card_repository import CardRepository

        tables, dynamodb = dynamodb_tables
        repo = CardRepository()

        card_data = {
            'id': 'card-001',
            'name': 'Test Card',
            'code': 'print("Hello")',
            'description': 'A test card',
            'dataset_ids': ['dataset-001', 'dataset-002'],
            'ownerId': 'owner-123'
        }

        card = await repo.create(card_data, dynamodb)

        assert card.id == 'card-001'
        assert card.name == 'Test Card'
        assert card.code == 'print("Hello")'
        assert card.dataset_ids == ['dataset-001', 'dataset-002']
        assert isinstance(card.created_at, datetime)
        assert isinstance(card.updated_at, datetime)

    async def test_get_by_id_exists(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving card by ID when it exists."""
        from app.repositories.card_repository import CardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['cards']
        now = datetime.now()
        table.put_item(
            Item={
                'cardId': 'card-003',
                'name': 'Existing Card',
                'code': 'def render(): return "<h1>Test</h1>"',
                'description': 'Description',
                'datasetIds': ['dataset-001'],
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = CardRepository()
        card = await repo.get_by_id('card-003', dynamodb)

        assert card is not None
        assert card.id == 'card-003'
        assert card.name == 'Existing Card'
        assert 'render()' in card.code

    async def test_get_by_id_not_found(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving card by ID when it does not exist."""
        from app.repositories.card_repository import CardRepository

        tables, dynamodb = dynamodb_tables
        repo = CardRepository()
        card = await repo.get_by_id('card-nonexistent', dynamodb)

        assert card is None

    async def test_list_by_owner(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test retrieving cards by owner using GSI."""
        from app.repositories.card_repository import CardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['cards']
        now = datetime.now()

        # Create multiple cards for same owner
        for i in range(3):
            table.put_item(
                Item={
                    'cardId': f'card-{i:03d}',
                    'name': f'Card {i}',
                    'code': f'print({i})',
                    'ownerId': 'owner-456',
                    'createdAt': int(now.timestamp()),
                    'updatedAt': int(now.timestamp())
                }
            )

        # Create card for different owner
        table.put_item(
            Item={
                'cardId': 'card-other',
                'name': 'Other Card',
                'code': 'print("other")',
                'ownerId': 'owner-999',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = CardRepository()
        cards = await repo.list_by_owner('owner-456', dynamodb)

        assert len(cards) == 3
        assert all(c.id.startswith('card-') for c in cards)
        # Should not include other owner's cards
        assert not any(c.id == 'card-other' for c in cards)

    async def test_update_card(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test updating card code and metadata."""
        from app.repositories.card_repository import CardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['cards']
        original_time = datetime(2024, 1, 1)
        table.put_item(
            Item={
                'cardId': 'card-update',
                'name': 'Old Name',
                'code': 'old_code',
                'ownerId': 'owner-123',
                'createdAt': int(original_time.timestamp()),
                'updatedAt': int(original_time.timestamp())
            }
        )

        repo = CardRepository()
        update_data = {
            'name': 'New Name',
            'code': 'new_code',
            'dataset_ids': ['dataset-new']
        }
        updated = await repo.update('card-update', update_data, dynamodb)

        assert updated is not None
        assert updated.name == 'New Name'
        assert updated.code == 'new_code'
        assert updated.dataset_ids == ['dataset-new']
        assert updated.updated_at.timestamp() > original_time.timestamp()

    async def test_delete_card(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test deleting a card."""
        from app.repositories.card_repository import CardRepository

        # Setup
        tables, dynamodb = dynamodb_tables
        table = tables['cards']
        now = datetime.now()
        table.put_item(
            Item={
                'cardId': 'card-delete',
                'name': 'To Delete',
                'code': 'print("delete")',
                'ownerId': 'owner-123',
                'createdAt': int(now.timestamp()),
                'updatedAt': int(now.timestamp())
            }
        )

        repo = CardRepository()
        await repo.delete('card-delete', dynamodb)

        # Verify deletion
        response = table.get_item(Key={'cardId': 'card-delete'})
        assert 'Item' not in response

    async def test_timestamps(self, dynamodb_tables: tuple[dict[str, Any], Any]) -> None:
        """Test that created_at and updated_at are properly managed."""
        from app.repositories.card_repository import CardRepository

        tables, dynamodb = dynamodb_tables
        repo = CardRepository()

        card_data = {
            'id': 'card-timestamps',
            'name': 'Test Card',
            'code': 'test_code',
            'ownerId': 'owner-123'
        }

        created = await repo.create(card_data, dynamodb)
        assert isinstance(created.created_at, datetime)
        assert isinstance(created.updated_at, datetime)
        assert created.created_at <= created.updated_at

        # Store original created_at timestamp (in seconds since DynamoDB stores as integer)
        created_at_timestamp = int(created.created_at.timestamp())

        # Update and verify updated_at changes
        import time
        time.sleep(1.0)  # Sleep 1 second to ensure timestamp changes
        updated = await repo.update('card-timestamps', {'name': 'Updated Name'}, dynamodb)
        assert int(updated.created_at.timestamp()) == created_at_timestamp
        assert updated.updated_at > created.updated_at
