# Task 1 Report: Character model + Alembic migration + schemas

**Status:** DONE_WITH_CONCERNS  
**Commit:** `4cae6d7` — feat: add character reference_sheet_url and visual_prompt fields

## What I implemented

1. **Model** (`app/models/character.py`): added `reference_sheet_url: Mapped[str | None]` and `visual_prompt: Mapped[str | None]` (both `Text`, nullable) after `voice_profile_id`, exactly per brief.
2. **Schemas** (`app/schemas/character.py`): `CharacterCreate` gains `visual_prompt: str | None = None` only (reference_sheet_url deliberately NOT client-settable); `CharacterRead` gains both `visual_prompt` and `reference_sheet_url`, both optional with defaults.
3. **Test fixture** (`tests/conftest.py`): added `reference_sheet_url TEXT,` and `visual_prompt TEXT,` to `CREATE_CHARACTERS` after `voice_profile_id`.
4. **Migration** (`alembic/versions/add_character_reference_fields.py`): revision `c0ffee123abc`, `down_revision=fcae66ea5e4b`, adds both columns as nullable `sa.Text()`, downgrade drops both in reverse order. Verified single alembic head: `c0ffee123abc (head)`, history chain `1239ffa4cbf8 -> fcae66ea5e4b -> c0ffee123abc`.
5. **Tests** (`tests/test_models/test_models.py`): appended `test_character_has_reference_fields` and `test_character_schemas_expose_visual_prompt` (imports placed in the existing import block rather than mid-file).

## TDD Evidence

### RED (before implementation)

Command: `python -m pytest tests/test_models/test_models.py -v`

```
tests/test_models/test_models.py::test_character_has_reference_fields FAILED
tests/test_models/test_models.py::test_character_schemas_expose_visual_prompt FAILED
=========================== short test summary ============================
FAILED tests/test_models/test_models.py::test_character_has_reference_fields
  E   AssertionError: assert False
   +  where False = hasattr(<app.models.character.Character object ...>, 'reference_sheet_url')
FAILED tests/test_models/test_models.py::test_character_schemas_expose_visual_prompt
  E   AttributeError: 'CharacterCreate' object has no attribute 'visual_prompt'
2 failed, 3 passed
```

Both failed for the expected reason (missing fields), not typos.

### GREEN (after implementation)

Command: `python -m pytest tests/test_models/test_models.py -v`

```
tests/test_models/test_models.py::test_project_model PASSED
tests/test_models/test_models.py::test_character_model PASSED
tests/test_models/test_models.py::test_shot_model PASSED
tests/test_models/test_models.py::test_character_has_reference_fields PASSED
tests/test_models/test_models.py::test_character_schemas_expose_visual_prompt PASSED
5 passed in 0.08s
```

### Full suite (before commit)

Command: `python -m pytest tests/ -q --ignore=tests/test_providers/test_registry.py --deselect=... (3 pre-existing broken tests, see concerns)`

```
102 passed, 3 deselected, 28 warnings in 20.56s
```

Warnings are pre-existing (`datetime.utcnow()` deprecation in SQLAlchemy defaults).

## Files changed

- `app/models/character.py` (+2 lines)
- `app/schemas/character.py` (+3 lines)
- `tests/conftest.py` (+2 lines)
- `tests/test_models/test_models.py` (+38 lines)
- `alembic/versions/add_character_reference_fields.py` (new, 27 lines)

## Self-review findings

- **Completeness:** All 8 brief steps done. `reference_sheet_url` absent from `CharacterCreate` (constraint honored). `down_revision` exact. Commit message exact from brief; only the 5 specified files staged.
- **Quality:** Names/fields match brief verbatim. Import for new schema types placed in the top import block (brief's snippet appended it mid-file after `test_shot_model`; mid-file import would be non-idiomatic — behavior identical).
- **YAGNI:** Nothing beyond the brief (no routes, no extra fields, no refactoring of pre-existing issues).
- **Testing:** TDD RED→GREEN followed; tests assert real behavior via public model/schema API. All my changed lines ≤100 chars (ruff line-length constraint).
- **Ruff:** `ruff check` on changed files reports violations (I001/UP007/UP035/F401) — all verified **identical to baseline** via stash comparison: they pre-exist on these files and on older migrations. My migration matches the existing Alembic template style verbatim as the brief requires. No new violations introduced.

## Issues / concerns (pre-existing, verified at baseline — not caused by this task)

1. **4 broken/hanging tests in full suite** (all confirmed by stashing my changes and re-running):
   - `tests/test_providers/test_registry.py` — collection error: `ModuleNotFoundError: No module named 'groq'` (missing dependency; `groq` not in pyproject deps).
   - `tests/test_db/test_database.py::test_database_connection` — `ConnectionRefusedError` (no local Postgres).
   - `tests/test_integration_local_analyzer.py::...::test_qwen_analyzer_init` — fails because Ollama IS available in this environment (test asserts unavailable).
   - `tests/test_local/test_coordinator.py::...::test_analyze_shot_returns_dict` — **hangs indefinitely** (>90 s timeout at baseline too; appears to call a live LLM backend). This is why a naive full-suite run never completes.
2. The project-wide baseline is not `pytest` green / `ruff` clean in this environment; constraints hold for all tests not already broken at baseline.
3. Note: a pre-existing unrelated stash (`stash@{1}` "local changes") was already in the repo before this task; I left it untouched.
