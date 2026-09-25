"""Live-pipeline tests: character visual_prompt must reach prompts built by running code.

Covers the three live prompt paths from code review:
- StoryBibleService.get_character_context (the seam)
- RenderService._build_injected_prompt (via start_render)
- VideoAnalyzer._build_prompt — fed by the creative-pipeline producer (shot dicts),
  which sources characters from the story bible via the /creative/render route
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tests.conftest import (
    CREATE_ANCHOR_FACES,
    CREATE_CHARACTERS,
    CREATE_PROJECTS,
    CREATE_RENDER_JOBS,
    CREATE_SHOTS,
)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(text(CREATE_PROJECTS))
        await conn.execute(text(CREATE_CHARACTERS))
        await conn.execute(text(CREATE_ANCHOR_FACES))
        await conn.execute(text(CREATE_SHOTS))
        await conn.execute(text(CREATE_RENDER_JOBS))
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


async def _make_character(session, visual_prompt=None, reference_sheet_url=None):
    from app.models.character import Character

    char = Character(
        project_id=uuid.uuid4(),
        name="Hero",
        visual_prompt=visual_prompt,
        reference_sheet_url=reference_sheet_url,
    )
    session.add(char)
    await session.commit()
    await session.refresh(char)
    return char


async def test_story_bible_context_carries_visual_prompt(session):
    from app.services.story_bible import StoryBibleService

    char = await _make_character(
        session,
        visual_prompt="white cloak",
        reference_sheet_url="/uploads/reference_sheets/sheet.png",
    )

    ctx = await StoryBibleService(session).get_character_context(str(char.id))

    assert ctx is not None
    assert ctx["name"] == "Hero"
    assert ctx.get("visual_prompt") == "white cloak"
    assert ctx.get("reference_sheet_url") == "/uploads/reference_sheets/sheet.png"


async def test_render_service_injected_prompt_contains_visual_reference(session, monkeypatch):
    from app.models.shot import Shot
    from app.services.render_service import RenderService

    char = await _make_character(session, visual_prompt="white cloak")
    shot = Shot(
        scene_id=uuid.uuid4(),
        shot_number=1,
        prompt_text="Hero enters the rain",
        speaker_character_id=char.id,
    )
    session.add(shot)
    await session.commit()
    await session.refresh(shot)

    monkeypatch.setattr(RenderService, "_dispatch_render_task", lambda *a, **k: None)

    job = await RenderService(session).start_render(str(shot.id), "FLOW")

    assert job.status == "QUEUED"
    assert "VISUAL REFERENCE — Hero: white cloak" in (shot.injected_prompt or "")


def test_video_analyzer_prompt_contains_visual_reference():
    from app.services.video_analyzer import VideoAnalyzer

    shot = {
        "prompt_text": "Hero enters the rain",
        "duration": 10,
        "characters": [{"name": "Hero", "visual_prompt": "white cloak"}],
    }

    prompt = VideoAnalyzer()._build_prompt(shot, "", has_video=False)

    assert "VISUAL REFERENCE — Hero: white cloak" in prompt


def test_video_analyzer_prompt_omits_visual_reference_when_absent():
    from app.services.video_analyzer import VideoAnalyzer

    prompt = VideoAnalyzer()._build_prompt(
        {"prompt_text": "Hero enters the rain", "duration": 10},
        "",
        has_video=False,
    )

    assert "VISUAL REFERENCE" not in prompt


async def test_producer_shot_dict_carries_characters_into_video_analyzer_prompt(session):
    """The shot dict built by the creative-pipeline producer carries characters."""
    from app.services.creative_pipeline import build_shot_dict, shape_characters
    from app.services.story_bible import StoryBibleService
    from app.services.video_analyzer import VideoAnalyzer

    char = await _make_character(
        session,
        visual_prompt="white cloak",
        reference_sheet_url="/uploads/reference_sheets/sheet.png",
    )

    # Same source the /creative/render route uses to populate the pipeline config
    characters = shape_characters(
        await StoryBibleService(session).get_all_characters(str(char.project_id))
    )
    shot = build_shot_dict(
        0, "workspace/clip.mp4", {"format": {"duration": "4.5"}}, characters
    )

    assert shot["characters"] == [
        {
            "name": "Hero",
            "locked_traits": [],
            "visual_prompt": "white cloak",
            "reference_sheet_url": "/uploads/reference_sheets/sheet.png",
        }
    ]

    prompt = VideoAnalyzer()._build_prompt(shot, "", has_video=False)
    assert "VISUAL REFERENCE — Hero: white cloak" in prompt


async def test_creative_route_loads_project_characters_into_pipeline_config(
    client, monkeypatch, tmp_path
):
    """POST /creative/render fetches story-bible characters for the given project."""
    from app.api.routes import creative

    captured = {}

    class FakePipeline:
        def run(self, clip_paths, config):
            captured["config"] = config
            return {
                "final_output": "out.mp4",
                "video_only": "vid.mp4",
                "duration": 1.0,
                "shots": len(clip_paths),
                "mood": "calm",
                "music_crescendo": False,
                "edit_plan": {
                    "timeline_segments": [],
                    "speed_adjustments": [],
                    "color_grades": [],
                    "transition_points": [],
                },
            }

    monkeypatch.setattr(creative, "CreativePipeline", FakePipeline)

    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"fake")

    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    await client.post(
        f"/api/v1/projects/{proj['id']}/characters",
        json={"name": "Hero", "visual_prompt": "white cloak"},
    )

    resp = await client.post(
        "/api/v1/creative/render",
        json={"clip_paths": [str(clip)], "project_id": proj["id"]},
    )

    assert resp.status_code == 200
    characters = captured["config"].characters
    assert characters and characters[0]["name"] == "Hero"
    assert characters[0]["visual_prompt"] == "white cloak"
