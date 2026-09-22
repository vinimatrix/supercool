from app.services.context_injector import ProductionContext


def test_mood_detection():
    ctx = ProductionContext()
    assert ctx.detect_mood("fight and chase") == "action"
    assert ctx.detect_mood("sad and alone") == "melancholic"
    assert ctx.detect_mood("quiet stillness") == "tense"
    assert ctx.detect_mood("random neutral text") == "neutral"


def test_duration_estimation():
    ctx = ProductionContext()
    d1 = ctx._estimate_duration("run and jump")
    d2 = ctx._estimate_duration("stand still")
    assert d1 < d2  # action shots are shorter

    d3 = ctx._estimate_duration("talk", "hello world one two three four five")
    assert d3 > d2  # dialogue shots are longer


def test_shot_context():
    ctx = ProductionContext()
    shot = {"id": "1", "prompt_text": "fight scene", "dialogue_text": "Let's go!"}
    sc = ctx.get_shot_context(shot)
    assert sc.shot_id == "1"
    assert sc.mood == "action"
    assert sc.estimated_duration > 0


def test_scene_context():
    ctx = ProductionContext()
    scene = {"id": "s1", "scene_number": 1, "location": "warehouse"}
    shots = [{"speaker_character_id": "c1"}, {"speaker_character_id": "c2"}]
    sc = ctx.get_scene_context(scene, shots)
    assert sc.location == "warehouse"
    assert len(sc.characters_involved) == 2


def test_narrative_context():
    ctx = ProductionContext()
    result = ctx.get_narrative_context([], {"scene_number": 1, "location": "warehouse"})
    assert "Opening scene" in result
    assert "warehouse" in result
