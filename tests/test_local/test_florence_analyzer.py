"""Tests for Florence Analyzer."""


class TestFlorenceAnalyzer:
    def test_is_available_no_model(self):
        from app.services.local.florence_analyzer import FlorenceAnalyzer
        analyzer = FlorenceAnalyzer()
        assert isinstance(analyzer.is_available(), bool)

    def test_analyze_shot_returns_dict(self):
        from app.services.local.florence_analyzer import FlorenceAnalyzer
        analyzer = FlorenceAnalyzer()
        result = analyzer.analyze_shot(["dummy.jpg"], {"prompt_text": "test"})
        assert isinstance(result, dict)
        assert "objects_detected" in result
        assert "caption" in result
        assert "key_props_present" in result