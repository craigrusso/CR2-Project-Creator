//! Rust High Performance Engine for ForwardFlow
//! 
//! This module provides a high-performance file transfer engine written in Rust,
//! designed to replace the C++ implementation with better performance and cross-platform support.

pub mod data_structures;
pub mod engine_core;
pub mod file_operations;
pub mod verification;
pub mod progress_tracking;
pub mod cloud_detection;
pub mod platform_helpers;
pub mod event_system;
pub mod event_hub_v2;
pub mod strategy_engine;
pub mod blast_engine;
pub mod destination_processors;
pub mod python_bindings;

// Python module initialization
use pyo3::prelude::*;

/// Python module initialization
#[pymodule]
fn rust_high_perf_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    // Register all the Python classes and functions
    data_structures::register_python_types(m)?;
    engine_core::register_python_types(m)?;
    file_operations::register_python_types(m)?;
    verification::register_python_types(m)?;
    progress_tracking::register_python_types(m)?;
    cloud_detection::register_python_types(m)?;
    event_system::register_python_types(m)?;
    strategy_engine::register_python_types(m)?;
    blast_engine::register_python_types(m)?;
    destination_processors::register_python_types(m)?;
    
    // Register the high-level Python bindings (TransferStrategyEngine, etc.)
    python_bindings::register_python_types(m)?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_functionality() {
        // Basic test to ensure the module compiles and loads
        assert!(true);
    }
}
