# Task 4 Report: Inject visual_prompt into LLM providers

## Summary
Successfully implemented visual_prompt injection into all four LLM providers (Google, OpenAI, NVIDIA, Groq) with Google-specific multimodal reference sheet attachment.

## Changes Made

### 1. `app/providers/base.py`
- Added shared `format_character_block(characters: list[dict]) -> str` helper function
- Formats each character with locked_traits and includes `VISUAL REFERENCE — {name}: {visual_prompt}` when visual_prompt is present
- Uses em dash (—) as specified

### 2. `app/providers/google.py`
- Added `resolve_sheet_path(url: str | None) -> _Path | None` function to resolve reference_sheet_url to local file path
- Modified `generate_prompt()` to use `format_character_block()`
- Added multimodal support: when a character has a resolvable `reference_sheet_url`, attaches the image as base64 `inline_data` (image/png) in the request parts
- Graceful degradation: never raises if file missing, simply omits image attachment

### 3. `app/providers/openai.py`, `app/providers/nvidia.py`, `app/providers/groq.py`
- Updated imports to include `format_character_block` from base
- Modified `generate_prompt()` to use `format_character_block()` instead of inline char_info construction
- No image attachment logic (Google-only as specified)

### 4. `tests/test_providers/test_visual_prompt.py`
- Added `test_format_includes_visual_reference_block()` - verifies helper formats visual reference correctly
- Added `test_google_builds_image_part_only_when_file_exists()` - verifies resolve_sheet_path behavior

## Test Results
```
tests/test_providers/test_registry.py::test_provider_registry_creation PASSED
tests/test_providers/test_registry.py::test_provider_interface PASSED
tests/test_providers/test_registry.py::test_entity_dataclass PASSED
tests/test_providers/test_registry.py::test_registry_with_empty_providers PASSED
tests/test_providers/test_registry.py::test_registry_get_named_provider PASSED
tests/test_providers/test_visual_prompt.py::test_format_includes_visual_reference_block PASSED
tests/test_providers/test_visual_prompt.py::test_google_builds_image_part_only_when_file_exists PASSED
```
All 7 tests pass.

## Linting
- Ran `ruff check app/providers/ --fix` - 7 auto-fixed import sorting issues
- 1 pre-existing BLE001 (blind exception catch in groq.py) remains, unchanged

## Commit
- `2861ead` - "feat: inject character visual_prompt into provider prompts"

## Critical Review Fix (resolve_sheet_path test)

### Finding
`test_google_builds_image_part_only_when_file_exists` did not exercise the function under test:
- Exists-case assigned `resolved = f` instead of calling `g.resolve_sheet_path(str(f))`
- Missing-case monkeypatched `resolve_sheet_path` to `lambda url: None`, then asserted against the mock
- Unused `from pathlib import Path` import (ruff F401)

### Fix (`tests/test_providers/test_visual_prompt.py`)
- Removed `monkeypatch` parameter; both cases now call the real `g.resolve_sheet_path`
- Missing file → asserts real function returns `None`
- Existing file → asserts real function returns the resolved `Path` (`resolved == f`)
- Removed unused `pathlib.Path` import

### Verification
```
uv run --extra dev pytest tests/test_providers/test_visual_prompt.py -v  → 2 passed
uv run --extra dev pytest tests/test_providers/ -v                       → 7 passed
uv run --extra dev ruff check app/providers/google.py tests/test_providers/test_visual_prompt.py → All checks passed!
```
Note: `groq` package installed into the venv (`uv pip install groq`) to unblock collection — pre-existing missing dependency documented in task-1 report, not part of this fix.

### Commit
- `26835c8` - "fix: correct test for resolve_sheet_path"