//! ForwardFlow V2.0 - Intelligent Transfer Strategy Engine with GPU Acceleration
//!
//! Analyzes destination characteristics and selects optimal transfer strategies
//! for professional DIT workflows. Supports BLAST, memory staging, direct copy,
//! GPU-accelerated transfers, and hybrid multi-destination strategies.

use anyhow::Result;
use parking_lot::RwLock;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, SystemTime};

use crate::event_hub_v2::{EventHub, EventPayload, EventPriority, EventType, TransferEvent};
use pyo3::prelude::*;

/// Destination classification based on hardware characteristics
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DestinationType {
    NvmeSsd,      // 3-7 GB/s - Fastest available, ideal for GPU acceleration
    LocalSsd,     // 500 MB/s - 2 GB/s - High speed local storage
    NetworkShare, // 50-500 MB/s - Network attached storage
    UsbDrive,     // 50-200 MB/s - External USB storage
    CloudStorage, // 10-100 MB/s - Cloud/remote storage
    GpuMemory,    // GPU VRAM - Ultra-fast staging for compute acceleration
    Unknown,      // Unable to classify
}

impl DestinationType {
    /// Get typical speed range for this destination type
    pub fn typical_speed_range(&self) -> (f64, f64) {
        match self {
            DestinationType::NvmeSsd => (3000.0, 7000.0), // MB/s
            DestinationType::LocalSsd => (500.0, 2000.0),
            DestinationType::NetworkShare => (50.0, 500.0),
            DestinationType::UsbDrive => (50.0, 200.0),
            DestinationType::CloudStorage => (10.0, 100.0),
            DestinationType::GpuMemory => (10000.0, 100000.0), // GPU memory bandwidth
            DestinationType::Unknown => (10.0, 100.0),
        }
    }

    /// Whether this destination benefits from multipart transfers
    pub fn supports_multipart(&self) -> bool {
        matches!(
            self,
            DestinationType::NetworkShare | DestinationType::CloudStorage
        )
    }

    /// Whether this destination can be used as a BLAST cache
    pub fn suitable_for_blast(&self) -> bool {
        matches!(
            self,
            DestinationType::NvmeSsd | DestinationType::LocalSsd | DestinationType::GpuMemory
        )
    }

    /// Whether this destination supports GPU acceleration
    pub fn supports_gpu_acceleration(&self) -> bool {
        matches!(self, DestinationType::GpuMemory | DestinationType::NvmeSsd)
    }
}

/// Analyzed destination with performance characteristics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DestinationAnalysis {
    pub path: PathBuf,
    pub dest_type: DestinationType,
    pub available_space_bytes: u64,
    pub benchmarked_speed_mbps: f64,
    pub optimal_chunk_size_mb: usize,
    pub supports_direct_io: bool,
    pub is_network_path: bool,
    pub volume_info: VolumeInfo,
    pub gpu_info: Option<GpuInfo>,
}

/// GPU acceleration information for compute workloads
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GpuInfo {
    pub device_name: String,
    pub memory_gb: f64,
    pub compute_units: u32,
    pub memory_bandwidth_gbps: f64,
    pub supports_unified_memory: bool,
}

/// Volume/filesystem information for optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VolumeInfo {
    pub filesystem: String, // APFS, NTFS, ext4, etc.
    pub mount_point: PathBuf,
    pub is_case_sensitive: bool,
    pub supports_sparse_files: bool,
    pub block_size: usize,
}

/// Transfer strategy selection based on destination analysis
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TransferStrategy {
    /// Single destination, direct copy for maximum speed
    DirectCopy {
        destination: PathBuf,
        use_memory_mapping: bool,
        chunk_size_mb: usize,
    },

    /// Multiple destinations, read once and distribute from memory
    MemoryStaging {
        destinations: Vec<PathBuf>,
        buffer_size_mb: usize,
        parallel_writes: usize,
    },

    /// GPU-accelerated transfer with compute operations
    GpuAccelerated {
        gpu_staging: PathBuf,
        final_destinations: Vec<PathBuf>,
        compute_pipeline: GpuComputePipeline,
        use_unified_memory: bool,
    },

    /// BLAST workflow: ultra-fast cache first, then distribute
    BlastWorkflow {
        blast_cache: PathBuf,
        final_destinations: Vec<PathBuf>,
        cache_strategy: Box<TransferStrategy>,
        distribution_strategy: Box<TransferStrategy>,
    },

    /// Mixed strategies for different destination types
    HybridMultiStrategy {
        strategies: Vec<(PathBuf, TransferStrategy)>,
    },
}

/// GPU compute pipeline configuration for accelerated transfers
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum GpuComputePipeline {
    /// Hash computation acceleration (xxHash, SHA, etc.)
    HashCompute {
        algorithm: String,
        parallel_streams: u32,
    },

    /// Data transformation/transcoding
    DataTransform {
        operation: String,
        shader_path: Option<PathBuf>,
    },

    /// Compression/decompression acceleration
    CompressionAccel {
        algorithm: String,
        compression_level: u8,
    },

    /// Memory bandwidth optimization only
    MemoryOptimized,
}

impl TransferStrategy {
    pub fn name(&self) -> &'static str {
        match self {
            TransferStrategy::DirectCopy { .. } => "DirectCopy",
            TransferStrategy::MemoryStaging { .. } => "MemoryStaging",
            TransferStrategy::GpuAccelerated { .. } => "GpuAccelerated",
            TransferStrategy::BlastWorkflow { .. } => "BlastWorkflow",
            TransferStrategy::HybridMultiStrategy { .. } => "HybridMultiStrategy",
        }
    }

    /// Estimate total transfer time for this strategy
    pub fn estimate_transfer_time(
        &self,
        total_bytes: u64,
        analyses: &[DestinationAnalysis],
    ) -> Duration {
        match self {
            TransferStrategy::DirectCopy { destination, .. } => {
                if let Some(analysis) = analyses.iter().find(|a| a.path == *destination) {
                    let seconds =
                        total_bytes as f64 / (analysis.benchmarked_speed_mbps * 1024.0 * 1024.0);
                    Duration::from_secs_f64(seconds)
                } else {
                    Duration::from_secs(3600) // Default to 1 hour if unknown
                }
            }
            TransferStrategy::MemoryStaging { destinations, .. } => {
                // Time = read time + max(write times to all destinations)
                let read_time = total_bytes as f64 / (2000.0 * 1024.0 * 1024.0); // Assume 2GB/s read
                let write_times: Vec<f64> = destinations
                    .iter()
                    .filter_map(|dest| {
                        analyses.iter().find(|a| a.path == *dest).map(|a| {
                            total_bytes as f64 / (a.benchmarked_speed_mbps * 1024.0 * 1024.0)
                        })
                    })
                    .collect();

                let max_write_time = write_times.into_iter().fold(0.0, f64::max);
                Duration::from_secs_f64(read_time + max_write_time)
            }
            TransferStrategy::BlastWorkflow { blast_cache, .. } => {
                // BLAST time is just the cache copy time (fastest operation)
                if let Some(cache_analysis) = analyses.iter().find(|a| a.path == *blast_cache) {
                    let seconds = total_bytes as f64
                        / (cache_analysis.benchmarked_speed_mbps * 1024.0 * 1024.0);
                    Duration::from_secs_f64(seconds)
                } else {
                    Duration::from_secs(60) // Fast cache default
                }
            }
            TransferStrategy::HybridMultiStrategy { .. } => {
                // Conservative estimate
                Duration::from_secs(1800)
            }
            TransferStrategy::GpuAccelerated { .. } => {
                // GPU acceleration provides significant speedup for large transfers
                Duration::from_secs(300)
            }
        }
    }
}

/// High-performance destination analyzer and strategy selector with GPU support
pub struct TransferStrategyEngine {
    /// Cached destination analyses to avoid re-benchmarking
    analysis_cache: Arc<RwLock<HashMap<PathBuf, DestinationAnalysis>>>,

    /// System memory information for buffer sizing
    total_system_memory: u64,
    available_cpu_cores: usize,

    /// GPU information for acceleration
    gpu_info: Option<GpuInfo>,

    /// Event hub for real-time strategy selection updates
    event_hub: Option<Arc<crate::event_hub_v2::EventHub>>,
}

impl TransferStrategyEngine {
    pub fn new() -> Self {
        Self {
            analysis_cache: Arc::new(RwLock::new(HashMap::new())),
            total_system_memory: Self::get_system_memory(),
            available_cpu_cores: num_cpus::get(),
            gpu_info: Self::detect_gpu_capabilities(),
            event_hub: None,
        }
    }

    /// Create engine with event hub integration
    pub fn with_event_hub(event_hub: Arc<crate::event_hub_v2::EventHub>) -> Self {
        let mut engine = Self::new();
        engine.event_hub = Some(event_hub);
        engine
    }

    /// Analyze destinations and select optimal transfer strategy
    pub fn analyze_and_select_strategy(
        &self,
        destinations: &[PathBuf],
        total_bytes: u64,
        blast_cache: Option<PathBuf>,
        job_id: &str,
    ) -> Result<(TransferStrategy, Vec<DestinationAnalysis>)> {
        println!(
            "Analyzing {} destinations for optimal transfer strategy",
            destinations.len()
        );

        // Emit strategy analysis start event
        if let Some(ref event_hub) = self.event_hub {
            let _ = event_hub.emit_event(TransferEvent::new(
                EventType::JobStrategySelected,
                EventPriority::Normal,
                job_id.to_string(),
                EventPayload::Job {
                    total_destinations: destinations.len(),
                    completed_destinations: 0,
                    total_speed_mbps: 0.0,
                    peak_speed_mbps: 0.0,
                    progress_percent: 0.0,
                    eta_seconds: 0.0,
                    total_bytes,
                    copied_bytes: 0,
                    total_files: 0,
                    completed_files: 0,
                    strategy_name: "Analyzing...".to_string(),
                    error_message: None,
                },
            ));
        }

        // Analyze all destinations in parallel for maximum performance
        let analyses: Result<Vec<_>, _> = destinations
            .par_iter()
            .map(|dest| self.analyze_destination(dest))
            .collect();

        let analyses = analyses?;

        // Log analysis results
        for analysis in &analyses {
            println!(
                "Destination: {} -> {:?} @ {:.1} MB/s",
                analysis.path.display(),
                analysis.dest_type,
                analysis.benchmarked_speed_mbps
            );
        }

        // Select optimal strategy based on analysis
        let strategy = self.select_optimal_strategy(&analyses, total_bytes, blast_cache, job_id)?;

        let estimated_time = strategy.estimate_transfer_time(total_bytes, &analyses);
        println!(
            "Selected strategy: {} (estimated time: {:?})",
            strategy.name(),
            estimated_time
        );

        // Emit strategy selection event
        if let Some(ref event_hub) = self.event_hub {
            let _ = event_hub.emit_event(TransferEvent::new(
                EventType::JobStrategySelected,
                EventPriority::High,
                job_id.to_string(),
                EventPayload::Job {
                    total_destinations: destinations.len(),
                    completed_destinations: 0,
                    total_speed_mbps: analyses.iter().map(|a| a.benchmarked_speed_mbps).sum(),
                    peak_speed_mbps: analyses
                        .iter()
                        .map(|a| a.benchmarked_speed_mbps)
                        .fold(0.0, f64::max),
                    progress_percent: 0.0,
                    eta_seconds: estimated_time.as_secs_f64(),
                    total_bytes,
                    copied_bytes: 0,
                    total_files: 0,
                    completed_files: 0,
                    strategy_name: strategy.name().to_string(),
                    error_message: None,
                },
            ));
        }

        Ok((strategy, analyses))
    }

    /// Analyze a single destination's characteristics
    pub fn analyze_destination(&self, destination: &Path) -> Result<DestinationAnalysis> {
        // Check cache first
        if let Some(cached) = self.analysis_cache.read().get(destination) {
            return Ok(cached.clone());
        }

        println!("Benchmarking destination: {}", destination.display());

        let dest_type = self.classify_destination(destination)?;
        let available_space = self.get_available_space(destination)?;
        let volume_info = self.analyze_volume(destination)?;

        // Benchmark actual transfer speed
        let benchmarked_speed = self.benchmark_destination_speed(destination)?;

        // Determine optimal chunk size based on destination type and volume
        let optimal_chunk_size = self.calculate_optimal_chunk_size(dest_type, &volume_info);

        let analysis = DestinationAnalysis {
            path: destination.to_path_buf(),
            dest_type,
            available_space_bytes: available_space,
            benchmarked_speed_mbps: benchmarked_speed,
            optimal_chunk_size_mb: optimal_chunk_size,
            supports_direct_io: self.test_direct_io_support(destination),
            is_network_path: self.is_network_path(destination),
            volume_info,
            gpu_info: self.gpu_info.clone(),
        };

        // Cache the analysis for future use
        self.analysis_cache
            .write()
            .insert(destination.to_path_buf(), analysis.clone());

        Ok(analysis)
    }

    /// Select optimal strategy based on destination analyses
    fn select_optimal_strategy(
        &self,
        analyses: &[DestinationAnalysis],
        total_bytes: u64,
        blast_cache: Option<PathBuf>,
        job_id: &str,
    ) -> Result<TransferStrategy> {
        // If BLAST cache is specified and suitable, use BLAST workflow
        if let Some(blast_path) = blast_cache {
            if let Some(blast_analysis) = analyses.iter().find(|a| a.path == blast_path) {
                if blast_analysis.dest_type.suitable_for_blast() {
                    let other_destinations: Vec<PathBuf> = analyses
                        .iter()
                        .filter(|a| a.path != blast_path)
                        .map(|a| a.path.clone())
                        .collect();

                    if !other_destinations.is_empty() {
                        return Ok(TransferStrategy::BlastWorkflow {
                            blast_cache: blast_path.clone(),
                            final_destinations: other_destinations.clone(),
                            cache_strategy: Box::new(TransferStrategy::DirectCopy {
                                destination: blast_path,
                                use_memory_mapping: true,
                                chunk_size_mb: blast_analysis.optimal_chunk_size_mb,
                            }),
                            distribution_strategy: Box::new(
                                self.select_multi_destination_strategy(
                                    &other_destinations,
                                    analyses,
                                    job_id,
                                )?,
                            ),
                        });
                    }
                }
            }
        }

        // Check if GPU acceleration is beneficial
        if let Some(ref gpu_info) = self.gpu_info {
            if self.should_use_gpu_acceleration(analyses, total_bytes, gpu_info) {
                return Ok(self.create_gpu_accelerated_strategy(analyses, gpu_info)?);
            }
        }

        match analyses.len() {
            0 => anyhow::bail!("No destinations to analyze"),

            1 => {
                // Single destination: use direct copy
                let analysis = &analyses[0];
                Ok(TransferStrategy::DirectCopy {
                    destination: analysis.path.clone(),
                    use_memory_mapping: analysis.dest_type == DestinationType::NvmeSsd,
                    chunk_size_mb: analysis.optimal_chunk_size_mb,
                })
            }

            _ => {
                // Multiple destinations: choose between memory staging and hybrid
                self.select_multi_destination_strategy(
                    &analyses.iter().map(|a| a.path.clone()).collect::<Vec<_>>(),
                    analyses,
                    job_id,
                )
            }
        }
    }

    /// Select strategy for multiple destinations
    fn select_multi_destination_strategy(
        &self,
        destinations: &[PathBuf],
        analyses: &[DestinationAnalysis],
        _job_id: &str,
    ) -> Result<TransferStrategy> {
        let total_speed: f64 = analyses.iter().map(|a| a.benchmarked_speed_mbps).sum();

        // Calculate memory requirements for staging
        let buffer_size_mb = (self.total_system_memory / (4 * 1024 * 1024)).min(2048) as usize; // Use max 1/4 of system RAM, cap at 2GB

        // If all destinations are similar speed, use memory staging
        let speed_variance = self.calculate_speed_variance(analyses);
        if speed_variance < 2.0 {
            // Destinations have similar speeds
            return Ok(TransferStrategy::MemoryStaging {
                destinations: destinations.to_vec(),
                buffer_size_mb,
                parallel_writes: analyses.len().min(self.available_cpu_cores),
            });
        }

        // Mixed speeds: use hybrid strategy with different approaches per destination
        let mut strategies = Vec::new();

        for analysis in analyses {
            let strategy = match analysis.dest_type {
                DestinationType::NvmeSsd | DestinationType::LocalSsd => {
                    TransferStrategy::DirectCopy {
                        destination: analysis.path.clone(),
                        use_memory_mapping: true,
                        chunk_size_mb: analysis.optimal_chunk_size_mb,
                    }
                }
                DestinationType::NetworkShare | DestinationType::CloudStorage => {
                    TransferStrategy::DirectCopy {
                        destination: analysis.path.clone(),
                        use_memory_mapping: false, // Network destinations don't benefit from mmap
                        chunk_size_mb: 1,          // Smaller chunks for network
                    }
                }
                _ => TransferStrategy::DirectCopy {
                    destination: analysis.path.clone(),
                    use_memory_mapping: false,
                    chunk_size_mb: analysis.optimal_chunk_size_mb,
                },
            };

            strategies.push((analysis.path.clone(), strategy));
        }

        Ok(TransferStrategy::HybridMultiStrategy { strategies })
    }

    /// Classify destination type based on path analysis and benchmarking
    fn classify_destination(&self, destination: &Path) -> Result<DestinationType> {
        // Network path detection
        if self.is_network_path(destination) {
            return Ok(DestinationType::NetworkShare);
        }

        // USB drive detection (heuristic)
        if self.is_usb_drive(destination) {
            return Ok(DestinationType::UsbDrive);
        }

        // Cloud storage detection (path patterns)
        if self.is_cloud_storage(destination) {
            return Ok(DestinationType::CloudStorage);
        }

        // Local storage: distinguish between NVMe SSD, SATA SSD, etc.
        // This would require platform-specific detection
        #[cfg(target_os = "macos")]
        {
            return self.classify_macos_storage(destination);
        }

        #[cfg(target_os = "linux")]
        {
            return self.classify_linux_storage(destination);
        }

        #[cfg(target_os = "windows")]
        {
            return self.classify_windows_storage(destination);
        }

        // Default classification
        Ok(DestinationType::Unknown)
    }

    #[cfg(target_os = "macos")]
    fn classify_macos_storage(&self, destination: &Path) -> Result<DestinationType> {
        // Use macOS system calls to detect storage type
        // This is a simplified implementation - would need actual macOS APIs

        let path_str = destination.to_string_lossy();

        // Common patterns for different storage types on macOS
        if path_str.contains("/Volumes/") {
            // External volume - could be USB or network
            if self.is_network_mount(destination) {
                Ok(DestinationType::NetworkShare)
            } else {
                Ok(DestinationType::UsbDrive)
            }
        } else if path_str.starts_with("/System/Volumes/Data") || path_str.starts_with("/Users/") {
            // Internal storage - assume SSD on modern Macs
            Ok(DestinationType::LocalSsd)
        } else {
            Ok(DestinationType::Unknown)
        }
    }

    #[cfg(target_os = "linux")]
    fn classify_linux_storage(&self, _destination: &Path) -> Result<DestinationType> {
        // Would implement Linux-specific storage detection
        Ok(DestinationType::Unknown)
    }

    #[cfg(target_os = "windows")]
    fn classify_windows_storage(&self, _destination: &Path) -> Result<DestinationType> {
        // Would implement Windows-specific storage detection
        Ok(DestinationType::Unknown)
    }

    /// Benchmark actual transfer speed to destination
    fn benchmark_destination_speed(&self, destination: &Path) -> Result<f64> {
        // Create a test file for benchmarking
        let test_size = 10 * 1024 * 1024; // 10 MB test file
        let test_data = vec![0u8; test_size];

        let test_file = destination.join("forwardflow_benchmark_test.tmp");

        let start_time = SystemTime::now();

        // Write test data
        std::fs::write(&test_file, &test_data)?;

        let write_duration = start_time.elapsed()?;

        // Clean up test file
        let _ = std::fs::remove_file(&test_file);

        // Calculate speed in MB/s
        let speed_mbps = (test_size as f64) / write_duration.as_secs_f64() / (1024.0 * 1024.0);

        Ok(speed_mbps)
    }

    /// Calculate optimal chunk size based on destination characteristics
    fn calculate_optimal_chunk_size(
        &self,
        dest_type: DestinationType,
        volume_info: &VolumeInfo,
    ) -> usize {
        let base_chunk_mb = match dest_type {
            DestinationType::NvmeSsd => 32,     // Large chunks for NVMe
            DestinationType::LocalSsd => 16,    // Medium chunks for SATA SSD
            DestinationType::NetworkShare => 1, // Small chunks for network
            DestinationType::UsbDrive => 4,     // Small-medium chunks for USB
            DestinationType::CloudStorage => 1, // Very small chunks for cloud
            DestinationType::Unknown => 4,
            DestinationType::GpuMemory => 128, // Large chunks for GPU memory transfers
        };

        // Adjust based on volume block size
        let volume_block_mb = (volume_info.block_size / (1024 * 1024)).max(1);

        // Use multiple of volume block size
        (base_chunk_mb / volume_block_mb).max(1) * volume_block_mb
    }

    /// Helper functions for destination classification
    fn is_network_path(&self, destination: &Path) -> bool {
        let path_str = destination.to_string_lossy().to_lowercase();

        path_str.contains("/volumes/")
            && (path_str.contains("smb://")
                || path_str.contains("afp://")
                || path_str.contains("nfs://")
                || path_str.contains(".local")
                || path_str.contains("synology")
                || path_str.contains("nas"))
    }

    fn is_usb_drive(&self, _destination: &Path) -> bool {
        // Platform-specific USB detection would go here
        false
    }

    fn is_cloud_storage(&self, destination: &Path) -> bool {
        let path_str = destination.to_string_lossy().to_lowercase();

        path_str.contains("dropbox")
            || path_str.contains("onedrive")
            || path_str.contains("google drive")
            || path_str.contains("icloud")
    }

    fn is_network_mount(&self, _destination: &Path) -> bool {
        // Would check if path is a network mount point
        false
    }

    fn test_direct_io_support(&self, _destination: &Path) -> bool {
        // Would test if destination supports direct I/O
        true
    }

    fn analyze_volume(&self, destination: &Path) -> Result<VolumeInfo> {
        // Basic volume analysis - would be platform-specific
        Ok(VolumeInfo {
            filesystem: "APFS".to_string(), // Default assumption
            mount_point: destination.to_path_buf(),
            is_case_sensitive: false,
            supports_sparse_files: true,
            block_size: 4096,
        })
    }

    fn get_available_space(&self, destination: &Path) -> Result<u64> {
        // Would use platform-specific APIs to get free space
        Ok(1024 * 1024 * 1024 * 100) // Default to 100GB
    }

    fn get_system_memory() -> u64 {
        // Would use platform-specific APIs to get system memory
        8 * 1024 * 1024 * 1024 // Default to 8GB
    }

    fn calculate_speed_variance(&self, analyses: &[DestinationAnalysis]) -> f64 {
        if analyses.len() < 2 {
            return 0.0;
        }

        let speeds: Vec<f64> = analyses.iter().map(|a| a.benchmarked_speed_mbps).collect();
        let mean = speeds.iter().sum::<f64>() / speeds.len() as f64;
        let variance = speeds
            .iter()
            .map(|speed| (speed - mean).powi(2))
            .sum::<f64>()
            / speeds.len() as f64;

        variance.sqrt() / mean // Coefficient of variation
    }

    /// Detect available GPU capabilities for acceleration
    fn detect_gpu_capabilities() -> Option<GpuInfo> {
        // Platform-specific GPU detection
        #[cfg(target_os = "macos")]
        {
            return Self::detect_macos_gpu();
        }

        #[cfg(target_os = "linux")]
        {
            return Self::detect_linux_gpu();
        }

        #[cfg(target_os = "windows")]
        {
            return Self::detect_windows_gpu();
        }

        None
    }

    #[cfg(target_os = "macos")]
    fn detect_macos_gpu() -> Option<GpuInfo> {
        // Detect Apple Silicon GPU or discrete GPUs on macOS
        // This would use Metal framework APIs

        // For demonstration, assume M1/M2/M3 with unified memory
        if std::env::consts::ARCH == "aarch64" {
            Some(GpuInfo {
                device_name: "Apple M-Series GPU".to_string(),
                memory_gb: 16.0,              // Would detect actual unified memory
                compute_units: 32,            // Would detect actual core count
                memory_bandwidth_gbps: 400.0, // M1/M2 typical bandwidth
                supports_unified_memory: true,
            })
        } else {
            None
        }
    }

    #[cfg(target_os = "linux")]
    fn detect_linux_gpu() -> Option<GpuInfo> {
        // Would implement CUDA/OpenCL/Vulkan detection on Linux
        None
    }

    #[cfg(target_os = "windows")]
    fn detect_windows_gpu() -> Option<GpuInfo> {
        // Would implement DirectX/CUDA/OpenCL detection on Windows
        None
    }

    /// Determine if GPU acceleration would be beneficial
    fn should_use_gpu_acceleration(
        &self,
        analyses: &[DestinationAnalysis],
        total_bytes: u64,
        gpu_info: &GpuInfo,
    ) -> bool {
        // GPU acceleration is beneficial when:
        // 1. Transfer size is large enough to amortize GPU setup costs
        // 2. Multiple destinations benefit from parallel compute
        // 3. Hash computation or data transformation is needed

        let min_size_for_gpu = 100 * 1024 * 1024; // 100MB minimum
        let has_fast_destinations = analyses
            .iter()
            .any(|a| a.dest_type.supports_gpu_acceleration());

        total_bytes >= min_size_for_gpu
            && analyses.len() > 1
            && has_fast_destinations
            && gpu_info.memory_gb >= 2.0 // Minimum 2GB GPU memory
    }

    /// Create GPU-accelerated transfer strategy
    fn create_gpu_accelerated_strategy(
        &self,
        analyses: &[DestinationAnalysis],
        gpu_info: &GpuInfo,
    ) -> Result<TransferStrategy> {
        // Use first NVMe/fast destination as GPU staging area
        let gpu_staging = analyses
            .iter()
            .find(|a| a.dest_type == DestinationType::NvmeSsd)
            .map(|a| a.path.clone())
            .unwrap_or_else(|| analyses[0].path.clone());

        let final_destinations: Vec<PathBuf> = analyses
            .iter()
            .filter(|a| a.path != gpu_staging)
            .map(|a| a.path.clone())
            .collect();

        // Choose compute pipeline based on workload
        let compute_pipeline = if gpu_info.supports_unified_memory {
            // Use memory optimization for unified memory architectures (Apple Silicon)
            GpuComputePipeline::MemoryOptimized
        } else {
            // Use hash computation acceleration for discrete GPUs
            GpuComputePipeline::HashCompute {
                algorithm: "xxHash64BE".to_string(),
                parallel_streams: (gpu_info.compute_units / 4).max(1), // Use 1/4 of compute units per stream
            }
        };

        Ok(TransferStrategy::GpuAccelerated {
            gpu_staging,
            final_destinations,
            compute_pipeline,
            use_unified_memory: gpu_info.supports_unified_memory,
        })
    }
}

/// Register Python types for this module
pub fn register_python_types(_m: &PyModule) -> PyResult<()> {
    // Strategy engine types are exported via python_bindings module
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_strategy_engine_creation() {
        let engine = TransferStrategyEngine::new();
        assert!(engine.available_cpu_cores > 0);
        assert!(engine.total_system_memory > 0);
    }

    #[test]
    fn test_destination_analysis() {
        let engine = TransferStrategyEngine::new();
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        let analysis = engine.analyze_destination(temp_dir.path());
        assert!(analysis.is_ok());

        let analysis = analysis.unwrap();
        assert_eq!(analysis.path, temp_dir.path());
        assert!(analysis.benchmarked_speed_mbps > 0.0);
    }

    #[test]
    fn test_single_destination_strategy() {
        let engine = TransferStrategyEngine::new();
        let temp_dir = TempDir::new().expect("Failed to create temp dir");

        let result = engine.analyze_and_select_strategy(
            &[temp_dir.path().to_path_buf()],
            1024 * 1024 * 1024, // 1GB
            None,
            "test_job_001",
        );

        assert!(result.is_ok());
        let (strategy, analyses) = result.unwrap();

        assert_eq!(analyses.len(), 1);
        assert_eq!(strategy.name(), "DirectCopy");
    }

    #[test]
    fn test_gpu_detection() {
        let engine = TransferStrategyEngine::new();
        // GPU detection is platform-specific, just verify it doesn't crash
        assert!(engine.available_cpu_cores > 0);
    }

    #[test]
    fn test_gpu_acceleration_strategy() {
        let engine = TransferStrategyEngine::new();
        let temp_dir1 = TempDir::new().expect("Failed to create temp dir 1");
        let temp_dir2 = TempDir::new().expect("Failed to create temp dir 2");

        let result = engine.analyze_and_select_strategy(
            &[
                temp_dir1.path().to_path_buf(),
                temp_dir2.path().to_path_buf(),
            ],
            500 * 1024 * 1024, // 500MB - large enough for GPU consideration
            None,
            "test_gpu_job",
        );

        assert!(result.is_ok());
        let (strategy, analyses) = result.unwrap();
        assert_eq!(analyses.len(), 2);

        // Strategy selection depends on GPU availability and destination types
        assert!(matches!(
            strategy.name(),
            "MemoryStaging" | "HybridMultiStrategy" | "GpuAccelerated"
        ));
    }
}
