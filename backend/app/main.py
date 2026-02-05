"""FastAPI application with authentication and health check."""
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifespan events."""
    # Startup
    setup_logging()

    # Start scheduler if enabled
    scheduler = None
    if settings.scheduler_enabled:
        from app.services.transform_scheduler_service import TransformSchedulerService
        scheduler = TransformSchedulerService()
        await scheduler.start()

    yield

    # Shutdown
    if scheduler:
        await scheduler.stop()


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
# Disable rate limiting if configured (e.g., for E2E tests)
limiter.enabled = settings.rate_limit_enabled

app = FastAPI(title="BI API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
