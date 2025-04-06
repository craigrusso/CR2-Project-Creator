#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Security-Scoped Bookmarks Manager for macOS

This module provides functionality to manage security-scoped bookmarks for
macOS sandboxed applications. This is necessary for App Store compliance.

On non-macOS platforms, this module provides compatible but non-operational stubs.
"""

import os
import json
import platform
import subprocess
from PyQt5.QtCore import QSettings

# Determine if we're running on macOS
IS_MACOS = platform.system() == "Darwin"

# Import macOS-specific modules only on macOS
if IS_MACOS:
    try:
        # We need to use objc directly for this functionality
        import objc
        from Foundation import NSURL, NSData, NSError
    except ImportError:
        print("WARNING: Could not import objc/Foundation modules. "
              "Security-scoped bookmarks will not work.")
        IS_MACOS = False

# Bookmark data storage location
BOOKMARK_FILE = "security_bookmarks.json"


class BookmarkManager:
    """
    Manager for security-scoped bookmarks on macOS.
    Provides stubs for other platforms.
    """

    def __init__(self, storage_path=None):
        """
        Initialize the bookmark manager.
        
        Args:
            storage_path (str): Path to store bookmark data. If None, uses the app settings directory.
        """
        self.is_macos = IS_MACOS
        
        # Get the storage path if not provided
        if storage_path is None:
            from app.core.config_manager import get_settings_path
            storage_path = get_settings_path()
        
        self.storage_path = storage_path
        self.bookmark_file = os.path.join(storage_path, BOOKMARK_FILE)
        self.bookmarks = {}
        
        # Load existing bookmarks
        self._load_bookmarks()
    
    def _load_bookmarks(self):
        """Load bookmarks from storage"""
        if not os.path.exists(self.bookmark_file):
            return
        
        try:
            with open(self.bookmark_file, 'r') as f:
                self.bookmarks = json.load(f)
        except Exception as e:
            print(f"Error loading bookmarks file: {e}")
            # Initialize with empty dict if loading fails
            self.bookmarks = {}
    
    def _save_bookmarks(self):
        """Save bookmarks to storage"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.bookmark_file), exist_ok=True)
            
            with open(self.bookmark_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving bookmarks file: {e}")
            return False
    
    def create_bookmark(self, path):
        """
        Create a security-scoped bookmark for the given path.
        
        Args:
            path (str): Path to create bookmark for
            
        Returns:
            bool: Success status
        """
        if not self.is_macos:
            # On non-macOS, just return success without doing anything
            return True
        
        try:
            # Create a URL from the path
            url = NSURL.fileURLWithPath_(path)
            
            # Create a security-scoped bookmark
            bookmark_data, error = url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_(
                1,  # NSURLBookmarkCreationWithSecurityScope
                None, 
                None, 
                None
            )
            
            if bookmark_data is None:
                print(f"Error creating bookmark: {error}")
                return False
            
            # Convert NSData to bytes and then to base64 string for storage
            bookmark_bytes = bookmark_data.bytes().tobytes()
            
            # Use the path as key for the bookmark
            self.bookmarks[path] = bookmark_bytes.hex()
            
            # Save changes
            self._save_bookmarks()
            
            print(f"Created security-scoped bookmark for {path}")
            return True
            
        except Exception as e:
            print(f"Exception creating bookmark: {e}")
            return False
    
    def access_bookmark(self, path):
        """
        Start accessing a security-scoped bookmark.
        
        Args:
            path (str): Path to access
            
        Returns:
            bool: Success status
            
        Note:
            When finished accessing, call stop_accessing_bookmark.
        """
        if not self.is_macos:
            # On non-macOS, just return success without doing anything
            return True
        
        # Check if we have a bookmark for this path
        if path not in self.bookmarks:
            print(f"No bookmark found for {path}")
            return False
        
        try:
            # Get the bookmark data
            bookmark_bytes = bytes.fromhex(self.bookmarks[path])
            bookmark_data = NSData.dataWithBytes_length_(bookmark_bytes, len(bookmark_bytes))
            
            # Resolve the bookmark
            url, stale, error = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(
                bookmark_data,
                1,  # NSURLBookmarkResolutionWithSecurityScope
                None,
                objc.byref(objc.c_bool(False)),
                None
            )
            
            if url is None:
                print(f"Error resolving bookmark: {error}")
                return False
            
            # Start accessing security-scoped resource
            success = url.startAccessingSecurityScopedResource()
            
            if not success:
                print(f"Failed to start accessing security-scoped resource: {path}")
                return False
            
            if stale:
                print(f"Bookmark for {path} is stale, updating...")
                # Update the bookmark
                self.create_bookmark(path)
            
            print(f"Started accessing security-scoped resource: {path}")
            return True
            
        except Exception as e:
            print(f"Exception accessing bookmark: {e}")
            return False
    
    def stop_accessing_bookmark(self, path):
        """
        Stop accessing a security-scoped bookmark.
        
        Args:
            path (str): Path to stop accessing
            
        Returns:
            bool: Success status
        """
        if not self.is_macos:
            # On non-macOS, just return success without doing anything
            return True
        
        # Check if we have a bookmark for this path
        if path not in self.bookmarks:
            print(f"No bookmark found for {path}")
            return False
        
        try:
            # Get the bookmark data
            bookmark_bytes = bytes.fromhex(self.bookmarks[path])
            bookmark_data = NSData.dataWithBytes_length_(bookmark_bytes, len(bookmark_bytes))
            
            # Resolve the bookmark
            url, stale, error = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(
                bookmark_data,
                1,  # NSURLBookmarkResolutionWithSecurityScope
                None,
                objc.byref(objc.c_bool(False)),
                None
            )
            
            if url is None:
                print(f"Error resolving bookmark: {error}")
                return False
            
            # Stop accessing security-scoped resource
            url.stopAccessingSecurityScopedResource()
            
            print(f"Stopped accessing security-scoped resource: {path}")
            return True
            
        except Exception as e:
            print(f"Exception stopping access to bookmark: {e}")
            return False
    
    def remove_bookmark(self, path):
        """
        Remove a bookmark.
        
        Args:
            path (str): Path to remove bookmark for
            
        Returns:
            bool: Success status
        """
        # On non-macOS platforms, always return success
        if not self.is_macos:
            return True
            
        if path in self.bookmarks:
            try:
                # Stop accessing if needed
                self.stop_accessing_bookmark(path)
                
                # Remove the bookmark
                del self.bookmarks[path]
                
                # Save changes
                self._save_bookmarks()
                
                print(f"Removed bookmark for {path}")
                return True
            except Exception as e:
                print(f"Error removing bookmark: {e}")
                return False
        
        print(f"No bookmark found for {path}")
        return False
    
    def has_bookmark(self, path):
        """Check if a bookmark exists for the given path"""
        return path in self.bookmarks
    
    def get_all_bookmark_paths(self):
        """Get all paths that have bookmarks"""
        return list(self.bookmarks.keys())

# Create a global instance for ease of use
_bookmark_manager = None

def get_bookmark_manager():
    """Get the global bookmark manager instance"""
    global _bookmark_manager
    if _bookmark_manager is None:
        _bookmark_manager = BookmarkManager()
    return _bookmark_manager

# Context manager for bookmark access
class BookmarkAccessContext:
    """Context manager for accessing security-scoped bookmarks"""
    
    def __init__(self, path):
        """
        Initialize the context manager.
        
        Args:
            path (str): Path to access
        """
        self.path = path
        self.manager = get_bookmark_manager()
        self.accessed = False
    
    def __enter__(self):
        """Start accessing the bookmark"""
        self.accessed = self.manager.access_bookmark(self.path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop accessing the bookmark"""
        if self.accessed:
            self.manager.stop_accessing_bookmark(self.path)
        return False  # Don't suppress exceptions

# Helper functions
def create_bookmark(path):
    """Create a security-scoped bookmark for the given path"""
    return get_bookmark_manager().create_bookmark(path)

def access_bookmark(path):
    """Start accessing a security-scoped bookmark"""
    return get_bookmark_manager().access_bookmark(path)

def stop_accessing_bookmark(path):
    """Stop accessing a security-scoped bookmark"""
    return get_bookmark_manager().stop_accessing_bookmark(path)

def with_bookmark_access(path):
    """Decorator for functions that need bookmark access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with BookmarkAccessContext(path):
                return func(*args, **kwargs)
        return wrapper
    return decorator 