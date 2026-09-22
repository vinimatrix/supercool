"""Anchor face routes for character reference images."""

import uuid as uuid_mod
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import AnchorFace, Character
from app.schemas.character import AnchorFaceRead

router = APIRouter(tags=["anchor-faces"])

UPLOAD_DIR = Path("uploads/anchor_faces")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/characters/{character_id}/anchor-faces", response_model=AnchorFaceRead)
async def create_anchor_face(
    character_id: uuid_mod.UUID,
    file: UploadFile = File(...),
    view_angle: str | None = Form(None),
    is_primary: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    """Upload an anchor face image for a character."""
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    ext = Path(file.filename or "image.png").suffix or ".png"
    filename = f"{uuid_mod.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    image_url = f"/uploads/anchor_faces/{filename}"

    face = AnchorFace(
        character_id=character_id,
        image_url=image_url,
        view_angle=view_angle,
        is_primary=is_primary,
    )
    db.add(face)
    await db.commit()
    await db.refresh(face)
    return face


@router.get("/characters/{character_id}/anchor-faces", response_model=list[AnchorFaceRead])
async def list_anchor_faces(
    character_id: uuid_mod.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all anchor faces for a character."""
    result = await db.execute(
        select(AnchorFace).where(AnchorFace.character_id == character_id)
    )
    return result.scalars().all()


@router.delete("/anchor-faces/{face_id}")
async def delete_anchor_face(
    face_id: uuid_mod.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an anchor face."""
    face = await db.get(AnchorFace, face_id)
    if not face:
        raise HTTPException(status_code=404, detail="Anchor face not found")

    filepath = Path(face.image_url.lstrip("/"))
    if filepath.exists():
        filepath.unlink()

    await db.delete(face)
    await db.commit()
    return {"status": "deleted"}
