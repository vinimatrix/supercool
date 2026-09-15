"""Tests for Qwen Analyzer."""
import pytest
from unittest.mock import patch, MagicMock


class TestQwenAnalyzer:
    def test_is_available_no_backend(self):
        from app.services.local.qwen_analyzer import QwenAnalyzer
        analyzer = QwenAnalyzer()
        assert isinstance(analyzer.is_available(), bool)

    def test_analyze_shot_returns_dict(self):
        from app.services.local.qwen_analyzer import QwenAnalyzer
        analyzer = QwenAnalyzer()
        result = analyzer.analyze_shot(
            ["dummy.jpg"],
            {"prompt_text": "test", "duration": 10},
            {"similarity_score": 0.8},
            {"caption": "test caption"},
        )
        assert isinstance(result, dict)
        assert "narrative_analysis" in result
