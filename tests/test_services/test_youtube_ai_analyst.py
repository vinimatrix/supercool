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
