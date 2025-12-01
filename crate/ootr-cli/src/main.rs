#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

use {
    std::path::{
        Path,
        PathBuf,
    },
    crossterm::tty::IsTty as _,
    pyo3::{
        prelude::*,
        types::PyDict,
    },
    tokio::io::{
        AsyncReadExt as _,
        stdout,
    },
    tokio_util::either::Either,
    wheel::{
        fs::{
            self,
            File,
        },
        traits::IoResultExt as _,
    },
    ootr_common::patch,
};

#[derive(Default, Clone, Copy, clap::ValueEnum)]
enum LogLevel {
    Error,
    Warning,
    #[default]
    Info,
    Debug,
}

impl LogLevel {
    fn try_into_py<'p>(&self, py: Python<'p>) -> PyResult<Bound<'p, PyAny>> {
        let logging = py.import("logging")?;
        match self {
            Self::Error => logging.getattr("ERROR"),
            Self::Warning => logging.getattr("WARNING"),
            Self::Info => logging.getattr("INFO"),
            Self::Debug => logging.getattr("DEBUG"),
        }
    }
}

#[derive(clap::Parser)]
#[clap(version)]
struct Args {
    /// Select level of logging for output.
    #[clap(long, alias = "loglevel", value_enum, default_value_t)]
    log_level: LogLevel,
    /// Provide sharable settings using a settings string. This will override all flags that it specifies.
    #[clap(long, alias = "settings_string")]
    settings_string: Option<String>,
    /// Only convert the specified settings to a settings string. If a settings string is specified output the used settings instead.
    #[clap(long, alias = "convert_settings")]
    convert_settings: bool,
    /// Use the specified settings file to use for generation
    #[clap(long)]
    settings: Option<PathBuf>,
    /// Use the given preset for base settings. Anything defined in the --settings file or the --settings_string will override the preset.
    #[clap(long, alias = "preset", alias = "settings_preset")]
    settings_preset: Option<String>,
    /// Generate the specified seed.
    #[clap(long)]
    seed: Option<String>,
    /// Generate a log file.
    #[clap(long)]
    log: bool,
    /// Always outputs a settings.json file even when spoiler is enabled.
    #[clap(long, alias = "output_settings")]
    output_settings: bool,
    #[clap(subcommand)]
    subcommand: Option<Subcommand>,
}

#[derive(clap::Subcommand)]
enum Subcommand {
    /// Generates a ZPF patch from the specified rom file.
    DiffRom {
        /// The vanilla rom. Defaults to using a cached rom if it exists.
        #[clap(long)]
        base_rom: Option<PathBuf>,
        /// The patched rom.
        diff_rom: PathBuf,
        /// Write the ZPF file to the given path instead of standard output. If there's an existing file at that path, it will be overwritten!
        #[clap(short, long)]
        output: Option<PathBuf>,
    },
}

#[derive(Debug, thiserror::Error)]
enum Error {
    #[error(transparent)] Decompress(#[from] decompress::Error),
    #[error(transparent)] Python(#[from] PyErr),
    #[error(transparent)] Wheel(#[from] wheel::Error),
    #[error("base rom is not a valid OoT 1.0 NTSC rom")]
    BaseRom,
    #[error("base rom is an OoT PAL rom, but we need an NTSC rom")]
    PalBaseRom,
    #[error("standard output is a TTY")]
    Stdout,
}

impl<'a, 'py> From<pyo3::DowncastError<'a, 'py>> for Error {
    fn from(e: pyo3::DowncastError<'a, 'py>) -> Self {
        Self::Python(e.into())
    }
}

#[wheel::main]
async fn main(Args { log_level, settings_string, convert_settings, settings, settings_preset, seed, log, output_settings, subcommand }: Args) -> Result<i32, Error> {
    match subcommand {
        None => match Python::with_gil(|py| {
            let py_version = py.version_info();
            if py_version < (3, 9) {
                panic!("Randomizer requires at least Python 3.9 and you are using {}.{}.{}", py_version.major, py_version.minor, py_version.patch);
            }
            let sys = py.import("sys")?;
            sys.getattr("path")?.call_method1("append", (concat!(env!("CARGO_MANIFEST_DIR"), "/../.."),))?;
            let json = py.import("json")?;
            let settings_mod = py.import("Settings")?;
            let settings_base = PyDict::new(py);
            if let Some(preset_name) = settings_preset {
                if let Some(preset) = settings_mod.call_method0("get_preset_files")?.try_iter()?.filter_map(|filename| filename.map_err(Error::from).and_then(|filename| {
                    let presets = filename.extract::<&str>()?;
                    let presets = json.call_method1("loads", (std::fs::read_to_string(presets).at(presets)?,))?;
                    let presets = presets.downcast::<PyDict>()?;
                    if let Some(preset) = presets.get_item(&preset_name)? {
                        return Ok(Some(preset))
                    }
                    for preset in presets.values() {
                        if let Ok(aliases) = preset.get_item("aliases") {
                            if aliases.contains(&preset_name)? {
                                return Ok(Some(preset))
                            }
                        }
                    }
                    Ok(None)
                }).transpose()).next() {
                    settings_base.call_method1("update", (preset?,))?;
                } else {
                    eprintln!("ERROR:No preset found with name {preset_name:?}");
                    return Ok(1)
                }
            }
            if settings.as_ref().is_some_and(|settings| settings == Path::new("-")) {
                settings_base.call_method1("update", (json.call_method1("loads", (sys.getattr("stdin")?.call_method0("read")?,))?,))?;
            } else if let Some(settings_path) = settings {
                let settings = std::fs::read_to_string(&settings_path).at(settings_path)?;
                settings_base.call_method1("update", (json.call_method1("loads", (settings,))?,))?;
            }
            let settings = settings_mod.call_method1("Settings", (settings_base,))?;
            settings.setattr("output_settings", output_settings)?;
            if let Some(ref settings_string) = settings_string {
                settings.call_method1("update_with_settings_string", (settings_string,))?;
            }
            if let Some(seed) = seed {
                settings.call_method1("update_seed", (seed,))?;
                settings.setattr("custom_seed", true)?;
            }
            if convert_settings {
                if settings_string.is_some() {
                    println!("{}", json.call_method1("dumps", (settings.call_method0("to_json")?,))?);
                } else {
                    println!("{}", settings.call_method0("get_settings_string")?);
                }
                return Ok(0)
            }
            py.import("OoTRandomizer")?.call_method1("start", (settings, log_level.try_into_py(py)?, !log))?;
            Ok(0)
        }) {
            Err(Error::Python(e)) => {
                Python::with_gil(|py| e.print(py));
                Ok(1)
            }
            result => result,
        },
        Some(Subcommand::DiffRom { base_rom, diff_rom: diff_rom_path, output: out_path }) => {
            let base_rom_path = base_rom.unwrap_or_else(|| PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../../ZOOTDEC.z64")));
            let mut base_rom_file = File::open(&base_rom_path).await?;
            let mut base_rom = vec![0; 0x0200_0000];
            base_rom_file.read_exact(&mut base_rom).await.at(&base_rom_path)?;
            let crc = &base_rom[0x10..0x18];
            let base_rom = match crc {
                [0xEC, 0x70, 0x11, 0xB7, 0x76, 0x16, 0xD7, 0x2B] | // regular compressed
                [0x70, 0xEC, 0xB7, 0x11, 0x16, 0x76, 0x2B, 0xD7] => { // byteswap compressed
                    decompress::decompress(&mut base_rom)?
                }
                [0x93, 0x52, 0x2E, 0x7B, 0xE5, 0x06, 0xD4, 0x27] => { // decompressed
                    base_rom.resize(0x0400_0000, 0);
                    base_rom_file.read_exact(&mut base_rom[0x0200_0000..]).await.at(base_rom_path)?;
                    base_rom
                }
                [0x44, 0xB0, 0x69, 0xB5, 0x3C, 0x37, 0x85, 0x19] | // PAL (regular compressed)
                [0xB0, 0x44, 0xB5, 0x69, 0x37, 0x3C, 0x19, 0x85] | // PAL (byteswap compressed)
                [0xEE, 0x9D, 0x53, 0xB5, 0xBC, 0x01, 0xD0, 0x15] => return Err(Error::PalBaseRom), // PAL (decompressed)
                _ => return Err(Error::BaseRom),
            };
            let mut diff_rom = fs::read(&diff_rom_path).await?;
            let diff_rom = decompress::decompress(&mut diff_rom)?; // assuming compressed diff rom
            let patch = patch::diff_roms(&base_rom, &diff_rom);
            let output = if let Some(out_path) = &out_path {
                Either::Left(File::create(out_path).await?)
            } else {
                let stdout = stdout();
                if stdout.is_tty() { return Err(Error::Stdout) }
                Either::Right(stdout)
            };
            let res = patch.write_zpf(output).await;
            if let Some(out_path) = out_path {
                res.at(out_path)
            } else {
                res.at_unknown()
            }?;
            Ok(0)
        }
    }
}
