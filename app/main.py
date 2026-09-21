from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import anchor_faces, creative, projects, render, scenes, shots

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(scenes.router, prefix="/api/v1")
    app.include_router(shots.router, prefix="/api/v1")
    app.include_router(render.router, prefix="/api/v1")
    app.include_router(anchor_faces.router, prefix="/api/v1")
    app.include_router(creative.router, prefix="/api/v1")

    # Serve uploaded files
    upload_dir = BASE_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    # Serve workspace files
    workspace_dir = BASE_DIR / "workspace"
    workspace_dir.mkdir(exist_ok=True)
    app.mount("/workspace", StaticFiles(directory=str(workspace_dir)), name="workspace")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
