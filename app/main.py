from fastapi import FastAPI

from app.api.routes import projects, scenes, shots


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(scenes.router, prefix="/api/v1")
    app.include_router(shots.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
