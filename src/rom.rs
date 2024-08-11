use {
    std::path::PathBuf,
    pyo3::{
        exceptions::PyValueError,
        prelude::*,
    },
    wheel::traits::IoResultExt as _,
};

#[pyfunction]
fn decompress_rom(input_file: PathBuf, output_file: PathBuf) -> PyResult<()> {
    let mut in_rom = std::fs::read(&input_file).at(&input_file)?;
    if in_rom.len() != 0x0200_0000 {
        return Err(PyValueError::new_err(format!("{} is not the correct size", input_file.display())))
    }
    let out_rom = decompress::decompress(&mut in_rom).map_err(|e| match e {
        decompress::Error::InputSize(path) => PyValueError::new_err(format!("{} is not the correct size", path.display())),
        decompress::Error::TableNotFound => PyValueError::new_err("Couldn't find table"),
        decompress::Error::TryFromInt(e) => e.into(),
        decompress::Error::Wheel(e) => e.into(),
    })?;
    std::fs::write(&output_file, out_rom).at(output_file)?;
    Ok(())
}

pub(crate) fn module(py: Python<'_>) -> PyResult<Bound<'_, PyModule>> {
    let m = PyModule::new_bound(py, "rom")?;
    m.add_function(wrap_pyfunction!(decompress_rom, m.clone())?)?;
    Ok(m)
}
