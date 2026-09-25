"""Render service for orchestrating shot rendering via the NLE client."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.render_job import RenderJob
from app.models.shot import Shot
from app.providers.base import format_visual_references
from app.schemas.render_job import RenderJobRead
from app.services.context_injector import ProductionContext
from app.services.story_bible import StoryBibleService


class RenderService:
    """Orchestrates rendering: inject prompt, create RenderJob, delegate to NLE."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ctx = ProductionContext()

    async def start_render(self, shot_id: str, engine_name: str) -> RenderJobRead:
        """Start a render job for a shot.

        1. Fetch the shot and inject context into its prompt.
        2. Create a RenderJob record.
        3. Dispatch background Celery task.
        4. Return the created job.
        """
        shot = await self.db.get(Shot, uuid.UUID(shot_id))
        if not shot:
            raise ValueError(f"Shot {shot_id} not found")

        characters = await self._load_character_context(shot)
        injected_prompt = self._build_injected_prompt(shot, characters)
        shot.injected_prompt = injected_prompt

        job = RenderJob(
            shot_id=shot.id,
            engine_name=engine_name,
            status="QUEUED",
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(job)

        self._dispatch_render_task(job, shot, injected_prompt)

        return RenderJobRead.model_validate(job)

    async def get_job(self, job_id: str) -> RenderJobRead | None:
        """Get a render job by ID."""
        job = await self.db.get(RenderJob, uuid.UUID(job_id))
        if not job:
            return None
        return RenderJobRead.model_validate(job)

    async def _load_character_context(self, shot: Shot) -> list[dict]:
        """Load story-bible context (incl. visual_prompt) for the shot's speaker."""
        if not shot.speaker_character_id:
            return []
        ctx = await StoryBibleService(self.db).get_character_context(
            str(shot.speaker_character_id)
        )
        return [ctx] if ctx else []

    def _build_injected_prompt(
        self, shot: Shot, characters: list[dict] | None = None
    ) -> str:
        """Build context summary for the shot, plus visual references if any."""
        shot_ctx = self.ctx.get_shot_context({
            "id": str(shot.id),
            "prompt_text": shot.prompt_text or "",
            "dialogue_text": shot.dialogue_text or "",
        })
        engine = shot.assigned_engine or "FLOW"
        summary = (
            f"Mood: {shot_ctx.mood}, "
            f"Duration: {shot_ctx.estimated_duration:.1f}s, "
            f"Engine: {engine}"
        )
        visual = format_visual_references(characters or [])
        if visual:
            summary = f"{summary}\n{visual}"
        return summary

    def _dispatch_render_task(self, job: RenderJob, shot: Shot, injected_prompt: str):
        """Dispatch the Celery render task. Fails silently if Redis is unavailable."""
        try:
            from app.tasks.render_tasks import process_render

            process_render.delay(
                job_id=str(job.id),
                shot_id=str(shot.id),
                engine_name=job.engine_name,
                injected_prompt=injected_prompt,
            )
        except Exception:
            pass
