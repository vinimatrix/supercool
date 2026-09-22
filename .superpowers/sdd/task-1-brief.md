# Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `Cargo.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Consumes: None (first task)
- Produces: `create_app()` factory, `Settings` class

## Step 1: Create pyproject.toml

```toml
[project]
name = "supercool"
version = "0.1.0"
description = "AI Cinematic Studio"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.35",
    "asyncpg>=0.29.0",
    "pydantic-settings>=2.5.0",
    "alembic>=1.13.0",
    "httpx>=0.27.0",
    "celery[redis]>=5.4.0",
    "pgvector>=0.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.6.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

## Step 2: Create Cargo.toml

```toml
[package]
name = "supercool-nle"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4"] }
tracing = "0.1"
tracing-subscriber = "0.3"
```

## Step 3: Create app/config.py

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "SUPERCOOL_"}

    database_url: str = "postgresql+asyncpg://supercool:supercool@localhost:5432/supercool"
    database_url_sync: str = "postgresql://supercool:supercool@localhost:5432/supercool"
    redis_url: str = "redis://localhost:6379/0"
    nle_url: str = "http://localhost:8080"
    google_api_key: str = ""
    openai_api_key: str = ""
    nvidia_api_key: str = ""
    llm_provider: str = "google"
    llm_fallback_enabled: bool = True


settings = Settings()
```

## Step 4: Create app/main.py

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="SuperCool - AI Cinematic Studio",
        version="0.1.0",
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
```

## Step 5: Create tests/conftest.py

```python
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

## Step 6: Write failing test

Create `tests/test_api/test_health.py`:

```python
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## Step 7: Run test to verify it passes

Run: `python -m pytest tests/test_api/test_health.py -v`
Expected: PASS

## Step 8: Commit

```bash
git add pyproject.toml Cargo.toml app/ tests/
git commit -m "feat: project scaffolding with FastAPI app factory"
```
