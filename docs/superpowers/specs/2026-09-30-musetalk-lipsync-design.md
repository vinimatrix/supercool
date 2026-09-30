# Lipsync Module (MuseTalk) — Design Spec

**Date:** 2026-09-30
**Status:** Approved
**Scope:** Backend job API + processing pipeline + new `lipsync` tab in the frontend

## Goal

Let the user select a video, select a portion of it (trim in/out), select the audio to synchronize, run MuseTalk lipsync asynchronously, preview/assign the result.

## Decisions (Q&A)

- **Portion selection:** A — trim in/out points (start/end seconds) on a chosen video
- **Audio source:** C — list existing `workspace/audio/` files + upload new
- **Video source:** A — list existing workspace videos + upload new
- **Execution:** Approach 2 — FastAPI threadpool (`run_in_executor`) + DB-backed job rows + polling (no Celery/Redis dependency)
- **Result:** A — job record in DB + output in `workspace/lipsync/` + history UI + "assign to shot"
- **UI location:** A — new `lipsync` tab in TabNavigator, panel in Sidebar
- **Models:** installed on user's other dev machine — no installation preflight; failures surface via strict mode

## Section 1: Data model + API

### Table `lipsync_jobs`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `project_id` | FK projects | |
| `status` | str | `PENDING \| RUNNING \| DONE \| FAILED` |
| `stage` | str nullable | `TRIMMING \| INFERRING \| FINALIZING` |
| `video_source` | str | workspace path or uploaded path |
| `trim_start` | float | seconds |
| `trim_end` | float | seconds |
| `audio_path` | str | |
| `output_path` | str nullable | `workspace/lipsync/lipsync_<id>.mp4` |
| `shot_id` | FK shots nullable | for "assign to shot" |
| `error` | text nullable | |
| `created_at` | datetime | |
| `completed_at` | datetime nullable | |

Alembic migration; `CREATE_LIPSYNC_JOBS` DDL added to `tests/conftest.py`.

### Endpoints (`app/api/routes/lipsync.py`, prefix `/api/v1/lipsync`)

- `GET /videos` — list selectable videos from `workspace/shots/`, `workspace/pipeline_output/`, `workspace/exports/` (+ renders): `{path, name, size, duration}`
- `GET /audios` — list `workspace/audio/*.wav|mp3|ogg`: `{path, name, size}`
- `POST /audios` — multipart upload → `workspace/audio/<uuid>.<ext>`
- `POST /jobs` — body `{project_id, video_path?, video_file?, trim_start, trim_end, audio_path, shot_id?}` → validates (422 bad trim bounds, 400 missing files), creates job `PENDING`, dispatches background work, returns job
- `GET /jobs?project_id=` — job history
- `GET /jobs/{id}` — status poll target
- `POST /jobs/{id}/assign` — `{shot_id}` → sets `shot.video_path` to job output
- Uploads for video: `POST /videos` multipart → `workspace/lipsync/sources/<uuid>.<ext>`

Output served via existing `/workspace` StaticFiles mount.

## Section 2: Processing pipeline

Runs in threadpool; each stage writes `stage` to the job row before execution.

1. **TRIMMING** — ffmpeg cuts `video_source` to `[trim_start, trim_end]` → temp clip; cuts audio to same duration (cap at audio length; if audio shorter than selection → `FAILED` with `audio shorter than selection`)
2. **INFERRING** — `MuseTalkClient.align_lip_sync(trimmed_clip, trimmed_audio, strict=True)` (subprocess, timeout configurable)
3. **FINALIZING** — result moved to `workspace/lipsync/lipsync_<job_id>.mp4` → `status=DONE`, `completed_at` set

**Failure handling:**
- `MuseTalkClient` gains `strict=True` mode: raise on error/no-output instead of the current silent source-video copy (existing callers keep lenient default)
- Any exception → `status=FAILED`, stderr excerpt in `error`
- No model-installation preflight (models live on user's other machine)

**Config:** `app/config.py` gains `musetalk_dir`, `musetalk_timeout` (currently hardcoded).

## Section 3: UI — `lipsync` tab

**Wiring:** `TabNavigator.tsx` adds `lipsync` tab → `components/lipsync/LipsyncPanel.tsx` rendered in `Sidebar.tsx` panel switch (youtube/drift pattern).

**Panel flow:**

1. **VIDEO** — list from `GET /lipsync/videos` (name + duration) or upload (hidden `<input type="file" accept="video/*">`, ShotCard pattern)
2. **TRIM** — `<video>` preview + `START` / `END` numeric inputs (seconds) + selection duration; typing sets `video.currentTime` for scrub-check
3. **AUDIO** — list from `GET /lipsync/audios` (select + `<audio controls>` preview) or upload; warn if selected audio shorter than trim selection
4. **RUN** — `GENERATE LIPSYNC` → `POST /jobs` → button shows live status polled every 2s (`GET /jobs/{id}`): `PENDING → TRIMMING → INFERRING → FINALIZING`
5. **RESULT** (`DONE`) — `<video>` preview of output + `DOWNLOAD` + `ASSIGN TO SHOT` (project shot dropdown → `POST /jobs/{id}/assign`) + success toast

**History:** recent jobs for project (status badge, date, click to preview); `FAILED` shows `error` in red.

**Client/hooks:** `lipsyncApi` in `frontend/src/api/client.ts`; `useStudioApi` wrappers with toasts + `loadingStates`; polling loop in panel component (cleanup on unmount/tab switch).

## Section 4: Testing + error handling

**Backend:**
- Model/conftest DDL + migration test
- API: create job validation (422 bad trim, 400 missing files), list/get, assign, videos/audios listing, audio upload
- Pipeline: trim step with mocked subprocess; strict failure → `FAILED` + error (mock `align_lip_sync` raising); background dispatch stubbed via monkeypatch so tests never spawn inference

**Frontend:**
- `LipsyncPanel.test.tsx`: renders steps from mocked API, trim binding, run → poll → DONE preview, FAILED error display
- `lipsyncApi` client tests (spy-on-`api` pattern)

**Error handling:** 422 invalid trim / 400 missing files at creation; job `FAILED` + `error` for inference failures; toasts for upload failures; poll stops on unmount; poll tolerates transient network errors (3 consecutive failures → toast, keep last known state).

## Out of scope

- Celery/Redis job queue (migrate later without API contract change: job id + status shape stay stable)
- WebSocket push (untested infra)
- Model installation/setup tooling
- Multi-character / batch lipsync
