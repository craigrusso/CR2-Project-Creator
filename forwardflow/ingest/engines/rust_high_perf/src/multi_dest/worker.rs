//! Destination worker for independent-speed file writing

use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Instant;
use crossbeam_channel::{Receiver, Sender};

use crate::verification::HashAlgorithm;
use super::types::{WorkerCommand, WorkerResult};
use super::hasher::StreamingHasher;
use super::channel_manager::MonitoredSender;

/// Worker that writes files to a specific destination
pub(crate) struct DestinationWorker {
    dest_index: usize,
    dest_root: PathBuf,
    commands: Receiver<WorkerCommand>,
    results: Sender<WorkerResult>,
    cancelled: Arc<AtomicBool>,
    /// Monitored sender for memory tracking
    sender: Option<MonitoredSender>,
}

impl DestinationWorker {
    pub fn new(
        dest_index: usize,
        dest_root: PathBuf,
        commands: Receiver<WorkerCommand>,
        results: Sender<WorkerResult>,
        cancelled: Arc<AtomicBool>,
        sender: MonitoredSender,
    ) -> Self {
        Self {
            dest_index,
            dest_root,
            commands,
            results,
            cancelled,
            sender: Some(sender),
        }
    }

    pub fn run(mut self) {
        let mut state = Option::<ActiveFile>::None;

        while let Ok(command) = self.commands.recv() {
            if self.cancelled.load(Ordering::Relaxed) {
                break;
            }

            match command {
                WorkerCommand::StartFile {
                    relative_path,
                    hash_algorithm,
                } => {
                    state = self.start_file(relative_path, hash_algorithm);
                }
                WorkerCommand::Chunk { data } => {
                    let chunk_size = data.len();

                    if let Some(active) = state.as_mut() {
                        active.write(data.as_ref());
                    }

                    // CRITICAL: Decrease memory counter after consuming chunk
                    if let Some(sender) = &self.sender {
                        sender.decrease_memory(chunk_size);
                    }
                }
                WorkerCommand::FinishFile => {
                    let result = state
                        .take()
                        .map(|active| active.finish())
                        .unwrap_or_else(|| WorkerResult {
                            dest_index: self.dest_index,
                            dest_path: self.dest_root.to_string_lossy().into_owned(),
                            relative_path: PathBuf::new(),
                            bytes_written: 0,
                            dest_hash: None,
                            duration_ms: 0,
                            error: Some(
                                "destination worker finished without active file".to_string(),
                            ),
                        });

                    let _ = self.results.send(result);
                }
            }
        }

        if let Some(active) = state.take() {
            let _ = self.results.send(active.finish());
        }
    }

    fn start_file(
        &self,
        relative_path: PathBuf,
        hash_algorithm: HashAlgorithm,
    ) -> Option<ActiveFile> {
        let destination_path = self.dest_root.join(&relative_path);
        if let Some(parent) = destination_path.parent() {
            if let Err(err) = std::fs::create_dir_all(parent) {
                let _ = self.results.send(WorkerResult {
                    dest_index: self.dest_index,
                    dest_path: self.dest_root.to_string_lossy().into_owned(),
                    relative_path,
                    bytes_written: 0,
                    dest_hash: None,
                    duration_ms: 0,
                    error: Some(format!("failed to create destination directory: {err}")),
                });
                return None;
            }
        }

        match OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&destination_path)
        {
            Ok(file) => Some(ActiveFile::new(
                self.dest_index,
                self.dest_root.to_string_lossy().into_owned(),
                relative_path,
                file,
                hash_algorithm,
            )),
            Err(err) => {
                let _ = self.results.send(WorkerResult {
                    dest_index: self.dest_index,
                    dest_path: self.dest_root.to_string_lossy().into_owned(),
                    relative_path,
                    bytes_written: 0,
                    dest_hash: None,
                    duration_ms: 0,
                    error: Some(format!("failed to open destination file: {err}")),
                });
                None
            }
        }
    }
}

/// Active file being written to a destination
struct ActiveFile {
    dest_index: usize,
    dest_path: String,
    relative_path: PathBuf,
    writer: BufWriter<File>,
    hasher: StreamingHasher,
    bytes_written: u64,
    start: Instant,
}

impl ActiveFile {
    fn new(
        dest_index: usize,
        dest_path: String,
        relative_path: PathBuf,
        file: File,
        hash_algorithm: HashAlgorithm,
    ) -> Self {
        Self {
            dest_index,
            dest_path,
            relative_path,
            writer: BufWriter::new(file),
            hasher: StreamingHasher::new(hash_algorithm),
            bytes_written: 0,
            start: Instant::now(),
        }
    }

    fn write(&mut self, data: &[u8]) {
        if let Err(err) = self.writer.write_all(data) {
            self.hasher.flag_error(format!("write failure: {err}"));
            return;
        }

        self.hasher.update(data);
        self.bytes_written += data.len() as u64;
    }

    fn finish(mut self) -> WorkerResult {
        let flush_error = self.writer.flush().err().map(|err| err.to_string());
        let error = self.hasher.take_error().or(flush_error);
        let dest_hash = if error.is_none() {
            Some(self.hasher.finish())
        } else {
            None
        };

        WorkerResult {
            dest_index: self.dest_index,
            dest_path: self.dest_path,
            relative_path: self.relative_path,
            bytes_written: self.bytes_written,
            dest_hash,
            duration_ms: self.start.elapsed().as_millis() as u64,
            error,
        }
    }
}
