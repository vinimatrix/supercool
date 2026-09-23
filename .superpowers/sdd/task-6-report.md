# Task 6 Report: Wire Sidebar + CommandCenter widths

**Status:** DONE_WITH_CONCERNS
**Commit:** `553de22` — feat: make sidebar and command center resizable
**Branch:** feat/frontend-obsidian-overhaul

## Changes

### `frontend/src/components/layout/Sidebar.tsx`
- Imported `useResizablePanel` + `PanelDivider`.
- Hook: `useResizablePanel('sidebar', 320, 220, 560, 1)`.
- `<aside>`: removed `w-80`, added `relative`, `style={{ width, borderColor: ... }}`.
- `<PanelDivider {...dividerProps} />` as last child (right edge).

### `frontend/src/components/command/CommandCenter.tsx`
- **Path deviation:** brief says `layout/CommandCenter.tsx`, actual path is `components/command/CommandCenter.tsx` (plan's file list was stale; import paths adjusted accordingly: `../../hooks/useResizablePanel`, `../layout/PanelDivider`).
- Hook: `useResizablePanel('command', 384, 300, 640, -1)`.
- `<aside>`: removed `w-96`, added `relative`, `style={{ width, borderColor: ... }}`.
- `<PanelDivider {...dividerProps} />` as first child (left edge).

### Unchanged
- `MainLayout.tsx` — center `<main>` stays `flex-1`, no divider (per constraints).
- No new dependencies.

## Deviation from brief (justified)

The brief showed a bare `<PanelDivider {...dividerProps} />` inside the `flex flex-col` asides. The divider is a `w-1` div with no content, so in a column flex container it collapses to **0 height** (invisible, undraggable) — the resize feature would not work. Minimal fix applied within the two edited files only:

- Added `relative` to both asides.
- Positioned the divider absolutely on its intended edge via a `style` prop:
  - Sidebar: `position: absolute; top: 0; bottom: 0; right: 0; zIndex: 10`
  - CommandCenter: same with `left: 0`
  - Includes `backgroundColor: var(--color-border)` because JSX prop spread order means the passed `style` fully replaces PanelDivider's internal style.

This preserves the brief's structure (divider first/last child, correct edge, correct keys/limits/sign) while making the handle actually visible and draggable.

## Verification

| Check | Command | Result |
|-------|---------|--------|
| Build | `npm run build` (`tsc -b && vite build`) | PASS |
| Tests | `npm test` | PASS — 28/28 (4 files), includes Task 5's 4 hook tests |
| Lint | `npm run lint` (oxlint) | PASS — exit 0; only pre-existing warnings, none in edited files |

## Self-review

- Keys/limits/sign match spec: sidebar 320/220/560/+1, command 384/300/640/−1. ✅
- `w-80`/`w-96` fully removed; no test references them (grep verified). ✅
- Story Bible label / App tests unaffected (still pass). ✅
- Drag math: sidebar right edge (sign +1) grows rightward; command left edge (sign −1) grows leftward. ✅
- Persistence on `pointerup` via `localStorage['panel-width:<key>']` (Task 5 hook). ✅
- Only the two intended files committed. ✅

## Concerns

1. **Divider placement deviation** (described above) — reviewers diffing against the plan will see `style` positioning and `relative` classes not in the brief. Intent-level correct; plan text was silently broken for a flex-col layout.
2. **Hover accent feedback** — `PanelDivider` sets inline `backgroundColor`, which beats its `hover:bg-[var(--color-accent)]` class, so hover highlight never applies (pre-existing Task 5 issue, unchanged here).
3. Plan's brief listed wrong path for CommandCenter (`layout/` vs actual `command/`) — worth fixing in the plan doc if reused.
