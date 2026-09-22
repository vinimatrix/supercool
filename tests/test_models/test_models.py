import pytest
from app.models.project import Project
from app.models.character import Character, AnchorFace
from app.models.scene import Scene
from app.models.shot import Shot
from app.models.render_job import RenderJob
from app.schemas.character import CharacterCreate, CharacterRead


def test_project_model():
    p = Project(title="Test Film", description="A test", fps=24, target_resolution="4K")
    assert p.title == "Test Film"
    assert p.fps == 24
    assert p.target_resolution == "4K"


def test_character_model():
    c = Character(name="Boruto", locked_traits=["scar", "cape"])
    assert c.name == "Boruto"
    assert c.locked_traits == ["scar", "cape"]


def test_shot_model():
    s = Shot(prompt_text="A warrior stands", status="PENDING")
    assert s.status == "PENDING"


def test_character_has_reference_fields():
    c = Character(name="Hero")
    assert hasattr(c, "reference_sheet_url")
    assert hasattr(c, "visual_prompt")


def test_character_schemas_expose_visual_prompt():
    create = CharacterCreate(name="Hero", visual_prompt="scar over left eye")
    assert create.visual_prompt == "scar over left eye"
    read = CharacterRead.model_validate(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "project_id": "00000000-0000-0000-0000-000000000002",
            "name": "Hero",
            "biography": None,
            "locked_traits": [],
            "voice_profile_id": None,
            "created_at": "2026-01-01T00:00:00",
            "reference_sheet_url": "/uploads/reference_sheets/a.png",
            "visual_prompt": "tall",
        }
    )
    assert read.reference_sheet_url.endswith("a.png")
    assert read.visual_prompt == "tall"
