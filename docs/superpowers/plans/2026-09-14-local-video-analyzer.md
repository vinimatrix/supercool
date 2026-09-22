# Local Video Analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate open-source AI models (CLIP, Florence-2, Qwen2-VL 2B) for local video analysis with NEMOTRON fallback.

**Architecture:** Modular pipeline with CLIP (similarity), Florence-2 (objects/captioning), Qwen2-VL (narrative), coordinated by a two-layer evaluation engine.

**Tech Stack:** Python, PyTorch, Transformers, OpenCV, Ollama/llama-cpp-python, httpx

## Global Constraints

- Python 3.11+
- GPU: 3GB VRAM max (CLIP ~400MB + Florence ~1.2GB = ~1.6GB total)
- RAM: 16GB (Qwen2-VL 2B uses ~1.8-2.5GB)
- Dependencies: torch, torchvision, transformers, pillow, opencv-python, httpx
- Keyframe extraction: 1 FPS using OpenCV
- Config via `.env` with `SUPERCOOL_` prefix

---

## File Structure

```
app/services/local/
├── __init__.py              # Exports all classes
├── clip_analyzer.py         # CLIP ViT-B/32 similarity scoring
├── florence_analyzer.py     # Florence-2 object detection + captioning + grounding
├── qwen_analyzer.py         # Qwen2-VL 2B narrative analysis (Ollama/llama-cpp)
└── coordinator.py           # Two-layer evaluation + NEMOTRON fallback

app/services/
├── video_analyzer.py        # Updated: delegates to coordinator

workspace/
├── analizador_video_qwen2_vl.py  # Standalone script
├── references/                   # Manual reference images
└── keyframes/                    # Extracted keyframes cache
```

---

### Task 1: Project Setup & Dependencies

**Files:**
- Create: `app/services/local/__init__.py`
- Modify: `requirements.txt` (add dependencies)
- Create: `workspace/references/.gitkeep`
- Create: `workspace/keyframes/.gitkeep`

**Interfaces:**
- Produces: `app.services.local` package

- [ ] **Step 1: Create local package directory**

```bash
mkdir -p app/services/local
```

- [ ] **Step 2: Create `__init__.py`**

```python
"""Local video analysis modules."""
from app.services.local.clip_analyzer import CLIPAnalyzer
from app.services.local.florence_analyzer import FlorenceAnalyzer
from app.services.local.qwen_analyzer import QwenAnalyzer
from app.services.local.coordinator import LocalVideoCoordinator

__all__ = ["CLIPAnalyzer", "FlorenceAnalyzer", "QwenAnalyzer", "LocalVideoCoordinator"]
```

- [ ] **Step 3: Add dependencies to requirements.txt**

Append to existing `requirements.txt`:

```
# Local video analysis
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.35.0
pillow>=10.0.0
opencv-python>=4.8.0
```

- [ ] **Step 4: Create workspace directories**

```bash
mkdir -p workspace/references workspace/keyframes
touch workspace/references/.gitkeep workspace/keyframes/.gitkeep
```

- [ ] **Step 5: Commit**

```bash
git add app/services/local/ workspace/references/.gitkeep workspace/keyframes/.gitkeep
git commit -m "feat: add local video analysis package structure"
```

---

### Task 2: CLIP Analyzer

**Files:**
- Create: `app/services/local/clip_analyzer.py`
- Create: `tests/test_local/test_clip_analyzer.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: `CLIPAnalyzer.is_available()`, `CLIPAnalyzer.extract_keyframe()`, `CLIPAnalyzer.compute_similarity()`, `CLIPAnalyzer.analyze_shot()`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for CLIP Analyzer."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestCLIPAnalyzer:
    def test_is_available_no_model(self):
        from app.services.local.clip_analyzer import CLIPAnalyzer
        analyzer = CLIPAnalyzer()
        # Should not crash even without model loaded
        assert isinstance(analyzer.is_available(), bool)

    def test_extract_keyframe_returns_list(self, tmp_path):
        from app.services.local.clip_analyzer import CLIPAnalyzer
        analyzer = CLIPAnalyzer()
        # Create a dummy video file (won't actually extract without OpenCV)
        video_path = tmp_path / "test.mp4"
        video_path.touch()
        # Mock OpenCV to avoid real video processing
        with patch("cv2.VideoCapture") as mock_cap:
            mock_cap.return_value.get.return_value = 0
            mock_cap.return_value.read.return_value = (False, None)
            result = analyzer.extract_keyframe(str(video_path))
            assert isinstance(result, list)

    def test_compute_similarity_returns_float(self):
        from app.services.local.clip_analyzer import CLIPAnalyzer
        analyzer = CLIPAnalyzer()
        # Without model loaded, should return 0.0
        result = analyzer.compute_similarity("dummy1.jpg", "dummy2.jpg")
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_local/test_clip_analyzer.py -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
"""CLIP Analyzer - Quantitative similarity scoring using CLIP ViT-B/32."""

import os
from pathlib import Path

import cv2
import torch
from PIL import Image


class CLIPAnalyzer:
    """Analyzes shot similarity using CLIP ViT-B/32 (~400MB VRAM)."""

    THRESHOLD_DIALOGUE = 0.78
    THRESHOLD_ACTION = 0.70

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._loaded = False

    def is_available(self) -> bool:
        """Check if CLIP model is loaded."""
        return self._loaded

    def load_model(self):
        """Load CLIP ViT-B/32 model."""
        if self._loaded:
            return
        try:
            from transformers import CLIPModel, CLIPProcessor
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.preprocessor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model.to(self.device)
            self._loaded = True
            print("[CLIP] Model loaded successfully")
        except Exception as e:
            print(f"[CLIP] Failed to load model: {e}")
            self._loaded = False

    def extract_keyframe(self, video_path: str, fps: float = 1.0) -> list[str]:
        """Extract keyframes at specified FPS using OpenCV."""
        keyframes = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return keyframes

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(video_fps / fps) if fps > 0 else int(video_fps)
        frame_interval = max(1, frame_interval)

        frame_count = 0
        saved_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                output_dir = Path(video_path).parent / "keyframes" / Path(video_path).stem
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"frame_{saved_count:03d}.jpg"
                cv2.imwrite(str(output_path), frame)
                keyframes.append(str(output_path))
                saved_count += 1

            frame_count += 1

        cap.release()
        return keyframes

    def compute_similarity(self, frame_path: str, reference_path: str) -> float:
        """Compute cosine similarity between frame and reference."""
        if not self._loaded:
            return 0.0

        try:
            frame = Image.open(frame_path).convert("RGB")
            reference = Image.open(reference_path).convert("RGB")

            inputs = self.preprocessor(images=[frame, reference], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
                frame_features = outputs[0]
                ref_features = outputs[1]
                similarity = torch.cosine_similarity(frame_features, ref_features, dim=0)

            return float(similarity.item())
        except Exception as e:
            print(f"[CLIP] Similarity error: {e}")
            return 0.0

    def analyze_shot(self, video_path: str, reference_path: str | None) -> dict:
        """Run full CLIP analysis on a shot."""
        keyframes = self.extract_keyframe(video_path)

        if not keyframes:
            return {
                "similarity_score": None,
                "keyframes_extracted": 0,
                "passed_threshold": False,
                "threshold_used": 0,
            }

        if reference_path and Path(reference_path).exists():
            scores = [self.compute_similarity(kf, reference_path) for kf in keyframes[:5]]
            avg_score = sum(scores) / len(scores) if scores else 0.0
        else:
            avg_score = None

        return {
            "similarity_score": avg_score,
            "keyframes_extracted": len(keyframes),
            "passed_threshold": avg_score is not None and avg_score >= self.THRESHOLD_DIALOGUE,
            "threshold_used": self.THRESHOLD_DIALOGUE,
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_local/test_clip_analyzer.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/local/clip_analyzer.py tests/test_local/test_clip_analyzer.py
git commit -m "feat: add CLIP analyzer for similarity scoring"
```

---

### Task 3: Florence Analyzer

**Files:**
- Create: `app/services/local/florence_analyzer.py`
- Create: `tests/test_local/test_florence_analyzer.py`

**Interfaces:**
- Consumes: Keyframes from CLIPAnalyzer
- Produces: `FlorenceAnalyzer.analyze_shot()` → {objects_detected, caption, key_props_present, visual_details}

- [ ] **Step 1: Write the failing test**

```python
"""Tests for Florence Analyzer."""
import pytest
from unittest.mock import patch, MagicMock


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_local/test_florence_analyzer.py -v
```

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
"""Florence Analyzer - Object detection, captioning, and visual grounding."""

import gc
from pathlib import Path

import torch
from PIL import Image


class FlorenceAnalyzer:
    """Analyzes shots using Florence-2-base (~800MB-1.2GB VRAM)."""

    KEY_PROPS = {
        "sword": ["sword", "katana", "blade", "weapon"],
        "cloak": ["cloak", "cape", "robe"],
        "scar": ["scar", "mark", "wound"],
        "headband": ["headband", "forehead protector"],
    }

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._loaded = False

    def is_available(self) -> bool:
        return self._loaded

    def load_model(self):
        """Load Florence-2-base model."""
        if self._loaded:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoProcessor
            self.model = AutoModelForCausalLM.from_pretrained(
                "microsoft/Florence-2-base", trust_remote_code=True
            )
            self.processor = AutoProcessor.from_pretrained(
                "microsoft/Florence-2-base", trust_remote_code=True
            )
            self.model.to(self.device)
            self._loaded = True
            print("[Florence] Model loaded successfully")
        except Exception as e:
            print(f"[Florence] Failed to load model: {e}")
            self._loaded = False

    def detect_objects(self, frame_path: str) -> list[dict]:
        """Detect objects in frame."""
        if not self._loaded:
            return []
        try:
            image = Image.open(frame_path).convert("RGB")
            prompt = "<OD>"
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=256)

            result = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            objects = []
            for part in result.split("：</OD>")[0].split("；"):
                if "：" in part:
                    label, conf = part.split("：", 1)
                    try:
                        objects.append({"label": label.strip(), "confidence": float(conf)})
                    except ValueError:
                        objects.append({"label": part.strip(), "confidence": 0.5})
            return objects
        except Exception as e:
            print(f"[Florence] Object detection error: {e}")
            return []

    def generate_caption(self, frame_path: str) -> str:
        """Generate detailed natural language caption of frame."""
        if not self._loaded:
            return ""
        try:
            image = Image.open(frame_path).convert("RGB")
            prompt = "<CAPTION>"
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=256)

            return self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
        except Exception as e:
            print(f"[Florence] Caption error: {e}")
            return ""

    def visual_grounding(self, frame_path: str, query: str) -> list[dict]:
        """Find regions matching text query."""
        if not self._loaded:
            return []
        try:
            image = Image.open(frame_path).convert("RGB")
            prompt = f"<REF EXP>{query}</REF EXP><OD>"
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=256)

            result = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            regions = []
            for part in result.split("：</OD>")[0].split("；"):
                if "：" in part:
                    coords, conf = part.split("：", 1)
                    try:
                        regions.append({"region": coords.strip(), "score": float(conf)})
                    except ValueError:
                        pass
            return regions
        except Exception as e:
            print(f"[Florence] Grounding error: {e}")
            return []

    def analyze_shot(self, keyframes: list[str], shot_info: dict) -> dict:
        """Full Florence analysis on keyframes."""
        if not keyframes:
            return {
                "objects_detected": [],
                "caption": "",
                "key_props_present": {},
                "visual_details": "",
            }

        # Use first keyframe for analysis
        frame = keyframes[0]

        # Detect objects
        objects = self.detect_objects(frame)
        object_labels = [obj["label"] for obj in objects]

        # Generate caption
        caption = self.generate_caption(frame)

        # Check key props
        props_present = {}
        for prop_name, keywords in self.KEY_PROPS.items():
            props_present[prop_name] = any(
                kw in label.lower() for label in object_labels for kw in keywords
            )

        return {
            "objects_detected": object_labels,
            "caption": caption,
            "key_props_present": props_present,
            "visual_details": caption,
        }

    def _cleanup_vram(self):
        """Clear VRAM after analysis."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_local/test_florence_analyzer.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/local/florence_analyzer.py tests/test_local/test_florence_analyzer.py
git commit -m "feat: add Florence analyzer for object detection and captioning"
```

---

### Task 4: Qwen Analyzer

**Files:**
- Create: `app/services/local/qwen_analyzer.py`
- Create: `tests/test_local/test_qwen_analyzer.py`

**Interfaces:**
- Consumes: Keyframes from CLIPAnalyzer, results from CLIPAnalyzer and FlorenceAnalyzer
- Produces: `QwenAnalyzer.analyze_shot()` → {narrative_analysis, lighting_assessment, costume_check, mood_suggestion, creative_notes}

- [ ] **Step 1: Write the failing test**

```python
"""Tests for Qwen Analyzer."""
import pytest
from unittest.mock import patch, MagicMock


class TestQwenAnalyzer:
    def test_is_available_no_backend(self):
        from app.services.local.qwen_analyzer import QwenAnalyzer
        analyzer = QwenAnalyzer()
        # Without Ollama or llama-cpp, should not be available
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_local/test_qwen_analyzer.py -v
```

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
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
        self.backend = None  # "ollama" or "llama_cpp"
        self.model = None
        self._detect_backend()

    def _detect_backend(self):
        """Auto-detect available backend."""
        # Try Ollama first
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

        # Try llama-cpp-python
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

    def analyze_shot(
        self,
        keyframes: list[str],
        shot_info: dict,
        clip_result: dict,
        florence_result: dict,
    ) -> dict:
        """Run qualitative analysis using keyframes + previous results."""
        if not self.is_available():
            return self._empty_result()

        # Build prompt
        prompt = self.PROMPT_TEMPLATE.format(
            description=shot_info.get("prompt_text", "Unknown"),
            duration=shot_info.get("duration", 0),
            similarity=clip_result.get("similarity_score", "N/A"),
            objects=", ".join(florence_result.get("objects_detected", [])),
            caption=florence_result.get("caption", "No caption"),
        )

        # Call backend
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

    def _call_ollama(self, prompt: str, images: list[str]) -> str:
        """Call Ollama API with vision support."""
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

    def _call_llama_cpp(self, prompt: str) -> str:
        """Call llama-cpp-python with GGUF model."""
        try:
            from llama_cpp import Llama
            model = Llama(model_path="models/qwen2.5-vl-2b.gguf", n_ctx=4096)
            output = model(prompt, max_tokens=512, temperature=0.3)
            return output["choices"][0]["text"]
        except Exception as e:
            print(f"[Qwen] llama-cpp error: {e}")
            return ""

    def _parse_response(self, response: str) -> dict:
        """Parse JSON from response."""
        try:
            # Find JSON block
            if "{" in response:
                start = response.rfind("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return self._empty_result()

    def _empty_result(self) -> dict:
        return {
            "narrative_analysis": "Analysis not available",
            "lighting_assessment": "neutral",
            "costume_check": "unclear",
            "mood_suggestion": "neutral",
            "creative_notes": "No analysis available",
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_local/test_qwen_analyzer.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/local/qwen_analyzer.py tests/test_local/test_qwen_analyzer.py
git commit -m "feat: add Qwen analyzer for narrative analysis"
```

---

### Task 5: Coordinator (Two-Layer Evaluation)

**Files:**
- Create: `app/services/local/coordinator.py`
- Create: `tests/test_local/test_coordinator.py`
- Modify: `app/config.py` (add new settings)

**Interfaces:**
- Consumes: CLIPAnalyzer, FlorenceAnalyzer, QwenAnalyzer, VideoAnalyzer (NEMOTRON)
- Produces: `LocalVideoCoordinator.analyze_shot()` → {layer1, layer2, decision}

- [ ] **Step 1: Add config settings to `app/config.py`**

Add to Settings class:

```python
clip_threshold_dialogue: float = 0.78
clip_threshold_action: float = 0.70
local_models_enabled: bool = True
qwen_backend: str = "auto"  # auto|ollama|llama_cpp
```

- [ ] **Step 2: Write the failing test**

```python
"""Tests for Local Video Coordinator."""
import pytest
from unittest.mock import patch, MagicMock


class TestLocalVideoCoordinator:
    def test_is_available(self):
        from app.services.local.coordinator import LocalVideoCoordinator
        coordinator = LocalVideoCoordinator()
        assert isinstance(coordinator.is_available(), bool)

    def test_analyze_shot_returns_dict(self):
        from app.services.local.coordinator import LocalVideoCoordinator
        coordinator = LocalVideoCoordinator()
        shot = {
            "id": "test",
            "prompt_text": "Test shot",
            "duration": 10,
            "video_path": None,
        }
        result = coordinator.analyze_shot(shot, "test context")
        assert isinstance(result, dict)
        assert "layer1" in result
        assert "layer2" in result
        assert "decision" in result
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_local/test_coordinator.py -v
```

Expected: FAIL

- [ ] **Step 4: Write implementation**

```python
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

        # Load models if enabled
        if settings.local_models_enabled:
            self._load_models()

    def _load_models(self):
        """Load available local models."""
        try:
            self.clip.load_model()
        except Exception as e:
            print(f"[Coordinator] CLIP load failed: {e}")

        try:
            self.florence.load_model()
        except Exception as e:
            print(f"[Coordinator] Florence load failed: {e}")

    def is_available(self) -> bool:
        """At least one local model available."""
        return (
            self.clip.is_available()
            or self.florence.is_available()
            or self.qwen.is_available()
            or self.nemotron.is_available()
        )

    async def analyze_shot(self, shot: dict, scene_context: str = "") -> dict:
        """Full two-layer analysis with fallback."""

        # Layer 1: Quantitative (GPU)
        layer1 = self._run_layer1(shot)

        # Layer 2: Qualitative (CPU)
        layer2 = self._run_layer2(shot, layer1)

        # Decision
        decision = self._make_decision(layer1, layer2, shot)

        # Fallback to NEMOTRON if local analysis is weak
        if decision["status"] == "NEEDS_ANALYSIS" and self.nemotron.is_available():
            nemotron_result = await self.nemotron.analyze_shot(shot, scene_context)
            decision["nemotron_fallback"] = nemotron_result

        return {
            "layer1": layer1,
            "layer2": layer2,
            "decision": decision,
        }

    def _run_layer1(self, shot: dict) -> dict:
        """CLIP + Florence analysis."""
        video_path = shot.get("video_path")
        if not video_path or not Path(video_path).exists():
            return {"error": "no_video"}

        # Extract keyframes
        keyframes = self.clip.extract_keyframe(video_path)

        # Get reference (manual or auto)
        reference = self._get_reference(shot, keyframes)

        # CLIP similarity
        clip_result = self.clip.analyze_shot(video_path, reference)

        # Florence objects + caption
        florence_result = self.florence.analyze_shot(keyframes, shot)

        # Cleanup VRAM
        self.florence._cleanup_vram()

        return {**clip_result, **florence_result}

    def _run_layer2(self, shot: dict, layer1: dict) -> dict:
        """Qwen narrative analysis."""
        if not self.qwen.is_available():
            return {"skipped": True, "reason": "qwen_not_available"}

        video_path = shot.get("video_path")
        if not video_path or not Path(video_path).exists():
            return {"skipped": True, "reason": "no_video"}

        keyframes = self.clip.extract_keyframe(video_path)

        return self.qwen.analyze_shot(keyframes, shot, layer1, {})

    def _get_reference(self, shot: dict, keyframes: list[str]) -> str | None:
        """Get reference image: manual or auto-extracted."""
        shot_id = shot.get("id", "unknown")

        # Check manual reference
        manual = Path("workspace/references") / f"{shot_id}.jpg"
        if manual.exists():
            return str(manual)

        # Auto-extract first keyframe
        if keyframes:
            return keyframes[0]

        return None

    def _make_decision(self, layer1: dict, layer2: dict, shot: dict) -> dict:
        """Make final decision based on both layers."""
        score = layer1.get("similarity_score")

        # Determine threshold based on shot type
        desc = shot.get("prompt_text", "").lower()
        is_action = any(w in desc for w in ["slash", "strike", "combat", "fight"])
        threshold = settings.clip_threshold_action if is_action else settings.clip_threshold_dialogue

        # Decision logic
        if score is None:
            status = "NEEDS_ANALYSIS"
        elif score >= threshold:
            status = "APPROVED_FOR_EDIT"
        else:
            status = "RE-RENDER_REQUIRED"

        # Check color from Layer 2
        if layer2.get("lighting_assessment") == "incorrect":
            status = "ADJUST_COLOR"

        return {
            "status": status,
            "similarity_score": score,
            "threshold": threshold,
            "layer1_summary": layer1.get("caption", ""),
            "layer2_summary": layer2.get("narrative_analysis", ""),
        }
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_local/test_coordinator.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/local/coordinator.py tests/test_local/test_coordinator.py app/config.py
git commit -m "feat: add coordinator for two-layer evaluation"
```

---

### Task 6: Update VideoAnalyzer Integration

**Files:**
- Modify: `app/services/video_analyzer.py`
- Create: `tests/test_video_analyzer_integration.py`

**Interfaces:**
- Consumes: LocalVideoCoordinator
- Produces: Updated `VideoAnalyzer.analyze_shot()` that uses local first, NEMOTRON fallback

- [ ] **Step 1: Write the failing test**

```python
"""Tests for VideoAnalyzer integration."""
import pytest
from unittest.mock import patch, MagicMock


class TestVideoAnalyzerIntegration:
    def test_is_available(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        assert isinstance(analyzer.is_available(), bool)

    @pytest.mark.asyncio
    async def test_analyze_shot_returns_dict(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        shot = {"id": "test", "prompt_text": "test", "duration": 10}
        result = await analyzer.analyze_shot(shot, "context")
        assert isinstance(result, dict)
        assert "emotion" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_video_analyzer_integration.py -v
```

Expected: FAIL

- [ ] **Step 3: Update `video_analyzer.py`**

Replace the full file content:

```python
"""Video Analyzer - Local first, NEMOTRON fallback."""

import json
import base64
from pathlib import Path

import httpx

from app.config import settings


class VideoAnalyzer:
    """Analyzes shots - local first, NEMOTRON fallback."""

    def __init__(self):
        self.api_key = settings.nvidia_api_key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

        # Lazy load local coordinator
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
        """Check if any analyzer is available."""
        if self.local and self.local.is_available():
            return True
        return bool(self.api_key)

    async def analyze_shot(self, shot_info: dict, context: str = "") -> dict:
        """Local analysis first, NEMOTRON fallback."""
        # Try local analysis first
        if self.local and self.local.is_available():
            try:
                local_result = await self.local.analyze_shot(shot_info, context)
                if local_result["decision"]["status"] != "NEEDS_ANALYSIS":
                    return self._map_local_to_format(local_result)
            except Exception as e:
                print(f"[VideoAnalyzer] Local analysis failed: {e}")

        # Fallback to NEMOTRON
        if self.api_key:
            video_path = shot_info.get("video_path")
            if video_path and Path(video_path).exists():
                result = await self._analyze_with_video(video_path, shot_info, context)
                if result.get("emotion") != "neutral":
                    return result
            return await self._analyze_text_only(shot_info, context)

        return self._empty_analysis()

    def _map_local_to_format(self, local_result: dict) -> dict:
        """Map local results to existing format for backward compatibility."""
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

    async def _analyze_with_video(
        self, video_path: str, shot_info: dict, context: str
    ) -> dict:
        """Analyze using NEMOTRON with actual video content."""
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
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": f"data:video/mp4;base64,{video_b64}"
                                },
                            },
                        ],
                    }
                ],
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

    async def _analyze_text_only(self, shot_info: dict, context: str) -> dict:
        """Analyze using NEMOTRON text only."""
        try:
            prompt = self._build_prompt(shot_info, context, has_video=False)

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}],
                    }
                ],
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

    async def _call_api(self, payload: dict) -> dict:
        """Call NVIDIA API and parse response."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                print(f"[NEMOTRON] Error {response.status_code}: {response.text[:200]}")
                return self._empty_analysis()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)

    def _build_prompt(self, shot_info: dict, context: str, has_video: bool) -> str:
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

    def _parse_response(self, content: str) -> dict:
        """Parse JSON from response, handling thinking mode."""
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
            else:
                print(f"[NEMOTRON] No JSON found in: {content[:100]}")

        except Exception as e:
            print(f"[NEMOTRON] Parse error: {e}")

        return self._empty_analysis()

    def _empty_analysis(self) -> dict:
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_video_analyzer_integration.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/video_analyzer.py tests/test_video_analyzer_integration.py
git commit -m "feat: update VideoAnalyzer for local-first analysis"
```

---

### Task 7: Standalone Script

**Files:**
- Create: `workspace/analizador_video_qwen2_vl.py`

**Interfaces:**
- Consumes: LocalVideoCoordinator
- Produces: CLI tool for testing

- [ ] **Step 1: Create standalone script**

```python
#!/usr/bin/env python3
"""
Standalone video analyzer for testing.
Usage: python analizador_video_qwen2_vl.py <video_path> [--reference <ref_image>] [--context "context"] [--output result.json]
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.local.coordinator import LocalVideoCoordinator


def get_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
            capture_output=True, text=True
        )
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 10.0


def main():
    parser = argparse.ArgumentParser(description="Analyze a video shot locally")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--reference", help="Reference image path")
    parser.add_argument("--context", default="", help="Scene context")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    video_path = args.video
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    print(f"Analyzing: {video_path}")
    print("=" * 50)

    coordinator = LocalVideoCoordinator()

    shot = {
        "id": Path(video_path).stem,
        "prompt_text": Path(video_path).stem,
        "duration": get_duration(video_path),
        "video_path": video_path,
    }

    # Add reference if provided
    if args.reference:
        ref_path = Path(args.reference)
        if ref_path.exists():
            shot["reference_path"] = str(ref_path)
            print(f"Reference: {args.reference}")

    print("\nRunning two-layer analysis...")
    result = coordinator.analyze_shot(shot, args.context)

    # Print summary
    print("\n" + "=" * 50)
    print("ANALYSIS RESULT")
    print("=" * 50)
    print(f"Status: {result['decision']['status']}")
    print(f"Similarity: {result['decision'].get('similarity_score', 'N/A')}")
    print(f"Threshold: {result['decision'].get('threshold', 'N/A')}")

    if result["layer2"].get("narrative_analysis"):
        print(f"\nNarrative: {result['layer2']['narrative_analysis']}")
        print(f"Lighting: {result['layer2'].get('lighting_assessment', 'N/A')}")
        print(f"Mood: {result['layer2'].get('mood_suggestion', 'N/A')}")

    # Save output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to: {args.output}")
    else:
        print("\nFull result:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make script executable (Unix)**

```bash
chmod +x workspace/analizador_video_qwen2_vl.py
```

- [ ] **Step 3: Commit**

```bash
git add workspace/analizador_video_qwen2_vl.py
git commit -m "feat: add standalone video analyzer script"
```

---

### Task 8: Integration Tests & Verification

**Files:**
- Create: `tests/test_integration_local_analyzer.py`

**Interfaces:**
- Tests full pipeline integration

- [ ] **Step 1: Write integration test**

```python
"""Integration tests for local video analyzer."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestLocalAnalyzerIntegration:
    def test_coordinator_init(self):
        from app.services.local.coordinator import LocalVideoCoordinator
        coordinator = LocalVideoCoordinator()
        assert coordinator is not None

    def test_video_analyzer_uses_local(self):
        from app.services.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        # Should try local first
        assert analyzer.local is not None or analyzer.api_key

    def test_config_settings_exist(self):
        from app.config import settings
        assert hasattr(settings, "clip_threshold_dialogue")
        assert hasattr(settings, "clip_threshold_action")
        assert hasattr(settings, "local_models_enabled")
        assert hasattr(settings, "qwen_backend")

    def test_empty_keyframes_handled(self):
        from app.services.local.coordinator import LocalVideoCoordinator
        coordinator = LocalVideoCoordinator()
        shot = {"id": "test", "prompt_text": "test", "duration": 10, "video_path": None}
        result = coordinator.analyze_shot(shot)
        assert result["decision"]["status"] == "NEEDS_ANALYSIS"
```

- [ ] **Step 2: Run integration tests**

```bash
pytest tests/test_integration_local_analyzer.py -v
```

Expected: PASS

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration_local_analyzer.py
git commit -m "feat: add integration tests for local video analyzer"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Project setup & dependencies | `__init__.py`, requirements |
| 2 | CLIP analyzer | `clip_analyzer.py`, tests |
| 3 | Florence analyzer | `florence_analyzer.py`, tests |
| 4 | Qwen analyzer | `qwen_analyzer.py`, tests |
| 5 | Coordinator | `coordinator.py`, config, tests |
| 6 | VideoAnalyzer update | `video_analyzer.py`, tests |
| 7 | Standalone script | `analizador_video_qwen2_vl.py` |
| 8 | Integration tests | `test_integration_local_analyzer.py` |

**Total estimated time:** 45-60 minutes
