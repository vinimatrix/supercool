"""Integration tests for local video analyzer."""
import pytest
from unittest.mock import patch


def _patch_nemotron():
    return patch(
        "app.services.local.coordinator.VideoAnalyzer",
        return_value=type("FakeNemotron", (), {"is_available": lambda self: False})(),
    )


class TestLocalAnalyzerIntegration:
    def test_coordinator_init(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            assert coordinator is not None

    def test_video_analyzer_uses_local(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        assert analyzer._local is not None or analyzer.api_key

    def test_config_settings_exist(self):
        from app.config import settings
        assert hasattr(settings, "clip_threshold_dialogue")
        assert hasattr(settings, "clip_threshold_action")
        assert hasattr(settings, "local_models_enabled")
        assert hasattr(settings, "qwen_backend")

    @pytest.mark.asyncio
    async def test_empty_keyframes_handled(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            shot = {"id": "test", "prompt_text": "test", "duration": 10, "video_path": None}
            result = await coordinator.analyze_shot(shot)
            assert result["decision"]["status"] == "NEEDS_ANALYSIS"

    def test_coordinator_has_analyzers(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            assert coordinator.clip is not None
            assert coordinator.florence is not None
            assert coordinator.qwen is not None
            assert coordinator.nemotron is not None

    def test_video_analyzer_init(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        assert analyzer.base_url == "https://integrate.api.nvidia.com/v1"
        assert "nemotron" in analyzer.model

    def test_clip_analyzer_init(self):
        from app.services.local.clip_analyzer import CLIPAnalyzer
        clip = CLIPAnalyzer()
        assert clip.is_available() is False

    def test_florence_analyzer_init(self):
        from app.services.local.florence_analyzer import FlorenceAnalyzer
        florence = FlorenceAnalyzer()
        assert florence.is_available() is False

    def test_qwen_analyzer_init(self):
        from app.services.local.qwen_analyzer import QwenAnalyzer
        qwen = QwenAnalyzer()
        assert qwen.is_available() is False

    def test_coordinator_availability(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            assert isinstance(coordinator.is_available(), bool)

    def test_video_analyzer_empty_analysis(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        result = analyzer._empty_analysis()
        assert result["emotion"] == "neutral"
        assert result["camera"] == "static"
        assert result["action_level"] == 0.5

    def test_video_analyzer_parse_response(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        json_str = '{"emotion": "tense", "camera": "dynamic", "dialogue": true, "action_level": 0.8, "grade": "cinematic", "transitions": ["cut"], "audio": "dramatic score"}'
        result = analyzer._parse_response(json_str)
        assert result["emotion"] == "tense"
        assert result["camera"] == "dynamic"
        assert result["dialogue"] is True

    def test_qwen_empty_result(self):
        from app.services.local.qwen_analyzer import QwenAnalyzer
        qwen = QwenAnalyzer()
        result = qwen._empty_result()
        assert result["lighting_assessment"] == "neutral"
        assert result["mood_suggestion"] == "neutral"

    def test_clip_thresholds(self):
        from app.config import settings
        assert settings.clip_threshold_dialogue == 0.78
        assert settings.clip_threshold_action == 0.70

    def test_video_analyzer_prompt_building(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        shot = {"prompt_text": "hero walks", "duration": 5}
        prompt = analyzer._build_prompt(shot, "context", has_video=True)
        assert "hero walks" in prompt
        assert "5s" in prompt
        assert "video" in prompt

    def test_florence_key_props(self):
        from app.services.local.florence_analyzer import FlorenceAnalyzer
        assert "sword" in FlorenceAnalyzer.KEY_PROPS
        assert "cloak" in FlorenceAnalyzer.KEY_PROPS

    @pytest.mark.asyncio
    async def test_coordinator_nonexistent_video(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            shot = {"id": "test", "prompt_text": "action scene", "duration": 10, "video_path": "/nonexistent/video.mp4"}
            result = await coordinator.analyze_shot(shot)
            assert result["decision"]["status"] == "NEEDS_ANALYSIS"

    @pytest.mark.asyncio
    async def test_analyze_shot_structure(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            shot = {"id": "test", "prompt_text": "test", "duration": 5, "video_path": None}
            result = await coordinator.analyze_shot(shot)
            assert "layer1" in result
            assert "layer2" in result
            assert "decision" in result
            assert "status" in result["decision"]

    def test_make_decision_needs_analysis_when_no_score(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            layer1 = {"error": "no_video"}
            layer2 = {"skipped": True}
            shot = {"prompt_text": "dialogue scene", "duration": 10}
            decision = coordinator._make_decision(layer1, layer2, shot)
            assert decision["status"] == "NEEDS_ANALYSIS"

    def test_make_decision_approved_above_threshold(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            layer1 = {"similarity_score": 0.9, "caption": "hero"}
            layer2 = {}
            shot = {"prompt_text": "dialogue scene", "duration": 10}
            decision = coordinator._make_decision(layer1, layer2, shot)
            assert decision["status"] == "APPROVED_FOR_EDIT"

    def test_make_decision_re_render_below_threshold(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            layer1 = {"similarity_score": 0.3, "caption": "off model"}
            layer2 = {}
            shot = {"prompt_text": "dialogue scene", "duration": 10}
            decision = coordinator._make_decision(layer1, layer2, shot)
            assert decision["status"] == "RE-RENDER_REQUIRED"

    def test_make_decision_adjust_color_bad_lighting(self):
        with _patch_nemotron():
            from app.services.local.coordinator import LocalVideoCoordinator
            coordinator = LocalVideoCoordinator()
            layer1 = {"similarity_score": 0.9, "caption": "hero"}
            layer2 = {"lighting_assessment": "incorrect"}
            shot = {"prompt_text": "dialogue scene", "duration": 10}
            decision = coordinator._make_decision(layer1, layer2, shot)
            assert decision["status"] == "ADJUST_COLOR"

    def test_action_threshold_lower_than_dialogue(self):
        from app.config import settings
        assert settings.clip_threshold_action < settings.clip_threshold_dialogue
