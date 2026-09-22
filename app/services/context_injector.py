"""Production Context - Understands existing footage and provides context for editing."""

from dataclasses import dataclass, field


@dataclass
class ShotContext:
    """Context about a shot for the editing pipeline."""

    shot_id: str
    description: str
    characters_present: list[str] = field(default_factory=list)
    props_visible: list[str] = field(default_factory=list)
    environment: str = ""
    mood: str = ""
    dialogue: str = ""
    speaker: str = ""
    estimated_duration: float = 0.0


@dataclass
class SceneContext:
    """Context about a scene for narrative understanding."""

    scene_id: str
    scene_number: int
    location: str = ""
    time_of_day: str = ""
    characters_involved: list[str] = field(default_factory=list)
    summary: str = ""
    emotional_arc: str = ""


# Mood detection keywords
MOOD_KEYWORDS = {
    "tense": {"tension", "suspense", "waiting", "quiet", "stillness"},
    "action": {"fight", "chase", "run", "jump", "combat", "explosion"},
    "romantic": {"love", "kiss", "embrace", "gentle", "soft"},
    "melancholic": {"sad", "alone", "cry", "loss", "grief"},
    "joyful": {"laugh", "celebrate", "dance", "smile", "happy"},
}


class ProductionContext:
    """Provides context about the production for editing decisions.

    This is NOT a prompt injector for video generation.
    It understands existing footage and provides context to:
    - Director AI: for edit planning and narrative understanding
    - QA system: for consistency verification
    - NLE engine: for assembly decisions
    """

    def get_shot_context(self, shot_data: dict) -> ShotContext:
        """Build context from shot metadata and description.

        Used by Director AI to understand what's in each shot
        before making edit decisions.
        """
        description = shot_data.get("prompt_text", "")
        dialogue = shot_data.get("dialogue_text", "")

        return ShotContext(
            shot_id=str(shot_data.get("id", "")),
            description=description,
            dialogue=dialogue,
            mood=self._detect_mood(description),
            estimated_duration=self._estimate_duration(description, dialogue),
        )

    def get_scene_context(self, scene_data: dict, shots: list[dict]) -> SceneContext:
        """Build context for a scene from its shots.

        Used to understand narrative flow across shots.
        """
        all_characters = set()
        for shot in shots:
            if shot.get("speaker_character_id"):
                all_characters.add(str(shot["speaker_character_id"]))

        return SceneContext(
            scene_id=str(scene_data.get("id", "")),
            scene_number=scene_data.get("scene_number", 0),
            location=scene_data.get("location", ""),
            time_of_day=scene_data.get("time_of_day", ""),
            characters_involved=list(all_characters),
            summary=scene_data.get("summary", ""),
        )

    def detect_mood(self, text: str) -> str:
        """Detect the mood of a shot from its description."""
        return self._detect_mood(text)

    def _detect_mood(self, text: str) -> str:
        """Internal mood detection based on keywords."""
        words = set(text.lower().split())
        for mood, keywords in MOOD_KEYWORDS.items():
            if words & keywords:
                return mood
        return "neutral"

    def _estimate_duration(self, description: str, dialogue: str = "") -> float:
        """Estimate shot duration in seconds.

        Dialogue shots are longer. Action shots are shorter.
        """
        base_duration = 5.0

        # Dialogue adds time
        if dialogue:
            words = len(dialogue.split())
            base_duration += words * 0.3  # ~0.3s per word

        # Action keywords suggest faster cuts
        action_words = {"fight", "chase", "run", "jump", "combat", "explosion"}
        if set(description.lower().split()) & action_words:
            base_duration *= 0.7

        return base_duration

    def get_narrative_context(self, previous_scenes: list[dict], current_scene: dict) -> str:
        """Build narrative context from previous scenes.

        Used by Director AI to maintain story continuity.
        """
        if not previous_scenes:
            return f"Opening scene: {current_scene.get('location', 'unknown location')}"

        last_scene = previous_scenes[-1]
        return (
            f"Previous scene: {last_scene.get('location', 'unknown')} "
            f"(scene {last_scene.get('scene_number', '?')}). "
            f"Current: Scene {current_scene.get('scene_number', '?')} "
            f"at {current_scene.get('location', 'unknown location')}"
        )
