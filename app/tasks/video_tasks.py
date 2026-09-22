from celery import shared_task
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="video.process_shoot")
def process_shoot(self, shoot_id: str, scene_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single shoot through the production pipeline.
    
    Args:
        shoot_id: Shoot identifier
        scene_data: Scene context data
        
    Returns:
        Processing result
    """
    logger.info(f"Processing shoot {shoot_id}")
    
    # Update task state
    self.update_state(state="PROCESSING", meta={"shoot_id": shoot_id})
    
    # Import services here to avoid circular imports
    from app.services.cosyvoice_client import CosyVoiceClient, VoiceProfile
    from app.services.musetalk_client import MuseTalkClient
    from app.services.qa_director import QADirector
    
    # Initialize services
    cosyvoice = CosyVoiceClient()
    musetalk = MuseTalkClient()
    qa_director = QADirector()
    
    result = {
        "shoot_id": shoot_id,
        "status": "processing",
        "steps": []
    }
    
    try:
        # Step 1: Generate dialogue audio
        if scene_data.get("dialogue_script"):
            self.update_state(state="GENERATING_AUDIO", meta={"shoot_id": shoot_id})
            profile = VoiceProfile(
                name="character",
                language=scene_data.get("language", "es"),
                emotion=scene_data.get("mood", "neutral")
            )
            audio_path = cosyvoice.synthesize(scene_data["dialogue_script"], profile)
            result["audio_path"] = audio_path
            result["steps"].append("audio_generated")
        
        # Step 2: Apply lip-sync
        if scene_data.get("video_path") and result.get("audio_path"):
            self.update_state(state="APPLYING_LIPSYNC", meta={"shoot_id": shoot_id})
            lipsync_path = musetalk.process_dialogue(
                scene_data["video_path"],
                result["audio_path"],
                emotion=scene_data.get("mood", "neutral")
            )
            result["video_path"] = lipsync_path
            result["steps"].append("lipsync_applied")
        
        # Step 3: QA evaluation
        if result.get("video_path"):
            self.update_state(state="EVALUATING_QA", meta={"shoot_id": shoot_id})
            qa_result = qa_director.evaluate_shoot(
                shoot_id=shoot_id,
                video_path=result["video_path"],
                scene_context=scene_data
            )
            result["qa_status"] = qa_result.status
            result["clip_score"] = qa_result.clip_score
            result["qwen_diagnosis"] = qa_result.qwen_diagnosis
            result["steps"].append("qa_evaluated")
        
        result["status"] = "completed"
        
    except Exception as e:
        logger.error(f"Error processing shoot {shoot_id}: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result


@shared_task(bind=True, name="video.render_scene")
def render_scene(self, scene_id: str, shots_data: list) -> Dict[str, Any]:
    """Render a complete scene with all shots.
    
    Args:
        scene_id: Scene identifier
        shots_data: List of shot data dictionaries
        
    Returns:
        Rendering result
    """
    logger.info(f"Rendering scene {scene_id} with {len(shots_data)} shots")
    
    self.update_state(state="RENDERING", meta={"scene_id": scene_id})
    
    from app.services.production_pipeline import ProductionPipeline
    
    pipeline = ProductionPipeline()
    
    result = {
        "scene_id": scene_id,
        "status": "rendering",
        "shots_total": len(shots_data),
        "shots_completed": 0
    }
    
    try:
        # Process each shot
        for i, shot_data in enumerate(shots_data):
            self.update_state(
                state="PROCESSING_SHOT",
                meta={"scene_id": scene_id, "shot_index": i + 1}
            )
            
            # Process shoot
            shoot_result = process_shoot.delay(
                shoot_id=shot_data.get("shoot_id"),
                scene_data=shot_data.get("scene_data", {})
            )
            
            # Wait for result (in production, this would be async)
            shot_result.get(timeout=3600)
            
            result["shots_completed"] = i + 1
        
        result["status"] = "completed"
        
    except Exception as e:
        logger.error(f"Error rendering scene {scene_id}: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result


@shared_task(name="video.export_master")
def export_master(scene_id: str, output_format: str = "4k") -> Dict[str, Any]:
    """Export final master video.
    
    Args:
        scene_id: Scene identifier
        output_format: Output format (4k, 1080p, 720p)
        
    Returns:
        Export result
    """
    logger.info(f"Exporting master for scene {scene_id} in {output_format}")
    
    result = {
        "scene_id": scene_id,
        "output_format": output_format,
        "status": "exporting"
    }
    
    try:
        # In production, this would use DaVinci MCP or FFmpeg
        import subprocess
        
        output_path = f"./workspace/output/scene_{scene_id}_{output_format}.mp4"
        
        # Placeholder export command
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "testsrc=duration=10:size=1920x1080:rate=24",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        
        result["output_path"] = output_path
        result["status"] = "completed"
        
    except Exception as e:
        logger.error(f"Error exporting master: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result
