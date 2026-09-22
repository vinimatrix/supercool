from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    analytics,
    anchor_faces,
    characters,
    creative,
    davinci_resolve,
    drift,
    mcp,
    nle,
    pipeline,
    production,
    projects,
    qa,
    render,
    scenes,
    screenplay,
    shots,
    story_bible,
    voice,
    websocket,
    youtube,
)
from app.db.database import Base, engine

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(scenes.router, prefix="/api/v1")
    app.include_router(shots.router, prefix="/api/v1")
    app.include_router(render.router, prefix="/api/v1")
    app.include_router(anchor_faces.router, prefix="/api/v1")
    app.include_router(characters.router, prefix="/api/v1")
    app.include_router(creative.router, prefix="/api/v1")
    app.include_router(drift.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(youtube.router, prefix="/api/v1")
    app.include_router(screenplay.router, prefix="/api/v1")
    app.include_router(story_bible.router, prefix="/api/v1")
    app.include_router(qa.router, prefix="/api/v1")
    app.include_router(nle.router, prefix="/api/v1")
    app.include_router(voice.router, prefix="/api/v1")
    app.include_router(mcp.router, prefix="/api/v1")
    app.include_router(production.router, prefix="/api/v1")
    app.include_router(pipeline.router, prefix="/api/v1")
    app.include_router(davinci_resolve.router)
    app.include_router(websocket.router)

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


app = create_app()
