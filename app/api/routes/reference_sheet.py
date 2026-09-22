"""Reference sheet routes for character reference images."""

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