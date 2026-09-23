# Task 3 Report: Reference Sheet Upload/DELETE Routes

## What Was Implemented

Created `app/api/routes/reference_sheet.py` with two endpoints:
- `POST /api/v1/characters/{character_id}/reference-sheet` — Upload a reference sheet image (multipart/form-data)
- `DELETE /api/v1/characters/{character_id}/reference-sheet` — Delete the reference sheet

Registered the router in `app/main.py` with prefix `/api/v1`.

## Key Implementation Details

- **File validation**: Only image content-types allowed (png, jpeg, webp, gif); max 5 MB
- **File storage**: Files saved to `uploads/reference_sheets/` with UUID filenames
- **URL format**: Returns `/uploads/reference_sheets/{filename}` (served by existing StaticFiles mount)
- **Old file cleanup**: On upload replacement or delete, the old file is removed from disk
- **Character not found**: Returns 404 if character doesn't exist
- **Follows anchor_faces.py pattern**: Same structure for file handling, DB operations, error responses

## Tests Written (TDD RED → GREEN)

Created `tests/test_api/test_reference_sheet.py` with 3 tests:

1. **test_upload_and_delete_reference_sheet** — Full upload/delete cycle; verifies URL format and cleanup
2. **test_upload_rejects_non_image** — Rejects non-image content-type with 400
3. **test_upload_character_not_found** — Returns 404 for non-existent character

All 3 tests pass (GREEN).

## Test Results

```
tests/test_api/test_reference_sheet.py::test_upload_and_delete_reference_sheet PASSED
tests/test_api/test_reference_sheet.py::test_upload_rejects_non_image PASSED
tests/test_api/test_reference_sheet.py::test_upload_character_not_found PASSED

tests/test_api/test_characters.py (6 tests) — all PASS
Full API test suite (16 tests) — all PASS
```

## Files Changed

- `app/api/routes/reference_sheet.py` (new, 65 lines)
- `app/main.py` (added import and router registration)
- `tests/test_api/test_reference_sheet.py` (new, 49 lines)

## Concerns

- **Pre-existing lint warnings**: ruff B008 (function calls in default args) and ASYNC230 (blocking file I/O in async) exist in both the new file and the reference `anchor_faces.py`. These are pre-existing patterns in the codebase and were not addressed per "follow existing patterns" instruction.
- **Test file ignored by .gitignore**: Had to force-add the test file; may need .gitignore update if tests should be tracked.

## Commit

```
85b1acb feat: character reference sheet upload and delete endpoints
```