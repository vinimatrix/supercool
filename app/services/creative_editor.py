"""Creative Editor - AI-powered video editing with transitions, audio mixing, and color grading."""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum


class TransitionType(Enum):
    CUT = "cut"
    CROSSFADE = "crossfade"
    WHIP_PAN = "whip_pan"
    MATCH_CUT = "match_cut"
    SPEED_RAMP = "speed_ramp"
    DIP_BLACK = "dip_black"


@dataclass
class ClipEdit:
    """Edit parameters for a single clip."""
    path: str
    duration: float
    transition_in: TransitionType = TransitionType.CUT
    transition_out: TransitionType = TransitionType.CUT
    transition_duration: float = 0.5
    speed: float = 1.0
    color_grade: str = "neutral"
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0


@dataclass
class EditDecision:
    """AI-generated edit decision for a clip."""
    clip_index: int
    transition_in: TransitionType
    transition_out: TransitionType
    transition_duration: float
    speed: float
    color_grade: str
    volume: float
    emotional_beat: str
    pacing_note: str


class CreativeEditor:
    """AI-powered creative editor that makes intelligent editing decisions."""

    COLOR_GRADES = {
        "neutral": "eq=brightness=0.02:saturation=1",
        "warm": "colortemperature=temperature=5500,eq=saturation=1.2:brightness=0.03",
        "cold": "colortemperature=temperature=4000,eq=saturation=0.9:brightness=0.02",
        "cinematic": "eq=saturation=0.9:contrast=1.05:brightness=0.01",
        "noir": "eq=saturation=0.1:contrast=1.2:brightness=0",
        "action": "eq=saturation=1.2:contrast=1.1:brightness=0.02",
        "dramatic": "eq=contrast=1.1:saturation=0.95:brightness=0.01,colorbalance=rs=-0.03:gs=-0.03:bs=0.03",
        "night": "eq=brightness=-0.25:saturation=0.5:contrast=1.3,colorbalance=rs=-0.15:gs=-0.1:bs=0.25:rm=-0.1:gm=-0.05:bm=0.15:rh=-0.2:gh=-0.15:bh=0.2",
    }

    def analyze_and_edit(self, clips: list[ClipEdit]) -> list[EditDecision]:
        """Analyze clips and generate edit decisions."""
        decisions = []
        for i, clip in enumerate(clips):
            decision = self._make_decision(clip, i, len(clips))
            decisions.append(decision)
        return decisions

    def _make_decision(self, clip: ClipEdit, index: int, total: int) -> EditDecision:
        """Make creative editing decision for a clip."""
        # Determine transitions based on position
        if index == 0:
            trans_in = TransitionType.CUT
        elif index == total - 1:
            trans_in = TransitionType.CROSSFADE
            trans_out = TransitionType.DIP_BLACK
        else:
            # Alternate transitions for variety
            trans_options = [TransitionType.CROSSFADE, TransitionType.WHIP_PAN, TransitionType.MATCH_CUT]
            trans_in = trans_options[index % len(trans_options)]

        # Speed ramps for action clips
        speed = 1.0
        if "action" in clip.path.lower() or "energy" in clip.path.lower():
            speed = 1.0

        # Color grade based on mood
        color = "cinematic"
        if "rain" in clip.path.lower() or "forest" in clip.path.lower():
            color = "cold"
        elif "energy" in clip.path.lower() or "burst" in clip.path.lower():
            color = "action"
        elif "dialogue" in clip.path.lower():
            color = "dramatic"

        return EditDecision(
            clip_index=index,
            transition_in=trans_in,
            transition_out=TransitionType.CUT if index < total - 1 else TransitionType.DIP_BLACK,
            transition_duration=0.5 if index > 0 else 0.0,
            speed=speed,
            color_grade=color,
            volume=1.0,
            emotional_beat="tension" if index < total // 2 else "resolution",
            pacing_note="build" if index < total - 1 else "resolve",
        )

    def render_clip(self, clip: ClipEdit, decision: EditDecision, output_path: str) -> str:
        """Apply edits to a single clip."""
        video_filters = []
        audio_filters = []
        
        # Speed
        if decision.speed != 1.0:
            video_filters.append(f"setpts={1/decision.speed}*PTS")
            audio_filters.append(f"atempo={decision.speed}")

        # Color grade (video only)
        if decision.color_grade in self.COLOR_GRADES:
            video_filters.append(self.COLOR_GRADES[decision.color_grade])

        # Fade in/out (both video and audio)
        if decision.transition_in == TransitionType.CROSSFADE and decision.clip_index > 0:
            video_filters.append(f"fade=t=in:st=0:d={decision.transition_duration}")
            audio_filters.append(f"afade=t=in:st=0:d={decision.transition_duration}")
        if decision.transition_out == TransitionType.DIP_BLACK:
            duration = clip.duration / decision.speed
            video_filters.append(f"fade=t=out:st={duration - decision.transition_duration}:d={decision.transition_duration}")
            audio_filters.append(f"afade=t=out:st={duration - decision.transition_duration}:d={decision.transition_duration}")

        cmd = ["ffmpeg", "-y", "-i", clip.path]
        
        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])
        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])
        
        cmd.extend([
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            output_path
        ])

        subprocess.run(cmd, capture_output=True)
        return output_path

    def assemble(self, clips: list[ClipEdit], output_path: str, decisions: list[EditDecision] | None = None) -> str:
        """Assemble clips with transitions into final output."""
        if not decisions:
            decisions = self.analyze_and_edit(clips)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Render each clip with edits
            rendered = []
            for i, (clip, decision) in enumerate(zip(clips, decisions)):
                out = os.path.join(tmpdir, f"clip_{i:03d}.mp4")
                self.render_clip(clip, decision, out)
                rendered.append(out)

            # Create concat file
            concat_file = os.path.join(tmpdir, "concat.txt")
            with open(concat_file, "w") as f:
                for path in rendered:
                    f.write(f"file '{path}'\n")

            # Final assembly
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                output_path
            ]
            subprocess.run(cmd, capture_output=True)

        return output_path


def get_clip_info(path: str) -> dict:
    """Get clip duration and stream info."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)


def create_montage(input_paths: list[str], output_path: str) -> str:
    """Create a creative montage from input clips."""
    editor = CreativeEditor()
    
    clips = []
    for path in input_paths:
        info = get_clip_info(path)
        duration = float(info["format"]["duration"])
        clips.append(ClipEdit(path=path, duration=duration))

    decisions = editor.analyze_and_edit(clips)
    
    print("Edit decisions:")
    for d in decisions:
        print(f"  Clip {d.clip_index}: {d.transition_in.value} in, {d.transition_out.value} out, "
              f"grade={d.color_grade}, beat={d.emotional_beat}")

    return editor.assemble(clips, output_path, decisions)


if __name__ == "__main__":
    import sys
    
    workspace = r"C:\Users\vm004458\Documents\supercool\workspace"
    clips = [
        os.path.join(workspace, "shot1_energy_burst.mp4"),
        os.path.join(workspace, "shot5_final.mp4"),
    ]
    
    output = os.path.join(workspace, "montage_creative.mp4")
    result = create_montage(clips, output)
    print(f"\nOutput: {result}")
