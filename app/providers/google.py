import base64
from pathlib import Path as _Path

import httpx

from app.config import settings
from app.providers.base import Entity, LLMProvider, _parse_entities, format_character_block


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
            data = response.json()
            raw = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return _parse_entities(raw)

    async def generate_prompt(self, scene_description: str, characters: list[dict]) -> str:
        char_info = format_character_block(characters)
        prompt = f"""Generate a detailed cinematic prompt for this scene:
        {scene_description}

        Characters:
        {char_info}

        Include visual details, lighting, camera angle, mood."""

        parts = [{"text": prompt}]
        for c in characters:
            sheet = resolve_sheet_path(c.get("reference_sheet_url"))
            if sheet:
                parts.append({
                    "inline_data": {
                        "mime_type": mime_for_sheet(sheet),
                        "data": base64.b64encode(sheet.read_bytes()).decode(),
                    }
                })
                break

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={"contents": [{"parts": parts}]},
                timeout=30.0,
            )
            data = response.json()
            return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

    async def health_check(self) -> bool:
        return bool(self.api_key)


MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def mime_for_sheet(path: _Path) -> str:
    """Derive the Gemini mime type from the stored file's suffix."""
    return MIME_BY_SUFFIX.get(path.suffix.lower(), "image/png")


def resolve_sheet_path(url: str | None) -> _Path | None:
    if not url:
        return None
    p = _Path(url.lstrip("/"))
    return p if p.exists() else None
