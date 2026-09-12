use std::fs;
use std::process::Command;
use tokio::task;

pub async fn concat_clips(clips: &[String], output: &str, working_dir: &str) -> Result<(), String> {
    let clips = clips.to_vec();
    let output = output.to_string();
    let working_dir = working_dir.to_string();
    
    task::spawn_blocking(move || {
        let clips_file = format!("{}/clips.txt", working_dir);
        let mut content = String::new();
        for clip in &clips {
            let clip_path = if clip.starts_with('/') {
                clip.clone()
            } else {
                format!("{}/{}", working_dir, clip)
            };
            content.push_str(&format!("file '{}'\n", clip_path));
        }
        
        fs::write(&clips_file, content).map_err(|e| e.to_string())?;
        
        let output_path = if output.starts_with('/') {
            output
        } else {
            format!("{}/{}", working_dir, output)
        };
        
        let status = Command::new("ffmpeg")
            .args(&[
                "-f", "concat",
                "-safe", "0",
                "-i", &clips_file,
                "-c", "copy",
                &output_path,
            ])
            .status()
            .map_err(|e| e.to_string())?;
        
        if status.success() {
            Ok(())
        } else {
            Err("FFmpeg concat failed".to_string())
        }
    })
    .await
    .map_err(|e| e.to_string())?
}