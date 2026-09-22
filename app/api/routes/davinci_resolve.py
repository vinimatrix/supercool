"""DaVinci Resolve API endpoints - control Resolve via MCP granular tools."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/api/v1/davinci", tags=["DaVinci Resolve"])


class DaVinciResponse(BaseModel):
    status: str
    data: dict[str, Any] | list | None = None
    error: str | None = None


# ─── Connection ───

@router.post("/connect")
async def connect_davinci():
    from app.services.davinci_resolve import get_davinci_client
    connected = await get_davinci_client().connect()
    if connected:
        return {"status": "connected", "message": "Connected to DaVinci Resolve MCP"}
    raise HTTPException(status_code=503, detail="Could not connect to DaVinci Resolve")


@router.post("/disconnect")
async def disconnect_davinci():
    from app.services.davinci_resolve import get_davinci_client
    await get_davinci_client().disconnect()
    return {"status": "disconnected"}


@router.get("/health")
async def health_check():
    from app.services.davinci_resolve import get_davinci_client
    result = await get_davinci_client().get_app_state()
    return {"status": "connected", "state": result}


@router.get("/version")
async def get_version():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_resolve_version()


# ─── Projects ───

@router.get("/projects")
async def list_projects():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().list_projects()


@router.post("/projects")
async def create_project(name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().create_project(name)


@router.post("/projects/open")
async def open_project(name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().open_project(name)


@router.post("/projects/save")
async def save_project(path: str | None = None):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().save_project(path)


@router.post("/projects/close")
async def close_project():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().close_project()


@router.post("/projects/settings")
async def set_project_setting(name: str, value: Any):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().set_project_setting(name, value)


@router.get("/projects/settings")
async def get_project_settings():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_project_settings()


@router.get("/projects/unique-id")
async def get_project_unique_id():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_project_unique_id()


@router.get("/projects/info")
async def get_project_info():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_project_info()


@router.get("/projects/folders")
async def get_project_folders():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_project_folder_list()


@router.post("/projects/folders")
async def create_project_folder(folder_name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().create_project_folder(folder_name)


@router.post("/projects/folders/open")
async def open_project_folder(folder_name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().open_project_folder(folder_name)


@router.get("/database")
async def get_current_database():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_current_database()


@router.get("/database/list")
async def get_database_list():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_database_list()


# ─── Timelines ───

@router.get("/timelines")
async def list_timelines():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().list_timelines()


@router.get("/timelines/all")
async def list_timelines_tool():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().list_timelines_tool()


@router.post("/timelines")
async def create_timeline(name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().create_timeline(name)


@router.post("/timelines/set-current")
async def set_current_timeline(name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().set_current_timeline(name)


@router.post("/timelines/duplicate")
async def duplicate_timeline(name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().timeline_duplicate(name)


@router.post("/timelines/from-clips")
async def create_timeline_from_clips(name: str, clips: list[str]):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().create_timeline_from_clips(name, clips)


@router.get("/timelines/timecode")
async def get_timeline_timecode():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().timeline_get_current_timecode()


@router.post("/timelines/timecode")
async def set_timeline_timecode(timecode: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().timeline_set_start_timecode(timecode)


@router.post("/timelines/add-track")
async def add_timeline_track(track_type: str = "video"):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().timeline_add_track(track_type)


# ─── Timeline Items ───

@router.get("/timeline-items/selected")
async def get_selected_items():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_selected_timeline_items()


@router.get("/timeline-items/{item_index}")
async def get_item_info(item_index: int, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().ti_get_info(item_index, track_type, track_index)


@router.post("/timeline-items/{item_index}/name")
async def set_item_name(item_index: int, name: str, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().ti_set_name(item_index, name, track_type, track_index)


@router.post("/timeline-items/{item_index}/color")
async def set_item_color(item_index: int, color: str, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().ti_set_clip_color(item_index, color, track_type, track_index)


@router.post("/timeline-items/{item_index}/property")
async def set_item_property(item_index: int, property_key: str, property_value: str, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().ti_set_property(item_index, property_key, property_value, track_type, track_index)


@router.get("/timeline-items/{item_index}/markers")
async def get_item_markers(item_index: int, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().ti_get_markers(item_index, track_type, track_index)


@router.post("/timeline-items/{item_index}/markers")
async def add_item_marker(item_index: int, frame_id: int, color: str, name: str, note: str = "", track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().ti_add_marker(item_index, frame_id, color, name, note, track_type, track_index)


# ─── Media Pool ───

@router.post("/media-pool/import")
async def import_media(paths: list[str]):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().import_media(paths)


@router.post("/media-pool/append")
async def append_to_timeline(clip_names: list[str]):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().append_to_timeline(clip_names)


@router.get("/media-pool/selected")
async def get_selected_clips():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_selected_clips()


@router.get("/media-pool/clip-id")
async def get_clip_id(clip_name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_clip_unique_id_by_name(clip_name)


@router.post("/media-pool/export-metadata")
async def export_metadata(file_path: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().export_media_pool_metadata(file_path)


# ─── Render ───

@router.get("/render/formats")
async def get_render_formats():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_render_formats()


@router.get("/render/codecs")
async def get_render_codecs(fmt: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_render_codecs(fmt)


@router.get("/render/current")
async def get_current_render_format():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_current_render_format_and_codec()


@router.post("/render/settings")
async def set_render_settings(**kwargs: Any):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().set_render_settings(kwargs)


@router.post("/render/start")
async def start_render():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().start_rendering_jobs()


@router.get("/render/status")
async def render_status():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().is_rendering_in_progress()


@router.get("/render/jobs")
async def get_render_jobs():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_render_job_list()


@router.get("/render/jobs/{job_id}")
async def get_render_job_status(job_id: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_render_job_status(job_id)


@router.post("/render/quick-export")
async def quick_export(preset: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().render_with_quick_export(preset)


# ─── Color ───

@router.get("/color/nodes")
async def get_node_count(item_index: int = 0, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().graph_get_num_nodes(item_index, track_type, track_index)


@router.get("/color/lut/{node_index}")
async def get_lut(node_index: int, item_index: int = 0, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().graph_get_lut(node_index, item_index, track_type, track_index)


@router.post("/color/lut/{node_index}")
async def set_lut(node_index: int, lut_path: str, item_index: int = 0, track_type: str = "video", track_index: int = 1):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().graph_set_lut(node_index, lut_path, item_index, track_type, track_index)


@router.get("/color/groups")
async def get_color_groups():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().get_color_groups_list()


@router.post("/color/groups")
async def add_color_group(group_name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().add_color_group(group_name)


# ─── Audio ───

@router.post("/audio/normalize")
async def normalize_audio(audio_type: str = "Dialogue", level: float = -14.0):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().normalize_timeline_audio_level(audio_type, level)


@router.post("/audio/auto-sync")
async def auto_sync_audio(track_type: str = "timeline"):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().auto_sync_audio(track_type)


@router.post("/audio/align")
async def auto_align_audio(align_type: str = "waveform"):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().auto_align_timeline_clips(align_type)


# ─── App Control ───

@router.post("/app/switch-page")
async def switch_page(page_name: str):
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().switch_page(page_name)


@router.post("/app/quit")
async def quit_app():
    from app.services.davinci_resolve import get_davinci_client
    return await get_davinci_client().quit_app()
