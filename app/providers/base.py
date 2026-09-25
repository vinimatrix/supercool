import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


def format_visual_references(characters: list[dict]) -> str:
    """Format `VISUAL REFERENCE — {name}: {visual_prompt}` lines for characters."""
    lines = []
    for c in characters:
        vp = c.get("visual_prompt")
        if vp and c.get("name"):
            lines.append(f"VISUAL REFERENCE — {c['name']}: {vp}")
    return "\n".join(lines)


def format_character_block(characters: list[dict]) -> str:
    lines = []
    for c in characters:
        traits = ", ".join(c.get("locked_traits", []))
        lines.append(f"- {c['name']}: {traits}")
        visual = format_visual_references([c])
        if visual:
            lines.append(visual)
    return "\n".join(lines)


@dataclass
class Entity:
    name: str
    entity_type: str  # "character", "location", "prop"
    traits: list[str] = field(default_factory=list)
    confidence: float = 0.0


def _parse_entities(raw: str) -> list[Entity]:
    """Parse LLM response into Entity list, handling JSON or text."""
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        items = json.loads(text)
        if isinstance(items, dict) and "entities" in items:
            items = items["entities"]
        if not isinstance(items, list):
            return []
        return [
            Entity(
                name=e.get("name", ""),
                entity_type=e.get("entity_type", e.get("type", "prop")),
                traits=e.get("traits", []),
                confidence=float(e.get("confidence", 0.5)),
            )
            for e in items
            if e.get("name")
        ]
    except (json.JSONDecodeError, ValueError, TypeError):
        return []


class LLMProvider(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> list[Entity]:
        """Extract entities from text."""
        ...

    @abstractmethod
    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        """Generate an enriched prompt from scene description."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        ...
