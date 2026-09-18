"""YouTube Publisher API - Upload finished videos to YouTube."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.youtube_ai_analyst import YouTubeAIAnalyst
from app.services.youtube_analytics import YouTubeAnalytics
from app.services.youtube_publisher import YouTubePublisher

router = APIRouter(tags=["youtube"])


class YouTubeUploadRequest(BaseModel):
    video_path: str
    title: str
    description: str = ""
    tags: list[str] = []
    category_id: str = "1"
    privacy_status: str = "unlisted"
    thumbnail_path: str | None = None
    access_token: str | None = None


class YouTubeUploadResponse(BaseModel):
    video_id: str
    url: str
    status: str
    title: str


@router.post("/youtube/upload", response_model=YouTubeUploadResponse)
async def upload_to_youtube(data: YouTubeUploadRequest):
    """Upload a video to YouTube.

    Requires YOUTUBE_ACCESS_TOKEN env var or access_token in request body.
    """
    publisher = YouTubePublisher(access_token=data.access_token)

    try:
        result = publisher.publish(
            video_path=data.video_path,
            title=data.title,
            description=data.description,
            tags=data.tags,
            category_id=data.category_id,
            privacy_status=data.privacy_status,
            thumbnail_path=data.thumbnail_path,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Video not found: {data.video_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return YouTubeUploadResponse(**result)


class YouTubeAnalyzeRequest(BaseModel):
    access_token: str | None = None
    ai_provider: str = "groq"
    video_ids: list[str] | None = None


class AnalysisReportResponse(BaseModel):
    summary: str
    trends: list[str]
    recommendations: list[str]
    growth_predictions: dict
    top_performing: list[dict]
    improvement_areas: list[str]
    charts_data: dict
    generated_at: str
    data_freshness: str


_analytics = YouTubeAnalytics()


@router.get("/youtube/analytics/channel")
async def get_channel_stats(access_token: str | None = None):
    """Get channel-level statistics."""
    stats = await _analytics.get_channel_stats(access_token)
    return {
        "subscriber_count": stats.subscriber_count,
        "total_view_count": stats.total_view_count,
        "total_watch_time_minutes": stats.total_watch_time_minutes,
        "video_count": stats.video_count,
        "channel_name": stats.channel_name,
        "thumbnail_url": stats.thumbnail_url,
    }


@router.get("/youtube/analytics/videos")
async def get_video_metrics(access_token: str | None = None, video_ids: str | None = None):
    """Get video performance metrics."""
    ids = video_ids.split(",") if video_ids else None
    metrics = await _analytics.get_video_metrics(access_token, ids)
    return [
        {
            "video_id": m.video_id,
            "title": m.title,
            "view_count": m.view_count,
            "like_count": m.like_count,
            "comment_count": m.comment_count,
            "average_view_duration_seconds": m.average_view_duration_seconds,
            "average_view_percentage": m.average_view_percentage,
            "click_through_rate": m.click_through_rate,
            "published_at": m.published_at,
        }
        for m in metrics
    ]


@router.get("/youtube/analytics/demographics")
async def get_demographics(access_token: str | None = None):
    """Get audience demographics."""
    demo = await _analytics.get_demographics(access_token)
    return {
        "age_groups": demo.age_groups,
        "gender": demo.gender,
        "geography": demo.geography,
    }


@router.get("/youtube/analytics/traffic")
async def get_traffic_sources(access_token: str | None = None):
    """Get traffic source breakdown."""
    sources = await _analytics.get_traffic_sources(access_token)
    return [{"source": s.source, "views": s.views, "percentage": s.percentage} for s in sources]


@router.get("/youtube/analytics/revenue")
async def get_revenue_data(access_token: str | None = None):
    """Get revenue and monetization metrics."""
    revenue = await _analytics.get_revenue_data(access_token)
    return {
        "estimated_revenue": revenue.estimated_revenue,
        "estimated_cpm": revenue.estimated_cpm,
        "estimated_rpm": revenue.estimated_rpm,
        "monthly_revenue": revenue.monthly_revenue,
    }


@router.get("/youtube/analytics/retention")
async def get_retention_curve(access_token: str | None = None, video_id: str = ""):
    """Get retention curve for a video."""
    curve = await _analytics.get_retention_curve(access_token, video_id)
    return [{"second": p.second, "retention_percentage": p.retention_percentage} for p in curve]


@router.get("/youtube/analytics/realtime")
async def get_realtime_views(access_token: str | None = None, hours: int = 48):
    """Get real-time view counts."""
    views = await _analytics.get_realtime_views(access_token, hours)
    return [{"timestamp": v.timestamp, "views": v.views} for v in views]


@router.post("/youtube/analyze", response_model=AnalysisReportResponse)
async def analyze_youtube(data: YouTubeAnalyzeRequest):
    """Fetch YouTube data and generate AI analysis report."""
    channel = await _analytics.get_channel_stats(data.access_token)
    videos = await _analytics.get_video_metrics(data.access_token, data.video_ids)
    demographics = await _analytics.get_demographics(data.access_token)
    traffic = await _analytics.get_traffic_sources(data.access_token)
    revenue = await _analytics.get_revenue_data(data.access_token)
    retention = await _analytics.get_retention_curve(data.access_token, videos[0].video_id if videos else "")

    youtube_data = {
        "subscriber_count": channel.subscriber_count,
        "total_views": channel.total_view_count,
        "watch_hours": channel.total_watch_time_minutes / 60,
        "video_count": channel.video_count,
        "videos": [
            {"title": v.title, "views": v.view_count, "likes": v.like_count,
             "comments": v.comment_count, "avg_duration": v.average_view_duration_seconds,
             "avg_view_pct": v.average_view_percentage, "ctr": v.click_through_rate}
            for v in videos
        ],
        "demographics": {
            "age_groups": demographics.age_groups,
            "gender": demographics.gender,
            "geography": demographics.geography[:5],
        },
        "traffic_sources": [{"source": s.source, "views": s.views, "pct": s.percentage} for s in traffic],
        "revenue": {
            "total": revenue.estimated_revenue,
            "cpm": revenue.estimated_cpm,
            "rpm": revenue.estimated_rpm,
            "monthly": revenue.monthly_revenue,
        },
        "retention": [{"second": p.second, "pct": p.retention_percentage} for p in retention],
    }

    analyst = YouTubeAIAnalyst(provider=data.ai_provider)
    report = await analyst.analyze(youtube_data)
    await analyst.close()

    return AnalysisReportResponse(
        summary=report.summary,
        trends=report.trends,
        recommendations=report.recommendations,
        growth_predictions=report.growth_predictions,
        top_performing=report.top_performing,
        improvement_areas=report.improvement_areas,
        charts_data=report.charts_data,
        generated_at=report.generated_at,
        data_freshness=report.data_freshness,
    )
