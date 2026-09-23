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

