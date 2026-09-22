use std::ffi::CStr;
use std::os::raw::c_char;
use std::process::Command;

/// Concatenate video clips into a single output file
#[no_mangle]
pub extern "C" fn drift_concat_clips(
    clips: *const *const c_char,
    clip_count: usize,
    output: *const c_char,
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

    let mut input_args: Vec<String> = Vec::new();

    for i in 0..clip_count {
        let clip = unsafe {
            let ptr = *clips.add(i);
            if ptr.is_null() {
                return false;
            }
            match CStr::from_ptr(ptr).to_str() {
                Ok(s) => s.to_string(),
                Err(_) => return false,
            }
        };

        // Create concat file
        input_args.push(format!("file '{}'", clip.replace('\\', "/")));
    }

    // Write concat list to temp file
    let concat_file = format!("{}.txt", output_path);
    let content = input_args.join("\n");
    if std::fs::write(&concat_file, &content).is_err() {
        return false;
    }

    let result = Command::new("ffmpeg")
        .args([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", &concat_file,
            "-c", "copy",
            &output_path,
        ])
        .output();

    // Clean up concat file
    let _ = std::fs::remove_file(&concat_file);

    match result {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}
