#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to check Python environment and configuration
"""

import sys
import os
import platform
import struct

def main():
    """Print information about the Python environment"""
    print("=== Python Environment Information ===")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"64-bit Python: {struct.calcsize('P') * 8 == 64}")
    
    # Check if running in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"Running in virtual environment: {in_venv}")
    
    # Check if this is an ARM64 system
    is_arm64 = platform.machine().lower() in ["arm64", "aarch64"]
    print(f"ARM64 system detected: {is_arm64}")
    
    # Try to import PyQt5
    try:
        import PyQt5
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        print(f"PyQt5 found: {PyQt5.__file__}")
        print(f"Qt version: {QT_VERSION_STR}")
        print(f"PyQt version: {PYQT_VERSION_STR}")
    except ImportError as e:
        print(f"PyQt5 import error: {e}")
    
    # Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Print environment variables
    print("\n=== Environment Variables ===")
    for key in ["PYTHONPATH", "PYTHONHOME", "PATH"]:
        print(f"{key}: {os.environ.get(key, 'Not set')}")
    
    print("\nTest completed successfully.")

if __name__ == "__main__":
    main() 