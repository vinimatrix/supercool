"""Creative Pipeline - Full AI-powered creative editing pipeline."""

import os
import json
import asyncio
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.services.director_ai import DirectorAI, StoryArc
from app.services.creative_editor import CreativeEditor, ClipEdit, TransitionType
from app.services.audio_engine import AudioEngine, AudioTrack, SoundLayer

BASE_DIR = Path(__file__).resolve().parent.parent.parent


@dataclass
class PipelineConfig:
    """Configuration for the creative pipeline."""
    workspace: str
    output_name: str = "final_render"
    scene_context: str = ""
    master_volume: float = 1.0
    enable_audio: bool = True
    enable_color: bool = True
    enable_transitions: bool = True


class CreativePipeline:
    """Full AI-powered creative pipeline that takes raw clips and produces a finished edit."""

    def __init__(self):
        self.director = DirectorAI()
        self.editor = CreativeEditor()
        self.audio = AudioEngine()

    def run(self, clip_paths: list[str], config: PipelineConfig) -> dict:
        """Run the full creative pipeline.
        
        Returns dict with output paths and edit summary.
        """
        print("=" * 50)
        print("CREATIVE PIPELINE - Starting")
        print("=" * 50)

        # Step 1: Director analyzes the scene (with video understanding if available)
        print("\n[1/5] Director AI analyzing scene...")
        if self.director.use_video_analysis:
            print("  [Video Understanding: ENABLED via NVIDIA NIM]")

        shots = []
        for i, path in enumerate(clip_paths):
            info = self._get_clip_info(path)
            shots.append({
                "id": str(i),
                "prompt_text": os.path.basename(path),
                "duration": float(info["format"]["duration"]),
                "video_path": path,  # Pass video path for analysis
            })

        # Use async analysis if video understanding is enabled
        if self.director.use_video_analysis:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        story_arc = pool.submit(
                            asyncio.run,
                            self.director.analyze_scene_async(shots, config.scene_context)
                        ).result()
                else:
                    story_arc = loop.run_until_complete(
                        self.director.analyze_scene_async(shots, config.scene_context)
                    )
            except RuntimeError:
                story_arc = asyncio.run(
                    self.director.analyze_scene_async(shots, config.scene_context)
                )
        else:
            story_arc = self.director.analyze_scene(shots, config.scene_context)
        print(self.director.get_summary(story_arc))

        # Step 2: Generate edit plan
        print("\n[2/5] Generating edit plan...")
        edit_plan = self.director.generate_edit_plan(story_arc)

        # Step 3: Editor processes clips
        print("\n[3/5] Creative Editor processing clips...")
        clips = []
        for i, (path, plan) in enumerate(zip(clip_paths, edit_plan["clips"])):
            info = self._get_clip_info(path)
            clips.append(ClipEdit(
                path=path,
                duration=float(info["format"]["duration"]),
                transition_in=TransitionType(plan["transition"]),
                transition_duration=plan["transition_duration"],
                speed=plan["speed"],
                color_grade=plan["color_grade"],
                volume=plan["volume"],
            ))

        # Step 4: Audio design
        output_dir = str(BASE_DIR / "workspace" / "pipeline_output")
        os.makedirs(output_dir, exist_ok=True)

        if config.enable_audio:
            print("\n[4/5] Audio Engine designing sound...")
            
            total_duration = sum(c.duration for c in clips)
            
            # Generate audio elements
            ambience_path = os.path.join(output_dir, "ambience.m4a")
            tension_path = os.path.join(output_dir, "tension.m4a")

            sound_design = self.audio.analyze_sound_design(
                clip_paths[0], config.scene_context
            )
            print(f"  Ambience: {sound_design.ambience} | Mood: {sound_design.mood}")

            self.audio.generate_ambience(
                total_duration, sound_design.ambience, ambience_path
            )
            if story_arc.suggested_music_crescendo:
                self.audio.generate_tension_bed(total_duration, tension_path)
        else:
            print("\n[4/5] Audio disabled, skipping...")

        # Step 5: Final assembly
        print("\n[5/5] Assembling final output...")
        video_output = os.path.join(output_dir, f"{config.output_name}_video.mp4")
        final_output = os.path.join(output_dir, f"{config.output_name}_final.mp4")

        # Render video with edits
        self.editor.assemble(clips, video_output)

        # Mix audio
        if config.enable_audio:
            print("  Mixing audio tracks...")
            tracks = [
                AudioTrack(path=video_output, layer=SoundLayer.DIALOGUE, volume=1.0),
                AudioTrack(path=ambience_path, layer=SoundLayer.AMBIENCE, volume=0.3),
            ]
            if story_arc.suggested_music_crescendo and os.path.exists(tension_path):
                tracks.append(
                    AudioTrack(path=tension_path, layer=SoundLayer.MUSIC, volume=0.4)
                )
            self.audio.mix_tracks(tracks, final_output, config.master_volume)
        else:
            import shutil
            shutil.copy2(video_output, final_output)

        # Summary
        result = {
            "final_output": final_output,
            "video_only": video_output,
            "duration": sum(c.duration for c in clips),
            "shots": len(clip_paths),
            "mood": story_arc.overall_mood,
            "music_crescendo": story_arc.suggested_music_crescendo,
            "edit_plan": edit_plan,
        }

        print("\n" + "=" * 50)
        print("CREATIVE PIPELINE - Complete")
        print(f"Output: {final_output}")
        print(f"Duration: {result['duration']:.1f}s | Shots: {result['shots']} | Mood: {result['mood']}")
        print("=" * 50)

        return result

    def _get_clip_info(self, path: str) -> dict:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)


if __name__ == "__main__":
    workspace = r"C:\Users\vm004458\Documents\supercool\workspace"

    clips = [
        os.path.join(workspace, "shot1_energy_burst.mp4"),
        os.path.join(workspace, "shot5_final.mp4"),
    ]

    config = PipelineConfig(
        workspace=workspace,
        output_name="rescue_scene",
        scene_context="Dense rainforest canopy, dusk, heavy rain, combat rescue, sword draw, dramatic handoff, dialogue",
    )

    pipeline = CreativePipeline()
    result = pipeline.run(clips, config)
    print(json.dumps({k: v for k, v in result.items() if k != "edit_plan"}, indent=2))
