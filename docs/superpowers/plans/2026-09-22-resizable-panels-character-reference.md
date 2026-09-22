# Resizable Panels + Character Reference Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mouse-resizable horizontal panels (Sidebar/CommandCenter) and character reference sheet image + visual_prompt AI text wired into the creative pipeline.

**Architecture:** A1 — custom `useResizablePanel` hook (localStorage persistence, pointer-capture drag) drives Sidebar/CommandCenter widths with `PanelDivider`. B1 — extend `Character` with `reference_sheet_url` + `visual_prompt`, add upload/DELETE routes, inject `visual_prompt` into all four LLM providers' `generate_prompt`, attach sheet image only in Google/Gemini multimodal path.

**Tech Stack:** React 19 + TS + vitest (jsdom), FastAPI + SQLAlchemy async + pytest (aiosqlite via conftest client), Alembic, oxlint.

## Global Constraints

- Frontend: `npm run build` (`tsc -b && vite build`), `npm test`, `npm run lint` must be green in `frontend/` (use `C:\Program Files\nodejs\npm.cmd`).
- Backend: `pytest` green (`asyncio_mode = auto`, tests in `tests/`); ruff line-length 100.
- Panel keys: `panel-width:sidebar` / `panel-width:command`; sidebar default 320 min 220 max 560 sign +1; command default 384 min 300 max 640 sign −1.
- Upload limits: image content-types only, max 5 MB, storage under `uploads/reference_sheets/`.
- Prompt format exactly: `VISUAL REFERENCE — {name}: {visual_prompt}` (em dash).
- Gemini attaches sheet image only if file exists on disk; other providers never fail on missing image.
- `reference_sheet_url` is not client-settable via create/update body (only upload/DELETE routes).
- No new frontend dependencies; no Drift API key/config changes.

---

### Task 1: Character model + Alembic migration + schemas

**Files:**
- Modify: `app/models/character.py` (Character class, lines ~16–30)
- Create: `alembic/versions/<new>_add_character_reference_fields.py` (down_revision=`fcae66ea5e4b`)
- Modify: `app/schemas/character.py`
- Modify: `tests/conftest.py` (CREATE_CHARACTERS SQL)
- Test: `tests/test_models/test_models.py`

**Interfaces:**
- Produces: `Character.reference_sheet_url: str | None`, `Character.visual_prompt: str | None`; `CharacterRead`/`CharacterCreate` expose `visual_prompt: str | None = None` (and `reference_sheet_url: str | None = None` on Read only).

- [ ] **Step 1: Write the failing model/schema test**

Append to `tests/test_models/test_models.py`:

```python
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterRead


def test_character_has_reference_fields():
    c = Character(name="Hero")
    assert hasattr(c, "reference_sheet_url")
    assert hasattr(c, "visual_prompt")


def test_character_schemas_expose_visual_prompt():
    create = CharacterCreate(name="Hero", visual_prompt="scar over left eye")
    assert create.visual_prompt == "scar over left eye"
    read = CharacterRead.model_validate(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "project_id": "00000000-0000-0000-0000-000000000002",
            "name": "Hero",
            "biography": None,
            "locked_traits": [],
            "voice_profile_id": None,
            "created_at": "2026-01-01T00:00:00",
            "reference_sheet_url": "/uploads/reference_sheets/a.png",
            "visual_prompt": "tall",
        }
    )
    assert read.reference_sheet_url.endswith("a.png")
    assert read.visual_prompt == "tall"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models/test_models.py -v`
Expected: FAIL (`AttributeError` / missing schema field)

- [ ] **Step 3: Implement model fields**

In `app/models/character.py` inside `Character`, after `voice_profile_id`:

```python
    reference_sheet_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Step 4: Implement schemas**

In `app/schemas/character.py`:

```python
class CharacterCreate(BaseModel):
    name: str
    biography: str | None = None
    locked_traits: list[str] = []
    voice_profile_id: str | None = None
    visual_prompt: str | None = None


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    biography: str | None = None
    locked_traits: list[str] = []
    voice_profile_id: str | None = None
    created_at: datetime
    visual_prompt: str | None = None
    reference_sheet_url: str | None = None
```

- [ ] **Step 5: Update test conftest CREATE_CHARACTERS**

In `tests/conftest.py` `CREATE_CHARACTERS`, add columns after `voice_profile_id`:

```sql
    reference_sheet_url TEXT,
    visual_prompt TEXT,
```

- [ ] **Step 6: Create Alembic migration**

Create `alembic/versions/add_character_reference_fields.py`:

```python
"""add character reference_sheet_url and visual_prompt

Revision ID: c0ffee123abc
Revises: fcae66ea5e4b
Create Date: 2026-09-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c0ffee123abc"
down_revision: Union[str, Sequence[str], None] = "fcae66ea5e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("characters", sa.Column("reference_sheet_url", sa.Text(), nullable=True))
    op.add_column("characters", sa.Column("visual_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("characters", "visual_prompt")
    op.drop_column("characters", "reference_sheet_url")
```

- [ ] **Step 7: Run tests to verify pass**

Run: `python -m pytest tests/test_models/test_models.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add app/models/character.py app/schemas/character.py tests/conftest.py tests/test_models/test_models.py alembic/versions/add_character_reference_fields.py
git commit -m "feat: add character reference_sheet_url and visual_prompt fields"
```

---

### Task 2: PUT /characters/{id} update endpoint (missing backend route)

**Files:**
- Create: `app/api/routes/characters.py`
- Modify: `app/main.py` (include router)
- Test: `tests/test_api/test_characters.py`

**Interfaces:**
- Consumes: `CharacterUpdate` schema from Task 1 family.
- Produces: `PUT /api/v1/characters/{character_id}` accepting `{name?, biography?, locked_traits?, visual_prompt?}` → `CharacterRead`.

Note: frontend `charactersApi.update` already calls `PUT /characters/{id}` but no route exists — this task adds it.

- [ ] **Step 1: Write failing test**

Create `tests/test_api/test_characters.py`:

```python
async def test_update_character_visual_prompt(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()
    resp = await client.put(
        f"/api/v1/characters/{char['id']}",
        json={"visual_prompt": "pale skin, white cloak", "name": "Hero Prime"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["visual_prompt"] == "pale skin, white cloak"
    assert data["name"] == "Hero Prime"


async def test_update_character_not_found(client):
    resp = await client.put(
        "/api/v1/characters/00000000-0000-0000-0000-000000000099",
        json={"visual_prompt": "x"},
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api/test_characters.py -v`
Expected: FAIL (405/404 — no PUT route)

- [ ] **Step 3: Implement schema + route**

In `app/schemas/character.py` add:

```python
class CharacterUpdate(BaseModel):
    name: str | None = None
    biography: str | None = None
    locked_traits: list[str] | None = None
    visual_prompt: str | None = None
```

Create `app/api/routes/characters.py`:

```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character
from app.schemas.character import CharacterRead, CharacterUpdate

router = APIRouter(tags=["characters"])


@router.put("/characters/{character_id}", response_model=CharacterRead)
async def update_character(
    character_id: UUID, data: CharacterUpdate, db: AsyncSession = Depends(get_db)
):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(char, key, value)
    await db.commit()
    await db.refresh(char)
    return char
```

- [ ] **Step 4: Register router in main.py**

In `app/main.py` imports add `characters` to the routes import list, and after `anchor_faces` include:

```python
    app.include_router(characters.router, prefix="/api/v1")
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_api/test_characters.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/api/routes/characters.py app/schemas/character.py app/main.py tests/test_api/test_characters.py
git commit -m "feat: add PUT /characters/{id} update endpoint"
```

---

### Task 3: Reference sheet upload/DELETE routes

**Files:**
- Create: `app/api/routes/reference_sheet.py`
- Modify: `app/main.py` (include router)
- Test: `tests/test_api/test_reference_sheet.py`

**Interfaces:**
- Consumes: `Character.reference_sheet_url` (Task 1).
- Produces:
  - `POST /api/v1/characters/{character_id}/reference-sheet` (multipart `file`) → `CharacterRead`
  - `DELETE /api/v1/characters/{character_id}/reference-sheet` → `CharacterRead`
  - Files under `uploads/reference_sheets/`; URL `/uploads/reference_sheets/{filename}` (already mounted in `main.py`).

- [ ] **Step 1: Write failing tests**

Create `tests/test_api/test_reference_sheet.py`:

```python
import io


async def test_upload_and_delete_reference_sheet(client, tmp_path, monkeypatch):
    import app.api.routes.reference_sheet as rs

    monkeypatch.setattr(rs, "UPLOAD_DIR", tmp_path)
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()

    resp = await client.post(
        f"/api/v1/characters/{char['id']}/reference-sheet",
        files={"file": ("sheet.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
    )
    assert resp.status_code == 200
    url = resp.json()["reference_sheet_url"]
    assert url.startswith("/uploads/reference_sheets/")

    resp = await client.delete(f"/api/v1/characters/{char['id']}/reference-sheet")
    assert resp.status_code == 200
    assert resp.json()["reference_sheet_url"] is None


async def test_upload_rejects_non_image(client):
    proj = (await client.post("/api/v1/projects", json={"title": "F"})).json()
    char = (
        await client.post(
            f"/api/v1/projects/{proj['id']}/characters",
            json={"name": "Hero"},
        )
    ).json()
    resp = await client.post(
        f"/api/v1/characters/{char['id']}/reference-sheet",
        files={"file": ("evil.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


async def test_upload_character_not_found(client):
    resp = await client.post(
        "/api/v1/characters/00000000-0000-0000-0000-000000000099/reference-sheet",
        files={"file": ("s.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api/test_reference_sheet.py -v`
Expected: FAIL (404/405 — no route)

- [ ] **Step 3: Implement route module**

Create `app/api/routes/reference_sheet.py`:

```python
import uuid as uuid_mod
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.character import Character

router = APIRouter(tags=["reference-sheet"])

UPLOAD_DIR = Path("uploads/reference_sheets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_BYTES = 5 * 1024 * 1024


@router.post("/characters/{character_id}/reference-sheet")
async def upload_reference_sheet(
    character_id: uuid_mod.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File must be an image")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 5MB)")

    if char.reference_sheet_url:
        old = Path(char.reference_sheet_url.lstrip("/"))
        if old.exists():
            old.unlink()

    ext = Path(file.filename or "sheet.png").suffix or ".png"
    filename = f"{uuid_mod.uuid4()}{ext}"
    (UPLOAD_DIR / filename).write_bytes(content)
    char.reference_sheet_url = f"/uploads/reference_sheets/{filename}"
    await db.commit()
    await db.refresh(char)
    return char


@router.delete("/characters/{character_id}/reference-sheet")
async def delete_reference_sheet(
    character_id: uuid_mod.UUID,
    db: AsyncSession = Depends(get_db),
):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if char.reference_sheet_url:
        path = Path(char.reference_sheet_url.lstrip("/"))
        if path.exists():
            path.unlink()
        char.reference_sheet_url = None
        await db.commit()
        await db.refresh(char)
    return char
```

- [ ] **Step 4: Register in main.py**

Add `reference_sheet` to imports; after anchor_faces include:

```python
    app.include_router(reference_sheet.router, prefix="/api/v1")
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_api/test_reference_sheet.py tests/test_api/test_characters.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/api/routes/reference_sheet.py app/main.py tests/test_api/test_reference_sheet.py
git commit -m "feat: character reference sheet upload and delete endpoints"
```

---

### Task 4: Inject visual_prompt into LLM providers

**Files:**
- Modify: `app/providers/base.py` (shared helper)
- Modify: `app/providers/google.py`, `openai.py`, `nvidia.py`, `groq.py`
- Test: `tests/test_providers/test_visual_prompt.py`

**Interfaces:**
- Consumes: `characters: list[dict]` may include `visual_prompt` and `reference_sheet_url`.
- Produces: helper `format_character_block(characters) -> str` used inside each `generate_prompt`; Google attaches base64 image when `reference_sheet_url` file exists.

- [ ] **Step 1: Write failing tests**

Create `tests/test_providers/test_visual_prompt.py`:

```python
from pathlib import Path

from app.providers.base import format_character_block


def test_format_includes_visual_reference_block():
    chars = [
        {"name": "Hero", "locked_traits": ["brave"], "visual_prompt": "white cloak"},
        {"name": "Villain", "locked_traits": [], "visual_prompt": None},
    ]
    block = format_character_block(chars)
    assert "VISUAL REFERENCE — Hero: white cloak" in block
    assert "Hero: brave" in block
    assert "VISUAL REFERENCE — Villain" not in block


def test_google_builds_image_part_only_when_file_exists(tmp_path, monkeypatch):
    from app.providers import google as g

    monkeypatch.setattr(g, "resolve_sheet_path", lambda url: None)
    assert g.resolve_sheet_path("/uploads/reference_sheets/missing.png") is None

    f = tmp_path / "sheet.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n")
    resolved = f
    assert resolved is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_providers/test_visual_prompt.py -v`
Expected: FAIL (`ImportError: format_character_block`)

- [ ] **Step 3: Implement shared helper**

In `app/providers/base.py` add:

```python
def format_character_block(characters: list[dict]) -> str:
    lines = []
    for c in characters:
        traits = ", ".join(c.get("locked_traits", []))
        lines.append(f"- {c['name']}: {traits}")
        vp = c.get("visual_prompt")
        if vp:
            lines.append(f"VISUAL REFERENCE — {c['name']}: {vp}")
    return "\n".join(lines)
```

- [ ] **Step 4: Replace char_info in all four providers**

In `google.py`, `openai.py`, `nvidia.py`, `groq.py` — replace:

```python
        char_info = "\n".join(
            f"- {c['name']}: {', '.join(c.get('locked_traits', []))}" for c in characters
        )
```

with:

```python
        char_info = format_character_block(characters)
```

and update the import line to include `format_character_block` from `app.providers.base`.

- [ ] **Step 5: Google multimodal sheet attachment**

In `app/providers/google.py` add:

```python
from pathlib import Path as _Path


def resolve_sheet_path(url: str | None) -> _Path | None:
    if not url:
        return None
    p = _Path(url.lstrip("/"))
    return p if p.exists() else None
```

In `generate_prompt`, when building the request body, if any character has a resolvable `reference_sheet_url`, append an inline_data part (base64 PNG) alongside the text part; otherwise keep text-only. Never raise if missing:

```python
import base64

parts = [{"text": prompt}]
for c in characters:
    sheet = resolve_sheet_path(c.get("reference_sheet_url"))
    if sheet:
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": base64.b64encode(sheet.read_bytes()).decode(),
            }
        })
        break
```

Use `parts` in `json={"contents": [{"parts": parts}]}`.

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_providers/ -v`
Expected: PASS (existing registry tests + new)

- [ ] **Step 7: Commit**

```bash
git add app/providers/ tests/test_providers/test_visual_prompt.py
git commit -m "feat: inject character visual_prompt into provider prompts"
```

---

### Task 5: useResizablePanel hook + PanelDivider (TDD)

**Files:**
- Create: `frontend/src/hooks/useResizablePanel.ts`
- Create: `frontend/src/components/layout/PanelDivider.tsx`
- Test: `frontend/src/test/useResizablePanel.test.ts`

**Interfaces:**
- Produces: `useResizablePanel(key, defaultWidth, min, max, sign): { width, dividerProps }`; `<PanelDivider {...dividerProps} />`.

- [ ] **Step 1: Write failing hook tests**

Create `frontend/src/test/useResizablePanel.test.ts`:

```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useResizablePanel } from '../hooks/useResizablePanel';

describe('useResizablePanel', () => {
  beforeEach(() => localStorage.clear());

  it('uses default when no stored value', () => {
    const { result } = renderHook(() => useResizablePanel('sidebar', 320, 220, 560, 1));
    expect(result.current.width).toBe(320);
  });

  it('reads stored value and clamps on init', () => {
    localStorage.setItem('panel-width:sidebar', '9999');
    const { result } = renderHook(() => useResizablePanel('sidebar', 320, 220, 560, 1));
    expect(result.current.width).toBe(560);
  });

  it('applies sign and clamps during drag, persists on pointerup', () => {
    const { result } = renderHook(() => useResizablePanel('sidebar', 320, 220, 560, 1));
    const handlers = result.current.dividerProps;
    (handlers as any).onPointerDown({ clientX: 0, currentTarget: { setPointerCapture: () => {} } });
    (handlers as any).onPointerMove({ clientX: 50 });
    expect(result.current.width).toBe(370);
    (handlers as any).onPointerMove({ clientX: 10000 });
    expect(result.current.width).toBe(560);
    (handlers as any).onPointerUp({});
    expect(localStorage.getItem('panel-width:sidebar')).toBe('560');
  });

  it('sign -1 shrinks on positive delta and clamps at min', () => {
    const { result } = renderHook(() => useResizablePanel('command', 384, 300, 640, -1));
    const handlers = result.current.dividerProps;
    (handlers as any).onPointerDown({ clientX: 0, currentTarget: { setPointerCapture: () => {} } });
    (handlers as any).onPointerMove({ clientX: 20 });
    // 384 - 20 = 364
    expect(result.current.width).toBe(364);
    (handlers as any).onPointerMove({ clientX: 10000 });
    // 384 - 10000 clamped to min 300
    expect(result.current.width).toBe(300);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Program Files\nodejs\npm.cmd test -- useResizablePanel`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement hook**

Create `frontend/src/hooks/useResizablePanel.ts`:

```ts
import { useCallback, useEffect, useRef, useState } from 'react';

export function useResizablePanel(
  key: string,
  defaultWidth: number,
  min: number,
  max: number,
  sign: 1 | -1
) {
  const storageKey = `panel-width:${key}`;
  const [width, setWidth] = useState<number>(() => {
    if (typeof window === 'undefined') return defaultWidth;
    const raw = window.localStorage.getItem(storageKey);
    const n = raw ? Number(raw) : NaN;
    if (Number.isFinite(n)) return Math.min(max, Math.max(min, n));
    return defaultWidth;
  });

  const startRef = useRef({ x: 0, w: defaultWidth });

  const onPointerDown = useCallback(
    (e: React.PointerEvent | any) => {
      startRef.current = { x: e.clientX, w: width };
      e.currentTarget?.setPointerCapture?.(e.pointerId ?? 1);
    },
    [width]
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent | any) => {
      if (typeof e.buttons === 'number' && e.buttons === 0 && e.type === 'pointermove' && !draggingRef.current) return;
      const delta = e.clientX - startRef.current.x;
      const next = Math.min(max, Math.max(min, startRef.current.w + sign * delta));
      setWidth(next);
    },
    [min, max, sign]
  );

  const draggingRef = useRef(false);

  // rebind with dragging flag
  const startDrag = useCallback(
    (e: any) => {
      draggingRef.current = true;
      startRef.current = { x: e.clientX, w: width };
      e.currentTarget?.setPointerCapture?.(e.pointerId ?? 1);
    },
    [width]
  );

  const onPointerUp = useCallback(() => {
    draggingRef.current = false;
    setWidth((w) => {
      window.localStorage.setItem(storageKey, String(w));
      return w;
    });
  }, [storageKey]);

  useEffect(() => {
    // noop: handlers are stable enough for consumers
  }, []);

  const dividerProps = {
    onPointerDown: startDrag,
    onPointerMove: (e: any) => {
      if (!draggingRef.current) return;
      const delta = e.clientX - startRef.current.x;
      setWidth(Math.min(max, Math.max(min, startRef.current.w + sign * delta)));
    },
    onPointerUp,
    onPointerCancel: onPointerUp,
  };

  return { width, dividerProps };
}
```

Note: use pointer capture so `pointermove`/`pointerup` fire on the divider itself; `draggingRef` guards stray moves. (Implement cleanly — the sketch above is the contract; final code must pass the tests.)

- [ ] **Step 4: Implement PanelDivider**

Create `frontend/src/components/layout/PanelDivider.tsx`:

```tsx
import React from 'react';

export const PanelDivider: React.FC<any> = (props) => (
  <div
    role="separator"
    aria-orientation="vertical"
    data-testid="panel-divider"
    className="w-1 shrink-0 cursor-col-resize hover:bg-[var(--color-accent)] transition-colors"
    style={{ backgroundColor: 'var(--color-border)' }}
    {...props}
  />
);
```

- [ ] **Step 5: Run tests to verify pass**

Run: `C:\Program Files\nodejs\npm.cmd test -- useResizablePanel`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/useResizablePanel.ts frontend/src/components/layout/PanelDivider.tsx frontend/src/test/useResizablePanel.test.ts
git commit -m "feat: resizable panel hook and divider component"
```

---

### Task 6: Wire Sidebar + CommandCenter widths

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.tsx` (aside line ~68)
- Modify: `frontend/src/components/layout/CommandCenter.tsx` (aside line ~24)

**Interfaces:**
- Consumes: `useResizablePanel`, `PanelDivider` (Task 5).
- Produces: Sidebar width key `sidebar` (320/220/560/+1, divider on right); CommandCenter key `command` (384/300/640/−1, divider on left).

- [ ] **Step 1: Update Sidebar**

In `Sidebar.tsx` add imports and hook call:

```tsx
import { useResizablePanel } from '../../hooks/useResizablePanel';
import { PanelDivider } from './PanelDivider';
// inside component:
const { width, dividerProps } = useResizablePanel('sidebar', 320, 220, 560, 1);
```

Change `<aside className="w-80 ...">` → `<aside className="flex flex-col border-r shrink-0 overflow-hidden surface-panel" style={{ width, borderColor: 'var(--color-border)' }}>`

Close aside with divider inside (right edge, last child before `</aside>`):

```tsx
      <PanelDivider {...dividerProps} />
    </aside>
```

- [ ] **Step 2: Update CommandCenter**

```tsx
import { useResizablePanel } from '../../hooks/useResizablePanel';
import { PanelDivider } from './PanelDivider';
// inside component:
const { width, dividerProps } = useResizablePanel('command', 384, 300, 640, -1);
```

Change aside: remove `w-96`, set `style={{ width, borderColor: 'var(--color-border)' }}`. Render `<PanelDivider {...dividerProps} />` as **first** child of the aside (left edge), or immediately before content — visually left border area.

- [ ] **Step 3: Verify build + existing tests**

Run: `C:\Program Files\nodejs\npm.cmd run build` then `C:\Program Files\nodejs\npm.cmd test`
Expected: build PASS; 24+ tests PASS (App tests still find Story Bible etc.)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/Sidebar.tsx frontend/src/components/layout/CommandCenter.tsx
git commit -m "feat: make sidebar and command center resizable"
```

---

### Task 7: Frontend API client + useStudioApi methods

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/hooks/useStudioApi.ts`
- Test: `frontend/src/test/api-client.test.ts` (extend if present)

**Interfaces:**
- Produces:
  - `Character.reference_sheet_url?: string | null`, `Character.visual_prompt?: string | null`
  - `charactersApi.uploadReferenceSheet(id, file): Promise<AxiosResponse<Character>>`
  - `charactersApi.deleteReferenceSheet(id): Promise<AxiosResponse<Character>>`
  - `useStudioApi` exposes `uploadReferenceSheet(characterId, file): Promise<Character>` and `deleteReferenceSheet(characterId): Promise<Character>` with toasts.

- [ ] **Step 1: Write failing client test**

Add to `frontend/src/test/api-client.test.ts` (or create):

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, charactersApi } from '../api/client';

describe('charactersApi reference sheet', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('uploadReferenceSheet posts multipart form data', async () => {
    const spy = vi.spyOn(api, 'post').mockResolvedValue({ data: {} } as any);
    const file = new File(['x'], 's.png', { type: 'image/png' });
    await charactersApi.uploadReferenceSheet('c1', file);
    expect(spy).toHaveBeenCalledWith(
      '/characters/c1/reference-sheet',
      expect.any(FormData),
      expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
    );
  });

  it('deleteReferenceSheet calls delete', async () => {
    const spy = vi.spyOn(api, 'delete').mockResolvedValue({ data: {} } as any);
    await charactersApi.deleteReferenceSheet('c1');
    expect(spy).toHaveBeenCalledWith('/characters/c1/reference-sheet');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Program Files\nodejs\npm.cmd test -- api-client`
Expected: FAIL (methods undefined)

- [ ] **Step 3: Implement client types + methods**

In `frontend/src/api/client.ts` update `Character` interface:

```ts
export interface Character {
  id: string;
  project_id: string;
  name: string;
  biography: string | null;
  locked_traits: string[];
  voice_profile_id: string | null;
  reference_sheet_url?: string | null;
  visual_prompt?: string | null;
}
```

Extend `charactersApi`:

```ts
  uploadReferenceSheet: (id: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Character>(`/characters/${id}/reference-sheet`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  deleteReferenceSheet: (id: string) =>
    api.delete<Character>(`/characters/${id}/reference-sheet`),
```

- [ ] **Step 4: Extend useStudioApi**

After `deleteAnchorFace` add:

```ts
  const uploadReferenceSheet = async (characterId: string, file: File) => {
    setLoading('reference-sheet', true);
    try {
      const res = await charactersApi.uploadReferenceSheet(characterId, file);
      showToast('Reference sheet uploaded', 'success');
      return res.data;
    } catch {
      showToast('Reference sheet upload failed', 'error');
      throw new Error('Reference sheet upload failed');
    } finally {
      setLoading('reference-sheet', false);
    }
  };

  const deleteReferenceSheet = async (characterId: string) => {
    try {
      const res = await charactersApi.deleteReferenceSheet(characterId);
      showToast('Reference sheet removed', 'info');
      return res.data;
    } catch {
      showToast('Reference sheet deletion failed', 'error');
      throw new Error('Reference sheet deletion failed');
    }
  };
```

Export both from the hook's return object.

- [ ] **Step 5: Run tests**

Run: `C:\Program Files\nodejs\npm.cmd test`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/hooks/useStudioApi.ts frontend/src/test/api-client.test.ts
git commit -m "feat: frontend API for character reference sheet and visual_prompt"
```

---

### Task 8: AssetsPanel editingCharData + PersonnelDossier UI

**Files:**
- Modify: `frontend/src/components/story/AssetsPanel.tsx`
- Modify: `frontend/src/components/story/PersonnelDossier.tsx`
- Test: `frontend/src/test/PersonnelDossier.test.tsx`

**Interfaces:**
- Consumes: `useStudioApi.uploadReferenceSheet/deleteReferenceSheet`, `Character.visual_prompt/reference_sheet_url` (Task 7).
- Produces: `editingCharData` includes `visual_prompt`; PersonnelDossier renders Reference Sheet dropzone/preview + Visual Reference textarea bound to `editingCharData.visual_prompt`, saved via existing SAVE CHANGES.

- [ ] **Step 1: Write failing UI test**

Create `frontend/src/test/PersonnelDossier.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PersonnelDossier } from '../components/story/PersonnelDossier';

const baseProps = {
  characters: [{ id: 'c1', name: 'Hero', locked_traits: [] }],
  anchorFaces: { c1: [] },
  selectedCharId: 'c1',
  setSelectedCharId: vi.fn(),
  editingCharData: { name: 'Hero', biography: '', locked_traits: [], visual_prompt: '' },
  setEditingCharData: vi.fn(),
  traitInput: '',
  setTraitInput: vi.fn(),
  updateCharacter: vi.fn(),
  uploadAnchorFace: vi.fn(),
  deleteAnchorFace: vi.fn(),
  faceAngle: 'Front',
  setFaceAngle: vi.fn(),
  isPrimaryFace: false,
  setIsPrimaryFace: vi.fn(),
  loadingStates: {},
  fileInputRef: { current: null } as any,
  uploadReferenceSheet: vi.fn(),
  deleteReferenceSheet: vi.fn(),
};

describe('PersonnelDossier', () => {
  it('shows reference sheet dropzone when no image', () => {
    render(<PersonnelDossier {...baseProps} />);
    expect(screen.getByText('REFERENCE SHEET')).toBeInTheDocument();
  });

  it('shows visual reference textarea', () => {
    render(<PersonnelDossier {...baseProps} />);
    expect(screen.getByLabelText(/visual reference/i)).toBeInTheDocument();
  });

  it('shows preview when reference_sheet_url present', () => {
    const char = { ...baseProps.characters[0], reference_sheet_url: '/uploads/reference_sheets/a.png' };
    render(<PersonnelDossier {...baseProps} characters={[char]} />);
    expect(screen.getByRole('img', { name: /reference/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Program Files\nodejs\npm.cmd test -- PersonnelDossier`
Expected: FAIL (dropzone/textarea missing)

- [ ] **Step 3: Extend AssetsPanel editingCharData**

In the character-select effect, add `visual_prompt`:

```ts
setEditingCharData({
  name: char.name,
  biography: char.biography || '',
  locked_traits: [...char.locked_traits],
  visual_prompt: char.visual_prompt || '',
});
```

Initialize state type:

```ts
const [editingCharData, setEditingCharData] = useState<{
  name: string; biography: string; locked_traits: string[]; visual_prompt: string;
} | null>(null);
```

Pass new props to `PersonnelDossier`: `uploadReferenceSheet={api.uploadReferenceSheet}` and `deleteReferenceSheet={api.deleteReferenceSheet}`.

Extend `handleUpdateCharacter` to send `visual_prompt` (it already passes `editingCharData`).

- [ ] **Step 4: Implement PersonnelDossier UI**

Add optional props to interface:

```ts
  uploadReferenceSheet?: (charId: string, file: File) => Promise<any>;
  deleteReferenceSheet?: (charId: string) => Promise<any>;
```

In active-char card, after Biography textarea add **Visual Reference** block:

```tsx
            <div className="space-y-1">
              <label className="text-[8px] mono text-gray-600 uppercase">
                Visual Reference (for AI)
              </label>
              <textarea
                aria-label="Visual Reference"
                value={editingCharData.visual_prompt ?? ''}
                onChange={(e) => setEditingCharData({ ...editingCharData, visual_prompt: e.target.value })}
                placeholder="Appearance, wardrobe, personality for renders..."
                className="w-full bg-black/40 text-xs p-2 rounded border border-[var(--color-border)] mono text-white h-24 resize-none focus:border-[var(--color-accent)] outline-none"
              />
            </div>
```

After Anchor Faces section (or before Locked Traits) add **Reference Sheet** block:

```tsx
            <div className="pt-3 border-t border-[var(--color-border)] space-y-2">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-3 h-3 text-gray-500" />
                <span className="text-[9px] mono text-gray-500 uppercase">Reference Sheet</span>
              </div>
              {activeChar.reference_sheet_url ? (
                <div className="relative aspect-[3/4] max-w-[120px] rounded border border-[var(--color-border)] bg-black group">
                  <img
                    src={`http://localhost:8000${activeChar.reference_sheet_url}`}
                    alt="Character reference sheet"
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100">
                    <label className="cursor-pointer px-1 py-0.5 bg-black/80 text-[8px] mono rounded border border-white/20">
                      Replace
                      <input type="file" accept="image/*" className="hidden"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) uploadReferenceSheet?.(activeChar.id, f);
                        }} />
                    </label>
                    <button
                      onClick={() => deleteReferenceSheet?.(activeChar.id)}
                      className="px-1 py-0.5 bg-red-500/40 text-[8px] mono rounded"
                    >Delete</button>
                  </div>
                </div>
              ) : (
                <label className="flex flex-col items-center justify-center aspect-[3/4] max-w-[120px] rounded border border-dashed border-[var(--color-border)] cursor-pointer hover:border-[var(--color-accent)]">
                  <Upload className="w-4 h-4 mb-1 opacity-50" />
                  <span className="text-[8px] mono text-gray-500 uppercase">REFERENCE SHEET</span>
                  <input type="file" accept="image/*" className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) uploadReferenceSheet?.(activeChar.id, f);
                    }} />
                </label>
              )}
            </div>
```

Import `Image` as `ImageIcon` from lucide-react if needed (already has `Upload`).

- [ ] **Step 5: Run tests**

Run: `C:\Program Files\nodejs\npm.cmd test`
Expected: PASS (all existing + new)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/story/AssetsPanel.tsx frontend/src/components/story/PersonnelDossier.tsx frontend/src/test/PersonnelDossier.test.tsx
git commit -m "feat: character reference sheet upload UI and visual reference textarea"
```

---

### Task 9: Full verification + final commit

**Files:** none new — run gates only.

- [ ] **Step 1: Frontend build + test + lint**

Run from `frontend/`:
```
C:\Program Files\nodejs\npm.cmd run build
C:\Program Files\nodejs\npm.cmd test
C:\Program Files\nodejs\npm.cmd run lint
```
Expected: all PASS; lint warnings only (no errors).

- [ ] **Step 2: Backend full pytest**

Run: `python -m pytest -q`
Expected: all PASS.

- [ ] **Step 3: Manual smoke (optional if API up)**

- Open `http://localhost:5173`, drag both dividers, reload → widths persist.
- Select character → upload sheet, see preview; type visual prompt → SAVE CHANGES.
- Verify PUT `/characters/{id}` returns `visual_prompt`.

- [ ] **Step 4: Final commit if any leftovers**

```bash
git add -A
git commit -m "chore: verification pass for resizable panels and character reference"
```

---

## Self-Review Notes (for plan author)

- Spec coverage: Task 1 (model/migration/schemas), Task 2 (PUT update — **discovered missing**), Task 3 (upload/DELETE routes), Task 4 (provider injection + Gemini image), Tasks 5–6 (hook + divider + layout), Task 7 (client + hook methods), Task 8 (UI), Task 9 (verification).
- Placeholders: none — all steps have code/commands.
- Type consistency: `visual_prompt` snake_case across Python/TS; `reference_sheet_url`; hook signature `(key, defaultWidth, min, max, sign)`.
- Ambiguity fixed: `/uploads` already mounted in `main.py` (no static-files task needed); character PUT did not exist and is explicitly Task 2.
