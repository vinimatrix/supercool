### Task 2: Settings additions + MuseTalk client strict mode

**Files:**
- Modify: `app/config.py`
- Modify: `app/services/musetalk_client.py`
- Test: `tests/test_services/test_musetalk_strict.py`

**Interfaces:**
- Produces: `settings.musetalk_dir: str` (default `""` → resolved against `BASE_DIR/musetalk`), `settings.musetalk_timeout: int` (default `3600`); `MuseTalkClient.align_lip_sync(..., strict: bool = False)` raising `RuntimeError` in strict mode.

- [ ] **Step 1: Write failing tests**

Create `tests/test_services/test_musetalk_strict.py`:

```python
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import settings
from app.services.musetalk_client import MuseTalkClient


def test_settings_musetalk_fields():
    assert hasattr(settings, "musetalk_dir")
    assert hasattr(settings, "musetalk_timeout")
    assert settings.musetalk_timeout > 0


def test_align_strict_raises_on_failed_inference(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    video = tmp_path / "src.mp4"
    audio = tmp_path / "a.wav"
    video.write_bytes(b"x")
    audio.write_bytes(b"x")
    with patch.object(client, "_run_musetalk", return_value=(False, "", "boom")):
        with pytest.raises(RuntimeError, match="MuseTalk failed"):
            client.align_lip_sync(str(video), str(audio), {}, strict=True)


def test_align_strict_raises_when_output_missing(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    video = tmp_path / "src.mp4"
    audio = tmp_path / "a.wav"
    video.write_bytes(b"x")
    audio.write_bytes(b"x")
    with patch.object(client, "_run_musetalk", return_value=(True, "", "")):
        with pytest.raises(RuntimeError, match="MuseTalk produced no output"):
            client.align_lip_sync(str(video), str(audio), {}, output_filename="out.mp4", strict=True)


def test_align_lenient_still_returns_on_failure(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    video = tmp_path / "src.mp4"
    audio = tmp_path / "a.wav"
    video.write_bytes(b"x")
    audio.write_bytes(b"x")
    with patch.object(client, "_run_musetalk", return_value=(False, "", "boom")):
        result = client.align_lip_sync(str(video), str(audio), {})
        assert Path(result).exists()
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_services/test_musetalk_strict.py -v`
Expected: FAIL (`TypeError: unexpected keyword 'strict'` / missing settings attrs)

- [ ] **Step 3: Read current code, then implement**

First read `app/config.py` and `app/services/musetalk_client.py` in full (also confirm `_run_musetalk` return signature — adjust test/impl to match reality; the tests above assume `(success: bool, stdout: str, stderr: str)`).

- Add to `Settings`:
  ```python
  musetalk_dir: str = ""
  musetalk_timeout: int = 3600
  ```
- In `MuseTalkClient.align_lip_sync`, accept `strict: bool = False`. When inference reports failure: if strict → `raise RuntimeError(f"MuseTalk failed: {stderr or stdout}")`; else keep existing lenient source-copy behavior. When success but output missing: if strict → `raise RuntimeError("MuseTalk produced no output video")`; else keep existing behavior.
- Do **not** change existing call sites (`voice.py` keeps default lenient).

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_services/test_musetalk_strict.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/config.py app/services/musetalk_client.py tests/test_services/test_musetalk_strict.py
git commit -m "feat: strict mode for MuseTalk client + lipsync settings"
```

