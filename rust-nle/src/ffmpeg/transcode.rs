use std::process::Command;
use tokio::task;

pub async fn transcode_to_24fps(input: &str, output: &str, fps: u32) -> Result<(), String> {
    let input = input.to_string();
    let output = output.to_string();
    
    task::spawn_blocking(move || {
        let vf = format!("fps=fps={}", fps);
        
        let status = Command::new("ffmpeg")
            .args(&[
                "-i", &input,
                "-vf", &vf,
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "medium",
                "-c:a", "copy",
                &output,
            ])
            .status()
            .map_err(|e| e.to_string())?;
        
        if status.success() {
            Ok(())
        } else {
            Err("FFmpeg transcode failed".to_string())
        }
    })
    .await
    .map_err(|e| e.to_string())?
}