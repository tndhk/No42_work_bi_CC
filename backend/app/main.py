"""FastAPI application with authentication and health check."""
# #region agent log
import json
import time
import os
DEBUG_LOG_PATH = "/Users/takahikotsunoda/Dev/No42_work_bi_CC/.cursor/debug.log"
def _debug_log(hypothesis_id: str, location: str, message: str, data: dict):
    try:
        os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
        with open(DEBUG_LOG_PATH, "a") as f:
            f.write(json.dumps({"hypothesisId": hypothesis_id, "location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000), "sessionId": "debug-session"}) + "\n")
    except: pass
# #endregion
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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

app = FastAPI(title="BI API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# #region agent log
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = None
    try:
        body = await request.json()
    except: pass
    _debug_log("A", "main.py:validation_handler", "ValidationError caught", {"path": str(request.url.path), "method": request.method, "errors": exc.errors(), "body": body})
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
# #endregion

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
