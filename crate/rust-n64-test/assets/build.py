import os
import subprocess

TOOLCHAIN = 'nightly-2025-05-05' # good: 2025-05-05, bad: 2025-05-06/07

try:
    subprocess.run(['rustup', 'toolchain', 'install', TOOLCHAIN], check=True)
    subprocess.run(['rustup', 'component', 'add', 'rust-src', '--toolchain', TOOLCHAIN], check=True)
except FileNotFoundError:
    # no rustup, assume Nix (uses latest nightly cargo)
    subprocess.run(
        ['cargo', 'build', '-Zbuild-std=core', '-Zbuild-std-features=compiler-builtins-mem', '-Zjson-target-spec', '--release', '--package=rust-n64-test', '--target=crate/rust-n64-test/assets/mips64-ultra64-cpu.json'],
        env={**os.environ, 'RUSTFLAGS': '-Csymbol-mangling-version=v0'}, # symbol-mangling-version (https://github.com/rust-lang/rust/issues/60705) required for armips to accept the symbols
        check=True,
    )
else:
    subprocess.run(
        ['cargo', f'+{TOOLCHAIN}', 'build', '-Zbuild-std=core', '-Zbuild-std-features=compiler-builtins-mem', '--release', '--package=rust-n64-test', '--target=crate/rust-n64-test/assets/mips64-ultra64-cpu.json'],
        env={**os.environ, 'RUSTFLAGS': '-Csymbol-mangling-version=v0'}, # symbol-mangling-version (https://github.com/rust-lang/rust/issues/60705) required for armips to accept the symbols
        check=True,
    )
