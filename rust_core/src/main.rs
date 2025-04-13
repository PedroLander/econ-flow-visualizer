use pyo3::prelude::*;
use polars::prelude::*;
use std::error::Error;
use std::path::Path;

/// A Python module implemented in Rust.
#[pymodule]
fn rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(process_flows, m)?)?;
    Ok(())
}

#[pyfunction]
fn process_flows(imports_path: String, exports_path: String, year: i32) -> PyResult<Vec<(String, String, f64)>> {
    get_flow_data(Path::new(&imports_path), Path::new(&exports_path), year)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

fn process_tsv(file_path: &Path) -> Result<DataFrame, Box<dyn Error>> {
    // Read the TSV file using LazyFrame for better performance
    let df = LazyCsvReader::new(file_path)
        .with_separator(b'\t')
        .finish()?
        .collect()?;
    
    // Get the first column name and data
    let first_col_name = df.get_column_names()[0].to_string();
    let first_col = df.column(&first_col_name)?;
    
    // Split the first column by comma and extract metadata
    let metadata: Vec<_> = first_col
        .cast(&DataType::String)?
        .str()?
        .into_iter()
        .map(|opt_val| {
            opt_val
                .map(|val| val.split(',').map(String::from).collect::<Vec<_>>())
                .unwrap_or_default()
        })
        .collect();
    
    // Create series for each metadata field
    let metadata_cols = ["freq", "nace_r2", "c_exp", "unit", "geo"];
    let mut columns = Vec::with_capacity(metadata_cols.len() + df.width() - 1);
    
    // Process metadata columns
    for (idx, &col_name) in metadata_cols.iter().enumerate() {
        let values: Vec<String> = metadata
            .iter()
            .map(|row| row.get(idx).cloned().unwrap_or_default())
            .collect();
            
        columns.push(Series::new(col_name.into(), values).into());
    }
    
    // Add year columns (all columns except the first one)
    for name in df.get_column_names().iter().skip(1) {
        if let Ok(col) = df.column(name) {
            // Convert year columns to float64 and add to columns
            columns.push(col.cast(&DataType::Float64)?);
        }
    }
    
    // Create new DataFrame with all columns
    DataFrame::new(columns).map_err(|e| Box::new(e) as Box<dyn Error>)
}

fn get_flow_data(imports_path: &Path, exports_path: &Path, year: i32) -> Result<Vec<(String, String, f64)>, Box<dyn Error>> {
    let imports_df = process_tsv(imports_path)?;
    let exports_df = process_tsv(exports_path)?;
    
    let year_col = year.to_string();
    let mut flows = Vec::new();
    
    // Helper closure to process a dataframe
    let process_df = |df: &DataFrame, flow_type: &str| -> Result<Vec<(String, String, f64)>, Box<dyn Error>> {
        let mut results = Vec::new();
        
        // Get required columns and convert to proper types
        let nace_col = df.column("nace_r2")?
            .cast(&DataType::String)?;
        let values_col = df.column(&year_col)?
            .cast(&DataType::Float64)?;
        
        // Convert columns to Series for proper type access
        let nace_series = nace_col.cast(&DataType::String)?;
        let values_series = values_col.cast(&DataType::Float64)?;
        
        // Get string and float iterators
        let nace_iter = nace_series.str()?;
        let values_iter = values_series.f64()?;
        
        // Iterate over both columns simultaneously
        for (nace, value) in nace_iter.into_iter().zip(values_iter.into_iter()) {
            if let (Some(nace), Some(value)) = (nace, value) {
                if !value.is_nan() {
                    results.push((
                        nace.to_string(),
                        flow_type.to_string(),
                        value
                    ));
                }
            }
        }
        
        Ok(results)
    };
    
    // Process imports and exports
    flows.extend(process_df(&imports_df, "Total Imports")?);
    flows.extend(process_df(&exports_df, "Total Exports")?);
    
    Ok(flows)
}