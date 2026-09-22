from pathlib import Path

from app.providers.base import format_character_block


def test_format_includes_visual_reference_block():
    chars = [
        {"name": "Hero", "locked_traits": ["brave"], "visual_prompt": "white cloak"},
        {"name": "Villain", "locked_traits": [], "visual_prompt": None},
    ]
    block = format_character_block(chars)
    assert "VISUAL REFERENCE — Hero: white cloak" in block
    assert "Hero: brave" in block
    assert "VISUAL REFERENCE — Villain" not in block


def test_google_builds_image_part_only_when_file_exists(tmp_path, monkeypatch):
    from app.providers import google as g

    monkeypatch.setattr(g, "resolve_sheet_path", lambda url: None)
    assert g.resolve_sheet_path("/uploads/reference_sheets/missing.png") is None

    f = tmp_path / "sheet.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n")
    resolved = f
    assert resolved is not None