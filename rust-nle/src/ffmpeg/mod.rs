pub mod audio;
pub mod concat;
pub mod transcode;

use std::process::Command;

pub fn check_ffmpeg_available() -> bool {
    Command::new("ffmpeg")
        .arg("-version")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}