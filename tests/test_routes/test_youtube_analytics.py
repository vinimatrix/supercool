"""Tests for YouTube analytics API routes."""

import pytest


@pytest.mark.asyncio
async def test_channel_stats_simulation(client):
    resp = await client.get("/api/v1/youtube/analytics/channel")
    assert resp.status_code == 200
    data = resp.json()
    assert "subscriber_count" in data
    assert data["channel_name"] == "Simulated Channel"


@pytest.mark.asyncio
async def test_videos_simulation(client):
    resp = await client.get("/api/v1/youtube/analytics/videos")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0


@pytest.mark.asyncio
async def test_demographics_simulation(client):
    resp = await client.get("/api/v1/youtube/analytics/demographics")
    assert resp.status_code == 200
    data = resp.json()
    assert "age_groups" in data
    assert "gender" in data
    assert "geography" in data


@pytest.mark.asyncio
async def test_traffic_sources_simulation(client):
    resp = await client.get("/api/v1/youtube/analytics/traffic")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0


@pytest.mark.asyncio
async def test_revenue_simulation(client):
    resp = await client.get("/api/v1/youtube/analytics/revenue")
    assert resp.status_code == 200
    data = resp.json()
    assert "estimated_revenue" in data
    assert "estimated_cpm" in data


@pytest.mark.asyncio
async def test_retention_simulation(client):
    resp = await client.get("/api/v1/youtube/analytics/retention")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_realtime_simulation(client):
    resp = await client.get("/api/v1/youtube/analytics/realtime")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_analyze_endpoint(client):
    resp = await client.post("/api/v1/youtube/analyze", json={
        "access_token": None,
        "ai_provider": "groq",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "recommendations" in data
