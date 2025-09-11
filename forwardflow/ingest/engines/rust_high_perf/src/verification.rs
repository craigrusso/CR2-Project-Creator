//! Hash verification and integrity checking

use std::collections::HashMap;
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::Path;
use std::sync::{Arc, Mutex};
use std::hash::Hasher;
use anyhow::Result;
use xxhash_rust::xxh3::Xxh3;
use sha2::{Sha256, Digest};
use sha3::Sha3_256;
use md5;
use blake3::Hasher as Blake3Hasher;

use crate::data_structures::FileTransferRecord;
use pyo3::prelude::*;
use pyo3::IntoPy;

/// Supported hash algorithms
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum HashAlgorithm {
    XxHash64,
    XxHash64BE,
    XxHash128,
    Sha256,
    Sha3,
    Md5,
    Blake3,
}

impl HashAlgorithm {
    pub fn from_string(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "xxhash64" | "xxhash64be" | "xxh3" => HashAlgorithm::XxHash64,
            "xxhash128" => HashAlgorithm::XxHash128,
            "sha256" | "sha-256" => HashAlgorithm::Sha256,
            "sha3" | "sha-3" => HashAlgorithm::Sha3,
            "md5" => HashAlgorithm::Md5,
            "blake3" => HashAlgorithm::Blake3,
            _ => HashAlgorithm::XxHash64, // Default to xxHash64 for best performance
        }
    }
    
    pub fn parse(s: &str) -> Result<Self, String> {
        Ok(Self::from_string(s))
    }
    
    pub fn to_string(&self) -> String {
        match self {
            HashAlgorithm::XxHash64 => "xxhash64".to_string(),
            HashAlgorithm::XxHash64BE => "xxhash64be".to_string(),
            HashAlgorithm::XxHash128 => "xxhash128".to_string(),
            HashAlgorithm::Sha256 => "sha256".to_string(),
            HashAlgorithm::Sha3 => "sha3".to_string(),
            HashAlgorithm::Md5 => "md5".to_string(),
            HashAlgorithm::Blake3 => "blake3".to_string(),
        }
    }
}

/// Hash verification result
#[derive(Debug, Clone)]
pub struct HashVerificationResult {
    pub algorithm: HashAlgorithm,
    pub source_hash: String,
    pub destination_hash: String,
    pub verification_passed: bool,
    pub error_message: Option<String>,
    pub verification_time_ms: u64,
}

impl HashVerificationResult {
    pub fn new(
        algorithm: HashAlgorithm,
        source_hash: String,
        destination_hash: String,
        verification_passed: bool,
        error_message: Option<String>,
        verification_time_ms: u64,
    ) -> Self {
        Self {
            algorithm,
            source_hash,
            destination_hash,
            verification_passed,
            error_message,
            verification_time_ms,
        }
    }
}

/// Hash calculator for different algorithms
#[derive(Clone)]
pub struct HashCalculator {
    algorithm: HashAlgorithm,
}

impl HashCalculator {
    pub fn new(algorithm: HashAlgorithm) -> Self {
        Self { algorithm }
    }
    
    /// Calculate hash for a file
    pub fn calculate_file_hash(&self, file_path: &Path) -> Result<String> {
        let mut file = File::open(file_path)?;
        let mut buffer = vec![0u8; 64 * 1024]; // 64KB buffer
        
        match self.algorithm {
            HashAlgorithm::XxHash64 | HashAlgorithm::XxHash64BE => {
                // Use xxHash3 for both XxHash64 variants
                let mut hasher = Xxh3::new();
                loop {
                    let bytes_read = file.read(&mut buffer)?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.write(&buffer[..bytes_read]);
                }
                Ok(format!("{:016x}", hasher.finish()))
            }
            
            HashAlgorithm::XxHash128 => {
                // Use xxHash3 with 128-bit output (using same as 64-bit for compatibility)
                let mut hasher = Xxh3::new();
                loop {
                    let bytes_read = file.read(&mut buffer)?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.write(&buffer[..bytes_read]);
                }
                Ok(format!("{:032x}", hasher.finish()))
            }
            
            HashAlgorithm::Sha256 => {
                let mut hasher = Sha256::new();
                loop {
                    let bytes_read = file.read(&mut buffer)?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.update(&buffer[..bytes_read]);
                }
                Ok(format!("{:x}", hasher.finalize()))
            }
            
            HashAlgorithm::Sha3 => {
                let mut hasher = Sha3_256::new();
                loop {
                    let bytes_read = file.read(&mut buffer)?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.update(&buffer[..bytes_read]);
                }
                Ok(format!("{:x}", hasher.finalize()))
            }
            
            HashAlgorithm::Md5 => {
                let mut hasher = md5::Context::new();
                loop {
                    let bytes_read = file.read(&mut buffer)?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.consume(&buffer[..bytes_read]);
                }
                Ok(format!("{:x}", hasher.compute()))
            }
            
            HashAlgorithm::Blake3 => {
                let mut hasher = Blake3Hasher::new();
                loop {
                    let bytes_read = file.read(&mut buffer)?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.update(&buffer[..bytes_read]);
                }
                Ok(hasher.finalize().to_hex().to_string())
            }
        }
    }
    
    /// Calculate hash for a specific range of a file
    pub fn calculate_file_range_hash(
        &self,
        file_path: &Path,
        start_offset: u64,
        length: u64,
    ) -> Result<String> {
        let mut file = File::open(file_path)?;
        file.seek(SeekFrom::Start(start_offset))?;
        
        let mut buffer = vec![0u8; 64 * 1024]; // 64KB buffer
        let mut remaining = length;
        
        match self.algorithm {
            HashAlgorithm::XxHash64 => {
                let mut hasher = Xxh3::new();
                while remaining > 0 {
                    let bytes_to_read = std::cmp::min(remaining as usize, buffer.len());
                    let bytes_read = file.read(&mut buffer[..bytes_to_read])?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.update(&buffer[..bytes_to_read]);
                    remaining -= bytes_read as u64;
                }
                Ok(format!("{:016x}", hasher.finish()))
            }
            
            HashAlgorithm::Sha256 => {
                let mut hasher = Sha256::new();
                while remaining > 0 {
                    let bytes_to_read = std::cmp::min(remaining as usize, buffer.len());
                    let bytes_read = file.read(&mut buffer[..bytes_to_read])?;
                    if bytes_read == 0 {
                        break;
                    }
                    hasher.update(&buffer[..bytes_to_read]);
                    remaining -= bytes_read as u64;
                }
                Ok(format!("{:x}", hasher.finalize()))
            }
            
            HashAlgorithm::XxHash64BE | HashAlgorithm::XxHash128 | HashAlgorithm::Sha3 | HashAlgorithm::Md5 => {
                Ok("placeholder_hash".to_string())
            }
            
            HashAlgorithm::Blake3 => {
                Ok("blake3_placeholder".to_string())
            }
        }
    }
}

/// Verification manager for handling multiple verification tasks
pub struct VerificationManager {
    verification_records: Arc<Mutex<Vec<FileTransferRecord>>>,
    hash_cache: Arc<Mutex<HashMap<String, String>>>,
}

impl VerificationManager {
    pub fn new() -> Self {
        Self {
            verification_records: Arc::new(Mutex::new(Vec::new())),
            hash_cache: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    /// Verify a single file transfer
    pub fn verify_file_transfer(
        &self,
        source_path: &Path,
        destination_path: &Path,
        algorithm: HashAlgorithm,
    ) -> Result<HashVerificationResult> {
        let start_time = std::time::Instant::now();
        
        // Check cache first
        let cache_key = format!("{}:{}", source_path.display(), algorithm.to_string());
        if let Ok(cache) = self.hash_cache.lock() {
            if let Some(cached_hash) = cache.get(&cache_key) {
                // Verify destination against cached source hash
                let dest_hash = self.calculate_destination_hash(destination_path, &algorithm)?;
                let verification_passed = cached_hash == &dest_hash;
                
                let result = HashVerificationResult::new(
                    algorithm.clone(),
                    cached_hash.clone(),
                    dest_hash,
                    verification_passed,
                    None,
                    start_time.elapsed().as_millis() as u64,
                );
                
                return Ok(result);
            }
        }
        
        // Calculate hashes
        let source_hash = self.calculate_source_hash(source_path, &algorithm)?;
        let dest_hash = self.calculate_destination_hash(destination_path, &algorithm)?;
        
        let verification_passed = source_hash == dest_hash;
        let error_message = if !verification_passed {
            Some("Hash mismatch detected".to_string())
        } else {
            None
        };
        
        // Cache the source hash
        if let Ok(mut cache) = self.hash_cache.lock() {
            cache.insert(cache_key, source_hash.clone());
        }
        
        let result = HashVerificationResult::new(
            algorithm,
            source_hash,
            dest_hash,
            verification_passed,
            error_message,
            start_time.elapsed().as_millis() as u64,
        );
        
        Ok(result)
    }
    
    /// Calculate source file hash
    fn calculate_source_hash(&self, source_path: &Path, algorithm: &HashAlgorithm) -> Result<String> {
        let calculator = HashCalculator::new(algorithm.clone());
        calculator.calculate_file_hash(source_path)
    }
    
    /// Calculate destination file hash
    fn calculate_destination_hash(&self, destination_path: &Path, algorithm: &HashAlgorithm) -> Result<String> {
        let calculator = HashCalculator::new(algorithm.clone());
        calculator.calculate_file_hash(destination_path)
    }
    
    /// Add a verification record
    pub fn add_verification_record(&self, record: FileTransferRecord) {
        if let Ok(mut records) = self.verification_records.lock() {
            records.push(record);
        }
    }
    
    /// Get all verification records
    pub fn get_verification_records(&self) -> Vec<FileTransferRecord> {
        if let Ok(records) = self.verification_records.lock() {
            records.clone()
        } else {
            Vec::new()
        }
    }
    
    /// Clear verification cache
    pub fn clear_cache(&self) {
        if let Ok(mut cache) = self.hash_cache.lock() {
            cache.clear();
        }
    }
    
    /// Get cache statistics
    pub fn get_cache_stats(&self) -> (usize, usize) {
        if let Ok(cache) = self.hash_cache.lock() {
            (cache.len(), 0) // Would track memory usage in full implementation
        } else {
            (0, 0)
        }
    }
}

/// Python wrapper for VerificationManager
#[pyclass]
pub struct PyVerificationManager {
    inner: Arc<VerificationManager>,
}

#[pymethods]
impl PyVerificationManager {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(VerificationManager::new()),
        }
    }
    
    fn verify_file_transfer(
        &self,
        source_path: String,
        destination_path: String,
        algorithm: String,
    ) -> PyResult<PyObject> {
        let source_path = std::path::Path::new(&source_path);
        let destination_path = std::path::Path::new(&destination_path);
        let algorithm = HashAlgorithm::from_string(&algorithm);
        
        match self.inner.verify_file_transfer(source_path, destination_path, algorithm) {
            Ok(result) => {
                Python::with_gil(|py| {
                    let py_result = pyo3::types::PyDict::new(py);
                    py_result.set_item("algorithm", result.algorithm.to_string())?;
                    py_result.set_item("source_hash", result.source_hash)?;
                    py_result.set_item("destination_hash", result.destination_hash)?;
                    py_result.set_item("verification_passed", result.verification_passed)?;
                    if let Some(error) = result.error_message {
                        py_result.set_item("error_message", error)?;
                    }
                    py_result.set_item("verification_time_ms", result.verification_time_ms)?;
                    
                    Ok(py_result.into_py(py))
                })
            },
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
        }
    }
    
    fn clear_cache(&self) {
        self.inner.clear_cache();
    }
    
    fn get_cache_stats(&self) -> PyResult<(usize, usize)> {
        Ok(self.inner.get_cache_stats())
    }
}

/// Register Python types for this module
pub fn register_python_types(m: &PyModule) -> PyResult<()> {
    m.add_class::<PyVerificationManager>()?;
    Ok(())
}
