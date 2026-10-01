import io
import uuid

import app.api.routes.lipsync as lipsync_routes
from app.models.lipsync_job import LipsyncJob


def _seed_workspace(tmp_path):
    video = tmp_path / "workspace" / "shots" / "v.mp4"
    audio = tmp_path / "workspace" / "audio" / "a.wav"
    video.parent.mkdir(parents=True, exist_ok=True)
    audio.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"vid")
    audio.write_bytes(b"aud")
    return "workspace/shots/v.mp4", "workspace/audio/a.wav"


def _patch_workspace(monkeypatch, tmp_path, probe=10.0):
    monkeypatch.setattr(lipsync_routes, "BASE_DIR", tmp_path)
    monkeypatch.setattr(lipsync_routes, "probe_duration", lambda _p: probe)


async def _create_project(client):
    resp = await client.post("/api/v1/projects", json={"title": "Lipsync"})
    assert resp.status_code == 200
    return resp.json()["id"]


async def _create_shot(client, project_id):
    scene = await client.post(
        f"/api/v1/projects/{project_id}/scenes", json={"scene_number": 1}
    )
    scene_id = scene.json()["id"]
    shot = await client.post(
        f"/api/v1/scenes/{scene_id}/shots",
        json={"shot_number": 1, "prompt_text": "x"},
    )
    return scene_id, shot.json()["id"]


def _record_run_job(monkeypatch):
    recorded = []

    async def fake_run_job(job_id, session_factory, project_root=None):
        recorded.append(job_id)

    monkeypatch.setattr(lipsync_routes, "run_job", fake_run_job)
    return recorded


async def test_list_videos_and_audios(client, tmp_path, monkeypatch):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    videos = (await client.get("/api/v1/lipsync/videos")).json()
    audios = (await client.get("/api/v1/lipsync/audios")).json()
    video_paths = [v["path"] for v in videos]
    assert video_rel in video_paths
    assert all(p.startswith("workspace/") for p in video_paths)
    matching = next(v for v in videos if v["path"] == video_rel)
    assert matching["duration"] == 10.0
    assert matching["size"] == 3
    assert audio_rel in [a["path"] for a in audios]


async def test_upload_audio_derives_extension_from_content_type(
    client, tmp_path, monkeypatch
):
    _patch_workspace(monkeypatch, tmp_path)
    project_id = await _create_project(client)
    resp = await client.post(
        f"/api/v1/lipsync/audios?project_id={project_id}",
        files={"file": ("evil.html", io.BytesIO(b"RIFFdata"), "audio/wav")},
    )
    assert resp.status_code == 200
    item = resp.json()
    assert item["path"].endswith(".wav")
    assert not item["path"].endswith(".html")
    stored = tmp_path / item["path"]
    assert stored.exists()
    assert stored.suffix == ".wav"


async def test_upload_rejects_oversize_audio(client, tmp_path, monkeypatch):
    _patch_workspace(monkeypatch, tmp_path)
    project_id = await _create_project(client)
    big = b"\0" * (lipsync_routes.MAX_AUDIO_BYTES + 1024)
    resp = await client.post(
        f"/api/v1/lipsync/audios?project_id={project_id}",
        files={"file": ("big.wav", io.BytesIO(big), "audio/wav")},
    )
    assert resp.status_code == 413
    assert not (tmp_path / "workspace" / "audio").exists() or list(
        (tmp_path / "workspace" / "audio").iterdir()
    ) == []


async def test_create_job_happy_path(client, tmp_path, monkeypatch):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    recorded = _record_run_job(monkeypatch)
    project_id = await _create_project(client)
    resp = await client.post(
        "/api/v1/lipsync/jobs",
        json={
            "project_id": project_id,
            "video_path": video_rel,
            "trim_start": 0.0,
            "trim_end": 3.0,
            "audio_path": audio_rel,
        },
    )
    assert resp.status_code == 201
    job = resp.json()
    assert job["status"] == "PENDING"
    assert job["stage"] is None
    assert job["video_source"] == video_rel
    assert job["audio_path"] == audio_rel
    assert len(recorded) == 1
    assert recorded[0] == job["id"]


async def test_create_job_rejects_bad_trim(client, tmp_path, monkeypatch):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    project_id = await _create_project(client)
    resp = await client.post(
        "/api/v1/lipsync/jobs",
        json={
            "project_id": project_id,
            "video_path": video_rel,
            "trim_start": 5.0,
            "trim_end": 3.0,
            "audio_path": audio_rel,
        },
    )
    assert resp.status_code == 422


async def test_create_job_missing_video_400(client, tmp_path, monkeypatch):
    _, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    project_id = await _create_project(client)
    resp = await client.post(
        "/api/v1/lipsync/jobs",
        json={
            "project_id": project_id,
            "video_path": "workspace/shots/nope.mp4",
            "trim_start": 0.0,
            "trim_end": 3.0,
            "audio_path": audio_rel,
        },
    )
    assert resp.status_code == 400


async def test_create_job_path_traversal_rejected(client, tmp_path, monkeypatch):
    _, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    project_id = await _create_project(client)
    resp = await client.post(
        "/api/v1/lipsync/jobs",
        json={
            "project_id": project_id,
            "video_path": "../../etc/passwd",
            "trim_start": 0.0,
            "trim_end": 3.0,
            "audio_path": audio_rel,
        },
    )
    assert resp.status_code == 400


async def test_create_job_project_not_found_404(client, tmp_path, monkeypatch):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    resp = await client.post(
        "/api/v1/lipsync/jobs",
        json={
            "project_id": str(uuid.uuid4()),
            "video_path": video_rel,
            "trim_start": 0.0,
            "trim_end": 3.0,
            "audio_path": audio_rel,
        },
    )
    assert resp.status_code == 404


async def test_create_job_audio_shorter_than_selection(client, tmp_path, monkeypatch):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    monkeypatch.setattr(lipsync_routes, "BASE_DIR", tmp_path)
    monkeypatch.setattr(
        lipsync_routes,
        "probe_duration",
        lambda p: 1.0 if str(p).endswith(".wav") else 10.0,
    )
    project_id = await _create_project(client)
    resp = await client.post(
        "/api/v1/lipsync/jobs",
        json={
            "project_id": project_id,
            "video_path": video_rel,
            "trim_start": 0.0,
            "trim_end": 3.0,
            "audio_path": audio_rel,
        },
    )
    assert resp.status_code == 422
    assert "audio shorter" in resp.json()["detail"]


async def test_create_job_trim_exceeds_video_duration(client, tmp_path, monkeypatch):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path, probe=10.0)
    project_id = await _create_project(client)
    resp = await client.post(
        "/api/v1/lipsync/jobs",
        json={
            "project_id": project_id,
            "video_path": video_rel,
            "trim_start": 0.0,
            "trim_end": 10.6,
            "audio_path": audio_rel,
        },
    )
    assert resp.status_code == 422


async def test_get_job_and_list(client, tmp_path, monkeypatch):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    _record_run_job(monkeypatch)
    project_id = await _create_project(client)
    created = (
        await client.post(
            "/api/v1/lipsync/jobs",
            json={
                "project_id": project_id,
                "video_path": video_rel,
                "trim_start": 0.0,
                "trim_end": 3.0,
                "audio_path": audio_rel,
            },
        )
    ).json()

    resp = await client.get(f"/api/v1/lipsync/jobs/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]

    resp = await client.get(f"/api/v1/lipsync/jobs?project_id={project_id}")
    assert resp.status_code == 200
    assert [j["id"] for j in resp.json()] == [created["id"]]

    resp = await client.get(f"/api/v1/lipsync/jobs/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_assign_requires_done_job(client, tmp_path, monkeypatch, session_factory):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    _record_run_job(monkeypatch)
    project_id = await _create_project(client)
    scene_id, shot_id = await _create_shot(client, project_id)
    created = (
        await client.post(
            "/api/v1/lipsync/jobs",
            json={
                "project_id": project_id,
                "video_path": video_rel,
                "trim_start": 0.0,
                "trim_end": 3.0,
                "audio_path": audio_rel,
            },
        )
    ).json()

    resp = await client.post(
        f"/api/v1/lipsync/jobs/{created['id']}/assign", json={"shot_id": shot_id}
    )
    assert resp.status_code == 400
    assert "not finished" in resp.json()["detail"]


async def test_assign_sets_shot_video_path(
    client, tmp_path, monkeypatch, session_factory
):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    _record_run_job(monkeypatch)
    project_id = await _create_project(client)
    scene_id, shot_id = await _create_shot(client, project_id)
    created = (
        await client.post(
            "/api/v1/lipsync/jobs",
            json={
                "project_id": project_id,
                "video_path": video_rel,
                "trim_start": 0.0,
                "trim_end": 3.0,
                "audio_path": audio_rel,
            },
        )
    ).json()

    output_path = "workspace/lipsync/lipsync_out.mp4"
    async with session_factory() as session:
        job = await session.get(LipsyncJob, uuid.UUID(created["id"]))
        job.status = "DONE"
        job.output_path = output_path
        await session.commit()

    resp = await client.post(
        f"/api/v1/lipsync/jobs/{created['id']}/assign", json={"shot_id": shot_id}
    )
    assert resp.status_code == 200
    assert resp.json()["shot_id"] == shot_id

    shots = (await client.get(f"/api/v1/scenes/{scene_id}/shots")).json()
    assert shots[0]["id"] == shot_id
    assert shots[0]["video_path"] == output_path


async def test_assign_shot_not_found_404(
    client, tmp_path, monkeypatch, session_factory
):
    video_rel, audio_rel = _seed_workspace(tmp_path)
    _patch_workspace(monkeypatch, tmp_path)
    _record_run_job(monkeypatch)
    project_id = await _create_project(client)
    await _create_shot(client, project_id)
    created = (
        await client.post(
            "/api/v1/lipsync/jobs",
            json={
                "project_id": project_id,
                "video_path": video_rel,
                "trim_start": 0.0,
                "trim_end": 3.0,
                "audio_path": audio_rel,
            },
        )
    ).json()
    async with session_factory() as session:
        job = await session.get(LipsyncJob, uuid.UUID(created["id"]))
        job.status = "DONE"
        job.output_path = "workspace/lipsync/lipsync_out.mp4"
        await session.commit()

    resp = await client.post(
        f"/api/v1/lipsync/jobs/{created['id']}/assign",
        json={"shot_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404
