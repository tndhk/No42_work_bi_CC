"""Tests for Card models."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.card import Card, CardCreate, CardUpdate


class TestCardCreate:
    """Test CardCreate model."""

    def test_card_create_valid(self):
        """Test creating CardCreate with valid data."""
        card = CardCreate(
            name="Sales Chart",
            code="import pandas as pd\ndf = pd.DataFrame()\nrender(df)"
        )

        assert card.name == "Sales Chart"
        assert card.code == "import pandas as pd\ndf = pd.DataFrame()\nrender(df)"

    def test_card_create_with_description(self):
        """Test CardCreate with description."""
        card = CardCreate(
            name="Sales Chart",
            code="render(pd.DataFrame())",
            description="Monthly sales visualization"
        )

        assert card.description == "Monthly sales visualization"

    def test_card_create_with_dataset_ids(self):
        """Test CardCreate with dataset_ids."""
        card = CardCreate(
            name="Sales Chart",
            code="render(pd.DataFrame())",
            dataset_ids=["dataset-1", "dataset-2"]
        )

        assert card.dataset_ids == ["dataset-1", "dataset-2"]

    def test_card_create_missing_name(self):
        """Test CardCreate validation fails without name."""
        with pytest.raises(ValidationError):
            CardCreate(code="render()")

    def test_card_create_empty_name(self):
        """Test CardCreate validation fails with empty name."""
        with pytest.raises(ValidationError):
            CardCreate(
                name="",
                code="render()"
            )

    def test_card_create_missing_code(self):
        """Test CardCreate validation fails without code."""
        with pytest.raises(ValidationError):
            CardCreate(name="Sales Chart")

    def test_card_create_empty_code(self):
        """Test CardCreate validation fails with empty code."""
        with pytest.raises(ValidationError):
            CardCreate(
                name="Sales Chart",
                code=""
            )

    def test_card_create_optional_description(self):
        """Test CardCreate with optional description."""
        card = CardCreate(
            name="Sales Chart",
            code="render()"
        )

        assert card.description is None


class TestCard:
    """Test Card model."""

    def test_card_valid(self):
        """Test creating Card with valid data."""
        now = datetime.utcnow()
        card = Card(
            id="card-123",
            name="Sales Chart",
            code="import pandas as pd\nrender(pd.DataFrame())",
            created_at=now,
            updated_at=now
        )

        assert card.id == "card-123"
        assert card.name == "Sales Chart"
        assert "import pandas" in card.code

    def test_card_with_dataset_ids(self):
        """Test Card with dataset_ids."""
        now = datetime.utcnow()
        card = Card(
            id="card-123",
            name="Sales Chart",
            code="render()",
            dataset_ids=["dataset-1"],
            created_at=now,
            updated_at=now
        )

        assert card.dataset_ids == ["dataset-1"]

    def test_card_missing_id(self):
        """Test Card validation fails without id."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Card(
                name="Sales Chart",
                code="render()",
                created_at=now,
                updated_at=now
            )

    def test_card_missing_code(self):
        """Test Card validation fails without code."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Card(
                id="card-123",
                name="Sales Chart",
                created_at=now,
                updated_at=now
            )

    def test_card_serialization(self):
        """Test Card serialization to dict."""
        now = datetime.utcnow()
        card = Card(
            id="card-123",
            name="Sales Chart",
            code="render()",
            created_at=now,
            updated_at=now
        )

        card_dict = card.model_dump()
        assert card_dict["id"] == "card-123"
        assert card_dict["name"] == "Sales Chart"
        assert "code" in card_dict


class TestCardUpdate:
    """Test CardUpdate model."""

    def test_card_update_valid(self):
        """Test creating CardUpdate with valid data."""
        update = CardUpdate(
            name="Updated Chart",
            code="render(new_df)"
        )

        assert update.name == "Updated Chart"
        assert update.code == "render(new_df)"

    def test_card_update_with_description(self):
        """Test CardUpdate with description."""
        update = CardUpdate(
            name="Updated Chart",
            description="Updated description"
        )

        assert update.description == "Updated description"

    def test_card_update_optional_fields(self):
        """Test CardUpdate with optional fields."""
        update = CardUpdate()

        assert update.name is None
        assert update.code is None
        assert update.description is None

    def test_card_update_partial(self):
        """Test CardUpdate with partial fields."""
        update = CardUpdate(name="New Name")

        assert update.name == "New Name"
        assert update.code is None

    def test_card_update_empty_name(self):
        """Test CardUpdate validation fails with empty name."""
        with pytest.raises(ValidationError):
            CardUpdate(name="")

    def test_card_update_empty_code(self):
        """Test CardUpdate validation fails with empty code."""
        with pytest.raises(ValidationError):
            CardUpdate(code="")

    def test_card_update_with_dataset_ids(self):
        """Test CardUpdate with dataset_ids."""
        update = CardUpdate(
            dataset_ids=["dataset-1", "dataset-2"]
        )

        assert update.dataset_ids == ["dataset-1", "dataset-2"]


class TestCardExtendedFields:
    """Test Card extended fields for Phase 2."""

    def test_card_with_dataset_id_single(self):
        """Test Card with dataset_id (single string, not list)."""
        now = datetime.utcnow()
        card = Card(
            id="card-123",
            name="Sales Chart",
            code="render()",
            dataset_id="dataset-456",
            created_at=now,
            updated_at=now
        )

        assert card.dataset_id == "dataset-456"

    def test_card_with_params(self):
        """Test Card with params field."""
        now = datetime.utcnow()
        params = {
            "chart_type": "bar",
            "color": "blue",
            "limit": 100
        }

        card = Card(
            id="card-123",
            name="Sales Chart",
            code="render()",
            params=params,
            created_at=now,
            updated_at=now
        )

        assert card.params == params
        assert card.params["chart_type"] == "bar"

    def test_card_with_used_columns(self):
        """Test Card with used_columns field."""
        now = datetime.utcnow()
        used_columns = ["sales", "date", "region"]

        card = Card(
            id="card-123",
            name="Sales Chart",
            code="render()",
            used_columns=used_columns,
            created_at=now,
            updated_at=now
        )

        assert card.used_columns == used_columns
        assert len(card.used_columns) == 3

    def test_card_with_filter_applicable(self):
        """Test Card with filter_applicable field."""
        now = datetime.utcnow()

        card = Card(
            id="card-123",
            name="Sales Chart",
            code="render()",
            filter_applicable=True,
            created_at=now,
            updated_at=now
        )

        assert card.filter_applicable is True

    def test_card_with_owner_id(self):
        """Test Card with owner_id field."""
        now = datetime.utcnow()

        card = Card(
            id="card-123",
            name="Sales Chart",
            code="render()",
            owner_id="user-789",
            created_at=now,
            updated_at=now
        )

        assert card.owner_id == "user-789"

    def test_card_create_with_dataset_id(self):
        """Test CardCreate with dataset_id field."""
        card_create = CardCreate(
            name="Sales Chart",
            code="render()",
            dataset_id="dataset-456"
        )

        assert card_create.dataset_id == "dataset-456"

    def test_card_create_with_params(self):
        """Test CardCreate with params field."""
        params = {"color": "red", "size": "large"}

        card_create = CardCreate(
            name="Sales Chart",
            code="render()",
            params=params
        )

        assert card_create.params == params

    def test_card_update_with_dataset_id(self):
        """Test CardUpdate with dataset_id field."""
        card_update = CardUpdate(
            dataset_id="dataset-789"
        )

        assert card_update.dataset_id == "dataset-789"

    def test_card_update_with_params(self):
        """Test CardUpdate with params field."""
        params = {"theme": "dark"}

        card_update = CardUpdate(
            params=params
        )

        assert card_update.params == params
