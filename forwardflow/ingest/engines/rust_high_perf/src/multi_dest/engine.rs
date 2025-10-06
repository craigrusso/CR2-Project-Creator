//! Multi-destination copy engine with independent-speed workers and memory monitoring

use std::fs::File;
use std::io::{BufReader, Read};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;

use anyhow::{Context, Result};
use crossbeam_channel::unbounded;

use crate::event_system::EventSystem;
use crate::verification::HashAlgorithm;

use super::types::{ChunkProgress, DestinationOutcome, MultiDestFileOutcome, WorkerCommand};
use super::worker::DestinationWorker;
use super::hasher::StreamingHasher;
use super::memory_monitor::MemoryMonitor;
use super::channel_manager::create_monitored_channel;

const DEFAULT_CHUNK_SIZE: usize = 8 * 1024 * 1024; // 8 MiB

/// Multi-destination copy engine with independent worker speeds
pub struct MultiDestCopyEngine {
    cancelled: Arc<AtomicBool>,
    chunk_size: usize,
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

        // Create memory monitor for backpressure control
        let memory_monitor = MemoryMonitor::new(dest_count, self.chunk_size);

        let (result_tx, result_rx) = unbounded();
        let mut worker_handles = Vec::with_capacity(dest_count);
        let mut worker_senders = Vec::with_capacity(dest_count);

        // Spawn independent workers with monitored unbounded channels
        for (dest_index, dest_root) in destination_paths.iter().enumerate() {
            let memory_tracker = memory_monitor.get_tracker(dest_index);
            let (monitored_tx, command_rx) = create_monitored_channel(memory_tracker, self.chunk_size);

            let worker = DestinationWorker::new(
                dest_index,
                PathBuf::from(dest_root),
                command_rx,
                result_tx.clone(),
                Arc::clone(&self.cancelled),
                monitored_tx.clone_sender(),
            );

            let thread_name = format!("ff-multi-dest-{}", dest_index);
            let handle = thread::Builder::new()
                .name(thread_name)
                .spawn(move || worker.run())
                .context("failed to spawn destination worker thread")?;

            worker_handles.push(handle);
            worker_senders.push(monitored_tx);
        }

        drop(result_tx);

        let mut outcomes = Vec::with_capacity(source_files.len());
        let mut chunk_buffer = vec![0u8; self.chunk_size];
        let mut backpressure_count = 0;

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

                // Send chunk to ALL destinations (unbounded, non-blocking)
                for sender in &worker_senders {
                    sender
                        .send(WorkerCommand::Chunk {
                            data: Arc::clone(&shared_chunk),
                        })
                        .context("failed to dispatch chunk to destination worker")?;
                }

                // Apply backpressure if any destination queue is too large
                if memory_monitor.should_backpressure() {
                    backpressure_count += 1;
                    if backpressure_count % 100 == 1 {
                        let stats = memory_monitor.get_stats();
                        println!("⚠️  Backpressure applied: Total memory {:.1} MB, Max dest {:.1} MB",
                            stats.total_mb, stats.max_dest_mb);
                    }
                    memory_monitor.apply_backpressure();
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

                // Emit FileCompleted events IMMEDIATELY for real-time DIT reporting
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
                    }
                }

                outcomes.push(MultiDestFileOutcome {
                    source_path: source_path.clone(),
                    relative_path,
                    file_size,
                    source_hash,
                    destinations: destination_results,
                });
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

        if backpressure_count > 0 {
            println!("✅ Transfer complete - Applied backpressure {} times (memory protection)", backpressure_count);
        }

        Ok(outcomes)
    }
}
