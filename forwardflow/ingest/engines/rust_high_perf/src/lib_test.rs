//! Test-only version of the Rust High Performance Engine
//! 
//! This module provides access to engine components without Python dependencies
//! for testing and development purposes.

pub mod event_hub_v2;
pub mod strategy_engine;
pub mod blast_engine;

// Re-export for testing
pub use event_hub_v2::*;
pub use strategy_engine::*;
pub use blast_engine::*;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_functionality() {
        // Basic test to ensure the module compiles and loads
        assert!(true);
    }
}