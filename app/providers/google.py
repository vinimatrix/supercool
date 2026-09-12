import httpx

from app.providers.base import LLMProvider, Entity
from app.config import settings


class GoogleProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.google_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract all named entities from this text. Return JSON array with:
        name, entity_type (character/location/prop), traits (list of strings), confidence (0-1).

        Text: {text}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30.0,
            )
            return []

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        char_info = "\n".join(
            f"- {c['name']}: {', '.join(c.get('locked_traits', []))}" for c in characters
        )
        prompt = f"""Generate a detailed cinematic prompt for this scene:
        {scene_description}

        Characters:
        {char_info}

        Include visual details, lighting, camera angle, mood."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30.0,
            )
            data = response.json()
            return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

    async def health_check(self) -> bool:
        return bool(self.api_key)
