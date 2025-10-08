use std::path::PathBuf;
use std::sync::Arc;

use crate::verification::HashAlgorithm;

/// Outcome for a single destination's copy operation
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

/// Outcome for a file copied to multiple destinations
#[derive(Debug, Clone)]
pub struct MultiDestFileOutcome {
    pub source_path: PathBuf,
    pub relative_path: PathBuf,
    pub file_size: u64,
    pub source_hash: String,
    pub destinations: Vec<DestinationOutcome>,
}

/// Progress report for a chunk being processed
pub struct ChunkProgress {
    pub file_index: usize,
    pub chunk_bytes: u64,
}

/// Commands sent to destination workers
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

/// Result from destination worker
pub(crate) struct WorkerResult {
    pub dest_index: usize,
    pub dest_path: String,
    pub relative_path: PathBuf,
    pub bytes_written: u64,
    pub dest_hash: Option<String>,
    pub duration_ms: u64,
    pub error: Option<String>,
}

