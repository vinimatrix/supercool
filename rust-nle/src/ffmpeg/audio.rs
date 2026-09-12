use std::process::Command;
use tokio::task;

pub async fn mix_audio(dialogue: &str, music: &str, output: &str, ducking: bool) -> Result<(), String> {
    let dialogue = dialogue.to_string();
    let music = music.to_string();
    let output = output.to_string();
    
    task::spawn_blocking(move || {
        let status = if ducking {
            Command::new("ffmpeg")
                .args(&[
                    "-i", &dialogue,
                    "-i", &music,
                    "-filter_complex",
                    "[0:a][1:a]sidechaincompress=threshold=0.08:ratio=12:attack=10:release=200[ducked];[1:a][ducked]amix=inputs=2:duration=first[aout]",
                    "-map", "[aout]",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    &output,
                ])
                .status()
                .map_err(|e| e.to_string())?
        } else {
            Command::new("ffmpeg")
                .args(&[
                    "-i", &dialogue,
                    "-i", &music,
                    "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                    "-map", "[aout]",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    &output,
                ])
                .status()
                .map_err(|e| e.to_string())?
        };
        
        if status.success() {
            Ok(())
        } else {
            Err("FFmpeg audio mix failed".to_string())
        }
    })
    .await
    .map_err(|e| e.to_string())?
}