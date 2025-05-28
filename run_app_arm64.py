#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Enhanced script to run the application on ARM64 systems or any Python environment
"""

import sys
import os
import platform
import subprocess

def find_python_executable():
    """Attempt to find the best Python executable to use"""
    # Check if we're running in a virtual environment first
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return sys.executable
    
    # Check for common Python executable locations based on platform
    potential_paths = []
    
    if platform.system() == "Windows":
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
        potential_paths = [
            venv_python,  # Try our local virtual environment first
            "python.exe",  # Check if python is in PATH
            "py.exe",     # Windows Python launcher
            r"C:\Program Files\Python\python.exe",
            r"C:\Program Files (x86)\Python\python.exe",
        ]
    elif platform.system() == "Darwin":  # macOS
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
        potential_paths = [
            venv_python,  # Try our local virtual environment first
            "/usr/bin/python3",
            "/usr/local/bin/python3",
            "/opt/homebrew/bin/python3",  # Homebrew on Apple Silicon
        ]
    else:  # Linux and others
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
        potential_paths = [
            venv_python,  # Try our local virtual environment first
            "/usr/bin/python3",
            "/usr/local/bin/python3",
        ]
    
    # Try each path
    for path in potential_paths:
        try:
            if os.path.exists(path):
                # Test if this Python executable works
                result = subprocess.run([path, "-c", "print('Python test')"], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"Found working Python at: {path}")
                    return path
        except (subprocess.SubprocessError, OSError):
            continue
    
    # If we get here, we couldn't find a working Python executable
    print("WARNING: Could not find a working Python executable. Falling back to sys.executable")
    return sys.executable

if __name__ == "__main__":
    try:
        # Find a working Python executable
        python_exe = find_python_executable()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(script_dir, "main.py")
        
        if os.path.exists(main_script):
            # Launch main.py with the identified Python executable
            print(f"Launching with Python: {python_exe}")
            result = subprocess.run([python_exe, main_script] + sys.argv[1:])
            sys.exit(result.returncode)
        else:
            print(f"ERROR: Cannot find main.py at {main_script}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR launching application: {e}")
        sys.exit(1) 