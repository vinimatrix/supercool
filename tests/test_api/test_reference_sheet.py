import io


async def test_upload_and_delete_reference_sheet(client, tmp_path, monkeypatch):
    import app.api.routes.reference_sheet as rs

    monkeypatch.setattr(rs, "UPLOAD_DIR", tmp_path)
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()

    resp = await client.post(
        f"/api/v1/characters/{char['id']}/reference-sheet",
        files={"file": ("sheet.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
    )
    assert resp.status_code == 200
    url = resp.json()["reference_sheet_url"]
    assert url.startswith("/uploads/reference_sheets/")

    resp = await client.delete(f"/api/v1/characters/{char['id']}/reference-sheet")
    assert resp.status_code == 200
    assert resp.json()["reference_sheet_url"] is None


async def test_upload_rejects_non_image(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()
    resp = await client.post(
        f"/api/v1/characters/{char['id']}/reference-sheet",
        files={"file": ("evil.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


async def test_upload_character_not_found(client):
    resp = await client.post(
        "/api/v1/characters/00000000-0000-0000-0000-000000000099/reference-sheet",
        files={"file": ("s.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
    )
    assert resp.status_code == 404