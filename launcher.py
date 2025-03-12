#!/usr/bin/env python3
"""
Launcher script for CR2 Creative Pro
This script sets up the environment and launches the main application
"""

import os
import sys
import site
import importlib.util

def main():
    # Get the directory where this launcher script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up to Resources directory
    resources_dir = os.path.normpath(os.path.join(current_dir, '..', 'Resources'))
    python_dir = os.path.join(resources_dir, 'python')
    site_packages_dir = os.path.join(python_dir, 'lib', 'python3.9', 'site-packages')
    
    # Add site-packages to Python path
    sys.path.insert(0, site_packages_dir)
    sys.path.insert(0, python_dir)
    
    # Change to python directory
    os.chdir(python_dir)
    
    # Check if PyQt5 can be imported
    try:
        import PyQt5.QtWidgets
        print("PyQt5 found and imported successfully")
    except ImportError as e:
        print(f"Error importing PyQt5: {e}")
        from tkinter import messagebox
        messagebox.showerror("Import Error", 
                           f"Error importing PyQt5: {e}\n\n"
                           "This probably means the application wasn't packaged correctly.\n"
                           "Please contact support.")
        sys.exit(1)
    
    # Import and run the main module
    try:
        main_file = os.path.join(python_dir, 'main.py')
        spec = importlib.util.spec_from_file_location("main", main_file)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
    except Exception as e:
        print(f"Error loading main module: {e}")
        from tkinter import messagebox
        messagebox.showerror("Launch Error", 
                           f"Error launching application: {e}\n\n"
                           "Please contact support.")
        sys.exit(1)

if __name__ == "__main__":
    main() 