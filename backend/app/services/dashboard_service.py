"""Dashboard service for analyzing dashboard dependencies."""
from typing import Any
from collections import defaultdict
import logging

from app.models.dashboard import Dashboard
from app.models.card import Card
from app.models.dataset import Dataset
from app.repositories.card_repository import CardRepository
from app.repositories.dataset_repository import DatasetRepository

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard-related operations."""

    def __init__(self) -> None:
        """Initialize DashboardService."""
        self.card_repo = CardRepository()
        self.dataset_repo = DatasetRepository()

    async def get_referenced_datasets(
        self,
        dashboard: Dashboard,
        dynamodb: Any
    ) -> list[dict[str, Any]]:
        """Get datasets referenced by dashboard cards.

        Args:
            dashboard: Dashboard instance
            dynamodb: DynamoDB resource

        Returns:
            List of dictionaries with dataset information:
            [{
                'dataset_id': str,
                'name': str,
                'row_count': int,
                'used_by_cards': [card_id1, card_id2]
            }]

        Raises:
            Exception: If database operations fail
        """
        try:
            if not dashboard.layout:
                logger.debug(
                    f"Dashboard {dashboard.id} has no layout, returning empty"
                )
                return []

            card_ids = self._extract_card_ids(dashboard)

            if not card_ids:
                return []

            cards = await self._fetch_cards(card_ids, dynamodb)

            if not cards:
                logger.warning(
                    f"No valid cards found for dashboard {dashboard.id}"
                )
                return []

            dataset_card_map = self._build_dataset_card_map(cards)

            if not dataset_card_map:
                logger.warning(
                    f"No datasets referenced in dashboard {dashboard.id}"
                )
                return []

            result = await self._fetch_datasets_with_usage(
                dataset_card_map, dynamodb
            )

            logger.info(
                f"Found {len(result)} datasets for dashboard {dashboard.id}"
            )

            return result
        except Exception as e:
            logger.error(
                f"Failed to get referenced datasets for "
                f"dashboard {dashboard.id}: {e}"
            )
            raise

    def _extract_card_ids(self, dashboard: Dashboard) -> list[str]:
        """Extract card IDs from dashboard layout.

        Args:
            dashboard: Dashboard instance

        Returns:
            List of card IDs
        """
        cards = dashboard.layout.cards if dashboard.layout else []
        return [item.card_id for item in cards]

    async def _fetch_cards(
        self, card_ids: list[str], dynamodb: Any
    ) -> list[Card]:
        """Fetch cards from database, skipping missing ones.

        Args:
            card_ids: List of card IDs to fetch
            dynamodb: DynamoDB resource

        Returns:
            List of Card instances
        """
        cards = []
        for card_id in card_ids:
            card = await self.card_repo.get_by_id(card_id, dynamodb)
            if card:
                cards.append(card)
            else:
                logger.warning(f"Card {card_id} not found, skipping")

        return cards

    def _build_dataset_card_map(
        self, cards: list[Card]
    ) -> dict[str, list[str]]:
        """Build mapping of dataset IDs to card IDs.

        Args:
            cards: List of Card instances

        Returns:
            Dictionary mapping dataset_id to list of card_ids
        """
        dataset_card_map: dict[str, list[str]] = defaultdict(list)
        for card in cards:
            if card.dataset_id:
                dataset_card_map[card.dataset_id].append(card.id)

        return dict(dataset_card_map)

    async def _fetch_datasets_with_usage(
        self,
        dataset_card_map: dict[str, list[str]],
        dynamodb: Any
    ) -> list[dict[str, Any]]:
        """Fetch datasets and include usage information.

        Args:
            dataset_card_map: Mapping of dataset_id to card_ids
            dynamodb: DynamoDB resource

        Returns:
            List of dataset information dictionaries
        """
        result = []
        for dataset_id, card_ids_using in dataset_card_map.items():
            dataset = await self.dataset_repo.get_by_id(dataset_id, dynamodb)
            if dataset:
                result.append(
                    self._create_dataset_info(dataset, card_ids_using)
                )
            else:
                logger.warning(f"Dataset {dataset_id} not found, skipping")

        return result

    def _create_dataset_info(
        self, dataset: Dataset, card_ids: list[str]
    ) -> dict[str, Any]:
        """Create dataset information dictionary.

        Args:
            dataset: Dataset instance
            card_ids: List of card IDs using this dataset

        Returns:
            Dictionary with dataset information
        """
        return {
            'dataset_id': dataset.id,
            'name': dataset.name,
            'row_count': dataset.row_count,
            'used_by_cards': card_ids
        }
