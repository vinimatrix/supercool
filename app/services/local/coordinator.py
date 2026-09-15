"""Local Video Coordinator - Two-layer evaluation with NEMOTRON fallback."""

import asyncio
from pathlib import Path
from app.config import settings
from app.services.local.clip_analyzer import CLIPAnalyzer
from app.services.local.florence_analyzer import FlorenceAnalyzer
from app.services.local.qwen_analyzer import QwenAnalyzer
from app.services.video_analyzer import VideoAnalyzer


class LocalVideoCoordinator:
    """Two-layer evaluation with NEMOTRON fallback."""

    def __init__(self):
        self.clip = CLIPAnalyzer()
        self.florence = FlorenceAnalyzer()
        self.qwen = QwenAnalyzer()
        self.nemotron = VideoAnalyzer()
        if settings.local_models_enabled:
            self._load_models()

    def _load_models(self):
        try:
            self.clip.load_model()
        except Exception as e:
            print(f"[Coordinator] CLIP load failed: {e}")
        try:
            self.florence.load_model()
        except Exception as e:
            print(f"[Coordinator] Florence load failed: {e}")

    def is_available(self) -> bool:
        return (
            self.clip.is_available()
            or self.florence.is_available()
            or self.qwen.is_available()
            or self.nemotron.is_available()
        )

    async def analyze_shot(self, shot: dict, scene_context: str = "") -> dict:
        layer1 = self._run_layer1(shot)
        layer2 = self._run_layer2(shot, layer1)
        decision = self._make_decision(layer1, layer2, shot)
        if decision["status"] == "NEEDS_ANALYSIS" and self.nemotron.is_available():
            nemotron_result = await self.nemotron.analyze_shot(shot, scene_context)
            decision["nemotron_fallback"] = nemotron_result
        return {"layer1": layer1, "layer2": layer2, "decision": decision}

    def _run_layer1(self, shot):
        video_path = shot.get("video_path")
        if not video_path or not Path(video_path).exists():
            return {"error": "no_video"}
        keyframes = self.clip.extract_keyframe(video_path)
        reference = self._get_reference(shot, keyframes)
        clip_result = self.clip.analyze_shot(video_path, reference)
        florence_result = self.florence.analyze_shot(keyframes, shot)
        self.florence._cleanup_vram()
        return {**clip_result, **florence_result}

    def _run_layer2(self, shot, layer1):
        if not self.qwen.is_available():
            return {"skipped": True, "reason": "qwen_not_available"}
        video_path = shot.get("video_path")
        if not video_path or not Path(video_path).exists():
            return {"skipped": True, "reason": "no_video"}
        keyframes = self.clip.extract_keyframe(video_path)
        return self.qwen.analyze_shot(keyframes, shot, layer1, {})

    def _get_reference(self, shot, keyframes):
        shot_id = shot.get("id", "unknown")
        manual = Path("workspace/references") / f"{shot_id}.jpg"
        if manual.exists():
            return str(manual)
        if keyframes:
            return keyframes[0]
        return None

    def _make_decision(self, layer1, layer2, shot):
        score = layer1.get("similarity_score")
        desc = shot.get("prompt_text", "").lower()
        is_action = any(w in desc for w in ["slash", "strike", "combat", "fight"])
        threshold = settings.clip_threshold_action if is_action else settings.clip_threshold_dialogue
        if score is None:
            status = "NEEDS_ANALYSIS"
        elif score >= threshold:
            status = "APPROVED_FOR_EDIT"
        else:
            status = "RE-RENDER_REQUIRED"
        if layer2.get("lighting_assessment") == "incorrect":
            status = "ADJUST_COLOR"
        return {
            "status": status,
            "similarity_score": score,
            "threshold": threshold,
            "layer1_summary": layer1.get("caption", ""),
            "layer2_summary": layer2.get("narrative_analysis", ""),
        }
