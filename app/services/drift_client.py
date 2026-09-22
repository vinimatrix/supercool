"""Drift MCP Client - Comunica SuperCool con Drift Editor via MCP (JSON-RPC over HTTP)."""

import json
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

import httpx


@dataclass
class DriftSession:
    port: int
    token: str
    url: str
    project_loaded: bool = False


class DriftMCPClient:
    def __init__(self):
        self.session: Optional[DriftSession] = None
        self.client = httpx.AsyncClient(timeout=60.0)
        self._request_id = 0
        self.simulated: bool = False

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def connect(self, port: int = 4731, token: str = None) -> bool:
        try:
            if token:
                self.session = DriftSession(
                    port=port, token=token,
                    url=f"http://127.0.0.1:{port}/mcp",
                )
            else:
                session_data = self._read_session_file()
                if session_data:
                    self.session = DriftSession(
                        port=session_data.get("port", port),
                        token=session_data.get("token", ""),
                        url=session_data.get("url", f"http://127.0.0.1:{port}/mcp"),
                    )

            if self.session:
                result = await self.inspect()
                if result is not None:
                    self.session.project_loaded = True
                    return True

            self._enter_simulated(port)
            return True
        except Exception as e:
            print(f"[DriftMCP] Connection failed ({e}), entering simulated mode")
            self._enter_simulated(port)
            return True

    def _enter_simulated(self, port: int):
        self.session = DriftSession(port=port, token="simulated", url="")
        self.simulated = True

    async def _rpc(self, method: str, params: dict = None) -> Optional[dict]:
        if self.simulated:
            return self._simulated_response(method, params or {})
        if not self.session:
            raise RuntimeError("Not connected to Drift")

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": method, "arguments": params or {}},
        }
        headers = {
            "Authorization": f"Bearer {self.session.token}",
            "Content-Type": "application/json",
        }

        try:
            response = await self.client.post(self.session.url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                content = result.get("content", [])
                if content and isinstance(content, list):
                    text = content[0].get("text", "")
                    try:
                        return json.loads(text)
                    except (json.JSONDecodeError, TypeError):
                        return {"text": text}
                return result
            print(f"[DriftMCP] HTTP {response.status_code}: {response.text[:200]}")
            return None
        except httpx.HTTPError as e:
            print(f"[DriftMCP] Request error: {e}")
            return None

    async def apply(self, ops: list[dict]) -> Optional[dict]:
        return await self._rpc("apply", {"ops": ops})

    async def inspect(self, clips: bool = True, detail: bool = True) -> Optional[dict]:
        return await self._rpc("inspect", {"clips": clips, "detail": detail})

    async def catalog(self) -> Optional[dict]:
        return await self._rpc("catalog", {})

    async def activity(self, start: float = 0, end: float = -1) -> Optional[dict]:
        params = {"start": start}
        if end > 0:
            params["end"] = end
        return await self._rpc("activity", params)

    async def frames(self, at: list[float] = None, n: int = 12) -> Optional[dict]:
        params = {"n": n}
        if at:
            params["at"] = at
        return await self._rpc("frames", params)

    async def capture(self, at: float = 0) -> Optional[dict]:
        return await self._rpc("capture", {"at": at})

    async def import_media(self, paths: list[str]) -> Optional[dict]:
        return await self.apply([{"name": "import_media", "args": {"paths": paths}}])

    async def list_assets(self) -> Optional[dict]:
        return await self._rpc("list_assets", {})

    async def add_track(self, track_type: str = "video") -> Optional[dict]:
        return await self.apply([{"name": "add_track", "args": {"type": track_type}}])

    async def place_clip(self, asset: str, at: float = 0, track: int = 0) -> Optional[dict]:
        return await self.apply([{"name": "place_clip", "args": {"asset": asset, "at": at, "track": track}}])

    async def move_clip(self, clip: str, to: float, track: int = None) -> Optional[dict]:
        args = {"clip": clip, "to": to}
        if track is not None:
            args["track"] = track
        return await self.apply([{"name": "move_clip", "args": args}])

    async def set_duration(self, clip: str, duration: float) -> Optional[dict]:
        return await self.apply([{"name": "set_duration", "args": {"clip": clip, "duration": duration}}])

    async def set_trim(self, clip: str, in_point: float = None, out_point: float = None) -> Optional[dict]:
        args = {"clip": clip}
        if in_point is not None:
            args["in"] = in_point
        if out_point is not None:
            args["out"] = out_point
        return await self.apply([{"name": "set_trim", "args": args}])

    async def split_clip(self, clip: str, at: float) -> Optional[dict]:
        return await self.apply([{"name": "split_clip", "args": {"clip": clip, "at": at}}])

    async def delete_clip(self, clip: str) -> Optional[dict]:
        return await self.apply([{"name": "delete_clip", "args": {"clip": clip}}])

    async def duplicate_clip(self, clip: str) -> Optional[dict]:
        return await self.apply([{"name": "duplicate_clip", "args": {"clip": clip}}])

    async def list_transitions(self) -> Optional[dict]:
        return await self._rpc("list_transitions", {})

    async def add_transition(self, from_clip: str, to_clip: str, kind: str = "crossfade", duration: float = 0.5) -> Optional[dict]:
        return await self.apply([{
            "name": "add_transition",
            "args": {"from": from_clip, "to": to_clip, "kind": kind, "duration": duration}
        }])

    async def remove_transition(self, transition: str) -> Optional[dict]:
        return await self.apply([{"name": "remove_transition", "args": {"transition": transition}}])

    async def list_effects(self) -> Optional[dict]:
        return await self._rpc("list_effects", {})

    async def add_effect(self, clip: str, effect_id: str) -> Optional[dict]:
        return await self.apply([{"name": "add_effect", "args": {"clip": clip, "effect": effect_id}}])

    async def remove_effect(self, clip: str, effect: int) -> Optional[dict]:
        return await self.apply([{"name": "remove_effect", "args": {"clip": clip, "effect": effect}}])

    async def set_effect_param(self, clip: str, effect_index: int, param: str, value) -> Optional[dict]:
        return await self.apply([{
            "name": "set_effect_param",
            "args": {"clip": clip, "effect": effect_index, "param": param, "value": value}
        }])

    async def list_audio_effects(self) -> Optional[dict]:
        return await self._rpc("list_audio_effects", {})

    async def add_audio_effect(self, clip: str, effect_id: str) -> Optional[dict]:
        return await self.apply([{"name": "add_audio_effect", "args": {"clip": clip, "effect": effect_id}}])

    async def set_transform(self, clip: str, x: float = 0, y: float = 0, w: float = 1920, h: float = 1080) -> Optional[dict]:
        return await self.apply([{
            "name": "set_transform",
            "args": {"clip": clip, "x": x, "y": y, "w": w, "h": h}
        }])

    async def set_volume(self, clip: str, volume: float) -> Optional[dict]:
        return await self.apply([{"name": "set_volume", "args": {"clip": clip, "volume": volume}}])

    async def set_fade(self, clip: str, fade_in: float = 0, fade_out: float = 0) -> Optional[dict]:
        args = {"clip": clip}
        if fade_in > 0:
            args["fadeIn"] = fade_in
        if fade_out > 0:
            args["fadeOut"] = fade_out
        return await self.apply([{"name": "set_fade", "args": args}])

    async def set_speed(self, clip: str, speed: float) -> Optional[dict]:
        return await self.apply([{"name": "set_clip_speed", "args": {"clip": clip, "speed": speed}}])

    async def set_blend_mode(self, clip: str, mode: str) -> Optional[dict]:
        return await self.apply([{"name": "set_blend_mode", "args": {"clip": clip, "mode": mode}}])

    async def add_text(self, text: str, preset: str = "title", at: float = 0, track: int = -1, duration: float = 5.0) -> Optional[dict]:
        return await self.apply([{
            "name": "add_text",
            "args": {"text": text, "preset": preset, "at": at, "track": track, "duration": duration}
        }])

    async def set_text_style(self, clip: str, style: dict) -> Optional[dict]:
        return await self.apply([{"name": "set_text", "args": {"clip": clip, "style": style}}])

    async def detect_beats(self, start: float = 0, duration: float = 30) -> Optional[dict]:
        return await self._rpc("detect_beats", {"start": start, "duration": duration})

    async def detect_scenes(self, clip: str) -> Optional[dict]:
        return await self._rpc("detect_scenes", {"clip": clip})

    async def set_project_setup(self, fps: int = 24, width: int = 3840, height: int = 2160) -> Optional[dict]:
        return await self.apply([{
            "name": "set_project_setup",
            "args": {"fps": fps, "width": width, "height": height}
        }])

    async def set_background(self, color: str = "#000000") -> Optional[dict]:
        return await self.apply([{"name": "set_background", "args": {"color": color}}])

    async def save_project(self, path: str = None) -> Optional[dict]:
        args = {}
        if path:
            args["path"] = path
        return await self._rpc("save_project", args)

    async def export_video(self, path: str, **kwargs) -> Optional[dict]:
        args = {"path": path}
        args.update(kwargs)
        return await self._rpc("export_video", args)

    async def export_status(self) -> Optional[dict]:
        return await self._rpc("export_status", {})

    async def undo(self) -> Optional[dict]:
        return await self.apply([{"name": "undo", "args": {}}])

    async def redo(self) -> Optional[dict]:
        return await self.apply([{"name": "redo", "args": {}}])

    async def list_history(self, limit: int = 20) -> Optional[dict]:
        return await self._rpc("list_history", {"limit": limit})

    async def seek(self, time: float) -> Optional[dict]:
        return await self.apply([{"name": "seek", "args": {"time": time}}])

    async def play(self) -> Optional[dict]:
        return await self.apply([{"name": "play", "args": {}}])

    async def pause(self) -> Optional[dict]:
        return await self.apply([{"name": "pause", "args": {}}])

    def _read_session_file(self) -> Optional[dict]:
        candidates = [
            Path.home() / "drift" / "mcp-session.json",
            Path.home() / "AppData" / "Local" / "Temp" / "drift" / "mcp-session.json",
            Path.home() / ".config" / "drift" / "mcp-session.json",
        ]
        for path in candidates:
            if path.exists():
                try:
                    with open(path) as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue
        return None

    async def close(self):
        await self.client.aclose()
        self.session = None
        self.simulated = False

    def _simulated_response(self, method: str, params: dict) -> dict:
        if method == "inspect":
            return {"ok": True, "tracks": [], "clips": 0, "dur": 0, "fps": 24, "w": 3840, "h": 2160, "name": "Untitled"}
        if method == "catalog":
            return {"ok": True, "toolboxes": []}
        if method == "list_assets":
            return {"ok": True, "assets": []}
        if method == "save_project":
            return {"ok": True, "saved": True}
        if method == "export_video":
            return {"ok": True, "exported": True, "path": params.get("path", "output.mp4")}
        if method == "export_status":
            return {"ok": True, "status": "ready"}
        return {"ok": True}
