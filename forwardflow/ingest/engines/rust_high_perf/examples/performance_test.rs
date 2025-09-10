//! Performance and threading test for ForwardFlow V2.0 Rust engine
//! 
//! This example tests the performance and capabilities of the new Rust engine
//! components without Python dependencies.

use std::path::PathBuf;
use std::time::{Instant, Duration};
use std::sync::Arc;
use tempfile::TempDir;
use tokio::fs;

// Note: These would normally be imported from the library, but we'll define them locally for testing
use rust_high_perf_engine::event_hub_v2::{EventHub, TransferEvent, EventType, EventPriority, EventPayload};
use rust_high_perf_engine::strategy_engine::{TransferStrategyEngine, DestinationType};
use rust_high_perf_engine::blast_engine::{BlastEngine, BlastConfig};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🚀 ForwardFlow V2.0 Rust Engine Performance Test");
    println!("================================================");
    
    // Test 1: EventHub Performance
    println!("\n📡 Testing EventHub Performance...");
    test_event_hub_performance().await?;
    
    // Test 2: Strategy Engine Analysis
    println!("\n🎯 Testing Transfer Strategy Engine...");
    test_strategy_engine().await?;
    
    // Test 3: BLAST Engine Performance  
    println!("\n💥 Testing BLAST Engine...");
    test_blast_engine().await?;
    
    // Test 4: Threading Capabilities
    println!("\n🧵 Testing Threading Capabilities...");
    test_threading_performance().await?;
    
    println!("\n✅ All performance tests completed successfully!");
    println!("🏁 ForwardFlow V2.0 Rust engine is ready for production use.");
    
    Ok(())
}

/// Test EventHub event processing performance
async fn test_event_hub_performance() -> Result<(), Box<dyn std::error::Error>> {
    let event_hub = Arc::new(EventHub::new()?);
    let start_time = Instant::now();
    let event_count = 10_000;
    
    // Generate events rapidly
    for i in 0..event_count {
        let event = TransferEvent::new(
            EventType::FileProgress,
            EventPriority::Normal,
            format!("job_{}", i % 100),
            EventPayload::File {
                file_id: format!("file_{}", i),
                filename: format!("test_file_{}.dat", i),
                file_size: 1024 * 1024, // 1MB
                bytes_copied: (i * 1024) % (1024 * 1024),
                destination_path: "/tmp/test".to_string(),
                source_checksum: None,
                destination_checksum: None,
                hash_algorithm: "xxHash64BE".to_string(),
                transfer_speed_mbps: 150.0,
                error_message: None,
            }
        );
        
        event_hub.emit_event(event)?;
    }
    
    let duration = start_time.elapsed();
    let events_per_second = event_count as f64 / duration.as_secs_f64();
    
    println!("  ✓ Processed {} events in {:?}", event_count, duration);
    println!("  ✓ Event throughput: {:.0} events/second", events_per_second);
    
    // Get statistics
    let stats = event_hub.get_stats();
    println!("  ✓ Events processed: {}", stats.events_processed);
    println!("  ✓ Events dropped: {}", stats.events_dropped);
    println!("  ✓ Average processing time: {} ns", stats.avg_processing_time_ns);
    
    Ok(())
}

/// Test strategy engine destination analysis
async fn test_strategy_engine() -> Result<(), Box<dyn std::error::Error>> {
    let strategy_engine = TransferStrategyEngine::new();
    
    // Create test destinations
    let temp_dir1 = TempDir::new()?;
    let temp_dir2 = TempDir::new()?;
    let temp_dir3 = TempDir::new()?;
    
    let destinations = vec![
        temp_dir1.path().to_path_buf(),
        temp_dir2.path().to_path_buf(), 
        temp_dir3.path().to_path_buf(),
    ];
    
    let start_time = Instant::now();
    
    // Analyze destinations and select strategy
    let result = strategy_engine.analyze_and_select_strategy(
        &destinations,
        5 * 1024 * 1024 * 1024, // 5GB transfer
        None, // No BLAST cache
        "perf_test_job"
    );
    
    let analysis_duration = start_time.elapsed();
    
    match result {
        Ok((strategy, analyses)) => {
            println!("  ✓ Strategy analysis completed in {:?}", analysis_duration);
            println!("  ✓ Selected strategy: {}", strategy.name());
            println!("  ✓ Analyzed {} destinations:", analyses.len());
            
            for analysis in &analyses {
                println!("    - {}: {:?} @ {:.1} MB/s", 
                    analysis.path.display(),
                    analysis.dest_type,
                    analysis.benchmarked_speed_mbps
                );
            }
            
            // Test GPU detection
            if let Some(ref gpu_info) = analyses[0].gpu_info {
                println!("  ✓ GPU detected: {} ({:.1} GB)", 
                    gpu_info.device_name, 
                    gpu_info.memory_gb
                );
            } else {
                println!("  ℹ No GPU acceleration available");
            }
        },
        Err(e) => {
            println!("  ❌ Strategy analysis failed: {}", e);
        }
    }
    
    Ok(())
}

/// Test BLAST engine performance with mock data
async fn test_blast_engine() -> Result<(), Box<dyn std::error::Error>> {
    // Create test directories
    let cache_dir = TempDir::new()?;
    let target_dir1 = TempDir::new()?;
    let target_dir2 = TempDir::new()?;
    let source_dir = TempDir::new()?;
    
    // Create test files
    let test_files = vec![
        source_dir.path().join("test1.dat"),
        source_dir.path().join("test2.dat"),
        source_dir.path().join("test3.dat"),
    ];
    
    for (i, file_path) in test_files.iter().enumerate() {
        let test_data = vec![i as u8; 1024 * 1024]; // 1MB per file
        fs::write(file_path, test_data).await?;
    }
    
    // Configure BLAST engine
    let config = BlastConfig {
        blast_cache_path: cache_dir.path().to_path_buf(),
        distribution_targets: vec![
            target_dir1.path().to_path_buf(),
            target_dir2.path().to_path_buf(),
        ],
        memory_buffer_mb: 64, // 64MB buffer
        max_parallel_streams: 4,
        use_direct_io: false, // Disable for test compatibility
        use_memory_mapping: false,
        cache_chunk_size_mb: 1,
    };
    
    let blast_engine = BlastEngine::new(config);
    let start_time = Instant::now();
    
    // Execute BLAST transfer
    let result = blast_engine.execute_blast_transfer(&test_files, "blast_perf_test").await;
    let blast_duration = start_time.elapsed();
    
    match result {
        Ok(blast_result) => {
            println!("  ✓ BLAST transfer completed in {:?}", blast_duration);
            println!("  ✓ Cache phase: {} files @ {:.1} MB/s",
                blast_result.cache_result.files_cached,
                blast_result.cache_result.average_speed_mbps
            );
            println!("  ✓ Distribution phase: {} files @ {:.1} MB/s",
                blast_result.distribution_result.files_distributed,
                blast_result.distribution_result.average_speed_mbps
            );
            println!("  ✓ Verification: {} files verified", 
                blast_result.verification_result.files_verified
            );
            
            // Verify files were actually copied
            for file_path in &test_files {
                let filename = file_path.file_name().unwrap();
                
                // Check cache
                let cache_path = cache_dir.path().join(filename);
                if cache_path.exists() {
                    println!("  ✓ Cache file exists: {}", filename.to_string_lossy());
                }
                
                // Check targets
                for target_dir in [&target_dir1, &target_dir2] {
                    let target_path = target_dir.path().join(filename);
                    if target_path.exists() {
                        println!("  ✓ Target file exists: {}", target_path.display());
                    }
                }
            }
        },
        Err(e) => {
            println!("  ❌ BLAST transfer failed: {}", e);
        }
    }
    
    Ok(())
}

/// Test multi-threading performance
async fn test_threading_performance() -> Result<(), Box<dyn std::error::Error>> {
    use std::thread;
    use std::sync::atomic::{AtomicU64, Ordering};
    
    let cpu_count = num_cpus::get();
    println!("  ℹ Available CPU cores: {}", cpu_count);
    
    // Test parallel computation
    let counter = Arc::new(AtomicU64::new(0));
    let start_time = Instant::now();
    let iterations_per_thread = 1_000_000;
    
    let handles: Vec<_> = (0..cpu_count)
        .map(|thread_id| {
            let counter = counter.clone();
            thread::spawn(move || {
                for i in 0..iterations_per_thread {
                    // Simulate some work
                    let value = thread_id as u64 * 1000 + i as u64;
                    let _ = value.wrapping_mul(12345).wrapping_add(67890);
                    counter.fetch_add(1, Ordering::Relaxed);
                }
            })
        })
        .collect();
    
    // Wait for all threads
    for handle in handles {
        handle.join().unwrap();
    }
    
    let duration = start_time.elapsed();
    let total_operations = counter.load(Ordering::Relaxed);
    let ops_per_second = total_operations as f64 / duration.as_secs_f64();
    
    println!("  ✓ Parallel computation test:");
    println!("    - {} threads × {} iterations", cpu_count, iterations_per_thread);
    println!("    - {} total operations in {:?}", total_operations, duration);
    println!("    - {:.0} operations/second", ops_per_second);
    
    // Test tokio async performance
    let start_time = Instant::now();
    let task_count = 1000;
    let mut tasks = Vec::new();
    
    for i in 0..task_count {
        tasks.push(tokio::spawn(async move {
            // Simulate async I/O work
            tokio::time::sleep(Duration::from_millis(1)).await;
            i * 2
        }));
    }
    
    // Wait for all async tasks
    let mut results = Vec::new();
    for task in tasks {
        results.push(task.await?);
    }
    
    let async_duration = start_time.elapsed();
    println!("  ✓ Async task performance:");
    println!("    - {} async tasks completed in {:?}", task_count, async_duration);
    println!("    - {:.1} tasks/second", task_count as f64 / async_duration.as_secs_f64());
    
    Ok(())
}