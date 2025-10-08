// Public API for multi-destination copy engine
pub use engine::MultiDestCopyEngine;
pub use types::{ChunkProgress, DestinationOutcome, MultiDestFileOutcome};

// Internal modules
mod channel_manager;
mod engine;
mod hasher;
mod memory_monitor;
mod types;
mod worker;

