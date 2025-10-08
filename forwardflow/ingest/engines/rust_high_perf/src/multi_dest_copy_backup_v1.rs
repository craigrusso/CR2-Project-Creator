use std::fs::{File, OpenOptions};
use std::hash::Hasher;
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Instant;

use anyhow::{Context, Result};
use crossbeam_channel::{bounded, unbounded, Receiver, Sender};
use sha2::Digest as Sha2Digest;
use sha3::Digest as Sha3Digest;

use crate::event_system::EventSystem;
use crate::verification::HashAlgorithm;

const DEFAULT_CHUNK_SIZE: usize = 8 * 1024 * 1024; // 8 MiB
const QUEUE_DEPTH: usize = 8;

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

#[derive(Debug, Clone)]
pub struct MultiDestFileOutcome {
    pub source_path: PathBuf,
    pub relative_path: PathBuf,
    pub file_size: u64,
    pub source_hash: String,
    pub destinations: Vec<DestinationOutcome>,
}

pub struct MultiDestCopyEngine {
    cancelled: Arc<AtomicBool>,
    chunk_size: usize,
}

pub struct ChunkProgress {
    pub file_index: usize,
    pub chunk_bytes: u64,
}

impl MultiDestCopyEngine {
    pub fn new(cancelled: Arc<AtomicBool>, chunk_size: Option<usize>) -> Self {
        Self {
            cancelled,
            chunk_size: chunk_size.unwrap_or(DEFAULT_CHUNK_SIZE),
        }
    }

    pub fn copy<F>(
        &self,
        source_files: &[PathBuf],
        relative_paths: &[PathBuf],
        destination_paths: &[String],
        hash_algorithm: HashAlgorithm,
        event_system: Arc<Mutex<EventSystem>>,
        mut progress_cb: F,
    ) -> Result<Vec<MultiDestFileOutcome>>
    where
        F: FnMut(ChunkProgress) -> bool,
    {
        if source_files.len() != relative_paths.len() {
            anyhow::bail!("Relative paths length mismatch");
        }

        let dest_count = destination_paths.len();
        if dest_count == 0 {
            return Ok(Vec::new());
        }

        let (result_tx, result_rx) = unbounded();
        let mut worker_handles = Vec::with_capacity(dest_count);
        let mut worker_senders = Vec::with_capacity(dest_count);

        for (dest_index, dest_root) in destination_paths.iter().enumerate() {
            let (command_tx, command_rx) = bounded(QUEUE_DEPTH);
            let worker = DestinationWorker::new(
                dest_index,
                PathBuf::from(dest_root),
                command_rx,
                result_tx.clone(),
                Arc::clone(&self.cancelled),
            );

            let thread_name = format!("ff-multi-dest-{}", dest_index);
            let handle = thread::Builder::new()
                .name(thread_name)
                .spawn(move || worker.run())
                .context("failed to spawn destination worker thread")?;

            worker_handles.push(handle);
            worker_senders.push(command_tx);
        }

        drop(result_tx);

        let mut outcomes = Vec::with_capacity(source_files.len());
        let mut chunk_buffer = vec![0u8; self.chunk_size];

        for (idx, source_path) in source_files.iter().enumerate() {
            // Check for cancellation before starting new file
            if self.cancelled.load(Ordering::Relaxed) {
                break;
            }

            let relative_path = relative_paths[idx].clone();
            let file_size = source_path
                .metadata()
                .with_context(|| format!("failed to stat {}", source_path.display()))?
                .len();

            let mut source_reader = BufReader::new(
                File::open(source_path)
                    .with_context(|| format!("failed to open {}", source_path.display()))?,
            );
            let mut source_hasher = StreamingHasher::new(hash_algorithm.clone());

            for sender in &worker_senders {
                sender
                    .send(WorkerCommand::StartFile {
                        relative_path: relative_path.clone(),
                        hash_algorithm: hash_algorithm.clone(),
                    })
                    .context("failed to dispatch StartFile command")?;
            }

            let mut file_completed = false;
            let mut was_cancelled = false;

            loop {
                let bytes_read = source_reader.read(&mut chunk_buffer)?;
                if bytes_read == 0 {
                    file_completed = true;
                    break;
                }

                source_hasher.update(&chunk_buffer[..bytes_read]);
                let mut owned_chunk = Vec::with_capacity(bytes_read);
                owned_chunk.extend_from_slice(&chunk_buffer[..bytes_read]);
                let shared_chunk = Arc::new(owned_chunk);

                // Send chunk BEFORE checking cancellation
                for sender in &worker_senders {
                    sender
                        .send(WorkerCommand::Chunk {
                            data: Arc::clone(&shared_chunk),
                        })
                        .context("failed to dispatch chunk to destination worker")?;
                }

                // Check for cancellation AFTER sending chunk
                if progress_cb(ChunkProgress {
                    file_index: idx,
                    chunk_bytes: bytes_read as u64,
                }) || self.cancelled.load(Ordering::Relaxed)
                {
                    was_cancelled = true;
                    break;
                }
            }

            // Always finish the file to keep workers in sync
            for sender in &worker_senders {
                let _ = sender.send(WorkerCommand::FinishFile);
            }

            let mut destination_results = Vec::with_capacity(dest_count);
            for _ in 0..dest_count {
                if let Ok(result) = result_rx.recv() {
                    destination_results.push(DestinationOutcome {
                        dest_index: result.dest_index,
                        dest_path: result.dest_path,
                        relative_path: result.relative_path,
                        bytes_written: result.bytes_written,
                        dest_hash: result.dest_hash,
                        duration_ms: result.duration_ms,
                        error: result.error,
                    });
                }
            }

            // Only add outcome if file completed successfully (not cancelled mid-file)
            if file_completed {
                let source_hash = source_hasher.finish();
                let source_hash_hex = source_hash.clone();

                // CRITICAL FIX: Emit FileCompleted events IMMEDIATELY for real-time DIT reporting
                // Don't wait until all files finish - emit as each completes
                let _ = std::fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open("/tmp/rust_engine_debug.log")
                    .and_then(|mut f| std::io::Write::write_all(&mut f,
                        format!("🎉 File completed: {} - emitting events for {} destinations\n",
                            relative_path.display(), destination_results.len()).as_bytes()));

                if let Ok(event_sys) = event_system.lock() {
                    for dest in &destination_results {
                        let filename = relative_path.file_name()
                            .and_then(|n| n.to_str())
                            .unwrap_or("unknown");

                        let full_dest_path = std::path::Path::new(&dest.dest_path).join(&dest.relative_path);
                        let dest_path_str = full_dest_path.to_string_lossy().to_string();
                        let source_path_str = source_path.to_string_lossy().to_string();

                        let dest_hash_hex = dest.dest_hash.clone().unwrap_or_default();
                        let verification_passed = dest.error.is_none() && !dest_hash_hex.is_empty();

                        let _ = event_sys.emit_file_completed_with_hash(
                            filename,
                            &source_path_str,
                            &dest_path_str,
                            dest.dest_index,
                            dest.bytes_written,
                            &source_hash_hex,
                            &dest_hash_hex,
                            &hash_algorithm.to_string(),
                            verification_passed,
                        );

                        let _ = std::fs::OpenOptions::new()
                            .create(true)
                            .append(true)
                            .open("/tmp/rust_engine_debug.log")
                            .and_then(|mut f| std::io::Write::write_all(&mut f,
                                format!("  ✅ Emitted FileCompleted for dest {}: {}\n", dest.dest_index, filename).as_bytes()));
                    }
                }

                outcomes.push(MultiDestFileOutcome {
                    source_path: source_path.clone(),
                    relative_path,
                    file_size,
                    source_hash,
                    destinations: destination_results,
                });
            } else {
                eprintln!("⚠️  MULTI_DEST: File {} was cancelled mid-copy - NO hash", relative_path.display());
            }

            // Break if cancelled during this file
            if was_cancelled {
                break;
            }
        }

        drop(worker_senders);

        for handle in worker_handles {
            let _ = handle.join();
        }

        Ok(outcomes)
    }
}

enum WorkerCommand {
    StartFile {
        relative_path: PathBuf,
        hash_algorithm: HashAlgorithm,
    },
    Chunk {
        data: Arc<Vec<u8>>,
    },
    FinishFile,
}

struct WorkerResult {
    dest_index: usize,
    dest_path: String,
    relative_path: PathBuf,
    bytes_written: u64,
    dest_hash: Option<String>,
    duration_ms: u64,
    error: Option<String>,
}

struct DestinationWorker {
    dest_index: usize,
    dest_root: PathBuf,
    commands: Receiver<WorkerCommand>,
    results: Sender<WorkerResult>,
    cancelled: Arc<AtomicBool>,
}

impl DestinationWorker {
    fn new(
        dest_index: usize,
        dest_root: PathBuf,
        commands: Receiver<WorkerCommand>,
        results: Sender<WorkerResult>,
        cancelled: Arc<AtomicBool>,
    ) -> Self {
        Self {
            dest_index,
            dest_root,
            commands,
            results,
            cancelled,
        }
    }

    fn run(mut self) {
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
                    if let Some(active) = state.as_mut() {
                        active.write(data.as_ref());
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

struct StreamingHasher {
    algorithm: HashAlgorithm,
    inner: StreamingHasherKind,
    error: Option<String>,
}

enum StreamingHasherKind {
    Xxh3(xxhash_rust::xxh3::Xxh3),
    Sha256(sha2::Sha256),
    Sha3(sha3::Sha3_256),
    Md5(md5::Context),
    Blake3(blake3::Hasher),
}

impl StreamingHasher {
    fn new(algorithm: HashAlgorithm) -> Self {
        let inner = match algorithm {
            HashAlgorithm::XxHash64 | HashAlgorithm::XxHash64BE | HashAlgorithm::XxHash128 => {
                StreamingHasherKind::Xxh3(xxhash_rust::xxh3::Xxh3::new())
            }
            HashAlgorithm::Sha256 => StreamingHasherKind::Sha256(sha2::Sha256::new()),
            HashAlgorithm::Sha3 => StreamingHasherKind::Sha3(sha3::Sha3_256::new()),
            HashAlgorithm::Md5 => StreamingHasherKind::Md5(md5::Context::new()),
            HashAlgorithm::Blake3 => StreamingHasherKind::Blake3(blake3::Hasher::new()),
        };

        Self {
            algorithm,
            inner,
            error: None,
        }
    }

    fn update(&mut self, data: &[u8]) {
        if self.error.is_some() {
            return;
        }

        match &mut self.inner {
            StreamingHasherKind::Xxh3(hasher) => hasher.update(data),
            StreamingHasherKind::Sha256(hasher) => Sha2Digest::update(hasher, data),
            StreamingHasherKind::Sha3(hasher) => Sha3Digest::update(hasher, data),
            StreamingHasherKind::Md5(ctx) => ctx.consume(data),
            StreamingHasherKind::Blake3(hasher) => {
                hasher.update(data);
            }
        }
    }

    fn flag_error(&mut self, message: String) {
        self.error.get_or_insert(message);
    }

    fn take_error(&mut self) -> Option<String> {
        self.error.take()
    }

    fn finish(mut self) -> String {
        match self.inner {
            StreamingHasherKind::Xxh3(hasher) => match self.algorithm {
                HashAlgorithm::XxHash128 => format!("{:032x}", hasher.finish()),
                _ => format!("{:016x}", hasher.finish()),
            },
            StreamingHasherKind::Sha256(hasher) => format!("{:x}", Sha2Digest::finalize(hasher)),
            StreamingHasherKind::Sha3(hasher) => format!("{:x}", Sha3Digest::finalize(hasher)),
            StreamingHasherKind::Md5(ctx) => format!("{:x}", ctx.compute()),
            StreamingHasherKind::Blake3(hasher) => hasher.finalize().to_hex().to_string(),
        }
    }
}
