"""Director AI - Intelligent creative direction, pacing, and story sense."""

import json
from dataclasses import dataclass, field
from enum import Enum

from app.services.video_analyzer import video_analyzer


class EmotionalBeat(Enum):
    TENSION_BUILD = "tension_build"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    QUIET_MOMENT = "quiet_moment"
    ACTION = "action"
    DIALOGUE = "dialogue"


class PacingType(Enum):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    VARIABLE = "variable"


@dataclass
class ShotAnalysis:
    """Analysis of a single shot."""
    shot_id: str
    description: str
    duration: float
    emotional_beat: EmotionalBeat
    pacing: PacingType
    camera_movement: str
    dialogue_present: bool
    action_level: float  # 0.0 calm, 1.0 high action
    suggested_transitions: list[str] = field(default_factory=list)
    audio_notes: str = ""
    color_mood: str = "neutral"


@dataclass
class StoryArc:
    """Complete story arc analysis."""
    shots: list[ShotAnalysis]
    overall_mood: str
    pacing_curve: list[float]  # 0.0-1.0 intensity per shot
    emotional_peaks: list[int]  # indices of emotional peaks
    suggested_music_crescendo: bool


class DirectorAI:
    """AI Director that makes creative decisions about pacing, emotion, and story."""

    def __init__(self):
        self.use_video_analysis = video_analyzer.is_available()

    async def analyze_scene_async(
        self, shots: list[dict], scene_context: str = ""
    ) -> StoryArc:
        """Analyze a scene with NEMOTRON intelligence (async)."""
        analyses = []

        for i, shot in enumerate(shots):
            # Use NEMOTRON analysis if available
            nemotron_analysis = None
            if self.use_video_analysis:
                nemotron_analysis = await video_analyzer.analyze_shot(
                    shot, scene_context
                )
                print(f"[NEMOTRON] Shot {i}: emotion={nemotron_analysis['emotion']}, "
                      f"action={nemotron_analysis['action_level']:.0%}, "
                      f"grade={nemotron_analysis['grade']}")

            analysis = self._analyze_shot(shot, i, len(shots), scene_context, nemotron_analysis)
            analyses.append(analysis)

        return self._build_story_arc(analyses, scene_context)

    def analyze_scene(self, shots: list[dict], scene_context: str = "") -> StoryArc:
        """Analyze a scene and create a story arc."""
        analyses = []
        
        for i, shot in enumerate(shots):
            analysis = self._analyze_shot(shot, i, len(shots), scene_context)
            analyses.append(analysis)

        # Determine overall arc
        pacing_curve = [s.action_level for s in analyses]
        emotional_peaks = [
            i for i, s in enumerate(analyses) 
            if s.emotional_beat in (EmotionalBeat.CLIMAX, EmotionalBeat.ACTION)
        ]

        # Overall mood from context
        context_lower = scene_context.lower()
        if "combat" in context_lower or "fight" in context_lower:
            overall_mood = "intense"
        elif "dialogue" in context_lower or "emotional" in context_lower:
            overall_mood = "dramatic"
        else:
            overall_mood = "cinematic"

        # Determine if music should build to climax
        has_build = any(s.emotional_beat == EmotionalBeat.TENSION_BUILD for s in analyses)
        has_climax = EmotionalBeat.CLIMAX in [s.emotional_beat for s in analyses]
        suggest_crescendo = has_build and has_climax

        return StoryArc(
            shots=analyses,
            overall_mood=overall_mood,
            pacing_curve=pacing_curve,
            emotional_peaks=emotional_peaks,
            suggested_music_crescendo=suggest_crescendo,
        )

    def _analyze_shot(
        self, shot: dict, index: int, total: int, context: str,
        video_analysis: dict | None = None
    ) -> ShotAnalysis:
        """Analyze individual shot characteristics, enhanced by video analysis."""
        desc = shot.get("prompt_text", "").lower()
        duration = shot.get("duration", 10.0)

        # If we have video analysis, use it as primary source
        if video_analysis:
            return self._analyze_from_video(
                shot, index, total, context, video_analysis
            )

        # Fallback to text-based analysis
        return self._analyze_from_text(shot, index, total, context)

    def _analyze_from_video(
        self, shot: dict, index: int, total: int, context: str, va: dict
    ) -> ShotAnalysis:
        """Create analysis from NEMOTRON analysis results."""
        # Map emotion to EmotionalBeat
        emotion_map = {
            "tense": EmotionalBeat.TENSION_BUILD,
            "dramatic": EmotionalBeat.DIALOGUE,
            "action": EmotionalBeat.ACTION,
            "calm": EmotionalBeat.QUIET_MOMENT,
            "romantic": EmotionalBeat.QUIET_MOMENT,
            "mysterious": EmotionalBeat.TENSION_BUILD,
        }
        beat = emotion_map.get(va["emotion"], EmotionalBeat.TENSION_BUILD)

        # Override for first/last shots
        if index == 0:
            beat = EmotionalBeat.TENSION_BUILD
        elif index == total - 1:
            beat = EmotionalBeat.RESOLUTION

        # Map camera movement
        camera_map = {
            "static": "static",
            "dynamic": "dynamic",
            "close-up": "static_close",
            "tracking": "tracking",
        }
        camera = camera_map.get(va["camera"], "static")

        # Pacing from action level
        if va["action_level"] > 0.7:
            pacing = PacingType.FAST
        elif va["action_level"] < 0.3:
            pacing = PacingType.SLOW
        else:
            pacing = PacingType.MEDIUM

        # Transitions from NEMOTRON analysis
        transitions = va.get("transitions", ["cut"])
        if not transitions:
            transitions = ["cut"]

        return ShotAnalysis(
            shot_id=shot.get("id", ""),
            description=shot.get("prompt_text", ""),
            duration=shot.get("duration", 10.0),
            emotional_beat=beat,
            pacing=pacing,
            camera_movement=camera,
            dialogue_present=va.get("dialogue", False),
            action_level=va.get("action_level", 0.5),
            suggested_transitions=transitions,
            audio_notes=va.get("audio", ""),
            color_mood=va.get("grade", "cinematic"),
        )

    def _analyze_from_text(self, shot: dict, index: int, total: int, context: str) -> ShotAnalysis:
        """Fallback: analyze from text description only."""
        desc = shot.get("prompt_text", "").lower()
        duration = shot.get("duration", 10.0)

        if index == 0:
            beat = EmotionalBeat.TENSION_BUILD
        elif index == total - 1:
            beat = EmotionalBeat.RESOLUTION
        elif "dialogue" in desc or "speak" in desc or "voice" in desc:
            beat = EmotionalBeat.DIALOGUE
        elif "slash" in desc or "strike" in desc or "draw" in desc:
            beat = EmotionalBeat.CLIMAX
        elif "land" in desc or "crouch" in desc:
            beat = EmotionalBeat.ACTION
        else:
            beat = EmotionalBeat.TENSION_BUILD

        if any(w in desc for w in ["slow", "close-up", "profile", "focus"]):
            pacing = PacingType.SLOW
        elif any(w in desc for w in ["fast", "rapid", "whip", "plummet"]):
            pacing = PacingType.FAST
        else:
            pacing = PacingType.MEDIUM

        action_keywords = ["slash", "strike", "draw", "plummet", "descent", "landing", "shears"]
        action_count = sum(1 for kw in action_keywords if kw in desc)
        action_level = min(1.0, action_count * 0.25)

        camera = "static"
        if "push" in desc or "track" in desc or "plunge" in desc:
            camera = "dynamic"
        elif "close-up" in desc:
            camera = "static_close"
        elif "over-the-shoulder" in desc:
            camera = "over_shoulder"

        dialogue = any(w in desc for w in ["dialogue", "speak", "voice", "lips articulate"])

        transitions = []
        if index > 0:
            if pacing == PacingType.FAST:
                transitions.append("whip_pan")
            elif dialogue:
                transitions.append("crossfade")
            else:
                transitions.append("match_cut")

        color_mood = "cinematic"
        if "rain" in context.lower() or "dusk" in context.lower():
            color_mood = "cold"
        elif action_level > 0.5:
            color_mood = "action"
        elif dialogue:
            color_mood = "dramatic"

        audio_notes = ""
        if dialogue:
            audio_notes = "Prioritize dialogue clarity, duck background"
        elif action_level > 0.5:
            audio_notes = "Emphasize SFX, impact sounds"
        else:
            audio_notes = "Ambient, minimal"

        return ShotAnalysis(
            shot_id=shot.get("id", ""),
            description=shot.get("prompt_text", ""),
            duration=duration,
            emotional_beat=beat,
            pacing=pacing,
            camera_movement=camera,
            dialogue_present=dialogue,
            action_level=action_level,
            suggested_transitions=transitions,
            audio_notes=audio_notes,
            color_mood=color_mood,
        )

    def _build_story_arc(self, analyses: list[ShotAnalysis], scene_context: str) -> StoryArc:
        """Build story arc from shot analyses."""
        pacing_curve = [s.action_level for s in analyses]
        emotional_peaks = [
            i for i, s in enumerate(analyses)
            if s.emotional_beat in (EmotionalBeat.CLIMAX, EmotionalBeat.ACTION)
        ]

        context_lower = scene_context.lower()
        if "combat" in context_lower or "fight" in context_lower:
            overall_mood = "intense"
        elif "dialogue" in context_lower or "emotional" in context_lower:
            overall_mood = "dramatic"
        else:
            overall_mood = "cinematic"

        has_build = any(s.emotional_beat == EmotionalBeat.TENSION_BUILD for s in analyses)
        has_climax = EmotionalBeat.CLIMAX in [s.emotional_beat for s in analyses]
        suggest_crescendo = has_build and has_climax

        return StoryArc(
            shots=analyses,
            overall_mood=overall_mood,
            pacing_curve=pacing_curve,
            emotional_peaks=emotional_peaks,
            suggested_music_crescendo=suggest_crescendo,
        )

    def generate_edit_plan(self, story_arc: StoryArc) -> dict:
        """Generate a complete edit plan from story arc analysis."""
        plan = {
            "overall_mood": story_arc.overall_mood,
            "music_crescendo": story_arc.suggested_music_crescendo,
            "clips": [],
        }

        for i, shot in enumerate(story_arc.shots):
            clip_plan = {
                "shot_index": i,
                "shot_id": shot.shot_id,
                "emotional_beat": shot.emotional_beat.value,
                "transition": shot.suggested_transitions[0] if shot.suggested_transitions else "cut",
                "transition_duration": 0.5 if shot.pacing != PacingType.FAST else 0.3,
                "color_grade": shot.color_mood,
                "speed": 1.0,
                "volume": 0.8 if shot.dialogue_present else 1.0,
                "audio_layer": "dialogue" if shot.dialogue_present else "ambience",
                "audio_notes": shot.audio_notes,
            }
            plan["clips"].append(clip_plan)

        return plan

    def get_summary(self, story_arc: StoryArc) -> str:
        """Generate human-readable summary of the edit."""
        lines = [
            f"=== DIRECTOR'S CUT ===",
            f"Mood: {story_arc.overall_mood}",
            f"Shots: {len(story_arc.shots)}",
            f"Music Crescendo: {'Yes' if story_arc.suggested_music_crescendo else 'No'}",
            "",
            "--- Shot Breakdown ---",
        ]
        
        for i, shot in enumerate(story_arc.shots):
            lines.append(
                f"  {i+1}. [{shot.emotional_beat.value}] {shot.pacing.value} pace | "
                f"Action: {shot.action_level:.0%} | {shot.color_mood} | {shot.audio_notes}"
            )

        return "\n".join(lines)


if __name__ == "__main__":
    director = DirectorAI()

    shots = [
        {"id": "1", "prompt_text": "Vertical camera plunge tracking Sasuke plummeting through canopy. Right hand grips blade.", "duration": 10},
        {"id": "2", "prompt_text": "Sasuke draws sword in crescent arc with electrical arcs. Shears through cables.", "duration": 10},
        {"id": "3", "prompt_text": "Over-shoulder MCU. Sasuke extends Kusanagi toward Boruto. Eye contact.", "duration": 10},
        {"id": "4", "prompt_text": "Close-up profile. Dialogue: speaking with gravitas.", "duration": 10},
        {"id": "5", "prompt_text": "Macro push toward headband. Water running across steel.", "duration": 10},
    ]

    context = "Dense rainforest canopy, dusk, heavy rain, combat rescue scene"
    
    arc = director.analyze_scene(shots, context)
    print(director.get_summary(arc))
    
    plan = director.generate_edit_plan(arc)
    print("\n--- Edit Plan ---")
    print(json.dumps(plan, indent=2))
