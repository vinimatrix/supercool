"""DaVinci Resolve MCP Client - Communicates via MCP stdio JSON-RPC protocol."""

import asyncio
import json
import os
from typing import Any

from app.config import settings


class DaVinciResolveClient:
    """MCP client for DaVinci Resolve using stdio JSON-RPC with 389 granular tools."""

    def __init__(self):
        self.process: asyncio.subprocess.Process | None = None
        self._connected = False
        self._request_id = 0
        self._lock = asyncio.Lock()

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def connect(self) -> bool:
        """Start MCP server process with --full flag for 389 granular tools."""
        try:
            python_exe = r"C:\Users\New User\AppData\Local\Programs\Python\Python312\python.exe"
            server_script = r"C:\Users\New User\AppData\Local\davinci-resolve-mcp\src\server.py"

            self.process = await asyncio.create_subprocess_exec(
                python_exe, server_script, "--full",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    **os.environ,
                    "RESOLVE_SCRIPT_API": r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting",
                    "RESOLVE_SCRIPT_LIB": r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll",
                    "PYTHONPATH": r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
                },
            )
            result = await self._send("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "supercool", "version": "1.0"},
            })
            if result and "result" in result:
                await self._send_notification("notifications/initialized")
                self._connected = True
                name = result["result"].get("serverInfo", {}).get("name", "unknown")
                print(f"[DaVinciMCP] Connected to {name}")
                return True
            return False
        except Exception as e:
            print(f"[DaVinciMCP] Connection failed: {e}")
            return False

    async def disconnect(self):
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
        self._connected = False
        self.process = None

    async def _send(self, method: str, params: dict[str, Any] | None = None) -> dict | None:
        if not self.process or not self.process.stdin:
            return None
        request = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}
        if params is not None:
            request["params"] = params
        async with self._lock:
            try:
                self.process.stdin.write((json.dumps(request) + "\n").encode())
                await self.process.stdin.drain()
                raw = await asyncio.wait_for(self.process.stdout.read(131072), timeout=30.0)
                if raw:
                    text = raw.decode().strip()
                    for part in text.split("\n"):
                        part = part.strip()
                        if part.startswith("{"):
                            try:
                                return json.loads(part)
                            except json.JSONDecodeError:
                                continue
                return None
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                print(f"[DaVinciMCP] Error: {e}")
                return None

    async def _send_notification(self, method: str, params: dict[str, Any] | None = None):
        if not self.process or not self.process.stdin:
            return
        notification = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            notification["params"] = params
        try:
            self.process.stdin.write((json.dumps(notification) + "\n").encode())
            await self.process.stdin.drain()
        except Exception:
            pass

    async def read_resource(self, uri: str) -> Any:
        """Read an MCP resource."""
        result = await self._send("resources/read", {"uri": uri})
        if result and "result" in result:
            contents = result["result"].get("contents", [])
            if contents:
                text = contents[0].get("text", "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return result

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict:
        """Call an MCP tool by its exact granular name."""
        result = await self._send("tools/call", {"name": tool_name, "arguments": arguments or {}})
        if result and "result" in result:
            content = result["result"].get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"text": text}
        return result or {"error": "No response"}

    # ─── Resources (read-only, fast) ───

    async def list_projects(self) -> Any:
        return await self.read_resource("resolve://projects")

    async def get_current_project(self) -> Any:
        return await self.read_resource("resolve://current-project")

    async def list_timelines(self) -> Any:
        return await self.read_resource("resolve://timelines")

    async def get_current_timeline(self) -> Any:
        return await self.read_resource("resolve://current-timeline")

    async def get_resolve_version(self) -> Any:
        return await self.read_resource("resolve://version")

    async def get_project_settings(self) -> Any:
        return await self.read_resource("resolve://project-settings")

    async def get_project_info(self) -> Any:
        return await self.read_resource("resolve://project/info")

    async def get_app_state(self) -> Any:
        return await self.read_resource("resolve://app/state")

    # ─── Project tools ───

    async def open_project(self, name: str) -> dict:
        return await self.call_tool("open_project", {"project_name": name})

    async def create_project(self, name: str) -> dict:
        return await self.call_tool("create_project", {"project_name": name})

    async def save_project(self, path: str | None = None) -> dict:
        args = {}
        if path:
            args["path"] = path
        return await self.call_tool("save_project", args)

    async def close_project(self) -> dict:
        return await self.call_tool("close_project", {})

    async def set_project_setting(self, name: str, value: Any) -> dict:
        return await self.call_tool("set_project_setting", {"setting_name": name, "setting_value": value})

    async def get_project_preset_list(self) -> dict:
        return await self.call_tool("get_project_preset_list", {})

    async def set_project_preset(self, preset: str) -> dict:
        return await self.call_tool("set_project_preset", {"preset_name": preset})

    async def set_project_name(self, name: str) -> dict:
        return await self.call_tool("set_project_name", {"project_name": name})

    async def get_project_unique_id(self) -> dict:
        return await self.call_tool("get_project_unique_id", {})

    # ─── Project folders ───

    async def get_project_folder_list(self) -> dict:
        return await self.call_tool("get_project_folder_list", {})

    async def get_current_project_folder(self) -> dict:
        return await self.call_tool("get_current_project_folder", {})

    async def create_project_folder(self, folder_name: str) -> dict:
        return await self.call_tool("create_project_folder", {"folder_name": folder_name})

    async def open_project_folder(self, folder_name: str) -> dict:
        return await self.call_tool("open_project_folder", {"folder_name": folder_name})

    # ─── Timeline tools ───

    async def create_timeline(self, name: str) -> dict:
        return await self.call_tool("create_timeline", {"timeline_name": name})

    async def set_current_timeline(self, name: str) -> dict:
        return await self.call_tool("set_current_timeline", {"timeline_name": name})

    async def list_timelines_tool(self) -> dict:
        return await self.call_tool("list_timelines_tool", {})

    async def timeline_set_name(self, old_name: str, new_name: str) -> dict:
        return await self.call_tool("timeline_set_name", {"old_name": old_name, "new_name": new_name})

    async def timeline_get_current_timecode(self) -> dict:
        return await self.call_tool("timeline_get_current_timecode", {})

    async def timeline_set_start_timecode(self, timecode: str) -> dict:
        return await self.call_tool("timeline_set_start_timecode", {"timecode": timecode})

    async def timeline_add_track(self, track_type: str) -> dict:
        return await self.call_tool("timeline_add_track", {"track_type": track_type})

    async def timeline_duplicate(self, name: str) -> dict:
        return await self.call_tool("timeline_duplicate", {"new_timeline_name": name})

    async def create_timeline_from_clips(self, name: str, clips: list[str]) -> dict:
        return await self.call_tool("create_timeline_from_clips", {"timeline_name": name, "clip_names": clips})

    # ─── Timeline items ───

    async def get_selected_timeline_items(self) -> dict:
        return await self.call_tool("get_selected_timeline_items", {})

    async def ti_get_info(self, item_index: int, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("ti_get_info", {"item_index": item_index, "track_type": track_type, "track_index": track_index})

    async def ti_set_name(self, item_index: int, name: str, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("ti_set_name", {"item_index": item_index, "name": name, "track_type": track_type, "track_index": track_index})

    async def ti_set_property(self, item_index: int, property_key: str, property_value: str, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("ti_set_property", {"item_index": item_index, "property_key": property_key, "property_value": property_value, "track_type": track_type, "track_index": track_index})

    async def ti_get_property(self, item_index: int, property_key: str, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("ti_get_property", {"item_index": item_index, "property_key": property_key, "track_type": track_type, "track_index": track_index})

    async def ti_add_marker(self, item_index: int, frame_id: int, color: str, name: str, note: str = "", track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("ti_add_marker", {"item_index": item_index, "frame_id": frame_id, "color": color, "name": name, "note": note, "track_type": track_type, "track_index": track_index})

    async def ti_get_markers(self, item_index: int, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("ti_get_markers", {"item_index": item_index, "track_type": track_type, "track_index": track_index})

    async def ti_set_clip_color(self, item_index: int, color: str, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("ti_set_clip_color", {"item_index": item_index, "color": color, "track_type": track_type, "track_index": track_index})

    # ─── Media Pool ───

    async def import_media(self, paths: list[str]) -> dict:
        return await self.call_tool("import_media", {"file_paths": paths})

    async def append_to_timeline(self, clip_names: list[str]) -> dict:
        return await self.call_tool("append_to_timeline", {"clip_names": clip_names})

    async def get_selected_clips(self) -> dict:
        return await self.call_tool("get_selected_clips", {})

    async def set_current_media_pool_folder(self, folder_path: str) -> dict:
        return await self.call_tool("set_current_media_pool_folder", {"folder_path": folder_path})

    async def get_clip_unique_id_by_name(self, clip_name: str) -> dict:
        return await self.call_tool("get_clip_unique_id_by_name", {"clip_name": clip_name})

    async def export_media_pool_metadata(self, file_path: str) -> dict:
        return await self.call_tool("export_media_pool_metadata", {"file_path": file_path})

    # ─── Render ───

    async def get_render_formats(self) -> dict:
        return await self.call_tool("get_render_formats", {})

    async def get_render_codecs(self, fmt: str) -> dict:
        return await self.call_tool("get_render_codecs", {"format": fmt})

    async def get_current_render_format_and_codec(self) -> dict:
        return await self.call_tool("get_current_render_format_and_codec", {})

    async def set_render_settings(self, settings_dict: dict) -> dict:
        return await self.call_tool("set_render_settings", settings_dict)

    async def add_render_job(self) -> dict:
        return await self.call_tool("add_render_job", {})

    async def start_rendering_jobs(self) -> dict:
        return await self.call_tool("start_rendering_jobs", {})

    async def is_rendering_in_progress(self) -> dict:
        return await self.call_tool("is_rendering_in_progress", {})

    async def get_render_job_list(self) -> dict:
        return await self.call_tool("get_render_job_list", {})

    async def get_render_job_status(self, render_job_id: str) -> dict:
        return await self.call_tool("get_render_job_status", {"render_job_id": render_job_id})

    async def render_with_quick_export(self, preset: str) -> dict:
        return await self.call_tool("render_with_quick_export", {"preset_name": preset})

    # ─── Color / Graph ───

    async def graph_get_num_nodes(self, item_index: int = 0, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("graph_get_num_nodes", {"item_index": item_index, "track_type": track_type, "track_index": track_index})

    async def graph_get_lut(self, node_index: int, item_index: int = 0, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("graph_get_lut", {"node_index": node_index, "item_index": item_index, "track_type": track_type, "track_index": track_index})

    async def graph_set_lut(self, node_index: int, lut_path: str, item_index: int = 0, track_type: str = "video", track_index: int = 1) -> dict:
        return await self.call_tool("graph_set_lut", {"node_index": node_index, "lut_path": lut_path, "item_index": item_index, "track_type": track_type, "track_index": track_index})

    async def get_color_groups_list(self) -> dict:
        return await self.call_tool("get_color_groups_list", {})

    async def add_color_group(self, group_name: str) -> dict:
        return await self.call_tool("add_color_group", {"group_name": group_name})

    # ─── Audio ───

    async def normalize_timeline_audio_level(self, audio_type: str = "Dialogue", normalize_level: float = -14.0) -> dict:
        return await self.call_tool("normalize_timeline_audio_level", {"audio_type": audio_type, "normalize_level": normalize_level})

    async def auto_sync_audio(self, track_type: str = "timeline") -> dict:
        return await self.call_tool("auto_sync_audio", {"sync_type": track_type})

    async def auto_align_timeline_clips(self, align_type: str = "waveform") -> dict:
        return await self.call_tool("auto_align_timeline_clips", {"alignment_type": align_type})

    # ─── Status / Info ───

    async def health_check(self) -> dict:
        return await self.call_tool("runtime_mode", {})

    async def get_version(self) -> dict:
        return await self.call_tool("get_version", {})

    async def is_resolve_studio(self) -> dict:
        return await self.call_tool("is_resolve_studio", {})

    # ─── Cloud ───

    async def get_current_database(self) -> dict:
        return await self.call_tool("get_current_database", {})

    async def get_database_list(self) -> dict:
        return await self.call_tool("get_database_list", {})

    # ─── App control ───

    async def switch_page(self, page_name: str) -> dict:
        return await self.call_tool("switch_page", {"page_name": page_name})

    async def quit_app(self) -> dict:
        return await self.call_tool("quit_app", {})


_davinci_client: DaVinciResolveClient | None = None


def get_davinci_client() -> DaVinciResolveClient:
    global _davinci_client
    if _davinci_client is None:
        _davinci_client = DaVinciResolveClient()
    return _davinci_client
