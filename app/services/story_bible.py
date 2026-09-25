"""Story Bible Service - Tracks characters, props, and context across the production.

This is NOT a prompt injection system. It's a knowledge base that:
- Identifies characters in footage (via face embeddings)
- Maintains consistency across scenes
- Provides context for the Director AI
- Manages voice profiles for dubbing
"""

import uuid as uuid_mod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import AnchorFace, Character
from app.services.context_injector import ProductionContext


class StoryBibleService:
    """Story Bible - the production's knowledge base.

    Provides context about characters and their traits so the
    Director AI can make informed editing decisions and the QA
    system can verify consistency.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.context = ProductionContext()

    async def get_character(self, character_id: str) -> Character | None:
        """Get a character by ID (accepts str or UUID)."""
        try:
            cid = uuid_mod.UUID(str(character_id))
        except ValueError:
            return None
        result = await self.db.execute(select(Character).where(Character.id == cid))
        return result.scalar_one_or_none()

    async def get_character_by_name(self, name: str, project_id: str) -> Character | None:
        """Get a character by name within a project."""
        result = await self.db.execute(
            select(Character).where(
                Character.name == name, Character.project_id == project_id
            )
        )
        return result.scalar_one_or_none()

    async def get_character_context(self, character_id: str) -> dict | None:
        """Get character context for identification.

        Returns face references, traits, and the visual reference data
        (visual_prompt / reference_sheet_url) so the QA system can verify
        if a character in a shot matches the story bible and so prompt
        builders can inject `VISUAL REFERENCE — {name}: {visual_prompt}`.
        """
        character = await self.get_character(character_id)
        if not character:
            return None

        result = await self.db.execute(
            select(AnchorFace).where(AnchorFace.character_id == character.id)
        )
        anchor_faces = result.scalars().all()

        primary_face = next((f for f in anchor_faces if f.is_primary), None)

        return {
            "id": str(character.id),
            "name": character.name,
            "biography": character.biography,
            "visual_traits": character.locked_traits or [],
            "visual_prompt": character.visual_prompt,
            "reference_sheet_url": character.reference_sheet_url,
            "face_references": [
                {
                    "url": f.image_url,
                    "view_angle": f.view_angle,
                    "is_primary": f.is_primary,
                }
                for f in anchor_faces
            ],
            "primary_face_url": primary_face.image_url if primary_face else None,
            "voice_profile_id": character.voice_profile_id,
        }

    async def get_all_characters(self, project_id: str) -> list[dict]:
        """Get all characters in a project for identification context."""
        result = await self.db.execute(
            select(Character).where(Character.project_id == project_id)
        )
        characters = result.scalars().all()

        contexts = []
        for char in characters:
            ctx = await self.get_character_context(str(char.id))
            if ctx:
                contexts.append(ctx)
        return contexts

    async def identify_characters_in_shot(
        self, shot_description: str, detected_faces: list[str] | None = None
    ) -> list[dict]:
        """Identify which characters might be in a shot.

        Uses face embeddings for identification when available,
        falls back to description analysis otherwise.
        """
        identified = []

        if detected_faces:
            # Match detected faces against known embeddings
            for face_url in detected_faces:
                # In production: compare CLIP embeddings against stored anchors
                identified.append({
                    "face_url": face_url,
                    "match_confidence": 0.0,
                    "character_id": None,
                    "note": "Embedding comparison not yet implemented",
                })

        return identified

    async def get_scene_characters(self, scene_id: str) -> list[dict]:
        """Get all characters that appear in a scene's shots."""
        from app.models.shot import Shot

        result = await self.db.execute(
            select(Shot).where(Shot.scene_id == scene_id)
        )
        shots = result.scalars().all()

        character_ids = set()
        for shot in shots:
            if shot.speaker_character_id:
                character_ids.add(str(shot.speaker_character_id))

        characters = []
        for char_id in character_ids:
            ctx = await self.get_character_context(char_id)
            if ctx:
                characters.append(ctx)

        return characters

    async def get_voice_profile(self, character_id: str) -> dict | None:
        """Get voice profile for dubbing/TTS."""
        character = await self.get_character(character_id)
        if not character or not character.voice_profile_id:
            return None

        return {
            "character_id": str(character.id),
            "character_name": character.name,
            "voice_id": character.voice_profile_id,
        }

    def get_production_context(self, scene_data: dict, shots: list[dict]) -> str:
        """Get narrative context for a scene.

        Used by Director AI to understand story flow.
        """
        return self.context.get_narrative_context([], scene_data)
