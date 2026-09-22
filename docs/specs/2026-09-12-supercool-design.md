# SuperCool - AI Cinematic Studio: Design Specification

**Date**: 2026-09-12
**Status**: Draft
**Approach**: Phased Incremental (MVP → Infrastructure → E2E)

---

## 1. Overview

SuperCool is an AI-powered virtual cinematography studio that transforms scripts/prompts into finished 4K films with professional audio, multilingual dubbing, and platform publishing — all from a single chat interface.

**Architecture**: Python (FastAPI + Celery + Redis) + Rust (NLE engine)
**Database**: PostgreSQL + pgvector (anchor face embeddings)
**GPU**: NVIDIA CUDA/NVENC for video encoding
**AI Providers**: Multi-provider (Google Gemini, OpenAI, NVIDIA NIM)

---

## 2. Phased Implementation Plan

### Phase 1: MVP
- FastAPI REST API with project/scene/shot CRUD
- Story Bible service (entity extraction, anchor faces, prompt injection)
- NLE engine in Rust (concat, transcode, audio mix, ducking)
- SQLite dev database → PostgreSQL production
- Multi-provider LLM abstraction

### Phase 2: Infrastructure
- Docker Compose (API, Rust NLE, Redis, PostgreSQL, Prometheus, Grafana)
- Celery task queue for async rendering
- GPU acceleration (NVENC)
- Monitoring dashboards

### Phase 3: E2E Pipeline
- Dynamic AI engine router (Flow/Seedance)
- Autonomous Art Director (QA agent with cosine similarity)
- YouTube/Prime Video publishing
- Monetization dashboard

---

## 3. Project Structure

```
supercool/
├── pyproject.toml
├── Cargo.toml
├── rust-nle/
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs              # Axum HTTP server
│       ├── lib.rs
│       ├── ffmpeg/
│       │   ├── mod.rs
│       │   ├── concat.rs        # Concatenation (stream copy + filter)
│       │   ├── transcode.rs     # Transcode to 24fps/4K
│       │   ├── filters.rs       # FFmpeg filter graph helpers
│       │   └── gpu.rs           # NVENC acceleration
│       ├── audio/
│       │   ├── mod.rs
│       │   ├── mix.rs           # amix multichannel
│       │   ├── ducking.rs       # sidechaincompress
│       │   └── lip_sync.rs      # Lip-sync alignment
│       └── pipeline.rs          # Full NLE pipeline orchestrator
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── config.py                # pydantic-settings
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract LLMProvider
│   │   ├── google.py            # Gemini / Vertex AI
│   │   ├── openai.py            # GPT-4o / DALL-E
│   │   ├── nvidia.py            # NVIDIA NIM endpoints
│   │   └── registry.py          # Provider registry + fallback
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py           # Project, Scene, Shot
│   │   ├── character.py         # Character, AnchorFace
│   │   └── render_job.py        # RenderJob
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py
│   │   │   ├── scenes.py
│   │   │   ├── shots.py
│   │   │   ├── story_bible.py
│   │   │   └── render.py
│   │   └── deps.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── story_bible.py       # Entity extraction + trait locking
│   │   ├── context_injector.py  # Prompt injection pipeline
│   │   ├── nle_client.py        # HTTP client → Rust NLE
│   │   └── render_service.py    # Render orchestration
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── render.py            # Celery async tasks (Phase 2)
│   └── db/
│       ├── __init__.py
│       ├── database.py          # SQLAlchemy async engine
│       └── migrations/          # Alembic migrations
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_nle/
└── docker-compose.yml           # Phase 2
```

---

## 4. Database Schema

### 4.1 projects

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, default gen_random_uuid() |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| target_resolution | VARCHAR(20) | DEFAULT '4K' |
| fps | INTEGER | DEFAULT 24 |
| aspect_ratio | VARCHAR(10) | DEFAULT '16:9' |
| created_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP |

### 4.2 characters

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| project_id | UUID | FK → projects(id) CASCADE |
| name | VARCHAR(255) | NOT NULL |
| biography | TEXT | |
| locked_traits | JSONB | DEFAULT '[]' |
| voice_profile_id | VARCHAR(255) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### 4.3 anchor_faces

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| character_id | UUID | FK → characters(id) CASCADE |
| image_url | TEXT | NOT NULL |
| view_angle | VARCHAR(50) | 'frontal', '3/4_left', 'profile' |
| face_embedding | vector(512) | ArcFace/CLIP embedding |
| is_primary | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | |

Index: `idx_anchor_faces_embedding_hnsw USING hnsw (face_embedding vector_cosine_ops)`

### 4.4 scenes

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| project_id | UUID | FK → projects(id) CASCADE |
| scene_number | INTEGER | NOT NULL |
| title | VARCHAR(255) | |
| location | VARCHAR(255) | |
| time_of_day | VARCHAR(50) | |
| summary | TEXT | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Unique index: (project_id, scene_number)

### 4.5 shots

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| scene_id | UUID | FK → scenes(id) CASCADE |
| shot_number | INTEGER | NOT NULL |
| shot_type | VARCHAR(50) | 'WIDE', 'CLOSE_UP', 'DUTCH_ANGLE' |
| motion_type | VARCHAR(50) | 'ATMOSPHERIC', 'ACTION_HIGH_SPEED' |
| assigned_engine | VARCHAR(50) | 'FLOW', 'SEEDANCE' |
| prompt_text | TEXT | NOT NULL |
| injected_prompt | TEXT | After context injection |
| dialogue_text | TEXT | |
| speaker_character_id | UUID | FK → characters(id) SET NULL |
| status | VARCHAR(50) | DEFAULT 'PENDING' |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### 4.6 render_jobs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| shot_id | UUID | FK → shots(id) CASCADE |
| engine_name | VARCHAR(50) | NOT NULL |
| status | VARCHAR(50) | 'QUEUED', 'RENDERING', 'QA_CHECK', 'APPROVED', 'REJECTED', 'FAILED' |
| output_url | TEXT | |
| qa_score | NUMERIC(4,3) | Cosine similarity (e.g., 0.845) |
| qa_feedback | TEXT | |
| retry_count | INTEGER | DEFAULT 0 |
| created_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |

---

## 5. Story Bible Service

### 5.1 Entity Data Structure

```json
{
  "project_id": "proj_boruto_tbv",
  "character_id": "char_boruto_tbv",
  "name": "Boruto Uzumaki (Live-Action TBV)",
  "anchors": {
    "primary_face_ref": "ref_boruto_liveaction_v1.png",
    "secondary_views": ["ref_boruto_34_v1.png", "ref_boruto_profile_v1.png"],
    "embeddings_vector_id": "vec_boruto_512d"
  },
  "locked_traits": [
    "Fine vertical scar over right eye",
    "Black cape with dark crimson inner lining",
    "Realistic blonde textured live-action hair",
    "Katana with black scabbard on left waist"
  ],
  "voice_config": {
    "voice_id": "eleven_labs_boruto_tbv_v1",
    "stability": 0.75,
    "similarity_boost": 0.85
  }
}
```

### 5.2 Anchor Face System

- **Format**: 16-bit PNG or WebP Lossless, min 1024×1024px
- **Normalization**: Face-alignment to canonical coordinates (eye centers + nose bridge)
- **Embedding**: ArcFace (ResNet-100) + CLIP ViT-L/14 → 512-dim float32 vector
- **Storage**: pgvector with HNSW index for sub-ms similarity search
- **Matching**: Cosine similarity
  - Dialogue/close-up: ≥ 0.78
  - Action/combat: ≥ 0.70 (motion blur tolerance)

### 5.3 Prompt Injection Pipeline

```
Raw User Prompt
  → [Entity Extractor] (LLM identifies character references)
  → [Trait Injector] (appends locked_traits)
  → [Style Appendage] (global project style)
  → [Negative Prompt] (mandatory artifact prevention)
  → Final Payload
```

**Rules**:
1. **Reference Tensor Tagging**: `[INPUT_REF: ref.png, ip_adapter_scale=0.85]`
2. **Locked Traits Injection**: `"Boruto [scar, black cape, katana]"`
3. **Global Style Appendage**: `"...cinematic 35mm lens, 4k resolution"`
4. **Negative Prompt**: `"2d anime, cartoon, plastic skin, deformed..."`
5. **Engine Routing**: Action keywords → Seedance (motion_scale=1.4), Atmospheric → Flow (motion_scale=0.8)

---

## 6. Rust NLE Engine

### 6.1 FFmpeg Operations

**Concatenation (Stream Copy)**:
```bash
ffmpeg -f concat -safe 0 -i clips.txt -c copy output.mp4
```

**Concatenation (Re-encode)**:
```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex \
  "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset fast -c:a aac output.mp4
```

**Transcode to 24fps**:
```bash
ffmpeg -i input.mp4 -vf "fps=fps=24" \
  -c:v libx264 -crf 18 -preset medium -c:a copy output_24fps.mp4
```

**Audio Mixing**:
```bash
ffmpeg -i dialogue.wav -i music.mp3 -filter_complex \
  "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]" \
  -map "[aout]" -c:a aac -b:a 192k mixed.m4a
```

**Ducking**:
```bash
ffmpeg -i video.mp4 -i dialogue.wav -i music.mp3 -filter_complex \
  "[2:a][1:a]sidechaincompress=threshold=0.08:ratio=12:attack=10:release=200[ducked]; \
   [1:a][ducked]amix=inputs=2:duration=first[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k final.mp4
```

### 6.2 Rust API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/nle/concat` | Concatenate video clips |
| POST | `/nle/transcode` | Transcode to target fps/resolution |
| POST | `/nle/mix-audio` | Mix multiple audio tracks |
| POST | `/nle/pipeline` | Execute full NLE pipeline |
| GET | `/nle/health` | GPU/FFmpeg health check |

### 6.3 Dependencies (Cargo)

```toml
[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4"] }
ffmpeg-next = "6"          # FFmpeg bindings
opus = "0.3"               # Audio codec support
```

---

## 7. Multi-Provider AI

### 7.1 Provider Interface

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> list[Entity]: ...

    @abstractmethod
    async def generate_prompt(self, scene: Scene, characters: list[Character]) -> str: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

### 7.2 Provider Registry

```python
PROVIDERS = {
    "google": GoogleProvider,     # Gemini 2.5 / Vertex AI
    "openai": OpenAIProvider,     # GPT-4o / DALL-E
    "nvidia": NVIDIAProvider,     # NIM / NeMo endpoints
}

# Fallback chain: google → openai → nvidia
```

### 7.3 Environment Variables

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=...
OPENAI_API_KEY=...
NVIDIA_API_KEY=...
LLM_FALLBACK_ENABLED=true
```

---

## 8. API Endpoints (MVP)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/projects/{id}` | Get project |
| POST | `/api/v1/projects/{id}/scenes` | Create scene |
| GET | `/api/v1/projects/{id}/scenes` | List scenes |
| POST | `/api/v1/projects/{id}/characters` | Create character |
| POST | `/api/v1/characters/{id}/anchor-faces` | Upload anchor face |
| POST | `/api/v1/projects/{id}/story-bible/extract` | Extract entities from text |
| POST | `/api/v1/scenes/{id}/shots` | Create shot |
| POST | `/api/v1/shots/{id}/inject-prompt` | Run prompt injection |
| POST | `/api/v1/shots/{id}/render` | Start render job |
| GET | `/api/v1/jobs/{id}` | Get render job status |
| GET | `/api/v1/nle/health` | NLE engine health |

---

## 9. Testing Strategy

- **Unit tests**: Story Bible entity extraction, prompt injection logic
- **Integration tests**: API endpoints with test database
- **NLE tests**: FFmpeg operations with sample video files
- **E2E tests**: Full pipeline from script → rendered output

---

## 10. Success Criteria

- [ ] API serves CRUD operations for projects/scenes/shots
- [ ] Story Bible extracts entities and injects prompts correctly
- [ ] Rust NLE concatenates, transcodes, mixes audio
- [ ] Multi-provider fallback works (Google → OpenAI → NVIDIA)
- [ ] Docker Compose deploys full stack
- [ ] Render pipeline produces valid MP4 output
