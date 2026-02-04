"""Tests for Dashboard Service."""
import pytest
from datetime import datetime
from decimal import Decimal

from app.services.dashboard_service import DashboardService
from app.models.dashboard import Dashboard, LayoutItem
from app.core.config import settings


@pytest.fixture
def setup_test_data(dynamodb_tables):
    """Setup test data in DynamoDB tables."""
    tables, dynamodb = dynamodb_tables

    # Create datasets
    datasets_table = tables['datasets']
    dataset1_id = 'dataset-001'
    dataset2_id = 'dataset-002'
    dataset3_id = 'dataset-003'

    datasets_table.put_item(Item={
        'datasetId': dataset1_id,
        'name': 'Sales Data',
        'description': 'Sales dataset',
        'sourceType': 'csv',
        'rowCount': Decimal('1000'),
        'schema': [
            {'name': 'id', 'dataType': 'int64', 'nullable': False},
            {'name': 'amount', 'dataType': 'float64', 'nullable': False}
        ],
        'ownerId': 'user-001',
        'columnCount': Decimal('2'),
        'createdAt': Decimal(str(datetime.now().timestamp())),
        'updatedAt': Decimal(str(datetime.now().timestamp()))
    })

    datasets_table.put_item(Item={
        'datasetId': dataset2_id,
        'name': 'Customer Data',
        'description': 'Customer dataset',
        'sourceType': 'csv',
        'rowCount': Decimal('500'),
        'schema': [
            {'name': 'id', 'dataType': 'int64', 'nullable': False},
            {'name': 'name', 'dataType': 'string', 'nullable': False}
        ],
        'ownerId': 'user-001',
        'columnCount': Decimal('2'),
        'createdAt': Decimal(str(datetime.now().timestamp())),
        'updatedAt': Decimal(str(datetime.now().timestamp()))
    })

    datasets_table.put_item(Item={
        'datasetId': dataset3_id,
        'name': 'Product Data',
        'description': 'Product dataset',
        'sourceType': 'csv',
        'rowCount': Decimal('300'),
        'schema': [
            {'name': 'id', 'dataType': 'int64', 'nullable': False},
            {'name': 'price', 'dataType': 'float64', 'nullable': False}
        ],
        'ownerId': 'user-001',
        'columnCount': Decimal('2'),
        'createdAt': Decimal(str(datetime.now().timestamp())),
        'updatedAt': Decimal(str(datetime.now().timestamp()))
    })

    # Create cards
    cards_table = tables['cards']
    card1_id = 'card-001'
    card2_id = 'card-002'
    card3_id = 'card-003'
    card4_id = 'card-004'

    cards_table.put_item(Item={
        'cardId': card1_id,
        'name': 'Sales Chart',
        'code': 'SELECT * FROM sales',
        'datasetId': dataset1_id,
        'ownerId': 'user-001',
        'createdAt': Decimal(str(datetime.now().timestamp())),
        'updatedAt': Decimal(str(datetime.now().timestamp()))
    })

    cards_table.put_item(Item={
        'cardId': card2_id,
        'name': 'Customer Chart',
        'code': 'SELECT * FROM customers',
        'datasetId': dataset2_id,
        'ownerId': 'user-001',
        'createdAt': Decimal(str(datetime.now().timestamp())),
        'updatedAt': Decimal(str(datetime.now().timestamp()))
    })

    cards_table.put_item(Item={
        'cardId': card3_id,
        'name': 'Combined Chart',
        'code': 'SELECT * FROM sales',
        'datasetId': dataset1_id,  # Same as card1
        'ownerId': 'user-001',
        'createdAt': Decimal(str(datetime.now().timestamp())),
        'updatedAt': Decimal(str(datetime.now().timestamp()))
    })

    cards_table.put_item(Item={
        'cardId': card4_id,
        'name': 'Product Chart',
        'code': 'SELECT * FROM products',
        'datasetId': dataset3_id,
        'ownerId': 'user-001',
        'createdAt': Decimal(str(datetime.now().timestamp())),
        'updatedAt': Decimal(str(datetime.now().timestamp()))
    })

    return {
        'dynamodb': dynamodb,
        'datasets': {
            'dataset1': dataset1_id,
            'dataset2': dataset2_id,
            'dataset3': dataset3_id
        },
        'cards': {
            'card1': card1_id,
            'card2': card2_id,
            'card3': card3_id,
            'card4': card4_id
        }
    }


class TestDashboardService:
    """Test DashboardService class."""

    @pytest.mark.asyncio
    async def test_get_referenced_datasets_multiple_cards_same_dataset(
        self, setup_test_data
    ):
        """Test when multiple cards reference the same dataset."""
        data = setup_test_data
        dynamodb = data['dynamodb']
        card1_id = data['cards']['card1']
        card3_id = data['cards']['card3']

        # Create dashboard with card1 and card3 (both use dataset1)
        dashboard = Dashboard(
            id='dashboard-001',
            name='Test Dashboard',
            layout=[
                LayoutItem(card_id=card1_id, x=0, y=0, w=6, h=4),
                LayoutItem(card_id=card3_id, x=6, y=0, w=6, h=4)
            ],
            owner_id='user-001',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        service = DashboardService()
        result = await service.get_referenced_datasets(dashboard, dynamodb)

        # Should return only one dataset (deduplicated)
        assert len(result) == 1
        assert result[0]['dataset_id'] == data['datasets']['dataset1']
        assert result[0]['name'] == 'Sales Data'
        assert result[0]['row_count'] == 1000
        assert set(result[0]['used_by_cards']) == {card1_id, card3_id}

    @pytest.mark.asyncio
    async def test_get_referenced_datasets_different_datasets(
        self, setup_test_data
    ):
        """Test with cards referencing different datasets."""
        data = setup_test_data
        dynamodb = data['dynamodb']
        card1_id = data['cards']['card1']
        card2_id = data['cards']['card2']
        card4_id = data['cards']['card4']

        dashboard = Dashboard(
            id='dashboard-002',
            name='Multi Dataset Dashboard',
            layout=[
                LayoutItem(card_id=card1_id, x=0, y=0, w=4, h=4),
                LayoutItem(card_id=card2_id, x=4, y=0, w=4, h=4),
                LayoutItem(card_id=card4_id, x=8, y=0, w=4, h=4)
            ],
            owner_id='user-001',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        service = DashboardService()
        result = await service.get_referenced_datasets(dashboard, dynamodb)

        # Should return 3 datasets
        assert len(result) == 3

        dataset_ids = {r['dataset_id'] for r in result}
        assert dataset_ids == {
            data['datasets']['dataset1'],
            data['datasets']['dataset2'],
            data['datasets']['dataset3']
        }

        # Check used_by_cards
        for item in result:
            if item['dataset_id'] == data['datasets']['dataset1']:
                assert item['used_by_cards'] == [card1_id]
            elif item['dataset_id'] == data['datasets']['dataset2']:
                assert item['used_by_cards'] == [card2_id]
            elif item['dataset_id'] == data['datasets']['dataset3']:
                assert item['used_by_cards'] == [card4_id]

    @pytest.mark.asyncio
    async def test_get_referenced_datasets_layout_none(self, setup_test_data):
        """Test when layout is None."""
        data = setup_test_data
        dynamodb = data['dynamodb']

        dashboard = Dashboard(
            id='dashboard-003',
            name='Empty Dashboard',
            layout=None,
            owner_id='user-001',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        service = DashboardService()
        result = await service.get_referenced_datasets(dashboard, dynamodb)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_referenced_datasets_layout_empty(self, setup_test_data):
        """Test when layout is empty list."""
        data = setup_test_data
        dynamodb = data['dynamodb']

        dashboard = Dashboard(
            id='dashboard-004',
            name='Empty Layout Dashboard',
            layout=[],
            owner_id='user-001',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        service = DashboardService()
        result = await service.get_referenced_datasets(dashboard, dynamodb)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_referenced_datasets_card_not_found(self, setup_test_data):
        """Test when a card does not exist."""
        data = setup_test_data
        dynamodb = data['dynamodb']
        card1_id = data['cards']['card1']

        dashboard = Dashboard(
            id='dashboard-005',
            name='Dashboard with Missing Card',
            layout=[
                LayoutItem(card_id=card1_id, x=0, y=0, w=6, h=4),
                LayoutItem(card_id='non-existent-card', x=6, y=0, w=6, h=4)
            ],
            owner_id='user-001',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        service = DashboardService()
        result = await service.get_referenced_datasets(dashboard, dynamodb)

        # Should skip non-existent card and return dataset1
        assert len(result) == 1
        assert result[0]['dataset_id'] == data['datasets']['dataset1']
        assert result[0]['used_by_cards'] == [card1_id]

    @pytest.mark.asyncio
    async def test_get_referenced_datasets_dataset_not_found(
        self, setup_test_data
    ):
        """Test when a dataset referenced by card does not exist."""
        data = setup_test_data
        dynamodb = data['dynamodb']
        card1_id = data['cards']['card1']

        # Create a card with non-existent dataset
        cards_table = data['dynamodb'].Table(f"{settings.dynamodb_table_prefix}cards")
        orphan_card_id = 'card-orphan'
        cards_table.put_item(Item={
            'cardId': orphan_card_id,
            'name': 'Orphan Card',
            'code': 'SELECT * FROM nowhere',
            'datasetId': 'non-existent-dataset',
            'ownerId': 'user-001',
            'createdAt': Decimal(str(datetime.now().timestamp())),
            'updatedAt': Decimal(str(datetime.now().timestamp()))
        })

        dashboard = Dashboard(
            id='dashboard-006',
            name='Dashboard with Orphan Card',
            layout=[
                LayoutItem(card_id=card1_id, x=0, y=0, w=6, h=4),
                LayoutItem(card_id=orphan_card_id, x=6, y=0, w=6, h=4)
            ],
            owner_id='user-001',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        service = DashboardService()
        result = await service.get_referenced_datasets(dashboard, dynamodb)

        # Should skip orphan card and return only dataset1
        assert len(result) == 1
        assert result[0]['dataset_id'] == data['datasets']['dataset1']

    @pytest.mark.asyncio
    async def test_get_referenced_datasets_used_by_cards_accuracy(
        self, setup_test_data
    ):
        """Test accuracy of used_by_cards field."""
        data = setup_test_data
        dynamodb = data['dynamodb']
        card1_id = data['cards']['card1']
        card2_id = data['cards']['card2']
        card3_id = data['cards']['card3']

        dashboard = Dashboard(
            id='dashboard-007',
            name='Used By Cards Test',
            layout=[
                LayoutItem(card_id=card1_id, x=0, y=0, w=4, h=4),
                LayoutItem(card_id=card2_id, x=4, y=0, w=4, h=4),
                LayoutItem(card_id=card3_id, x=8, y=0, w=4, h=4)
            ],
            owner_id='user-001',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        service = DashboardService()
        result = await service.get_referenced_datasets(dashboard, dynamodb)

        # Find dataset1 (used by card1 and card3)
        dataset1_result = next(
            r for r in result
            if r['dataset_id'] == data['datasets']['dataset1']
        )

        assert set(dataset1_result['used_by_cards']) == {card1_id, card3_id}
        assert len(dataset1_result['used_by_cards']) == 2

        # Find dataset2 (used by card2 only)
        dataset2_result = next(
            r for r in result
            if r['dataset_id'] == data['datasets']['dataset2']
        )

        assert dataset2_result['used_by_cards'] == [card2_id]
        assert len(dataset2_result['used_by_cards']) == 1
