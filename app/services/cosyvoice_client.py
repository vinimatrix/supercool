"""CosyVoice 3.0 client for text-to-speech and voice cloning."""

import os
import sys
import uuid
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_cosyvoice_model = None


def _get_cosyvoice_model():
    """Lazy-load CosyVoice2 model (singleton)."""
    global _cosyvoice_model
    if _cosyvoice_model is not None:
        return _cosyvoice_model

    cosyvoice_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "models", "CosyVoice"
    )
    cosyvoice_dir = os.path.abspath(cosyvoice_dir)
    model_dir = os.path.join(cosyvoice_dir, "pretrained_models", "CosyVoice2-0.5B")

    if not os.path.isdir(model_dir):
        raise FileNotFoundError(f"CosyVoice2 model not found at {model_dir}")

    if cosyvoice_dir not in sys.path:
        sys.path.insert(0, cosyvoice_dir)
    third_party = os.path.join(cosyvoice_dir, "third_party", "Matcha-TTS")
    if third_party not in sys.path:
        sys.path.insert(0, third_party)

    from cosyvoice.cli.cosyvoice import AutoModel

    logger.info("Loading CosyVoice2 model from %s...", model_dir)
    _cosyvoice_model = AutoModel(model_dir=model_dir)
    logger.info("CosyVoice2 model loaded (SR=%d)", _cosyvoice_model.sample_rate)
    return _cosyvoice_model


@dataclass
class VoiceProfile:
    """Voice profile for TTS synthesis."""
    name: str
    language: str = "es"  # es, en, ja, zh
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 1.0


class CosyVoiceClient:
    """Client for CosyVoice 3.0 text-to-speech engine."""

    def __init__(self, model_path: Optional[str] = None):
        self.output_dir = Path("./workspace/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _lang_tag(self, language: str) -> str:
        lang_map = {"es": "es", "en": "en", "ja": "ja", "zh": "zh", "auto": "auto"}
        return lang_map.get(language, "auto")

    def synthesize(
        self,
        text: str,
        voice_profile: VoiceProfile,
        output_filename: Optional[str] = None,
        prompt_wav: Optional[str] = None,
    ) -> str:
        if output_filename is None:
            output_filename = f"dialogue_{uuid.uuid4().hex[:8]}.wav"

        output_path = self.output_dir / output_filename

        try:
            model = _get_cosyvoice_model()
            from cosyvoice.utils.file_utils import save_wav

            lang_tag = self._lang_tag(voice_profile.language)
            tts_text = f"<|{lang_tag}|>{text}"

            if prompt_wav is None:
                prompt_wav = os.path.join(
                    os.path.dirname(__file__), "..", "..",
                    "models", "CosyVoice", "asset", "zero_shot_prompt.wav"
                )
                prompt_wav = os.path.abspath(prompt_wav)

            if not os.path.isfile(prompt_wav):
                raise FileNotFoundError(f"Prompt audio not found: {prompt_wav}")

            for i, result in enumerate(model.inference_cross_lingual(
                tts_text, prompt_wav, stream=False
            )):
                chunk_path = str(output_path).replace(".wav", f"_{i}.wav")
                save_wav(chunk_path, result["tts_speech"], model.sample_rate)
                logger.info("Saved CosyVoice chunk: %s", chunk_path)

            return str(output_path)

        except Exception as e:
            logger.error("CosyVoice synthesis failed: %s", e)
            self._create_placeholder_audio(output_path, text)
            return str(output_path)

    def clone_voice(
        self,
        reference_audio_path: str,
        text: str,
        output_filename: Optional[str] = None,
    ) -> str:
        if output_filename is None:
            output_filename = f"cloned_{uuid.uuid4().hex[:8]}.wav"

        output_path = self.output_dir / output_filename

        try:
            model = _get_cosyvoice_model()
            from cosyvoice.utils.file_utils import save_wav

            for i, result in enumerate(model.inference_cross_lingual(
                f"<|auto|>{text}", reference_audio_path, stream=False
            )):
                chunk_path = str(output_path).replace(".wav", f"_{i}.wav")
                save_wav(chunk_path, result["tts_speech"], model.sample_rate)

            return str(output_path)

        except Exception as e:
            logger.error("CosyVoice voice clone failed: %s", e)
            self._create_placeholder_audio(output_path, text)
            return str(output_path)

    def _create_placeholder_audio(self, output_path: Path, text: str):
        """Fallback: create silent audio placeholder."""
        import subprocess

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "anullsrc=r=24000:cl=mono",
            "-t", "3", str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, timeout=10)
