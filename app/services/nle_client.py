"""HTTP client for communicating with the Rust NLE server."""

import httpx

from app.config import settings


class NLEClient:
    """Client for the Rust NLE service."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.nle_url

    async def health_check(self) -> bool:
        """Check if the NLE server is reachable."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/health")
                resp.raise_for_status()
                return True
        except httpx.HTTPError:
            return False

    async def concat(self, clips: list[str], output_path: str) -> dict:
        """Concatenate video clips into a single output file."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/concat",
                json={"clips": clips, "output": output_path},
            )
            resp.raise_for_status()
            return resp.json()

    async def transcode(
        self, input_path: str, output_path: str, fps: int = 24
    ) -> dict:
        """Transcode a video file with optional frame rate conversion."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/transcode",
                json={"input": input_path, "output": output_path, "fps": fps},
            )
            resp.raise_for_status()
            return resp.json()

    async def mix_audio(self, tracks: list[str], output_path: str) -> dict:
        """Mix multiple audio tracks into a single output file."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/mix_audio",
                json={"tracks": tracks, "output": output_path},
            )
            resp.raise_for_status()
            return resp.json()

    async def pipeline(self, config: dict) -> dict:
        """Execute a full render pipeline with the given config."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/pipeline",
                json=config,
            )
            resp.raise_for_status()
            return resp.json()
