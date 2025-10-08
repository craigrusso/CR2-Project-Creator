//! Legacy multi_dest_copy module - re-exports from new modular multi_dest
//!
//! This module provides backward compatibility by re-exporting types from
//! the new modular multi_dest implementation.

// Re-export all public types from the new multi_dest module
pub use crate::multi_dest::{
    ChunkProgress,
    DestinationOutcome,
    MultiDestCopyEngine,
    MultiDestFileOutcome,
};

