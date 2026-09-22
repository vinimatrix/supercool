use std::ffi::CStr;
use std::os::raw::c_char;
use std::process::Command;

/// Scene structure for pipeline
#[repr(C)]
pub struct DriftScene {
    pub clips: *const *const c_char,
    pub clip_count: usize,
    pub output: *const c_char,
}

/// Run a full render pipeline
#[no_mangle]
pub extern "C" fn drift_run_pipeline(
    scenes: *const DriftScene,
    scene_count: usize,
    output: *const c_char,
    _fps: u32,
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

    // For each scene, concatenate clips
    let mut temp_files: Vec<String> = Vec::new();

    for i in 0..scene_count {
        let scene = unsafe { &*scenes.add(i) };

        let mut scene_clips: Vec<String> = Vec::new();
        for j in 0..scene.clip_count {
            let clip = unsafe {
                let ptr = *scene.clips.add(j);
                if ptr.is_null() {
                    return false;
                }
                match CStr::from_ptr(ptr).to_str() {
                    Ok(s) => s.to_string(),
                    Err(_) => return false,
                }
            };
            scene_clips.push(clip);
        }

        if scene_clips.is_empty() {
            continue;
        }

        // Create concat list
        let concat_file = format!("{}_scene_{}.txt", output_path, i);
        let content: Vec<String> = scene_clips
            .iter()
            .map(|c| format!("file '{}'", c.replace('\\', "/")))
            .collect();

        if std::fs::write(&concat_file, &content.join("\n")).is_err() {
            return false;
        }

        let temp_output = format!("{}_scene_{}.mp4", output_path, i);

        let result = Command::new("ffmpeg")
            .args([
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", &concat_file,
                "-c", "copy",
                &temp_output,
            ])
            .output();

        let _ = std::fs::remove_file(&concat_file);

        match result {
            Ok(output) => {
                if !output.status.success() {
                    return false;
                }
            }
            Err(_) => return false,
        }

        temp_files.push(temp_output);
    }

    if temp_files.is_empty() {
        return false;
    }

    // Concatenate all scenes
    if temp_files.len() == 1 {
        let result = Command::new("ffmpeg")
            .args(["-y", "-i", &temp_files[0], "-c", "copy", &output_path])
            .output();

        let _ = std::fs::remove_file(&temp_files[0]);

        return match result {
            Ok(output) => output.status.success(),
            Err(_) => false,
        };
    }

    // Multiple scenes - concatenate them
    let concat_file = format!("{}_final.txt", output_path);
    let content: Vec<String> = temp_files
        .iter()
        .map(|f| format!("file '{}'", f.replace('\\', "/")))
        .collect();

    if std::fs::write(&concat_file, &content.join("\n")).is_err() {
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

    let _ = std::fs::remove_file(&concat_file);
    for f in &temp_files {
        let _ = std::fs::remove_file(f);
    }

    match result {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}
