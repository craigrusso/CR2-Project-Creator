#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Binary File Handler
Utilities for handling binary files in structure data
"""

import os
import base64
import mimetypes
from pathlib import Path

class BinaryFileHandler:
    """
    Handles encoding and decoding of binary files for inclusion in structure data
    
    This utility class provides methods to encode binary files as base64 strings
    for storage in structure JSON files, and to decode them back to binary files
    when creating projects.
    """
    
    @staticmethod
    def encode_binary_file(file_path):
        """
        Encode a binary file as a base64 string
        
        Args:
            file_path: Path to the binary file
            
        Returns:
            str: Base64-encoded string of file contents, or None if file doesn't exist
        """
        if not os.path.exists(file_path):
            print(f"Warning: File does not exist: {file_path}")
            return None
            
        try:
            with open(file_path, 'rb') as f:
                binary_data = f.read()
                encoded_data = base64.b64encode(binary_data).decode('utf-8')
                return encoded_data
        except Exception as e:
            print(f"Error encoding binary file {file_path}: {e}")
            return None
    
    @staticmethod
    def decode_binary_file(encoded_data, output_path):
        """
        Decode a base64 string to a binary file
        
        Args:
            encoded_data: Base64-encoded string
            output_path: Path to save the decoded file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Decode and write the file
            binary_data = base64.b64decode(encoded_data)
            with open(output_path, 'wb') as f:
                f.write(binary_data)
            return True
        except Exception as e:
            print(f"Error decoding binary file to {output_path}: {e}")
            return False
    
    @staticmethod
    def is_binary_file(file_path):
        """
        Determine if a file is binary based on extension and content sampling
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if the file is binary, False otherwise
        """
        # Check by extension first
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Common binary extensions
        binary_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
            # Audio
            '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a',
            # Video
            '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            # Executables
            '.exe', '.dll', '.so', '.dylib',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
        }
        
        if ext in binary_extensions:
            return True
            
        # Use mimetype detection
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith(('text/', 'application/json', 'application/xml')):
            return True
            
        # As a last resort, check file content
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    sample = f.read(1024)  # Read first 1KB
                return b'\0' in sample  # Binary files often contain null bytes
            except Exception:
                # If we can't read the file, assume it's binary to be safe
                return True
                
        return False
    
    @staticmethod
    def get_file_size(file_path):
        """
        Get the size of a file in bytes
        
        Args:
            file_path: Path to the file
            
        Returns:
            int: Size of the file in bytes, or 0 if file doesn't exist
        """
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    
    @staticmethod
    def should_embed_binary_file(file_path, max_size_kb=500):
        """
        Determine if a binary file should be embedded in the structure JSON
        
        Args:
            file_path: Path to the file
            max_size_kb: Maximum file size in KB to embed (default: 500KB)
            
        Returns:
            bool: True if the file should be embedded, False otherwise
        """
        # Always embed if file size is below threshold
        file_size_kb = BinaryFileHandler.get_file_size(file_path) / 1024
        return file_size_kb <= max_size_kb 