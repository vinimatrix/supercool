"""Reference sheet routes for character reference images."""

import uuid as uuid_mod
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character

router = APIRouter(tags=["reference-sheet"])

UPLOAD_DIR = Path("uploads/reference_sheets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_BYTES = 5 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
# Multipart framing (boundaries + part headers) sits on top of the raw file bytes.
CONTENT_LENGTH_OVERHEAD = 16 * 1024
# Stored extension is derived from the validated content type, never from the
# client filename (a `evil.html` upload with Content-Type image/png must not be
# stored as .html and served as HTML).
EXT_BY_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


async def _read_limited(file: UploadFile) -> bytes:
    """Read the upload in bounded chunks, aborting once it exceeds MAX_BYTES."""
    buf = bytearray()
    while True:
        chunk = await file.read(CHUNK_BYTES)
        if not chunk:
            break
        buf += chunk
        if len(buf) > MAX_BYTES:
            raise HTTPException(status_code=413, detail="Image too large (max 5MB)")
    return bytes(buf)


@router.post("/characters/{character_id}/reference-sheet")
async def upload_reference_sheet(
    request: Request,
    character_id: uuid_mod.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and (
        int(content_length) > MAX_BYTES + CONTENT_LENGTH_OVERHEAD
    ):
        raise HTTPException(status_code=413, detail="Image too large (max 5MB)")

    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File must be an image")
    content = await _read_limited(file)

    if char.reference_sheet_url:
        old = Path(char.reference_sheet_url.lstrip("/"))
        if old.exists():
            old.unlink()

    filename = f"{uuid_mod.uuid4()}{EXT_BY_TYPE[file.content_type]}"
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