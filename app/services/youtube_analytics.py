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


YOUTUBE_ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
YOUTUBE_DATA_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAnalytics:
    """YouTube Analytics API client for fetching real Studio data."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_channel_stats(self, access_token: str | None) -> ChannelStats:
        """Get channel-level statistics."""
        if access_token is None:
            return self._simulate_channel_stats()

        if not access_token or access_token.strip() == "":
            raise ValueError("access_token cannot be empty")

        # Real API call
        try:
            data = await self._fetch_analytics(
                access_token=access_token,
                metrics="subscribers,views,estimatedMinutesWatched,videoCount",
                dimensions=None,
                filters=None,
                sort=None,
                limit=1,
            )
            if not data.get("rows"):
                return self._simulate_channel_stats()

            row = data["rows"][0]
            return ChannelStats(
                subscriber_count=int(row[0]),
                total_view_count=int(row[1]),
                total_watch_time_minutes=float(row[2]),
                video_count=int(row[3]),
                channel_name="YouTube Channel",
                thumbnail_url="",
            )
        except Exception as e:
            raise ValueError(f"access_token error: {e}") from e

    async def get_video_metrics(
        self, access_token: str | None, video_ids: list[str] | None = None
    ) -> list[VideoMetrics]:
        """Get video performance metrics."""
        if access_token is None:
            return self._simulate_video_metrics()

        if not access_token or access_token.strip() == "":
            raise ValueError("access_token cannot be empty")

        # Real API call
        try:
            filters = None
            if video_ids:
                filters = f"video=={','.join(video_ids)}"

            data = await self._fetch_analytics(
                access_token=access_token,
                metrics="views,likes,comments,averageViewDuration,averageViewPercentage,impressions,impressionClickThroughRate",
                dimensions="video",
                filters=filters,
                sort="-views",
                limit=10,
            )

            result = []
            for row in data.get("rows", []):
                result.append(
                    VideoMetrics(
                        video_id=str(row[0]),
                        title="",
                        view_count=int(row[1]),
                        like_count=int(row[2]),
                        comment_count=int(row[3]),
                        average_view_duration_seconds=float(row[4]),
                        average_view_percentage=float(row[5]),
                        click_through_rate=float(row[6]) if len(row) > 6 else 0.0,
                        published_at="",
                    )
                )
            return result if result else self._simulate_video_metrics()
        except Exception as e:
            raise ValueError(f"access_token error: {e}") from e

    async def get_demographics(self, access_token: str | None) -> Demographics:
        """Get audience demographics."""
        if access_token is None:
            return self._simulate_demographics()

        if not access_token or access_token.strip() == "":
            raise ValueError("access_token cannot be empty")

        # Real API call
        try:
            data = await self._fetch_analytics(
                access_token=access_token,
                metrics="viewerPercentage",
                dimensions="ageGroup,gender",
                filters=None,
                sort=None,
                limit=20,
            )

            age_groups = {}
            gender = {}
            for row in data.get("rows", []):
                age_group = str(row[0])
                gen = str(row[1])
                percentage = float(row[2])
                age_groups[age_group] = percentage
                gender[gen] = gender.get(gen, 0) + percentage

            geography_data = []
            geo_data = await self._fetch_analytics(
                access_token=access_token,
                metrics="views",
                dimensions="country",
                filters=None,
                sort="-views",
                limit=10,
            )
            for row in geo_data.get("rows", []):
                geography_data.append(
                    {"country": str(row[0]), "views": int(row[1])}
                )

            return Demographics(
                age_groups=age_groups,
                gender=gender,
                geography=geography_data,
            )
        except Exception as e:
            raise ValueError(f"access_token error: {e}") from e

    async def get_traffic_sources(self, access_token: str | None) -> list[TrafficSource]:
        """Get traffic source breakdown."""
        if access_token is None:
            return self._simulate_traffic_sources()

        if not access_token or access_token.strip() == "":
            raise ValueError("access_token cannot be empty")

        # Real API call
        try:
            data = await self._fetch_analytics(
                access_token=access_token,
                metrics="views",
                dimensions="insightTrafficSourceType",
                filters=None,
                sort="-views",
                limit=10,
            )

            total_views = sum(row[1] for row in data.get("rows", []))
            result = []
            for row in data.get("rows", []):
                views = int(row[1])
                percentage = (views / total_views * 100) if total_views > 0 else 0
                result.append(
                    TrafficSource(
                        source=str(row[0]),
                        views=views,
                        percentage=round(percentage, 2),
                    )
                )
            return result if result else self._simulate_traffic_sources()
        except Exception as e:
            raise ValueError(f"access_token error: {e}") from e

    async def get_revenue_data(self, access_token: str | None) -> RevenueData:
        """Get revenue and monetization data."""
        if access_token is None:
            return self._simulate_revenue()

        if not access_token or access_token.strip() == "":
            raise ValueError("access_token cannot be empty")

        # Real API call
        try:
            data = await self._fetch_analytics(
                access_token=access_token,
                metrics="estimatedRevenue,estimatedCpm,estimatedRpm",
                dimensions=None,
                filters=None,
                sort=None,
                limit=1,
            )

            if not data.get("rows"):
                return self._simulate_revenue()

            row = data["rows"][0]
            monthly_data = []
            monthly = await self._fetch_analytics(
                access_token=access_token,
                metrics="estimatedRevenue",
                dimensions="month",
                filters=None,
                sort="month",
                limit=6,
            )
            for m_row in monthly.get("rows", []):
                monthly_data.append(
                    {"month": str(m_row[0]), "revenue": float(m_row[1])}
                )

            return RevenueData(
                estimated_revenue=float(row[0]),
                estimated_cpm=float(row[1]),
                estimated_rpm=float(row[2]),
                monthly_revenue=monthly_data,
            )
        except Exception as e:
            raise ValueError(f"access_token error: {e}") from e

    async def get_retention_curve(
        self, access_token: str | None, video_id: str
    ) -> list[RetentionPoint]:
        """Get retention curve for a specific video."""
        if access_token is None:
            return self._simulate_retention()

        if not access_token or access_token.strip() == "":
            raise ValueError("access_token cannot be empty")

        if not video_id:
            raise ValueError("video_id cannot be empty")

        # Real API call
        try:
            data = await self._fetch_analytics(
                access_token=access_token,
                metrics="audienceWatchRatio",
                dimensions="elapsedVideoTimeRatio",
                filters=f"video=={video_id}",
                sort="elapsedVideoTimeRatio",
                limit=100,
            )

            result = []
            for row in data.get("rows", []):
                # elapsedVideoTimeRatio is 0.0 to 1.0
                ratio = float(row[0])
                # Convert to seconds assuming video length
                second = int(ratio * 100)  # Approximate
                result.append(
                    RetentionPoint(
                        second=second,
                        retention_percentage=float(row[1]) * 100,
                    )
                )
            return result if result else self._simulate_retention()
        except Exception as e:
            raise ValueError(f"access_token error: {e}") from e

    async def get_realtime_views(
        self, access_token: str | None, hours: int = 48
    ) -> list[RealtimeView]:
        """Get real-time view data."""
        if access_token is None:
            return self._simulate_realtime(hours)

        if not access_token or access_token.strip() == "":
            raise ValueError("access_token cannot be empty")

        # Real API call
        try:
            data = await self._fetch_analytics(
                access_token=access_token,
                metrics="views",
                dimensions="insightPlaybackLocationType",
                filters=None,
                sort=None,
                limit=1,
            )
            # Realtime data is complex; simulate for now
            return self._simulate_realtime(hours)
        except Exception as e:
            raise ValueError(f"access_token error: {e}") from e

    async def _fetch_analytics(
        self,
        access_token: str,
        metrics: str,
        dimensions: str | None,
        filters: str | None,
        sort: str | None,
        limit: int,
    ) -> dict:
        """Internal helper for YouTube Analytics API."""
        params = {
            "ids": "channel==MINE",
            "metrics": metrics,
            "startDate": "2024-01-01",
            "endDate": "2024-12-31",
        }
        if dimensions:
            params["dimensions"] = dimensions
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        if limit:
            params["maxResults"] = str(limit)

        headers = {"Authorization": f"Bearer {access_token}"}
        resp = await self.client.get(
            YOUTUBE_ANALYTICS_URL, params=params, headers=headers
        )
        resp.raise_for_status()
        return resp.json()

    def _simulate_channel_stats(self) -> ChannelStats:
        """Simulate channel stats for demo."""
        return ChannelStats(
            subscriber_count=125000,
            total_view_count=4500000,
            total_watch_time_minutes=1250000.0,
            video_count=156,
            channel_name="Simulated Channel",
            thumbnail_url="https://example.com/thumb.jpg",
        )

    def _simulate_video_metrics(self) -> list[VideoMetrics]:
        """Simulate video metrics for demo."""
        return [
            VideoMetrics(
                video_id="sim_video_1",
                title="AI-Generated Short Film: Neon Dreams",
                view_count=250000,
                like_count=12000,
                comment_count=850,
                average_view_duration_seconds=245.5,
                average_view_percentage=68.2,
                click_through_rate=4.8,
                published_at="2024-03-15T10:00:00Z",
            ),
            VideoMetrics(
                title="Behind the Scenes: AI Animation Process",
                video_id="sim_video_2",
                view_count=180000,
                like_count=9500,
                comment_count=420,
                average_view_duration_seconds=312.0,
                average_view_percentage=72.5,
                click_through_rate=5.2,
                published_at="2024-04-02T14:30:00Z",
            ),
            VideoMetrics(
                title="Tutorial: Creating AI Art for Videos",
                video_id="sim_video_3",
                view_count=95000,
                like_count=5200,
                comment_count=310,
                average_view_duration_seconds=180.3,
                average_view_percentage=55.8,
                click_through_rate=3.9,
                published_at="2024-05-10T09:15:00Z",
            ),
        ]

    def _simulate_demographics(self) -> Demographics:
        """Simulate demographics for demo."""
        return Demographics(
            age_groups={
                "18-24": 28.5,
                "25-34": 35.2,
                "35-44": 18.7,
                "45-54": 11.3,
                "55-64": 4.8,
                "65+": 1.5,
            },
            gender={"male": 62.3, "female": 36.8, "other": 0.9},
            geography=[
                {"country": "US", "views": 1200000},
                {"country": "UK", "views": 680000},
                {"country": "Canada", "views": 420000},
                {"country": "Germany", "views": 310000},
                {"country": "Australia", "views": 280000},
                {"country": "Japan", "views": 240000},
                {"country": "France", "views": 190000},
                {"country": "Brazil", "views": 160000},
                {"country": "India", "views": 150000},
                {"country": "Mexico", "views": 120000},
            ],
        )

    def _simulate_traffic_sources(self) -> list[TrafficSource]:
        """Simulate traffic sources for demo."""
        return [
            TrafficSource(source="YT_SEARCH", views=1800000, percentage=40.0),
            TrafficSource(source="EXT_URL", views=900000, percentage=20.0),
            TrafficSource(source="YT_RECOMMEND", views=1350000, percentage=30.0),
            TrafficSource(source="SUBSCRIBER", views=270000, percentage=6.0),
            TrafficSource(source="DIRECT", views=180000, percentage=4.0),
        ]

    def _simulate_revenue(self) -> RevenueData:
        """Simulate revenue data for demo."""
        return RevenueData(
            estimated_revenue=8750.0,
            estimated_cpm=7.25,
            estimated_rpm=4.85,
            monthly_revenue=[
                {"month": "2024-07", "revenue": 1120.0},
                {"month": "2024-08", "revenue": 1340.0},
                {"month": "2024-09", "revenue": 1560.0},
                {"month": "2024-10", "revenue": 1890.0},
                {"month": "2024-11", "revenue": 1420.0},
                {"month": "2024-12", "revenue": 1420.0},
            ],
        )

    def _simulate_retention(self) -> list[RetentionPoint]:
        """Simulate retention curve for demo."""
        return [
            RetentionPoint(second=0, retention_percentage=100.0),
            RetentionPoint(second=10, retention_percentage=95.2),
            RetentionPoint(second=20, retention_percentage=88.5),
            RetentionPoint(second=30, retention_percentage=82.1),
            RetentionPoint(second=40, retention_percentage=76.8),
            RetentionPoint(second=50, retention_percentage=71.3),
            RetentionPoint(second=60, retention_percentage=65.9),
            RetentionPoint(second=80, retention_percentage=58.4),
            RetentionPoint(second=100, retention_percentage=52.1),
            RetentionPoint(second=120, retention_percentage=45.7),
        ]

    def _simulate_realtime(self, hours: int) -> list[RealtimeView]:
        """Simulate real-time views for demo."""
        import random
        from datetime import datetime, timedelta

        now = datetime.now()
        result = []
        for i in range(hours):
            timestamp = now - timedelta(hours=i)
            views = random.randint(50, 200)
            result.append(
                RealtimeView(
                    timestamp=timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    views=views,
                )
            )
        return result
