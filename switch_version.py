#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Switch Version Script for CR2 Creative Pro

This script allows users to switch between the Tkinter and PyQt versions
of the application. It updates the main.py file to use the appropriate
version and installs any required dependencies.
"""

import os
import sys
import shutil
import subprocess
import platform

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header():
    """Print the script header"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 60)
    print("CR2 Creative Pro - Version Switcher")
    print("=" * 60)
    print(f"{Colors.END}")

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"{Colors.FAIL}Error: Python 3.7 or higher is required.{Colors.END}")
        print(f"Current Python version: {sys.version}")
        sys.exit(1)

def check_pip():
    """Check if pip is installed"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}Error: pip is not installed or not working.{Colors.END}")
        print("Please install pip and try again.")
        return False

def install_requirements(version):
    """Install the required packages for the specified version"""
    req_file = "requirements.txt" if version == "tkinter" else "requirements_pyqt.txt"
    
    if not os.path.exists(req_file):
        print(f"{Colors.FAIL}Error: {req_file} not found.{Colors.END}")
        return False
    
    # For PyQt, check if it's already installed
    if version == "pyqt":
        try:
            # Try importing PyQt directly to see if it's installed
            import PyQt5
            print(f"{Colors.GREEN}PyQt5 is already installed.{Colors.END}")
            return True
        except ImportError:
            # If the import fails, continue with the install
            pass
    
    print(f"{Colors.BLUE}Installing dependencies from {req_file}...{Colors.END}")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"{Colors.FAIL}Failed to install dependencies:{Colors.END}")
        print(result.stderr.decode())
        
        if version == "pyqt":
            print(f"{Colors.WARNING}Trying to install PyQt5 directly...{Colors.END}")
            direct_result = subprocess.run([sys.executable, "-m", "pip", "install", "PyQt5"],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if direct_result.returncode != 0:
                print(f"{Colors.FAIL}Failed to install PyQt5 directly:{Colors.END}")
                print(direct_result.stderr.decode())
                # Check if PyQt is already installed despite the pip error
                try:
                    import PyQt5
                    print(f"{Colors.GREEN}PyQt5 is already installed despite pip errors.{Colors.END}")
                    return True
                except ImportError:
                    return False
            else:
                print(f"{Colors.GREEN}PyQt5 installed successfully.{Colors.END}")
                return True
        return False
    
    print(f"{Colors.GREEN}Dependencies installed successfully.{Colors.END}")
    return True

def switch_to_version(version):
    """Switch to the specified version"""
    if version not in ["tkinter", "pyqt"]:
        print(f"{Colors.FAIL}Error: Invalid version. Use 'tkinter' or 'pyqt'.{Colors.END}")
        return False
    
    # File paths
    main_file = "main.py"
    main_pyqt_file = "main_pyqt.py"
    main_backup = "main_backup.py"
    
    # Create backup of current main.py
    if os.path.exists(main_file):
        shutil.copy2(main_file, main_backup)
        print(f"{Colors.BLUE}Backup created: {main_backup}{Colors.END}")
    
    if version == "pyqt":
        # Ensure the PyQt main file exists
        if not os.path.exists(main_pyqt_file):
            print(f"{Colors.FAIL}Error: {main_pyqt_file} not found.{Colors.END}")
            return False
        
        # Replace main.py with main_pyqt.py
        shutil.copy2(main_pyqt_file, main_file)
        print(f"{Colors.GREEN}Switched to PyQt version.{Colors.END}")
        
        # Install PyQt requirements
        return install_requirements("pyqt")
    else:
        # Check if we have a Tkinter backup
        if not os.path.exists(main_backup):
            print(f"{Colors.FAIL}Error: No Tkinter backup found ({main_backup}).{Colors.END}")
            return False
        
        # Replace main.py with the backup
        shutil.copy2(main_backup, main_file)
        print(f"{Colors.GREEN}Switched to Tkinter version.{Colors.END}")
        
        # Install Tkinter requirements
        return install_requirements("tkinter")

def main():
    """Main function"""
    print_header()
    check_python_version()
    
    if not check_pip():
        return
    
    # Get version choice from command line args or user input
    if len(sys.argv) > 1 and sys.argv[1] in ["tkinter", "pyqt"]:
        version = sys.argv[1]
    else:
        print(f"{Colors.BOLD}Select version to use:{Colors.END}")
        print("1. Tkinter (original)")
        print("2. PyQt (new)")
        choice = input("Enter choice (1/2): ").strip()
        version = "tkinter" if choice == "1" else "pyqt"
    
    if switch_to_version(version):
        print(f"\n{Colors.GREEN}{Colors.BOLD}Version switched successfully to {version.upper()}.{Colors.END}")
        print(f"Run '{sys.executable} main.py' to start the application.")
    else:
        print(f"\n{Colors.FAIL}Failed to switch versions. See errors above.{Colors.END}")

if __name__ == "__main__":
    main() 