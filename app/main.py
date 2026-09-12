from fastapi import FastAPI

from app.api.routes import projects


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    app.include_router(projects.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
