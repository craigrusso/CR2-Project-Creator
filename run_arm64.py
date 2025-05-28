#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Simplified launcher for ARM64 systems
"""

import sys
import os
import platform
import subprocess

def find_python_executable():
    """Find a working Python executable"""
    # If we're already in a virtual environment, use it
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return sys.executable
    
    # Check for Python in the virtual environment
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if platform.system() == "Windows":
        venv_python = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(script_dir, ".venv", "bin", "python")
        
    if os.path.exists(venv_python):
        return venv_python
    
    # If virtual environment Python not found, use the system Python
    return sys.executable

def main():
    """Run the main application using the best available Python"""
    try:
        # Find the best Python executable
        python_exe = find_python_executable()
        print(f"Using Python: {python_exe}")
        
        # Find the main.py script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(script_dir, "main.py")
        
        if not os.path.exists(main_script):
            print(f"Error: Could not find main.py at {main_script}")
            return 1
        
        # Run the main script with the found Python
        result = subprocess.run([python_exe, main_script] + sys.argv[1:])
        return result.returncode
    
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 