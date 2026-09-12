use crate::ffmpeg;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct Scene {
    pub clips: Vec<String>,
    pub dialogue: Option<String>,
    pub music: Option<String>,
}

pub async fn run_pipeline(scenes: &[Scene], output: &str, working_dir: &str, fps: u32) -> Result<(), String> {
    let mut all_clips = Vec::new();
    
    for (i, scene) in scenes.iter().enumerate() {
        let scene_video = format!("scene_{}_video.mp4", i);
        
        if scene.clips.len() > 1 {
            ffmpeg::concat::concat_clips(&scene.clips, &scene_video, working_dir).await?;
        } else if scene.clips.len() == 1 {
            let src = if scene.clips[0].starts_with('/') {
                scene.clips[0].clone()
            } else {
                format!("{}/{}", working_dir, scene.clips[0])
            };
            let dest = format!("{}/{}", working_dir, scene_video);
            std::fs::copy(&src, &dest).map_err(|e| e.to_string())?;
        }
        
        let scene_transcoded = format!("scene_{}_transcoded.mp4", i);
        ffmpeg::transcode::transcode_to_24fps(
            &format!("{}/{}", working_dir, scene_video),
            &format!("{}/{}", working_dir, scene_transcoded),
            fps,
        ).await?;
        
        if let (Some(dialogue), Some(music)) = (&scene.dialogue, &scene.music) {
            let scene_audio = format!("scene_{}_mixed.m4a", i);
            ffmpeg::audio::mix_audio(dialogue, music, &scene_audio, true).await?;
            
            let scene_final = format!("scene_{}_final.mp4", i);
            let status = std::process::Command::new("ffmpeg")
                .args(&[
                    "-i", &format!("{}/{}", working_dir, scene_transcoded),
                    "-i", &format!("{}/{}", working_dir, scene_audio),
                    "-c:v", "copy",
                    "-c:a", "copy",
                    "-map", "0:v",
                    "-map", "1:a",
                    &format!("{}/{}", working_dir, scene_final),
                ])
                .status()
                .map_err(|e| e.to_string())?;
            
            if !status.success() {
                return Err("FFmpeg merge failed".to_string());
            }
            
            all_clips.push(format!("{}/{}", working_dir, scene_final));
        } else {
            all_clips.push(format!("{}/{}", working_dir, scene_transcoded));
        }
    }
    
    if all_clips.len() > 1 {
        ffmpeg::concat::concat_clips(&all_clips, output, working_dir).await?;
    } else if all_clips.len() == 1 {
        let dest = if output.starts_with('/') {
            output.to_string()
        } else {
            format!("{}/{}", working_dir, output)
        };
        std::fs::copy(&all_clips[0], &dest).map_err(|e| e.to_string())?;
    }
    
    Ok(())
}