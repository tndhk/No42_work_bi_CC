"""Tests for Dashboard models."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.models.dashboard import Dashboard, DashboardCreate, DashboardUpdate, LayoutItem


class TestLayoutItem:
    """Test LayoutItem model."""

    def test_layout_item_valid(self):
        """Test creating LayoutItem with valid data."""
        item = LayoutItem(
            card_id="card-123",
            x=0,
            y=0,
            w=4,
            h=3
        )

        assert item.card_id == "card-123"
        assert item.x == 0
        assert item.y == 0
        assert item.w == 4
        assert item.h == 3

    def test_layout_item_missing_card_id(self):
        """Test LayoutItem validation fails without card_id."""
        with pytest.raises(ValidationError):
            LayoutItem(x=0, y=0, w=4, h=3)

    def test_layout_item_missing_position(self):
        """Test LayoutItem validation fails without x."""
        with pytest.raises(ValidationError):
            LayoutItem(card_id="card-123", y=0, w=4, h=3)

    def test_layout_item_negative_dimensions(self):
        """Test LayoutItem validation fails with negative dimensions."""
        with pytest.raises(ValidationError):
            LayoutItem(
                card_id="card-123",
                x=0,
                y=0,
                w=-1,
                h=3
            )


class TestDashboardCreate:
    """Test DashboardCreate model."""

    def test_dashboard_create_valid(self):
        """Test creating DashboardCreate with valid data."""
        dashboard = DashboardCreate(
            name="Sales Dashboard",
            description="Monthly sales overview"
        )

        assert dashboard.name == "Sales Dashboard"
        assert dashboard.description == "Monthly sales overview"

    def test_dashboard_create_with_layout(self):
        """Test DashboardCreate with layout."""
        layout = [
            LayoutItem(card_id="card-1", x=0, y=0, w=4, h=3),
            LayoutItem(card_id="card-2", x=4, y=0, w=4, h=3)
        ]
        dashboard = DashboardCreate(
            name="Sales Dashboard",
            description="Overview",
            layout=layout
        )

        assert len(dashboard.layout) == 2
        assert dashboard.layout[0].card_id == "card-1"

    def test_dashboard_create_missing_name(self):
        """Test DashboardCreate validation fails without name."""
        with pytest.raises(ValidationError):
            DashboardCreate(description="Test")

    def test_dashboard_create_empty_name(self):
        """Test DashboardCreate validation fails with empty name."""
        with pytest.raises(ValidationError):
            DashboardCreate(
                name="",
                description="Test"
            )

    def test_dashboard_create_optional_description(self):
        """Test DashboardCreate with optional description."""
        dashboard = DashboardCreate(name="Sales Dashboard")

        assert dashboard.description is None


class TestDashboard:
    """Test Dashboard model."""

    def test_dashboard_valid(self):
        """Test creating Dashboard with valid data."""
        now = datetime.utcnow()
        dashboard = Dashboard(
            id="dashboard-123",
            name="Sales Dashboard",
            created_at=now,
            updated_at=now
        )

        assert dashboard.id == "dashboard-123"
        assert dashboard.name == "Sales Dashboard"

    def test_dashboard_with_layout(self):
        """Test Dashboard with layout."""
        now = datetime.utcnow()
        layout = [LayoutItem(card_id="card-1", x=0, y=0, w=4, h=3)]
        dashboard = Dashboard(
            id="dashboard-123",
            name="Sales Dashboard",
            layout=layout,
            created_at=now,
            updated_at=now
        )

        assert len(dashboard.layout) == 1
        assert dashboard.layout[0].card_id == "card-1"

    def test_dashboard_missing_id(self):
        """Test Dashboard validation fails without id."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Dashboard(
                name="Sales Dashboard",
                created_at=now,
                updated_at=now
            )

    def test_dashboard_missing_name(self):
        """Test Dashboard validation fails without name."""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            Dashboard(
                id="dashboard-123",
                created_at=now,
                updated_at=now
            )

    def test_dashboard_serialization(self):
        """Test Dashboard serialization to dict."""
        now = datetime.utcnow()
        dashboard = Dashboard(
            id="dashboard-123",
            name="Sales Dashboard",
            created_at=now,
            updated_at=now
        )

        dashboard_dict = dashboard.model_dump()
        assert dashboard_dict["id"] == "dashboard-123"
        assert dashboard_dict["name"] == "Sales Dashboard"


class TestDashboardUpdate:
    """Test DashboardUpdate model."""

    def test_dashboard_update_valid(self):
        """Test creating DashboardUpdate with valid data."""
        update = DashboardUpdate(
            name="Updated Dashboard",
            description="Updated description"
        )

        assert update.name == "Updated Dashboard"
        assert update.description == "Updated description"

    def test_dashboard_update_with_layout(self):
        """Test DashboardUpdate with layout."""
        layout = [LayoutItem(card_id="card-1", x=0, y=0, w=4, h=3)]
        update = DashboardUpdate(
            name="Updated Dashboard",
            layout=layout
        )

        assert len(update.layout) == 1

    def test_dashboard_update_optional_fields(self):
        """Test DashboardUpdate with optional fields."""
        update = DashboardUpdate()

        assert update.name is None
        assert update.description is None
        assert update.layout is None

    def test_dashboard_update_partial(self):
        """Test DashboardUpdate with partial fields."""
        update = DashboardUpdate(name="New Name")

        assert update.name == "New Name"
        assert update.description is None

    def test_dashboard_update_empty_name(self):
        """Test DashboardUpdate validation fails with empty name."""
        with pytest.raises(ValidationError):
            DashboardUpdate(name="")


class TestFilterDefinition:
    """Test FilterDefinition model for Phase 2."""

    def test_filter_definition_valid(self):
        """Test creating FilterDefinition with valid data."""
        from app.models.dashboard import FilterDefinition

        filter_def = FilterDefinition(
            id="filter-1",
            type="select",
            column="region",
            label="Region Filter"
        )

        assert filter_def.id == "filter-1"
        assert filter_def.type == "select"
        assert filter_def.column == "region"
        assert filter_def.label == "Region Filter"

    def test_filter_definition_with_multi_select(self):
        """Test FilterDefinition with multi_select field."""
        from app.models.dashboard import FilterDefinition

        filter_def = FilterDefinition(
            id="filter-2",
            type="select",
            column="category",
            label="Category Filter",
            multi_select=True
        )

        assert filter_def.multi_select is True

    def test_filter_definition_with_options(self):
        """Test FilterDefinition with options field."""
        from app.models.dashboard import FilterDefinition

        filter_def = FilterDefinition(
            id="filter-3",
            type="category",
            column="region",
            label="Region",
            options=["East", "West", "North"]
        )

        assert filter_def.options == ["East", "West", "North"]

    def test_filter_definition_options_default_none(self):
        """Test FilterDefinition options defaults to None."""
        from app.models.dashboard import FilterDefinition

        filter_def = FilterDefinition(
            id="filter-4",
            type="category",
            column="region",
            label="Region"
        )

        assert filter_def.options is None

    def test_filter_definition_missing_required_fields(self):
        """Test FilterDefinition validation fails without required fields."""
        from app.models.dashboard import FilterDefinition

        with pytest.raises(ValidationError):
            FilterDefinition(
                type="select",
                column="region",
                label="Region Filter"
            )


class TestDashboardExtendedFields:
    """Test Dashboard extended fields for Phase 2."""

    def test_dashboard_with_owner_id(self):
        """Test Dashboard with owner_id field."""
        now = datetime.utcnow()

        dashboard = Dashboard(
            id="dashboard-123",
            name="Sales Dashboard",
            owner_id="user-456",
            created_at=now,
            updated_at=now
        )

        assert dashboard.owner_id == "user-456"

    def test_dashboard_with_filters(self):
        """Test Dashboard with filters field."""
        from app.models.dashboard import FilterDefinition

        now = datetime.utcnow()
        filters = [
            FilterDefinition(
                id="filter-1",
                type="select",
                column="region",
                label="Region"
            ),
            FilterDefinition(
                id="filter-2",
                type="date_range",
                column="date",
                label="Date Range"
            )
        ]

        dashboard = Dashboard(
            id="dashboard-123",
            name="Sales Dashboard",
            filters=filters,
            created_at=now,
            updated_at=now
        )

        assert len(dashboard.filters) == 2
        assert dashboard.filters[0].column == "region"
        assert dashboard.filters[1].type == "date_range"

    def test_dashboard_with_default_filter_view_id(self):
        """Test Dashboard with default_filter_view_id field."""
        now = datetime.utcnow()

        dashboard = Dashboard(
            id="dashboard-123",
            name="Sales Dashboard",
            default_filter_view_id="view-789",
            created_at=now,
            updated_at=now
        )

        assert dashboard.default_filter_view_id == "view-789"

    def test_dashboard_create_with_filters(self):
        """Test DashboardCreate with filters field."""
        from app.models.dashboard import FilterDefinition

        filters = [
            FilterDefinition(
                id="filter-1",
                type="select",
                column="status",
                label="Status"
            )
        ]

        dashboard_create = DashboardCreate(
            name="Sales Dashboard",
            filters=filters
        )

        assert len(dashboard_create.filters) == 1
        assert dashboard_create.filters[0].column == "status"

    def test_dashboard_update_with_filters(self):
        """Test DashboardUpdate with filters field."""
        from app.models.dashboard import FilterDefinition

        filters = [
            FilterDefinition(
                id="filter-1",
                type="select",
                column="category",
                label="Category"
            )
        ]

        dashboard_update = DashboardUpdate(
            filters=filters
        )

        assert len(dashboard_update.filters) == 1
