import pytest
from app.models.project import Project
from app.models.character import Character, AnchorFace
from app.models.scene import Scene
from app.models.shot import Shot
from app.models.render_job import RenderJob


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
