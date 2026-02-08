use sha2::Digest as Sha2Digest;
use sha3::Digest as Sha3Digest;
use std::hash::Hasher;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use crate::gpu::{gpu_acceleration_available_for, GpuStreamingHasher as DeviceStreamingHasher};
use crate::verification::HashAlgorithm;

/// Streaming hasher that can hash data incrementally
pub(crate) struct StreamingHasher {
    algorithm: HashAlgorithm,
    inner: StreamingHasherKind,
    error: Option<String>,
    cancelled: Option<Arc<AtomicBool>>,
}

enum StreamingHasherKind {
    Xxh3(xxhash_rust::xxh3::Xxh3),
    Gpu(DeviceStreamingHasher),
    Sha256(sha2::Sha256),
    Sha3(sha3::Sha3_256),
    Md5(md5::Context),
    Blake3(blake3::Hasher),
}

impl StreamingHasher {
    pub fn new(algorithm: HashAlgorithm) -> Self {
        Self::new_with_cancellation(algorithm, None)
    }

    pub fn new_with_cancellation(algorithm: HashAlgorithm, cancelled: Option<Arc<AtomicBool>>) -> Self {
        let inner = match algorithm {
            HashAlgorithm::XxHash64 | HashAlgorithm::XxHash64BE | HashAlgorithm::XxHash128 => {
                StreamingHasherKind::Xxh3(xxhash_rust::xxh3::Xxh3::new())
            }
            HashAlgorithm::Sha256 | HashAlgorithm::Md5
                if gpu_acceleration_available_for(&algorithm) =>
            {
                match DeviceStreamingHasher::try_new(&algorithm) {
                    Some(gpu_hasher) => {
                        eprintln!("✅ GPU acceleration ENABLED for {:?}", algorithm);
                        StreamingHasherKind::Gpu(gpu_hasher)
                    }
                    None => {
                        eprintln!("⚠️  GPU acceleration requested but unavailable for {:?}, falling back to CPU", algorithm);
                        match algorithm {
                            HashAlgorithm::Sha256 => StreamingHasherKind::Sha256(sha2::Sha256::new()),
                            HashAlgorithm::Md5 => StreamingHasherKind::Md5(md5::Context::new()),
                            _ => unreachable!(),
                        }
                    }
                }
            }
            HashAlgorithm::Sha256 => {
                eprintln!("ℹ️  SHA-256 using CPU (GPU not available or not requested)");
                StreamingHasherKind::Sha256(sha2::Sha256::new())
            }
            HashAlgorithm::Sha3 => StreamingHasherKind::Sha3(sha3::Sha3_256::new()),
            HashAlgorithm::Md5 => StreamingHasherKind::Md5(md5::Context::new()),
            HashAlgorithm::Blake3 => StreamingHasherKind::Blake3(blake3::Hasher::new()),
        };

        Self {
            algorithm,
            inner,
            error: None,
            cancelled,
        }
    }

    pub fn update(&mut self, data: &[u8]) {
        // Check for cancellation first
        if let Some(ref cancelled) = self.cancelled {
            if cancelled.load(Ordering::Relaxed) {
                self.flag_error("Hashing cancelled".to_string());
                return;
            }
        }

        // Check for existing error
        if self.error.is_some() {
            return;
        }

        // For large data chunks, check cancellation periodically
        const CANCELLATION_CHECK_INTERVAL: usize = 64 * 1024; // Check every 64KB
        if data.len() > CANCELLATION_CHECK_INTERVAL {
            let chunks = data.chunks(CANCELLATION_CHECK_INTERVAL);
            for chunk in chunks {
                if let Some(ref cancelled) = self.cancelled {
                    if cancelled.load(Ordering::Relaxed) {
                        self.flag_error("Hashing cancelled".to_string());
                        return;
                    }
                }

                match &mut self.inner {
                    StreamingHasherKind::Xxh3(hasher) => hasher.update(chunk),
                    StreamingHasherKind::Gpu(ctx) => {
                        if let Err(e) = ctx.update(chunk) {
                            self.flag_error(e.to_string());
                            return;
                        }
                    }
                    StreamingHasherKind::Sha256(hasher) => Sha2Digest::update(hasher, chunk),
                    StreamingHasherKind::Sha3(hasher) => Sha3Digest::update(hasher, chunk),
                    StreamingHasherKind::Md5(ctx) => ctx.consume(chunk),
                    StreamingHasherKind::Blake3(hasher) => {
                        hasher.update(chunk);
                    }
                }
            }
        } else {
            match &mut self.inner {
                StreamingHasherKind::Xxh3(hasher) => hasher.update(data),
                StreamingHasherKind::Gpu(ctx) => {
                    if let Err(e) = ctx.update(data) {
                        self.flag_error(e.to_string());
                    }
                }
                StreamingHasherKind::Sha256(hasher) => Sha2Digest::update(hasher, data),
                StreamingHasherKind::Sha3(hasher) => Sha3Digest::update(hasher, data),
                StreamingHasherKind::Md5(ctx) => ctx.consume(data),
                StreamingHasherKind::Blake3(hasher) => {
                    hasher.update(data);
                }
            }
        }
    }

    pub fn flag_error(&mut self, message: String) {
        self.error.get_or_insert(message);
    }

    pub fn take_error(&mut self) -> Option<String> {
        self.error.take()
    }

    pub fn finish(self) -> String {
        // Check for cancellation before finalizing
        if let Some(ref cancelled) = self.cancelled {
            if cancelled.load(Ordering::Relaxed) {
                return "cancelled".to_string();
            }
        }

        match self.inner {
            StreamingHasherKind::Xxh3(hasher) => match self.algorithm {
                HashAlgorithm::XxHash128 => {
                    // CRITICAL FIX: Use digest128() for 128-bit hash, not finish() which only returns u64
                    format!("{:032x}", hasher.digest128())
                }
                _ => format!("{:016x}", hasher.finish()),
            },
            StreamingHasherKind::Gpu(ctx) => {
                // Check cancellation before GPU finalize (which can be slow)
                if let Some(ref cancelled) = self.cancelled {
                    if cancelled.load(Ordering::Relaxed) {
                        return "cancelled".to_string();
                    }
                }
                ctx.finalize()
                    .unwrap_or_else(|e| format!("gpu_error: {}", e))
            }
            StreamingHasherKind::Sha256(hasher) => {
                // Check cancellation before SHA finalize (which can be slow)
                if let Some(ref cancelled) = self.cancelled {
                    if cancelled.load(Ordering::Relaxed) {
                        return "cancelled".to_string();
                    }
                }
                format!("{:x}", Sha2Digest::finalize(hasher))
            }
            StreamingHasherKind::Sha3(hasher) => {
                if let Some(ref cancelled) = self.cancelled {
                    if cancelled.load(Ordering::Relaxed) {
                        return "cancelled".to_string();
                    }
                }
                format!("{:x}", Sha3Digest::finalize(hasher))
            }
            StreamingHasherKind::Md5(ctx) => {
                if let Some(ref cancelled) = self.cancelled {
                    if cancelled.load(Ordering::Relaxed) {
                        return "cancelled".to_string();
                    }
                }
                format!("{:x}", ctx.compute())
            }
            StreamingHasherKind::Blake3(hasher) => {
                if let Some(ref cancelled) = self.cancelled {
                    if cancelled.load(Ordering::Relaxed) {
                        return "cancelled".to_string();
                    }
                }
                hasher.finalize().to_hex().to_string()
            }
        }
    }
}
