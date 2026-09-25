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


def test_google_builds_image_part_only_when_file_exists(tmp_path):
    from app.providers import google as g

    missing = tmp_path / "missing.png"
    assert g.resolve_sheet_path(str(missing)) is None

    f = tmp_path / "sheet.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n")
    resolved = g.resolve_sheet_path(str(f))
    assert resolved == f


class _FakeGeminiResponse:
    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}


class _FakeAsyncClient:
    captured = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, timeout=None):
        type(self).captured = json
        return _FakeGeminiResponse()


async def test_google_generate_prompt_mime_follows_sheet_suffix(monkeypatch, tmp_path):
    from app.providers import google as g

    monkeypatch.setattr(g.httpx, "AsyncClient", _FakeAsyncClient)

    sheet = tmp_path / "sheet.webp"
    sheet.write_bytes(b"RIFF____WEBP")
    chars = [
        {
            "name": "Hero",
            "locked_traits": [],
            "visual_prompt": "white cloak",
            "reference_sheet_url": str(sheet),
        }
    ]

    await g.GoogleProvider().generate_prompt("A hero appears", chars)

    parts = _FakeAsyncClient.captured["contents"][0]["parts"]
    images = [p for p in parts if "inline_data" in p]
    assert len(images) == 1
    assert images[0]["inline_data"]["mime_type"] == "image/webp"
    assert "VISUAL REFERENCE — Hero: white cloak" in parts[0]["text"]


async def test_google_generate_prompt_skips_missing_sheet_without_failing(
    monkeypatch, tmp_path
):
    from app.providers import google as g

    monkeypatch.setattr(g.httpx, "AsyncClient", _FakeAsyncClient)

    chars = [
        {
            "name": "Hero",
            "locked_traits": [],
            "visual_prompt": "white cloak",
            "reference_sheet_url": str(tmp_path / "gone.png"),
        }
    ]

    await g.GoogleProvider().generate_prompt("A hero appears", chars)

    parts = _FakeAsyncClient.captured["contents"][0]["parts"]
    assert not [p for p in parts if "inline_data" in p]
    assert "VISUAL REFERENCE — Hero: white cloak" in parts[0]["text"]