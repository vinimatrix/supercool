from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.character import CharacterCreate, CharacterRead, AnchorFaceCreate, AnchorFaceRead
from app.schemas.scene import SceneCreate, SceneRead
from app.schemas.shot import ShotCreate, ShotRead
from app.schemas.render_job import RenderJobCreate, RenderJobRead


def test_project_create_schema():
    p = ProjectCreate(title="Test")
    assert p.title == "Test"
    assert p.fps == 24


def test_project_read_schema():
    from datetime import datetime
    from uuid import uuid4

    p = ProjectRead(
        id=uuid4(),
        title="Test",
        target_resolution="4K",
        fps=24,
        aspect_ratio="16:9",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert p.id is not None
    assert p.title == "Test"


def test_character_create_schema():
    c = CharacterCreate(name="Boruto", locked_traits=["scar"])
    assert c.name == "Boruto"
    assert c.locked_traits == ["scar"]


def test_character_read_schema():
    from datetime import datetime
    from uuid import uuid4

    c = CharacterRead(
        id=uuid4(),
        project_id=uuid4(),
        name="Boruto",
        locked_traits=["scar"],
        created_at=datetime.now(),
    )
    assert c.name == "Boruto"


def test_anchor_face_create_schema():
    a = AnchorFaceCreate(image_url="https://example.com/face.jpg")
    assert a.image_url == "https://example.com/face.jpg"
    assert a.is_primary is False


def test_anchor_face_read_schema():
    from datetime import datetime
    from uuid import uuid4

    a = AnchorFaceRead(
        id=uuid4(),
        character_id=uuid4(),
        image_url="https://example.com/face.jpg",
        is_primary=True,
        created_at=datetime.now(),
    )
    assert a.image_url == "https://example.com/face.jpg"
    assert a.is_primary is True


def test_scene_create_schema():
    s = SceneCreate(scene_number=1)
    assert s.scene_number == 1


def test_scene_read_schema():
    from datetime import datetime
    from uuid import uuid4

    s = SceneRead(
        id=uuid4(),
        project_id=uuid4(),
        scene_number=1,
        created_at=datetime.now(),
    )
    assert s.scene_number == 1


def test_shot_create_schema():
    s = ShotCreate(shot_number=1, prompt_text="A warrior")
    assert s.prompt_text == "A warrior"
    assert s.status == "PENDING"


def test_shot_read_schema():
    from datetime import datetime
    from uuid import uuid4

    s = ShotRead(
        id=uuid4(),
        scene_id=uuid4(),
        shot_number=1,
        prompt_text="A warrior",
        status="PENDING",
        created_at=datetime.now(),
    )
    assert s.prompt_text == "A warrior"


def test_render_job_create_schema():
    r = RenderJobCreate(engine_name="kling")
    assert r.engine_name == "kling"


def test_render_job_read_schema():
    from datetime import datetime
    from decimal import Decimal
    from uuid import uuid4

    r = RenderJobRead(
        id=uuid4(),
        shot_id=uuid4(),
        engine_name="kling",
        status="PENDING",
        retry_count=0,
        created_at=datetime.now(),
    )
    assert r.engine_name == "kling"
    assert r.retry_count == 0
