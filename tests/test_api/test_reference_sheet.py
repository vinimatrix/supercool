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


async def test_upload_rejects_oversized_body_with_413(client, tmp_path, monkeypatch):
    import app.api.routes.reference_sheet as rs

    monkeypatch.setattr(rs, "UPLOAD_DIR", tmp_path)
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()

    big = b"\x89PNG\r\n\x1a\n" + b"\0" * (rs.MAX_BYTES + 1024)
    resp = await client.post(
        f"/api/v1/characters/{char['id']}/reference-sheet",
        files={"file": ("big.png", io.BytesIO(big), "image/png")},
    )
    assert resp.status_code == 413
    assert list(tmp_path.iterdir()) == []


async def test_upload_stores_extension_from_content_type_not_filename(
    client, tmp_path, monkeypatch
):
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
        files={"file": ("evil.html", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
    )

    assert resp.status_code == 200
    url = resp.json()["reference_sheet_url"]
    assert url.endswith(".png")
    assert not url.endswith(".html")
    stored = tmp_path / url.rsplit("/", 1)[-1]
    assert stored.exists()
    assert stored.suffix == ".png"


async def test_upload_rejects_large_content_length_before_reading_body():
    import uuid as uuid_mod

    import pytest
    from fastapi import HTTPException
    from starlette.datastructures import Headers, UploadFile
    from starlette.requests import Request

    import app.api.routes.reference_sheet as rs

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": "/reference-sheet",
        "query_string": b"",
        "headers": [(b"content-length", str(rs.MAX_BYTES + 1024 * 1024).encode())],
    }
    request = Request(scope)

    class ExplodingFile(io.BytesIO):
        def read(self, *args, **kwargs):
            raise AssertionError("body must not be read before size check")

    file = UploadFile(
        file=ExplodingFile(b"data"),
        filename="sheet.png",
        headers=Headers({"content-type": "image/png"}),
    )

    with pytest.raises(HTTPException) as exc:
        await rs.upload_reference_sheet(
            request, uuid_mod.uuid4(), file=file, db=None
        )
    assert exc.value.status_code == 413


async def test_upload_reads_in_bounded_chunks_until_limit():
    import uuid as uuid_mod

    import pytest
    from fastapi import HTTPException
    from starlette.datastructures import Headers, UploadFile
    from starlette.requests import Request

    import app.api.routes.reference_sheet as rs

    class TrackingFile(io.BytesIO):
        def __init__(self, data):
            super().__init__(data)
            self.read_sizes = []

        def read(self, size=-1):
            self.read_sizes.append(size)
            return super().read(size)

    class _FakeChar:
        reference_sheet_url = None

    class _FakeDB:
        async def get(self, *args, **kwargs):
            return _FakeChar()

    payload = b"x" * (rs.MAX_BYTES + 1024)
    tracking = TrackingFile(payload)
    file = UploadFile(
        file=tracking,
        filename="sheet.png",
        headers=Headers({"content-type": "image/png"}),
    )
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": "/reference-sheet",
        "query_string": b"",
        "headers": [],
    }
    request = Request(scope)

    with pytest.raises(HTTPException) as exc:
        await rs.upload_reference_sheet(
            request, uuid_mod.uuid4(), file=file, db=_FakeDB()
        )
    assert exc.value.status_code == 413
    assert tracking.read_sizes, "expected chunked reads"
    assert all(size > 0 for size in tracking.read_sizes)
    assert max(tracking.read_sizes) <= rs.MAX_BYTES