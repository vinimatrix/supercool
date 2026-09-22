fn main() {
    let config = cbindgen::Config::from_file("cbindgen.toml").unwrap_or_default();
    cbindgen::Builder::new()
        .with_crate(".")
        .with_config(config)
        .generate()
        .expect("Unable to generate C bindings")
        .write_to_file("drift_core.h");
}
