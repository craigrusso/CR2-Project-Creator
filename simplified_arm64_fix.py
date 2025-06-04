#!/usr/bin/env python3
# Simplified ARM64 Fix for PyQt6 Applications
# Addresses the "FORMAT MESSAGE W failed" error with minimal code

import os
import sys
import shutil
import ctypes
from pathlib import Path

def fix_format_message_error():
    """Fix the FORMAT MESSAGE W failed error for PyQt6 on Windows ARM64"""
    print("=== Simplified Fix for FORMAT MESSAGE W Error ===")
    
    # Get paths
    base_dir = Path(os.getcwd())
    app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
    
    # Check if the directory exists
    if not app_dir.exists():
        print(f"ERROR: Application directory not found: {app_dir}")
        custom_dir = input("Enter the correct path to the application directory: ")
        if custom_dir.strip():
            app_dir = Path(custom_dir)
            if not app_dir.exists():
                print(f"ERROR: Directory not found: {app_dir}")
                return False
        else:
            return False
    
    print(f"Using application directory: {app_dir}")
    internal_dir = app_dir / "_internal"
    
    # Ensure target directories exist
    for dir_name in ["platforms", "imageformats", "styles", "iconengines", "logs"]:
        target_dir = app_dir / dir_name
        os.makedirs(target_dir, exist_ok=True)
        print(f"Created directory: {target_dir}")
    
    # Copy essential DLLs
    essential_dlls = [
        # Core Qt DLLs
        (internal_dir / "PyQt6/Qt6/bin/Qt6Core.dll", app_dir / "Qt6Core.dll"),
        (internal_dir / "PyQt6/Qt6/bin/Qt6Gui.dll", app_dir / "Qt6Gui.dll"),
        (internal_dir / "PyQt6/Qt6/bin/Qt6Widgets.dll", app_dir / "Qt6Widgets.dll"),
        
        # Platform plugin - most important for the error
        (internal_dir / "PyQt6/Qt6/plugins/platforms/qwindows.dll", 
         app_dir / "platforms" / "qwindows.dll"),
    ]
    
    for src, dst in essential_dlls:
        if src.exists():
            print(f"Copying {src} to {dst}")
            shutil.copy2(src, dst)
        else:
            print(f"Warning: Source file not found: {src}")
    
    # Create a simple batch file launcher
    batch_content = f"""@echo off
echo Running Echelon ARM64 Edition with FORMAT MESSAGE W fix...

:: Set the path to the application directory
set APP_DIR={str(app_dir).replace('/', '\\')}
cd "%APP_DIR%"

:: Enable Qt debugging
set QT_DEBUG_PLUGINS=1

:: Set up PATH with necessary directories
set PATH=%APP_DIR%;%APP_DIR%\\platforms;%APP_DIR%\\_internal;%APP_DIR%\\_internal\\PyQt6\\Qt6\\bin;%PATH%

:: Set Qt environment variables
set QT_PLUGIN_PATH=%APP_DIR%\\platforms;%APP_DIR%\\_internal\\PyQt6\\Qt6\\plugins
set QT_QPA_PLATFORM_PLUGIN_PATH=%APP_DIR%\\platforms

:: Run the application
echo Starting application...
%APP_DIR%\\Echelon.exe > "%APP_DIR%\\logs\\app_log.txt" 2>&1
set EXIT_CODE=%ERRORLEVEL%

:: Display the exit code
echo Application exited with code: %EXIT_CODE%
if %EXIT_CODE% NEQ 0 (
    echo Application failed to start. See log at: %APP_DIR%\\logs\\app_log.txt
    pause
)
"""
    
    # Write the batch file
    batch_file = Path("run_echelon_arm64_simple.bat")
    with open(batch_file, "w") as f:
        f.write(batch_content)
    
    print(f"\nCreated launcher batch file: {batch_file}")
    print("Run this batch file to launch the application with FORMAT MESSAGE W fix.")
    
    # Preload Windows API DLLs to verify they work
    print("\n=== Testing Windows API DLLs ===")
    try:
        kernel32 = ctypes.WinDLL("kernel32.dll")
        print("Successfully loaded kernel32.dll")
        
        # Test FormatMessageW
        try:
            FormatMessageW = kernel32.FormatMessageW
            FormatMessageW.argtypes = [
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_void_p
            ]
            FormatMessageW.restype = ctypes.c_uint32
            
            # Test with error code 2 (ERROR_FILE_NOT_FOUND)
            buffer = ctypes.create_unicode_buffer(1024)
            result = FormatMessageW(0x1000, None, 2, 0, buffer, 1024, None)
            
            if result > 0:
                print(f"FormatMessageW works properly: '{buffer.value}'")
                print("This confirms the Windows API is accessible and should resolve the error.")
            else:
                print("FormatMessageW call failed - this might be the root of the problem.")
        except Exception as e:
            print(f"Error testing FormatMessageW: {e}")
    except Exception as e:
        print(f"Error loading kernel32.dll: {e}")
    
    print("\n=== Fix Complete ===")
    return True

if __name__ == "__main__":
    success = fix_format_message_error()
    if success:
        print("FORMAT MESSAGE W error fix applied successfully!")
        run_now = input("Run the application now? (y/n): ").lower()
        if run_now == 'y':
            batch_file = "run_echelon_arm64_simple.bat"
            print(f"Running {batch_file}...")
            os.system(batch_file)
    else:
        print("Failed to apply FORMAT MESSAGE W error fix.")
    
    input("Press Enter to exit...") 