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
