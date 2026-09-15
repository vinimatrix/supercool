"""Video Analyzer - Local first, NEMOTRON fallback."""

import base64
import json
from pathlib import Path

import httpx

from app.config import settings


class VideoAnalyzer:
    """Analyzes shots - local first, NEMOTRON fallback."""

    def __init__(self):
        self.api_key = settings.nvidia_api_key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
        self._local = None

    @property
    def local(self):
        if self._local is None:
            try:
                from app.services.local.coordinator import LocalVideoCoordinator
                self._local = LocalVideoCoordinator()
            except Exception as e:
                print(f"[VideoAnalyzer] Local coordinator init failed: {e}")
                self._local = None
        return self._local

    def is_available(self) -> bool:
        if self.local and self.local.is_available():
            return True
        return bool(self.api_key)

    async def analyze_shot(self, shot_info: dict, context: str = "") -> dict:
        if self.local and self.local.is_available():
            try:
                local_result = await self.local.analyze_shot(shot_info, context)
                if local_result["decision"]["status"] != "NEEDS_ANALYSIS":
                    return self._map_local_to_format(local_result)
            except Exception as e:
                print(f"[VideoAnalyzer] Local analysis failed: {e}")
        if self.api_key:
            video_path = shot_info.get("video_path")
            if video_path and Path(video_path).exists():
                result = await self._analyze_with_video(video_path, shot_info, context)
                if result.get("emotion") != "neutral":
                    return result
            return await self._analyze_text_only(shot_info, context)
        return self._empty_analysis()

    def _map_local_to_format(self, local_result: dict) -> dict:
        decision = local_result["decision"]
        layer2 = local_result.get("layer2", {})
        return {
            "emotion": layer2.get("mood_suggestion", "neutral"),
            "camera": "static",
            "dialogue": "dialogue" in decision.get("layer1_summary", "").lower(),
            "action_level": 0.5,
            "grade": "cinematic",
            "transitions": ["cut"],
            "audio": layer2.get("creative_notes", "Ambient, minimal"),
            "local_analysis": {
                "status": decision["status"],
                "similarity_score": decision.get("similarity_score"),
                "threshold": decision.get("threshold"),
            },
        }

    async def _analyze_with_video(self, video_path, shot_info, context):
        try:
            path = Path(video_path)
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 20:
                print(f"[NEMOTRON] Video too large: {size_mb:.1f}MB")
                return self._empty_analysis()
            with open(path, "rb") as f:
                video_b64 = base64.b64encode(f.read()).decode()
            prompt = self._build_prompt(shot_info, context, has_video=True)
            payload = {
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}},
                ]}],
                "model": self.model,
                "max_tokens": 2048,
                "reasoning_budget": 1024,
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.95,
                "chat_template_kwargs": {"enable_thinking": True},
            }
            return await self._call_api(payload)
        except Exception as e:
            print(f"[NEMOTRON] Video error: {e}")
            return self._empty_analysis()

    async def _analyze_text_only(self, shot_info, context):
        try:
            prompt = self._build_prompt(shot_info, context, has_video=False)
            payload = {
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                "model": self.model,
                "max_tokens": 2048,
                "reasoning_budget": 1024,
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.95,
                "chat_template_kwargs": {"enable_thinking": True},
            }
            return await self._call_api(payload)
        except Exception as e:
            print(f"[NEMOTRON] Text error: {e}")
            return self._empty_analysis()

    async def _call_api(self, payload):
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            if response.status_code != 200:
                print(f"[NEMOTRON] Error {response.status_code}: {response.text[:200]}")
                return self._empty_analysis()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)

    def _build_prompt(self, shot_info, context, has_video):
        prompt_text = shot_info.get("prompt_text", "")
        duration = shot_info.get("duration", 10)
        source = "video" if has_video else "shot description"
        return f"""Analyze this {source} for cinematic editing.

Shot: {prompt_text}
Duration: {duration}s
Context: {context if context else "None"}

Return ONLY this JSON, no other text:
{{
    "emotion": "tense|dramatic|action|calm|mysterious",
    "camera": "static|dynamic|close-up|tracking",
    "dialogue": true/false,
    "action_level": 0.0-1.0,
    "grade": "neutral|warm|cold|cinematic|noir|action|dramatic",
    "transitions": ["crossfade|whip_pan|match_cut|cut"],
    "audio": "audio treatment"
}}"""

    def _parse_response(self, content):
        try:
            content = content.strip()
            if "{" in content:
                start = content.rfind("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    data = json.loads(json_str)
                    def first_option(val):
                        if isinstance(val, str) and "|" in val:
                            return val.split("|")[0]
                        return val
                    return {
                        "emotion": first_option(data.get("emotion", "neutral")),
                        "camera": first_option(data.get("camera", "static")),
                        "dialogue": data.get("dialogue", False),
                        "action_level": max(0.0, min(1.0, float(data.get("action_level", 0.5)))),
                        "grade": first_option(data.get("grade", "cinematic")),
                        "transitions": data.get("transitions", ["cut"]),
                        "audio": data.get("audio", "Ambient, minimal"),
                    }
        except Exception as e:
            print(f"[NEMOTRON] Parse error: {e}")
        return self._empty_analysis()

    def _empty_analysis(self):
        return {
            "emotion": "neutral",
            "camera": "static",
            "dialogue": False,
            "action_level": 0.5,
            "grade": "cinematic",
            "transitions": ["cut"],
            "audio": "Ambient, minimal",
        }


video_analyzer = VideoAnalyzer()
