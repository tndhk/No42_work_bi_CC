"""API routes initialization."""
from fastapi import APIRouter

from app.api.routes import auth, datasets, dashboards, cards

# Create main API router
api_router = APIRouter()

# Include auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include datasets routes
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])

# Include dashboards routes
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])

# Include cards routes
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
