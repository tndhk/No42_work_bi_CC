"""Background scheduler for periodic transform execution."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import aioboto3
from croniter import croniter

from app.core.config import settings
from app.repositories.transform_execution_repository import TransformExecutionRepository
from app.repositories.transform_repository import TransformRepository
from app.services.transform_execution_service import TransformExecutionService

logger = logging.getLogger(__name__)


class TransformSchedulerService:
    """Asyncio-based background scheduler for transforms."""

    def __init__(self) -> None:
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the scheduler background task."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Transform scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler background task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Transform scheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_execute()
            except Exception:
                logger.exception("Scheduler tick error")
            await asyncio.sleep(settings.scheduler_interval_seconds)

    async def _check_and_execute(self) -> None:
        """Check scheduled transforms and execute if due."""
        session = aioboto3.Session()
        async with session.resource(
            'dynamodb',
            region_name=settings.dynamodb_region,
            endpoint_url=settings.dynamodb_endpoint,
        ) as dynamodb:
            async with session.client(
                's3',
                region_name=settings.s3_region,
                endpoint_url=settings.s3_endpoint if settings.s3_endpoint else None,
                aws_access_key_id=settings.s3_access_key if settings.s3_access_key and settings.s3_secret_key else None,
                aws_secret_access_key=settings.s3_secret_key if settings.s3_access_key and settings.s3_secret_key else None,
            ) as s3:
                await self._execute_due_transforms(dynamodb, s3)

    async def _execute_due_transforms(self, dynamodb: Any, s3: Any) -> None:
        """Find and execute transforms that are due."""
        transform_repo = TransformRepository()
        exec_repo = TransformExecutionRepository()
        exec_service = TransformExecutionService()

        table = await transform_repo._execute_db_operation(
            dynamodb.Table(transform_repo.table_name)
        )
        response = await transform_repo._execute_db_operation(
            table.scan(
                FilterExpression='scheduleEnabled = :enabled',
                ExpressionAttributeValues={':enabled': True},
            )
        )

        now = datetime.now(timezone.utc)
        items = response.get('Items', [])

        for item in items:
            transform = transform_repo.model(
                **transform_repo._from_dynamodb_item(item)
            )

            if not transform.schedule_cron:
                continue

            if not self._is_due(transform.schedule_cron, now):
                continue

            if await exec_repo.has_running_execution(transform.id, dynamodb):
                logger.info("Transform %s already running, skipping", transform.id)
                continue

            logger.info("Executing scheduled transform: %s", transform.id)
            try:
                await exec_service.execute(
                    transform=transform,
                    dynamodb=dynamodb,
                    s3=s3,
                    triggered_by="schedule",
                )
            except Exception:
                logger.exception("Scheduled execution failed for %s", transform.id)

    @staticmethod
    def _is_due(cron_expr: str, now: datetime) -> bool:
        """Check if a cron expression is due within the scheduler interval."""
        cron = croniter(cron_expr, now)
        prev_time = cron.get_prev(datetime)
        diff = (now - prev_time).total_seconds()
        return diff < settings.scheduler_interval_seconds
