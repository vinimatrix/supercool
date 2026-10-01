import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import settings
from app.services.musetalk_client import LipSyncConfig, MuseTalkClient


def _client(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    client.output_dir = tmp_path / "out"
    client.output_dir.mkdir()
    return client


def _inputs(tmp_path):
    video = tmp_path / "src.mp4"
    audio = tmp_path / "a.wav"
    video.write_bytes(b"x")
    audio.write_bytes(b"x")
    return video, audio


def test_settings_musetalk_fields():
    assert hasattr(settings, "musetalk_dir")
    assert hasattr(settings, "musetalk_timeout")
    assert settings.musetalk_timeout > 0


def test_align_strict_raises_on_failed_inference(tmp_path):
    client = _client(tmp_path)
    video, audio = _inputs(tmp_path)
    failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")
    with (
        patch.object(client, "_run_musetalk", return_value=failed),
        pytest.raises(RuntimeError, match="MuseTalk failed"),
    ):
        client.align_lip_sync(str(video), str(audio), LipSyncConfig(), strict=True)


def test_align_strict_raises_when_output_missing(tmp_path):
    client = _client(tmp_path)
    video, audio = _inputs(tmp_path)
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with (
        patch.object(client, "_run_musetalk", return_value=ok),
        pytest.raises(RuntimeError, match="MuseTalk produced no output"),
    ):
        client.align_lip_sync(
            str(video), str(audio), LipSyncConfig(), output_filename="out.mp4", strict=True
        )


def test_align_strict_wraps_exceptions(tmp_path):
    client = _client(tmp_path)
    video, audio = _inputs(tmp_path)
    with (
        patch.object(client, "_run_musetalk", side_effect=TimeoutError("timed out")),
        pytest.raises(RuntimeError, match="MuseTalk failed"),
    ):
        client.align_lip_sync(str(video), str(audio), LipSyncConfig(), strict=True)


def test_align_lenient_still_returns_on_failure(tmp_path):
    client = _client(tmp_path)
    video, audio = _inputs(tmp_path)
    failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")
    with patch.object(client, "_run_musetalk", return_value=failed):
        result = client.align_lip_sync(str(video), str(audio), LipSyncConfig())
        assert Path(result).exists()


def test_client_accepts_musetalk_dir(tmp_path):
    client = MuseTalkClient(musetalk_dir=str(tmp_path))
    assert client.musetalk_dir == str(tmp_path)
