"""Render service for orchestrating shot rendering via the NLE client."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.render_job import RenderJob
from app.models.shot import Shot
from app.schemas.render_job import RenderJobRead
from app.services.nle_client import NLEClient
from app.services.story_bible import StoryBibleService
from app.services.context_injector import ContextInjector


class RenderService:
    """Orchestrates rendering: inject prompt, create RenderJob, delegate to NLE."""

    def __init__(self, db: AsyncSession, nle_client: NLEClient | None = None):
        self.db = db
        self.nle = nle_client or NLEClient()
        self.injector = ContextInjector()

    async def start_render(self, shot_id: str, engine_name: str) -> RenderJobRead:
        """Start a render job for a shot.

        1. Fetch the shot and inject context into its prompt.
        2. Create a RenderJob record.
        3. Submit a pipeline request to the NLE server.
        4. Return the created job.
        """
        shot = await self.db.get(Shot, shot_id)
        if not shot:
            raise ValueError(f"Shot {shot_id} not found")

        injected_prompt = self._build_injected_prompt(shot)
        shot.injected_prompt = injected_prompt

        job = RenderJob(
            shot_id=shot.id,
            engine_name=engine_name,
            status="QUEUED",
        )
        self.db.add(job)
        await self.db.flush()

        await self.nle.pipeline(
            {
                "shot_id": str(shot.id),
                "job_id": str(job.id),
                "engine": engine_name,
                "prompt": injected_prompt,
            }
        )

        job.status = "SUBMITTED"
        await self.db.commit()
        await self.db.refresh(job)
        return RenderJobRead.model_validate(job)

    async def get_job(self, job_id: str) -> RenderJobRead | None:
        """Get a render job by ID."""
        job = await self.db.get(RenderJob, job_id)
        if not job:
            return None
        return RenderJobRead.model_validate(job)

    def _build_injected_prompt(self, shot: Shot) -> str:
        """Build the full injected prompt for a shot."""
        prompt = shot.prompt_text
        if shot.assigned_engine:
            prompt = f"{prompt} [engine:{shot.assigned_engine}]"
        return self.injector.inject_global_style(prompt)
