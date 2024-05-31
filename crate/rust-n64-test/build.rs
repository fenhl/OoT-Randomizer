use std::env;

fn main() -> Result<(), cbindgen::Error> {
    cbindgen::Builder::new()
        .with_crate(env::var_os("CARGO_MANIFEST_DIR").unwrap())
        .with_language(cbindgen::Language::C)
        .generate()?
        .write_to_file("../../ASM/c/rs.h");
    Ok(())
}
