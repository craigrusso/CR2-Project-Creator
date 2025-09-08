//! File I/O operations and parallel processing

use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write, BufReader, BufWriter};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::sync::atomic::AtomicBool;
use std::time::Instant;
use std::thread;
use std::sync::mpsc;
use std::time::Duration;
use anyhow::Result;
use rayon::prelude::*;
use walkdir::WalkDir;
use pyo3::prelude::*;

use crate::data_structures::FileTransferRecord;
use crate::platform_helpers::{get_disk_space, create_dir_all_safe, get_file_size};
use crate::verification::{HashCalculator, HashAlgorithm};

/// File operation result
#[derive(Debug, Clone)]
pub struct FileOperationResult {
    pub success: bool,
    pub bytes_copied: u64,
    pub error_message: Option<String>,
    pub operation_time_ms: u64,
}

impl FileOperationResult {
    pub fn new(success: bool, bytes_copied: u64, error_message: Option<String>, operation_time_ms: u64) -> Self {
        Self {
            success,
            bytes_copied,
            error_message,
            operation_time_ms,
        }
    }
}

/// File operation manager
pub struct FileOperationManager {
    buffer_size: usize,
    use_direct_io: bool,
    parallel_workers: usize,
}

impl FileOperationManager {
    pub fn new(buffer_size: usize, use_direct_io: bool, parallel_workers: usize) -> Self {
        Self {
            buffer_size,
            use_direct_io,
            parallel_workers,
        }
    }
    
    /// Collect all files from source paths
    pub fn collect_files(&self, source_paths: &[String]) -> Result<Vec<PathBuf>> {
        let mut all_files = Vec::new();
        
        for source_path in source_paths {
            let path = Path::new(source_path);
            if path.is_file() {
                all_files.push(path.to_path_buf());
            } else if path.is_dir() {
                for entry in WalkDir::new(path)
                    .into_iter()
                    .filter_map(|e| e.ok())
                    .filter(|e| e.file_type().is_file())
                {
                    all_files.push(entry.path().to_path_buf());
                }
            }
        }
        
        Ok(all_files)
    }
    
    /// Copy a single file with progress tracking
    pub fn copy_single_file(
        &self,
        source_path: &Path,
        destination_path: &Path,
        progress_callback: Option<Box<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> Result<FileOperationResult> {
        let start_time = Instant::now();
        
        // Ensure destination directory exists
        if let Some(parent) = destination_path.parent() {
            create_dir_all_safe(parent)?;
        }
        
        // Check disk space
        let source_size = get_file_size(source_path)?;
        let disk_space = get_disk_space(destination_path.parent().unwrap_or(Path::new(".")))?;
        
        if disk_space.available_bytes < source_size {
            return Err(anyhow::anyhow!(
                "Insufficient disk space. Required: {} bytes, Available: {} bytes",
                source_size,
                disk_space.available_bytes
            ));
        }
        
        // Open source and destination files
        let source_file = File::open(source_path)?;
        let destination_file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(destination_path)?;
        
        let mut reader = BufReader::new(source_file);
        let mut writer = BufWriter::new(destination_file);
        
        let mut buffer = vec![0u8; self.buffer_size];
        let mut total_copied = 0u64;
        
        loop {
            let bytes_read = reader.read(&mut buffer)?;
            if bytes_read == 0 {
                break;
            }
            
            writer.write_all(&buffer[..bytes_read])?;
            total_copied += bytes_read as u64;
            
            // Call progress callback if provided
            if let Some(ref callback) = progress_callback {
                callback(total_copied, source_size);
            }
        }
        
        writer.flush()?;
        
        let operation_time = start_time.elapsed().as_millis() as u64;
        
        Ok(FileOperationResult::new(
            true,
            total_copied,
            None,
            operation_time,
        ))
    }
    
    /// Copy a single file with cancellation support
    pub fn copy_single_file_with_cancellation(
        &self,
        source_path: &Path,
        destination_path: &Path,
        progress_callback: Option<Box<dyn Fn(u64, u64) + Send + Sync>>,
        cancelled: &AtomicBool,
    ) -> Result<FileOperationResult> {
        let start_time = std::time::Instant::now();
        let source_size = get_file_size(source_path)?;
        
        // Create destination directory if it doesn't exist
        if let Some(parent) = destination_path.parent() {
            create_dir_all_safe(parent)?;
        }
        
        // Open source and destination files
        let source_file = File::open(source_path)?;
        let destination_file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(destination_path)?;
        
        let mut reader = BufReader::new(source_file);
        let mut writer = BufWriter::new(destination_file);
        
        let mut buffer = vec![0u8; self.buffer_size];
        let mut total_copied = 0u64;
        let mut bytes_since_last_check = 0u64;
        const CANCELLATION_CHECK_INTERVAL: u64 = 64 * 1024; // Check every 64KB for faster response
        
        loop {
            // Check for cancellation BEFORE reading
            if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                println!("DEBUG: File copy cancelled before read");
                return Err(anyhow::anyhow!("Operation cancelled"));
            }
            
            let bytes_read = reader.read(&mut buffer)?;
            if bytes_read == 0 {
                break;
            }
            
            writer.write_all(&buffer[..bytes_read])?;
            total_copied += bytes_read as u64;
            bytes_since_last_check += bytes_read as u64;
            
            // Check for cancellation every 64KB copied
            if bytes_since_last_check >= CANCELLATION_CHECK_INTERVAL {
                if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                    println!("DEBUG: File copy cancelled during transfer");
                    return Err(anyhow::anyhow!("Operation cancelled"));
                }
                bytes_since_last_check = 0;
            }
            
            // Call progress callback if provided
            if let Some(ref callback) = progress_callback {
                callback(total_copied, source_size);
            }
        }
        
        writer.flush()?;
        
        let operation_time = start_time.elapsed().as_millis() as u64;
        
        Ok(FileOperationResult::new(
            true,
            total_copied,
            None,
            operation_time,
        ))
    }
    
    /// Copy multiple files in parallel
    pub fn copy_files_parallel(
        &self,
        source_files: &[PathBuf],
        destination_dir: &Path,
        progress_callback: Option<Box<dyn Fn(usize, usize) + Send + Sync>>,
    ) -> Result<Vec<FileOperationResult>> {
        let results: Vec<Result<FileOperationResult>> = source_files
            .par_iter()
            .enumerate()
            .map(|(index, source_path)| {
                let filename = source_path.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown");
                
                let destination_path = destination_dir.join(filename);
                
                let result = self.copy_single_file(source_path, &destination_path, None);
                
                // Call progress callback if provided
                if let Some(ref callback) = progress_callback {
                    callback(index + 1, source_files.len());
                }
                
                result
            })
            .collect();
        
        // Convert results to proper format
        let mut final_results = Vec::new();
        for result in results {
            match result {
                Ok(op_result) => final_results.push(op_result),
                Err(e) => final_results.push(FileOperationResult::new(
                    false,
                    0,
                    Some(e.to_string()),
                    0,
                )),
            }
        }
        
        Ok(final_results)
    }
    
    /// Copy multiple files in parallel with cancellation support
    pub fn copy_files_parallel_with_cancellation(
        &self,
        source_files: &[PathBuf],
        destination_dir: &Path,
        progress_callback: Option<Box<dyn Fn(usize, usize) + Send + Sync>>,
        cancelled: &AtomicBool,
    ) -> Result<Vec<FileOperationResult>> {
        let mut results = Vec::new();
        
        for (index, source_path) in source_files.iter().enumerate() {
            // Check for cancellation before processing each file
            if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                println!("DEBUG: Copy operation cancelled during file processing");
                return Err(anyhow::anyhow!("Operation cancelled"));
            }
            
            let filename = source_path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown");
            
            let destination_path = destination_dir.join(filename);
            
            // Copy single file with cancellation checks
            let result = self.copy_single_file_with_cancellation(source_path, &destination_path, None, cancelled)?;
            results.push(result);
            
            // Call progress callback if provided
            if let Some(ref callback) = progress_callback {
                callback(index + 1, source_files.len());
            }
        }
        
        Ok(results)
    }
    
    /// Copy multiple files in parallel with immediate cancellation support using threads
    pub fn copy_files_parallel_with_cancellation_threaded(
        &self,
        source_files: &[PathBuf],
        destination_dir: &Path,
        progress_callback: Option<Box<dyn Fn(usize, usize) + Send + Sync>>,
        cancelled: Arc<AtomicBool>,
    ) -> Result<Vec<FileOperationResult>> {
        use std::thread;
        use std::sync::mpsc;
        use std::time::Duration;
        
        let (tx, rx) = mpsc::channel();
        let mut handles = Vec::new();
        let mut results = Vec::new();
        
        // Spawn a thread for each file copy operation
        for (index, source_path) in source_files.iter().enumerate() {
            // Check for cancellation before spawning thread
            if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                println!("DEBUG: Copy operation cancelled before spawning threads");
                return Err(anyhow::anyhow!("Operation cancelled"));
            }
            
            let source_path = source_path.clone();
            let dest_dir = destination_dir.to_path_buf();
            let tx = tx.clone();
            let cancelled = cancelled.clone();
            
            let handle = thread::spawn(move || {
                let filename = source_path.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown");
                
                let destination_path = dest_dir.join(filename);
                
                // Copy single file with cancellation checks
                let result = match Self::copy_single_file_with_cancellation_internal(
                    &source_path, 
                    &destination_path, 
                    None, 
                    &cancelled
                ) {
                    Ok(result) => result,
                    Err(e) => FileOperationResult::new(false, 0, Some(e.to_string()), 0),
                };
                
                let _ = tx.send((index, result));
            });
            
            handles.push(handle);
        }
        
        // Collect results with cancellation checks
        let mut completed = 0;
        while completed < source_files.len() {
            // Check for cancellation every 100ms
            if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                println!("DEBUG: Copy operation cancelled during result collection");
                return Err(anyhow::anyhow!("Operation cancelled"));
            }
            
            match rx.recv_timeout(Duration::from_millis(100)) {
                Ok((index, result)) => {
                    results.push((index, result));
                    completed += 1;
                    
                    // Call progress callback if provided
                    if let Some(ref callback) = progress_callback {
                        callback(completed, source_files.len());
                    }
                }
                Err(mpsc::RecvTimeoutError::Timeout) => {
                    // Continue waiting
                    continue;
                }
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    // All threads finished
                    break;
                }
            }
        }
        
        // Wait for all threads to finish
        for handle in handles {
            let _ = handle.join();
        }
        
        // Sort results by index and extract FileOperationResult
        results.sort_by_key(|(index, _)| *index);
        Ok(results.into_iter().map(|(_, result)| result).collect())
    }
    
    /// Internal copy function for threaded operations
    fn copy_single_file_with_cancellation_internal(
        source_path: &Path,
        destination_path: &Path,
        progress_callback: Option<Box<dyn Fn(u64, u64) + Send + Sync>>,
        cancelled: &AtomicBool,
    ) -> Result<FileOperationResult> {
        let start_time = std::time::Instant::now();
        let source_size = get_file_size(source_path)?;
        
        // Create destination directory if it doesn't exist
        if let Some(parent) = destination_path.parent() {
            create_dir_all_safe(parent)?;
        }
        
        // Open source and destination files
        let source_file = File::open(source_path)?;
        let destination_file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(destination_path)?;
        
        let mut reader = BufReader::new(source_file);
        let mut writer = BufWriter::new(destination_file);
        
        let mut buffer = vec![0u8; 4 * 1024 * 1024]; // 4MB buffer
        let mut total_copied = 0u64;
        let mut bytes_since_last_check = 0u64;
        const CANCELLATION_CHECK_INTERVAL: u64 = 64 * 1024; // Check every 64KB for faster response
        
        loop {
            // Check for cancellation BEFORE reading
            if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                println!("DEBUG: Internal file copy cancelled before read");
                return Err(anyhow::anyhow!("Operation cancelled"));
            }
            
            let bytes_read = reader.read(&mut buffer)?;
            if bytes_read == 0 {
                break;
            }
            
            writer.write_all(&buffer[..bytes_read])?;
            total_copied += bytes_read as u64;
            bytes_since_last_check += bytes_read as u64;
            
            // Check for cancellation every 64KB copied
            if bytes_since_last_check >= CANCELLATION_CHECK_INTERVAL {
                if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                    println!("DEBUG: Internal file copy cancelled during transfer");
                    return Err(anyhow::anyhow!("Operation cancelled"));
                }
                bytes_since_last_check = 0;
            }
            
            // Call progress callback if provided
            if let Some(ref callback) = progress_callback {
                callback(total_copied, source_size);
            }
        }
        
        writer.flush()?;
        
        let operation_time = start_time.elapsed().as_millis() as u64;
        
        Ok(FileOperationResult::new(
            true,
            total_copied,
            None,
            operation_time,
        ))
    }
    
    /// Copy files to multiple destinations
    pub fn copy_to_multiple_destinations(
        &self,
        source_files: &[PathBuf],
        destination_paths: &[String],
        progress_callback: Option<Box<dyn Fn(usize, usize) + Send + Sync>>,
    ) -> Result<Vec<FileOperationResult>> {
        let mut all_results = Vec::new();
        
        for (dest_index, dest_path) in destination_paths.iter().enumerate() {
            let dest_dir = Path::new(dest_path);
            
            // Create destination directory if it doesn't exist
            create_dir_all_safe(dest_dir)?;
            
            // Copy files to this destination
            let results = self.copy_files_parallel(source_files, dest_dir, None)?;
            all_results.extend(results);
            
            // Call progress callback
            if let Some(ref callback) = progress_callback {
                callback(dest_index + 1, destination_paths.len());
            }
        }
        
        Ok(all_results)
    }
    
    /// Copy files to multiple destinations with cancellation support
    pub fn copy_to_multiple_destinations_with_cancellation(
        &self,
        source_files: &[PathBuf],
        destination_paths: &[String],
        progress_callback: Option<Box<dyn Fn(usize, usize) + Send + Sync>>,
        cancelled: &AtomicBool,
    ) -> Result<Vec<FileOperationResult>> {
        let mut all_results = Vec::new();
        
        for (dest_index, dest_path) in destination_paths.iter().enumerate() {
            // Check for cancellation before processing each destination
            if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                println!("DEBUG: Multiple destinations copy cancelled");
                return Err(anyhow::anyhow!("Operation cancelled"));
            }
            
            let dest_dir = Path::new(dest_path);
            
            // Create destination directory if it doesn't exist
            create_dir_all_safe(dest_dir)?;
            
            // Copy files to this destination with cancellation support
            let results = self.copy_files_parallel_with_cancellation(source_files, dest_dir, None, cancelled)?;
            all_results.extend(results);
            
            // Call progress callback
            if let Some(ref callback) = progress_callback {
                callback(dest_index + 1, destination_paths.len());
            }
        }
        
        Ok(all_results)
    }
    
    /// Copy files to multiple destinations with immediate cancellation support using threads
    pub fn copy_to_multiple_destinations_with_cancellation_threaded(
        &self,
        source_files: &[PathBuf],
        destination_paths: &[String],
        progress_callback: Option<Box<dyn Fn(usize, usize) + Send + Sync>>,
        cancelled: Arc<AtomicBool>,
    ) -> Result<Vec<FileOperationResult>> {
        let mut all_results = Vec::new();
        
        for (dest_index, dest_path) in destination_paths.iter().enumerate() {
            // Check for cancellation before processing each destination
            if cancelled.load(std::sync::atomic::Ordering::Relaxed) {
                println!("DEBUG: Multiple destinations copy cancelled");
                return Err(anyhow::anyhow!("Operation cancelled"));
            }
            
            let dest_dir = Path::new(dest_path);
            
            // Create destination directory if it doesn't exist
            create_dir_all_safe(dest_dir)?;
            
            // Copy files to this destination with threaded cancellation support
            let results = self.copy_files_parallel_with_cancellation_threaded(source_files, dest_dir, None, Arc::clone(&cancelled))?;
            all_results.extend(results);
            
            // Call progress callback
            if let Some(ref callback) = progress_callback {
                callback(dest_index + 1, destination_paths.len());
            }
        }
        
        Ok(all_results)
    }
    
    /// Verify file integrity after copy
    pub fn verify_file_integrity(
        &self,
        source_path: &Path,
        destination_path: &Path,
        hash_algorithm: &str,
    ) -> Result<bool> {
        let calculator = HashCalculator::new(HashAlgorithm::from_string(hash_algorithm));
        
        let source_hash = calculator.calculate_file_hash(source_path)?;
        let dest_hash = calculator.calculate_file_hash(destination_path)?;
        
        Ok(source_hash == dest_hash)
    }
    
    /// Get file information
    pub fn get_file_info(&self, file_path: &Path) -> Result<FileTransferRecord> {
        let metadata = fs::metadata(file_path)?;
        let filename = file_path.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown")
            .to_string();
        
        Ok(FileTransferRecord {
            source_path: file_path.to_string_lossy().to_string(),
            destination_path: String::new(), // Will be set during copy
            filename,
            file_size: metadata.len(),
            checksum_source: String::new(), // Will be calculated during verification
            checksum_destination: String::new(),
            status: "PENDING".to_string(),
            error_message: String::new(),
            transfer_speed_mib_s: 0.0,
            verification_passed: false,
            verification_error: String::new(),
        })
    }
    
    /// Calculate optimal buffer size based on file size
    pub fn calculate_optimal_buffer_size(&self, file_size: u64) -> usize {
        const MIN_BUFFER_SIZE: usize = 64 * 1024; // 64KB
        const MAX_BUFFER_SIZE: usize = 16 * 1024 * 1024; // 16MB
        const TARGET_BUFFER_SIZE: usize = 4 * 1024 * 1024; // 4MB
        
        if file_size < 1024 * 1024 {
            // Small files: use smaller buffer
            MIN_BUFFER_SIZE
        } else if file_size > 100 * 1024 * 1024 {
            // Large files: use larger buffer
            MAX_BUFFER_SIZE
        } else {
            // Medium files: use target buffer size
            TARGET_BUFFER_SIZE
        }
    }
    
    /// Get file transfer statistics
    pub fn get_transfer_stats(&self, results: &[FileOperationResult]) -> (u64, usize, usize) {
        let total_bytes: u64 = results.iter().map(|r| r.bytes_copied).sum();
        let successful_operations = results.iter().filter(|r| r.success).count();
        let failed_operations = results.iter().filter(|r| !r.success).count();
        
        (total_bytes, successful_operations, failed_operations)
    }
}

/// Python wrapper for FileOperationManager
#[pyclass]
pub struct PyFileOperationManager {
    inner: Arc<FileOperationManager>,
}

#[pymethods]
impl PyFileOperationManager {
    #[new]
    fn new(buffer_size: usize, use_direct_io: bool, parallel_workers: usize) -> Self {
        Self {
            inner: Arc::new(FileOperationManager::new(buffer_size, use_direct_io, parallel_workers)),
        }
    }
    
    fn collect_files(&self, source_paths: Vec<String>) -> PyResult<Vec<String>> {
        match self.inner.collect_files(&source_paths) {
            Ok(files) => Ok(files.into_iter().map(|p| p.to_string_lossy().to_string()).collect()),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
        }
    }
    
    fn copy_single_file(&self, source_path: String, destination_path: String) -> PyResult<PyObject> {
        let source_path = Path::new(&source_path);
        let destination_path = Path::new(&destination_path);
        
        match self.inner.copy_single_file(source_path, destination_path, None) {
            Ok(result) => {
                Python::with_gil(|py| {
                    let py_result = pyo3::types::PyDict::new(py);
                    py_result.set_item("success", result.success)?;
                    py_result.set_item("bytes_copied", result.bytes_copied)?;
                    if let Some(error) = result.error_message {
                        py_result.set_item("error_message", error)?;
                    }
                    py_result.set_item("operation_time_ms", result.operation_time_ms)?;
                    
                    Ok(py_result.into_py(py))
                })
            },
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
        }
    }
    
    fn copy_files_parallel(&self, source_files: Vec<String>, destination_dir: String) -> PyResult<Vec<PyObject>> {
        let source_paths: Vec<PathBuf> = source_files.into_iter().map(PathBuf::from).collect();
        let dest_dir = Path::new(&destination_dir);
        
        match self.inner.copy_files_parallel(&source_paths, dest_dir, None) {
            Ok(results) => {
                Python::with_gil(|py| {
                    let mut py_results = Vec::new();
                    for result in results {
                        let py_result = pyo3::types::PyDict::new(py);
                        py_result.set_item("success", result.success)?;
                        py_result.set_item("bytes_copied", result.bytes_copied)?;
                        if let Some(error) = result.error_message {
                            py_result.set_item("error_message", error)?;
                        }
                        py_result.set_item("operation_time_ms", result.operation_time_ms)?;
                        py_results.push(py_result.into_py(py));
                    }
                    Ok(py_results)
                })
            },
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
        }
    }
    
    fn verify_file_integrity(&self, source_path: String, destination_path: String, hash_algorithm: String) -> PyResult<bool> {
        let source_path = Path::new(&source_path);
        let destination_path = Path::new(&destination_path);
        
        match self.inner.verify_file_integrity(source_path, destination_path, &hash_algorithm) {
            Ok(result) => Ok(result),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
        }
    }
    
    fn get_file_info(&self, file_path: String) -> PyResult<FileTransferRecord> {
        let file_path = Path::new(&file_path);
        match self.inner.get_file_info(file_path) {
            Ok(result) => Ok(result),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
        }
    }
}

/// Register Python types for this module
pub fn register_python_types(m: &PyModule) -> PyResult<()> {
    m.add_class::<PyFileOperationManager>()?;
    Ok(())
}
