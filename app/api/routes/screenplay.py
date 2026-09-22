"""Screenplay API - Parse scripts and generate outlines."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.project import Project
from app.models.scene import Scene
from app.models.shot import Shot

router = APIRouter(prefix="/screenplay", tags=["screenplay"])


class ScreenplayParseRequest(BaseModel):
    text: str
    format: str = "text"  # text, pdf, fdx


class ScreenplayParseResponse(BaseModel):
    project_id: UUID
    scenes_created: int
    shots_created: int
    summary: str


class SceneOutline(BaseModel):
    scene_id: UUID
    scene_number: int
    title: str | None
    location: str | None
    shot_count: int


@router.post("/parse", response_model=ScreenplayParseResponse)
async def parse_screenplay(data: ScreenplayParseRequest, db: AsyncSession = Depends(get_db)):
    """Parse raw script text into scenes and shots."""
    # Create a new project for this screenplay
    project = Project(title="Screenplay Import", description=data.text[:200])
    db.add(project)
    await db.flush()
    
    # Simple line-based parser
    scenes_created = 0
    shots_created = 0
    current_scene = None
    scene_number = 0
    
    for line in data.text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        
        # Detect scene headings (INT./EXT.)
        if line.upper().startswith(("INT.", "EXT.", "INT/EXT")):
            scene_number += 1
            current_scene = Scene(
                project_id=project.id,
                scene_number=scene_number,
                title=line[:255],
                location=line[:255],
            )
            db.add(current_scene)
            await db.flush()
            scenes_created += 1
            continue
        
        # Detect action/description lines as shots
        if current_scene and len(line) > 20:
            shot = Shot(
                scene_id=current_scene.id,
                shot_number=shots_created + 1,
                prompt_text=line,
                status="PENDING",
            )
            db.add(shot)
            shots_created += 1
    
    await db.commit()
    
    return ScreenplayParseResponse(
        project_id=project.id,
        scenes_created=scenes_created,
        shots_created=shots_created,
        summary=f"Parsed {scenes_created} scenes and {shots_created} shots from screenplay.",
    )


@router.get("/{project_id}/outline", response_model=list[SceneOutline])
async def get_outline(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get structured outline of scenes for a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get scenes with shot counts
    scenes_result = await db.execute(
        select(Scene).where(Scene.project_id == project_id).order_by(Scene.scene_number)
    )
    scenes = scenes_result.scalars().all()
    
    outlines = []
    for scene in scenes:
        shots_result = await db.execute(
            select(Shot).where(Shot.scene_id == scene.id)
        )
        shot_count = len(shots_result.scalars().all())
        outlines.append(SceneOutline(
            scene_id=scene.id,
            scene_number=scene.scene_number,
            title=scene.title,
            location=scene.location,
            shot_count=shot_count,
        ))
    
    return outlines
