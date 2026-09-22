"""Analytics API - Project metrics and revenue projections."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.analytics_dashboard import Dashboard, ProjectMetrics

router = APIRouter(tags=["analytics"])

_dashboard = Dashboard()


class MetricsInput(BaseModel):
    project_id: str
    title: str
    views: int = 0
    watch_hours: float = 0.0
    cpm: float = 2.0
    platform: str = "youtube"


class ProjectionRequest(BaseModel):
    months: int = 6
    monthly_growth_rate: float = 0.15


@router.post("/analytics/metrics")
async def add_metrics(data: MetricsInput):
    """Add or update project metrics."""
    metrics = ProjectMetrics(
        project_id=data.project_id,
        title=data.title,
        views=data.views,
        watch_hours=data.watch_hours,
        cpm=data.cpm,
        platform=data.platform,
    )
    _dashboard.add_project(metrics)
    return {"status": "ok", "total_projects": len(_dashboard.projects)}


@router.get("/analytics/summary")
async def get_summary():
    """Get aggregated analytics summary."""
    return {
        "total_projects": len(_dashboard.projects),
        "total_views": _dashboard.total_views,
        "total_watch_hours": _dashboard.total_watch_hours,
        "total_revenue": _dashboard.total_revenue,
        "average_cpm": _dashboard.average_cpm,
        "projects": _dashboard.project_earnings(),
    }


@router.post("/analytics/projections")
async def get_projections(data: ProjectionRequest):
    """Get future earnings projections."""
    return {
        "projections": _dashboard.project_future_earnings(
            months=data.months,
            monthly_growth_rate=data.monthly_growth_rate,
        )
    }


@router.get("/analytics/dashboard")
async def get_dashboard():
    """Get comprehensive analytics dashboard data."""
    return {
        "overview": {
            "total_projects": len(_dashboard.projects),
            "total_views": _dashboard.total_views,
            "total_watch_hours": _dashboard.total_watch_hours,
            "total_revenue": _dashboard.total_revenue,
            "average_cpm": _dashboard.average_cpm,
        },
        "projects": _dashboard.project_earnings(),
        "projections": _dashboard.project_future_earnings(months=6, monthly_growth_rate=0.15),
    }
