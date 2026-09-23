# Task 7 Report: Frontend API client + useStudioApi methods

**Status:** DONE
**Commit:** `ad1edb9` — feat: frontend API for character reference sheet and visual_prompt
**Branch:** feat/frontend-obsidian-overhaul

## Changes

### `frontend/src/api/client.ts`
- `Character` interface: added `reference_sheet_url?: string | null` and `visual_prompt?: string | null` (snake_case, matches backend).
- `charactersApi.uploadReferenceSheet(id, file)` — builds `FormData` with `file` entry, `POST /characters/{id}/reference-sheet` with `Content-Type: multipart/form-data`; returns `Promise<AxiosResponse<Character>>`.
- `charactersApi.deleteReferenceSheet(id)` — `DELETE /characters/{id}/reference-sheet`; returns `Promise<AxiosResponse<Character>>`.
- Pattern mirrors existing `shotsApi.uploadVideo` multipart usage.

### `frontend/src/hooks/useStudioApi.ts`
- Added `uploadReferenceSheet(characterId, file)` after `deleteAnchorFace`:
  - `setLoading('reference-sheet', true/false)` in try/finally
  - toasts: success `'Reference sheet uploaded'`, error `'Reference sheet upload failed'` + rethrow
  - returns `res.data` (`Character`)
- Added `deleteReferenceSheet(characterId)`:
  - no loading key (matches `deleteAnchorFace` pattern per brief)
  - toasts: info `'Reference sheet removed'`, error `'Reference sheet deletion failed'` + rethrow
  - returns `res.data` (`Character`)
- Both exported from the hook's return object.

### `frontend/src/test/api-client.test.ts`
- Extended with `describe('charactersApi reference sheet')` (per brief, spying on shared `api` instance):
  - `uploadReferenceSheet posts multipart form data` — asserts `api.post` called with `/characters/c1/reference-sheet`, `expect.any(FormData)`, headers `multipart/form-data`
  - `deleteReferenceSheet calls delete` — asserts `api.delete` called with `/characters/c1/reference-sheet`

## TDD

| Phase | Command | Result |
|-------|---------|--------|
| RED | `npm test -- api-client` | FAIL as expected: `charactersApi.uploadReferenceSheet is not a function`, `charactersApi.deleteReferenceSheet is not a function` (feature missing, not typo) |
| GREEN | `npm test -- api-client` | PASS — 8/8 |
| Full suite | `npm test` | PASS — 30/30 (4 files) |

## Verification

| Check | Command | Result |
|-------|---------|--------|
| Tests | `C:\Program Files\nodejs\npm.cmd test` | PASS — 30/30 (4 files) |
| Build | `C:\Program Files\nodejs\npm.cmd run build` (`tsc -b && vite build`) | PASS |
| Lint | `C:\Program Files\nodejs\npm.cmd run lint` (oxlint) | PASS — exit 0; only pre-existing warnings, none in edited files |

## Self-review

- Field names snake_case: `reference_sheet_url`, `visual_prompt` ✅
- Endpoints match backend Tasks 1–3: `POST`/`DELETE /characters/{id}/reference-sheet` ✅
- Multipart form field key is `file` (matches backend upload contract) ✅
- Hook methods return `Character`, use toasts, upload uses `reference-sheet` loading key ✅
- Only the three intended files committed; no new deps ✅
- Existing tests untouched and still green; static import of `api`/`charactersApi` coexists with the file's axios module mock (`axios.create` returns the shared mock, so `vi.spyOn(api, ...)` works) ✅
- `updateCharacter(id, Partial<Character>)` now type-allows `visual_prompt`/`reference_sheet_url` updates through existing `PUT /characters/{id}` ✅

## Concerns

1. Hook methods (`uploadReferenceSheet`/`deleteReferenceSheet`) are not covered by a dedicated unit test — the brief scoped tests to the API client only; behavior follows the established `deleteAnchorFace` pattern.
2. No UI consumes the new methods yet (expected — later tasks wire PersonnelDossier).
