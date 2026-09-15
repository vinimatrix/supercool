"""Tests for CLIP Analyzer."""
from unittest.mock import patch


class TestCLIPAnalyzer:
    def test_is_available_no_model(self):
        from app.services.local.clip_analyzer import CLIPAnalyzer
        analyzer = CLIPAnalyzer()
        assert isinstance(analyzer.is_available(), bool)

    def test_extract_keyframe_returns_list(self, tmp_path):
        from app.services.local.clip_analyzer import CLIPAnalyzer
        analyzer = CLIPAnalyzer()
        video_path = tmp_path / "test.mp4"
        video_path.touch()
        with patch("cv2.VideoCapture") as mock_cap:
            mock_cap.return_value.get.return_value = 0
            mock_cap.return_value.read.return_value = (False, None)
            result = analyzer.extract_keyframe(str(video_path))
            assert isinstance(result, list)

    def test_compute_similarity_returns_float(self):
        from app.services.local.clip_analyzer import CLIPAnalyzer
        analyzer = CLIPAnalyzer()
        result = analyzer.compute_similarity("dummy1.jpg", "dummy2.jpg")
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
