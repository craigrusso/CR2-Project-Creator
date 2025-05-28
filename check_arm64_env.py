#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Environment checker for ARM64 Python installations
"""

import sys
import os
import platform
import struct
import subprocess

def check_arm64():
    """Check if we're running on ARM64 architecture"""
    machine = platform.machine().lower()
    is_arm = machine in ["arm64", "aarch64"]
    
    print(f"Architecture: {platform.machine()}")
    print(f"ARM64 system: {is_arm}")
    
    if platform.system() == "Windows":
        # Check Windows-specific ARM64 indicators
        try:
            # Use PowerShell to check processor architecture
            result = subprocess.run(
                ["powershell", "-Command", "$env:PROCESSOR_ARCHITECTURE"], 
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                print(f"Windows PROCESSOR_ARCHITECTURE: {result.stdout.strip()}")
        except Exception:
            pass
    
    return is_arm

def check_python():
    """Check Python installation details"""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {os.pathsep.join(sys.path)}")
    print(f"64-bit Python: {struct.calcsize('P') * 8 == 64}")
    
    # Check if running in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"Running in virtual environment: {in_venv}")
    
    if in_venv:
        print(f"Virtual environment path: {sys.prefix}")
        if hasattr(sys, 'base_prefix'):
            print(f"Base Python path: {sys.base_prefix}")

def check_dependencies():
    """Check if required dependencies are installed"""
    dependencies = [
        "PyQt5",
        "certifi",
        "charset_normalizer",
        "idna",
        "requests",
        "urllib3"
    ]
    
    print("\nChecking dependencies:")
    for dep in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {dep} - version {version}")
            # For PyQt5, get more details
            if dep == "PyQt5":
                try:
                    from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
                    print(f"   - Qt version: {QT_VERSION_STR}")
                    print(f"   - PyQt version: {PYQT_VERSION_STR}")
                except ImportError:
                    pass
        except ImportError:
            print(f"❌ {dep} - NOT FOUND")

def check_clang():
    """Check for Clang installation"""
    try:
        result = subprocess.run(
            ["clang", "--version"], 
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print(f"\nClang installation found:")
            print(result.stdout.strip())
        else:
            print("\nClang not found or not properly installed")
    except Exception:
        print("\nClang not found in PATH")

def main():
    """Run all environment checks"""
    print("=== ARM64 Environment Check ===\n")
    
    print("System Information:")
    print(f"OS: {platform.system()} {platform.version()}")
    is_arm = check_arm64()
    
    print("\nPython Information:")
    check_python()
    
    # Check dependencies
    check_dependencies()
    
    # Check Clang
    check_clang()
    
    print("\nEnvironment Variables:")
    for var in ["PATH", "PYTHONPATH", "PYTHONHOME"]:
        value = os.environ.get(var, "Not set")
        if var == "PATH":
            # Just show the first few entries for PATH to avoid clutter
            path_entries = value.split(os.pathsep)
            if len(path_entries) > 5:
                value = os.pathsep.join(path_entries[:5]) + f" ... (and {len(path_entries)-5} more)"
        print(f"{var}: {value}")
    
    print("\nCheck completed.")
    
    if not is_arm:
        print("\nWARNING: This does not appear to be an ARM64 system.")
        print("This script is intended for ARM64 environments.")

if __name__ == "__main__":
    main() 