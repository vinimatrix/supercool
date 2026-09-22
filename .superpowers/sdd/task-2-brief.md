# Task 2: Database Layer

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/database.py`
- Modify: `app/config.py` (add database settings)

**Interfaces:**
- Consumes: `settings` from config
- Produces: `engine`, `async_session`, `Base` declarative base

## Step 1: Write failing test

Create `tests/test_db/test_database.py`:

```python
import pytest
from sqlalchemy import text
from app.db.database import engine


async def test_engine_creation():
    assert engine is not None


async def test_database_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

## Step 2: Run test to verify it fails

Run: `python -m pytest tests/test_db/test_database.py -v`
Expected: FAIL with ImportError

## Step 3: Create app/db/database.py

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
```

## Step 4: Run test to verify it passes

Run: `python -m pytest tests/test_db/test_database.py -v`
Expected: PASS (requires running PostgreSQL)

## Step 5: Commit

```bash
git add app/db/ tests/test_db/
git commit -m "feat: async SQLAlchemy database layer"
```
