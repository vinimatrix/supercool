# SuperCool AI Cinematic Studio — System Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Configuration](#setup--configuration)
4. [Database Models](#database-models)
5. [API Endpoints](#api-endpoints)
6. [Services](#services)
7. [Local Video Analyzer](#local-video-analyzer)
8. [Frontend](#frontend)
9. [Creative Pipeline](#creative-pipeline)
10. [Troubleshooting](#troubleshooting)

---

## Overview

SuperCool is an **AI-powered virtual cinematography studio** that takes pre-recorded video clips and produces finished cinematic edits with AI-driven transitions, color grading, audio mixing, and creative direction.

### Key Features

- **Multi-provider AI**: Google Gemini, OpenAI GPT-4o, NVIDIA NIM with automatic fallback
- **Video Understanding**: NVIDIA NEMOTRON Omni analyzes video content for intelligent editing decisions
- **Creative Pipeline**: End-to-end AI editing from raw clips to finished 4K output
- **Real-time Preview**: Web-based 4K video preview with playback controls
- **Shot Management**: Full CRUD for projects, scenes, shots, and characters

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+ (FastAPI + SQLAlchemy) |
| Database | PostgreSQL 16 (pgvector:pg16) |
| Cache | Redis 7 |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| Video Processing | FFmpeg |
| AI Models | NVIDIA NEMOTRON Omni, Google Gemini, OpenAI |
| Local AI | CLIP ViT-B/32, Florence-2, Qwen2-VL 2B |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│              http://localhost:5173                            │
├─────────────────────────────────────────────────────────────┤
│                     API Proxy (Vite)                         │
│              /api → localhost:8000                            │
├─────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                           │
│              http://localhost:8000                            │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Projects │ Scenes   │ Shots    │ Render   │ Creative        │
│ Routes   │ Routes   │ Routes   │ Routes   │ Routes          │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                     Services Layer                            │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Director │ Video    │ Creative │ Audio    │ Story           │
│ AI       │ Analyzer │ Pipeline │ Engine   │ Bible           │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                     Infrastructure                            │
├──────────┬──────────┬──────────┬─────────────────────────────┤
│PostgreSQL│ Redis    │ FFmpeg   │ NVIDIA/Google/OpenAI APIs   │
│:5432     │ :6379    │ System   │ External                    │
└──────────┴──────────┴──────────┴─────────────────────────────┘
```

### Port Reference

| Service | Port |
|---------|------|
| PostgreSQL | 5432 |
| Redis | 6379 |
| Python API | 8000 |
| Rust NLE | 3001 |
| Frontend (dev) | 5173 |

---

## Setup & Configuration

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- FFmpeg installed and in PATH

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- PostgreSQL with pgvector extension
- Redis 7

### 2. Configure Environment

Create `.env` file in project root:

```env
# Database
SUPERCOOL_DATABASE_URL=postgresql+asyncpg://supercool:supercool@localhost:5432/supercool

# AI Providers (at least one required)
SUPERCOOL_GOOGLE_API_KEY=your_google_key
SUPERCOOL_OPENAI_API_KEY=your_openai_key
SUPERCOOL_NVIDIA_API_KEY=your_nvidia_key

# LLM Provider Selection
SUPERCOOL_LLM_PROVIDER=google
SUPERCOOL_LLM_FALLBACK_ENABLED=true

# Local Video Analyzer (optional, for local AI analysis)
SUPERCOOL_LOCAL_MODELS_ENABLED=true
SUPERCOOL_CLIP_THRESHOLD_DIALOGUE=0.78
SUPERCOOL_CLIP_THRESHOLD_ACTION=0.70
SUPERCOOL_QWEN_BACKEND=auto
```

### 3. Install Dependencies

```bash
# Backend
uv sync

# Frontend
cd frontend && npm install
```

### 4. Run Migrations

```bash
uv run alembic upgrade head
```

### 5. Start Services

```bash
# Terminal 1: Backend API
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### API Key Sources

| Provider | Sign Up |
|----------|---------|
| Google Gemini | https://aistudio.google.com/apikey |
| OpenAI | https://platform.openai.com/api-keys |
| NVIDIA NIM | https://build.nvidia.com |

---

## Database Models

### Project

Top-level container for a film/video project.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `title` | String(255) | Project title |
| `description` | Text | Project description |
| `target_resolution` | String(20) | Default: `"4K"` |
| `fps` | Integer | Default: `24` |
| `aspect_ratio` | String(10) | Default: `"16:9"` |
| `created_at` | DateTime | Auto-set |
| `updated_at` | DateTime | Auto-updated |

### Scene

A scene within a project, containing multiple shots.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `project_id` | UUID | FK → projects |
| `scene_number` | Integer | Unique per project |
| `title` | String(255) | Scene title |
| `location` | String(255) | Filming location |
| `time_of_day` | String(50) | e.g., "dusk", "night" |
| `summary` | Text | Scene description |

### Shot

Individual shots within a scene.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `scene_id` | UUID | FK → scenes |
| `shot_number` | Integer | Unique per scene |
| `shot_type` | String(50) | e.g., "close-up", "wide" |
| `motion_type` | String(50) | e.g., "static", "tracking" |
| `assigned_engine` | String(50) | e.g., "SEEDANCE", "FLOW" |
| `prompt_text` | Text | AI generation prompt |
| `injected_prompt` | Text | Prompt with character context |
| `dialogue_text` | Text | Spoken dialogue |
| `video_path` | String(500) | Path to attached video clip |
| `speaker_character_id` | UUID | FK → characters |
| `status` | String(50) | PENDING, APPROVED, REJECTED |

### Character

Characters for consistency across shots.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `project_id` | UUID | FK → projects |
| `name` | String(255) | Character name |
| `biography` | Text | Character backstory |
| `locked_traits` | JSONB | Consistent traits |
| `voice_profile_id` | String(255) | Voice reference |
| `embedding` | Vector(512) | For similarity search |

### AnchorFace

Reference images for character consistency.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `character_id` | UUID | FK → characters |
| `image_url` | Text | Image path/URL |
| `view_angle` | String(50) | e.g., "front", "profile" |
| `is_primary` | Boolean | Primary reference |
| `embedding` | Vector(512) | For similarity search |

### RenderJob

Tracks video render jobs.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `shot_id` | UUID | FK → shots |
| `engine_name` | String(50) | Rendering engine |
| `status` | String(50) | QUEUED, PROCESSING, COMPLETED, FAILED |
| `output_url` | Text | Output file path |
| `qa_score` | Numeric(4,3) | Quality score |
| `qa_feedback` | Text | QA notes |
| `retry_count` | Integer | Retry attempts |
| `completed_at` | DateTime | Completion timestamp |

---

## API Endpoints

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/projects` | Create project |
| `GET` | `/api/v1/projects` | List all projects |
| `GET` | `/api/v1/projects/{id}` | Get project |

### Scenes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/projects/{project_id}/scenes` | Create scene |
| `GET` | `/api/v1/projects/{project_id}/scenes` | List scenes |

### Characters

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/projects/{project_id}/characters` | Create character |
| `GET` | `/api/v1/projects/{project_id}/characters` | List characters |

### Shots

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scenes/{scene_id}/shots` | Create shot |
| `GET` | `/api/v1/scenes/{scene_id}/shots` | List shots |
| `POST` | `/api/v1/shots/{shot_id}/upload-video` | Upload video clip |
| `PUT` | `/api/v1/shots/{shot_id}/assign-video` | Assign workspace video |

### Render

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/shots/{shot_id}/render` | Start render job |
| `GET` | `/api/v1/jobs/{job_id}` | Get render job |

### Anchor Faces

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/characters/{character_id}/anchor-faces` | Upload face |
| `GET` | `/api/v1/characters/{character_id}/anchor-faces` | List faces |
| `DELETE` | `/api/v1/anchor-faces/{face_id}` | Delete face |

### Creative Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/creative/render` | Run full creative pipeline |
| `GET` | `/api/v1/creative/workspace` | List workspace files |
| `POST` | `/api/v1/creative/upload` | Upload clip to workspace |

### Video Upload Example

```bash
# Upload video to a shot
curl -X POST http://localhost:8000/api/v1/shots/{shot_id}/upload-video \
  -F "file=@video.mp4"
```

### Creative Render Example

```bash
# Run creative pipeline
curl -X POST http://localhost:8000/api/v1/creative/render \
  -H "Content-Type: application/json" \
  -d '{
    "clips": ["path/to/clip1.mp4", "path/to/clip2.mp4"],
    "scene_context": "Combat scene in rainforest, dusk",
    "output_name": "my_scene",
    "enable_audio": true
  }'
```

---

## Services

### Director AI (`app/services/director_ai.py`)

Analyzes scenes and creates story arcs for editing decisions.

**Capabilities:**
- Analyzes shot descriptions for emotional beats
- Determines pacing (slow/medium/fast)
- Detects camera movement types
- Suggests transitions and color grades
- Uses NEMOTRON for intelligent analysis when available

**Output:**
```python
StoryArc(
    shots=[ShotAnalysis(...)],
    overall_mood="cinematic",
    pacing_curve=[0.8, 0.5, 0.9],
    emotional_peaks=[0, 2],
    suggested_music_crescendo=True
)
```

### Video Analyzer (`app/services/video_analyzer.py`)

Uses NVIDIA NEMOTRON Omni for video+text understanding.

**Capabilities:**
- Analyzes video content (MP4, up to 2 minutes)
- Falls back to text-only analysis
- Returns: emotion, camera, dialogue, action_level, grade, transitions, audio

**Configuration:**
- Model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- Requires: `SUPERCOOL_NVIDIA_API_KEY` in `.env`

### Local Video Analyzer (`app/services/local/`)

Open-source local video analysis system. **Local-first**, NEMOTRON fallback.

**Two-Layer Evaluation:**
1. **Layer 1 (GPU - CLIP + Florence):** Quantitative similarity scoring + object detection
2. **Layer 2 (CPU - Qwen2-VL):** Qualitative narrative analysis

**Shot States:**
| State | Description |
|-------|-------------|
| `APPROVED_FOR_EDIT` | Shot passes QA (similarity ≥ threshold) |
| `RE-RENDER_REQUIRED` | Shot failed QA (similarity below threshold) |
| `ADJUST_COLOR` | Color grading adjustment needed |
| `NEEDS_ANALYSIS` | No video or analysis unavailable |

### Creative Pipeline (`app/services/creative_pipeline.py`)

End-to-end AI editing pipeline.

**Pipeline Steps:**
1. **Director AI** analyzes scene structure
2. **Edit Plan** generated from story arc
3. **Creative Editor** processes clips with transitions and color
4. **Audio Engine** designs sound (ambience, tension, music)
5. **Assembly** combines everything into final output

**Output Files:**
```
workspace/pipeline_output/
├── {name}_video.mp4    # Video only
├── {name}_final.mp4    # Video + Audio
├── ambience.m4a        # Ambient audio
└── tension.m4a         # Tension bed (if applicable)
```

### Creative Editor (`app/services/creative_editor.py`)

FFmpeg-based video editing engine.

**Features:**
- Transitions: crossfade, whip_pan, match_cut, dip_black
- Color grades: neutral, warm, cold, cinematic, noir, action, dramatic
- Speed control
- Audio fades (in/out)
- Output: yuv420p for player compatibility

### Audio Engine (`app/services/audio_engine.py`)

AI-powered sound design.

**Ambience Types:**
- `rain` — Rainfall soundscape
- `forest` — Forest/nature ambience
- `wind` — Wind effects
- `city` — Urban background
- `silence` — Minimal ambience

**Features:**
- Tension bed generation (rising intensity)
- Multi-track mixing with volume control
- Ducking (auto-volume reduction for dialogue)
- Fade in/out

### Story Bible (`app/services/story_bible.py`)

Character context management.

**Features:**
- Character lookup and context retrieval
- Prompt injection with character traits
- Entity extraction via LLM
- Anchor face management

---

## Local Video Analyzer

### Overview

The Local Video Analyzer is a modular pipeline for analyzing video clips using open-source AI models running on your local machine. It runs **locally first** (no cloud dependency for most analysis) and falls back to NEMOTRON Omni when local models aren't available or produce weak results.

### Architecture

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

### File Structure

```
app/services/local/
├── __init__.py              # Package exports
├── clip_analyzer.py         # CLIP ViT-B/32 similarity scoring
├── florence_analyzer.py     # Florence-2 object detection + captioning + grounding
├── qwen_analyzer.py         # Qwen2-VL 2B narrative analysis (Ollama/llama-cpp)
└── coordinator.py           # Two-layer evaluation + NEMOTRON fallback

workspace/
├── analizador_video_qwen2_vl.py  # Standalone CLI script
├── references/                   # Manual reference images
│   └── {shot_id}.jpg
└── keyframes/                    # Extracted keyframes cache
    └── {shot_id}/
        ├── frame_001.jpg
        ├── frame_002.jpg
        └── ...
```

### Hardware Requirements

| Component | VRAM/RAM | Purpose |
|-----------|----------|---------|
| CLIP ViT-B/32 | ~400MB VRAM | Similarity scoring |
| Florence-2-base | ~800MB-1.2GB VRAM | Object detection + captioning |
| **Total GPU** | **~1.2-1.6GB** | Under 3GB limit |
| Qwen2-VL 2B | ~1.8-2.5GB RAM | Narrative (CPU) |

### Installation

#### 1. Install Python Dependencies

```bash
pip install torch torchvision transformers pillow opencv-python httpx
```

#### 2. Install Ollama (for Qwen2-VL)

```bash
# Install Ollama
# Windows: https://ollama.ai/download
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Pull Qwen2-VL 2B model
ollama pull qwen2.5-vl:2b
```

**Alternative:** Install llama-cpp-python for CPU inference without Ollama:

```bash
pip install llama-cpp-python
```

#### 3. (Optional) Download GGUF Model for llama-cpp

If using llama-cpp-python instead of Ollama, download the Qwen2-VL 2B GGUF model:

```bash
mkdir models
# Download from Hugging Face or other source
# Place in models/qwen2.5-vl-2b.gguf
```

### Configuration

Add these settings to your `.env` file:

```env
# Local Video Analyzer Settings
SUPERCOOL_LOCAL_MODELS_ENABLED=true
SUPERCOOL_CLIP_THRESHOLD_DIALOGUE=0.78
SUPERCOOL_CLIP_THRESHOLD_ACTION=0.70
SUPERCOOL_QWEN_BACKEND=auto  # auto|ollama|llama_cpp
```

### Usage

#### Standalone CLI (Testing)

```bash
# Basic analysis
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4

# With reference image
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4 \
  --reference workspace/references/shot1.jpg

# With scene context
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4 \
  --context "Combat scene in rainforest, dusk"

# Save output to JSON
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4 \
  --output analysis_result.json

# Full example
python workspace/analizador_video_qwen2_vl.py workspace/shots/shot1.mp4 \
  --reference workspace/references/shot1.jpg \
  --context "Dense rainforest canopy, dusk, heavy rain, combat rescue" \
  --output workspace/analysis/shot1_analysis.json
```

#### API Integration

The local analyzer is automatically used when you call the Creative Pipeline:

```bash
# The system automatically uses local analysis first
curl -X POST http://localhost:8000/api/v1/creative/render \
  -H "Content-Type: application/json" \
  -d '{
    "clips": ["workspace/shots/shot1.mp4", "workspace/shots/shot2.mp4"],
    "scene_context": "Combat scene in rainforest, dusk",
    "output_name": "my_scene"
  }'
```

#### Python API

```python
from app.services.local.coordinator import LocalVideoCoordinator

coordinator = LocalVideoCoordinator()

shot = {
    "id": "shot1",
    "prompt_text": "Sasuke draws sword in crescent arc",
    "duration": 10.0,
    "video_path": "workspace/shots/shot1.mp4",
}

result = coordinator.analyze_shot(shot, "Combat scene in rainforest")

print(result["decision"]["status"])  # APPROVED_FOR_EDIT, RE-RENDER_REQUIRED, etc.
print(result["decision"]["similarity_score"])  # 0.85
print(result["layer2"]["narrative_analysis"])  # Natural language analysis
```

### Story Bible References

The system supports reference images for shot-to-storyboard comparison:

1. **Manual references:** Place images in `workspace/references/{shot_id}.jpg`
2. **Auto-extracted:** First keyframe of each clip is used as reference
3. **No reference:** Similarity check is skipped

### Thresholds

| Shot Type | Threshold | Description |
|-----------|-----------|-------------|
| Dialogue / Close-up | 0.78 | Stricter quality bar |
| Action / Combat | 0.70 | Allows for motion blur |

Thresholds are configurable via `.env`:
- `SUPERCOOL_CLIP_THRESHOLD_DIALOGUE=0.78`
- `SUPERCOOL_CLIP_THRESHOLD_ACTION=0.70`

### Model Details

#### CLIP ViT-B/32

- **Purpose:** Quantitative similarity scoring between shots
- **VRAM:** ~400MB
- **How:** Extracts visual features, computes cosine similarity
- **Threshold:** ≥0.78 (dialogue), ≥0.70 (action)

#### Florence-2-base

- **Purpose:** Object detection, captioning, visual grounding
- **VRAM:** ~800MB-1.2GB
- **Capabilities:**
  - Object detection: Find objects in frame
  - Captioning: Generate natural language description
  - Visual grounding: Find regions matching text query
- **Key Props Tracked:** sword, cloak, scar, headband

#### Qwen2-VL 2B

- **Purpose:** Qualitative narrative analysis
- **RAM:** ~1.8-2.5GB (CPU)
- **Backends:** Ollama (preferred) or llama-cpp-python
- **Output:** Lighting assessment, costume check, mood suggestion, creative notes

### Troubleshooting

**1. "No backend available" for Qwen**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Verify model is downloaded
ollama pull qwen2.5-vl:2b
```

**2. CUDA out of memory**
```bash
# Reduce keyframe extraction
# The system extracts 1 FPS by default

# Or disable GPU for CLIP
export CUDA_VISIBLE_DEVICES=""
```

**3. Low similarity scores**
- Check if reference images are clear
- Ensure video quality is sufficient
- Adjust thresholds in `.env`

**4. Florence model not loading**
```bash
# First run downloads the model (~800MB)
# Check internet connection
# Ensure sufficient disk space
```

**5. Standalone script errors**
```bash
# Ensure you're in the project root
cd C:\Users\vm004458\Documents\supercool

# Run with Python explicitly
python workspace/analizador_video_qwen2_vl.py --help
```

### Integration with Existing Pipeline

The local analyzer integrates seamlessly with the existing Creative Pipeline:

1. **Automatic fallback:** If local models are unavailable, NEMOTRON is used
2. **Same interface:** Output format is compatible with existing Director AI
3. **No breaking changes:** Existing API endpoints work unchanged

### Performance Notes

- **Keyframe extraction:** ~1 FPS (not 24fps) to save VRAM
- **VRAM cleanup:** Automatic `torch.cuda.empty_cache()` after each analysis
- **Caching:** Keyframes are cached in `workspace/keyframes/`
- **Lazy loading:** Models are loaded on first use, not at startup

---

## Frontend

### URL

http://localhost:5173

### Layout

The UI uses a dark-mode cinematic aesthetic (#0D0F12 background) with a 4-quadrant layout:

```
┌─────────────────┬─────────────────────────┐
│  Story Bible    │   Direction Chat         │
│  (Left Panel)   │   (Top Right)            │
├─────────────────┤─────────────────────────┤
│  Shot Timeline  │   4K Preview             │
│  (Bottom Left)  │   (Bottom Right)         │
└─────────────────┴─────────────────────────┘
```

### Tabs

1. **Story Bible** — Manage characters, scenes, project settings
2. **QA Monitor** — Shot rendering status (APPROVED/PENDING/REJECTED)
3. **Analytics** — Project metrics and revenue projections

### Key Features

- **Upload Clips**: Bulk upload videos to workspace
- **Attach Clip**: Assign videos to individual shots
- **Render Button**: Run full creative pipeline
- **Preview Player**: Play rendered video with controls
- **Chat Interface**: Conversational direction

### API Client

Located at `frontend/src/api/client.ts`:

```typescript
// Projects
projectsApi.list()
projectsApi.get(id)
projectsApi.create(data)

// Shots
shotsApi.list(sceneId)
shotsApi.uploadVideo(shotId, file)
shotsApi.assignVideo(shotId, videoPath)

// Creative
creativeApi.render(config)
creativeApi.workspace()
```

---

## Creative Pipeline

### Full Workflow

```
1. User uploads clips to workspace
         ↓
2. User attaches clips to shots
         ↓
3. User clicks "Render Final"
         ↓
4. Director AI analyzes scene (with NEMOTRON)
         ↓
5. Edit plan generated
         ↓
6. Creative Editor processes clips
   - Transitions applied
   - Color grading applied
   - Speed adjustments
         ↓
7. Audio Engine designs sound
   - Ambience generated
   - Tension bed (if needed)
   - Tracks mixed
         ↓
8. Final assembly
   - Video + Audio combined
   - Output saved to workspace
         ↓
9. Preview available in UI
```

### Render Configuration

```json
{
  "clips": ["path/to/clip1.mp4", "path/to/clip2.mp4"],
  "scene_context": "Description of the scene",
  "output_name": "scene_name",
  "master_volume": 1.0,
  "enable_audio": true,
  "enable_color": true,
  "enable_transitions": true
}
```

### Color Grades

| Grade | Description |
|-------|-------------|
| `neutral` | No adjustment |
| `warm` | Orange/amber tones |
| `cold` | Blue tones |
| `cinematic` | Film look |
| `noir` | High contrast B&W |
| `action` | High saturation |
| `dramatic` | Deep shadows |

### Transitions

| Transition | Description |
|------------|-------------|
| `cut` | Hard cut (default) |
| `crossfade` | Smooth blend |
| `whip_pan` | Fast blur transition |
| `match_cut` | Visual match |
| `dip_black` | Fade to black |

---

## Troubleshooting

### Common Issues

**1. API won't start**
```bash
# Check if ports are in use
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Restart Docker
docker-compose down && docker-compose up -d
```

**2. Database connection error**
```bash
# Verify PostgreSQL is running
docker ps | findstr postgres

# Test connection
psql -h localhost -U supercool -d supercool
```

**3. NVIDIA API not working**
```bash
# Check API key in .env
cat .env | findstr NVIDIA

# Test API key
curl -H "Authorization: Bearer $NVIDIA_API_KEY" \
  https://integrate.api.nvidia.com/v1/models
```

**4. FFmpeg not found**
```bash
# Install FFmpeg
winget install FFmpeg

# Verify
ffmpeg -version
```

**5. Video render fails**
- Check FFmpeg output for errors
- Verify input video codec (H.264 recommended)
- Check disk space in workspace/

### Logs

```bash
# API logs
tail -f api.log

# Docker logs
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

## File Structure

```
supercool/
├── app/
│   ├── api/routes/         # API endpoint handlers
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   │   ├── local/          # Local video analysis modules
│   │   │   ├── clip_analyzer.py
│   │   │   ├── florence_analyzer.py
│   │   │   ├── qwen_analyzer.py
│   │   │   └── coordinator.py
│   │   ├── video_analyzer.py
│   │   ├── director_ai.py
│   │   ├── creative_pipeline.py
│   │   ├── creative_editor.py
│   │   └── audio_engine.py
│   ├── providers/          # LLM providers
│   ├── db/                 # Database setup
│   └── main.py             # FastAPI app
├── frontend/
│   └── src/
│       ├── App.tsx         # Main UI component
│       └── api/client.ts   # API client
├── workspace/
│   ├── shots/              # Uploaded video clips
│   ├── references/         # Story Bible reference images
│   ├── keyframes/          # Extracted keyframes cache
│   ├── pipeline_output/    # Rendered outputs
│   └── analizador_video_qwen2_vl.py  # Standalone CLI
├── alembic/                # Database migrations
├── docker-compose.yml      # Infrastructure
├── .env                    # Environment variables
└── pyproject.toml          # Python dependencies
```

---

## License

Proprietary — SuperCool AI Cinematic Studio
