from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.shot import Shot
from app.providers.base import format_visual_references
from app.schemas.shot import (
    GenerateRequest,
    GenerateResponse,
    InjectContextRequest,
    InjectContextResponse,
    ShotCreate,
    ShotRead,
    ShotUpdate,
)
from app.services.context_injector import ProductionContext
from app.services.story_bible import StoryBibleService

router = APIRouter(tags=["shots"])

WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)


@router.post("/scenes/{scene_id}/shots", response_model=ShotRead)
async def create_shot(scene_id: UUID, data: ShotCreate, db: AsyncSession = Depends(get_db)):
    shot = Shot(scene_id=scene_id, **data.model_dump())
    db.add(shot)
    await db.commit()
    await db.refresh(shot)
    return shot


@router.get("/scenes/{scene_id}/shots", response_model=list[ShotRead])
async def list_shots(scene_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shot).where(Shot.scene_id == scene_id))
    return result.scalars().all()


@router.post("/shots/{shot_id}/upload-video", response_model=ShotRead)
async def upload_shot_video(
    shot_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """Upload video clip to a shot."""
    result = await db.execute(select(Shot).where(Shot.id == shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    # Save file to workspace
    shot_dir = WORKSPACE / "shots"
    shot_dir.mkdir(exist_ok=True)
    file_path = shot_dir / f"{shot_id}{Path(file.filename).suffix}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update shot with video path
    shot.video_path = str(file_path)
    shot.status = "CLIP_ASSIGNED"
    await db.commit()
    await db.refresh(shot)
    return shot


@router.put("/shots/{shot_id}/assign-video")
async def assign_shot_video(shot_id: UUID, data: dict, db: AsyncSession = Depends(get_db)):
    """Assign existing workspace video to a shot."""
    result = await db.execute(select(Shot).where(Shot.id == shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    shot.video_path = data.get("video_path")
    shot.status = "CLIP_ASSIGNED" if shot.video_path else "PENDING"
    await db.commit()
    await db.refresh(shot)
    return ShotRead.model_validate(shot)


@router.put("/shots/{shot_id}", response_model=ShotRead)
async def update_shot(shot_id: UUID, data: ShotUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shot).where(Shot.id == shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(shot, field, value)
    await db.commit()
    await db.refresh(shot)
    return shot


@router.post("/shots/{shot_id}/inject-context", response_model=InjectContextResponse)
async def inject_context(
    shot_id: UUID, data: InjectContextRequest, db: AsyncSession = Depends(get_db)
):
    """Analyze a shot and return context for the editing pipeline.

    This does NOT inject prompts for video generation.
    It analyzes the shot and returns:
    - Detected mood
    - Estimated duration
    - Characters present (from DB)
    - Assigned engine for processing
    """
    result = await db.execute(select(Shot).where(Shot.id == shot_id))
    shot = result.scalar_one_or_none()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    ctx = ProductionContext()
    shot_ctx = ctx.get_shot_context({
        "id": str(shot.id),
        "prompt_text": shot.prompt_text or "",
        "dialogue_text": shot.dialogue_text or "",
        "speaker_character_id": (
            str(shot.speaker_character_id) if shot.speaker_character_id else None
        ),
    })

    # Determine processing engine based on content
    engine = "FLOW"  # Default for dialogue/atmospheric
    if shot.motion_type:
        if "ACTION" in shot.motion_type.upper():
            engine = "SEEDANCE"
        elif "ATMOSPHERIC" in shot.motion_type.upper():
            engine = "FLOW"

    # Build context summary (not an injected prompt)
    context_summary = f"Mood: {shot_ctx.mood}, Duration: {shot_ctx.estimated_duration:.1f}s"
    if shot_ctx.characters_present:
        context_summary += f", Characters: {', '.join(shot_ctx.characters_present)}"

    if shot.speaker_character_id:
        char_ctx = await StoryBibleService(db).get_character_context(
            str(shot.speaker_character_id)
        )
        if char_ctx:
            visual = format_visual_references([char_ctx])
            if visual:
                context_summary = f"{context_summary}\n{visual}"

    shot.injected_prompt = context_summary
    shot.assigned_engine = engine
    await db.commit()

    return InjectContextResponse(
        shot_id=shot.id,
        original_prompt=shot.prompt_text or "",
        injected_prompt=context_summary,
        engine=engine,
        negative_prompt="",  # Not applicable for footage analysis
    )


@router.post("/shots/generate", response_model=GenerateResponse)
async def generate_shots(data: GenerateRequest, db: AsyncSession = Depends(get_db)):
    """Prepare shots for the editing pipeline.

    Analyzes each shot and assigns:
    - Processing engine (FLOW for dialogue, SEEDANCE for action)
    - Context metadata for the Director AI
    - Status update to READY_FOR_EDIT
    """
    stmt = select(Shot).where(Shot.scene_id == data.scene_id)
    if data.shot_ids:
        stmt = stmt.where(Shot.id.in_(data.shot_ids))
    result = await db.execute(stmt)
    shots = result.scalars().all()

    ctx = ProductionContext()
    count = 0
    for shot in shots:
        shot_ctx = ctx.get_shot_context({
            "id": str(shot.id),
            "prompt_text": shot.prompt_text or "",
            "dialogue_text": shot.dialogue_text or "",
        })

        # Assign engine based on motion type
        engine = "FLOW"
        if shot.motion_type and "ACTION" in shot.motion_type.upper():
            engine = "SEEDANCE"

        shot.injected_prompt = (
            f"Mood: {shot_ctx.mood}, Duration: {shot_ctx.estimated_duration:.1f}s"
        )
        shot.assigned_engine = engine
        shot.status = "READY_FOR_EDIT"
        count += 1

    await db.commit()

    return GenerateResponse(
        scene_id=data.scene_id,
        shots_queued=count,
        status="queued",
    )
