"""Tests for AuditLogRepository."""
import pytest
from datetime import datetime, timezone, timedelta
from typing import Any

from app.models.audit_log import AuditLog, EventType
from app.repositories.audit_log_repository import AuditLogRepository


@pytest.mark.asyncio
class TestAuditLogRepository:
    """Tests for AuditLogRepository."""

    async def _create_sample_log(
        self, repo: AuditLogRepository, dynamodb: Any,
        log_id: str = "log_test001",
        timestamp: datetime = None,
        event_type: EventType = EventType.USER_LOGIN,
        user_id: str = "user-001",
        target_type: str = "user",
        target_id: str = "user-001",
        details: dict = None,
        request_id: str = None,
    ) -> AuditLog:
        if timestamp is None:
            timestamp = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        data = {
            "log_id": log_id,
            "timestamp": timestamp,
            "event_type": event_type.value,
            "user_id": user_id,
            "target_type": target_type,
            "target_id": target_id,
            "details": details or {},
            "request_id": request_id,
        }
        return await repo.create(data, dynamodb)

    async def test_create(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test creating an audit log entry."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        ts = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        result = await self._create_sample_log(
            repo, dynamodb,
            log_id="log_create001",
            timestamp=ts,
            event_type=EventType.USER_LOGIN,
            user_id="user-001",
            target_type="user",
            target_id="user-001",
            details={"ip": "127.0.0.1"},
            request_id="req-001",
        )
        assert result.log_id == "log_create001"
        assert result.event_type == EventType.USER_LOGIN
        assert result.user_id == "user-001"
        assert result.details == {"ip": "127.0.0.1"}
        assert result.request_id == "req-001"

    async def test_list_all(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test listing all audit logs."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        for i in range(3):
            await self._create_sample_log(
                repo, dynamodb,
                log_id=f"log_all{i:03d}",
                timestamp=datetime(2026, 2, 4, 10+i, 0, 0, tzinfo=timezone.utc),
                event_type=EventType.USER_LOGIN,
                user_id=f"user-{i}",
                target_id=f"user-{i}",
            )
        results = await repo.list_all(dynamodb)
        assert len(results) == 3

    async def test_list_by_user(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test listing logs by user ID using GSI."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        # Create logs for different users
        for i in range(3):
            await self._create_sample_log(
                repo, dynamodb,
                log_id=f"log_usr{i:03d}",
                timestamp=datetime(2026, 2, 4, 10+i, 0, 0, tzinfo=timezone.utc),
                user_id="user-target",
                target_id=f"target-{i}",
            )
        await self._create_sample_log(
            repo, dynamodb,
            log_id="log_usr_other",
            timestamp=datetime(2026, 2, 4, 13, 0, 0, tzinfo=timezone.utc),
            user_id="user-other",
            target_id="target-other",
        )
        results = await repo.list_by_user("user-target", dynamodb)
        assert len(results) == 3
        assert all(r.user_id == "user-target" for r in results)

    async def test_list_by_target(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test listing logs by target ID using GSI."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        for i in range(2):
            await self._create_sample_log(
                repo, dynamodb,
                log_id=f"log_tgt{i:03d}",
                timestamp=datetime(2026, 2, 4, 10+i, 0, 0, tzinfo=timezone.utc),
                target_id="ds-001",
                user_id=f"user-{i}",
            )
        await self._create_sample_log(
            repo, dynamodb,
            log_id="log_tgt_other",
            timestamp=datetime(2026, 2, 4, 12, 0, 0, tzinfo=timezone.utc),
            target_id="ds-002",
            user_id="user-2",
        )
        results = await repo.list_by_target("ds-001", dynamodb)
        assert len(results) == 2
        assert all(r.target_id == "ds-001" for r in results)

    async def test_list_all_filter_by_event_type(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test filtering by event_type."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        await self._create_sample_log(
            repo, dynamodb,
            log_id="log_evt001",
            event_type=EventType.USER_LOGIN,
        )
        await self._create_sample_log(
            repo, dynamodb,
            log_id="log_evt002",
            timestamp=datetime(2026, 2, 4, 11, 0, 0, tzinfo=timezone.utc),
            event_type=EventType.DATASET_CREATED,
            target_type="dataset",
            target_id="ds-001",
        )
        results = await repo.list_all(dynamodb, event_type=EventType.DATASET_CREATED)
        assert len(results) == 1
        assert results[0].event_type == EventType.DATASET_CREATED

    async def test_list_all_filter_by_time_range(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test filtering by time range."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        base = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(5):
            await self._create_sample_log(
                repo, dynamodb,
                log_id=f"log_time{i:03d}",
                timestamp=base + timedelta(hours=i),
            )
        start = base + timedelta(hours=1)
        end = base + timedelta(hours=3)
        results = await repo.list_all(dynamodb, start_date=start, end_date=end)
        assert len(results) == 3  # hours 1, 2, 3

    async def test_list_ordering_descending(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test that results are ordered newest first."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        base = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(3):
            await self._create_sample_log(
                repo, dynamodb,
                log_id=f"log_ord{i:03d}",
                timestamp=base + timedelta(hours=i),
                user_id="user-order",
                target_id="tgt-order",
            )
        # list_by_user should be newest first
        results = await repo.list_by_user("user-order", dynamodb)
        assert len(results) == 3
        assert results[0].timestamp > results[1].timestamp
        assert results[1].timestamp > results[2].timestamp
        # list_by_target should also be newest first
        results2 = await repo.list_by_target("tgt-order", dynamodb)
        assert results2[0].timestamp > results2[1].timestamp

    async def test_list_empty(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test listing with no results."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        results = await repo.list_all(dynamodb)
        assert results == []
        results2 = await repo.list_by_user("nonexistent", dynamodb)
        assert results2 == []
        results3 = await repo.list_by_target("nonexistent", dynamodb)
        assert results3 == []

    async def test_list_all_combined_filters(self, dynamodb_tables: tuple[dict[str, Any], Any]):
        """Test combining event_type and time range filters."""
        tables, dynamodb = dynamodb_tables
        repo = AuditLogRepository()
        base = datetime(2026, 2, 4, 10, 0, 0, tzinfo=timezone.utc)
        await self._create_sample_log(
            repo, dynamodb,
            log_id="log_comb001",
            timestamp=base,
            event_type=EventType.USER_LOGIN,
        )
        await self._create_sample_log(
            repo, dynamodb,
            log_id="log_comb002",
            timestamp=base + timedelta(hours=1),
            event_type=EventType.DATASET_CREATED,
            target_type="dataset",
            target_id="ds-001",
        )
        await self._create_sample_log(
            repo, dynamodb,
            log_id="log_comb003",
            timestamp=base + timedelta(hours=2),
            event_type=EventType.USER_LOGIN,
        )
        # Filter: USER_LOGIN + time range [base, base+1h]
        results = await repo.list_all(
            dynamodb,
            event_type=EventType.USER_LOGIN,
            start_date=base,
            end_date=base + timedelta(hours=1),
        )
        assert len(results) == 1
        assert results[0].log_id == "log_comb001"
