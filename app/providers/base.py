from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Entity:
    name: str
    entity_type: str  # "character", "location", "prop"
    traits: list[str] = field(default_factory=list)
    confidence: float = 0.0


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
