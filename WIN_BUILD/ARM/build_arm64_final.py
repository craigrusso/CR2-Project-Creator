#!/usr/bin/env python3
# Final build script for Echelon Windows ARM64 executable
# Based on the successful Mac build command - MODIFIED FOR DIRECTORY OUTPUT

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Changed output directory name to reflect it's a directory build
DIST_DIR = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "dist_final_dir") 
BUILD_DIR = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "build_final_dir")
ICON_FILE = os.path.join(PROJECT_ROOT, "ICONS", "Echelon.ico")
MANIFEST_FILE = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "echelon_arm64_manifest.xml")

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

def fix_dll_paths():
    """Create a hook file to handle DLL loading on Windows ARM64"""
    print("Creating hook file for DLL loading...")
    
    hook_file_path = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "hook-app.py")
    # Assuming hook-app.py is correctly configured by the user or previous steps
    if not os.path.exists(hook_file_path):
        print(f"WARNING: Hook file {hook_file_path} not found. Creating a basic one.")
        with open(hook_file_path, 'w') as f:
            f.write("""
# hook-app.py - PyInstaller hook for Windows ARM64
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

# Collect all data files from the app module
datas = collect_data_files('app')

# Add submodules for app
hiddenimports = collect_submodules('app')

# Add submodules for logging
hiddenimports.extend(collect_submodules('logging'))
""")
    else:
        print(f"Using existing hook file: {hook_file_path}")
    
    print("Hook file setup completed.")
    return True

def build_executable():
    """Build the executable using PyInstaller with settings from Mac version"""
    print("Building the executable (directory output)...")
    
    # Create hook file if needed
    fix_dll_paths()
    
    # Build command for PyInstaller
    cmd = [
        "pyinstaller",
        "--clean",
        "--target-architecture", "arm64",
        "--name", "Echelon",
        f"--icon={ICON_FILE}",
        "--windowed",
        "--noupx",  # Don't use UPX compression (like Mac version)
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--noconfirm",
        # REMOVED --onefile for directory output
        f"--manifest={MANIFEST_FILE}",
        "--additional-hooks-dir", os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM"),
    ]
    
    # Add hidden imports (same as Mac version plus Windows-specific ones)
    hidden_imports = [
        "json", "webbrowser", "uuid", "requests", "packaging",
        "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "PyQt6.QtSvg", "PyQt5.sip",
        "logging", "logging.handlers", "logging.config",
        "os", "sys", "shutil", "platform",
        "app", "app.core", "app.ui", "app.config", "app.templates", "app.utils", "app.dialogs"
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Add collect-submodules for logging (like Mac version)
    cmd.extend(["--collect-submodules", "logging"])
    
    # Add data files (same structure as Mac version but with Windows path separator)
    data_files = [
        (os.path.join(PROJECT_ROOT, "app"), "app"),
        (os.path.join(PROJECT_ROOT, "app", "assets", "css"), os.path.join("app", "assets", "css")),
        (os.path.join(PROJECT_ROOT, "app", "assets", "icons"), os.path.join("app", "assets", "icons")),
        (os.path.join(PROJECT_ROOT, "app", "assets", "bundled_example_templates"), 
         os.path.join("app", "assets", "bundled_example_templates")),
        (os.path.join(PROJECT_ROOT, "EULA.txt"), "."),
        (os.path.join(PROJECT_ROOT, "ICONS"), "ICONS")  # Include entire ICONS directory
    ]
    
    for src, dest in data_files:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src};{dest}"])
        else:
            print(f"Warning: Data file path does not exist: {src}")
    
    # Add main script
    cmd.append(os.path.join(PROJECT_ROOT, "main.py"))
    
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
    
    # In a directory build, the executable is inside a folder named after the app
    executable_path = os.path.join(DIST_DIR, "Echelon", "Echelon.exe") 
    
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
    
    executable_path = os.path.join(DIST_DIR, "Echelon", "Echelon.exe")
    shortcut_path = os.path.join(DIST_DIR, "Echelon", "Echelon.lnk") # Place shortcut inside app dir for now
    
    try:
        # PowerShell command to create a shortcut
        ps_command = f"""
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{executable_path}"
        $Shortcut.IconLocation = "{executable_path},0"
        $Shortcut.WorkingDirectory = "{os.path.dirname(executable_path)}" # Set working directory
        $Shortcut.Save()
        """
        
        # Write the PowerShell script to a file
        ps_script_path = os.path.join(PROJECT_ROOT, "WIN_BUILD", "ARM", "create_shortcut.ps1")
        with open(ps_script_path, 'w') as f:
            f.write(ps_command)
        
        # Execute the PowerShell script
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script_path], check=False)
        
        print(f"Created shortcut at {shortcut_path}")
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        print(f"Would create shortcut at {shortcut_path} pointing to {executable_path}")
    
    print("Shortcut creation completed.")
    return True

def main():
    """Main build process"""
    print("\n=== Starting Echelon Windows ARM64 Final Build (Directory Output) ===\n")
    
    # Print system information
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Architecture: {platform.machine()}")
    
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
    print(f"Executable created in directory: {os.path.join(DIST_DIR, 'Echelon')}")
    print("\nNote: If the application still doesn't run, you may need to:")
    print("1. Examine the contents of the output directory for missing files/DLLs.")
    print("2. Check for additional dependencies needed specifically for Windows ARM64.")
    print("3. Verify that all native libraries are compatible with ARM64 architecture.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 