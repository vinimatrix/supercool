"""Production Pipeline Orchestrator - Coordinates CosyVoice, MuseTalk, and QA Director."""

from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import subprocess
from pathlib import Path

from app.models.scene import Scene
from app.models.shot import Shot
from app.models.shoot import Shoot, ShootStatus
from app.services.cosyvoice_client import CosyVoiceClient, VoiceProfile
from app.services.musetalk_client import MuseTalkClient
from app.services.qa_director import QADirector


@dataclass
class PipelineResult:
    """Result of pipeline execution for a scene."""
    scene_id: str
    shots_processed: int
    shoots_approved: int
    shoots_rejected: int
    final_video_path: Optional[str]
    timestamp: datetime
    details: dict


class ProductionPipeline:
    """Orchestrates the production pipeline: TTS -> LipSync -> QA."""

    def __init__(self):
        self.cosyvoice = CosyVoiceClient()
        self.musetalk = MuseTalkClient()
        self.qa_director = QADirector()
        self.output_dir = Path("./workspace/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_shot(
        self,
        shot: Shot,
        scene: Scene,
        shoots: List[Shoot]
    ) -> List[Shoot]:
        """Process all shoots for a shot through the pipeline."""
        processed_shoots = []
        
        for shoot in shoots:
            # Step 1: Generate dialogue audio
            if scene.dialogue_script:
                profile = VoiceProfile(
                    name="character",
                    language="es",
                    emotion=scene.mood or "neutral"
                )
                audio_path = self.cosyvoice.synthesize(
                    scene.dialogue_script,
                    profile
                )
                shoot.audio_path = audio_path
            
            # Step 2: Apply lip-sync if video exists
            if shoot.video_path and shoot.audio_path:
                lipsync_path = self.musetalk.process_dialogue(
                    shoot.video_path,
                    shoot.audio_path,
                    emotion=scene.mood or "neutral"
                )
                shoot.video_path = lipsync_path
            
            # Step 3: QA evaluation
            if shoot.video_path:
                qa_result = self.qa_director.evaluate_shoot(
                    shoot_id=str(shoot.id),
                    video_path=shoot.video_path,
                    scene_context={
                        "location": scene.location,
                        "time_of_day": scene.time_of_day,
                        "mood": scene.mood,
                        "lighting": scene.time_of_day
                    },
                    shot_type=shot.shot_type or "CLOSE_UP"
                )
                
                shoot.clip_score = qa_result.clip_score
                shoot.qwen_diagnosis = qa_result.qwen_diagnosis
                shoot.qa_status = qa_result.status
                shoot.qa_timestamp = qa_result.timestamp
                
                if qa_result.status == "approved":
                    shoot.status = ShootStatus.APPROVED
                else:
                    shoot.status = ShootStatus.REJECTED
            
            processed_shoots.append(shoot)
        
        return processed_shoots
    
    def select_best_shoot(self, shoots: List[Shoot]) -> Optional[Shoot]:
        """Select the best approved shoot based on CLIP score."""
        approved = [s for s in shoots if s.status == ShootStatus.APPROVED]
        if not approved:
            return None
        return max(approved, key=lambda s: s.clip_score or 0)
    
    def assemble_scene(
        self,
        approved_shoots: List[Shoot],
        output_path: str
    ) -> str:
        """Assemble approved shoots into final scene."""
        # Create ffmpeg concat file
        concat_file = output_path + ".txt"
        with open(concat_file, "w") as f:
            for shoot in approved_shoots:
                if shoot.video_path:
                    f.write(f"file '{shoot.video_path}'\n")
        
        # Concatenate videos
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        
        return output_path
    
    def execute_pipeline(
        self,
        scene: Scene,
        shots: List[Shot],
        shoots_dict: Dict[str, List[Shoot]]
    ) -> PipelineResult:
        """Execute full production pipeline for a scene."""
        all_approved_shoots = []
        total_shoots = 0
        approved_count = 0
        rejected_count = 0
        
        for shot in shots:
            shoots = shoots_dict.get(str(shot.id), [])
            total_shoots += len(shoots)
            
            # Process shoots
            processed = self.process_shot(shot, scene, shoots)
            
            # Select best shoot
            best = self.select_best_shoot(processed)
            if best:
                all_approved_shoots.append(best)
                approved_count += 1
            else:
                rejected_count += 1
        
        # Assemble final video
        final_path = None
        if all_approved_shoots:
            final_path = f"./workspace/output/scene_{scene.scene_number}_final.mp4"
            self.assemble_scene(all_approved_shoots, final_path)
        
        return PipelineResult(
            scene_id=str(scene.id),
            shots_processed=len(shots),
            shoots_approved=approved_count,
            shoots_rejected=rejected_count,
            final_video_path=final_path,
            timestamp=datetime.utcnow(),
            details={
                "total_shoots": total_shoots,
                "scene_title": scene.title
            }
        )