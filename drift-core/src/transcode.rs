use std::ffi::CStr;
use std::os::raw::c_char;
use std::process::Command;

/// Transcode video with frame rate conversion
#[no_mangle]
pub extern "C" fn drift_transcode(
    input: *const c_char,
    output: *const c_char,
    fps: u32,
) -> bool {
    let input_path = unsafe {
        if input.is_null() {
            return false;
        }
        match CStr::from_ptr(input).to_str() {
            Ok(s) => s.to_string(),
            Err(_) => return false,
        }
    };

    let output_path = unsafe {
        if output.is_null() {
            return false;
        }
        match CStr::from_ptr(output).to_str() {
            Ok(s) => s.to_string(),
            Err(_) => return false,
        }
    };

    let result = Command::new("ffmpeg")
        .args([
            "-y",
            "-i", &input_path,
            "-filter:v", &format!("fps={}", fps),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            &output_path,
        ])
        .output();

    match result {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}
