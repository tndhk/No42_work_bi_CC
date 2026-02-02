"""API routes initialization."""
from fastapi import APIRouter

from app.api.routes import auth, datasets, dashboards, cards, filter_views, filter_view_detail, users, groups, dashboard_shares

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

# Include filter views routes (dashboard-scoped)
api_router.include_router(
    filter_views.router,
    prefix="/dashboards/{dashboard_id}/filter-views",
    tags=["filter-views"],
)

# Include users routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include filter view detail routes (independent)
api_router.include_router(
    filter_view_detail.router,
    prefix="/filter-views",
    tags=["filter-views"],
)

# Include dashboard shares routes (dashboard-scoped)
api_router.include_router(
    dashboard_shares.router,
    prefix="/dashboards/{dashboard_id}/shares",
    tags=["dashboard-shares"],
)

# Include groups routes
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
