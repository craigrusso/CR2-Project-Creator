"""
Structure Editor Handlers Package

This package contains utility classes and core logic that was previously
embedded in the monolithic file_operations.py file.
"""

from .binary_file_handler import BinaryFileHandler
from .file_operations_core import FileOperationsCore

__all__ = [
    'BinaryFileHandler',
    'FileOperationsCore'
] 