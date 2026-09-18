"""Tests for YouTube Analytics service."""

from app.services.youtube_analytics import (
    ChannelStats,
    VideoMetrics,
    Demographics,
    TrafficSource,
    RevenueData,
    RetentionPoint,
    RealtimeView,
)


def test_channel_stats_defaults():
    stats = ChannelStats()
    assert stats.subscriber_count == 0
    assert stats.total_view_count == 0
    assert stats.channel_name == ""


def test_video_metrics_defaults():
    metrics = VideoMetrics()
    assert metrics.video_id == ""
    assert metrics.view_count == 0
    assert metrics.click_through_rate == 0.0


def test_demographics_defaults():
    demo = Demographics()
    assert demo.age_groups == {}
    assert demo.gender == {}
    assert demo.geography == []


def test_traffic_source_defaults():
    ts = TrafficSource()
    assert ts.source == ""
    assert ts.views == 0
    assert ts.percentage == 0.0


def test_revenue_data_defaults():
    rd = RevenueData()
    assert rd.estimated_revenue == 0.0
    assert rd.monthly_revenue == []


def test_retention_point_defaults():
    rp = RetentionPoint()
    assert rp.second == 0
    assert rp.retention_percentage == 0.0


def test_realtime_view_defaults():
    rv = RealtimeView()
    assert rv.timestamp == ""
    assert rv.views == 0


import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.youtube_analytics import YouTubeAnalytics


@pytest.fixture
def analytics():
    return YouTubeAnalytics()


@pytest.mark.asyncio
async def test_get_channel_stats_simulation(analytics):
    """Without token, returns simulated data."""
    stats = await analytics.get_channel_stats(None)
    assert isinstance(stats, ChannelStats)
    assert stats.channel_name == "Simulated Channel"
    assert stats.subscriber_count > 0


@pytest.mark.asyncio
async def test_get_channel_stats_requires_token(analytics):
    """With invalid token, raises ValueError."""
    with pytest.raises(ValueError, match="access_token"):
        await analytics.get_channel_stats("invalid_token")


@pytest.mark.asyncio
async def test_get_video_metrics_simulation(analytics):
    """Without token, returns simulated data."""
    metrics = await analytics.get_video_metrics(None)
    assert isinstance(metrics, list)
    assert len(metrics) == 3
    assert all(isinstance(m, VideoMetrics) for m in metrics)
    assert metrics[0].view_count > 0


@pytest.mark.asyncio
async def test_get_demographics_simulation(analytics):
    """Without token, returns simulated data."""
    demo = await analytics.get_demographics(None)
    assert isinstance(demo, Demographics)
    assert len(demo.age_groups) == 6
    assert len(demo.gender) == 3
    assert len(demo.geography) == 10


@pytest.mark.asyncio
async def test_get_traffic_sources_simulation(analytics):
    """Without token, returns simulated data."""
    sources = await analytics.get_traffic_sources(None)
    assert isinstance(sources, list)
    assert len(sources) == 5
    assert all(isinstance(s, TrafficSource) for s in sources)
    total_percentage = sum(s.percentage for s in sources)
    assert abs(total_percentage - 100.0) < 0.1


@pytest.mark.asyncio
async def test_get_revenue_data_simulation(analytics):
    """Without token, returns simulated data."""
    revenue = await analytics.get_revenue_data(None)
    assert isinstance(revenue, RevenueData)
    assert revenue.estimated_revenue == 8750.0
    assert len(revenue.monthly_revenue) == 6


@pytest.mark.asyncio
async def test_get_retention_curve_simulation(analytics):
    """Without token, returns simulated data."""
    retention = await analytics.get_retention_curve(None, "any_video_id")
    assert isinstance(retention, list)
    assert len(retention) == 10
    assert all(isinstance(r, RetentionPoint) for r in retention)
    assert retention[0].retention_percentage == 100.0


@pytest.mark.asyncio
async def test_get_realtime_views_simulation(analytics):
    """Without token, returns simulated data."""
    views = await analytics.get_realtime_views(None, hours=24)
    assert isinstance(views, list)
    assert len(views) == 24
    assert all(isinstance(v, RealtimeView) for v in views)


@pytest.mark.asyncio
async def test_close(analytics):
    """Close method works."""
    await analytics.close()
    assert analytics.client.is_closed
