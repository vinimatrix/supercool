"""Integration test for YouTube analytics flow."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app


@pytest.mark.asyncio
async def test_full_youtube_flow():
    """Test complete flow: connect → get stats → analyze."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
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
