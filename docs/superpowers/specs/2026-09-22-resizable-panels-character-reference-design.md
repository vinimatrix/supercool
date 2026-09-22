# Design: Resizable Panels + Character Reference Sheet

**Date:** 2026-09-22
**Status:** Approved
**Scope:** Frontend layout + character assets (Story Bible) + creative pipeline prompt injection

## Context

The obsidian frontend uses fixed-width panels (`Sidebar w-80`, `CommandCenter w-96`). Users need to drag-resize the three horizontal regions. Characters currently have biography, locked traits, and anchor faces, but no single "character sheet" image or AI-facing visual reference text. Both must feed the creative render pipeline.

## Decisions (user-confirmed)

| Question | Answer |
|---|---|
| Which panels resizable? | All 3 horizontal (sidebar, center flex, command center) |
| Reference sheet shape? | One primary image per character (not a gallery; does not replace anchor faces) |
| "Textos de referencia"? | Editable AI visual-prompt fields (appearance, wardrobe, personality) |
| Pipeline integration? | Persist in backend + inject into creative pipeline prompt; sheet available as control image |

**Approaches chosen:** A1 (custom hook + localStorage) and B1 (extend `Character` model).

**Unresolved until implementation:** confirm the exact existing character-update HTTP method/path used by `charactersApi.update` and whether `app/main.py` already mounts `/uploads` (plan step verifies both; add mount only if missing).

---

## Section 1: Resizable panels (A1)

### `useResizablePanel(key, defaultWidth, min, max, sign)`

Location: `frontend/src/hooks/useResizablePanel.ts`

- Initial width: `localStorage['panel-width:' + key]` if present, else `defaultWidth`; always clamped to `[min, max]`.
- `sign: 1 | -1` converts drag deltaX into width delta: `width = startWidth + sign * deltaX`.
- Returns `{ width, dividerProps }` where `dividerProps` are pointer handlers for the divider element.
- On `pointerdown`: `setPointerCapture`, listen `pointermove`/`pointerup` on the divider (captured), compute `deltaX = clientX - startX`, apply sign, clamp to `[min, max]`, `setState`; on `pointerup`, persist to `localStorage` and release listeners.
- SSR/jsdom safe: no window access at module top level.

### `PanelDivider`

Location: `frontend/src/components/layout/PanelDivider.tsx`

- 4px wide, `cursor-col-resize`, background `var(--color-border)`, hover/focus → `var(--color-accent)` with subtle glow.
- Spreads `dividerProps` from the hook; `role="separator"` with `aria-orientation="vertical"`.

### Layout integration

- `Sidebar`: replace `w-80` with `style={{ width }}`; key `sidebar`, default 320, min 220, max 560, `sign = 1` (its right edge moves right → wider). Renders `PanelDivider` on its right edge.
- `CommandCenter`: replace `w-96` with `style={{ width }}`; key `command`, default 384, min 300, max 640, `sign = -1` (its left edge moves left → wider, i.e. positive deltaX shrinks it). Renders `PanelDivider` on its left edge.
- `MainLayout` center `<main>` stays `flex-1`; no center divider (vertical preview/timeline resize out of scope).
- Hook lives **inside** each side panel; panels own their width state.

### Tests (vitest)

- Hook: reads default when no localStorage; reads stored value; clamps on init; clamps during drag; persists on pointerup; width math for `sign = 1` vs `sign = -1`.
- `PanelDivider` renders with `cursor-col-resize` class/style and separator role.

---

## Section 2: Character reference sheet + visual reference (B1)

### Backend

**Model** `app/models/character.py` — `Character`:

- `reference_sheet_url: Mapped[str | None]` (nullable)
- `visual_prompt: Mapped[str | None]` (nullable, text)

**Migration:** Alembic revision adding both columns (nullable, no data migration).

**Schemas** `app/schemas/character.py`:

- `CharacterRead`: + `reference_sheet_url`, `visual_prompt`
- `CharacterCreate`: + optional `visual_prompt`. `reference_sheet_url` is **not** client-settable on create/update (only upload/DELETE routes touch it).

**Routes:**

- `POST /api/v1/characters/{character_id}/reference-sheet` — `UploadFile`; save to `uploads/reference_sheets/{uuid}{ext}`; if previous file exists on disk, delete it; set `reference_sheet_url = /uploads/reference_sheets/{filename}`; return `CharacterRead`. 404 if character missing. Reject non-image content types and >5MB (400/413).
- `DELETE /api/v1/characters/{character_id}/reference-sheet` — remove file if present, null the column, return `CharacterRead`.
- Character update: the existing `charactersApi.update` (PATCH/PUT already used by `updateCharacter` in `useStudioApi`) accepts optional `visual_prompt` in its body.

**Static files:** ensure `/uploads/...` is served (same mechanism as `anchor_faces` / workspace files — verify `app/main.py` StaticFiles mounts; add mount for `uploads` if missing).

**Creative pipeline injection:**

- Where providers build prompts from characters (`app/providers/google.py`, `openai.py`, `nvidia.py`, `groq.py` — same place `locked_traits` is formatted today): append per-character block when `visual_prompt` is set:
  `VISUAL REFERENCE — {name}: {visual_prompt}`
- Multimodal path (Gemini / `google.py`): if `reference_sheet_url` resolves to an existing file on disk, attach image content to the request. Other providers: text-only (image omitted, never fail the render if file missing).

### Frontend

**API client** (`frontend/src/api/client.ts`):

- Type `Character`: + `reference_sheet_url?: string | null`, `visual_prompt?: string | null`
- `charactersApi.uploadReferenceSheet(id, file)` — multipart POST
- `charactersApi.deleteReferenceSheet(id)` — DELETE
- Update path already sends `visual_prompt` once added to edit state.

**`AssetsPanel`:** extend `editingCharData` state with `visual_prompt`; sync in existing character-select effect.

**`PersonnelDossier`** — two new blocks in the active-character card:

1. **Reference Sheet** (adjacent to Anchor Faces):
   - No image: dashed dropzone `aspect-[3/4]`, Upload icon, label "REFERENCE SHEET".
   - Has image: `<img>` `object-contain` on black; hover overlays Replace (file input) and Delete buttons.
   - Optimistic preview via `URL.createObjectURL` until server response; revoke object URL on unmount/replace.
2. **Visual Reference (for AI):** textarea (`h-24`) bound to `editingCharData.visual_prompt`, placed under Biography; persisted with the existing **SAVE CHANGES** button (no new save button).

### Errors

- Client: toast via existing `useStudioApi` toast channel on upload failure, non-image type, >5MB.
- Server: 404 character, 400 bad type, 413 too large → structured HTTP errors; frontend maps to toast.
- Pipeline: missing image file on disk → skip image attachment, continue render.

### Testing

- Backend (pytest): upload happy path sets URL and stores file; delete removes file and nulls column; 404 unknown character; provider prompt includes `visual_prompt` when set.
- Frontend (vitest): PersonnelDossier shows dropzone when `reference_sheet_url` null, preview when set; visual_prompt textarea visible and bound; existing App tests keep passing.

### Non-goals

- Multi-image gallery / reference types table (defer until needed).
- Vertical (preview vs timeline) resize.
- Replacing or reinterpreting anchor faces.
- Non-Gemini multimodal image attachment.

## Verification

- `npm run build`, `npm test`, `npm run lint` green in `frontend/`.
- Backend: targeted pytest for new routes + provider prompt test.
- Manual: drag both dividers → widths persist across reload; upload/delete reference sheet; save visual_prompt; creative render prompt contains the text block.
