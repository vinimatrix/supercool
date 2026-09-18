"""YouTube Analytics API v1 client for fetching real Studio data."""

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class ChannelStats:
    subscriber_count: int = 0
    total_view_count: int = 0
    total_watch_time_minutes: float = 0.0
    video_count: int = 0
    channel_name: str = ""
    thumbnail_url: str = ""


@dataclass
class VideoMetrics:
    video_id: str = ""
    title: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    average_view_duration_seconds: float = 0.0
    average_view_percentage: float = 0.0
    click_through_rate: float = 0.0
    published_at: str = ""


@dataclass
class Demographics:
    age_groups: dict[str, float] = field(default_factory=dict)
    gender: dict[str, float] = field(default_factory=dict)
    geography: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TrafficSource:
    source: str = ""
    views: int = 0
    percentage: float = 0.0


@dataclass
class RevenueData:
    estimated_revenue: float = 0.0
    estimated_cpm: float = 0.0
    estimated_rpm: float = 0.0
    monthly_revenue: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RetentionPoint:
    second: int = 0
    retention_percentage: float = 0.0


@dataclass
class RealtimeView:
    timestamp: str = ""
    views: int = 0
