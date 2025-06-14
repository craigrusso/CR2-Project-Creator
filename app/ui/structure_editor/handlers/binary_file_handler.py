#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Binary File Handler

Handles binary file detection, validation, and embedding decisions.
Extracted from the monolithic file_operations.py for better organization.
"""

import os
from app.config.file_types import FILE_TYPES
from ..utils.file_type_detector import FileTypeDetector


class BinaryFileHandler:
    """Utility class for handling binary files"""
    
    @staticmethod
    def is_binary_file(file_path):
        """Check if a file is binary by attempting to read it as text"""
        try:
            with open(file_path, 'tr') as check_file:
                check_file.read(1024)
                return False
        except:
            return True
    
    @staticmethod
    def should_embed_binary_file(file_path, max_size_kb=500):
        """Check if a binary file should be embedded based on size"""
        try:
            size_kb = os.path.getsize(file_path) / 1024
            return size_kb <= max_size_kb
        except:
            return False

    @staticmethod
    def get_file_type_from_extension(file_path):
        """Determine file type from extension"""
        ext = os.path.splitext(file_path.lower())[1]
        
        for file_type, extensions in FILE_TYPES.items():
            if ext in extensions:
                return file_type
        return 'other'

    @staticmethod
    def get_file_icon(file_type):
        """Get appropriate icon for file type"""
        icon_map = {
            'video': '🎬',
            'audio': '🎵',
            'image': '🖼️',
            'document': '📄',
            'spreadsheet': '📊',
            'presentation': '📽️',
            'archive': '📦',
            'script': '💻',
            'folder': '',
            'other': '📄'
        }
        return icon_map.get(file_type, '📄')

    @staticmethod
    def get_file_info(file_path):
        """Get comprehensive file information"""
        if not os.path.exists(file_path):
            return None
        
        try:
            stat = os.stat(file_path)
            file_type = FileTypeDetector.get_file_type_from_extension(file_path)
            is_binary = BinaryFileHandler.is_binary_file(file_path)
            
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'size_kb': stat.st_size / 1024,
                'file_type': file_type,
                'is_binary': is_binary,
                'should_embed': BinaryFileHandler.should_embed_binary_file(file_path) if is_binary else True,
                'icon': FileTypeDetector.get_file_icon(file_type)
            }
        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return None
    
    @staticmethod
    def validate_file_for_template(file_path):
        """Validate if a file is suitable for template inclusion"""
        info = BinaryFileHandler.get_file_info(file_path)
        if not info:
            return False, "File not found or inaccessible"
        
        # Check file size limits
        max_size_mb = 50  # 50MB limit for any file
        if info['size_kb'] > max_size_mb * 1024:
            return False, f"File too large ({info['size_kb']:.1f}KB > {max_size_mb}MB limit)"
        
        # Binary files have stricter limits
        if info['is_binary'] and not info['should_embed']:
            return False, f"Binary file too large for embedding ({info['size_kb']:.1f}KB > 500KB limit)"
        
        return True, "File is valid for template inclusion" 