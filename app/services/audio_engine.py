"""Audio Engine - AI-powered sound design, music generation, and mixing."""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum


class SoundLayer(Enum):
    DIALOGUE = "dialogue"
    MUSIC = "music"
    SFX = "sfx"
    AMBIENCE = "ambience"


@dataclass
class AudioTrack:
    """An audio track to mix."""
    path: str
    layer: SoundLayer
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    duck_under: bool = False
    pan: float = 0.0  # -1.0 left, 0.0 center, 1.0 right


@dataclass
class SoundDesign:
    """AI-generated sound design plan."""
    ambience: str  # rain, forest, city, silence
    mood: str  # tense, calm, action, dramatic
    music_style: str  # orchestral, electronic, ambient, none


class AudioEngine:
    """AI-powered audio engine for sound design and mixing."""

    AMBIENCE_PATTERNS = {
        "rain": "anoisesrc=d={dur}:c=pink:r=48000:a=0.02",
        "forest": "anoisesrc=d={dur}:c=brown:r=48000:a=0.01",
        "wind": "anoisesrc=d={dur}:c=pink:r=48000:a=0.015",
        "silence": "anullsrc=r=48000:cl=stereo",
        "city": "anoisesrc=d={dur}:c=pink:r=48000:a=0.025",
    }

    def generate_ambience(self, duration: float, ambience_type: str, output_path: str) -> str:
        """Generate ambient background sound."""
        pattern = self.AMBIENCE_PATTERNS.get(ambience_type, self.AMBIENCE_PATTERNS["silence"])
        source = pattern.format(dur=duration + 1)
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", source,
            "-t", str(duration),
            "-af", "lowpass=f=2000,highpass=f=100",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path

    def generate_tone(self, frequency: float, duration: float, output_path: str, 
                      volume: float = 0.3, fade: float = 0.5) -> str:
        """Generate a tone (for music beds, tension, etc.)."""
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration={duration}",
            "-af", f"volume={volume},afade=t=in:d={fade},afade=t=out:st={duration-fade}:d={fade}",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path

    def generate_tension_bed(self, duration: float, output_path: str) -> str:
        """Generate a tension-building audio bed."""
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"sine=frequency=60:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=120:duration={duration}",
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2,"
            f"volume=0.4,afade=t=in:d=2,afade=t=out:st={duration-2}:d=2[out]",
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path

    def mix_tracks(self, tracks: list[AudioTrack], output_path: str, master_volume: float = 1.0) -> str:
        """Mix multiple audio tracks with volume control and ducking."""
        if not tracks:
            return output_path

        cmd = ["ffmpeg", "-y"]
        inputs = []
        
        for i, track in enumerate(tracks):
            # Normalize path for ffmpeg
            track_path = track.path.replace("\\", "/")
            cmd.extend(["-i", track_path])
            inputs.append(i)

        # Build filter complex
        filters = []
        for i, track in enumerate(tracks):
            vol = track.volume
            fades = []
            
            if track.fade_in > 0:
                fades.append(f"afade=t=in:d={track.fade_in}")
            if track.fade_out > 0:
                fades.append(f"afade=t=out:st=999:d={track.fade_out}")
            
            # Pan
            pan_filter = ""
            if track.pan != 0:
                pan_val = (track.pan + 1) / 2
                pan_filter = f",pan=stereo|c0=c0*{1-pan_val}+c1*{pan_val}|c1=c0*{pan_val}+c1*{1-pan_val}"

            af = []
            if vol != 1.0:
                af.append(f"volume={vol}")
            af.extend(fades)
            
            if af or pan_filter:
                filter_str = f"[{i}:a]" + ",".join(af) + pan_filter + f"[a{i}]"
            else:
                filter_str = f"[{i}:a]anull[a{i}]"
            filters.append(filter_str)

        # Mix all tracks
        mix_inputs = "".join(f"[a{i}]" for i in range(len(tracks)))
        filters.append(
            f"{mix_inputs}amix=inputs={len(tracks)}:duration=longest:dropout_transition=2"
            f"[out]"
        )

        filter_complex = ";".join(filters)
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[out]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Audio mix error: {result.stderr[-500:]}")
        return output_path

    def duck_audio(self, main_path: str, duck_path: str, output_path: str,
                   duck_level: float = 0.15, threshold: float = 0.02) -> str:
        """Duck audio when dialogue/presence detected."""
        cmd = [
            "ffmpeg", "-y",
            "-i", main_path,
            "-i", duck_path,
            "-filter_complex",
            f"[1:a]volume={duck_level}[duck];"
            f"[0:a][duck]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path

    def analyze_sound_design(self, video_path: str, scene_context: str = "") -> SoundDesign:
        """AI analysis to determine appropriate sound design."""
        context_lower = scene_context.lower()
        
        if "rain" in context_lower or "forest" in context_lower:
            ambience = "rain"
        elif "wind" in context_lower or "mountain" in context_lower:
            ambience = "wind"
        elif "city" in context_lower or "urban" in context_lower:
            ambience = "city"
        else:
            ambience = "silence"

        if "action" in context_lower or "combat" in context_lower or "fight" in context_lower:
            mood = "tense"
            music_style = "orchestral"
        elif "dialogue" in context_lower or "quiet" in context_lower:
            mood = "dramatic"
            music_style = "ambient"
        else:
            mood = "calm"
            music_style = "none"

        return SoundDesign(ambience=ambience, mood=mood, music_style=music_style)


if __name__ == "__main__":
    engine = AudioEngine()
    workspace = r"C:\Users\vm004458\Documents\supercool\workspace"
    
    # Generate tension bed
    print("Generating tension bed...")
    engine.generate_tension_bed(20.0, os.path.join(workspace, "tension_bed.m4a"))
    
    # Generate rain ambience
    print("Generating rain ambience...")
    engine.generate_ambience(20.0, "rain", os.path.join(workspace, "rain_ambience.m4a"))
    
    print("Done!")
