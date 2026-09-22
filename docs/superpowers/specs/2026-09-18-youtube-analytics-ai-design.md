# YouTube Studio Analytics + AI Analysis Integration

## Overview

Integrate YouTube Analytics API v1 with Groq/Ollama AI to provide on-demand analysis reports of YouTube channel performance. Users connect their YouTube account via OAuth2 access token, and the system fetches real analytics data from YouTube Studio, then uses AI to generate insights, recommendations, and growth predictions.

## Goals

1. Fetch real YouTube Analytics data (not manual input)
2. AI-powered analysis with actionable recommendations
3. Support both Groq (cloud) and Ollama (local) as AI providers
4. On-demand report generation (user clicks "Analyze")
5. Full report: summary, trends, recommendations, predictions, charts data

## Architecture

```
Frontend (React)  →  FastAPI Routes  →  YouTube Analytics Service  →  Google API
                                        ↓
                                    AI Analyst  →  Groq / Ollama
                                        ↓
                                    AnalysisReport (JSON)
```

## Components

### 1. YouTube Analytics Service (`app/services/youtube_analytics.py`)

Communicates with YouTube Analytics API v1.

**Endpoints used:**
- `https://youtubeanalytics.googleapis.com/v2/reports` — main analytics queries
- `https://www.googleapis.com/youtube/v3/channels` — channel metadata

**Methods:**
```python
class YouTubeAnalytics:
    def get_channel_stats(access_token: str) -> ChannelStats
    def get_video_metrics(access_token: str, video_ids: list[str]) -> list[VideoMetrics]
    def get_demographics(access_token: str) -> Demographics
    def get_traffic_sources(access_token: str) -> list[TrafficSource]
    def get_revenue_data(access_token: str) -> RevenueData
    def get_retention_curve(access_token: str, video_id: str) -> list[RetentionPoint]
    def get_realtime_views(access_token: str, hours: int = 48) -> list[RealtimeView]
```

**Data models:**
```python
@dataclass
class ChannelStats:
    subscriber_count: int
    total_view_count: int
    total_watch_time_minutes: float
    video_count: int
    channel_name: str
    thumbnail_url: str

@dataclass
class VideoMetrics:
    video_id: str
    title: str
    view_count: int
    like_count: int
    comment_count: int
    average_view_duration_seconds: float
    average_view_percentage: float  # % watched
    click_through_rate: float
    published_at: str

@dataclass
class Demographics:
    age_groups: dict[str, float]  # {"18-24": 0.25, "25-34": 0.35, ...}
    gender: dict[str, float]      # {"male": 0.6, "female": 0.4}
    geography: list[dict]          # [{"country": "US", "views": 12000}, ...]

@dataclass
class TrafficSource:
    source: str    # "SEARCH", "SUGGESTED", "EXTERNAL", "DIRECT", etc.
    views: int
    percentage: float

@dataclass
class RevenueData:
    estimated_revenue: float
    estimated_cpm: float
    estimated_rpm: float
    monthly_revenue: list[dict]  # [{"month": "2026-01", "revenue": 120.50}, ...]

@dataclass
class RetentionPoint:
    second: int
    retention_percentage: float

@dataclass
class RealtimeView:
    timestamp: str
    views: int
```

**Error handling:**
- Retry with exponential backoff (3 attempts)
- Rate limiting (YouTube API: 10,000 units/day)
- Token expiry detection → clear error message
- Simulation mode when no token provided

### 2. AI Analysis Service (`app/services/youtube_ai_analyst.py`)

Takes raw YouTube data and generates structured analysis.

**Prompt structure:**
```
Eres un analista de YouTube experto. Analiza los siguientes datos de un canal de YouTube y genera un reporte completo en español.

Datos del Canal:
- Suscriptores: {subscriber_count}
- Views totales: {total_views}
- Watch time: {watch_hours} horas

Rendimiento de Videos:
{video_metrics_table}

Demografía:
{demographics_json}

Fuentes de Tráfico:
{traffic_sources_table}

Revenue:
{revenue_data}

Curva de Retención:
{retention_data}

Genera un reporte JSON con:
1. summary: Resumen ejecutivo (2-3 oraciones)
2. trends: Lista de tendencias detectadas (max 5)
3. recommendations: Lista de acciones recomendadas (max 5)
4. growth_predictions: Predicciones 3/6/12 meses
5. top_performing: Top 3 videos con mejor rendimiento
6. improvement_areas: Áreas de mejora (max 3)
7. charts_data: Datos para gráficos (views_over_time, demographics_pie, traffic_bar)
```

**AI Provider support:**
```python
class YouTubeAIAnalyst:
    def __init__(self, provider: str = "groq")  # "groq" or "ollama"
    
    async def analyze(self, youtube_data: dict) -> AnalysisReport
    
    async def _call_groq(self, prompt: str) -> str
    async def _call_ollama(self, prompt: str) -> str
    
    def _parse_report(self, response: str) -> AnalysisReport
```

**Groq config:** Uses existing `app/providers/groq.py` with `GROQ_API_KEY` env var.
**Ollama config:** Checks `http://localhost:11434` availability, falls back to Groq if unavailable.

### 3. API Routes (`app/api/routes/youtube.py`)

Extended with analytics endpoints.

**New endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/youtube/analytics/channel` | GET | Channel stats (subs, views, watch time) |
| `/youtube/analytics/videos` | GET | Video performance metrics |
| `/youtube/analytics/demographics` | GET | Audience demographics |
| `/youtube/analytics/traffic` | GET | Traffic sources |
| `/youtube/analytics/revenue` | GET | Revenue and CPM data |
| `/youtube/analytics/retention` | GET | Retention curve for a video |
| `/youtube/analytics/realtime` | GET | Real-time views (48h) |
| `/youtube/analyze` | POST | **Main endpoint**: fetch data + generate AI report |

**Request/Response models:**
```python
class YouTubeConnectRequest(BaseModel):
    access_token: str

class YouTubeAnalyzeRequest(BaseModel):
    access_token: str
    ai_provider: str = "groq"  # "groq" or "ollama"
    video_ids: list[str] | None = None  # Optional: specific videos to analyze

class AnalysisReportResponse(BaseModel):
    summary: str
    trends: list[str]
    recommendations: list[str]
    growth_predictions: dict
    top_performing: list[dict]
    improvement_areas: list[str]
    charts_data: dict
    generated_at: str
    data_freshness: str  # "realtime" or "cached"
```

### 4. Frontend — YouTube Analytics Tab

New tab in the sidebar (alongside Story Bible, QA Monitor, Analytics).

**Components:**
- `YouTubeConnect.tsx` — Access token input + connect button
- `YouTubeDashboard.tsx` — Channel stats cards (subs, views, watch time, revenue)
- `YouTubeVideos.tsx` — Table of video performance metrics
- `YouTubeDemographics.tsx` — Age/gender charts
- `YouTubeTraffic.tsx` — Traffic sources bar chart
- `YouTubeRetention.tsx` — Retention curve line chart
- `YouTubeAIReport.tsx` — AI analysis report display
- `YouTubeAnalyze.tsx` — "Analyze with AI" button + provider selector

**State management:**
```typescript
interface YouTubeState {
  connected: boolean;
  accessToken: string | null;
  channelStats: ChannelStats | null;
  videos: VideoMetrics[];
  demographics: Demographics | null;
  trafficSources: TrafficSource[];
  revenue: RevenueData | null;
  analysisReport: AnalysisReport | null;
  loading: boolean;
  error: string | null;
}
```

## Files to Create/Modify

**Create:**
- `app/services/youtube_analytics.py` — YouTube Analytics API client
- `app/services/youtube_ai_analyst.py` — AI analysis service
- `frontend/src/components/youtube/` — All YouTube analytics components

**Modify:**
- `app/api/routes/youtube.py` — Add analytics endpoints
- `app/config.py` — Add YouTube Analytics API settings
- `frontend/src/App.tsx` — Add YouTube Analytics tab
- `frontend/src/api/youtube.ts` — Frontend API client for YouTube analytics

## Testing

- Unit tests for `YouTubeAnalytics` methods (mock Google API responses)
- Unit tests for `YouTubeAIAnalyst` (mock LLM responses)
- Integration test for `/youtube/analyze` endpoint
- Frontend component tests for YouTube dashboard
- E2E test: connect YouTube → view stats → analyze with AI

## Security

- Access tokens stored in memory only (not persisted)
- Tokens passed via request body, not URL params
- Rate limiting on analytics endpoints
- No sensitive data in AI prompts (only aggregate metrics)

## Dependencies

- YouTube Analytics API v1 (Google)
- YouTube Data API v3 (Google) — for channel metadata
- Groq API (existing)
- Ollama (optional, local)
- httpx (existing)
