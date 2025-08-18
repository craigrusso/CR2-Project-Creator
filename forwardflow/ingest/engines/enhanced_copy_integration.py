#!/usr/bin/env python3
"""
Enhanced Copy Engine Integration

This module provides easy access to the enhanced copy engine from anywhere in the ForwardFlow app.
Just import this module and use the copy functions - they'll automatically use the best available engine.
"""

import os
import sys
import shutil
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

# Import the enhanced copy engine
try:
    from . import (
        CppEnhancedCopyEngine, CopyOptions, CopyStats, PathAnalyzer,
        copy_file as cpp_copy_file, copy_files as cpp_copy_files, test_bandwidth, is_enhanced_copy_available
    )
    ENHANCED_ENGINE_AVAILABLE = True
except ImportError:
    ENHANCED_ENGINE_AVAILABLE = False

# Simple fallback CopyStats class
class CopyStats:
    def __init__(self):
        self.total_files = 0
        self.copied_files = 0
        self.total_bytes = 0
        self.copied_bytes = 0
        self.start_time = time.time()
        self.end_time = 0.0
        self.speed_mbps = 0.0
        self.errors = []
        self.hash_verifications = 0
        self.hash_failures = 0
    
    def duration(self):
        return self.end_time - self.start_time
    
    def success_rate(self):
        return (self.copied_files * 100.0) / self.total_files if self.total_files > 0 else 0.0

def copy_file(source_path: str, destination_path: str, **kwargs) -> CopyStats:
    """
    Copy a single file using the enhanced copy engine if available, otherwise fallback to standard library.
    
    Args:
        source_path: Path to source file
        destination_path: Path to destination file
        **kwargs: Additional options (block_size, use_direct_io, verify_integrity, etc.)
    
    Returns:
        CopyStats: Statistics from the copy operation
    """
    if ENHANCED_ENGINE_AVAILABLE:
        return cpp_copy_file(source_path, destination_path, **kwargs)
    else:
        # Fallback to standard library
        stats = CopyStats()
        try:
            # Ensure destination directory exists
            dest_dir = Path(destination_path).parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, destination_path)
            
            # Update stats
            stats.total_files = 1
            stats.copied_files = 1
            stats.total_bytes = Path(source_path).stat().st_size
            stats.copied_bytes = stats.total_bytes
            stats.end_time = time.time()
            
            if stats.duration() > 0:
                stats.speed_mbps = (stats.copied_bytes / (1024.0 * 1024.0)) / stats.duration()
            
        except Exception as e:
            stats.errors.append(str(e))
        
        return stats

def copy_files(source_paths: List[str], destination_paths: List[str], **kwargs) -> CopyStats:
    """
    Copy multiple files using the enhanced copy engine if available, otherwise fallback to standard library.
    
    Args:
        source_paths: List of source file paths
        destination_paths: List of destination paths (can be directories or files)
        **kwargs: Additional options
    
    Returns:
        CopyStats: Statistics from the copy operation
    """
    if ENHANCED_ENGINE_AVAILABLE:
        return cpp_copy_files(source_paths, destination_paths, **kwargs)
    else:
        # Fallback to standard library
        stats = CopyStats()
        try:
            for i, source_path in enumerate(source_paths):
                if i < len(destination_paths):
                    dest_path = destination_paths[i]
                else:
                    # If fewer destinations than sources, use the last destination as a directory
                    dest_path = destination_paths[-1]
                
                # If destination is a directory, append the source filename
                if os.path.isdir(dest_path) or dest_path.endswith('/') or dest_path.endswith('\\'):
                    dest_path = os.path.join(dest_path, os.path.basename(source_path))
                
                # Ensure destination directory exists
                dest_dir = Path(dest_path).parent
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy the file
                shutil.copy2(source_path, dest_path)
                
                # Update stats
                stats.total_files += 1
                stats.copied_files += 1
                stats.total_bytes += Path(source_path).stat().st_size
                stats.copied_bytes += Path(source_path).stat().st_size
            
            stats.end_time = time.time()
            
            if stats.duration() > 0:
                stats.speed_mbps = (stats.copied_bytes / (1024.0 * 1024.0)) / stats.duration()
                
        except Exception as e:
            stats.errors.append(str(e))
        
        return stats

def copy_directory(source_dir: str, destination_dir: str, **kwargs) -> CopyStats:
    """
    Copy a directory using the enhanced copy engine if available, otherwise fallback to standard library.
    
    Args:
        source_dir: Source directory path
        destination_dir: Destination directory path
        **kwargs: Additional options
    
    Returns:
        CopyStats: Statistics from the copy operation
    """
    if ENHANCED_ENGINE_AVAILABLE:
        return cpp_copy_files([source_dir], [destination_dir], **kwargs)
    else:
        # Fallback to standard library
        stats = CopyStats()
        try:
            # Ensure destination directory exists
            dest_path = Path(destination_dir)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Copy the directory
            shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)
            
            # Calculate total size (this is approximate for the fallback)
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += Path(file_path).stat().st_size
                        file_count += 1
                    except:
                        pass
            
            # Update stats
            stats.total_files = file_count
            stats.copied_files = file_count
            stats.total_bytes = total_size
            stats.copied_bytes = total_size
            stats.end_time = time.time()
            
            if stats.duration() > 0:
                stats.speed_mbps = (stats.copied_bytes / (1024.0 * 1024.0)) / stats.duration()
                
        except Exception as e:
            stats.errors.append(str(e))
        
        return stats

def get_copy_engine_status() -> Dict[str, Any]:
    """
    Get the status of the copy engines.
    
    Returns:
        Dict with engine availability information
    """
    return {
        "enhanced_engine_available": ENHANCED_ENGINE_AVAILABLE,
        "cpp_engine_available": ENHANCED_ENGINE_AVAILABLE and is_enhanced_copy_available(),
        "fallback_available": True,  # Standard library is always available
        "recommended_engine": "enhanced" if ENHANCED_ENGINE_AVAILABLE else "standard"
    }

# Export the main functions
__all__ = [
    'copy_file',
    'copy_files', 
    'copy_directory',
    'get_copy_engine_status',
    'CopyStats',
    'CopyOptions',
    'ENHANCED_ENGINE_AVAILABLE'
]
