//! Shared types for multi-destination copy engine

use std::path::PathBuf;
use std::sync::Arc;
use crate::verification::HashAlgorithm;

/// Outcome for a single destination after file copy
#[derive(Debug, Clone)]
pub struct DestinationOutcome {
    pub dest_index: usize,
    pub dest_path: String,
    pub relative_path: PathBuf,
    pub bytes_written: u64,
    pub dest_hash: Option<String>,
    pub duration_ms: u64,
    pub error: Option<String>,
}

/// Complete outcome for a file copied to multiple destinations
#[derive(Debug, Clone)]
pub struct MultiDestFileOutcome {
    pub source_path: PathBuf,
    pub relative_path: PathBuf,
    pub file_size: u64,
    pub source_hash: String,
    pub destinations: Vec<DestinationOutcome>,
}

/// Progress callback data for chunk-level tracking
pub struct ChunkProgress {
    pub file_index: usize,
    pub chunk_bytes: u64,
}

/// Commands sent from producer to destination workers
pub(crate) enum WorkerCommand {
    StartFile {
        relative_path: PathBuf,
        hash_algorithm: HashAlgorithm,
    },
    Chunk {
        data: Arc<Vec<u8>>,
    },
    FinishFile,
}

/// Result sent from destination worker back to engine
pub(crate) struct WorkerResult {
    pub dest_index: usize,
    pub dest_path: String,
    pub relative_path: PathBuf,
    pub bytes_written: u64,
    pub dest_hash: Option<String>,
    pub duration_ms: u64,
    pub error: Option<String>,
}
