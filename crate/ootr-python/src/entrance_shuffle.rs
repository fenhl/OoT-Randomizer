use pyo3::prelude::*;

#[pyclass(frozen, eq, hash)]
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum EntranceKind {
    Dungeon,
    DungeonSpecial,
    ChildBoss,
    AdultBoss,
    SpecialBoss,
    Interior,
    SpecialInterior,
    Hideout,
    Grotto,
    Grave,
    Overworld,
    OverworldOneWay,
    OwlDrop,
    ChildSpawn,
    AdultSpawn,
    WarpSong,
    BlueWarp,
    Extra,
}

pub(crate) fn module(py: Python<'_>) -> PyResult<Bound<'_, PyModule>> {
    let m = PyModule::new_bound(py, "entrance_shuffle")?;
    m.add_class::<EntranceKind>()?;
    Ok(m)
}
