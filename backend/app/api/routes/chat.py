"""Chat API routes for AI-powered dashboard data analysis."""
import logging
from typing import Any
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.core.config import settings
from app.models.chat import ChatRequest
from app.models.dashboard_share import Permission
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.services.audit_service import AuditService
from app.services.dashboard_service import DashboardService
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
limiter.enabled = settings.rate_limit_enabled


@router.post("/{dashboard_id}/chat")
@limiter.limit(f"{settings.chatbot_rate_limit_user}/minute")
async def chat(
    request: Request,
    dashboard_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3_client: Any = Depends(get_s3_client),
) -> StreamingResponse:
    """Stream AI chat response for a dashboard.

    Processing flow:
      1. JWT authentication + Dashboard VIEWER permission check
      2. Fetch referenced datasets via DashboardService
      3. Generate dataset summaries via DatasetSummarizer
      4. Convert summaries to prompt text via DatasetSummary.to_prompt_text()
      5. Stream chat response via ChatbotService
      6. Format as SSE events
      7. Log chatbot query via AuditService

    Rate limit: Configurable via settings.chatbot_rate_limit_user per minute per IP address.

    Args:
        request: HTTP request object (for rate limiting)
        dashboard_id: Dashboard ID
        chat_request: Chat request containing message and conversation history
        current_user: Authenticated user
        dynamodb: DynamoDB resource
        s3_client: S3 client

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: 404 if dashboard not found, 403 if insufficient permission
    """
    # 1. Fetch dashboard and check VIEWER permission
    repo = DashboardRepository()
    dashboard = await repo.get_by_id(dashboard_id, dynamodb)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    permission_service = PermissionService()
    await permission_service.assert_permission(
        dashboard, current_user.id, Permission.VIEWER, dynamodb
    )

    # 2. Get referenced datasets
    dashboard_service = DashboardService()
    referenced_datasets = await dashboard_service.get_referenced_datasets(
        dashboard=dashboard, dynamodb=dynamodb
    )

    # 3. Generate summaries for each dataset
    # Import here to avoid top-level dependency on vertexai
    from app.services.parquet_storage import ParquetReader
    from app.services.dataset_summarizer import DatasetSummarizer
    from app.models.dataset_summary import DatasetSummary

    parquet_reader = ParquetReader(s3_client=s3_client, bucket=settings.s3_bucket_datasets)
    summarizer = DatasetSummarizer(parquet_reader=parquet_reader)

    dataset_texts: list[str] = []
    for ds_info in referenced_datasets:
        ds_name = ds_info.get("name", "Unknown")
        ds_id = ds_info.get("dataset_id", "")
        s3_path = f"datasets/{ds_id}/data.parquet"

        try:
            summary_dict = await summarizer.generate_summary(s3_path)
            summary = DatasetSummary(
                name=ds_name,
                schema=summary_dict["schema"],
                row_count=summary_dict["row_count"],
                column_count=summary_dict["column_count"],
                sample_rows=[],
                statistics=summary_dict["statistics"],
            )
            dataset_texts.append(summary.to_prompt_text())
        except Exception:
            logger.warning(
                "Failed to generate summary for dataset %s (%s), skipping",
                ds_name,
                ds_id,
            )

    # 5-6. Stream chat response as SSE
    from app.services.chatbot_service import ChatbotService, format_sse_event

    chatbot_service = ChatbotService(settings=settings)

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from chatbot stream."""
        try:
            async for token in chatbot_service.stream_chat(
                dashboard_name=dashboard.name,
                dataset_texts=dataset_texts,
                message=chat_request.message,
                conversation_history=chat_request.conversation_history,
            ):
                yield format_sse_event(data=token, event="token")
        except Exception as e:
            logger.error("Chat streaming error: %s", e)
            yield format_sse_event(data=str(e), event="error")

        # Send done event to signal end of stream
        yield format_sse_event(data="", event="done")

        # 7. Log chatbot query after stream completes
        audit = AuditService()
        await audit.log_chatbot_query(
            user_id=current_user.id,
            dashboard_id=dashboard_id,
            message=chat_request.message,
            dynamodb=dynamodb,
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
