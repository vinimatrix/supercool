"""Groq LLM Provider - Fast inference via Groq API."""

from groq import AsyncGroq

from app.config import settings
from app.providers.base import Entity, LLMProvider, _parse_entities, format_character_block


class GroqProvider(LLMProvider):
    """Groq API provider for fast LLM inference."""

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = "openai/gpt-oss-20b"
        self.client = AsyncGroq(api_key=self.api_key) if self.api_key else None

    async def extract_entities(self, text: str) -> list[Entity]:
        if not self.client:
            return []

        prompt = f"""Extract all named entities from this text. Return JSON array with:
        name, entity_type (character/location/prop), traits (list of strings), confidence (0-1).

        Text: {text}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content
        return _parse_entities(raw)

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        if not self.client:
            return ""

        char_info = format_character_block(characters)
        prompt = f"""Generate a detailed cinematic prompt for this scene:
        {scene_description}

        Characters:
        {char_info}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    async def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            response = await self.client.models.list()
            return len(response.data) > 0
        except Exception:
            return False
