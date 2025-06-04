#!/usr/bin/env python3
# Windows API Preloader for PyQt6 on ARM64
# This script preloads critical Windows API DLLs before launching Echelon.exe
# to prevent the FORMAT MESSAGE W failed error

import os
import sys
import ctypes
import subprocess
from pathlib import Path

def preload_windows_api_and_launch():
    """
    Preload Windows API DLLs and then launch the Echelon application
    """
    print("=== Windows API Preloader for PyQt6 on ARM64 ===")
    
    # Get paths
    base_dir = Path(os.getcwd())
    app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
    
    # Set up environment
    os.environ["QT_DEBUG_PLUGINS"] = "1"
    
    # Path to include all necessary directories
    paths = [
        str(app_dir),
        str(app_dir / "platforms"),
        str(app_dir / "imageformats"),
        str(app_dir / "styles"),
        str(app_dir / "iconengines"),
        str(app_dir / "_internal"),
        str(app_dir / "_internal" / "PyQt6" / "Qt6" / "bin"),
        os.environ.get("PATH", "")
    ]
    os.environ["PATH"] = os.pathsep.join(paths)
    
    # Qt plugin paths
    qt_plugin_paths = [
        str(app_dir / "platforms"),
        str(app_dir / "imageformats"),
        str(app_dir / "styles"),
        str(app_dir / "iconengines"),
        str(app_dir / "_internal" / "PyQt6" / "Qt6" / "plugins")
    ]
    os.environ["QT_PLUGIN_PATH"] = os.pathsep.join(qt_plugin_paths)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(app_dir / "platforms")
    
    # Windows API DLLs to preload
    windows_dlls = [
        "kernel32.dll",  # Contains FormatMessageW
        "user32.dll",    # UI functions
        "gdi32.dll",     # Graphics functions
        "advapi32.dll",  # Advanced API
        "shell32.dll",   # Shell functions
        "ole32.dll",     # OLE functions
        "oleaut32.dll",  # OLE Automation
        "version.dll",   # Version information
        "winspool.drv"   # Print spooler
    ]
    
    # Load each DLL
    loaded_dlls = []
    print("Preloading Windows API DLLs...")
    for dll_name in windows_dlls:
        try:
            dll = ctypes.WinDLL(dll_name)
            loaded_dlls.append(dll)
            print(f"  Loaded {dll_name}")
        except Exception as e:
            print(f"  Failed to load {dll_name}: {e}")
    
    # Specifically test FormatMessageW
    try:
        kernel32 = ctypes.WinDLL("kernel32.dll")
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
        
        # Test the function
        error_code = 2  # ERROR_FILE_NOT_FOUND
        buffer_size = 1024
        buffer = ctypes.create_unicode_buffer(buffer_size)
        
        # FORMAT_MESSAGE_FROM_SYSTEM = 0x1000
        result = FormatMessageW(0x1000, None, error_code, 0, buffer, buffer_size, None)
        
        if result > 0:
            print(f"FormatMessageW works: '{buffer.value}'")
        else:
            print("FormatMessageW call failed")
    except Exception as e:
        print(f"FormatMessageW test failed: {e}")
    
    # Try loading Qt DLLs directly
    try:
        # Load Qt DLLs directly to prevent issues
        qt_dlls = [
            (app_dir / "Qt6Core.dll", "Qt6Core"),
            (app_dir / "Qt6Gui.dll", "Qt6Gui"),
            (app_dir / "Qt6Widgets.dll", "Qt6Widgets"),
            (app_dir / "platforms" / "qwindows.dll", "qwindows platform")
        ]
        
        for dll_path, dll_name in qt_dlls:
            if dll_path.exists():
                try:
                    dll = ctypes.CDLL(str(dll_path))
                    print(f"  Loaded {dll_name} DLL")
                except Exception as e:
                    print(f"  Failed to load {dll_name} DLL: {e}")
            else:
                print(f"  {dll_name} DLL not found at {dll_path}")
    except Exception as e:
        print(f"Error loading Qt DLLs: {e}")
    
    # Launch the application
    print("\nLaunching Echelon.exe...")
    app_exe = app_dir / "Echelon.exe"
    
    # Change to the application directory
    os.chdir(app_dir)
    
    # Create log files
    with open("preloader_log.txt", "w") as f:
        f.write("Windows API Preloader Log\n")
        f.write(f"PATH={os.environ['PATH']}\n")
        f.write(f"QT_PLUGIN_PATH={os.environ.get('QT_PLUGIN_PATH', '')}\n")
        f.write(f"QT_QPA_PLATFORM_PLUGIN_PATH={os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH', '')}\n")
    
    try:
        # Launch the executable
        result = subprocess.run([str(app_exe)], capture_output=True, text=True)
        
        # Save output to files
        with open("app_stdout.txt", "w") as f:
            f.write(result.stdout)
        
        with open("app_stderr.txt", "w") as f:
            f.write(result.stderr)
        
        # Print status
        print(f"Application exited with code: {result.returncode}")
        
        if result.returncode != 0:
            print("\nApplication error output:")
            print(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
        
        return result.returncode
    except Exception as e:
        print(f"Error launching application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(preload_windows_api_and_launch()) 