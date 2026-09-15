"""Tests for VideoAnalyzer integration."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestVideoAnalyzerIntegration:
    def test_is_available(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        analyzer._local = MagicMock()
        analyzer._local.is_available.return_value = False
        assert isinstance(analyzer.is_available(), bool)

    @pytest.mark.asyncio
    async def test_analyze_shot_returns_dict(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        analyzer._local = MagicMock()
        analyzer._local.is_available.return_value = False
        shot = {"id": "test", "prompt_text": "test", "duration": 10}
        with patch.object(analyzer, '_call_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "emotion": "calm",
                "camera": "static",
                "dialogue": False,
                "action_level": 0.3,
                "grade": "cinematic",
                "transitions": ["cut"],
                "audio": "Ambient",
            }
            result = await analyzer.analyze_shot(shot, "context")
            assert isinstance(result, dict)
            assert "emotion" in result

    def test_has_local_property(self):
        from app.services.video_analyzer import VideoAnalyzer
        assert hasattr(VideoAnalyzer, 'local')

    @pytest.mark.asyncio
    async def test_uses_local_first_when_available(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        
        # Mock local coordinator
        mock_local = MagicMock()
        mock_local.is_available.return_value = True
        mock_local.analyze_shot = AsyncMock(return_value={
            "decision": {
                "status": "SIMILAR",
                "similarity_score": 0.8,
                "threshold": 0.7,
                "layer1_summary": "dialogue scene"
            },
            "layer2": {
                "mood_suggestion": "tense",
                "creative_notes": "Ambient tension"
            }
        })
        analyzer._local = mock_local
        
        shot = {"id": "test", "prompt_text": "test", "duration": 10}
        result = await analyzer.analyze_shot(shot, "context")
        
        # Should call local first
        mock_local.analyze_shot.assert_called_once()
        # Should not call NEMOTRON
        assert "emotion" in result
        assert result["emotion"] == "tense"

    @pytest.mark.asyncio
    async def test_falls_back_to_nemotron_when_local_returns_needs_analysis(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        
        # Mock local coordinator that returns NEEDS_ANALYSIS
        mock_local = MagicMock()
        mock_local.is_available.return_value = True
        mock_local.analyze_shot = AsyncMock(return_value={
            "decision": {
                "status": "NEEDS_ANALYSIS",
                "similarity_score": 0.3,
                "threshold": 0.7,
                "layer1_summary": "unknown scene"
            },
            "layer2": {}
        })
        analyzer._local = mock_local
        
        # Mock NEMOTRON response
        with patch.object(analyzer, '_call_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "emotion": "dramatic",
                "camera": "dynamic",
                "dialogue": True,
                "action_level": 0.8,
                "grade": "cinematic",
                "transitions": ["crossfade"],
                "audio": "Dramatic score"
            }
            
            shot = {"id": "test", "prompt_text": "test", "duration": 10}
            result = await analyzer.analyze_shot(shot, "context")
            
            # Should call local first
            mock_local.analyze_shot.assert_called_once()
            # Should fall back to NEMOTRON
            mock_api.assert_called_once()
            assert result["emotion"] == "dramatic"

    def test_map_local_to_format(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        
        local_result = {
            "decision": {
                "status": "SIMILAR",
                "similarity_score": 0.8,
                "threshold": 0.7,
                "layer1_summary": "dialogue scene"
            },
            "layer2": {
                "mood_suggestion": "tense",
                "creative_notes": "Ambient tension"
            }
        }
        
        mapped = analyzer._map_local_to_format(local_result)
        assert mapped["emotion"] == "tense"
        assert mapped["camera"] == "static"
        assert mapped["dialogue"] is True
        assert mapped["local_analysis"]["status"] == "SIMILAR"