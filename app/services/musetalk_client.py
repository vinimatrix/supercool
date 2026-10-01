"""MuseTalk 1.5 client for lip-sync integration."""

import os
import uuid
import json
import shutil
import subprocess
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

MUSOTALK_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models", "MuseTalk")
)


@dataclass
class LipSyncConfig:
    """Configuration for lip-sync processing."""
    bbox_shift: int = 0
    preparation_mode: bool = False
    fps: int = 25
    resolution: str = "256x256"


class MuseTalkClient:
    """Client for MuseTalk 1.5 lip-sync engine."""

    def __init__(self, model_path: Optional[str] = None, musetalk_dir: Optional[str] = None):
        self.output_dir = Path("./workspace/lipsync")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.musetalk_dir = os.path.abspath(musetalk_dir) if musetalk_dir else MUSOTALK_DIR

    def _run_musetalk(self, args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
        """Run MuseTalk inference script with proper PYTHONPATH."""
        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{self.musetalk_dir};{pythonpath}" if pythonpath else self.musetalk_dir
        env["TORCHDYNAMO_DISABLE"] = "1"

        cmd = ["python", os.path.join(self.musetalk_dir, "scripts", "inference.py")] + args
        logger.info("Running MuseTalk: %s", " ".join(cmd))
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)

    def prepare_avatar(
        self,
        video_path: str,
        output_filename: Optional[str] = None,
    ) -> str:
        if output_filename is None:
            output_filename = f"avatar_{uuid.uuid4().hex[:8]}"

        output_path = self.output_dir / output_filename
        output_path.mkdir(parents=True, exist_ok=True)

        frames_dir = output_path / "frames"
        frames_dir.mkdir(exist_ok=True)

        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", video_path, str(frames_dir / "%08d.png")],
                capture_output=True, check=True, timeout=60,
            )
            logger.info("Avatar prepared: %s frames extracted", len(list(frames_dir.glob("*.png"))))
        except Exception as e:
            logger.error("Avatar preparation failed: %s", e)

        return str(output_path)

    def align_lip_sync(
        self,
        video_path: str,
        audio_path: str,
        config: LipSyncConfig,
        output_filename: Optional[str] = None,
        strict: bool = False,
    ) -> str:
        if output_filename is None:
            output_filename = f"lipsync_{uuid.uuid4().hex[:8]}.mp4"

        output_path = self.output_dir / output_filename

        with tempfile.TemporaryDirectory() as tmpdir:
            inference_config = {
                "task_0": {
                    "video_path": os.path.abspath(video_path),
                    "audio_path": os.path.abspath(audio_path),
                    "bbox_shift": config.bbox_shift,
                }
            }
            config_path = os.path.join(tmpdir, "inference.yaml")
            with open(config_path, "w") as f:
                json.dump(inference_config, f, indent=2)

            try:
                result = self._run_musetalk([
                    "--inference_config", config_path,
                    "--result_dir", tmpdir,
                    "--fps", str(config.fps),
                    "--use_float16",
                    "--gpu_id", "0",
                    "--version", "v15",
                    "--unet_config", "./models/musetalkV15/musetalk.json",
                    "--unet_model_path", "./models/musetalkV15/unet.pth",
                ], timeout=settings.musetalk_timeout)

                if result.returncode != 0:
                    if strict:
                        detail = (result.stderr or result.stdout or "").strip()
                        raise RuntimeError(f"MuseTalk failed: {detail[-500:]}")
                    logger.warning("MuseTalk stderr: %s", result.stderr[-500:])

                for mp4 in Path(tmpdir).rglob("*.mp4"):
                    shutil.copy2(str(mp4), str(output_path))
                    break
                else:
                    if strict:
                        raise RuntimeError("MuseTalk produced no output video")
                    logger.warning("No output video found, copying source")
                    shutil.copy2(video_path, str(output_path))

            except Exception as e:
                if strict:
                    if isinstance(e, RuntimeError):
                        raise
                    raise RuntimeError(f"MuseTalk failed: {e}") from e
                logger.error("MuseTalk lip-sync failed: %s", e)
                shutil.copy2(video_path, str(output_path))

        return str(output_path)

    def process_dialogue(
        self,
        video_path: str,
        audio_path: str,
        emotion: str = "neutral",
        output_filename: Optional[str] = None,
    ) -> str:
        emotion_shifts = {
            "neutral": 0, "happy": 2, "sad": -1,
            "angry": 3, "determined": 2, "whisper": -2,
        }
        config = LipSyncConfig(bbox_shift=emotion_shifts.get(emotion, 0))
        return self.align_lip_sync(video_path, audio_path, config, output_filename)
