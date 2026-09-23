# Task 2 Report: PUT /characters/{id} update endpoint

**Status:** DONE
**Commit:** `304ac3f` — feat: add PUT /characters/{id} update endpoint

## What I implemented

1. **Schema** (`app/schemas/character.py`): added `CharacterUpdate` with exactly `name`, `biography`, `locked_traits`, `visual_prompt` — all `str | None` / `list[str] | None = None`. `reference_sheet_url` deliberately ABSENT (constraint: only upload/DELETE routes set it).
2. **Route** (`app/api/routes/characters.py`, new): `PUT /characters/{character_id}` → `CharacterRead`; 404 `"Character not found"` when missing; `model_dump(exclude_unset=True)` partial update; commit + refresh. One deviation from the brief snippet: dropped the unused `from sqlalchemy import select` import (would be ruff F401; brief code doesn't use it).
3. **Registration** (`app/main.py`): added `characters` to the routes import list; `app.include_router(characters.router, prefix="/api/v1")` immediately after `anchor_faces`, as specified.
4. **Tests** (`tests/test_api/test_characters.py`, new): `test_update_character_visual_prompt` and `test_update_character_not_found`, verbatim from the brief.

## TDD Evidence

### RED (before implementation)

Command: `python -m pytest tests/test_api/test_characters.py -v`

```
tests/test_api/test_characters.py::test_update_character_visual_prompt FAILED
tests/test_api/test_characters.py::test_update_character_not_found FAILED
E   assert 405 == 200   (405 Method Not Allowed — no PUT route)
E   assert 405 == 404
============================== short test summary summary ===========================
2 failed, 4 warnings in 1.32s
```

Failed for the expected reason (missing route), exactly as the brief predicted.

### GREEN (after implementation)

Command: `python -m pytest tests/test_api/test_characters.py -v`

```
tests/test_api/test_characters.py::test_update_character_visual_prompt PASSED
tests/test_api/test_characters.py::test_update_character_not_found PASSED
============================== short test summary ==========================
2 passed, 5 warnings in 0.43s
```

### Full suite (before commit)

Command: `python -m pytest tests/ -q --ignore=tests/test_providers/test_registry.py --deselect=tests/test_db/test_database.py::test_database_connection --deselect=tests/test_integration_local_analyzer.py::TestLocalAnalyzerIntegration::test_qwen_analyzer_init --deselect=tests/test_local/test_coordinator.py::TestLocalVideoCoordinator::test_analyze_shot_returns_dict`

```
104 passed, 3 deselected, 33 warnings in 14.30s
```

104 = 102 baseline (per Task 1 report) + 2 new. The ignored/deselected tests are the same 4 pre-existing environment-broken tests documented in Task 1 (missing `groq`, no local Postgres, Ollama-available assertion mismatch, hanging coordinator test) — not touched.

## Files changed

- `app/api/routes/characters.py` (new, 25 lines)
- `app/schemas/character.py` (+7 lines: `CharacterUpdate`)
- `app/main.py` (+2 lines: import + include_router)
- `tests/test_api/test_characters.py` (new, 24 lines)

Commit contains exactly the 4 files the brief specified, message exact: `feat: add PUT /characters/{id} update endpoint`.

## Self-review findings

- **Completeness:** All 6 brief steps done. Interface matches: `PUT /api/v1/characters/{character_id}` accepting `{name?, biography?, locked_traits?, visual_prompt?}` → `CharacterRead`. Router placed after `anchor_faces` as specified.
- **Quality:** Follows existing route patterns (`scenes.py` style: UUID path param, `db.get`, 404 raise, commit/refresh). All changed lines ≤100 chars (ruff line-length 100).
- **YAGNI:** Nothing beyond the brief — no extra fields, no partial-update helper, no refactoring of pre-existing issues.
- **Testing:** TDD RED→GREEN followed; tests assert real HTTP behavior through the public API. Focused-test output pristine (2 passed).
- **Ruff:** `python -m ruff check` on changed files reports only:
  - `B008` in `characters.py` — the standard FastAPI `Depends(...)` idiom; fires identically on every baseline route file (`scenes.py`, `anchor_faces.py`, 11 pre-existing hits). Matches project convention; suppressing/reworking would diverge from all sibling routes.
  - `I001` in `app/schemas/character.py` — verified **pre-existing** by stashing my change and re-running ruff (fires at baseline). Not introduced by this task.

## Concerns

1. **`.gitignore:90` has a broad `test_*.py` pattern** that matches everything under `tests/`. Existing test files are tracked (force-added historically). I used `git add -f tests/test_api/test_characters.py` to include it, per the brief's instruction to commit that file. A follow-up could narrow the ignore pattern (e.g. `/test_*.py`) so new tests aren't silently ignored — left alone as out of scope.
2. Same 4 pre-existing environment-broken tests as Task 1 (deselected, not fixed). Baseline remains: full suite is green only with those exclusions.
3. `B008`/`I001` ruff findings on changed files are baseline-identical (evidence above); the project-wide ruff baseline is not clean in this environment.

---

## Fix Report: Review Finding — Reject null for non-nullable fields in CharacterUpdate

**Status:** DONE
**Commit:** `e9ff054` — fix: reject null for non-nullable fields in CharacterUpdate

### What changed

1. **Route** (`app/api/routes/characters.py`): Added validation in `update_character` to check if `name` or `locked_traits` are explicitly set to `null` in the request body (using `model_fields_set`). If so, raises `HTTPException 422` with detail `"Field 'X' cannot be null"`. Omitted fields still work for partial updates. `biography` and `visual_prompt` still accept explicit `null` (nullable columns).

2. **Tests** (`tests/test_api/test_characters.py`): Added 4 new tests:
   - `test_update_character_rejects_null_name` — PUT with `{"name": null}` → 422
   - `test_update_character_rejects_null_locked_traits` — PUT with `{"locked_traits": null}` → 422
   - `test_update_character_allows_null_biography` — PUT with `{"biography": null}` → 200
   - `test_update_character_allows_null_visual_prompt` — PUT with `{"visual_prompt": null}` → 200

### Covering test commands + results

```
python -m pytest tests/test_api/test_characters.py -v
# 6 passed

python -m pytest tests/test_api -v
# 13 passed
```

All tests pass. Existing tests still pass. The fix prevents 500 IntegrityError by rejecting explicit null for non-nullable DB columns at the API layer with clear 422 response.
