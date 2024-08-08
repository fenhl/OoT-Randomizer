How to build the tools in the `bin` directory:

# Decompress

1. On x86_64 Windows:
    1. Install [Rust](https://rust-lang.org/)
    2. `rustup target add i686-pc-windows-msvc aarch64-pc-windows-msvc`
    2. `cd bin/Decompress/src`
    5. `cargo build --release --target=x86_64-pc-windows-msvc --target=i686-pc-windows-msvc --target=aarch64-pc-windows-msvc`
    4. `cp target/x86_64-pc-windows-msvc/release/decompress-cli.exe ../Decompress.exe`
    6. `cp target/i686-pc-windows-msvc/release/decompress-cli.exe ../Decompress32.exe`
    7. `cp target/aarch64-pc-windows-msvc/release/decompress-cli.exe ../Decompress_ARM64.exe`
    8. Install Rust inside WSL
    9. `wsl rustup target add x86_64-unknown-linux-musl`
    10. `wsl cargo build --release --target=x86_64-unknown-linux-musl`
    11. `cp target/x86_64-unknown-linux-musl/release/decompress-cli ../Decompress`
2. On aarch64 macOS:
    1. Install Rust
    2. `rustup target add x86_64-apple-darwin`
    3. `cd bin/Decompress/src`
    4. `cargo build --release --target=aarch64-apple-darwin --target=x86_64-apple-darwin`
    5. `cp target/aarch64-apple-darwin/release/decompress-cli ../Decompress_ARM64.out`
    6. `cp target/x86_64-apple-darwin/release/decompress-cli ../Decompress.out`
3. On aarch64 NixOS:
    1. Start a `nix-shell` with `nativeBuildInputs = with pkgs; [ rustup ];`
    2. `rustup target add aarch64-unknown-linux-musl`
    3. `cargo build --release --target=aarch64-unknown-linux-musl`
    4. `cp target/aarch64-unknown-linux-musl/release/decompress-cli ../Decompress_ARM64`
