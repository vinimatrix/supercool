"""Tests for Local Video Coordinator."""
import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestLocalVideoCoordinator:
    def test_is_available(self):
        from app.services.local.coordinator import LocalVideoCoordinator
        coordinator = LocalVideoCoordinator()
        assert isinstance(coordinator.is_available(), bool)

    @pytest.mark.asyncio
    async def test_analyze_shot_returns_dict(self):
        from app.services.local.coordinator import LocalVideoCoordinator
        coordinator = LocalVideoCoordinator()
        shot = {"id": "test", "prompt_text": "Test shot", "duration": 10, "video_path": None}
        result = await coordinator.analyze_shot(shot, "test context")
        assert isinstance(result, dict)
        assert "layer1" in result
        assert "layer2" in result
        assert "decision" in result
