# Local Video Analyzer Design

**Date:** 2026-09-14
**Status:** Approved
**Approach:** Modular Pipeline (Option B)

## Overview

Integrate open-source AI models for local video analysis, replacing cloud dependency (NEMOTRON) as primary. NEMOTRON becomes fallback. Optimized for 3GB VRAM GPU + 16GB RAM.

## Architecture

### Module Structure

```
app/services/
├── local/
│   ├── __init__.py
│   ├── clip_analyzer.py
│   ├── florence_analyzer.py
│   ├── qwen_analyzer.py
│   └── coordinator.py
├── video_analyzer.py
└── director_ai.py

workspace/
├── analizador_video_qwen2_vl.py
├── references/
└── keyframes/
```

### Data Flow

```
Shot (video_path + prompt_text)
  │
  ▼
┌─────────────────────────────────────┐
│ Layer 1: Quantitative (GPU - CLIP)  │
│ - Extract keyframe (1 FPS)          │
│ - Compare vs reference              │
│ - cosine_similarity score           │
│ - Object presence (Florence-2)      │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ Layer 2: Qualitative (CPU - Qwen)   │
│ - Natural language analysis          │
│ - Lighting, costume, mood            │
│ - Creative recommendations           │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ Decision Engine                     │
│ - APPROVED_FOR_EDIT                 │
│ - RE-RENDER_REQUIRED               │
│ - ADJUST_COLOR                      │
└─────────────┬───────────────────────┘
              │
              ▼ (fallback)
┌─────────────────────────────────────┐
│ NEMOTRON Omni (Cloud API)           │
└─────────────────────────────────────┘
```

## Modules

### 1. CLIPAnalyzer (`clip_analyzer.py`)

**Model:** openai/clip-vit-base-patch32 (~400MB VRAM)

**Methods:**
- `load_model()` — Lazy load CLIP
- `extract_keyframe(video_path, fps=1.0)` — Extract keyframes using OpenCV
- `compute_similarity(frame_path, reference_path)` — Cosine similarity 0.0-1.0
- `analyze_shot(video_path, reference_path)` — Full analysis

**Reference Handling:**
- Manual: `workspace/references/{shot_id}.jpg`
- Auto: First keyframe of clip
- None: Skip similarity check

**Thresholds:**
- `SUPERCOOL_CLIP_THRESHOLD_DIALOGUE=0.78`
- `SUPERCOOL_CLIP_THRESHOLD_ACTION=0.70`

### 2. FlorenceAnalyzer (`florence_analyzer.py`)

**Model:** microsoft/Florence-2-base (~800MB-1.2GB VRAM)

**Methods:**
- `load_model()` — Lazy load Florence-2
- `detect_objects(frame_path)` — Returns [{label, confidence, bbox}]
- `generate_caption(frame_path)` — Detailed natural language caption
- `visual_grounding(frame_path, query)` — Find regions matching text
- `analyze_shot(keyframes, shot_info)` — Full analysis

**Key Props:**
```python
KEY_PROPS = {
    "sword": ["sword", "katana", "blade", "weapon"],
    "cloak": ["cloak", "cape", "robe"],
    "scar": ["scar", "mark", "wound"],
    "headband": ["headband", "forehead protector"],
}
```

**VRAM Management:**
- `torch.cuda.empty_cache()` after each pass
- `gc.collect()` for memory cleanup

### 3. QwenAnalyzer (`qwen_analyzer.py`)

**Model:** Qwen2-VL 2B GGUF (~1.8-2.5GB RAM)

**Backend Detection:**
1. Check `which ollama` → use Ollama
2. Try `import llama_cpp` → use llama-cpp-python
3. Else: disabled

**Methods:**
- `_detect_backend()` — Auto-detect available backend
- `is_available()` — Check if any backend works
- `analyze_shot(keyframes, shot_info, clip_result, florence_result)` — Narrative analysis

**Ollama Call:**
```python
POST http://localhost:11434/api/generate
model: qwen2.5-vl:2b
images: base64 encoded keyframes
```

**Prompt Template:**
```
You are a film director analyzing a shot for editing.

Shot description: {description}
Duration: {duration}s
CLIP similarity score: {similarity}/1.0
Objects detected: {objects}
Caption: {caption}

Analyze this shot and provide:
1. Lighting assessment (dark/bright/golden_hour/neutral)
2. Costume verification (correct/incorrect/unclear)
3. Mood suggestion (tense/dramatic/action/calm/mysterious)
4. Creative notes for the editor

Respond in JSON format.
```

**Output:**
```json
{
  "narrative_analysis": "string",
  "lighting_assessment": "dark|bright|golden_hour|neutral",
  "costume_check": "correct|incorrect|unclear",
  "mood_suggestion": "tense|dramatic|action|calm|mysterious",
  "creative_notes": "string"
}
```

### 4. LocalVideoCoordinator (`coordinator.py`)

**Two-Layer Evaluation:**
1. Layer 1: CLIP + Florence (quantitative, GPU)
2. Layer 2: Qwen (qualitative, CPU)
3. Decision: APPROVED_FOR_EDIT / RE-RENDER_REQUIRED / ADJUST_COLOR
4. Fallback: NEMOTRON if local analysis weak

**Decision Logic:**
```python
if score is None:
    status = "NEEDS_ANALYSIS"
elif score >= threshold:
    status = "APPROVED_FOR_EDIT"
else:
    status = "RE-RENDER_REQUIRED"

if layer2.lighting_assessment == "incorrect":
    status = "ADJUST_COLOR"
```

**Config:**
```bash
SUPERCOOL_CLIP_THRESHOLD_DIALOGUE=0.78
SUPERCOOL_CLIP_THRESHOLD_ACTION=0.70
SUPERCOOL_LOCAL_MODELS_ENABLED=true
SUPERCOOL_QWEN_BACKEND=auto
```

### 5. Updated VideoAnalyzer

Delegates to `LocalVideoCoordinator` first, falls back to NEMOTRON.

### 6. Standalone Script

`workspace/analizador_video_qwen2_vl.py`

```bash
python analizador_video_qwen2_vl.py <video_path> [--reference <ref>] [--context "context"] [--output result.json]
```

## Dependencies

```bash
pip install torch torchvision transformers pillow opencv-python
pip install llama-cpp-python  # optional
# Ollama: https://ollama.ai
```

## Keyframe Cache

- Store in `workspace/keyframes/{shot_id}/`
- Reuse if already extracted
- Format: `frame_{n:03d}.jpg`

## VRAM Budget

| Model | VRAM | Purpose |
|-------|------|---------|
| CLIP ViT-B/32 | ~400MB | Similarity scoring |
| Florence-2-base | ~800MB-1.2GB | Object detection + captioning |
| **Total GPU** | **~1.2-1.6GB** | Under 3GB limit |
| Qwen2-VL 2B | ~1.8-2.5GB RAM | Narrative (CPU) |
