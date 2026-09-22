"""DaVinci Resolve HTTP MCP Client - Communicates via HTTP JSON-RPC to MCP server."""

from dataclasses import dataclass, field
from typing import Any

import httpx

MCP_URL = "http://127.0.0.1:4731/mcp"
MCP_TOKEN = "b83ab8f1d7870add64da439b5d563841662b65bb4198f1ce5fbb5d98d58eacac"


@dataclass
class TimelineInfo:
    name: str
    fps: int
    start_timecode: str
    duration_frames: int
    tracks: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ClipInfo:
    clip_id: str
    shot_id: str
    media_path: str
    duration_frames: int
    qa_status: str


class DaVinciMCPClient:
    def __init__(self, mcp_url: str = MCP_URL, token: str = MCP_TOKEN):
        self.mcp_url = mcp_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call MCP tool via JSON-RPC over HTTP."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.mcp_url,
                json=payload,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()
            if "result" in result:
                return result["result"]
            raise Exception(f"MCP error: {result.get('error', 'Unknown error')}")

    async def get_active_timeline(self) -> TimelineInfo:
        """Get active timeline structure from DaVinci."""
        result = await self._call_tool("davinci_get_active_timeline", {})
        return TimelineInfo(**result)

    async def create_tracks(
        self,
        video_track_names: list[str],
        audio_track_names: list[str],
    ) -> bool:
        """Create track structure in DaVinci."""
        result = await self._call_tool("davinci_create_tracks", {
            "video_track_names": video_track_names,
            "audio_track_names": audio_track_names,
        })
        return result.get("success", False)

    async def append_clip(
        self,
        media_path: str,
        track_type: str,
        track_index: int,
        start_timecode: str,
        clip_name: str,
    ) -> bool:
        """Append clip to timeline."""
        result = await self._call_tool("davinci_append_clip", {
            "media_path": media_path,
            "track_type": track_type,
            "track_index": track_index,
            "start_timecode": start_timecode,
            "clip_name": clip_name,
        })
        return result.get("success", False)

    async def get_timeline_clips(
        self,
        track_type: str = "video",
        track_index: int = 1,
    ) -> list[ClipInfo]:
        """Get clips from timeline."""
        result = await self._call_tool("davinci_get_timeline_clips", {
            "track_type": track_type,
            "track_index": track_index,
        })
        return [ClipInfo(**clip) for clip in result.get("clips", [])]

    async def sync_ducking_keyframes(
        self,
        target_track_index: int,
        ducking_envelope: list[dict[str, Any]],
    ) -> bool:
        """Sync audio ducking keyframes to Fairlight."""
        result = await self._call_tool("davinci_sync_ducking_keyframes", {
            "target_track_index": target_track_index,
            "ducking_envelope": ducking_envelope,
        })
        return result.get("success", False)

    async def add_qa_marker(
        self,
        timecode: str,
        color: str,
        note: str,
    ) -> bool:
        """Add QA marker to timeline."""
        result = await self._call_tool("davinci_add_qa_marker", {
            "timecode": timecode,
            "color": color,
            "note": note,
        })
        return result.get("success", False)

    async def export_master(
        self,
        preset_name: str,
        output_folder: str,
    ) -> bool:
        """Export final master from DaVinci."""
        result = await self._call_tool("davinci_export_master", {
            "preset_name": preset_name,
            "output_folder": output_folder,
        })
        return result.get("success", False)


_davinci_http_client: DaVinciMCPClient | None = None


def get_davinci_http_client() -> DaVinciMCPClient:
    global _davinci_http_client
    if _davinci_http_client is None:
        _davinci_http_client = DaVinciMCPClient()
    return _davinci_http_client
