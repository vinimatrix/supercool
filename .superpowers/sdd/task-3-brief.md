### Task 3: Reference sheet upload/DELETE routes

**Files:**
- Create: `app/api/routes/reference_sheet.py`
- Modify: `app/main.py` (include router)
- Test: `tests/test_api/test_reference_sheet.py`

**Interfaces:**
- Consumes: `Character.reference_sheet_url` (Task 1).
- Produces:
  - `POST /api/v1/characters/{character_id}/reference-sheet` (multipart `file`) → `CharacterRead`
  - `DELETE /api/v1/characters/{character_id}/reference-sheet` → `CharacterRead`
  - Files under `uploads/reference_sheets/`; URL `/uploads/reference_sheets/{filename}` (already mounted in `main.py`).

- [ ] **Step 1: Write failing tests**

Create `tests/test_api/test_reference_sheet.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api/test_reference_sheet.py -v`
Expected: FAIL (404/405 — no route)

- [ ] **Step 3: Implement route module**

Create `app/api/routes/reference_sheet.py`:

```python
import uuid as uuid_mod
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character

router = APIRouter(tags=["reference-sheet"])

UPLOAD_DIR = Path("uploads/reference_sheets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_BYTES = 5 * 1024 * 1024


@router.post("/characters/{character_id}/reference-sheet")
async def upload_reference_sheet(
    character_id: uuid_mod.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File must be an image")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 5MB)")

    if char.reference_sheet_url:
        old = Path(char.reference_sheet_url.lstrip("/"))
        if old.exists():
            old.unlink()

    ext = Path(file.filename or "sheet.png").suffix or ".png"
    filename = f"{uuid_mod.uuid4()}{ext}"
    (UPLOAD_DIR / filename).write_bytes(content)
    char.reference_sheet_url = f"/uploads/reference_sheets/{filename}"
    await db.commit()
    await db.refresh(char)
    return char


@router.delete("/characters/{character_id}/reference-sheet")
async def delete_reference_sheet(
    character_id: uuid_mod.UUID,
    db: AsyncSession = Depends(get_db),
):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if char.reference_sheet_url:
        path = Path(char.reference_sheet_url.lstrip("/"))
        if path.exists():
            path.unlink()
        char.reference_sheet_url = None
        await db.commit()
        await db.refresh(char)
    return char
```

- [ ] **Step 4: Register in main.py**

Add `reference_sheet` to imports; after anchor_faces include:

```python
    app.include_router(reference_sheet.router, prefix="/api/v1")
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_api/test_reference_sheet.py tests/test_api/test_characters.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/api/routes/reference_sheet.py app/main.py tests/test_api/test_reference_sheet.py
git commit -m "feat: character reference sheet upload and delete endpoints"
```

---

