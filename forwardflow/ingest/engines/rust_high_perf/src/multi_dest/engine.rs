use std::fs::File;
use std::io::{BufReader, Read};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;

use anyhow::{Context, Result};
use crossbeam_channel::unbounded;

use super::channel_manager::create_monitored_channel;
use super::hasher::StreamingHasher;
use super::memory_monitor::MemoryMonitor;
use super::types::{ChunkProgress, DestinationOutcome, MultiDestFileOutcome, WorkerCommand};
use super::worker::DestinationWorker;
use crate::event_system::EventSystem;
use crate::verification::HashAlgorithm;

const DEFAULT_CHUNK_SIZE: usize = 8 * 1024 * 1024; // 8 MiB

/// Multi-destination copy engine with independent transfer speeds
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

        // Create memory monitor for backpressure
        let memory_monitor = MemoryMonitor::new(dest_count, self.chunk_size);

        // Create result channel
        let (result_tx, result_rx) = unbounded();
        let mut worker_handles = Vec::with_capacity(dest_count);
        let mut worker_senders = Vec::with_capacity(dest_count);

        // Spawn worker threads with monitored unbounded channels
        for (dest_index, dest_root) in destination_paths.iter().enumerate() {
            let memory_tracker = memory_monitor.get_tracker(dest_index);
            let (monitored_tx, command_rx) = create_monitored_channel(Arc::clone(&memory_tracker));
            
            let worker = DestinationWorker::new(
                dest_index,
                PathBuf::from(dest_root),
                command_rx,
                result_tx.clone(),
                Arc::clone(&self.cancelled),
                Some(memory_tracker),
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

        // Spawn background thread to collect worker results and emit events IMMEDIATELY
        // This allows workers to report completion at their own speed (INDEPENDENT!)
        let event_sys_clone = Arc::clone(&event_system);
        let hash_algo_str = hash_algorithm.to_string();
        let source_files_clone = source_files.to_vec();
        let relative_paths_clone = relative_paths.to_vec();
        let total_files = source_files.len();
        let dest_count = destination_paths.len();
        let dest_paths = destination_paths.to_vec();
        let start_time = std::time::Instant::now();
        
        // Calculate total expected bytes (sum of all source files * dest count)
        let total_source_bytes: u64 = source_files.iter()
            .filter_map(|f| f.metadata().ok())
            .map(|m| m.len())
            .sum();
        let total_expected_bytes = total_source_bytes * dest_count as u64;
        
        let result_collector = thread::spawn(move || {
            // Track per-destination completion counts and bytes
            let mut dest_file_counts = vec![0usize; dest_count];
            let mut dest_byte_counts = vec![0u64; dest_count];
            
            while let Ok(result) = result_rx.recv() {
                // Emit file.completed event IMMEDIATELY when this worker finishes
                if let Ok(event_sys) = event_sys_clone.lock() {
                    let filename = result.relative_path
                        .file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("unknown");
                    
                    // Find the source file for this relative path
                    let source_path_str = relative_paths_clone
                        .iter()
                        .position(|p| p == &result.relative_path)
                        .and_then(|idx| source_files_clone.get(idx))
                        .map(|p| p.to_string_lossy().to_string())
                        .unwrap_or_default();
                    
                    let full_dest_path = std::path::Path::new(&result.dest_path)
                        .join(&result.relative_path);
                    
                    let dest_path_str = full_dest_path.to_string_lossy().to_string();
                    
                    // Extract hash or use empty string
                    let empty_hash = String::new();
                    let source_hash = result.dest_hash.as_ref().unwrap_or(&empty_hash);
                    let dest_hash = result.dest_hash.as_ref().unwrap_or(&empty_hash);
                    let verification_passed = result.error.is_none() && !source_hash.is_empty();
                    
                    let _ = event_sys.emit_file_completed_with_hash(
                        filename,
                        &source_path_str,
                        &dest_path_str,
                        result.dest_index,
                        result.bytes_written,
                        source_hash,
                        dest_hash,
                        &hash_algo_str,
                        verification_passed,
                    );
                    
                    eprintln!(
                        "✅ INDEPENDENT: Dest #{} finished {} ({} bytes in {} ms)",
                        result.dest_index, filename, result.bytes_written, result.duration_ms
                    );
                    
                    // CRITICAL FIX: Track per-destination completion and emit DestCompleted when done
                    if result.dest_index < dest_count {
                        dest_file_counts[result.dest_index] += 1;
                        dest_byte_counts[result.dest_index] += result.bytes_written;
                        
                        // CRITICAL FIX: Emit JobProgress based on CONSUMER bytes (aggregate of all destinations)
                        // This keeps the main progress bar updating even after producer finishes
                        let elapsed = start_time.elapsed().as_secs_f64();
                        let total_consumer_bytes: u64 = dest_byte_counts.iter().sum();
                        let total_consumer_files: usize = dest_file_counts.iter().sum();
                        let total_target_bytes = total_expected_bytes; // Will be updated by first file
                        let speed_mbps = if elapsed > 0.0 {
                            (total_consumer_bytes as f64 / elapsed) / (1024.0 * 1024.0)
                        } else {
                            0.0
                        };
                        
                        let _ = event_sys.emit_job_progress(
                            total_consumer_bytes,
                            total_target_bytes,
                            total_consumer_files,
                            total_files * dest_count,
                            elapsed,
                            speed_mbps,
                        );
                        
                        // Check if this destination has finished all files
                        if dest_file_counts[result.dest_index] >= total_files {
                            let dest_path = &dest_paths[result.dest_index];
                            
                            eprintln!(
                                "🎯🎯🎯 MULTI_DEST: Dest #{} ({}) COMPLETED - {} files, {} bytes, {:.1}s elapsed",
                                result.dest_index, dest_path, dest_file_counts[result.dest_index],
                                dest_byte_counts[result.dest_index], elapsed
                            );
                            
                            let _ = event_sys.emit_dest_completed(
                                result.dest_index,
                                &dest_path,
                                dest_byte_counts[result.dest_index],
                                dest_byte_counts[result.dest_index], // total_bytes same as copied for this dest
                                dest_file_counts[result.dest_index],
                                total_files,
                                elapsed,
                            );
                        }
                    }
                }
            }
            eprintln!("🏁 Background result collector thread finished");
        });

        let mut outcomes = Vec::with_capacity(source_files.len());
        let mut chunk_buffer = vec![0u8; self.chunk_size];

        // Process each source file
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

            // Send StartFile to all destinations
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

            // Read and broadcast chunks
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
                    let total_mb = memory_monitor.total_memory_mb();
                    if let Some(slowest) = memory_monitor.slowest_destination() {
                        let slowest_mb = memory_monitor.dest_memory_mb(slowest);
                        eprintln!(
                            "⚠️  Backpressure: Total queue {:.1} MB, slowest dest #{} has {:.1} MB queued",
                            total_mb, slowest, slowest_mb
                        );
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

            // Signal file completion to all workers
            for sender in &worker_senders {
                let _ = sender.send(WorkerCommand::FinishFile);
            }

            // ❌ OLD: Blocked here waiting for ALL destinations to finish (SERIAL!)
            // ✅ NEW: Don't wait - let workers finish at their own speed (PARALLEL!)
            //
            // Background thread collects worker results and emits file.completed IMMEDIATELY.
            // Fast workers get ahead, slow workers fall behind.
            // Progress reporting is now truly independent per destination!

            // Track file outcome (events emitted asynchronously by background thread)
            if file_completed {
                let source_hash = source_hasher.finish();

                eprintln!(
                    "📤 Producer sent file {} to all destinations - moving to next file immediately",
                    relative_path.display()
                );

                outcomes.push(MultiDestFileOutcome {
                    source_path: source_path.clone(),
                    relative_path,
                    file_size,
                    source_hash,
                    destinations: Vec::new(),  // Workers report independently via background thread
                });
            } else {
                eprintln!(
                    "⚠️  MULTI_DEST: File {} was cancelled mid-copy - NO hash",
                    relative_path.display()
                );
            }

            // Break if cancelled during this file
            if was_cancelled {
                break;
            }
        }

        // Clean up: drop senders to signal workers to exit
        drop(worker_senders);

        // Wait for all workers to complete
        for handle in worker_handles {
            let _ = handle.join();
        }

        // Wait for background result collector to finish processing all worker results
        // (result_rx is owned by the background thread and will close when all workers exit)
        let _ = result_collector.join();

        eprintln!("✅ All workers and result collector finished - transfer complete");

        Ok(outcomes)
    }
}

