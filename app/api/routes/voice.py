"""Voice API - CosyVoice 3.0 text-to-speech and voice cloning endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.cosyvoice_client import CosyVoiceClient, VoiceProfile
from app.services.musetalk_client import MuseTalkClient, LipSyncConfig

router = APIRouter(prefix="/voice", tags=["voice"])

# Initialize client
cosyvoice_client = CosyVoiceClient()


class SynthesizeRequest(BaseModel):
    """Request model for text-to-speech synthesis."""
    text: str
    language: str = "es"
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 1.0
    voice_name: str = "default"


class SynthesizeResponse(BaseModel):
    """Response model for synthesis results."""
    audio_path: str
    duration_seconds: float = 3.0


class CloneVoiceRequest(BaseModel):
    """Request model for voice cloning."""
    reference_audio_path: str
    text: str


class CloneVoiceResponse(BaseModel):
    """Response model for voice cloning results."""
    audio_path: str
    duration_seconds: float = 3.0


class LipSyncRequest(BaseModel):
    """Request model for lip-sync processing."""
    video_path: str
    audio_path: str
    emotion: str = "neutral"
    bbox_shift: int = 0


class LipSyncResponse(BaseModel):
    """Response model for lip-sync results."""
    output_path: str
    duration_seconds: float = 3.0
    fps: int = 24


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(data: SynthesizeRequest):
    """Synthesize dialogue text into speech audio.

    Uses CosyVoice 3.0 to generate natural-sounding speech with the specified
    language, emotion, and voice characteristics.
    """
    try:
        voice_profile = VoiceProfile(
            name=data.voice_name,
            language=data.language,
            emotion=data.emotion,
            speed=data.speed,
            pitch=data.pitch,
        )
        audio_path = cosyvoice_client.synthesize(
            text=data.text,
            voice_profile=voice_profile,
        )
        return SynthesizeResponse(audio_path=audio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone", response_model=CloneVoiceResponse)
async def clone_voice(data: CloneVoiceRequest):
    """Clone a voice from reference audio and synthesize new text.

    Uses CosyVoice 3.0's voice cloning capability to generate speech
    that matches the voice characteristics of the reference audio.
    """
    try:
        audio_path = cosyvoice_client.clone_voice(
            reference_audio_path=data.reference_audio_path,
            text=data.text,
        )
        return CloneVoiceResponse(audio_path=audio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lipsync", response_model=LipSyncResponse)
def align_lip_sync(request: LipSyncRequest):
    """Align lip-sync between video and audio.

    Uses MuseTalk 1.5 to synchronize lip movements in the video
    with the provided audio track.
    """
    try:
        musetalk = MuseTalkClient()

        config = LipSyncConfig(
            bbox_shift=request.bbox_shift,
            preparation_mode=False
        )

        output_path = musetalk.align_lip_sync(
            request.video_path,
            request.audio_path,
            config
        )

        return LipSyncResponse(
            output_path=output_path,
            duration_seconds=3.0,
            fps=24
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
