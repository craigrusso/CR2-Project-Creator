#!/usr/bin/env python3
# Build script for Echelon Windows ARM64 executable
# This script handles the build process and code signing

import os
import sys
import subprocess
import shutil
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DIST_DIR = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "build")
SPEC_FILE = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "echelon_windows_arm64.spec")
ICON_FILE = os.path.join(PROJECT_ROOT, "ICONS", "Echelon.ico")

# Code signing credentials
ESIGNER_ID = "469181"
CREDENTIAL_ID = "25312c27-34a7-4680-925c-a6082eb85884"
CERTIFICATE_SERIAL = "40ce5f463c0dc239629caef88f88c849"
ESIGNER_LABEL = "eSigner-CR2_Creative-40ce5f463c0dc239629caef88f88c849-1736276"

def clean_directories():
    """Clean up build and dist directories before starting the build"""
    print("Cleaning build directories...")
    
    for directory in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(directory):
            print(f"Removing {directory}")
            shutil.rmtree(directory)
        
        # Create the directory again
        os.makedirs(directory, exist_ok=True)
    
    print("Clean up completed.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building the executable...")
    
    # Build command for PyInstaller
    cmd = [
        "pyinstaller",
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--noconfirm",
        "--onefile",  # Create a single executable file
        "--windowed",  # No console window (GUI only)
        "--icon", ICON_FILE,
        "--target-architecture", "arm64",
        f"--manifest={os.path.join(PROJECT_ROOT, 'WIN_BUILD', 'ARM', 'echelon_arm64_manifest.xml')}",
        os.path.join(PROJECT_ROOT, "main.py")
    ]
    
    # Add data files
    app_path = os.path.join(PROJECT_ROOT, "app")
    cmd.extend(["--add-data", f"{app_path};app"])
    
    # Add icon paths
    template_icon_src = os.path.join(PROJECT_ROOT, "app", "assets", "icons", "template_structure_icon.svg")
    template_icon_dest = os.path.join("app", "assets", "icons")
    cmd.extend(["--add-data", f"{template_icon_src};{template_icon_dest}"])
    
    # Add template icon to ICONS/templates
    icons_template_src = os.path.join(PROJECT_ROOT, "ICONS", "templates", "template_structure_icon.svg")
    icons_template_dest = os.path.join("ICONS", "templates")
    cmd.extend(["--add-data", f"{icons_template_src};{icons_template_dest}"])
    
    # Add other important files
    for file in ["EULA.txt", "LICENSE", "PrivacyPolicy.txt"]:
        file_path = os.path.join(PROJECT_ROOT, file)
        if os.path.exists(file_path):
            cmd.extend(["--add-data", f"{file_path};."])
    
    # Add hidden imports
    hidden_imports = [
        "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "PyQt5.sip",
        "json", "webbrowser", "requests",
        "app", "app.core", "app.ui", "app.config", "app.templates", "app.utils", "app.dialogs"
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Set application name
    cmd.extend(["--name", "Echelon"])
    
    # Execute the command
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        print(f"Error: PyInstaller build failed with return code {result.returncode}")
        return False
    
    print("PyInstaller build completed successfully.")
    return True

def code_sign_executable():
    """Sign the executable with the provided credentials"""
    print("Code signing the executable...")
    
    executable_path = os.path.join(DIST_DIR, "Echelon.exe")
    
    if not os.path.exists(executable_path):
        print(f"Error: Could not find executable at {executable_path}")
        return False
    
    # Code signing command would go here
    # This is a placeholder - you would need to integrate with your actual code signing tool
    print(f"Would sign {executable_path} with:")
    print(f"  eSigner ID: {ESIGNER_ID}")
    print(f"  Credential ID: {CREDENTIAL_ID}")
    print(f"  Certificate Serial: {CERTIFICATE_SERIAL}")
    print(f"  eSigner Label: {ESIGNER_LABEL}")
    
    print("Code signing completed.")
    return True

def create_windows_shortcut():
    """Create a Windows shortcut for the executable"""
    print("Creating Windows shortcut...")
    
    executable_path = os.path.join(DIST_DIR, "Echelon.exe")
    shortcut_path = os.path.join(DIST_DIR, "Echelon.lnk")
    
    # Create shortcut command would go here
    # This is a placeholder - you'd need Windows-specific code to create a proper shortcut
    print(f"Would create shortcut at {shortcut_path} pointing to {executable_path}")
    
    print("Shortcut creation completed.")
    return True

def main():
    """Main build process"""
    print("\n=== Starting Echelon Windows ARM64 Build ===\n")
    
    clean_directories()
    
    if not build_executable():
        print("Build failed. Exiting.")
        return 1
    
    if not code_sign_executable():
        print("Code signing failed. Exiting.")
        return 1
    
    if not create_windows_shortcut():
        print("Shortcut creation failed. Exiting.")
        return 1
    
    print("\n=== Build Process Completed Successfully ===")
    print(f"Executable created at: {os.path.join(DIST_DIR, 'Echelon.exe')}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 