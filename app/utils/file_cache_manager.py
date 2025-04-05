#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Cache Manager
Handles caching and management of files used in templates
"""

import os
import shutil
import json
import hashlib
import time
from pathlib import Path
import datetime

class FileCacheManager:
    """
    Manages caching of files for templates, ensuring files are available even if the original source changes.
    
    The cache uses a structured approach:
    - cache_dir/
      - template_name/
        - files/
          - actual files stored here, potentially in subdirectories
        - metadata.json (stores info about cached files including original paths)
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize the file cache manager
        
        Args:
            cache_dir: Base directory for the cache. If None, a default location is used
        """
        if cache_dir is None:
            # Default to a cache directory in the user's home directory
            home_dir = os.path.expanduser("~")
            self.cache_dir = os.path.join(home_dir, ".cr2", "template_cache")
        else:
            self.cache_dir = cache_dir
            
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Track statistics
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "cached_files": 0,
            "total_size": 0  # bytes
        }
        
        # Load cache stats if available
        self._load_stats()
    
    def _load_stats(self):
        """Load cache statistics from the cache directory"""
        stats_path = os.path.join(self.cache_dir, "cache_stats.json")
        if os.path.exists(stats_path):
            try:
                with open(stats_path, 'r') as f:
                    self.cache_stats = json.load(f)
            except Exception as e:
                print(f"Error loading cache stats: {e}")
    
    def _save_stats(self):
        """Save cache statistics to the cache directory"""
        stats_path = os.path.join(self.cache_dir, "cache_stats.json")
        try:
            with open(stats_path, 'w') as f:
                json.dump(self.cache_stats, f, indent=2)
        except Exception as e:
            print(f"Error saving cache stats: {e}")
    
    def cache_file(self, file_path, template_name, folder_path='', rename_flag=False, file_metadata=None):
        """
        Cache a file for a template
        
        Args:
            file_path: Path to the file to cache
            template_name: Name of the template this file belongs to
            folder_path: Optional relative folder path within the template
            rename_flag: Whether the file should be renamed with the project name
            file_metadata: Optional additional metadata for the file
            
        Returns:
            str: Path to the cached file, or None if caching failed
        """
        # Ensure paths don't have problematic characters
        template_name = template_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Error: File does not exist: {file_path}")
            return None
            
        # Create cache directory for this template if it doesn't exist
        template_cache_dir = os.path.join(self.cache_dir, template_name)
        template_files_dir = os.path.join(template_cache_dir, 'files')
        os.makedirs(template_files_dir, exist_ok=True)
        
        # Get filename and determine destination path
        file_name = os.path.basename(file_path)
        
        # Destination path in cache (flattened structure)
        cache_path = os.path.join(template_files_dir, file_name)
        
        # Determine file type and attributes
        file_extension = os.path.splitext(file_name)[1].lower()
        file_size = os.path.getsize(file_path)
        file_type = self._determine_file_type(file_extension)
        is_binary = self._is_binary_file(file_path, file_extension)
        
        # Get file hash for tracking duplicates and updates
        file_hash = self._get_file_hash(file_path)
        
        # Copy file to cache location
        try:
            # First ensure any parent directories exist
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            shutil.copy2(file_path, cache_path)
            
            # Update statistics
            if template_name not in self.cache_stats:
                self.cache_stats[template_name] = {
                    'file_count': 0,
                    'total_size': 0,
                    'file_types': {},
                    'last_updated': time.time()
                }
                
            self.cache_stats[template_name]['file_count'] += 1
            self.cache_stats[template_name]['total_size'] += file_size
            
            if file_type not in self.cache_stats[template_name]['file_types']:
                self.cache_stats[template_name]['file_types'][file_type] = 0
            self.cache_stats[template_name]['file_types'][file_type] += 1
            
            self.cache_stats[template_name]['last_updated'] = time.time()
            
            # Save updated statistics
            self._save_stats()
            
            # Save metadata for this file
            metadata_file = os.path.join(template_cache_dir, 'metadata.json')
            file_metadata_entry = {
                'file_name': file_name,
                'original_path': file_path,
                'cached_path': cache_path,
                'folder': folder_path,
                'file_size': file_size,
                'file_type': file_type,
                'file_hash': file_hash,
                'is_binary': is_binary,
                'extension': file_extension,
                'rename_flag': rename_flag,
                'cache_time': time.time()
            }
            
            # Add any additional metadata
            if file_metadata:
                file_metadata_entry.update(file_metadata)
                
            self._update_file_metadata(metadata_file, file_name, file_metadata_entry)
            
            # Return the path to the cached file
            return cache_path
            
        except Exception as e:
            print(f"Error caching file {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
    def _determine_file_type(self, extension):
        """
        Determine file type based on extension
        
        Args:
            extension (str): File extension including the dot
            
        Returns:
            str: File type category
        """
        extension = extension.lower()
        
        # Image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.raw', '.psd', '.ai']
        
        # Video files
        video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpg', '.mpeg', '.mxf']
        
        # Audio files
        audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a', '.aif', '.aiff']
        
        # Document files
        document_extensions = ['.txt', '.md', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx']
        
        # Code files
        code_extensions = ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.json', '.xml', '.yaml', '.yml']
        
        # Project files
        project_extensions = ['.prproj', '.aep', '.aepx', '.drp', '.fcpxml', '.fcpx']
        
        if extension in image_extensions:
            return 'image'
        elif extension in video_extensions:
            return 'video'
        elif extension in audio_extensions:
            return 'audio'
        elif extension in document_extensions:
            return 'document'
        elif extension in code_extensions:
            return 'code'
        elif extension in project_extensions:
            return 'project'
        else:
            return 'other'
            
    def _is_binary_file(self, file_path, extension=None):
        """
        Check if a file is binary
        
        Args:
            file_path (str): Path to the file
            extension (str, optional): File extension to use as a hint
            
        Returns:
            bool: True if file is binary, False otherwise
        """
        # Quick check by extension
        if extension:
            extension = extension.lower()
            # Known binary extensions
            binary_extensions = [
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.raw', 
                '.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpg', '.mpeg', '.mxf',
                '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a', '.aif', '.aiff',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.rar', '.7z', '.tar', '.gz', '.exe', '.dll', '.so', '.dylib',
                '.psd', '.ai', '.prproj', '.aep', '.aepx', '.drp'
            ]
            
            if extension in binary_extensions:
                return True
                
            # Known text extensions
            text_extensions = [
                '.txt', '.md', '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.cs', '.php', 
                '.json', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.bat', '.sh', '.ps1', '.rtf', '.csv'
            ]
            
            if extension in text_extensions:
                return False
                
        # If extension check is inconclusive, read the first part of the file
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:  # Null bytes indicate binary
                    return True
                
                # Try to decode as text
                try:
                    chunk.decode('utf-8')
                    return False
                except UnicodeDecodeError:
                    return True
                    
        except Exception:
            # If there's an error reading the file, assume it's binary
            return True
            
        return False
        
    def _get_file_hash(self, file_path):
        """
        Calculate MD5 hash of a file
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: MD5 hash of the file
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {str(e)}")
            return None
    
    def get_cached_file(self, template_name, file_path=None, file_key=None):
        """
        Get information about a cached file
        
        Args:
            template_name: Name of the template
            file_path: Original file path (optional if file_key is provided)
            file_key: File key (optional if file_path is provided)
            
        Returns:
            dict: Information about the cached file or None if not found
        """
        # Clean template name for filesystem use
        safe_template_name = self._sanitize_name(template_name)
        
        # Get metadata
        metadata_path = os.path.join(self.cache_dir, safe_template_name, "metadata.json")
        if not os.path.exists(metadata_path):
            self.cache_stats["misses"] += 1
            self._save_stats()
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            self.cache_stats["misses"] += 1
            self._save_stats()
            return None
        
        # Check if files dictionary exists
        if "files" not in metadata:
            self.cache_stats["misses"] += 1
            self._save_stats()
            return None
        
        # Find the file
        if file_key:
            # Use direct key lookup
            file_info = metadata["files"].get(file_key)
        elif file_path:
            # Search by original path
            file_info = None
            for key, info in metadata["files"].items():
                if info.get("original_path") == file_path:
                    file_info = info
                    break
        else:
            # No key or path provided
            self.cache_stats["misses"] += 1
            self._save_stats()
            return None
        
        # Return file info if found
        if file_info:
            self.cache_stats["hits"] += 1
            self._save_stats()
            
            # Check if the file actually exists in the cache
            if "cached_path" in file_info and os.path.exists(file_info["cached_path"]):
                return file_info
            else:
                # File is in metadata but missing from cache
                self.cache_stats["misses"] += 1
                self._save_stats()
                return None
        else:
            self.cache_stats["misses"] += 1
            self._save_stats()
            return None
    
    def get_all_cached_files(self, template_name):
        """
        Get information about all cached files for a template
        
        Args:
            template_name: Name of the template
            
        Returns:
            dict: Dictionary of file keys to file info
        """
        # Clean template name for filesystem use
        safe_template_name = self._sanitize_name(template_name)
        
        # Get metadata
        metadata_path = os.path.join(self.cache_dir, safe_template_name, "metadata.json")
        if not os.path.exists(metadata_path):
            return {}
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            return metadata.get("files", {})
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return {}
    
    def clear_template_cache(self, template_name):
        """
        Remove all cached files for a template
        
        Args:
            template_name: Name of the template
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Clean template name for filesystem use
        safe_template_name = self._sanitize_name(template_name)
        
        # Get template cache directory
        template_cache_dir = os.path.join(self.cache_dir, safe_template_name)
        
        # Check if it exists
        if not os.path.exists(template_cache_dir):
            return True  # Nothing to delete
        
        # Try to delete the directory
        try:
            shutil.rmtree(template_cache_dir)
            return True
        except Exception as e:
            print(f"Error clearing template cache: {e}")
            return False
    
    def clear_all_caches(self):
        """
        Remove all cached files
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get list of directories in cache (excluding stats file)
            for item in os.listdir(self.cache_dir):
                if item != "cache_stats.json":
                    item_path = os.path.join(self.cache_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
            
            # Reset stats
            self.cache_stats = {
                "hits": 0,
                "misses": 0,
                "cached_files": 0,
                "total_size": 0
            }
            self._save_stats()
            
            return True
        except Exception as e:
            print(f"Error clearing all caches: {e}")
            return False
    
    def get_cache_stats(self):
        """
        Get current cache statistics, recalculating size and file count.
        
        Returns:
            dict: Dictionary containing cache stats like total_size, cached_files, etc.
        """
        # Calculate total size and file count dynamically by iterating through cache
        total_size = 0
        total_files = 0
        template_count = 0
        
        if os.path.exists(self.cache_dir):
            for item in os.listdir(self.cache_dir):
                item_path = os.path.join(self.cache_dir, item)
                # Only count template directories 
                if os.path.isdir(item_path):
                    template_count += 1
                    # Use helper function to get size and count of this template's cache dir
                    dir_size, file_count = self._get_directory_size(item_path) # Unpack tuple
                    total_size += dir_size
                    total_files += file_count # Correctly increment total_files
                    
        # Update the internal stats dictionary (can be saved later if needed)
        self.cache_stats['total_size'] = total_size
        self.cache_stats['cached_files'] = total_files
        self.cache_stats['template_count'] = template_count # Keep template count
        
        # Add human-readable size
        self.cache_stats['total_size_human'] = self._human_readable_size(total_size)

        # Return a copy of the current, recalculated stats
        return self.cache_stats.copy()
    
    def prune_cache(self, max_age_days=None, max_size_mb=None):
        """
        Prune the cache by removing old files
        
        Args:
            max_age_days: Maximum age of cached files in days (optional)
            max_size_mb: Maximum size of the cache in MB (optional)
            
        Returns:
            dict: Statistics about pruned files
        """
        pruned_stats = {
            "files_removed": 0,
            "bytes_removed": 0
        }
        
        # Calculate pruning criteria
        current_time = time.time()
        max_age_seconds = max_age_days * 86400 if max_age_days else None
        max_size_bytes = max_size_mb * 1024 * 1024 if max_size_mb else None
        
        # Get all template directories
        template_dirs = []
        for item in os.listdir(self.cache_dir):
            if item != "cache_stats.json" and os.path.isdir(os.path.join(self.cache_dir, item)):
                template_dirs.append(item)
        
        # Sort templates by last modified time
        template_info = []
        for template_name in template_dirs:
            metadata_path = os.path.join(self.cache_dir, template_name, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    last_updated = metadata.get("last_updated", 0)
                    template_info.append((template_name, last_updated))
                except Exception as e:
                    print(f"Error loading metadata for {template_name}: {e}")
                    template_info.append((template_name, 0))
        
        # Sort by last update time (oldest first)
        template_info.sort(key=lambda x: x[1])
        
        # Process templates
        for template_name, last_updated in template_info:
            # Skip if we're not pruning by age or size
            if not max_age_seconds and not max_size_bytes:
                break
            
            # Check if this template is old enough to prune
            if max_age_seconds and (current_time - last_updated) > max_age_seconds:
                # Remove template cache
                template_cache_dir = os.path.join(self.cache_dir, template_name)
                
                # Get size before removal
                template_size, file_count = self._get_directory_size(template_cache_dir)
                
                try:
                    shutil.rmtree(template_cache_dir)
                    pruned_stats["files_removed"] += file_count
                    pruned_stats["bytes_removed"] += template_size
                except Exception as e:
                    print(f"Error removing template cache {template_name}: {e}")
            
            # Check if we need to reduce cache size
            if max_size_bytes:
                # Calculate current cache size
                current_size = self.cache_stats.get("total_size", 0)
                
                # If we're still over the limit, remove more templates
                if current_size - pruned_stats["bytes_removed"] > max_size_bytes:
                    # Remove this template cache
                    template_cache_dir = os.path.join(self.cache_dir, template_name)
                    
                    # Get size before removal
                    template_size, file_count = self._get_directory_size(template_cache_dir)
                    
                    try:
                        shutil.rmtree(template_cache_dir)
                        pruned_stats["files_removed"] += file_count
                        pruned_stats["bytes_removed"] += template_size
                    except Exception as e:
                        print(f"Error removing template cache {template_name}: {e}")
                else:
                    # We've removed enough to get under the limit
                    break
        
        # Update stats
        self.cache_stats["cached_files"] -= pruned_stats["files_removed"]
        self.cache_stats["total_size"] -= pruned_stats["bytes_removed"]
        if self.cache_stats["cached_files"] < 0:
            self.cache_stats["cached_files"] = 0
        if self.cache_stats["total_size"] < 0:
            self.cache_stats["total_size"] = 0
        
        self._save_stats()
        
        # Add human-readable size to stats
        pruned_stats["bytes_removed_human"] = self._human_readable_size(pruned_stats["bytes_removed"])
        
        return pruned_stats
    
    def _sanitize_name(self, name):
        """
        Sanitize a name for use in the filesystem
        
        Args:
            name: The name to sanitize
            
        Returns:
            str: Sanitized name
        """
        # Replace invalid characters with underscores
        import re
        return re.sub(r'[<>:"/\\|?*]', '_', name)
    
    def _calculate_file_hash(self, file_path):
        """
        Calculate a hash for a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: File hash (SHA-256)
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read file in chunks to avoid memory issues with large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return ""
    
    def _get_directory_size(self, path):
        """
        Calculate the total size of a directory
        
        Args:
            path: Path to the directory
            
        Returns:
            tuple: (Total size in bytes, Total file count)
        """
        total_size = 0
        file_count = 0 # Initialize file count
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1 # Increment file count
        return total_size, file_count # Return tuple
    
    def _human_readable_size(self, size_bytes):
        """
        Convert size in bytes to human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Human-readable size
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f} {units[i]}"

    def create_file_object(self, template_name, file_path, folder_path=None, rename_flag=False):
        """
        Create a file object suitable for adding to a template's files array
        
        Args:
            template_name: Name of the template
            file_path: Path to the original file
            folder_path: Path within the structure where the file belongs
            rename_flag: Whether the file should be renamed with project name
            
        Returns:
            dict: A file object with all necessary metadata
        """
        try:
            # Make sure file exists
            if not os.path.exists(file_path):
                print(f"Warning: File does not exist: {file_path}")
                return None
                
            # Cache the file
            file_info = self.cache_file(file_path, template_name, folder_path)
            
            if not file_info:
                return None
                
            # Create file object
            file_obj = {
                "file_name": file_info["file_name"],
                "original_path": file_info["original_path"],
                "cached_path": file_info["cached_path"],
                "rename_flag": rename_flag,
                "folder": folder_path or "",
                "file_type": file_info["file_type"],
                "size": file_info["file_size"],
                "last_modified": datetime.datetime.fromtimestamp(file_info["cache_time"]).isoformat()
            }
            
            return file_obj
            
        except Exception as e:
            print(f"Error creating file object: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _update_file_metadata(self, metadata_file, file_name, file_metadata):
        """
        Update metadata file with information about a cached file
        
        Args:
            metadata_file: Path to the metadata JSON file
            file_name: The name of the file (as key in the metadata)
            file_metadata: The metadata to store for this file
        """
        try:
            # Load existing metadata if it exists
            metadata = {}
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except Exception as e:
                    print(f"Error loading metadata file: {e}")
                    metadata = {}
            
            # Ensure files dictionary exists
            if 'files' not in metadata:
                metadata['files'] = {}
                
            # Update file metadata
            metadata['files'][file_name] = file_metadata
            
            # Update last_updated timestamp
            metadata['last_updated'] = time.time()
            
            # Save metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error updating file metadata: {e}")
            import traceback
            traceback.print_exc()
            return False 