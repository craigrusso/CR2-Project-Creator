//! Cross-platform utilities and helpers

use anyhow::Result;
use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::path::{Path, PathBuf};

cfg_if::cfg_if! {
    if #[cfg(target_os = "windows")] {
        use winapi::um::fileapi::GetDiskFreeSpaceExW;
        use winapi::um::winbase::GetVolumePathNameW;
        use std::os::windows::ffi::OsStrExt;
        use std::ffi::OsStr;
    } else if #[cfg(target_os = "macos")] {
        // macOS-specific imports will be added when needed
    } else if #[cfg(target_os = "linux")] {
        use std::os::linux::fs::MetadataExt;
    }
}

/// Platform-specific disk space information
#[derive(Debug, Clone)]
pub struct DiskSpaceInfo {
    pub total_bytes: u64,
    pub available_bytes: u64,
    pub free_bytes: u64,
}

impl DiskSpaceInfo {
    pub fn new(total: u64, available: u64, free: u64) -> Self {
        Self {
            total_bytes: total,
            available_bytes: available,
            free_bytes: free,
        }
    }

    pub fn used_bytes(&self) -> u64 {
        self.total_bytes.saturating_sub(self.available_bytes)
    }

    pub fn usage_percent(&self) -> f64 {
        if self.total_bytes > 0 {
            (self.used_bytes() as f64 / self.total_bytes as f64) * 100.0
        } else {
            0.0
        }
    }
}

/// Get available disk space for a path
pub fn get_disk_space(path: &Path) -> Result<DiskSpaceInfo> {
    cfg_if::cfg_if! {
        if #[cfg(target_os = "windows")] {
            get_disk_space_windows(path)
        } else if #[cfg(target_os = "macos")] {
            get_disk_space_macos(path)
        } else if #[cfg(target_os = "linux")] {
            get_disk_space_linux(path)
        } else {
            get_disk_space_generic(path)
        }
    }
}

#[cfg(target_os = "windows")]
fn get_disk_space_windows(path: &Path) -> Result<DiskSpaceInfo> {
    use std::ptr;

    let path_str = path.to_string_lossy();
    let wide_path: Vec<u16> = OsStr::new(&path_str)
        .encode_wide()
        .chain(std::iter::once(0))
        .collect();

    let mut free_bytes_available: i64 = 0;
    let mut total_number_of_bytes: i64 = 0;
    let mut total_number_of_free_bytes: i64 = 0;

    let result = unsafe {
        GetDiskFreeSpaceExW(
            wide_path.as_ptr(),
            &mut free_bytes_available as *mut _ as *mut _,
            &mut total_number_of_bytes as *mut _ as *mut _,
            &mut total_number_of_free_bytes as *mut _ as *mut _,
        )
    };

    if result != 0 {
        Ok(DiskSpaceInfo::new(
            total_number_of_bytes as u64,
            free_bytes_available as u64,
            total_number_of_free_bytes as u64,
        ))
    } else {
        Err(std::io::Error::last_os_error().into())
    }
}

#[cfg(target_os = "macos")]
fn get_disk_space_macos(path: &Path) -> Result<DiskSpaceInfo> {
    // For macOS, we'll use the generic implementation for now
    // In a full implementation, we'd use Core Foundation APIs
    get_disk_space_generic(path)
}

#[cfg(target_os = "linux")]
fn get_disk_space_linux(path: &Path) -> Result<DiskSpaceInfo> {
    // For Linux, we'll use the generic implementation for now
    // In a full implementation, we'd use statvfs
    get_disk_space_generic(path)
}

fn get_disk_space_generic(path: &Path) -> Result<DiskSpaceInfo> {
    // Generic implementation using std::fs
    let metadata = fs::metadata(path)?;

    // This is a simplified implementation - in practice, we'd need
    // platform-specific calls to get accurate disk space information
    Ok(DiskSpaceInfo::new(
        1024 * 1024 * 1024 * 1024, // 1TB placeholder
        512 * 1024 * 1024 * 1024,  // 512GB placeholder
        512 * 1024 * 1024 * 1024,  // 512GB placeholder
    ))
}

/// Check if a path is a cloud storage location
pub fn is_cloud_storage(path: &Path) -> bool {
    let path_str = path.to_string_lossy().to_lowercase();

    // Common cloud storage patterns
    path_str.contains("onedrive")
        || path_str.contains("dropbox")
        || path_str.contains("google drive")
        || path_str.contains("icloud")
        || path_str.contains("box")
        || path_str.contains("mega")
        || path_str.contains("pcloud")
        || path_str.contains("sync.com")
        || path_str.contains("tresorit")
        || path_str.contains("spideroak")
}

/// Get the root path of a cloud storage location
pub fn get_cloud_root(path: &Path) -> Option<PathBuf> {
    let mut current = path;

    while let Some(parent) = current.parent() {
        if is_cloud_storage(parent) {
            return Some(parent.to_path_buf());
        }
        current = parent;
    }

    None
}

/// Check if a file is a symbolic link
pub fn is_symlink(path: &Path) -> bool {
    if let Ok(metadata) = fs::symlink_metadata(path) {
        metadata.file_type().is_symlink()
    } else {
        false
    }
}

/// Resolve symbolic links to their target
pub fn resolve_symlink(path: &Path) -> Result<PathBuf> {
    if is_symlink(path) {
        let target = fs::read_link(path)?;
        Ok(target)
    } else {
        Ok(path.to_path_buf())
    }
}

/// Get file size with proper error handling
pub fn get_file_size(path: &Path) -> Result<u64> {
    let metadata = fs::metadata(path)?;
    Ok(metadata.len())
}

/// Check if a path exists and is accessible
pub fn path_exists_and_accessible(path: &Path) -> bool {
    fs::metadata(path).is_ok()
}

/// Create directory with parent directories if needed
pub fn create_dir_all_safe(path: &Path) -> Result<()> {
    if !path.exists() {
        fs::create_dir_all(path)?;
    }
    Ok(())
}

/// Get the canonical path (resolve all symlinks and . components)
pub fn canonicalize_path(path: &Path) -> Result<PathBuf> {
    let canonical = fs::canonicalize(path)?;
    Ok(canonical)
}

/// Check if a path is absolute
pub fn is_absolute_path(path: &Path) -> bool {
    path.is_absolute()
}

/// Convert a path to absolute if it's relative
pub fn to_absolute_path(path: &Path) -> Result<PathBuf> {
    if path.is_absolute() {
        Ok(path.to_path_buf())
    } else {
        let current_dir = std::env::current_dir()?;
        Ok(current_dir.join(path))
    }
}

/// Get the file extension as a string
pub fn get_file_extension(path: &Path) -> Option<String> {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|s| s.to_lowercase())
}

/// Check if a file is hidden
pub fn is_hidden_file(path: &Path) -> bool {
    if let Some(name) = path.file_name() {
        if let Some(name_str) = name.to_str() {
            return name_str.starts_with('.');
        }
    }
    false
}

/// Get the parent directory safely
pub fn get_parent_directory(path: &Path) -> Option<PathBuf> {
    path.parent().map(|p| p.to_path_buf())
}

/// Check if a path is a directory
pub fn is_directory(path: &Path) -> bool {
    if let Ok(metadata) = fs::metadata(path) {
        metadata.is_dir()
    } else {
        false
    }
}

/// Check if a path is a regular file
pub fn is_regular_file(path: &Path) -> bool {
    if let Ok(metadata) = fs::metadata(path) {
        metadata.is_file()
    } else {
        false
    }
}

/// Get file permissions as a string (simplified)
pub fn get_file_permissions_string(path: &Path) -> Result<String> {
    let metadata = fs::metadata(path)?;
    let permissions = metadata.permissions();

    // Simplified permission string - in practice, we'd parse the actual permissions
    Ok("rw-r--r--".to_string())
}

/// Check if a file is executable
pub fn is_executable(path: &Path) -> bool {
    if let Ok(metadata) = fs::metadata(path) {
        let permissions = metadata.permissions();
        permissions.mode() & 0o111 != 0
    } else {
        false
    }
}

/// Get the last modified time as a timestamp
pub fn get_last_modified_timestamp(path: &Path) -> Result<f64> {
    let metadata = fs::metadata(path)?;
    let modified = metadata.modified()?;
    let duration = modified.duration_since(std::time::UNIX_EPOCH)?;
    Ok(duration.as_secs_f64())
}

/// Check if two paths point to the same file
pub fn paths_point_to_same_file(path1: &Path, path2: &Path) -> bool {
    if let (Ok(metadata1), Ok(metadata2)) = (fs::metadata(path1), fs::metadata(path2)) {
        // On Unix-like systems, dev() and ino() return u64 directly
        let dev1 = metadata1.dev();
        let dev2 = metadata2.dev();
        let ino1 = metadata1.ino();
        let ino2 = metadata2.ino();

        return dev1 == dev2 && ino1 == ino2;
    }
    false
}
