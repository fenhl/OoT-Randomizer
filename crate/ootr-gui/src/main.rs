#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

use {
    std::{
        borrow::Cow,
        collections::{
            BTreeMap,
            BTreeSet,
            HashMap,
            HashSet,
        },
        io,
        iter,
        num::NonZero,
        path::{
            Path,
            PathBuf,
        },
        sync::Arc,
    },
    collect_mac::collect,
    enum_iterator::all,
    futures::{
        future::{
            self,
            Future,
            FutureExt as _,
        },
        stream::TryStreamExt as _,
    },
    gres::{
        Percent,
        Progress as _,
        Task as _,
    },
    iced::{
        Element,
        Length,
        Size,
        Task,
        clipboard,
        widget::*,
        window::{
            self,
            icon,
        },
    },
    if_chain::if_chain,
    ::image::ImageFormat,
    indexmap::IndexMap,
    itertools::{
        Itertools as _,
        Position,
    },
    nonempty_collections::{
        NEVec,
        NonEmptyIterator as _,
    },
    pyo3::{
        exceptions::*,
        prelude::*,
    },
    rfd::{
        AsyncFileDialog,
        AsyncMessageDialog,
    },
    serde_json::json,
    serde_json_inner as _, // `preserve_order` feature required to correctly display presets
    serenity::utils::MessageBuilder,
    smart_default::SmartDefault,
    tokio::task::spawn_blocking,
    wheel::{
        fs,
        traits::IoResultExt as _,
    },
    ootr_common::{
        Generator,
        RollError,
    },
    ootr_macros::translate,
    crate::{
        lang::Language::{
            self,
            *,
        },
        settings::ValueExt as _,
    },
};
#[cfg(target_arch = "wasm32")] use {
    std::io::{
        Cursor,
        prelude::*,
    },
    zip::ZipWriter,
};
#[cfg(not(target_arch = "wasm32"))] use {
    async_zip::{
        Compression,
        ZipEntryBuilder,
        tokio::write::ZipFileWriter,
    },
    wheel::fs::File,
};

mod lang;
mod settings;

const MAIN_WINDOW_SIZE: Size = Size { width: 754.0, height: 512.0 };
const DEFAULT_PRESET: &str = "Default / Beginner";
const CUSTOM_PRESETS_PATH: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/../../data/Presets");
const CUSTOM_PRESET_SUFFIX: &str = ".custom.json";
const PLANDO_SUFFIX: &str = ".plando.json";

fn custom_preset_path(name: &str) -> PathBuf {
    Path::new(CUSTOM_PRESETS_PATH).join(format!("{}{CUSTOM_PRESET_SUFFIX}", name.replace('/', "_")))
}

fn plando_path(name: &str) -> PathBuf {
    Path::new(CUSTOM_PRESETS_PATH).join(format!("{}{PLANDO_SUFFIX}", name.replace('/', "_")))
}

fn cmd(future: impl Future<Output = Result<Message, Error>> + Send + 'static) -> Task<Message> {
    Task::future(
        future.map(|res| res.unwrap_or_else(|e| Message::CommandError(Arc::new(e.into()))))
    )
}

#[derive(Debug, thiserror::Error)]
enum Error {
    #[error(transparent)] Iced(#[from] iced::Error),
    #[error(transparent)] Icon(#[from] icon::Error),
    #[error(transparent)] Patch(#[from] ootr_common::PatchError),
    #[error(transparent)] Python(#[from] PyErr),
    #[error(transparent)] Task(#[from] tokio::task::JoinError),
    #[error(transparent)] Wheel(#[from] wheel::Error),
    #[cfg(target_arch = "wasm32")] #[error(transparent)] Zip(#[from] zip::result::ZipError),
    #[cfg(not(target_arch = "wasm32"))] #[error(transparent)] Zip(#[from] async_zip::error::ZipError),
    #[error("Randomizer requires at least Python 3.9 and you are using {major}.{minor}.{patch}")]
    PythonVersion {
        major: u8,
        minor: u8,
        patch: u8,
    },
    #[error("integer overflow while attempting to copy preset")]
    TooManyCopies,
    #[error("support for non-UTF-8 paths not yet implemented")] //TODO
    Utf8,
}

#[derive(Debug, Clone /*TODO this requires PyO3's py-clone feature, remove by using on_press_with (requires patch to iced to remove the unconditional Clone bound) */)]
enum Message {
    AskDeletePlando(String),
    AskDeletePreset(String),
    AskSavePatches {
        window_to_close: window::Id,
        window_to_check: window::Id,
        unsaved_worlds: NEVec<NonZero<u8>>,
    },
    AskSaveSpoiler {
        window_to_close: window::Id,
        window_to_check: window::Id,
    },
    BaseRomBrowse,
    BeginRenamePlando(String),
    BeginRenamePreset(String),
    CancelRenamePresetOrPlando,
    CloseRequested(window::Id),
    CommandError(Arc<Error>),
    ConfirmRenamePresetOrPlando,
    CopyPresetOrPlando(String),
    CopyRollDebugInfo(window::Id),
    CosmeticPlandoBrowse(window::Id),
    CustomizeSettings,
    DeletePlando(String),
    DeletePreset(String),
    DismissError,
    Done {
        window: window::Id,
        seed: ootr_common::Seed,
    },
    EditPlayerNumber {
        window: window::Id,
        new_value: NonZero<u8>,
    },
    EditPreset(String),
    EditPresetSetting {
        window: window::Id,
        setting_name: String,
        new_value: settings::Value,
    },
    EditRenamePresetOrPlando(String),
    Generate,
    GenerateError {
        window: window::Id,
        settings_base: settings::Preset,
        error: Arc<RollError>,
    },
    ImportPlando(PathBuf),
    Init {
        icon: window::Icon,
        default_presets: settings::PresetsDefault,
        custom_presets: BTreeMap<String, settings::Preset>,
        plandos: BTreeSet<String>,
        settings_mapping: settings::Mapping,
    },
    MarkCompressedRomSaved {
        window: window::Id,
        player: NonZero<u8>,
    },
    MarkPatchesSaved {
        window: window::Id,
    },
    MarkPatchesSavedAndContinueClosing {
        window_to_close: window::Id,
        window_to_check: window::Id,
    },
    MarkSpoilerSaved {
        window: window::Id,
    },
    MarkSpoilerSavedAndContinueClosing {
        window_to_close: window::Id,
        window_to_check: window::Id,
    },
    Nop,
    PalRomBrowse,
    PlandoAdded {
        name: String,
    },
    PlandoBrowse,
    PlandoRenamed {
        from: String,
        to: String,
    },
    PresetCopied {
        copy_name: String,
        value: settings::Preset,
    },
    PresetRenamed {
        from: String,
        to: String,
    },
    ResetPlayerNumber(window::Id),
    RetrySeed(window::Id),
    RunGenerator {
        window: window::Id,
        generator: Arc<Generator>,
    },
    SaveCompressedRom {
        window: window::Id,
    },
    SavePatches {
        window: window::Id,
    },
    SavePatchesResponse {
        window_to_close: window::Id,
        window_to_check: window::Id,
        response: rfd::MessageDialogResult,
    },
    SaveSpoiler {
        window: window::Id,
    },
    SaveSpoilerResponse {
        window_to_close: window::Id,
        window_to_check: window::Id,
        response: rfd::MessageDialogResult,
    },
    SetBaseRomPath(PathBuf),
    SetCosmeticPlandoPath {
        window: window::Id,
        path: PathBuf,
    },
    SetLanguage(Language),
    SetPalRomPath(PathBuf),
    SetPresetOrPlando(String),
    SetSettingsTab {
        window: window::Id,
        tab_name: String,
    },
}

#[derive(SmartDefault)]
struct Gui {
    windows: HashMap<window::Id, WindowState>,
    // global/main window state
    main_view: MainWindowView,
    error: Option<Arc<Error>>,
    //TODO default to system language if possible, see https://github.com/unicode-org/icu4x/issues/3990
    language: Language,
    base_rom_path: PathBuf,
    pal_rom_path: PathBuf,
    icon: Option<window::Icon>,
    default_presets: settings::PresetsDefault,
    custom_presets: BTreeMap<String, settings::Preset>,
    plandos: BTreeSet<String>,
    settings_mapping: settings::Mapping,
}

#[derive(SmartDefault)]
enum MainWindowView {
    #[default]
    Default {
        #[default(DEFAULT_PRESET.to_owned())]
        selected_preset_or_plando: String,
    },
    CustomizingPresets {
        renaming: Option<(bool, String, String)>,
    },
}

enum WindowState {
    Main,
    Preset {
        preset_name: String,
        active_tab: String,
    },
    Generator {
        settings_base: settings::Preset,
        progress: Percent,
        display: String,
    },
    Seed {
        seed: Seed,
        player: Option<NonZero<u8>>,
    },
    RollError {
        settings_base: settings::Preset,
        error: Arc<RollError>,
    },
}

#[derive(Debug, Clone)]
struct Seed {
    inner: ootr_common::Seed,
    cosmetic_plando_path: PathBuf,
    saving_compressed_rom: bool,
    saving_patches: bool,
    saving_spoiler_log: bool,
    patches_saved: NEVec<bool>,
    spoiler_log_saved: bool,
}

impl Seed {
    fn before_close_message(&self, window_to_close: window::Id, window_to_check: window::Id) -> Option<Message> {
        let unsaved_worlds = self.patches_saved.iter()
            .enumerate()
            .filter(|&(_, &saved)| !saved)
            .map(|(world_idx, _)| NonZero::new(u8::try_from(world_idx + 1).expect("got more than 255 seeds")).expect("got more than 255 seeds"))
            .collect_vec();
        if let Ok(unsaved_worlds) = unsaved_worlds.try_into() {
            return Some(Message::AskSavePatches { window_to_close, window_to_check, unsaved_worlds })
        }
        if !self.spoiler_log_saved {
            return Some(Message::AskSaveSpoiler { window_to_close, window_to_check })
        }
        None
    }

    async fn compressed_rom_save_dialog(&self, lang: Language, base_rom_path: PathBuf, world: NonZero<u8>) -> Result<bool, Error> {
        let dialog = AsyncFileDialog::default()
            .add_filter(translate! {
                lang;
                English => "Nintendo 64 rom";
            }, &["z64"]);
        Ok(if let Some(file) = dialog.save_file().await {
            self.inner.write_compressed_rom(world, base_rom_path, Some(self.cosmetic_plando_path.clone()).filter(|p| !p.as_os_str().is_empty()), file.path().to_owned()).await?;
            true
        } else {
            false
        })
    }

    async fn patches_save_dialog(&self, lang: Language) -> Result<bool, Error> {
        let dialog = AsyncFileDialog::default();
        let dialog = if self.inner.patches.len() == NonZero::<usize>::MIN {
            dialog.add_filter(translate! {
                lang;
                English => "Ocarina of Time randomizer patch file";
            }, &["zpf"])
        } else {
            dialog.add_filter(translate! {
                lang;
                English => "Ocarina of Time randomizer patch file archive";
            }, &["zpfz"])
        };
        Ok(if let Some(file) = dialog.save_file().await {
            if let Ok(patch) = self.inner.patches.iter().into_iter().exactly_one() {
                file.write(patch).await.at(file.path())?;
            } else {
                #[cfg(target_arch = "wasm32")] {
                    let mut zip = ZipWriter::new(Cursor::<Vec<_>>::default());
                    for (world_idx, world_patch) in self.patches.iter().enumerate() {
                        let world_id = NonZero::new(u8::try_from(world_idx + 1).expect("got more than 255 seeds")).expect("got more than 255 seeds");
                        zip.start_file(format!("P{world_id}"), zip::write::SimpleFileOptions::default())?;
                        zip.write_all(world_patch).at_unknown()?;
                    }
                    file.write(&zip.finish()?.into_inner()).await.at(file.path())?;
                }
                #[cfg(not(target_arch = "wasm32"))] {
                    let mut zip = ZipFileWriter::with_tokio(File::create(file.path()).await?);
                    for (world_idx, world_patch) in self.inner.patches.iter().enumerate() {
                        let world_id = NonZero::new(u8::try_from(world_idx + 1).expect("got more than 255 seeds")).expect("got more than 255 seeds");
                        zip.write_entry_whole(ZipEntryBuilder::new(format!("P{world_id}").into(), Compression::Deflate), world_patch).await?;
                    }
                    zip.close().await?.into_inner().sync_all().await?;
                }
            }
            true
        } else {
            false
        })
    }

    async fn spoiler_save_dialog(&self, lang: Language) -> Result<bool, Error> {
        let dialog = AsyncFileDialog::default()
            .add_filter(translate! {
                lang;
                German => "JSON-Dokument";
                English => "JSON document";
            }, &["json"]);
        Ok(if let Some(file) = dialog.save_file().await {
            file.write(self.inner.spoiler_log.as_bytes()).await.at(file.path())?;
            true
        } else {
            false
        })
    }
}

impl Gui {
    fn has_cached_base_rom(&self) -> bool {
        Path::new(concat!(env!("CARGO_MANIFEST_DIR"), "/../../ZOOTDEC.z64")).exists()
    }

    fn has_cached_pal_rom(&self) -> bool {
        Path::new(concat!(env!("CARGO_MANIFEST_DIR"), "/../../ZOOTDEC-PAL.z64")).exists()
    }

    fn presets_and_plandos(&self) -> impl Iterator<Item = (&str, bool, Option<Cow<'_, settings::Preset>>)> {
        iter::once((DEFAULT_PRESET, false, Some(Cow::Owned(HashMap::default()))))
            .chain(self.default_presets.iter().map(|(name, settings)| (&**name, false, Some(Cow::Borrowed(settings)))))
            .chain(self.custom_presets.iter().map(|(name, settings)| (&**name, true, Some(Cow::Borrowed(settings)))))
            .chain(self.plandos.iter().map(|name| (&**name, true, None)))
    }

    fn preset_or_plando(&self, name: &str) -> Option<Cow<'_, settings::Preset>> {
        self.presets_and_plandos().find(|(iter_name, _, _)| *iter_name == name).expect("requested preset does not exist").2
    }

    fn selected_preset_or_plando(&self) -> Option<Option<Cow<'_, settings::Preset>>> {
        let MainWindowView::Default { selected_preset_or_plando } = &self.main_view else { return None };
        Some(self.preset_or_plando(&selected_preset_or_plando))
    }

    fn seed(&self, window: window::Id) -> &Seed {
        match self.windows.get(&window) {
            Some(WindowState::Seed { seed, .. }) => seed,
            Some(_) => panic!("attempted to look up seed for non-seed window"),
            None => panic!("attempted to look up seed for unknown window"),
        }
    }

    fn seed_mut(&mut self, window: window::Id) -> &mut Seed {
        match self.windows.get_mut(&window) {
            Some(WindowState::Seed { seed, .. }) => seed,
            Some(_) => panic!("attempted to look up seed for non-seed window"),
            None => panic!("attempted to look up seed for unknown window"),
        }
    }

    fn title(&self, window: window::Id) -> String {
        match self.windows.get(&window) {
            None | Some(WindowState::Main) => translate! {
                self.language;
                English => format!("OoT Randomizer");
            },
            Some(WindowState::Preset { preset_name, .. }) => preset_name.clone(),
            Some(WindowState::Generator { .. }) => translate! {
                self.language;
                English => format!("Generating Seed…");
            },
            Some(WindowState::Seed { .. }) => translate! {
                self.language;
                English => format!("Seed");
            },
            Some(WindowState::RollError { .. }) => translate! {
                self.language;
                English => format!("Seed Error");
            },
        }
    }

    fn update(&mut self, msg: Message) -> Task<Message> {
        match msg {
            Message::AskDeletePlando(name) => {
                let delete_label = translate! {
                    self.language;
                    English => "Delete";
                };
                let cancel_label = translate! {
                    self.language;
                    English => "Cancel";
                };
                return cmd(AsyncMessageDialog::default()
                    .set_level(rfd::MessageLevel::Warning)
                    .set_title(translate! {
                        self.language;
                        English => "Delete Plando";
                    })
                    .set_description(translate! {
                        self.language;
                        English => format!("Are you sure you want to permanently delete the plando “{name}”?");
                    })
                    .set_buttons(rfd::MessageButtons::OkCancelCustom(delete_label.to_owned(), cancel_label.to_owned()))
                    //TODO set_parent (iced::window::run_with_handle, requires iced to upgrade to raw-window-handle 0.6)
                    .show()
                    .map(move |response| Ok(if let rfd::MessageDialogResult::Custom(label) = response {
                        if label == delete_label {
                            Message::DeletePlando(name)
                        } else if label == cancel_label {
                            Message::Nop
                        } else {
                            unreachable!("got {label} from Delete/Cancel dialog")
                        }
                    } else {
                        unreachable!("got non-custom response from dialog with custom labels")
                    }))
                )
            }
            Message::AskDeletePreset(name) => {
                let delete_label = translate! {
                    self.language;
                    English => "Delete";
                };
                let cancel_label = translate! {
                    self.language;
                    English => "Cancel";
                };
                return cmd(AsyncMessageDialog::default()
                    .set_level(rfd::MessageLevel::Warning)
                    .set_title(translate! {
                        self.language;
                        English => "Delete Preset";
                    })
                    .set_description(translate! {
                        self.language;
                        English => format!("Are you sure you want to permanently delete the preset “{name}”?");
                    })
                    .set_buttons(rfd::MessageButtons::OkCancelCustom(delete_label.to_owned(), cancel_label.to_owned()))
                    //TODO set_parent (iced::window::run_with_handle, requires iced to upgrade to raw-window-handle 0.6)
                    .show()
                    .map(move |response| Ok(if let rfd::MessageDialogResult::Custom(label) = response {
                        if label == delete_label {
                            Message::DeletePreset(name)
                        } else if label == cancel_label {
                            Message::Nop
                        } else {
                            unreachable!("got {label} from Delete/Cancel dialog")
                        }
                    } else {
                        unreachable!("got non-custom response from dialog with custom labels")
                    }))
                )
            }
            Message::AskSavePatches { window_to_close, window_to_check, unsaved_worlds } => {
                let save_label = translate! {
                    self.language;
                    English => "Save";
                };
                let delete_label = translate! {
                    self.language;
                    English => "Delete";
                };
                let cancel_label = translate! {
                    self.language;
                    English => "Cancel";
                };
                return cmd(AsyncMessageDialog::default()
                    .set_level(rfd::MessageLevel::Warning)
                    .set_title(translate! {
                        self.language;
                        English => "Unsaved Seed";
                    })
                    .set_description(translate! {
                        self.language;
                        English => if_chain! {
                            if let Some(WindowState::Seed { seed, .. }) = self.windows.get(&window_to_check);
                            if unsaved_worlds.len() == seed.inner.patches.len();
                            then {
                                format!("Do you want to keep this seed?")
                            } else {
                                format!("Do you want to keep this seed? You haven't saved world{} {}.", if unsaved_worlds.len() == NonZero::<usize>::MIN { "" } else { "s" }, English.join(unsaved_worlds))
                            }
                        };
                    })
                    .set_buttons(rfd::MessageButtons::YesNoCancelCustom(save_label.to_owned(), delete_label.to_owned(), cancel_label.to_owned()))
                    //TODO set_parent (iced::window::run_with_handle, requires iced to upgrade to raw-window-handle 0.6)
                    .show()
                    .map(move |response| Ok(Message::SavePatchesResponse { window_to_close, window_to_check, response }))
                )
            }
            Message::AskSaveSpoiler { window_to_close, window_to_check } => {
                let save_label = translate! {
                    self.language;
                    English => "Save";
                };
                let delete_label = translate! {
                    self.language;
                    English => "Delete";
                };
                let cancel_label = translate! {
                    self.language;
                    English => "Cancel";
                };
                return cmd(AsyncMessageDialog::default()
                    .set_level(rfd::MessageLevel::Warning)
                    .set_title(translate! {
                        self.language;
                        English => "Unsaved Spoiler Log";
                    })
                    .set_description("Do you want to save the spoiler log for this seed? A spoiler log is vital if you need help while playing the seed.")
                    .set_buttons(rfd::MessageButtons::YesNoCancelCustom(save_label.to_owned(), delete_label.to_owned(), cancel_label.to_owned()))
                    //TODO set_parent (iced::window::run_with_handle, requires iced to upgrade to raw-window-handle 0.6)
                    .show()
                    .map(move |response| Ok(Message::SaveSpoilerResponse { window_to_close, window_to_check, response }))
                )
            }
            Message::BaseRomBrowse => {
                let lang = self.language;
                return cmd(async move {
                    Ok(if let Some(file) = AsyncFileDialog::default()
                        .add_filter(translate! {
                            lang;
                            English => "Nintendo 64 rom";
                        }, &["n64", "v64", "z64"])
                        .pick_file().await
                    {
                        Message::SetBaseRomPath(file.path().to_owned())
                    } else {
                        Message::Nop
                    })
                })
            }
            Message::BeginRenamePlando(plando) => if let MainWindowView::CustomizingPresets { renaming } = &mut self.main_view {
                *renaming = Some((true, plando.clone(), plando));
            },
            Message::BeginRenamePreset(preset) => if let MainWindowView::CustomizingPresets { renaming } = &mut self.main_view {
                *renaming = Some((false, preset.clone(), preset));
            },
            Message::CancelRenamePresetOrPlando => if let MainWindowView::CustomizingPresets { renaming } = &mut self.main_view {
                *renaming = None;
            },
            Message::CloseRequested(window) => {
                match &self.windows[&window] {
                    WindowState::Main => {
                        for (&seed_window, window_state) in &self.windows {
                            if let WindowState::Seed { seed, .. } = window_state {
                                if let Some(msg) = seed.before_close_message(window, seed_window) {
                                    return cmd(future::ok(msg))
                                }
                            }
                        }
                        return iced::exit()
                    }
                    WindowState::Preset { .. } => {}
                    WindowState::Generator { .. } => {} //TODO cancel rolling seed (ask first?)
                    WindowState::Seed { seed, .. } => if let Some(msg) = seed.before_close_message(window, window) {
                        return cmd(future::ok(msg))
                    },
                    WindowState::RollError { .. } => {}
                }
                self.windows.remove(&window);
                return window::close(window)
            }
            Message::CommandError(e) => {
                self.error = Some(e);
                if !self.windows.values().any(|window_state| matches!(window_state, WindowState::Main)) {
                    let (main_window_id, window_open_task) = window::open(window::Settings {
                        size: MAIN_WINDOW_SIZE,
                        exit_on_close_request: false,
                        icon: self.icon.clone(),
                        ..window::Settings::default()
                    });
                    self.windows.insert(main_window_id, WindowState::Main);
                    return window_open_task.map(|_| Message::Nop)
                }
            }
            Message::ConfirmRenamePresetOrPlando => if let MainWindowView::CustomizingPresets { renaming } = &mut self.main_view {
                if let Some((is_plando, from, to)) = renaming.take() {
                    return cmd(async move {
                        if is_plando {
                            let from_path = plando_path(&from);
                            let to_path = plando_path(&to);
                            let from_path_clone = from_path.clone();
                            let to_path_clone = to_path.clone();
                            let _was_atomic = spawn_blocking(move || renamore::rename_exclusive_fallback(from_path_clone, to_path_clone)).await?.at2(from_path, to_path)?;
                            Ok(Message::PlandoRenamed { from, to })
                        } else {
                            let from_path = custom_preset_path(&from);
                            let to_path = custom_preset_path(&to);
                            let from_path_clone = from_path.clone();
                            let to_path_clone = to_path.clone();
                            let _was_atomic = spawn_blocking(move || renamore::rename_exclusive_fallback(from_path_clone, to_path_clone)).await?.at2(from_path, to_path)?;
                            Ok(Message::PresetRenamed { from, to })
                        }
                    })
                }
            },
            Message::CopyPresetOrPlando(name) => {
                let lang = self.language;
                if let Some(value) = self.preset_or_plando(&name) {
                    let value = value.into_owned();
                    return cmd(async move {
                        for copy_idx in 1.. {
                            let copy_name = translate! {
                                lang;
                                English => if copy_idx == 1 {
                                    format!("Copy of {name}")
                                } else {
                                    format!("Copy {copy_idx} of {name}")
                                };
                            };
                            match fs::write_json_new(custom_preset_path(&copy_name), &value).await {
                                Ok(()) => return Ok(Message::PresetCopied { copy_name, value }),
                                Err(wheel::Error::Io { inner, .. }) if inner.kind() == io::ErrorKind::AlreadyExists => {}
                                Err(e) => return Err(e.into()),
                            }
                        }
                        Err(Error::TooManyCopies)
                    })
                } else {
                    return cmd(async move {
                        for copy_idx in 1.. {
                            let copy_name = translate! {
                                lang;
                                English => if copy_idx == 1 {
                                    format!("Copy of {name}")
                                } else {
                                    format!("Copy {copy_idx} of {name}")
                                };
                            };
                            match fs::copy_new(plando_path(&name), plando_path(&copy_name)).await {
                                Ok(_) => return Ok(Message::PlandoAdded { name: copy_name }),
                                Err(wheel::Error::Io { inner, .. }) if inner.kind() == io::ErrorKind::AlreadyExists => {}
                                Err(e) => return Err(e.into()),
                            }
                        }
                        Err(Error::TooManyCopies)
                })
                }
            }
            Message::CopyRollDebugInfo(window) => if let Some(WindowState::RollError { error, .. }) = self.windows.get(&window) {
                let mut builder = MessageBuilder::default();
                builder.push_line(format!("error in OoTR version {}{} while trying to generate a seed:", env!("CARGO_PKG_VERSION"), {
                    #[cfg(debug_assertions)] { " (debug)" }
                    #[cfg(not(debug_assertions))] { "" }
                }));
                builder.push_line_safe(error.to_string());
                if_chain! {
                    if let RollError::Python(ref error) = **error;
                    if let Some(traceback) = Python::with_gil(|py| error.traceback(py).and_then(|traceback| traceback.format().ok()));
                    then {
                        builder.push_codeblock_safe(traceback, Some("python-traceback"));
                    } else {
                        builder.push_codeblock_safe(format!("{error:?}"), Some("rust"));
                    }
                }
                return clipboard::write(builder.build())
            },
            Message::CosmeticPlandoBrowse(window) => {
                let lang = self.language;
                return cmd(async move {
                    Ok(if let Some(file) = AsyncFileDialog::default()
                        .add_filter(translate! {
                            lang;
                            English => "Cosmetic plandomizer";
                        }, &["json"])
                        .pick_file().await
                    {
                        Message::SetCosmeticPlandoPath { window, path: file.path().to_owned() }
                    } else {
                        Message::Nop
                    })
                })
            }
            Message::CustomizeSettings => self.main_view = MainWindowView::CustomizingPresets { renaming: None },
            Message::DeletePlando(name) => {
                self.plandos.remove(&name);
                match &mut self.main_view {
                    MainWindowView::Default { selected_preset_or_plando } => if *selected_preset_or_plando == name {
                        *selected_preset_or_plando = DEFAULT_PRESET.to_owned();
                    },
                    MainWindowView::CustomizingPresets { renaming } => if renaming.as_ref().is_some_and(|(_, from, _)| *from == name) {
                        *renaming = None;
                    },
                }
                return cmd(async move {
                    fs::remove_file(plando_path(&name)).await?;
                    Ok(Message::Nop)
                })
            }
            Message::DeletePreset(name) => {
                self.custom_presets.remove(&name);
                match &mut self.main_view {
                    MainWindowView::Default { selected_preset_or_plando } => if *selected_preset_or_plando == name {
                        *selected_preset_or_plando = DEFAULT_PRESET.to_owned();
                    },
                    MainWindowView::CustomizingPresets { renaming } => if renaming.as_ref().is_some_and(|(_, from, _)| *from == name) {
                        *renaming = None;
                    },
                }
                let mut tasks = Vec::with_capacity(2);
                if let Some((&window, _)) = self.windows.iter().find(|(_, window_state)| if let WindowState::Preset { preset_name, .. } = window_state { *preset_name == name } else { false }) {
                    self.windows.remove(&window);
                    tasks.push(window::close(window));
                }
                tasks.push(cmd(async move {
                    fs::remove_file(custom_preset_path(&name)).await?;
                    Ok(Message::Nop)
                }));
                return Task::batch(tasks)
            }
            Message::DismissError => self.error = None,
            Message::Done { window, seed } => if let Some(window_state) = self.windows.get_mut(&window) {
                *window_state = WindowState::Seed {
                    seed: Seed {
                        cosmetic_plando_path: PathBuf::default(),
                        saving_compressed_rom: false,
                        saving_patches: false,
                        saving_spoiler_log: false,
                        patches_saved: seed.patches.nonempty_iter().map(|_| false).collect(),
                        spoiler_log_saved: false,
                        inner: seed,
                    },
                    player: None,
                };
            },
            Message::EditPlayerNumber { window, new_value } => if let Some(WindowState::Seed { player, .. }) = self.windows.get_mut(&window) {
                *player = Some(new_value);
            },
            Message::EditPreset(preset_name) => if let Some((window, _)) = self.windows.iter().find(|(_, window_state)| if let WindowState::Preset { preset_name: iter_preset_name, .. } = window_state { *iter_preset_name == preset_name } else { false }) {
                return window::gain_focus(*window)
            } else {
                let (preset_window_id, window_open_task) = window::open(window::Settings {
                    size: Size { width: 750.0, height: 768.0 },
                    exit_on_close_request: false,
                    icon: self.icon.clone(),
                    ..window::Settings::default()
                });
                self.windows.insert(preset_window_id, WindowState::Preset { active_tab: format!("main_tab"), preset_name });
                return window_open_task.map(|_| Message::Nop)
            },
            Message::EditPresetSetting { window, setting_name, new_value } => if let Some(window) = self.windows.get_mut(&window) {
                if let WindowState::Preset { preset_name, .. } = window {
                    if let Some(preset) = self.custom_presets.get_mut(preset_name) {
                        preset.insert(setting_name, new_value);
                        let path = custom_preset_path(preset_name);
                        let preset = preset.clone();
                        return cmd(async move {
                            fs::write_json(path, preset).await?;
                            Ok(Message::Nop)
                        })
                    }
                }
            },
            Message::EditRenamePresetOrPlando(new_name) => if let MainWindowView::CustomizingPresets { renaming: Some((_, _, to)) } = &mut self.main_view {
                *to = new_name;
            },
            Message::Generate => if let Some(preset_or_plando) = self.selected_preset_or_plando() {
                let MainWindowView::Default { selected_preset_or_plando } = &self.main_view else { unreachable!("should be Some since self.selected_preset_or_plando() is Some") };
                let mut settings_base = if let Some(settings_base) = preset_or_plando {
                    settings_base.into_owned()
                } else {
                    match plando_path(&selected_preset_or_plando).to_str() {
                        Some(plando_path) => collect![
                            format!("enable_distribution_file") => settings::Value(json!(true)),
                            format!("distribution_file") => settings::Value(json!(plando_path.to_owned())),
                        ],
                        None => return cmd(future::err(Error::Utf8)),
                    }
                };
                settings_base.insert(format!("language"), settings::Value(json!(self.language.setting_value())));
                settings_base.insert(format!("user_message"), settings::Value(json!(selected_preset_or_plando)));
                if !self.base_rom_path.as_os_str().is_empty() {
                    match self.base_rom_path.to_str() {
                        Some(base_rom_path) => { settings_base.insert(format!("rom"), settings::Value(json!(base_rom_path.to_owned()))); }
                        None => return cmd(future::err(Error::Utf8)),
                    }
                }
                if self.language.requires_pal_rom() && !self.pal_rom_path.as_os_str().is_empty() {
                    match self.pal_rom_path.to_str() {
                        Some(pal_rom_path) => { settings_base.insert(format!("pal_rom"), settings::Value(json!(pal_rom_path.to_owned()))); }
                        None => return cmd(future::err(Error::Utf8)),
                    }
                }
                //TODO if goal hints are used and there are more than 5 worlds, ask for confirmation due to long generation times
                let (seed_window_id, window_open_task) = window::open(window::Settings {
                    exit_on_close_request: false,
                    icon: self.icon.clone(),
                    ..window::Settings::default()
                });
                let generator = Arc::new(Generator::new(settings_base.clone()));
                self.windows.insert(seed_window_id, WindowState::Generator {
                    progress: Percent::default(),
                    display: format!("Starting seed generator"),
                    settings_base,
                });
                return window_open_task.map(move |window| Message::RunGenerator { window, generator: Arc::clone(&generator) })
            },
            Message::GenerateError { window, settings_base, error } => if let Some(window_state) = self.windows.get_mut(&window) {
                *window_state = WindowState::RollError { settings_base, error };
            }
            Message::ImportPlando(path) => if let Some(name) = path.file_stem() {
                let lang = self.language;
                let name = name.to_string_lossy().to_string();
                return cmd(async move {
                    for copy_idx in 1.. {
                        let name = translate! {
                            lang;
                            English => if copy_idx == 1 {
                                name.clone()
                            } else {
                                format!("{name} {copy_idx}")
                            };
                        };
                        match fs::copy_new(&path, plando_path(&name)).await {
                            Ok(_) => return Ok(Message::PlandoAdded { name }),
                            Err(wheel::Error::Io { inner, .. }) if inner.kind() == io::ErrorKind::AlreadyExists => {}
                            Err(e) => return Err(e.into()),
                        }
                    }
                    Err(Error::TooManyCopies)
                })
            }
            Message::Init { icon, default_presets, custom_presets, plandos, settings_mapping } => {
                self.icon = Some(icon);
                self.default_presets = default_presets;
                self.custom_presets = custom_presets;
                self.plandos = plandos;
                self.settings_mapping = settings_mapping;
                let (main_window_id, window_open_task) = window::open(window::Settings {
                    size: MAIN_WINDOW_SIZE,
                    exit_on_close_request: false,
                    icon: self.icon.clone(),
                    ..window::Settings::default()
                });
                self.windows.insert(main_window_id, WindowState::Main);
                return window_open_task.map(|_| Message::Nop)
            }
            Message::MarkCompressedRomSaved { window, player } => {
                let seed = self.seed_mut(window);
                seed.saving_compressed_rom = false;
                seed.patches_saved[usize::from(player.get() - 1)] = true;
            }
            Message::MarkPatchesSaved { window } => {
                let seed = self.seed_mut(window);
                seed.saving_patches = false;
                for saved in seed.patches_saved.nonempty_iter_mut() {
                    *saved = true;
                }
            }
            Message::MarkPatchesSavedAndContinueClosing { window_to_close, window_to_check } => {
                for saved in self.seed_mut(window_to_check).patches_saved.nonempty_iter_mut() {
                    *saved = true;
                }
                return cmd(future::ok(Message::CloseRequested(window_to_close)))
            }
            Message::MarkSpoilerSaved { window } => {
                let seed = self.seed_mut(window);
                seed.saving_spoiler_log = false;
                seed.spoiler_log_saved = true;
            }
            Message::MarkSpoilerSavedAndContinueClosing { window_to_close, window_to_check } => {
                self.seed_mut(window_to_check).spoiler_log_saved = true;
                return cmd(future::ok(Message::CloseRequested(window_to_close)))
            }
            Message::Nop => {}
            Message::PalRomBrowse => {
                let lang = self.language;
                return cmd(async move {
                    Ok(if let Some(file) = AsyncFileDialog::default()
                        .add_filter(translate! {
                            lang;
                            English => "Nintendo 64 rom";
                        }, &["n64", "v64", "z64"])
                        .pick_file().await
                    {
                        Message::SetPalRomPath(file.path().to_owned())
                    } else {
                        Message::Nop
                    })
                })
            }
            Message::PlandoAdded { name } => {
                self.plandos.insert(name);
            }
            Message::PlandoBrowse => {
                let lang = self.language;
                return cmd(async move {
                    Ok(if let Some(file) = AsyncFileDialog::default()
                        .add_filter(translate! {
                            lang;
                            English => "Plandomizer";
                        }, &["json"])
                        .pick_file().await
                    {
                        Message::ImportPlando(file.path().to_owned())
                    } else {
                        Message::Nop
                    })
                })
            }
            Message::PlandoRenamed { from, to } => {
                self.plandos.remove(&from);
                self.plandos.insert(to.clone());
                if let MainWindowView::CustomizingPresets { renaming } = &mut self.main_view {
                    *renaming = None;
                }
            }
            Message::PresetCopied { copy_name, value } => {
                self.custom_presets.insert(copy_name.clone(), value);
                return cmd(future::ok(Message::EditPreset(copy_name)))
            }
            Message::PresetRenamed { from, to } => {
                let settings = self.custom_presets.remove(&from).expect("presets desync");
                self.custom_presets.insert(to.clone(), settings);
                if let MainWindowView::CustomizingPresets { renaming } = &mut self.main_view {
                    *renaming = None;
                }
                if let Some(window_state) = self.windows.values_mut().find(|window_state| if let WindowState::Preset { preset_name, .. } = window_state { *preset_name == from } else { false }) {
                    let WindowState::Preset { preset_name, .. } = window_state else { unreachable!("checked in `find`") };
                    *preset_name = to;
                }
            }
            Message::ResetPlayerNumber(window) => if let Some(WindowState::Seed { player, .. }) = self.windows.get_mut(&window) {
                *player = None;
            },
            Message::RetrySeed(window) => if let Some(window_state) = self.windows.get_mut(&window) {
                if let WindowState::RollError { settings_base, .. } = window_state {
                    let generator = Arc::new(Generator::new(settings_base.clone()));
                    *window_state = WindowState::Generator {
                        settings_base: settings_base.clone(),
                        progress: Percent::default(),
                        display: format!("Starting seed generator"),
                    };
                    return cmd(future::ok(Message::RunGenerator { window, generator }))
                }
            },
            Message::RunGenerator { window, generator } => if let Some(window_state) = self.windows.get_mut(&window) {
                if let WindowState::Generator { settings_base, progress, display } = window_state {
                    *progress = generator.progress();
                    *display = generator.to_string();
                    let settings_base = settings_base.clone();
                    return cmd(async move {
                        Ok(match Arc::into_inner(generator).expect("generator used multiple times").run().await {
                            Ok(Ok(seed)) => Message::Done { window, seed },
                            Ok(Err(e)) => Message::GenerateError { window, settings_base, error: Arc::new(e) },
                            Err(generator) => Message::RunGenerator { window, generator: Arc::new(generator) },
                        })
                    })
                }
            },
            Message::SaveCompressedRom { window } => if let Some(&WindowState::Seed { player, .. }) = self.windows.get(&window) {
                let lang = self.language;
                let base_rom_path = Some(self.base_rom_path.clone()).filter(|path| !path.as_os_str().is_empty()).unwrap_or_else(|| PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../../ZOOTDEC.z64")));
                let seed = self.seed_mut(window);
                seed.saving_compressed_rom = true;
                let seed = seed.clone();
                let player = player.unwrap_or(NonZero::<u8>::MIN);
                return cmd(async move {
                    Ok(if seed.compressed_rom_save_dialog(lang, base_rom_path, player).await? {
                        Message::MarkCompressedRomSaved { window, player }
                    } else {
                        Message::Nop
                    })
                })
            },
            Message::SavePatches { window } => {
                let lang = self.language;
                let seed = self.seed_mut(window);
                seed.saving_patches = true;
                let seed = seed.clone();
                return cmd(async move {
                    Ok(if seed.patches_save_dialog(lang).await? {
                        Message::MarkPatchesSaved { window }
                    } else {
                        Message::Nop
                    })
                })
            }
            Message::SavePatchesResponse { window_to_close, window_to_check, response } => if let rfd::MessageDialogResult::Custom(label) = response {
                let save_label = translate! {
                    self.language;
                    English => "Save";
                };
                let delete_label = translate! {
                    self.language;
                    English => "Delete";
                };
                let cancel_label = translate! {
                    self.language;
                    English => "Cancel";
                };
                if label == save_label {
                    let lang = self.language;
                    let seed = self.seed(window_to_check).clone();
                    return cmd(async move {
                        Ok(if seed.patches_save_dialog(lang).await? {
                            Message::MarkPatchesSavedAndContinueClosing { window_to_close, window_to_check }
                        } else {
                            Message::Nop
                        })
                    })
                } else if label == delete_label {
                    self.windows.remove(&window_to_check);
                    return if window_to_close == window_to_check {
                        window::close(window_to_check)
                    } else {
                        window::close(window_to_check)
                        .chain(cmd(future::ok(Message::CloseRequested(window_to_close))))
                    }
                } else if label == cancel_label {
                    // do nothing
                } else {
                    unreachable!("got {label} from Save/Delete/Cancel dialog")
                }
            } else {
                unreachable!("got non-custom response from dialog with custom labels")
            },
            Message::SaveSpoiler { window } => {
                let lang = self.language;
                let seed = self.seed_mut(window);
                seed.saving_spoiler_log = true;
                let seed = seed.clone();
                return cmd(async move {
                    Ok(if seed.spoiler_save_dialog(lang).await? {
                        Message::MarkSpoilerSaved { window }
                    } else {
                        Message::Nop
                    })
                })
            }
            Message::SaveSpoilerResponse { window_to_close, window_to_check, response } => if let rfd::MessageDialogResult::Custom(label) = response {
                let save_label = translate! {
                    self.language;
                    English => "Save";
                };
                let delete_label = translate! {
                    self.language;
                    English => "Delete";
                };
                let cancel_label = translate! {
                    self.language;
                    English => "Cancel";
                };
                if label == save_label {
                    let lang = self.language;
                    let seed = self.seed(window_to_check).clone();
                    return cmd(async move {
                        Ok(if seed.spoiler_save_dialog(lang).await? {
                            Message::MarkSpoilerSavedAndContinueClosing { window_to_close, window_to_check }
                        } else {
                            Message::Nop
                        })
                    })
                } else if label == delete_label {
                    self.windows.remove(&window_to_check);
                    return if window_to_close == window_to_check {
                        window::close(window_to_check)
                    } else {
                        window::close(window_to_check)
                        .chain(cmd(future::ok(Message::CloseRequested(window_to_close))))
                    }
                } else if label == cancel_label {
                    // do nothing
                } else {
                    unreachable!("got {label} from Save/Delete/Cancel dialog")
                }
            } else {
                unreachable!("got non-custom response from dialog with custom labels")
            },
            Message::SetBaseRomPath(new_path) => self.base_rom_path = new_path,
            Message::SetCosmeticPlandoPath { window, path } => self.seed_mut(window).cosmetic_plando_path = path,
            Message::SetLanguage(language) => self.language = language,
            Message::SetPalRomPath(new_path) => self.pal_rom_path = new_path,
            Message::SetPresetOrPlando(selected_preset_or_plando) => self.main_view = MainWindowView::Default { selected_preset_or_plando },
            Message::SetSettingsTab { window, tab_name } => if let Some(window) = self.windows.get_mut(&window) {
                if let WindowState::Preset { active_tab, .. } = window {
                    *active_tab = tab_name;
                }
            },
        }
        Task::none()
    }

    fn view(&self, window: window::Id) -> Element<'_, Message> {
        // see https://gist.github.com/fenhl/394e09e8ea5ac5e552c8c61d016992a6

        match self.windows.get(&window) {
            None => Column::new().into(),
            Some(WindowState::Main) => {
                if let Some(ref e) = self.error {
                    Column::new()
                    .push(Text::new(translate! {
                        self.language;
                        German => "Fehler";
                        English => "Error";
                    }).size(24))
                    .push(Text::new(e.to_string()))
                    .push(Button::new(translate! {
                        self.language;
                        English => "Dismiss";
                    }).on_press(Message::DismissError))
                    .spacing(8)
                    .padding(8)
                    .into()
                } else {
                    match &self.main_view {
                        MainWindowView::Default { selected_preset_or_plando } => {
                            let mut col = Column::new()
                            //TODO “Generate from” (dropdown, random seed/set seed/patch file, hide irrelevant GUI elements)
                            //TODO “Seed” (text field, only if “Generate from set seed”)
                            .push(Row::new()
                                .push(translate! {
                                    self.language;
                                    French => "Langue :";
                                    German => "Sprache:";
                                    English => "Language:";
                                })
                                .push(PickList::new(all().collect_vec(), Some(self.language), Message::SetLanguage).width(Length::Fill))
                                .align_y(iced::Alignment::Center)
                                .spacing(8)
                            )
                            .push(Row::new()
                                .push(if self.language.requires_pal_rom() {
                                    translate! {
                                        self.language;
                                        English => "Base rom (NTSC):";
                                    }
                                } else {
                                    translate! {
                                        self.language;
                                        English => "Base rom:";
                                    }
                                })
                                .push(TextInput::new(if self.has_cached_base_rom() {
                                    translate! {
                                        self.language;
                                        English => "Using cached rom";
                                    }
                                } else {
                                    translate! {
                                        self.language;
                                        English => "Required";
                                    }
                                }, &self.base_rom_path.to_string_lossy())
                                    .on_input(|s| Message::SetBaseRomPath(PathBuf::from(s)))
                                    .on_paste(|s| Message::SetBaseRomPath(PathBuf::from(s)))
                                )
                                .push(Button::new(translate! {
                                    self.language;
                                    English => "Browse…";
                                }).on_press(Message::BaseRomBrowse))
                                .align_y(iced::Alignment::Center)
                                .spacing(8)
                            );
                            if self.language.requires_pal_rom() {
                                col = col.push(Row::new()
                                    .push(translate! {
                                        self.language;
                                        English => "Base rom (PAL):";
                                    })
                                    .push(TextInput::new(if self.has_cached_pal_rom() {
                                        translate! {
                                            self.language;
                                            English => "Using cached rom";
                                        }
                                    } else {
                                        translate! {
                                            self.language;
                                            English => "Required";
                                        }
                                    }, &self.pal_rom_path.to_string_lossy())
                                        .on_input(|s| Message::SetPalRomPath(PathBuf::from(s)))
                                        .on_paste(|s| Message::SetPalRomPath(PathBuf::from(s)))
                                    )
                                    .push(Button::new(translate! {
                                        self.language;
                                        English => "Browse…";
                                    }).on_press(Message::PalRomBrowse))
                                    .align_y(iced::Alignment::Center)
                                    .spacing(8)
                                );
                            }
                            col
                            .push(Row::new()
                                .push(translate! {
                                    self.language;
                                    German => "Einstellungen:";
                                    English => "Settings:";
                                })
                                .push(PickList::<&str, _, _, _, _>::new(self.presets_and_plandos().map(|(name, _, _)| name).collect_vec(), Some(&**selected_preset_or_plando), |preset| Message::SetPresetOrPlando(preset.to_owned())).width(Length::Fill))
                                .push(Button::new(translate! {
                                    self.language;
                                    English => "Customize";
                                }).on_press(Message::CustomizeSettings))
                                .align_y(iced::Alignment::Center)
                                .spacing(8)
                            )
                            //TODO “Cosmetics” (dropdown with “Customize” button)
                            .push({
                                let disable_reason = if !self.has_cached_base_rom() && self.base_rom_path.as_os_str().is_empty() {
                                    Some(translate! {
                                        self.language;
                                        English => "Please load a base rom";
                                    })
                                } else if self.language.requires_pal_rom() && !self.has_cached_pal_rom() && self.pal_rom_path.as_os_str().is_empty() {
                                    Some(translate! {
                                        self.language;
                                        English => "Please load a PAL base rom";
                                    })
                                } else {
                                    None
                                };
                                let mut btn = Button::new(Text::new(translate! {
                                    self.language;
                                    English => "Generate!";
                                }));
                                if disable_reason.is_none() { btn = btn.on_press(Message::Generate) }
                                let mut row = Row::new().push(btn);
                                if let Some(disable_reason) = disable_reason {
                                    row = row.push(disable_reason);
                                }
                                row.align_y(iced::Alignment::Center).spacing(8)
                            }) //TODO keep button enabled but style as disabled if prerequisites to generate seed not met (e.g. generate from patch file but no patch file) so an error can be shown on click or next to it
                            .spacing(8)
                            .padding(8)
                            .into()
                        }
                        MainWindowView::CustomizingPresets { renaming } => Scrollable::new(
                            Row::new()
                                .push(
                                    Column::new()
                                    .push(Row::new()
                                        //TODO button to import from settings string
                                        .push(Button::new(translate! {
                                            self.language;
                                            English => "Import Plando";
                                        }).on_press(Message::PlandoBrowse))
                                        .spacing(8)
                                    )
                                    .extend(self.presets_and_plandos().map(|(name, is_custom, settings_base)| {
                                        let mut row = Row::new();
                                        if_chain! {
                                            if let Some((_, from, to)) = renaming;
                                            if from == name;
                                            then {
                                                row = row
                                                    .push(TextInput::new(from, to).on_input(Message::EditRenamePresetOrPlando).on_submit_maybe((!self.presets_and_plandos().any(|(name, _, _)| name == to)).then_some(Message::ConfirmRenamePresetOrPlando)))
                                                    .push(Button::new(translate! {
                                                        self.language;
                                                        English => "Confirm";
                                                    }).on_press_maybe((!self.presets_and_plandos().any(|(name, _, _)| name == to)).then_some(Message::ConfirmRenamePresetOrPlando)))
                                                    .push(Button::new(translate! {
                                                        self.language;
                                                        English => "Cancel";
                                                    }).on_press(Message::CancelRenamePresetOrPlando))
                                                ;
                                            } else {
                                                row = row
                                                    .push(Button::new(translate! {
                                                        self.language;
                                                        German => "Auswählen";
                                                        English => "Select";
                                                    }).on_press_maybe(renaming.is_none().then(|| Message::SetPresetOrPlando(name.to_owned()))))
                                                    .push(Button::new(translate! {
                                                        self.language;
                                                        German => "Kopieren";
                                                        English => "Copy";
                                                    }).on_press(Message::CopyPresetOrPlando(name.to_owned())))
                                                    .push(Button::new(translate! {
                                                        self.language;
                                                        German => "Bearbeiten";
                                                        English => "Edit";
                                                    }).on_press_maybe((is_custom && settings_base.is_some()).then(|| Message::EditPreset(name.to_owned())))) //TODO support editing plandos (text area + button to edit with external editor)
                                                    .push(Button::new(translate! {
                                                        self.language;
                                                        German => "Umbenennen";
                                                        English => "Rename";
                                                    }).on_press_maybe((renaming.is_none() && is_custom).then(|| if settings_base.is_some() {
                                                        Message::BeginRenamePreset(name.to_owned())
                                                    } else {
                                                        Message::BeginRenamePlando(name.to_owned())
                                                    })))
                                                    .push(Button::new(translate! {
                                                        self.language;
                                                        German => "Löschen";
                                                        English => "Delete";
                                                    }).on_press_maybe(is_custom.then(|| if settings_base.is_some() {
                                                        Message::AskDeletePreset(name.to_owned())
                                                    } else {
                                                        Message::AskDeletePlando(name.to_owned())
                                                    })))
                                                    .push(name)
                                                ;
                                            }
                                        }
                                        row.align_y(iced::Alignment::Center).spacing(8).into()
                                    }))
                                    .spacing(8)
                                    .padding(8)
                                    .width(Length::Fill)
                                )
                                .push(Space::with_width(Length::Shrink)) // to avoid overlap with the scrollbar
                                .spacing(16)
                        ).height(Length::Fill).into(),
                    }
                }
            }
            Some(WindowState::Preset { preset_name, active_tab }) => {
                let preset = self.preset_or_plando(preset_name).expect("preset window for a plando");
                let mut disabled_tabs = HashSet::new();
                let mut disabled_sections = HashSet::new();
                let mut disabled_settings = HashSet::new();
                let mut col = Column::new();
                let mut button_row = Row::new();
                for tab in &self.settings_mapping.tabs {
                    //TODO reintroduce relevant settings:
                    // generate_from_file, patch_file → main view? file argument/drop handler? both?
                    // cosmetics, sfx → separate preset list in seed window
                    // any others?
                    if tab.name != "general_tab" && !tab.exclude_from_web && !tab.exclude_from_electron && !tab.app_type.iter().any(|app_type| app_type != "generator") {
                        button_row = button_row.push(Button::new(Text::new(&tab.text).size(24))
                            .on_press_maybe((tab.name != *active_tab).then(|| Message::SetSettingsTab { window, tab_name: tab.name.clone() }))
                        );
                    }
                    for section in &tab.sections {
                        for setting_name in &section.settings {
                            match Python::with_gil(|py| {
                                let setting_info = py.import("SettingsList")?.getattr("SettingInfos")?.getattr("setting_infos")?.get_item(setting_name)?;
                                PyResult::Ok((
                                    setting_info.getattr("default")?.extract::<settings::Value>()?,
                                    setting_info.getattr("disable")?.extract::<Option<HashMap<settings::Value, settings::Disable>>>()?.unwrap_or_default(),
                                ))
                            }) {
                                Ok((default, disable)) => for (value, settings::Disable { tabs, sections, settings }) in disable {
                                    if preset.get(setting_name).unwrap_or(&default).matches_disable(&value) {
                                        disabled_tabs.extend(tabs);
                                        disabled_sections.extend(sections);
                                        disabled_settings.extend(settings);
                                    }
                                },
                                Err(e) => col = col.push(Text::new(translate! {
                                    self.language;
                                    English => format!("error checking disables for setting {setting_name}: {e}");
                                }).color(iced::Color::from_rgb8(255, 0, 0))),
                            }
                        }
                    }
                }
                col
                    .push(button_row.align_y(iced::Alignment::Center).spacing(8).padding(8))
                    .push(Scrollable::new(
                        Row::new()
                            .push({
                                let mut col = Column::new();
                                if active_tab == "main_tab" {
                                    let enabled = !disabled_tabs.contains("general_tab") && !disabled_sections.contains("multiworld_section") && !disabled_settings.contains("world_count");
                                    col = setting_view(col, self.language, window, &preset, "world_count", enabled); //TODO use section description as tooltip
                                }
                                for tab in &self.settings_mapping.tabs {
                                    if tab.name == *active_tab {
                                        for (pos, section) in tab.sections.iter().with_position() {
                                            if let Position::Middle | Position::Last = pos {
                                                col = col.push(Rule::horizontal(1));
                                            }
                                            if !section.text.is_empty() {
                                                col = col.push(Text::new(&section.text).size(18));
                                            }
                                            for setting_name in &section.settings {
                                                let enabled = !disabled_tabs.contains(&tab.name) && !disabled_sections.contains(&section.name) && !disabled_settings.contains(setting_name);
                                                col = setting_view(col, self.language, window, &preset, &setting_name, enabled);
                                            }
                                        }
                                    }
                                }
                                col.spacing(8).padding(8).width(Length::Fill)
                            })
                            .push(Space::with_width(Length::Shrink)) // to avoid overlap with the scrollbar
                            .spacing(16)
                    ).height(Length::Fill))
                    .into()
            }
            Some(WindowState::Generator { progress, display, .. }) => Column::new()
                .push(Text::new(translate! {
                    self.language;
                    English => "Generating Seed…";
                }).size(24))
                .push(ProgressBar::new(0.0..=100.0, (*progress).into()))
                .push(Text::new(display))
                .spacing(8)
                .padding(8)
                .into(),
            Some(WindowState::Seed { seed, player }) => Column::new()
                .push(Text::new(translate! {
                    self.language;
                    English => "Seed";
                }).size(24)) //TODO show file hash instead
                .push(Row::new()
                    .push(translate! {
                        self.language;
                        English => "Cosmetic plando:";
                    })
                    .push(TextInput::new(translate! {
                        self.language;
                        English => "None";
                    }, &seed.cosmetic_plando_path.to_string_lossy())
                        .on_input(move |s| Message::SetCosmeticPlandoPath { window, path: PathBuf::from(s) })
                        .on_paste(move |s| Message::SetCosmeticPlandoPath { window, path: PathBuf::from(s) })
                    )
                    .push(Button::new(translate! {
                        self.language;
                        English => "Browse…";
                    }).on_press(Message::CosmeticPlandoBrowse(window)))
                    .align_y(iced::Alignment::Center)
                    .spacing(8)
                )
                .push({
                    let mut row = Row::new()
                        .push(if seed.saving_compressed_rom {
                            Button::new(translate! {
                                self.language;
                                English => "Saving rom…";
                            })
                        } else {
                            Button::new(translate! {
                                self.language;
                                English => "Save rom";
                            }).on_press_maybe((seed.inner.patches.len() == NonZero::<usize>::MIN || player.is_some()).then(|| Message::SaveCompressedRom { window }))
                        })
                        //TODO “or” text + button to save wad (shares player number selection with “Save rom”)
                        //TODO convenience buttons to launch the seed in an emulator discovered on the system
                    ;
                    if seed.inner.patches.len() != NonZero::<usize>::MIN {
                        row = row
                            .push("for player")
                            .push(TextInput::new(&format!("1–{}", seed.inner.patches.len()), &player.map(|player| player.to_string()).unwrap_or_default()).on_input(move |new_value: String| if new_value.is_empty() {
                                Message::ResetPlayerNumber(window)
                            } else {
                                if_chain! {
                                    if let Ok(new_value) = new_value.parse::<NonZero<u8>>();
                                    if NonZero::<usize>::from(new_value) <= seed.inner.patches.len();
                                    then {
                                        Message::EditPlayerNumber { window, new_value }
                                    } else {
                                        Message::Nop
                                    }
                                }
                            }).width(48).align_x(iced::Alignment::End))
                        ;
                    }
                    row.align_y(iced::Alignment::Center).spacing(8)
                })
                .push(Rule::horizontal(1))
                .push(Row::new()
                    .push(if seed.saving_spoiler_log {
                        Button::new(translate! {
                            self.language;
                            English => "Saving spoiler log…";
                        })
                    } else {
                        Button::new(translate! {
                            self.language;
                            English => "Save spoiler log";
                        }).on_press(Message::SaveSpoiler { window })
                    })
                    .push(if seed.saving_patches {
                        Button::new(if seed.inner.patches.len() == NonZero::<usize>::MIN {
                            translate! {
                                self.language;
                                English => "Saving patch file…";
                            }
                        } else {
                            translate! {
                                self.language;
                                English => "Saving patch file archive…";
                            }
                        })
                    } else {
                        Button::new(if seed.inner.patches.len() == NonZero::<usize>::MIN {
                            translate! {
                                self.language;
                                English => "Save patch file";
                            }
                        } else {
                            translate! {
                                self.language;
                                English => "Save patch file archive";
                            }
                        }).on_press_maybe((!seed.saving_patches).then(|| Message::SavePatches { window }))
                    })
                    .spacing(8)
                )
                .spacing(8)
                .padding(8)
                .into(),
            Some(WindowState::RollError { error, .. }) => Column::new()
                .push(Text::new(translate! {
                    self.language;
                    English => "Error rolling seed";
                }).size(24))
                .push(Text::new(error.to_string()))
                .push(Row::new()
                    .push(Button::new(translate! {
                        self.language;
                        English => "Copy Debug Info";
                    }).on_press(Message::CopyRollDebugInfo(window)))
                    .push(Button::new(translate! {
                        self.language;
                        English => "Retry";
                    }).on_press(Message::RetrySeed(window)))
                    .spacing(8)
                )
                .spacing(8)
                .padding(8)
                .into(),
        }
    }
}

fn setting_view<'a>(mut col: Column<'a, Message>, language: Language, window: window::Id, preset: &settings::Preset, setting_name: &'a str, enabled: bool) -> Column<'a, Message> {
    //TODO “?” button to display tooltip
    match Python::with_gil(|py| {
        let setting_info = py.import("SettingsList")?.getattr("SettingInfos")?.getattr("setting_infos")?.get_item(setting_name)?;
        let gui_params = setting_info.getattr("gui_params")?.extract::<HashMap<String, Py<PyAny>>>()?;
        PyResult::Ok((
            setting_info.getattr("gui_text")?.extract::<String>()?,
            setting_info.getattr("gui_type")?.extract::<Option<String>>()?,
            setting_info.getattr("default")?.extract::<settings::Value>()?,
            setting_info.getattr("disabled_default")?.extract::<settings::Value>()?,
            setting_info.getattr("choices")?.extract::<IndexMap<settings::Value, String>>()?,
            if let Some(hide_when_disabled) = gui_params.get("hide_when_disabled") { hide_when_disabled.extract(py)? } else { false },
            gui_params,
        ))
    }) {
        Ok((gui_text, gui_type, default, disabled_default, choices, hide_when_disabled, gui_params)) => {
            let value = if enabled {
                preset.get(setting_name).unwrap_or(&default)
            } else {
                if hide_when_disabled { return col }
                &disabled_default
            };
            let Some(gui_type) = gui_type else { return col };
            match &*gui_type {
                "Checkbutton" => col = col.push(Checkbox::new(gui_text, value.as_bool().unwrap_or_default())
                    .on_toggle_maybe(enabled.then(|| move |new_value| Message::EditPresetSetting { window, setting_name: setting_name.to_owned(), new_value: settings::Value(json!(new_value)) }))
                ),
                "Combobox" => col = col.push(Row::new()
                    .push(Text::new(format!("{gui_text}:")))
                    .push(PickList::new(
                        if enabled {
                            choices.iter().filter_map(|(value, display)| Some(settings::DisplayValue { value: value.as_str()?.to_owned(), display: display.clone() })).collect_vec()
                        } else {
                            vec![settings::DisplayValue { value: String::default(), display: translate! {
                                language;
                                English => format!("This setting is disabled.");
                            } }]
                        },
                        value.as_str().and_then(|value| Some(settings::DisplayValue { value: value.to_owned(), display: choices.get(&settings::Value(json!(value)))?.to_owned() })),
                        move |settings::DisplayValue { value, .. }| if enabled {
                            Message::EditPresetSetting { window, setting_name: setting_name.to_owned(), new_value: settings::Value(json!(value)) }
                        } else {
                            Message::Nop
                        },
                    ).width(Length::Fill))
                    .align_y(iced::Alignment::Center)
                    .spacing(8)
                ),
                "MultipleSelect" | "SearchBox" => {
                    let choices_clone = choices.clone();
                    let new_value = value.clone();
                    col = col.push(Row::new()
                        .push(Text::new(format!("{gui_text}:")))
                        .push(PickList::new(
                            if enabled {
                                choices.iter().filter_map(|(iter_value, display)| Some(settings::DisplayValue { value: iter_value.as_str()?.to_owned(), display: format!("{} {display}", if value.as_array().is_some_and(|choices| choices.contains(iter_value)) { '✓' } else { ' ' }) })).collect_vec()
                            } else {
                                vec![settings::DisplayValue { value: String::default(), display: translate! {
                                    language;
                                    English => format!("This setting is disabled.");
                                } }]
                            },
                            None::<settings::DisplayValue>,
                            move |settings::DisplayValue { value, .. }| if enabled {
                                let mut new_value = new_value.clone();
                                if let Some(new_value) = new_value.as_array_mut() {
                                    if new_value.contains(&settings::Value(json!(value))) {
                                        new_value.retain(|iter_value| iter_value.as_str().is_none_or(|iter_value| iter_value != value));
                                    } else {
                                        if let Err(idx) = new_value.binary_search_by_key(&choices_clone.iter().position(|(iter_value, _)| *iter_value == settings::Value(json!(value))), |value| choices_clone.iter().position(|(iter_value, _)| *iter_value == settings::Value(json!(value)))) {
                                            new_value.insert(idx, json!(value));
                                        }
                                    }
                                }
                                Message::EditPresetSetting { window, setting_name: setting_name.to_owned(), new_value }
                            } else {
                                Message::Nop
                            },
                        ).placeholder(if let settings::Value(serde_json::Value::Array(value)) = value {
                            if choices.keys().map(|settings::Value(value)| value).eq(value) {
                                translate! {
                                    language;
                                    English => format!("All");
                                }
                            } else {
                                match &**value {
                                    [] => translate! {
                                        language;
                                        English => format!("None");
                                    },
                                    [value] => choices.get(value).map(|value| &**value).unwrap_or(translate! {
                                        language;
                                        English => "Unknown";
                                    }).to_owned(),
                                    [v1, v2] => format!("{}, {}", choices.get(v1).as_deref().map(|value| &**value).unwrap_or(translate! {
                                        language;
                                        English => "Unknown";
                                    }), choices.get(v2).as_deref().map(|value| &**value).unwrap_or(translate! {
                                        language;
                                        English => "Unknown";
                                    })),
                                    [_, _, _, ..] => translate! {
                                        language;
                                        English => format!("{} Selected", value.len());
                                    },
                                }
                            }
                        } else {
                            translate! {
                                language;
                                German => format!("Fehler");
                                English => format!("Error");
                            }
                        }).width(Length::Fill))
                        .align_y(iced::Alignment::Center)
                        .spacing(8)
                    );
                }
                "Numberinput" | "Scale" => match Python::with_gil(|py| PyResult::Ok((
                    gui_params.get("min").ok_or_else(|| PyKeyError::new_err("Scale setting without minimum"))?.extract::<i32>(py)?,
                    gui_params.get("max").ok_or_else(|| PyKeyError::new_err("Scale setting without maximum"))?.extract::<i32>(py)?,
                    if let Some(step) = gui_params.get("step") { step.extract::<i32>(py)? } else { 1 },
                ))) {
                    Ok((min, max, step)) => {
                        let value = value.as_i64().expect("Scale value is not valid i64") as i32;
                        col = col.push(Row::new()
                            .push(Text::new(format!("{gui_text}:")))
                            .push(Slider::new(min..=max, value, move |new_value| if enabled {
                                Message::EditPresetSetting { window, setting_name: setting_name.to_owned(), new_value: settings::Value(json!(new_value)) }
                            } else {
                                Message::Nop
                            }).step(step))
                            .push(TextInput::new(&format!("{min}–{max}"), &value.to_string()).on_input_maybe(enabled.then(|| move |new_value: String| if_chain! {
                                if let Ok(new_value) = new_value.parse::<i32>();
                                if (min..=max).contains(&new_value);
                                then {
                                    Message::EditPresetSetting { window, setting_name: setting_name.to_owned(), new_value: settings::Value(json!(new_value)) }
                                } else {
                                    Message::Nop
                                }
                            })).width(48).align_x(iced::Alignment::End))
                            .align_y(iced::Alignment::Center)
                            .spacing(8)
                        );
                    }
                    Err(e) => col = col.push(Text::new(format!("error displaying setting {setting_name}: {e}")).color(iced::Color::from_rgb8(255, 0, 0))),
                },
                "Textbox" => col = col.push(Text::new(gui_text)),
                "Textinput" => col = col.push(Row::new()
                    .push(Text::new(format!("{gui_text}:")))
                    .push(TextInput::new("", value.as_str().unwrap_or_default()).on_input_maybe(enabled.then(|| move |new_value| Message::EditPresetSetting { window, setting_name: setting_name.to_owned(), new_value: settings::Value(json!(new_value)) })))
                    .align_y(iced::Alignment::Center)
                    .spacing(8)
                ),
                _ => col = col.push(Text::new(format!("unknown gui_type {gui_type} for setting {setting_name}")).color(iced::Color::from_rgb8(255, 0, 0))),
            }
        }
        Err(e) => col = col.push(Text::new(format!("error displaying setting {setting_name}: {e}")).color(iced::Color::from_rgb8(255, 0, 0))),
    }
    col
}

fn main() -> Result<(), Error> {
    iced::daemon(Gui::title, Gui::update, Gui::view)
        .subscription(|_| iced::event::listen_with(|event, _, window| if let iced::Event::Window(window::Event::CloseRequested) = event {
            Some(Message::CloseRequested(window))
        } else {
            None
        }))
        .theme(|_, _| wheel::gui::theme())
        .default_font(iced::Font::with_name("DejaVu Sans"))
        .run_with(|| (Gui::default(), cmd(async move {
            let icon = icon::from_file_data(include_bytes!("../../../assets/ootr-arrows.ico"), Some(ImageFormat::Ico))?;
            let () = spawn_blocking(move || Python::with_gil(|py| {
                let py_version = py.version_info();
                if py_version < (3, 9) {
                    return Err(Error::PythonVersion {
                        major: py_version.major,
                        minor: py_version.minor,
                        patch: py_version.patch,
                    })
                }
                let sys = py.import("sys")?;
                sys.getattr("path")?.call_method1("append", (concat!(env!("CARGO_MANIFEST_DIR"), "/../.."),))?;
                Ok::<_, Error>(())
            })).await??;
            let default_presets = fs::read_json(concat!(env!("CARGO_MANIFEST_DIR"), "/../../data/presets_default.json")).await?;
            let custom_presets = fs::read_dir(CUSTOM_PRESETS_PATH)
                .err_into::<Error>()
                .try_filter_map(|entry| async move {
                    let file_name = entry.file_name().into_string().map_err(|_| Error::Utf8)?;
                    Ok(if let Some(preset_name) = file_name.strip_suffix(CUSTOM_PRESET_SUFFIX) {
                        Some((preset_name.replace('_', "/"), fs::read_json(entry.path()).await?))
                    } else {
                        None
                    })
                })
                .try_collect().await?;
            let plandos = fs::read_dir(CUSTOM_PRESETS_PATH)
                .err_into::<Error>()
                .try_filter_map(|entry| async move {
                    let file_name = entry.file_name().into_string().map_err(|_| Error::Utf8)?;
                    Ok(if let Some(preset_name) = file_name.strip_suffix(PLANDO_SUFFIX) {
                        Some(preset_name.replace('_', "/"))
                    } else {
                        None
                    })
                })
                .try_collect().await?;
            let settings_mapping = fs::read_json::<settings::Mapping>(concat!(env!("CARGO_MANIFEST_DIR"), "/../../data/settings_mapping.json")).await?;
            Ok(Message::Init { icon, default_presets, custom_presets, plandos, settings_mapping })
        })))?;
    Ok(())
}
