//! Multi-destination copy engine with independent worker speeds and memory monitoring
//!
//! This module provides a refactored multi-destination copy engine that allows
//! each destination to transfer at its own speed, with memory monitoring to prevent OOM.
//!
//! ## Architecture
//!
//! - **Producer-Consumer Pattern**: Single producer reads source, multiple consumers write destinations
//! - **Unbounded Channels**: Workers don't block each other (fast destinations don't wait for slow ones)
//! - **Memory Monitoring**: Backpressure applied when queue memory exceeds limits
//! - **Independent Speeds**: USB at 768 MB/s, Desktop SSD at 3800 MB/s, Network at 100 MB/s - all simultaneously
//!
//! ## Modules
//!
//! - `types` - Shared data structures
//! - `hasher` - Streaming hash calculation
//! - `memory_monitor` - Queue memory monitoring and backpressure
//! - `channel_manager` - Monitored unbounded channels
//! - `worker` - Destination worker implementation
//! - `engine` - Main orchestration engine

pub mod types;
pub mod hasher;
pub mod memory_monitor;
pub mod channel_manager;
pub mod worker;
pub mod engine;

// Re-export public API
pub use engine::MultiDestCopyEngine;
pub use types::{ChunkProgress, DestinationOutcome, MultiDestFileOutcome};
