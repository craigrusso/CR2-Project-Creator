//! Streaming hash calculation for file verification

use std::hash::Hasher;
use sha2::Digest as Sha2Digest;
use sha3::Digest as Sha3Digest;
use crate::verification::HashAlgorithm;

/// Streaming hasher that can compute various hash algorithms incrementally
pub(crate) struct StreamingHasher {
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
    pub fn new(algorithm: HashAlgorithm) -> Self {
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

    pub fn update(&mut self, data: &[u8]) {
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

    pub fn flag_error(&mut self, message: String) {
        self.error.get_or_insert(message);
    }

    pub fn take_error(&mut self) -> Option<String> {
        self.error.take()
    }

    pub fn finish(mut self) -> String {
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
