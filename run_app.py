#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Simple script to run the application with fixed ARM64 Python path
"""

import sys
import os
import subprocess

def main():
    # Specific ARM64 Python path
    python_path = sys.executable  # Use the current Python interpreter
    
    # Check if the Python executable exists
    if not os.path.exists(python_path):
        print(f"ERROR: Python not found at {python_path}")
        return 1
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the main.py script
    main_script = os.path.join(script_dir, "main.py")
    
    if not os.path.exists(main_script):
        print(f"ERROR: main.py not found at {main_script}")
        return 1
    
    print(f"Launching application with Python: {python_path}")
    print(f"Running script: {main_script}")
    
    # Run the main.py script directly in the foreground
    try:
        # Pass all command line arguments to the main script
        args = [python_path, main_script] + sys.argv[1:]
        
        # Execute directly in the foreground (no subprocess)
        os.execv(python_path, args)
        
        # We should never reach here if execv succeeds
        return 0
    except Exception as e:
        print(f"ERROR: Failed to launch application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 