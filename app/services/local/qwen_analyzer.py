"""Qwen Analyzer - Qualitative narrative analysis using Qwen2-VL 2B."""

import json
import base64
import subprocess
from pathlib import Path
import httpx


class QwenAnalyzer:
    """Analyzes shots using Qwen2-VL 2B (CPU, ~1.8-2.5GB RAM)."""

    PROMPT_TEMPLATE = """You are a film director analyzing a shot for editing.

Shot description: {description}
Duration: {duration}s
CLIP similarity score: {similarity}
Objects detected: {objects}
Caption: {caption}

Analyze this shot and provide:
1. Lighting assessment (dark/bright/golden_hour/neutral)
2. Costume verification (correct/incorrect/unclear)
3. Mood suggestion (tense/dramatic/action/calm/mysterious)
4. Creative notes for the editor

Respond in this JSON format:
{{
    "narrative_analysis": "string",
    "lighting_assessment": "dark|bright|golden_hour|neutral",
    "costume_check": "correct|incorrect|unclear",
    "mood_suggestion": "tense|dramatic|action|calm|mysterious",
    "creative_notes": "string"
}}"""

    def __init__(self):
        self.backend = None
        self.model = None
        self._detect_backend()

    def _detect_backend(self):
        try:
            result = subprocess.run(
                ["which", "ollama"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.backend = "ollama"
                print("[Qwen] Detected Ollama backend")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        try:
            import llama_cpp
            self.backend = "llama_cpp"
            print("[Qwen] Detected llama-cpp-python backend")
            return
        except ImportError:
            pass
        self.backend = None
        print("[Qwen] No backend available (install Ollama or llama-cpp-python)")

    def is_available(self) -> bool:
        return self.backend is not None

    def analyze_shot(self, keyframes, shot_info, clip_result, florence_result):
        if not self.is_available():
            return self._empty_result()
        prompt = self.PROMPT_TEMPLATE.format(
            description=shot_info.get("prompt_text", "Unknown"),
            duration=shot_info.get("duration", 0),
            similarity=clip_result.get("similarity_score", "N/A"),
            objects=", ".join(florence_result.get("objects_detected", [])),
            caption=florence_result.get("caption", "No caption"),
        )
        try:
            if self.backend == "ollama":
                response = self._call_ollama(prompt, keyframes[:3])
            elif self.backend == "llama_cpp":
                response = self._call_llama_cpp(prompt)
            else:
                return self._empty_result()
            return self._parse_response(response)
        except Exception as e:
            print(f"[Qwen] Analysis error: {e}")
            return self._empty_result()

    def _call_ollama(self, prompt, images):
        images_b64 = []
        for img_path in images:
            if Path(img_path).exists():
                with open(img_path, "rb") as f:
                    images_b64.append(base64.b64encode(f.read()).decode())
        payload = {
            "model": "qwen2.5-vl:2b",
            "prompt": prompt,
            "images": images_b64,
            "stream": False,
            "options": {"temperature": 0.3, "num_ctx": 4096},
        }
        with httpx.Client(timeout=120) as client:
            response = client.post("http://localhost:11434/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")

    def _call_llama_cpp(self, prompt):
        try:
            from llama_cpp import Llama
            model = Llama(model_path="models/qwen2.5-vl-2b.gguf", n_ctx=4096)
            output = model(prompt, max_tokens=512, temperature=0.3)
            return output["choices"][0]["text"]
        except Exception as e:
            print(f"[Qwen] llama-cpp error: {e}")
            return ""

    def _parse_response(self, response):
        try:
            if "{" in response:
                start = response.rfind("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return self._empty_result()

    def _empty_result(self):
        return {
            "narrative_analysis": "Analysis not available",
            "lighting_assessment": "neutral",
            "costume_check": "unclear",
            "mood_suggestion": "neutral",
            "creative_notes": "No analysis available",
        }
