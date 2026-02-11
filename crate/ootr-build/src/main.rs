use {
    std::{
        collections::{
            BTreeMap,
            HashMap,
        },
        env,
        iter::{
            self,
            FusedIterator,
        },
        path::Path,
    },
    decompress::fix_crc,
    directories::UserDirs,
    futures::stream::TryStreamExt as _,
    itermore::IterArrayChunks as _,
    lazy_regex::regex_captures,
    serde::Serialize,
    tokio::{
        io::{
            AsyncBufReadExt as _,
            AsyncWriteExt as _,
            BufReader,
        },
        process::Command,
    },
    tokio_stream::wrappers::LinesStream,
    wheel::{
        fs::{
            self,
            File,
        },
        traits::{
            AsyncCommandOutputExt as _,
            IoResultExt as _,
        },
    },
};

struct UnequalChunks<'a> {
    addr: usize,
    file1: &'a [u8],
    file2: &'a [u8],
}

impl Iterator for UnequalChunks<'_> {
    type Item = (usize, Vec<u32>, Vec<u32>);

    fn next(&mut self) -> Option<Self::Item> {
        const CHUNK_SIZE: usize = 4096;

        loop {
            let chunk1 = &self.file1[..self.file1.len().min(CHUNK_SIZE)];
            let chunk2 = &self.file2[..self.file2.len().min(CHUNK_SIZE)];
            self.addr += CHUNK_SIZE;
            self.file1 = &self.file1[chunk1.len()..];
            self.file2 = &self.file2[chunk2.len()..];
            if chunk1.is_empty() {
                break None
            }
            if chunk1 != chunk2 {
                let words1 = chunk1.iter().copied().arrays().map(|x| u32::from_be_bytes(x)).collect();
                let words2 = chunk2.iter().copied().arrays().map(|x| u32::from_be_bytes(x)).collect();
                break Some((self.addr - CHUNK_SIZE, words1, words2))
            }
        }
    }
}

impl FusedIterator for UnequalChunks<'_> {}

struct SymbolData<'a> {
    sym_type: &'a str,
    address: &'a str,
    length: usize,
}

#[derive(Serialize)]
struct DataSymbol {
    address: String,
    length: usize,
}

#[derive(clap::Parser)]
#[clap(version)]
struct Args {
    /// Build Rust code called from Python without optimizations.
    #[clap(long)]
    debug: bool,
}

#[derive(Debug, thiserror::Error)]
enum Error {
    #[error(transparent)] EnvJoinPaths(#[from] env::JoinPathsError),
    #[error(transparent)] ParseInt(#[from] std::num::ParseIntError),
    #[error(transparent)] Utf8(#[from] std::string::FromUtf8Error),
    #[error(transparent)] Wheel(#[from] wheel::Error),
    #[error("roms/base.z64 should be 0x4000000 bytes (64 MiB), but yours is {:#x} bytes ({} MiB). Make sure you have an uncompressed base ROM (see https://github.com/fenhl/OoT_Decompressor).", .0, .0 / 1024_usize.pow(2))]
    BaseRomSize(usize),
}

#[wheel::main]
async fn main(Args { debug }: Args) -> Result<(), Error> {
    let root_dir = Path::new(concat!(env!("CARGO_MANIFEST_DIR"), "/../../ASM"));
    let tools_dir = root_dir.join("tools");
    // Makes it possible to use the "tools" directory as the prefix for the toolchain
    let tools_bin_dir = tools_dir.join("bin");
    // Makes it possible to copy the full toolchain prefix into the "tools" directory
    let n64_bin_dir = tools_dir.join("n64").join("bin");
    let path = env::join_paths([tools_dir, tools_bin_dir, n64_bin_dir].into_iter().chain(env::var_os("PATH").map(|path| env::split_paths(&path).collect::<Vec<_>>()).into_iter().flatten()))?;

    // Compile code

    let base_rom = fs::read(root_dir.join("roms").join("base.z64")).await?;
    let base_rom_size = base_rom.len();
    if base_rom_size != 0x0400_0000 {
        return Err(Error::BaseRomSize(base_rom_size))
    }

    Command::new("make").env("PATH", &path).current_dir(root_dir).check("make").await?;

    Command::new("armips").arg("-sym2").arg("../build/asm_symbols.txt").arg("build.asm").env("PATH", path).current_dir(root_dir.join("src")).check("armips").await?;

    let mut asm_symbols = fs::read(root_dir.join("build").join("asm_symbols.txt")).await?;
    let mut original_idx = 0;
    let mut target_idx = 0;
    while original_idx < asm_symbols.len() {
        if asm_symbols.get(original_idx..original_idx + 2).is_some_and(|slice| slice == b"\r\n") {
            asm_symbols[target_idx] = b'\n';
            original_idx += 2;
            target_idx += 1;
        } else if asm_symbols[original_idx] == 0x1a {
            original_idx += 1;
        } else {
            asm_symbols[target_idx] = asm_symbols[original_idx];
            original_idx += 1;
            target_idx += 1;
        }
    }
    asm_symbols.truncate(target_idx);
    fs::write(root_dir.join("build").join("asm_symbols.txt"), &asm_symbols).await?;

    // Parse symbols

    let mut c_sym_types = HashMap::new();

    let c_symbols_path = root_dir.join("build").join("c_symbols.txt");
    let mut c_symbols = LinesStream::new(BufReader::new(File::open(&c_symbols_path).await?).lines());
    while let Some(line) = c_symbols.try_next().await.at(&c_symbols_path)? {
        if let Some((_, sym_type, name)) = regex_captures!(r"^[0-9a-fA-F]+.*\.([^\s]+)\s+[0-9a-fA-F]+\s+([^.$][^\s]+)\s*$", &line) {
            c_sym_types.insert(name.to_owned(), if sym_type == "text" { "code" } else { "data" });
        }
    }

    let mut symbols = HashMap::new();

    let asm_symbols = String::from_utf8(asm_symbols)?;
    for line in asm_symbols.lines() {
        if let Some((address, sym_name)) = line.split_once(' ') {
            if !address.starts_with('8') { continue }
            if sym_name.starts_with(&['.', '@'][..]) { continue }
            let sym_type = c_sym_types.get(sym_name).copied().unwrap_or_else(|| if sym_name.chars().any(|c| c.is_ascii_lowercase()) { "code" } else { "data" });
            symbols.insert(sym_name, SymbolData { sym_type, address, length: 0 });
        }
    }

    // Loop through a second time, add lengths to each data symbol
    // This could probably be optimized to run in a single pass :)
    for line in asm_symbols.lines() {
        if let Some((address, sym_name)) = line.split_once(' ') {
            if sym_name.starts_with('.') {
                // split on the ':' to get the length, in hex
                let Some((_, hex_length)) = sym_name.split_once(':') else { continue };
                for sym_data in &mut symbols.values_mut() {
                    if sym_data.address == address && sym_data.sym_type == "data" {
                        sym_data.length = usize::from_str_radix(hex_length, 16)?;
                    }
                }
            }
        }
    }

    // Output symbols

    let payload_start = usize::from_str_radix(symbols["PAYLOAD_START"].address, 16)?;
    let payload_end = usize::from_str_radix(symbols["PAYLOAD_END"].address, 16)?;
    let mut data_symbols = BTreeMap::default();
    let mut patch_symbols = BTreeMap::default();
    for (name, sym) in symbols {
        if sym.sym_type == "data" {
            let addr = usize::from_str_radix(sym.address, 16)?;
            if (payload_start..payload_end).contains(&addr) {
                let addr = addr - 0x8040_0000 + 0x0348_0000;
                data_symbols.insert(name, DataSymbol {
                    address: format!("{addr:08X}"),
                    length: sym.length,
                });
            } else {
                patch_symbols.insert(name, addr);
            }
        }
    }

    fs::write_json(concat!(env!("CARGO_MANIFEST_DIR"), "/../../data/generated/symbols.json"), data_symbols).await?;

    fs::write_json(concat!(env!("CARGO_MANIFEST_DIR"), "/../../data/generated/patch_symbols.json"), patch_symbols).await?;

    let patched_rom_path = root_dir.join("roms").join("patched.z64");
    let mut patched_rom = fs::read(&patched_rom_path).await?;
    fix_crc(&mut patched_rom);
    fs::write(patched_rom_path, &patched_rom).await?;

    // Diff ROMs
    const ROM_PATCH_PATH: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/../../data/generated/rom_patch.txt");
    let mut out_f = File::create(ROM_PATCH_PATH).await?;
    for (addr, base_words, comp_words) in (UnequalChunks { addr: 0, file1: &base_rom, file2: &patched_rom }) {
        for (j, comp_word) in comp_words.into_iter().enumerate() {
            if comp_word != base_words[j] {
                out_f.write_all(format!("{:x},{comp_word:x}\n", addr + 4 * j).as_bytes()).await.at(ROM_PATCH_PATH)?;
            }
        }
    }

    // build Rust code called from Python
    let mut cargo = Command::new("cargo");
    if let Some(user_dirs) = UserDirs::new() {
        cargo.env("PATH", env::join_paths(iter::once(user_dirs.home_dir().join(".cargo").join("bin")).chain(env::var_os("PATH").map(|path| env::split_paths(&path).collect::<Vec<_>>()).into_iter().flatten()))?);
    }
    cargo.arg("build");
    if !debug {
        cargo.arg("--release");
    }
    cargo.arg("--package=ootr-python");
    cargo.current_dir(concat!(env!("CARGO_MANIFEST_DIR"), "/../.."));
    cargo.spawn().at_command("cargo build")?.check("cargo build").await?;
    #[cfg(target_os = "windows")] fs::copy(concat!(env!("CARGO_MANIFEST_DIR"), "/../../target/release/rs.dll"), concat!(env!("CARGO_MANIFEST_DIR"), "/../../rs.pyd")).await?;
    #[cfg(target_os = "linux")] fs::copy(concat!(env!("CARGO_MANIFEST_DIR"), "/../../target/release/librs.so"), concat!(env!("CARGO_MANIFEST_DIR"), "/../../rs.so")).await?;
    #[cfg(target_os = "macos")] fs::copy(concat!(env!("CARGO_MANIFEST_DIR"), "/../../target/release/librs.dylib"), concat!(env!("CARGO_MANIFEST_DIR"), "/../../rs.so")).await?;

    Ok(())
}
