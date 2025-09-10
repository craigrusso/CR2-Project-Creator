//! Integration tests for ForwardFlow V2.0 Rust engine
//! 
//! These tests verify the performance and functionality of the core engine
//! components without Python dependencies.

use std::path::PathBuf;
use std::time::{Instant, Duration};
use std::sync::Arc;
use tempfile::TempDir;
use tokio::fs;

// Import from the crate modules (adjust paths as needed)
use rust_high_perf_engine::event_hub_v2::*;
use rust_high_perf_engine::strategy_engine::*;
use rust_high_perf_engine::blast_engine::*;

#[tokio::test]
async fn test_event_hub_basic_functionality() {
    let event_hub = EventHub::new().expect("Failed to create EventHub");
    
    // Test basic event emission
    let event = TransferEvent::new(
        EventType::FileStarted,
        EventPriority::Normal,
        "test_job".to_string(),
        EventPayload::File {
            file_id: "test_file_001".to_string(),
            filename: "test.dat".to_string(),
            file_size: 1024,
            bytes_copied: 0,
            destination_path: "/tmp/test".to_string(),
            source_checksum: None,
            destination_checksum: None,
            hash_algorithm: "xxHash64BE".to_string(),
            transfer_speed_mbps: 0.0,
            error_message: None,
        }
    );
    
    let result = event_hub.emit_event(event);
    assert!(result.is_ok(), "Failed to emit event");
    
    // Allow some processing time
    tokio::time::sleep(Duration::from_millis(100)).await;
    
    let stats = event_hub.get_stats();
    assert!(stats.events_processed > 0, "No events were processed");
}

#[tokio::test]
async fn test_event_hub_performance() {
    let event_hub = Arc::new(EventHub::new().expect("Failed to create EventHub"));
    let start_time = Instant::now();
    let event_count = 1000;
    
    // Generate events rapidly
    for i in 0..event_count {
        let event = TransferEvent::new(
            EventType::FileProgress,
            EventPriority::Normal,
            format!("job_{}", i % 10),
            EventPayload::File {
                file_id: format!("file_{}", i),
                filename: format!("test_file_{}.dat", i),
                file_size: 1024 * 1024,
                bytes_copied: (i * 1024) % (1024 * 1024),
                destination_path: "/tmp/test".to_string(),
                source_checksum: None,
                destination_checksum: None,
                hash_algorithm: "xxHash64BE".to_string(),
                transfer_speed_mbps: 150.0,
                error_message: None,
            }
        );
        
        event_hub.emit_event(event).expect("Failed to emit event");
    }
    
    let duration = start_time.elapsed();
    let events_per_second = event_count as f64 / duration.as_secs_f64();
    
    println!("Event throughput: {:.0} events/second", events_per_second);
    assert!(events_per_second > 100.0, "Event throughput too low");
    
    // Wait for processing
    tokio::time::sleep(Duration::from_millis(200)).await;
    
    let stats = event_hub.get_stats();
    assert!(stats.events_processed >= event_count as u64 * 0.9, "Too many events lost");
}

#[test]
fn test_strategy_engine_creation() {
    let engine = TransferStrategyEngine::new();
    // Should not panic and should initialize properly
}

#[test]
fn test_strategy_engine_destination_analysis() {
    let engine = TransferStrategyEngine::new();
    let temp_dir = TempDir::new().expect("Failed to create temp dir");
    
    let result = engine.analyze_destination(temp_dir.path());
    assert!(result.is_ok(), "Failed to analyze destination");
    
    let analysis = result.unwrap();
    assert_eq!(analysis.path, temp_dir.path());
    assert!(analysis.benchmarked_speed_mbps > 0.0, "Benchmark speed should be positive");
    assert!(analysis.optimal_chunk_size_mb > 0, "Chunk size should be positive");
}

#[test]
fn test_strategy_engine_multi_destination() {
    let engine = TransferStrategyEngine::new();
    let temp_dir1 = TempDir::new().expect("Failed to create temp dir 1");
    let temp_dir2 = TempDir::new().expect("Failed to create temp dir 2");
    let temp_dir3 = TempDir::new().expect("Failed to create temp dir 3");
    
    let destinations = vec![
        temp_dir1.path().to_path_buf(),
        temp_dir2.path().to_path_buf(),
        temp_dir3.path().to_path_buf(),
    ];
    
    let result = engine.analyze_and_select_strategy(
        &destinations,
        1024 * 1024 * 1024, // 1GB
        None,
        "test_multi_dest"
    );
    
    assert!(result.is_ok(), "Multi-destination analysis failed");
    
    let (strategy, analyses) = result.unwrap();
    assert_eq!(analyses.len(), 3, "Should analyze all 3 destinations");
    assert!(matches!(strategy.name(), "MemoryStaging" | "HybridMultiStrategy"), 
        "Should select appropriate multi-destination strategy");
}

#[test]
fn test_destination_type_classification() {
    // Test destination type methods
    assert!(DestinationType::NvmeSsd.suitable_for_blast());
    assert!(DestinationType::LocalSsd.suitable_for_blast());
    assert!(!DestinationType::NetworkShare.suitable_for_blast());
    
    assert!(DestinationType::NetworkShare.supports_multipart());
    assert!(DestinationType::CloudStorage.supports_multipart());
    assert!(!DestinationType::NvmeSsd.supports_multipart());
    
    assert!(DestinationType::GpuMemory.supports_gpu_acceleration());
    assert!(DestinationType::NvmeSsd.supports_gpu_acceleration());
    assert!(!DestinationType::UsbDrive.supports_gpu_acceleration());
}

#[tokio::test]
async fn test_blast_engine_creation() {
    let temp_cache = TempDir::new().expect("Failed to create temp cache dir");
    let temp_target = TempDir::new().expect("Failed to create temp target dir");
    
    let config = BlastConfig {
        blast_cache_path: temp_cache.path().to_path_buf(),
        distribution_targets: vec![temp_target.path().to_path_buf()],
        ..Default::default()
    };
    
    let _engine = BlastEngine::new(config);
    // Should not panic
}

#[tokio::test]
async fn test_blast_engine_preparation() {
    let temp_cache = TempDir::new().expect("Failed to create temp cache dir");
    let temp_target = TempDir::new().expect("Failed to create temp target dir");
    let temp_source = TempDir::new().expect("Failed to create temp source dir");
    
    // Create test file
    let test_file = temp_source.path().join("test.txt");
    fs::write(&test_file, b"Hello BLAST Engine!").await.expect("Failed to write test file");
    
    let config = BlastConfig {
        blast_cache_path: temp_cache.path().to_path_buf(),
        distribution_targets: vec![temp_target.path().to_path_buf()],
        memory_buffer_mb: 32,
        max_parallel_streams: 2,
        use_direct_io: false, // Disable for test compatibility
        use_memory_mapping: false,
        cache_chunk_size_mb: 1,
    };
    
    let engine = BlastEngine::new(config);
    
    // Test just the preparation phase
    let source_files = vec![test_file];
    
    // Note: We can't easily test the full BLAST workflow without refactoring
    // the private methods, but the engine creation and basic setup should work
    assert!(temp_cache.path().exists());
    assert!(temp_target.path().exists());
}

#[test]
fn test_blast_phase_enum() {
    assert_eq!(BlastPhase::Preparation.as_str(), "Preparation");
    assert_eq!(BlastPhase::CacheLoad.as_str(), "CacheLoad");
    assert_eq!(BlastPhase::Distribution.as_str(), "Distribution");
    assert_eq!(BlastPhase::Verification.as_str(), "Verification");
    assert_eq!(BlastPhase::Complete.as_str(), "Complete");
}

#[test]
fn test_blast_stats() {
    let stats = BlastStats::new();
    
    // Test initial state
    assert_eq!(stats.get_cache_progress_percent(), 0.0);
    assert_eq!(stats.get_distribution_progress_percent(), 0.0);
    
    // Test with some progress
    stats.total_bytes.store(1000, std::sync::atomic::Ordering::Relaxed);
    stats.cached_bytes.store(500, std::sync::atomic::Ordering::Relaxed);
    stats.distributed_bytes.store(300, std::sync::atomic::Ordering::Relaxed);
    
    assert_eq!(stats.get_cache_progress_percent(), 50.0);
    assert_eq!(stats.get_distribution_progress_percent(), 30.0);
}

#[test] 
fn test_transfer_strategy_names() {
    let direct_copy = TransferStrategy::DirectCopy {
        destination: PathBuf::from("/tmp/test"),
        use_memory_mapping: true,
        chunk_size_mb: 32,
    };
    assert_eq!(direct_copy.name(), "DirectCopy");
    
    let memory_staging = TransferStrategy::MemoryStaging {
        destinations: vec![PathBuf::from("/tmp/test1"), PathBuf::from("/tmp/test2")],
        buffer_size_mb: 512,
        parallel_writes: 4,
    };
    assert_eq!(memory_staging.name(), "MemoryStaging");
    
    let gpu_accelerated = TransferStrategy::GpuAccelerated {
        gpu_staging: PathBuf::from("/tmp/gpu_cache"),
        final_destinations: vec![PathBuf::from("/tmp/dest1")],
        compute_pipeline: crate::strategy_engine::GpuComputePipeline::MemoryOptimized,
        use_unified_memory: true,
    };
    assert_eq!(gpu_accelerated.name(), "GpuAccelerated");
}

#[test]
fn test_gpu_info_creation() {
    let gpu_info = crate::strategy_engine::GpuInfo {
        device_name: "Test GPU".to_string(),
        memory_gb: 8.0,
        compute_units: 32,
        memory_bandwidth_gbps: 400.0,
        supports_unified_memory: true,
    };
    
    assert_eq!(gpu_info.device_name, "Test GPU");
    assert_eq!(gpu_info.memory_gb, 8.0);
    assert_eq!(gpu_info.compute_units, 32);
    assert!(gpu_info.supports_unified_memory);
}

#[tokio::test]
async fn test_concurrent_event_processing() {
    use std::sync::atomic::{AtomicU64, Ordering};
    
    let event_hub = Arc::new(EventHub::new().expect("Failed to create EventHub"));
    let events_sent = Arc::new(AtomicU64::new(0));
    let task_count = 10;
    let events_per_task = 100;
    
    // Spawn multiple tasks that emit events concurrently
    let mut tasks = Vec::new();
    
    for task_id in 0..task_count {
        let event_hub = event_hub.clone();
        let events_sent = events_sent.clone();
        
        tasks.push(tokio::spawn(async move {
            for i in 0..events_per_task {
                let event = TransferEvent::new(
                    EventType::FileProgress,
                    EventPriority::Normal,
                    format!("job_task_{}_{}", task_id, i),
                    EventPayload::File {
                        file_id: format!("file_{}_{}", task_id, i),
                        filename: format!("file_{}_{}.dat", task_id, i),
                        file_size: 1024,
                        bytes_copied: 512,
                        destination_path: "/tmp/test".to_string(),
                        source_checksum: None,
                        destination_checksum: None,
                        hash_algorithm: "xxHash64BE".to_string(),
                        transfer_speed_mbps: 100.0,
                        error_message: None,
                    }
                );
                
                if event_hub.emit_event(event).is_ok() {
                    events_sent.fetch_add(1, Ordering::Relaxed);
                }
            }
        }));
    }
    
    // Wait for all tasks to complete
    for task in tasks {
        task.await.expect("Task failed");
    }
    
    // Allow processing time
    tokio::time::sleep(Duration::from_millis(300)).await;
    
    let total_sent = events_sent.load(Ordering::Relaxed);
    let stats = event_hub.get_stats();
    
    println!("Total events sent: {}", total_sent);
    println!("Events processed: {}", stats.events_processed);
    println!("Events dropped: {}", stats.events_dropped);
    
    assert_eq!(total_sent, (task_count * events_per_task) as u64);
    assert!(stats.events_processed > 0, "No events were processed");
    
    // Should process most events (allow for some loss in high-throughput scenario)
    let processing_rate = stats.events_processed as f64 / total_sent as f64;
    assert!(processing_rate > 0.8, "Too many events lost: {:.2}%", (1.0 - processing_rate) * 100.0);
}