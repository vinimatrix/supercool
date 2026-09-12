"""Story Bible Service for managing character context and shot prompts."""

from sqlalchemy.orm import Session

from app.models.character import AnchorFace, Character
from app.providers.registry import ProviderRegistry
from app.services.context_injector import ContextInjector


class StoryBibleService:
    """Story Bible service for character context and prompt injection."""

    def __init__(self, db: Session, provider_registry: ProviderRegistry):
        self.db = db
        self.registry = provider_registry
        self.injector = ContextInjector()

    def get_character(self, character_id: str) -> Character | None:
        """Get a character by ID."""
        return self.db.query(Character).filter(Character.id == character_id).first()

    def get_character_by_name(self, name: str, project_id: str) -> Character | None:
        """Get a character by name within a project."""
        return (
            self.db.query(Character)
            .filter(Character.name == name, Character.project_id == project_id)
            .first()
        )

    def get_character_context(self, character_id: str) -> dict | None:
        """Get character context including traits and face references."""
        character = self.get_character(character_id)
        if not character:
            return None

        anchor_faces = (
            self.db.query(AnchorFace)
            .filter(AnchorFace.character_id == character_id)
            .all()
        )

        primary_face = next((f for f in anchor_faces if f.is_primary), None)

        return {
            "id": str(character.id),
            "name": character.name,
            "biography": character.biography,
            "locked_traits": character.locked_traits or [],
            "face_references": [
                {"url": f.image_url, "view_angle": f.view_angle, "is_primary": f.is_primary}
                for f in anchor_faces
            ],
            "primary_face_url": primary_face.image_url if primary_face else None,
        }

    def extract_entities(self, text: str) -> list[dict]:
        """Extract character entities from text using LLM."""
        provider = self.registry.get_provider()
        if not provider:
            return []

        prompt = f"""Extract character names and descriptions from this text.
Return as JSON array with "name" and "description" fields.

Text: {text}

Response:"""

        try:
            response = provider.generate(prompt)
            import json
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            return []

    def inject_shot_prompt(
        self,
        shot_description: str,
        character_ids: list[str],
        ref_images: dict[str, str] | None = None,
    ) -> str:
        """Inject full context into a shot prompt."""
        context_parts = []
        all_traits = []

        for char_id in character_ids:
            ctx = self.get_character_context(char_id)
            if ctx:
                context_parts.append(f"{ctx['name']}: {ctx['biography'] or ''}")
                all_traits.extend(ctx["locked_traits"])

        prompt = shot_description
        if all_traits:
            prompt = self.injector.inject_locked_traits(prompt, all_traits)

        if ref_images:
            for char_id, ref_url in ref_images.items():
                prompt = self.injector.inject_reference_tag(prompt, ref_url)

        prompt = self.injector.inject_global_style(prompt)

        return prompt

    def get_negative_prompt(self) -> str:
        """Get the negative prompt."""
        return self.injector.get_negative_prompt()

    def detect_engine(self, prompt: str) -> str:
        """Detect the appropriate engine for a prompt."""
        return self.injector.detect_engine(prompt)