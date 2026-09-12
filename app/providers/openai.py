import httpx

from app.providers.base import LLMProvider, Entity
from app.config import settings


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"

    async def extract_entities(self, text: str) -> list[Entity]:
        prompt = f"""Extract all named entities from this text. Return JSON array with:
        name, entity_type (character/location/prop), traits (list of strings), confidence (0-1).

        Text: {text}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
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
        {char_info}"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )
            return response.json()["choices"][0]["message"]["content"]

    async def health_check(self) -> bool:
        return bool(self.api_key)
