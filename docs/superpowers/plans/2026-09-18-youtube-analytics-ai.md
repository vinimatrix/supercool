# YouTube Analytics + AI Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate YouTube Analytics API v1 with Groq/Ollama AI to provide on-demand analysis reports of YouTube channel performance.

**Architecture:** Backend service fetches real analytics data from YouTube Analytics API v1, sends structured data to Groq/Ollama for AI analysis, returns structured report. Frontend provides YouTube Analytics tab with dashboard, charts, and AI report display.

**Tech Stack:** Python httpx (async), FastAPI, YouTube Analytics API v1, Groq API, Ollama (optional), React, TypeScript, Recharts (charts)

## Global Constraints

- Python venv managed by `uv`; run tests with `.venv\Scripts\python.exe -m pytest`
- Windows environment (PowerShell) — use `;` not `&&`, `where` not `which`
- Server runs on port **8001**
- Frontend runs on port **5173/5174** (Vite dev server, proxies `/api` to 8001)
- `tsconfig.app.json` has `verbatimModuleSyntax: true` — type-only imports must use `import type`
- Groq API key: `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`, model: `openai/gpt-oss-20b`
- YouTube Analytics API v1 endpoint: `https://youtubeanalytics.googleapis.com/v2/reports`
- YouTube Data API v3 endpoint: `https://www.googleapis.com/youtube/v3`

---

## File Structure

**Create:**
- `app/services/youtube_analytics.py` — YouTube Analytics API client (7 methods)
- `app/services/youtube_ai_analyst.py` — AI analysis service (Groq + Ollama)
- `tests/test_services/test_youtube_analytics.py` — Unit tests for analytics service
- `tests/test_services/test_youtube_ai_analyst.py` — Unit tests for AI analyst
- `frontend/src/components/youtube/YouTubeConnect.tsx` — Token input + connect
- `frontend/src/components/youtube/YouTubeDashboard.tsx` — Channel stats cards
- `frontend/src/components/youtube/YouTubeVideos.tsx` — Video performance table
- `frontend/src/components/youtube/YouTubeDemographics.tsx` — Age/gender charts
- `frontend/src/components/youtube/YouTubeTraffic.tsx` — Traffic sources chart
- `frontend/src/components/youtube/YouTubeRetention.tsx` — Retention curve chart
- `frontend/src/components/youtube/YouTubeAIReport.tsx` — AI analysis display
- `frontend/src/components/youtube/YouTubeAnalyze.tsx` — Analyze button + provider
- `frontend/src/components/youtube/index.ts` — Barrel export
- `frontend/src/api/youtube.ts` — Frontend API client

**Modify:**
- `app/api/routes/youtube.py` — Add 8 analytics endpoints
- `app/config.py` — Add YouTube Analytics API settings
- `frontend/src/App.tsx` — Add YouTube Analytics tab to sidebar

---

### Task 1: YouTube Analytics Service — Data Models

**Files:**
- Create: `app/services/youtube_analytics.py`
- Test: `tests/test_services/test_youtube_analytics.py`

**Interfaces:**
- Produces: `ChannelStats`, `VideoMetrics`, `Demographics`, `TrafficSource`, `RevenueData`, `RetentionPoint`, `RealtimeView` dataclasses

- [ ] **Step 1: Create data models**

```python
# app/services/youtube_analytics.py
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
```

- [ ] **Step 2: Write failing test for data models**

```python
# tests/test_services/test_youtube_analytics.py
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
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_services/test_youtube_analytics.py -v`
Expected: All 7 tests PASS (dataclasses have defaults)

- [ ] **Step 4: Commit**

```bash
git add app/services/youtube_analytics.py tests/test_services/test_youtube_analytics.py
git commit -m "feat(youtube): add analytics data models"
```

---

### Task 2: YouTube Analytics Service — API Client

**Files:**
- Modify: `app/services/youtube_analytics.py`
- Modify: `tests/test_services/test_youtube_analytics.py`

**Interfaces:**
- Consumes: Data models from Task 1
- Produces: `YouTubeAnalytics` class with 7 methods

- [ ] **Step 1: Write failing tests for API client**

Append to `tests/test_services/test_youtube_analytics.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_services/test_youtube_analytics.py::test_get_channel_stats_simulation -v`
Expected: FAIL with `AttributeError: 'YouTubeAnalytics' object has no attribute 'get_channel_stats'`

- [ ] **Step 3: Implement YouTubeAnalytics class**

```python
# Add to app/services/youtube_analytics.py after dataclasses

YOUTUBE_ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
YOUTUBE_DATA_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAnalytics:
    """Fetches real analytics data from YouTube Analytics API v1."""

    def __init__(self):
        self._http = httpx.AsyncClient(timeout=30)

    async def close(self):
        await self._http.aclose()

    async def get_channel_stats(self, access_token: str | None) -> ChannelStats:
        """Get channel-level statistics."""
        if not access_token:
            return self._simulate_channel_stats()

        # Get channel metadata from Data API v3
        channel_resp = await self._http.get(
            f"{YOUTUBE_DATA_URL}/channels",
            params={"part": "snippet,statistics", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        channel_resp.raise_for_status()
        channel_data = channel_resp.json()["items"][0]

        # Get watch time from Analytics API
        analytics_resp = await self._fetch_analytics(
            access_token,
            metrics="estimatedMinutesWatched,views",
            dimensions="channel",
        )

        stats = ChannelStats(
            subscriber_count=int(channel_data["statistics"]["subscriberCount"]),
            total_view_count=int(channel_data["statistics"]["viewCount"]),
            total_watch_time_minutes=analytics_resp.get("estimatedMinutesWatched", 0),
            video_count=int(channel_data["statistics"]["videoCount"]),
            channel_name=channel_data["snippet"]["title"],
            thumbnail_url=channel_data["snippet"]["thumbnails"]["default"]["url"],
        )
        return stats

    async def get_video_metrics(self, access_token: str | None, video_ids: list[str] | None = None) -> list[VideoMetrics]:
        """Get performance metrics for specific videos."""
        if not access_token:
            return self._simulate_video_metrics()

        # Get video details from Data API v3
        params = {"part": "snippet,statistics,contentDetails"}
        if video_ids:
            params["id"] = ",".join(video_ids)
        else:
            params["chart"] = "mostPopular"
            params["maxResults"] = "10"

        resp = await self._http.get(
            f"{YOUTUBE_DATA_URL}/videos",
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        videos = resp.json().get("items", [])

        # Get analytics for each video
        metrics_list = []
        for video in videos:
            vid = video["id"]
            analytics = await self._fetch_analytics(
                access_token,
                metrics="estimatedMinutesWatched,views,likes,comments,averageViewDuration,averageViewPercentage,impressions,clicks",
                dimensions="video",
                filters=f"video=={vid}",
            )
            row = analytics.get("rows", [[]])[0] if analytics.get("rows") else []
            metrics_list.append(VideoMetrics(
                video_id=vid,
                title=video["snippet"]["title"],
                view_count=int(video["statistics"].get("viewCount", 0)),
                like_count=int(video["statistics"].get("likeCount", 0)),
                comment_count=int(video["statistics"].get("commentCount", 0)),
                average_view_duration_seconds=row[4] if len(row) > 4 else 0,
                average_view_percentage=row[5] if len(row) > 5 else 0,
                click_through_rate=(row[7] / row[6] * 100) if len(row) > 7 and row[6] > 0 else 0,
                published_at=video["snippet"]["publishedAt"],
            ))
        return metrics_list

    async def get_demographics(self, access_token: str | None) -> Demographics:
        """Get audience demographics (age, gender, geography)."""
        if not access_token:
            return self._simulate_demographics()

        # Age groups
        age_resp = await self._fetch_analytics(
            access_token,
            metrics="viewPercentage",
            dimensions="ageGroup",
        )
        age_groups = {row[0]: row[1] for row in age_resp.get("rows", [])}

        # Gender
        gender_resp = await self._fetch_analytics(
            access_token,
            metrics="viewPercentage",
            dimensions="gender",
        )
        gender = {row[0]: row[1] for row in gender_resp.get("rows", [])}

        # Geography
        geo_resp = await self._fetch_analytics(
            access_token,
            metrics="views",
            dimensions="country",
            sort="-views",
            limit="10",
        )
        geography = [{"country": row[0], "views": row[1]} for row in geo_resp.get("rows", [])]

        return Demographics(age_groups=age_groups, gender=gender, geography=geography)

    async def get_traffic_sources(self, access_token: str | None) -> list[TrafficSource]:
        """Get traffic source breakdown."""
        if not access_token:
            return self._simulate_traffic_sources()

        resp = await self._fetch_analytics(
            access_token,
            metrics="views",
            dimensions="insightTrafficSourceType",
        )
        total_views = sum(row[1] for row in resp.get("rows", []))
        sources = []
        for row in resp.get("rows", []):
            sources.append(TrafficSource(
                source=row[0],
                views=row[1],
                percentage=(row[1] / total_views * 100) if total_views > 0 else 0,
            ))
        return sorted(sources, key=lambda x: x.views, reverse=True)

    async def get_revenue_data(self, access_token: str | None) -> RevenueData:
        """Get revenue and monetization metrics."""
        if not access_token:
            return self._simulate_revenue()

        # Monthly revenue
        resp = await self._fetch_analytics(
            access_token,
            metrics="estimatedRevenue,estimatedAdRevenue,estimatedRedPartnerRevenue,playbackBasedCpmRevenue",
            dimensions="month",
            sort="month",
        )
        monthly = []
        total_revenue = 0
        for row in resp.get("rows", []):
            revenue = row[1] + row[2] + row[3]
            total_revenue += revenue
            monthly.append({"month": row[0], "revenue": round(revenue, 2)})

        # CPM/RPM from latest month
        latest = monthly[-1] if monthly else {"revenue": 0}
        views_resp = await self._fetch_analytics(
            access_token,
            metrics="views",
        )
        total_views = views_resp.get("rows", [[0]])[0][0] if views_resp.get("rows") else 0

        return RevenueData(
            estimated_revenue=round(total_revenue, 2),
            estimated_cpm=round((latest["revenue"] / total_views * 1000) if total_views > 0 else 0, 2),
            estimated_rpm=round(total_revenue / (total_views / 1000) if total_views > 0 else 0, 2),
            monthly_revenue=monthly,
        )

    async def get_retention_curve(self, access_token: str | None, video_id: str) -> list[RetentionPoint]:
        """Get retention curve for a specific video."""
        if not access_token:
            return self._simulate_retention()

        resp = await self._fetch_analytics(
            access_token,
            metrics="viewPercentage",
            dimensions="elapsedVideoTimeRatio",
            filters=f"video=={video_id}",
        )
        return [
            RetentionPoint(second=int(row[0] * 100), retention_percentage=row[1])
            for row in resp.get("rows", [])
        ]

    async def get_realtime_views(self, access_token: str | None, hours: int = 48) -> list[RealtimeView]:
        """Get real-time view counts for last N hours."""
        if not access_token:
            return self._simulate_realtime(hours)

        resp = await self._fetch_analytics(
            access_token,
            metrics="views",
            dimensions="minute",
            sort="minute",
            limit=str(hours * 60),
        )
        return [
            RealtimeView(timestamp=row[0], views=row[1])
            for row in resp.get("rows", [])
        ]

    async def _fetch_analytics(
        self,
        access_token: str,
        metrics: str,
        dimensions: str = "",
        filters: str = "",
        sort: str = "",
        limit: str = "",
    ) -> dict:
        """Fetch from YouTube Analytics API v2."""
        params = {
            "ids": "channel==MINE",
            "metrics": metrics,
            "startDate": "2020-01-01",
            "endDate": "2099-12-31",
        }
        if dimensions:
            params["dimensions"] = dimensions
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        if limit:
            params["maxResults"] = limit

        resp = await self._http.get(
            YOUTUBE_ANALYTICS_URL,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()

    def _simulate_channel_stats(self) -> ChannelStats:
        return ChannelStats(
            subscriber_count=125000,
            total_view_count=4500000,
            total_watch_time_minutes=180000,
            video_count=47,
            channel_name="Simulated Channel",
            thumbnail_url="",
        )

    def _simulate_video_metrics(self) -> list[VideoMetrics]:
        return [
            VideoMetrics(video_id="sim_1", title="Boruto TBV - Scene 1", view_count=125000, like_count=8500, comment_count=340, average_view_duration_seconds=180, average_view_percentage=75.0, click_through_rate=8.2, published_at="2026-01-15"),
            VideoMetrics(video_id="sim_2", title="Boruto TBV - Episode 1", view_count=350000, like_count=22000, comment_count=1200, average_view_duration_seconds=420, average_view_percentage=68.0, click_through_rate=7.5, published_at="2026-02-01"),
            VideoMetrics(video_id="sim_3", title="Naruto Flashback", view_count=89000, like_count=5200, comment_count=180, average_view_duration_seconds=95, average_view_percentage=82.0, click_through_rate=9.1, published_at="2026-03-10"),
        ]

    def _simulate_demographics(self) -> Demographics:
        return Demographics(
            age_groups={"18-24": 35.0, "25-34": 28.0, "35-44": 18.0, "45-54": 12.0, "55-64": 5.0, "65+": 2.0},
            gender={"male": 62.0, "female": 36.0, "other": 2.0},
            geography=[{"country": "US", "views": 1800000}, {"country": "JP", "views": 900000}, {"country": "BR", "views": 600000}, {"country": "MX", "views": 450000}, {"country": "IN", "views": 350000}],
        )

    def _simulate_traffic_sources(self) -> list[TrafficSource]:
        return [
            TrafficSource(source="SEARCH", views=1800000, percentage=40.0),
            TrafficSource(source="SUGGESTED", views=1350000, percentage=30.0),
            TrafficSource(source="EXTERNAL", views=675000, percentage=15.0),
            TrafficSource(source="DIRECT", views=450000, percentage=10.0),
            TrafficSource(source="SUBSCRIBER", views=225000, percentage=5.0),
        ]

    def _simulate_revenue(self) -> RevenueData:
        return RevenueData(
            estimated_revenue=8750.00,
            estimated_cpm=2.50,
            estimated_rpm=3.20,
            monthly_revenue=[
                {"month": "2026-01", "revenue": 950.00},
                {"month": "2026-02", "revenue": 1200.00},
                {"month": "2026-03", "revenue": 1450.00},
                {"month": "2026-04", "revenue": 1600.00},
                {"month": "2026-05", "revenue": 1750.00},
                {"month": "2026-06", "revenue": 1800.00},
            ],
        )

    def _simulate_retention(self) -> list[RetentionPoint]:
        return [
            RetentionPoint(second=0, retention_percentage=100.0),
            RetentionPoint(second=10, retention_percentage=95.0),
            RetentionPoint(second=30, retention_percentage=88.0),
            RetentionPoint(second=60, retention_percentage=78.0),
            RetentionPoint(second=90, retention_percentage=72.0),
            RetentionPoint(second=120, retention_percentage=68.0),
            RetentionPoint(second=180, retention_percentage=62.0),
            RetentionPoint(second=240, retention_percentage=58.0),
            RetentionPoint(second=300, retention_percentage=55.0),
            RetentionPoint(second=360, retention_percentage=52.0),
        ]

    def _simulate_realtime(self, hours: int) -> list[RealtimeView]:
        import random
        return [
            RealtimeView(timestamp=f"2026-09-18T{i:02d}:00Z", views=random.randint(100, 500))
            for i in range(hours)
        ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_services/test_youtube_analytics.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/youtube_analytics.py tests/test_services/test_youtube_analytics.py
git commit -m "feat(youtube): add analytics API client with simulation mode"
```

---

### Task 3: YouTube AI Analyst Service

**Files:**
- Create: `app/services/youtube_ai_analyst.py`
- Test: `tests/test_services/test_youtube_ai_analyst.py`

**Interfaces:**
- Consumes: Data models from Task 1
- Produces: `AnalysisReport` dataclass, `YouTubeAIAnalyst` class

- [ ] **Step 1: Create data models and service skeleton**

```python
# app/services/youtube_ai_analyst.py
"""AI-powered YouTube analytics analysis using Groq/Ollama."""

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class AnalysisReport:
    summary: str = ""
    trends: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    growth_predictions: dict[str, Any] = field(default_factory=dict)
    top_performing: list[dict[str, Any]] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)
    charts_data: dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""
    data_freshness: str = "simulated"


class YouTubeAIAnalyst:
    """Generates AI-powered analysis reports from YouTube data."""

    def __init__(self, provider: str = "groq"):
        self.provider = provider
        self._http = httpx.AsyncClient(timeout=60)

    async def close(self):
        await self._http.aclose()

    async def analyze(self, youtube_data: dict[str, Any]) -> AnalysisReport:
        """Generate full analysis report from YouTube data."""
        prompt = self._build_prompt(youtube_data)

        if self.provider == "ollama":
            response = await self._call_ollama(prompt)
        else:
            response = await self._call_groq(prompt)

        return self._parse_report(response)

    def _build_prompt(self, data: dict[str, Any]) -> str:
        """Build structured prompt for LLM."""
        return f"""Eres un analista de YouTube experto. Analiza los siguientes datos y genera un reporte completo en español.

Datos del Canal:
- Suscriptores: {data.get('subscriber_count', 0):,}
- Views totales: {data.get('total_views', 0):,}
- Watch time: {data.get('watch_hours', 0):,.1f} horas
- Videos: {data.get('video_count', 0)}

Rendimiento de Videos:
{json.dumps(data.get('videos', []), indent=2, ensure_ascii=False)}

Demografía:
{json.dumps(data.get('demographics', {}), indent=2, ensure_ascii=False)}

Fuentes de Tráfico:
{json.dumps(data.get('traffic_sources', []), indent=2, ensure_ascii=False)}

Revenue:
{json.dumps(data.get('revenue', {}), indent=2, ensure_ascii=False)}

Retención:
{json.dumps(data.get('retention', []), indent=2, ensure_ascii=False)}

Genera un reporte JSON con esta estructura exacta:
{{
  "summary": "Resumen ejecutivo en 2-3 oraciones",
  "trends": ["tendencia 1", "tendencia 2", "tendencia 3"],
  "recommendations": ["recomendación 1", "recomendación 2", "recomendación 3"],
  "growth_predictions": {{
    "3_months": "predicción 3 meses",
    "6_months": "predicción 6 meses",
    "12_months": "predicción 12 meses"
  }},
  "top_performing": [{{"title": "video", "reason": "por qué es exitoso"}}],
  "improvement_areas": ["área 1", "área 2"]
}}

Responde SOLO con el JSON, sin texto adicional."""

    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API for analysis."""
        api_key = os.environ.get("GROQ_API_KEY", "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")

        resp = await self._http.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for analysis."""
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")

        resp = await self._http.post(
            f"{ollama_url}/api/chat",
            json={
                "model": "llama3.1",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def _parse_report(self, response: str) -> AnalysisReport:
        """Parse LLM response into structured report."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            return AnalysisReport(
                summary=data.get("summary", ""),
                trends=data.get("trends", []),
                recommendations=data.get("recommendations", []),
                growth_predictions=data.get("growth_predictions", {}),
                top_performing=data.get("top_performing", []),
                improvement_areas=data.get("improvement_areas", []),
                generated_at=__import__("datetime").datetime.now().isoformat(),
                data_freshness="real",
            )
        except (json.JSONDecodeError, IndexError):
            # Fallback: treat entire response as summary
            return AnalysisReport(
                summary=response[:500],
                trends=[],
                recommendations=[],
                generated_at=__import__("datetime").datetime.now().isoformat(),
                data_freshness="real",
            )
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_services/test_youtube_ai_analyst.py
"""Tests for YouTube AI Analyst service."""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.youtube_ai_analyst import YouTubeAIAnalyst, AnalysisReport


@pytest.fixture
def analyst():
    return YouTubeAIAnalyst(provider="groq")


def test_analysis_report_defaults():
    report = AnalysisReport()
    assert report.summary == ""
    assert report.trends == []
    assert report.recommendations == []


@pytest.mark.asyncio
async def test_build_prompt(analyst):
    data = {"subscriber_count": 1000, "total_views": 50000}
    prompt = analyst._build_prompt(data)
    assert "1,000" in prompt
    assert "50,000" in prompt
    assert "analista de YouTube" in prompt


@pytest.mark.asyncio
async def test_parse_report_valid_json(analyst):
    response = '{"summary": "Test summary", "trends": ["trend1"], "recommendations": ["rec1"], "growth_predictions": {}, "top_performing": [], "improvement_areas": []}'
    report = analyst._parse_report(response)
    assert report.summary == "Test summary"
    assert report.trends == ["trend1"]
    assert report.data_freshness == "real"


@pytest.mark.asyncio
async def test_parse_report_markdown_json(analyst):
    response = '```json\n{"summary": "From markdown", "trends": [], "recommendations": [], "growth_predictions": {}, "top_performing": [], "improvement_areas": []}\n```'
    report = analyst._parse_report(response)
    assert report.summary == "From markdown"


@pytest.mark.asyncio
async def test_parse_report_invalid_json(analyst):
    response = "This is not JSON at all"
    report = analyst._parse_report(response)
    assert report.summary == "This is not JSON at all"
    assert report.trends == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_services/test_youtube_ai_analyst.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_services/test_youtube_ai_analyst.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/youtube_ai_analyst.py tests/test_services/test_youtube_ai_analyst.py
git commit -m "feat(youtube): add AI analysis service with Groq/Ollama support"
```

---

### Task 4: YouTube Analytics API Routes

**Files:**
- Modify: `app/api/routes/youtube.py`
- Test: `tests/test_routes/test_youtube_analytics.py`

**Interfaces:**
- Consumes: `YouTubeAnalytics` from Task 2, `YouTubeAIAnalyst` from Task 3
- Produces: 8 new FastAPI endpoints

- [ ] **Step 1: Write failing tests**

```python
# tests/test_routes/test_youtube_analytics.py
"""Tests for YouTube analytics API routes."""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_channel_stats_simulation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/youtube/analytics/channel")
    assert resp.status_code == 200
    data = resp.json()
    assert "subscriber_count" in data
    assert data["channel_name"] == "Simulated Channel"


@pytest.mark.asyncio
async def test_videos_simulation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/youtube/analytics/videos")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0


@pytest.mark.asyncio
async def test_analyze_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/youtube/analyze", json={
            "access_token": None,
            "ai_provider": "groq",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "recommendations" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_routes/test_youtube_analytics.py -v`
Expected: FAIL with 404 (endpoints don't exist yet)

- [ ] **Step 3: Add analytics endpoints to youtube.py**

Append to `app/api/routes/youtube.py`:

```python
from pydantic import BaseModel
from app.services.youtube_analytics import YouTubeAnalytics
from app.services.youtube_ai_analyst import YouTubeAIAnalyst


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
    # Collect all YouTube data
    channel = await _analytics.get_channel_stats(data.access_token)
    videos = await _analytics.get_video_metrics(data.access_token, data.video_ids)
    demographics = await _analytics.get_demographics(data.access_token)
    traffic = await _analytics.get_traffic_sources(data.access_token)
    revenue = await _analytics.get_revenue_data(data.access_token)
    retention = await _analytics.get_retention_curve(data.access_token, videos[0].video_id if videos else "")

    # Build data dict for AI
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

    # Generate AI analysis
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_routes/test_youtube_analytics.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/routes/youtube.py tests/test_routes/test_youtube_analytics.py
git commit -m "feat(youtube): add 8 analytics API endpoints"
```

---

### Task 5: Frontend API Client

**Files:**
- Create: `frontend/src/api/youtube.ts`

**Interfaces:**
- Produces: TypeScript types and API functions for YouTube analytics

- [ ] **Step 1: Create frontend API client**

```typescript
// frontend/src/api/youtube.ts
import { apiClient } from "./client";

export interface ChannelStats {
  subscriber_count: number;
  total_view_count: number;
  total_watch_time_minutes: number;
  video_count: number;
  channel_name: string;
  thumbnail_url: string;
}

export interface VideoMetrics {
  video_id: string;
  title: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  average_view_duration_seconds: number;
  average_view_percentage: number;
  click_through_rate: number;
  published_at: string;
}

export interface Demographics {
  age_groups: Record<string, number>;
  gender: Record<string, number>;
  geography: { country: string; views: number }[];
}

export interface TrafficSource {
  source: string;
  views: number;
  percentage: number;
}

export interface RevenueData {
  estimated_revenue: number;
  estimated_cpm: number;
  estimated_rpm: number;
  monthly_revenue: { month: string; revenue: number }[];
}

export interface RetentionPoint {
  second: number;
  retention_percentage: number;
}

export interface AnalysisReport {
  summary: string;
  trends: string[];
  recommendations: string[];
  growth_predictions: Record<string, string>;
  top_performing: { title: string; reason: string }[];
  improvement_areas: string[];
  charts_data: Record<string, unknown>;
  generated_at: string;
  data_freshness: string;
}

export const youtubeApi = {
  async getChannelStats(token: string | null): Promise<ChannelStats> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await apiClient.get(`/youtube/analytics/channel${params}`);
    return resp.data;
  },

  async getVideoMetrics(token: string | null, videoIds?: string[]): Promise<VideoMetrics[]> {
    const params = new URLSearchParams();
    if (token) params.set("access_token", token);
    if (videoIds) params.set("video_ids", videoIds.join(","));
    const resp = await apiClient.get(`/youtube/analytics/videos?${params}`);
    return resp.data;
  },

  async getDemographics(token: string | null): Promise<Demographics> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await apiClient.get(`/youtube/analytics/demographics${params}`);
    return resp.data;
  },

  async getTrafficSources(token: string | null): Promise<TrafficSource[]> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await apiClient.get(`/youtube/analytics/traffic${params}`);
    return resp.data;
  },

  async getRevenue(token: string | null): Promise<RevenueData> {
    const params = token ? `?access_token=${token}` : "";
    const resp = await apiClient.get(`/youtube/analytics/revenue${params}`);
    return resp.data;
  },

  async getRetention(token: string | null, videoId: string): Promise<RetentionPoint[]> {
    const params = new URLSearchParams();
    if (token) params.set("access_token", token);
    params.set("video_id", videoId);
    const resp = await apiClient.get(`/youtube/analytics/retention?${params}`);
    return resp.data;
  },

  async getRealtimeViews(token: string | null, hours?: number): Promise<{ timestamp: string; views: number }[]> {
    const params = new URLSearchParams();
    if (token) params.set("access_token", token);
    if (hours) params.set("hours", String(hours));
    const resp = await apiClient.get(`/youtube/analytics/realtime?${params}`);
    return resp.data;
  },

  async analyze(token: string | null, provider: string = "groq", videoIds?: string[]): Promise<AnalysisReport> {
    const resp = await apiClient.post("/youtube/analyze", {
      access_token: token,
      ai_provider: provider,
      video_ids: videoIds,
    });
    return resp.data;
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/youtube.ts
git commit -m "feat(youtube): add frontend API client for analytics"
```

---

### Task 6: Frontend YouTube Components

**Files:**
- Create: `frontend/src/components/youtube/YouTubeConnect.tsx`
- Create: `frontend/src/components/youtube/YouTubeDashboard.tsx`
- Create: `frontend/src/components/youtube/YouTubeAIReport.tsx`
- Create: `frontend/src/components/youtube/index.ts`

**Interfaces:**
- Consumes: `youtubeApi` from Task 5
- Produces: React components for YouTube analytics UI

- [ ] **Step 1: Create YouTubeConnect component**

```tsx
// frontend/src/components/youtube/YouTubeConnect.tsx
import { useState } from "react";

interface YouTubeConnectProps {
  onConnect: (token: string | null) => void;
  connected: boolean;
}

export function YouTubeConnect({ onConnect, connected }: YouTubeConnectProps) {
  const [token, setToken] = useState("");

  return (
    <div style={{ padding: "16px", borderBottom: "1px solid #333" }}>
      <h3 style={{ color: "#fff", marginBottom: "8px" }}>YouTube Studio</h3>
      {connected ? (
        <div style={{ color: "#4ade80" }}>
          ✓ Connected to YouTube Analytics
          <button
            onClick={() => onConnect(null)}
            style={{ marginLeft: "12px", padding: "4px 8px", background: "#ef4444", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
          >
            Disconnect
          </button>
        </div>
      ) : (
        <div>
          <input
            type="password"
            placeholder="YouTube Access Token (leave empty for demo)"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            style={{ width: "100%", padding: "8px", marginBottom: "8px", background: "#1a1a1a", color: "#fff", border: "1px solid #444", borderRadius: "4px" }}
          />
          <button
            onClick={() => onConnect(token || null)}
            style={{ width: "100%", padding: "8px", background: "#3b82f6", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
          >
            Connect YouTube
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create YouTubeDashboard component**

```tsx
// frontend/src/components/youtube/YouTubeDashboard.tsx
import type { ChannelStats, VideoMetrics } from "../../api/youtube";

interface YouTubeDashboardProps {
  stats: ChannelStats | null;
  videos: VideoMetrics[];
}

export function YouTubeDashboard({ stats, videos }: YouTubeDashboardProps) {
  if (!stats) return null;

  const formatNumber = (n: number) => n.toLocaleString();
  const formatDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <div style={{ padding: "16px" }}>
      <h3 style={{ color: "#fff", marginBottom: "12px" }}>Channel Overview</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "16px" }}>
        {[
          { label: "Subscribers", value: formatNumber(stats.subscriber_count) },
          { label: "Total Views", value: formatNumber(stats.total_view_count) },
          { label: "Watch Time", value: formatDuration(stats.total_watch_time_minutes * 60) },
          { label: "Videos", value: String(stats.video_count) },
        ].map((item) => (
          <div key={item.label} style={{ background: "#1a1a1a", padding: "12px", borderRadius: "8px", border: "1px solid #333" }}>
            <div style={{ color: "#888", fontSize: "12px" }}>{item.label}</div>
            <div style={{ color: "#fff", fontSize: "20px", fontWeight: "bold" }}>{item.value}</div>
          </div>
        ))}
      </div>

      <h3 style={{ color: "#fff", marginBottom: "12px" }}>Top Videos</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {videos.slice(0, 5).map((v) => (
          <div key={v.video_id} style={{ background: "#1a1a1a", padding: "12px", borderRadius: "8px", border: "1px solid #333", display: "flex", justifyContent: "space-between" }}>
            <div>
              <div style={{ color: "#fff", fontWeight: "bold" }}>{v.title}</div>
              <div style={{ color: "#888", fontSize: "12px" }}>
                {formatNumber(v.view_count)} views · {formatDuration(v.average_view_duration_seconds)} avg · {v.click_through_rate.toFixed(1)}% CTR
              </div>
            </div>
            <div style={{ color: "#4ade80", fontSize: "12px" }}>
              {v.average_view_percentage.toFixed(0)}% watched
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create YouTubeAIReport component**

```tsx
// frontend/src/components/youtube/YouTubeAIReport.tsx
import type { AnalysisReport } from "../../api/youtube";

interface YouTubeAIReportProps {
  report: AnalysisReport | null;
  onAnalyze: () => void;
  loading: boolean;
  provider: string;
  onProviderChange: (p: string) => void;
}

export function YouTubeAIReport({ report, onAnalyze, loading, provider, onProviderChange }: YouTubeAIReportProps) {
  return (
    <div style={{ padding: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ color: "#fff", margin: 0 }}>AI Analysis</h3>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <select
            value={provider}
            onChange={(e) => onProviderChange(e.target.value)}
            style={{ padding: "6px 12px", background: "#1a1a1a", color: "#fff", border: "1px solid #444", borderRadius: "4px" }}
          >
            <option value="groq">Groq (Cloud)</option>
            <option value="ollama">Ollama (Local)</option>
          </select>
          <button
            onClick={onAnalyze}
            disabled={loading}
            style={{ padding: "8px 16px", background: loading ? "#666" : "#8b5cf6", color: "#fff", border: "none", borderRadius: "4px", cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? "Analyzing..." : "Analyze with AI"}
          </button>
        </div>
      </div>

      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
            <h4 style={{ color: "#8b5cf6", marginBottom: "8px" }}>Summary</h4>
            <p style={{ color: "#fff", margin: 0 }}>{report.summary}</p>
          </div>

          {report.trends.length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#8b5cf6", marginBottom: "8px" }}>Trends</h4>
              <ul style={{ color: "#fff", margin: 0, paddingLeft: "20px" }}>
                {report.trends.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}

          {report.recommendations.length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#4ade80", marginBottom: "8px" }}>Recommendations</h4>
              <ul style={{ color: "#fff", margin: 0, paddingLeft: "20px" }}>
                {report.recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {report.growth_predictions && Object.keys(report.growth_predictions).length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#fbbf24", marginBottom: "8px" }}>Growth Predictions</h4>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
                {Object.entries(report.growth_predictions).map(([key, value]) => (
                  <div key={key}>
                    <div style={{ color: "#888", fontSize: "12px" }}>{key.replace("_", " ")}</div>
                    <div style={{ color: "#fff", fontSize: "14px" }}>{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.improvement_areas.length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
              <h4 style={{ color: "#f87171", marginBottom: "8px" }}>Areas for Improvement</h4>
              <ul style={{ color: "#fff", margin: 0, paddingLeft: "20px" }}>
                {report.improvement_areas.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}

          <div style={{ color: "#666", fontSize: "12px", textAlign: "right" }}>
            Generated: {new Date(report.generated_at).toLocaleString()} · Data: {report.data_freshness}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Create barrel export**

```typescript
// frontend/src/components/youtube/index.ts
export { YouTubeConnect } from "./YouTubeConnect";
export { YouTubeDashboard } from "./YouTubeDashboard";
export { YouTubeAIReport } from "./YouTubeAIReport";
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/youtube/
git commit -m "feat(youtube): add YouTube analytics UI components"
```

---

### Task 7: Integrate YouTube Tab in App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: YouTube components from Task 6, `youtubeApi` from Task 5

- [ ] **Step 1: Add YouTube Analytics tab to sidebar**

Add to the sidebar tabs array in `App.tsx`:

```typescript
// In the tabs/sections array, add:
{ id: "youtube", label: "YouTube Analytics", icon: "📊" }
```

- [ ] **Step 2: Add YouTube Analytics section content**

Add the YouTube Analytics section rendering in the main content area:

```tsx
// YouTube Analytics section
{activeSection === "youtube" && (
  <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
    <YouTubeConnect onConnect={handleYouTubeConnect} connected={youtubeConnected} />
    {youtubeConnected && (
      <>
        <YouTubeDashboard stats={channelStats} videos={videos} />
        <YouTubeAIReport
          report={analysisReport}
          onAnalyze={handleAnalyze}
          loading={analyzing}
          provider={aiProvider}
          onProviderChange={setAiProvider}
        />
      </>
    )}
  </div>
)}
```

- [ ] **Step 3: Add state management**

Add to the component state:

```typescript
// YouTube state
const [youtubeConnected, setYoutubeConnected] = useState(false);
const [youtubeToken, setYoutubeToken] = useState<string | null>(null);
const [channelStats, setChannelStats] = useState<ChannelStats | null>(null);
const [videos, setVideos] = useState<VideoMetrics[]>([]);
const [analysisReport, setAnalysisReport] = useState<AnalysisReport | null>(null);
const [analyzing, setAnalyzing] = useState(false);
const [aiProvider, setAiProvider] = useState("groq");
```

- [ ] **Step 4: Add handler functions**

```typescript
const handleYouTubeConnect = async (token: string | null) => {
  setYoutubeToken(token);
  setYoutubeConnected(true);

  // Fetch initial data
  const stats = await youtubeApi.getChannelStats(token);
  setChannelStats(stats);

  const videoMetrics = await youtubeApi.getVideoMetrics(token);
  setVideos(videoMetrics);
};

const handleAnalyze = async () => {
  setAnalyzing(true);
  try {
    const report = await youtubeApi.analyze(youtubeToken, aiProvider);
    setAnalysisReport(report);
  } finally {
    setAnalyzing(false);
  }
};
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(youtube): integrate YouTube Analytics tab in main app"
```

---

### Task 8: Config and Settings

**Files:**
- Modify: `app/config.py`

**Interfaces:**
- Consumes: Existing config pattern
- Produces: YouTube Analytics API settings

- [ ] **Step 1: Add YouTube Analytics settings**

```python
# Add to app/config.py

# YouTube Analytics API
YOUTUBE_ANALYTICS_API_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
YOUTUBE_DATA_API_URL = "https://www.googleapis.com/youtube/v3"
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
```

- [ ] **Step 2: Commit**

```bash
git add app/config.py
git commit -m "feat(youtube): add YouTube Analytics API config"
```

---

### Task 9: Integration Tests

**Files:**
- Test: `tests/test_routes/test_youtube_integration.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: End-to-end integration test

- [ ] **Step 1: Write integration test**

```python
# tests/test_routes/test_youtube_integration.py
"""Integration test for YouTube analytics flow."""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_full_youtube_flow():
    """Test complete flow: connect → get stats → analyze."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Get channel stats (simulation mode)
        stats_resp = await client.get("/api/v1/youtube/analytics/channel")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["subscriber_count"] > 0

        # Step 2: Get video metrics
        videos_resp = await client.get("/api/v1/youtube/analytics/videos")
        assert videos_resp.status_code == 200
        videos = videos_resp.json()
        assert len(videos) > 0

        # Step 3: Get demographics
        demo_resp = await client.get("/api/v1/youtube/analytics/demographics")
        assert demo_resp.status_code == 200
        demo = demo_resp.json()
        assert "age_groups" in demo

        # Step 4: Get traffic sources
        traffic_resp = await client.get("/api/v1/youtube/analytics/traffic")
        assert traffic_resp.status_code == 200
        assert len(traffic_resp.json()) > 0

        # Step 5: Get revenue
        revenue_resp = await client.get("/api/v1/youtube/analytics/revenue")
        assert revenue_resp.status_code == 200
        revenue = revenue_resp.json()
        assert revenue["estimated_revenue"] > 0

        # Step 6: Full analysis
        analyze_resp = await client.post("/api/v1/youtube/analyze", json={
            "access_token": None,
            "ai_provider": "groq",
        })
        assert analyze_resp.status_code == 200
        report = analyze_resp.json()
        assert "summary" in report
        assert "recommendations" in report
```

- [ ] **Step 2: Run integration test**

Run: `.venv\Scripts\python.exe -m pytest tests/test_routes/test_youtube_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_routes/test_youtube_integration.py
git commit -m "test(youtube): add integration test for analytics flow"
```

---

### Task 10: Final Verification

**Files:**
- None (verification only)

**Interfaces:**
- None

- [ ] **Step 1: Run all backend tests**

Run: `.venv\Scripts\python.exe -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run frontend type check**

Run: `cd frontend; npx tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: Start server and verify endpoints**

Run: `.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001`
Verify: `curl http://localhost:8001/api/v1/youtube/analytics/channel` returns 200

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(youtube): complete YouTube Analytics + AI integration"
```
