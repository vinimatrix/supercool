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

