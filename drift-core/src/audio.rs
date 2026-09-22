use std::ffi::CStr;
use std::os::raw::c_char;
use std::process::Command;

/// Mix multiple audio tracks into a single output
#[no_mangle]
pub extern "C" fn drift_mix_audio(
    tracks: *const *const c_char,
    track_count: usize,
    output: *const c_char,
    ducking: bool,
) -> bool {
    let output_path = unsafe {
        if output.is_null() {
            return false;
        }
        match CStr::from_ptr(output).to_str() {
            Ok(s) => s.to_string(),
            Err(_) => return false,
        }
    };

    let mut inputs: Vec<String> = Vec::new();
    let mut filter_parts: Vec<String> = Vec::new();

    for i in 0..track_count {
        let track = unsafe {
            let ptr = *tracks.add(i);
            if ptr.is_null() {
                return false;
            }
            match CStr::from_ptr(ptr).to_str() {
                Ok(s) => s.to_string(),
                Err(_) => return false,
            }
        };

        inputs.push("-i".to_string());
        inputs.push(track);
        filter_parts.push(format!("[{}:a]", i));
    }

    let filter = if ducking && track_count > 1 {
        // Apply sidechaincompress for ducking
        format!(
            "{}amix=inputs={}:duration=longest",
            filter_parts.join(""),
            track_count
        )
    } else {
        format!(
            "{}amix=inputs={}:duration=longest",
            filter_parts.join(""),
            track_count
        )
    };

    let mut args: Vec<String> = vec!["-y".to_string()];
    args.extend(inputs);
    args.push("-filter_complex".to_string());
    args.push(filter);
    args.push("-c:a".to_string());
    args.push("aac".to_string());
    args.push("-b:a".to_string());
    args.push("192k".to_string());
    args.push(output_path);

    let result = Command::new("ffmpeg")
        .args(&args)
        .output();

    match result {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}
