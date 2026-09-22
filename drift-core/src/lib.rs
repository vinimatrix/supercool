use std::ffi::CString;
use std::os::raw::c_char;
use std::process::Command;

pub mod concat;
pub mod transcode;
pub mod audio;
pub mod pipeline;

/// Check if FFmpeg is available on the system
#[no_mangle]
pub extern "C" fn drift_check_ffmpeg() -> bool {
    Command::new("ffmpeg")
        .arg("-version")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

/// Get version string
#[no_mangle]
pub extern "C" fn drift_version() -> *mut c_char {
    let version = CString::new("0.1.0").unwrap();
    version.into_raw()
}

/// Free a string returned by drift functions
#[no_mangle]
pub extern "C" fn drift_free_string(s: *mut c_char) {
    if !s.is_null() {
        unsafe {
            let _ = CString::from_raw(s);
        }
    }
}
