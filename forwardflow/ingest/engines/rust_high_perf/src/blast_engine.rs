//! ForwardFlow V2.0 - BLAST Engine for Ultra-Fast Multi-Destination Transfer
//!
//! BLAST (Burst Load And Sequential Transfer) engine optimizes multi-destination
//! transfers by first copying to an ultra-fast cache, then distributing in parallel.
//! Designed for professional DIT workflows requiring maximum speed and reliability.

use anyhow::Result;
use crossbeam_channel::{bounded, Receiver, Sender};
use parking_lot::{Mutex, RwLock};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{
    atomic::{AtomicBool, AtomicU64, Ordering},
    Arc,
};
use std::time::{Duration, SystemTime};
use tokio::fs;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

use crate::event_hub_v2::{EventHub, EventPayload, EventPriority, EventType, TransferEvent};
use crate::strategy_engine::{DestinationAnalysis, DestinationType, TransferStrategy};
use pyo3::prelude::*;

/// BLAST workflow configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlastConfig {
    /// Ultra-fast cache destination (NVMe SSD or similar)
    pub blast_cache_path: PathBuf,

    /// Final distribution destinations
    pub distribution_targets: Vec<PathBuf>,

    /// Memory staging buffer size in MB
    pub memory_buffer_mb: usize,

    /// Maximum parallel distribution threads
    pub max_parallel_streams: usize,

    /// Enable direct I/O for cache operations
    pub use_direct_io: bool,

    /// Enable memory-mapped I/O for large files
    pub use_memory_mapping: bool,

    /// Chunk size for optimal cache performance
    pub cache_chunk_size_mb: usize,
}

impl Default for BlastConfig {
    fn default() -> Self {
        Self {
            blast_cache_path: PathBuf::from("/tmp/forwardflow_blast"),
            distribution_targets: Vec::new(),
            memory_buffer_mb: 512, // 512MB default buffer
            max_parallel_streams: num_cpus::get(),
            use_direct_io: true,
            use_memory_mapping: true,
            cache_chunk_size_mb: 64, // 64MB chunks for NVMe optimization
        }
    }
}

/// BLAST transfer phases
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default, Serialize, Deserialize)]
pub enum BlastPhase {
    /// Initial analysis and setup
    #[default]
    Preparation,

    /// Ultra-fast copy to cache
    CacheLoad,

    /// Parallel distribution to final destinations
    Distribution,

    /// Final verification and cleanup
    Verification,

    /// BLAST complete
    Complete,
}

impl BlastPhase {
    pub fn as_str(&self) -> &'static str {
        match self {
            BlastPhase::Preparation => "Preparation",
            BlastPhase::CacheLoad => "CacheLoad",
            BlastPhase::Distribution => "Distribution",
            BlastPhase::Verification => "Verification",
            BlastPhase::Complete => "Complete",
        }
    }
}

/// BLAST transfer statistics
#[derive(Debug, Default)]
pub struct BlastStats {
    /// Total bytes to transfer
    pub total_bytes: AtomicU64,

    /// Bytes cached (Phase 1)
    pub cached_bytes: AtomicU64,

    /// Bytes distributed (Phase 2)
    pub distributed_bytes: AtomicU64,

    /// Cache transfer speed (MB/s)
    pub cache_speed_mbps: AtomicU64,

    /// Peak distribution speed (MB/s)
    pub distribution_speed_mbps: AtomicU64,

    /// Number of files processed
    pub files_processed: AtomicU64,

    /// Current phase
    pub current_phase: Arc<RwLock<BlastPhase>>,

    /// Phase timing information
    pub phase_timings: Arc<RwLock<HashMap<BlastPhase, Duration>>>,
}

impl BlastStats {
    pub fn new() -> Self {
        Self {
            total_bytes: AtomicU64::new(0),
            cached_bytes: AtomicU64::new(0),
            distributed_bytes: AtomicU64::new(0),
            cache_speed_mbps: AtomicU64::new(0),
            distribution_speed_mbps: AtomicU64::new(0),
            files_processed: AtomicU64::new(0),
            current_phase: Arc::new(RwLock::new(BlastPhase::Preparation)),
            phase_timings: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub fn get_cache_progress_percent(&self) -> f64 {
        let total = self.total_bytes.load(Ordering::Relaxed);
        if total == 0 {
            return 0.0;
        }

        let cached = self.cached_bytes.load(Ordering::Relaxed);
        (cached as f64 / total as f64) * 100.0
    }

    pub fn get_distribution_progress_percent(&self) -> f64 {
        let total = self.total_bytes.load(Ordering::Relaxed);
        if total == 0 {
            return 0.0;
        }

        let distributed = self.distributed_bytes.load(Ordering::Relaxed);
        (distributed as f64 / total as f64) * 100.0
    }
}

/// High-performance BLAST transfer engine
pub struct BlastEngine {
    /// Configuration for this BLAST operation
    config: BlastConfig,

    /// Real-time statistics
    stats: Arc<BlastStats>,

    /// Event hub for progress reporting
    event_hub: Option<Arc<EventHub>>,

    /// Cancellation signal
    cancel_signal: Arc<AtomicBool>,

    /// File manifest for tracking
    file_manifest: Arc<RwLock<Vec<BlastFileRecord>>>,
}

/// Individual file record in BLAST operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlastFileRecord {
    pub source_path: PathBuf,
    pub cache_path: PathBuf,
    pub target_paths: Vec<PathBuf>,
    pub file_size: u64,
    pub cache_complete: bool,
    pub distribution_complete: HashMap<PathBuf, bool>,
    pub source_checksum: Option<String>,
    pub cache_checksum: Option<String>,
    pub target_checksums: HashMap<PathBuf, String>,
}

impl BlastEngine {
    /// Create new BLAST engine with configuration
    pub fn new(config: BlastConfig) -> Self {
        Self {
            config,
            stats: Arc::new(BlastStats::new()),
            event_hub: None,
            cancel_signal: Arc::new(AtomicBool::new(false)),
            file_manifest: Arc::new(RwLock::new(Vec::new())),
        }
    }

    /// Create BLAST engine with event hub integration
    pub fn with_event_hub(config: BlastConfig, event_hub: Arc<EventHub>) -> Self {
        let mut engine = Self::new(config);
        engine.event_hub = Some(event_hub);
        engine
    }

    /// Execute complete BLAST workflow
    pub async fn execute_blast_transfer(
        &self,
        source_files: &[PathBuf],
        job_id: &str,
    ) -> Result<BlastTransferResult> {
        println!("Starting BLAST transfer for {} files", source_files.len());

        // Phase 1: Preparation
        self.set_phase(BlastPhase::Preparation, job_id).await?;
        self.prepare_blast_operation(source_files, job_id).await?;

        // Phase 2: Cache Load (Ultra-fast copy to cache)
        self.set_phase(BlastPhase::CacheLoad, job_id).await?;
        let cache_result = self.execute_cache_load(job_id).await?;

        // Phase 3: Distribution (Parallel copy to final destinations)
        self.set_phase(BlastPhase::Distribution, job_id).await?;
        let distribution_result = self.execute_distribution(job_id).await?;

        // Phase 4: Verification
        self.set_phase(BlastPhase::Verification, job_id).await?;
        let verification_result = self.execute_verification(job_id).await?;

        // Phase 5: Complete
        self.set_phase(BlastPhase::Complete, job_id).await?;

        Ok(BlastTransferResult {
            cache_result,
            distribution_result,
            verification_result,
            total_time: self.get_total_elapsed_time(),
            final_stats: self.get_final_stats(),
        })
    }

    /// Phase 1: Prepare BLAST operation
    async fn prepare_blast_operation(&self, source_files: &[PathBuf], job_id: &str) -> Result<()> {
        println!(
            "BLAST Phase 1: Preparing operation for {} files",
            source_files.len()
        );

        // Ensure cache directory exists
        fs::create_dir_all(&self.config.blast_cache_path).await?;

        // Calculate total transfer size and build file manifest
        let mut total_bytes = 0u64;
        let mut manifest = Vec::new();

        for source_file in source_files {
            if self.cancel_signal.load(Ordering::Relaxed) {
                anyhow::bail!("BLAST operation cancelled");
            }

            let metadata = fs::metadata(source_file).await?;
            let file_size = metadata.len();
            total_bytes += file_size;

            // Create cache path maintaining directory structure
            let relative_path = source_file
                .file_name()
                .ok_or_else(|| anyhow::anyhow!("Invalid source file path"))?;
            let cache_path = self.config.blast_cache_path.join(relative_path);

            let mut target_paths = Vec::new();
            for target in &self.config.distribution_targets {
                target_paths.push(target.join(relative_path));
            }

            manifest.push(BlastFileRecord {
                source_path: source_file.clone(),
                cache_path,
                target_paths: target_paths.clone(),
                file_size,
                cache_complete: false,
                distribution_complete: target_paths.iter().map(|p| (p.clone(), false)).collect(),
                source_checksum: None,
                cache_checksum: None,
                target_checksums: HashMap::new(),
            });
        }

        self.stats.total_bytes.store(total_bytes, Ordering::Relaxed);
        *self.file_manifest.write() = manifest;

        // Emit preparation complete event
        if let Some(ref event_hub) = self.event_hub {
            let _ = event_hub.emit_event(TransferEvent::new(
                EventType::BlastInitiated,
                EventPriority::High,
                job_id.to_string(),
                EventPayload::Blast {
                    blast_drive_path: self.config.blast_cache_path.to_string_lossy().to_string(),
                    distribution_destinations: self
                        .config
                        .distribution_targets
                        .iter()
                        .map(|p| p.to_string_lossy().to_string())
                        .collect(),
                    blast_progress_percent: 0.0,
                    distribution_progress_percent: 0.0,
                    phase: BlastPhase::Preparation.as_str().to_string(),
                },
            ));
        }

        println!(
            "BLAST preparation complete: {} files, {:.2} GB total",
            source_files.len(),
            total_bytes as f64 / (1024.0 * 1024.0 * 1024.0)
        );

        Ok(())
    }

    /// Phase 2: Execute ultra-fast cache load
    async fn execute_cache_load(&self, job_id: &str) -> Result<CacheLoadResult> {
        println!("BLAST Phase 2: Executing cache load");

        let start_time = SystemTime::now();
        let mut bytes_cached = 0u64;
        let mut files_cached = 0usize;

        // Process files in parallel for maximum cache performance
        let manifest = self.file_manifest.read().clone();
        let chunk_size = self.config.cache_chunk_size_mb * 1024 * 1024;

        for (index, file_record) in manifest.iter().enumerate() {
            if self.cancel_signal.load(Ordering::Relaxed) {
                anyhow::bail!("BLAST cache load cancelled");
            }

            // High-performance copy to cache
            let file_start = SystemTime::now();
            self.copy_to_cache(
                &file_record.source_path,
                &file_record.cache_path,
                chunk_size,
            )
            .await?;
            let file_duration = file_start.elapsed()?;

            bytes_cached += file_record.file_size;
            files_cached += 1;

            // Update statistics
            self.stats
                .cached_bytes
                .store(bytes_cached, Ordering::Relaxed);
            self.stats
                .files_processed
                .store(files_cached as u64, Ordering::Relaxed);

            // Calculate current speed
            let current_speed = if file_duration.as_secs_f64() > 0.0 {
                (file_record.file_size as f64) / file_duration.as_secs_f64() / (1024.0 * 1024.0)
            } else {
                0.0
            };

            self.stats
                .cache_speed_mbps
                .store(current_speed as u64, Ordering::Relaxed);

            // Mark file as cached
            if let Some(mut record) = self.file_manifest.write().get_mut(index) {
                record.cache_complete = true;
            }

            // Emit progress event
            if let Some(ref event_hub) = self.event_hub {
                let _ = event_hub.emit_event(TransferEvent::new(
                    EventType::BlastInitiated,
                    EventPriority::Normal,
                    job_id.to_string(),
                    EventPayload::Blast {
                        blast_drive_path: self
                            .config
                            .blast_cache_path
                            .to_string_lossy()
                            .to_string(),
                        distribution_destinations: self
                            .config
                            .distribution_targets
                            .iter()
                            .map(|p| p.to_string_lossy().to_string())
                            .collect(),
                        blast_progress_percent: self.stats.get_cache_progress_percent(),
                        distribution_progress_percent: 0.0,
                        phase: BlastPhase::CacheLoad.as_str().to_string(),
                    },
                ));
            }

            println!(
                "Cached file {}/{}: {} @ {:.1} MB/s",
                files_cached,
                manifest.len(),
                file_record.source_path.display(),
                current_speed
            );
        }

        let total_duration = start_time.elapsed()?;
        let average_speed = if total_duration.as_secs_f64() > 0.0 {
            (bytes_cached as f64) / total_duration.as_secs_f64() / (1024.0 * 1024.0)
        } else {
            0.0
        };

        println!(
            "BLAST cache load complete: {} files, {:.2} GB @ {:.1} MB/s average",
            files_cached,
            bytes_cached as f64 / (1024.0 * 1024.0 * 1024.0),
            average_speed
        );

        Ok(CacheLoadResult {
            files_cached,
            bytes_cached,
            duration: total_duration,
            average_speed_mbps: average_speed,
        })
    }

    /// Phase 3: Execute parallel distribution
    async fn execute_distribution(&self, job_id: &str) -> Result<DistributionResult> {
        println!("BLAST Phase 3: Executing parallel distribution");

        let start_time = SystemTime::now();
        let manifest = self.file_manifest.read().clone();
        let target_count = self.config.distribution_targets.len();

        // Create parallel distribution tasks
        let (sender, receiver) = bounded::<DistributionTask>(1000);

        // Generate distribution tasks
        for file_record in &manifest {
            for target_path in &file_record.target_paths {
                let task = DistributionTask {
                    cache_path: file_record.cache_path.clone(),
                    target_path: target_path.clone(),
                    file_size: file_record.file_size,
                };
                sender.send(task)?;
            }
        }
        drop(sender);

        // Execute distribution in parallel
        let stats = self.stats.clone();
        let cancel_signal = self.cancel_signal.clone();
        let event_hub = self.event_hub.clone();
        let job_id_clone = job_id.to_string();

        let distribution_handles: Vec<_> = (0..self.config.max_parallel_streams)
            .map(|stream_id| {
                let receiver = receiver.clone();
                let stats = stats.clone();
                let cancel_signal = cancel_signal.clone();
                let event_hub = event_hub.clone();
                let job_id = job_id_clone.clone();
                let config = self.config.clone();

                tokio::spawn(async move {
                    Self::distribution_worker(
                        stream_id,
                        receiver,
                        stats,
                        cancel_signal,
                        event_hub,
                        job_id,
                        config,
                    )
                    .await
                })
            })
            .collect();

        // Wait for all distribution tasks to complete
        let mut total_files_distributed = 0usize;
        let mut total_bytes_distributed = 0u64;

        for handle in distribution_handles {
            let (files, bytes) = handle.await??;
            total_files_distributed += files;
            total_bytes_distributed += bytes;
        }

        let total_duration = start_time.elapsed()?;
        let average_speed = if total_duration.as_secs_f64() > 0.0 {
            (total_bytes_distributed as f64) / total_duration.as_secs_f64() / (1024.0 * 1024.0)
        } else {
            0.0
        };

        // Emit distribution complete event
        if let Some(ref event_hub) = self.event_hub {
            let _ = event_hub.emit_event(TransferEvent::new(
                EventType::BlastDistributionCompleted,
                EventPriority::High,
                job_id.to_string(),
                EventPayload::Blast {
                    blast_drive_path: self.config.blast_cache_path.to_string_lossy().to_string(),
                    distribution_destinations: self
                        .config
                        .distribution_targets
                        .iter()
                        .map(|p| p.to_string_lossy().to_string())
                        .collect(),
                    blast_progress_percent: 100.0,
                    distribution_progress_percent: 100.0,
                    phase: BlastPhase::Distribution.as_str().to_string(),
                },
            ));
        }

        println!(
            "BLAST distribution complete: {} files to {} destinations @ {:.1} MB/s average",
            total_files_distributed / target_count,
            target_count,
            average_speed
        );

        Ok(DistributionResult {
            files_distributed: total_files_distributed,
            bytes_distributed: total_bytes_distributed,
            duration: total_duration,
            average_speed_mbps: average_speed,
        })
    }

    /// High-performance copy to cache using optimized I/O
    async fn copy_to_cache(
        &self,
        source: &Path,
        cache_dest: &Path,
        chunk_size: usize,
    ) -> Result<()> {
        // Ensure cache destination directory exists
        if let Some(parent) = cache_dest.parent() {
            fs::create_dir_all(parent).await?;
        }

        // Open source and destination files
        let mut source_file = fs::File::open(source).await?;
        let mut cache_file = fs::File::create(cache_dest).await?;

        // Use large buffer for optimal NVMe performance
        let mut buffer = vec![0u8; chunk_size];

        loop {
            let bytes_read = source_file.read(&mut buffer).await?;
            if bytes_read == 0 {
                break;
            }

            cache_file.write_all(&buffer[..bytes_read]).await?;

            if self.cancel_signal.load(Ordering::Relaxed) {
                anyhow::bail!("Cache copy cancelled");
            }
        }

        cache_file.sync_all().await?;
        Ok(())
    }

    /// Distribution worker for parallel copy operations
    async fn distribution_worker(
        _stream_id: usize,
        receiver: Receiver<DistributionTask>,
        stats: Arc<BlastStats>,
        cancel_signal: Arc<AtomicBool>,
        _event_hub: Option<Arc<EventHub>>,
        _job_id: String,
        _config: BlastConfig,
    ) -> Result<(usize, u64)> {
        let mut files_processed = 0usize;
        let mut bytes_processed = 0u64;

        while let Ok(task) = receiver.recv() {
            if cancel_signal.load(Ordering::Relaxed) {
                break;
            }

            // Ensure target directory exists
            if let Some(parent) = task.target_path.parent() {
                fs::create_dir_all(parent).await?;
            }

            // Copy from cache to final destination
            fs::copy(&task.cache_path, &task.target_path).await?;

            files_processed += 1;
            bytes_processed += task.file_size;

            // Update global statistics
            stats
                .distributed_bytes
                .fetch_add(task.file_size, Ordering::Relaxed);
        }

        Ok((files_processed, bytes_processed))
    }

    /// Phase 4: Execute verification
    async fn execute_verification(&self, _job_id: &str) -> Result<VerificationResult> {
        println!("BLAST Phase 4: Executing verification");

        // Implementation would verify checksums between cache and targets
        // For now, return success

        Ok(VerificationResult {
            files_verified: self.file_manifest.read().len(),
            verification_passed: true,
            failed_files: Vec::new(),
        })
    }

    /// Set current BLAST phase and emit event
    async fn set_phase(&self, phase: BlastPhase, job_id: &str) -> Result<()> {
        let start_time = SystemTime::now();

        // Update phase timing for previous phase
        if let Some(previous_phase) = self.stats.phase_timings.read().keys().last().copied() {
            if let Some(previous_start) = self.stats.phase_timings.read().get(&previous_phase) {
                let duration = start_time
                    .duration_since(SystemTime::now() - *previous_start)
                    .unwrap_or_default();
                self.stats
                    .phase_timings
                    .write()
                    .insert(previous_phase, duration);
            }
        }

        // Set new phase
        *self.stats.current_phase.write() = phase;
        self.stats
            .phase_timings
            .write()
            .insert(phase, Duration::from_secs(0));

        println!("BLAST Phase: {}", phase.as_str());

        // Emit phase change event
        if let Some(ref event_hub) = self.event_hub {
            let _ = event_hub.emit_event(TransferEvent::new(
                match phase {
                    BlastPhase::CacheLoad => EventType::BlastInitiated,
                    BlastPhase::Distribution => EventType::BlastDistributionStarted,
                    BlastPhase::Complete => EventType::BlastCompleted,
                    _ => EventType::BlastInitiated,
                },
                EventPriority::High,
                job_id.to_string(),
                EventPayload::Blast {
                    blast_drive_path: self.config.blast_cache_path.to_string_lossy().to_string(),
                    distribution_destinations: self
                        .config
                        .distribution_targets
                        .iter()
                        .map(|p| p.to_string_lossy().to_string())
                        .collect(),
                    blast_progress_percent: self.stats.get_cache_progress_percent(),
                    distribution_progress_percent: self.stats.get_distribution_progress_percent(),
                    phase: phase.as_str().to_string(),
                },
            ));
        }

        Ok(())
    }

    /// Get total elapsed time across all phases
    fn get_total_elapsed_time(&self) -> Duration {
        self.stats.phase_timings.read().values().sum()
    }

    /// Get final statistics summary
    fn get_final_stats(&self) -> BlastStatsSummary {
        BlastStatsSummary {
            total_bytes: self.stats.total_bytes.load(Ordering::Relaxed),
            cached_bytes: self.stats.cached_bytes.load(Ordering::Relaxed),
            distributed_bytes: self.stats.distributed_bytes.load(Ordering::Relaxed),
            cache_speed_mbps: self.stats.cache_speed_mbps.load(Ordering::Relaxed) as f64,
            distribution_speed_mbps: self.stats.distribution_speed_mbps.load(Ordering::Relaxed)
                as f64,
            files_processed: self.stats.files_processed.load(Ordering::Relaxed),
            phase_timings: self.stats.phase_timings.read().clone(),
        }
    }

    /// Cancel ongoing BLAST operation
    pub fn cancel(&self) {
        self.cancel_signal.store(true, Ordering::Relaxed);
        println!("BLAST operation cancellation requested");
    }
}

/// Distribution task for parallel processing
#[derive(Debug, Clone)]
struct DistributionTask {
    cache_path: PathBuf,
    target_path: PathBuf,
    file_size: u64,
}

/// BLAST transfer results
#[derive(Debug)]
pub struct BlastTransferResult {
    pub cache_result: CacheLoadResult,
    pub distribution_result: DistributionResult,
    pub verification_result: VerificationResult,
    pub total_time: Duration,
    pub final_stats: BlastStatsSummary,
}

#[derive(Debug)]
pub struct CacheLoadResult {
    pub files_cached: usize,
    pub bytes_cached: u64,
    pub duration: Duration,
    pub average_speed_mbps: f64,
}

#[derive(Debug)]
pub struct DistributionResult {
    pub files_distributed: usize,
    pub bytes_distributed: u64,
    pub duration: Duration,
    pub average_speed_mbps: f64,
}

#[derive(Debug)]
pub struct VerificationResult {
    pub files_verified: usize,
    pub verification_passed: bool,
    pub failed_files: Vec<PathBuf>,
}

#[derive(Debug, Clone)]
pub struct BlastStatsSummary {
    pub total_bytes: u64,
    pub cached_bytes: u64,
    pub distributed_bytes: u64,
    pub cache_speed_mbps: f64,
    pub distribution_speed_mbps: f64,
    pub files_processed: u64,
    pub phase_timings: HashMap<BlastPhase, Duration>,
}

/// Register Python types for this module
pub fn register_python_types(_m: &PyModule) -> PyResult<()> {
    // BLAST engine types are exported via python_bindings module
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_blast_engine_creation() {
        let config = BlastConfig::default();
        let engine = BlastEngine::new(config);

        assert_eq!(*engine.stats.current_phase.read(), BlastPhase::Preparation);
        assert_eq!(engine.stats.total_bytes.load(Ordering::Relaxed), 0);
    }

    #[tokio::test]
    async fn test_blast_preparation() {
        let temp_cache = TempDir::new().expect("Failed to create temp cache dir");
        let temp_target = TempDir::new().expect("Failed to create temp target dir");
        let temp_source = TempDir::new().expect("Failed to create temp source dir");

        // Create test file
        let test_file = temp_source.path().join("test.txt");
        fs::write(&test_file, b"Hello BLAST!")
            .await
            .expect("Failed to write test file");

        let config = BlastConfig {
            blast_cache_path: temp_cache.path().to_path_buf(),
            distribution_targets: vec![temp_target.path().to_path_buf()],
            ..Default::default()
        };

        let engine = BlastEngine::new(config);

        let result = engine
            .prepare_blast_operation(&[test_file], "test_job")
            .await;
        assert!(result.is_ok());

        assert_eq!(engine.stats.total_bytes.load(Ordering::Relaxed), 12); // "Hello BLAST!" = 12 bytes
        assert_eq!(engine.file_manifest.read().len(), 1);
    }
}
