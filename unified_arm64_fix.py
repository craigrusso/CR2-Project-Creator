#!/usr/bin/env python3
# Unified ARM64 Fix for PyQt6 Applications
# This script combines all approaches to fix "FORMAT MESSAGE W failed" errors
# and other PyQt6 issues on Windows ARM64

import os
import sys
import shutil
import ctypes
import subprocess
import platform
from pathlib import Path
import importlib.util

def check_architecture():
    """Check if we're running on ARM64"""
    is_arm64 = platform.machine().lower() in ["arm64", "aarch64"]
    print(f"Running on ARM64: {is_arm64}")
    print(f"Python version: {platform.python_version()}")
    print(f"System: {platform.system()} {platform.release()}")
    
    # More detailed architecture check on Windows
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
            processor_arch = winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]
            processor_arch_wow64 = winreg.QueryValueEx(key, "PROCESSOR_ARCHITEW6432")[0] \
                if "PROCESSOR_ARCHITEW6432" in os.environ else "Not defined"
            winreg.CloseKey(key)
            print(f"PROCESSOR_ARCHITECTURE: {processor_arch}")
            print(f"PROCESSOR_ARCHITEW6432: {processor_arch_wow64}")
        except Exception as e:
            print(f"Error checking Windows architecture: {e}")
    
    return is_arm64

def preload_windows_api():
    """Preload critical Windows API DLLs to prevent FORMAT MESSAGE W errors"""
    print("\n=== Preloading Windows API DLLs ===")
    
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
    for dll_name in windows_dlls:
        try:
            dll = ctypes.WinDLL(dll_name)
            loaded_dlls.append(dll)
            print(f"  Loaded {dll_name}")
            
            # Specifically test FormatMessageW if this is kernel32.dll
            if dll_name == "kernel32.dll":
                try:
                    FormatMessageW = dll.FormatMessageW
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
                    
                    # Test with a simple system error code (ERROR_FILE_NOT_FOUND = 2)
                    error_code = 2
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
        except Exception as e:
            print(f"  Failed to load {dll_name}: {e}")
    
    return loaded_dlls

def check_pyqt6_installation():
    """Check if PyQt6 is properly installed and compatible with ARM64"""
    print("\n=== Checking PyQt6 Installation ===")
    
    # Check if PyQt6 is installed
    pyqt6_spec = importlib.util.find_spec("PyQt6")
    if pyqt6_spec is None:
        print("PyQt6 is NOT installed")
        return False, None
    
    pyqt6_path = Path(pyqt6_spec.origin).parent
    print(f"PyQt6 installed at: {pyqt6_path}")
    
    # Try to import PyQt6.QtCore to check version
    try:
        from PyQt6 import QtCore
        print(f"PyQt6 version: {QtCore.PYQT_VERSION_STR}")
        print(f"Qt version: {QtCore.QT_VERSION_STR}")
        return True, pyqt6_path
    except ImportError as e:
        print(f"Failed to import PyQt6.QtCore: {e}")
        return False, pyqt6_path
    except Exception as e:
        print(f"Error checking PyQt6 version: {e}")
        return False, pyqt6_path

def fix_dll_loading(app_dir=None):
    """Fix DLL loading issues by copying required DLLs to the right locations"""
    print("\n=== Fixing DLL loading issues ===")
    
    # Get paths
    base_dir = Path(os.getcwd())
    
    # If app_dir is not provided, use the default path
    if app_dir is None:
        app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
    elif isinstance(app_dir, str):
        app_dir = Path(app_dir)
    
    internal_dir = app_dir / "_internal"
    
    # Check if directories exist
    print(f"Checking app directory: {app_dir.exists()}")
    print(f"Checking internal directory: {internal_dir.exists()}")
    
    if not app_dir.exists():
        print(f"ERROR: Application directory not found: {app_dir}")
        return False
    
    # Ensure target directories exist
    for dir_name in ["platforms", "imageformats", "styles", "iconengines"]:
        target_dir = app_dir / dir_name
        os.makedirs(target_dir, exist_ok=True)
        print(f"Ensured directory exists: {target_dir}")
    
    # Create logs directory
    logs_dir = app_dir / "logs"
    os.makedirs(logs_dir, exist_ok=True)
    print(f"Created logs directory: {logs_dir}")
    
    # Essential DLLs to copy from _internal to app root
    essential_dlls = [
        # Core Qt DLLs
        (internal_dir / "PyQt6/Qt6/bin/Qt6Core.dll", app_dir / "Qt6Core.dll"),
        (internal_dir / "PyQt6/Qt6/bin/Qt6Gui.dll", app_dir / "Qt6Gui.dll"),
        (internal_dir / "PyQt6/Qt6/bin/Qt6Widgets.dll", app_dir / "Qt6Widgets.dll"),
        (internal_dir / "PyQt6/Qt6/bin/Qt6Svg.dll", app_dir / "Qt6Svg.dll"),
        (internal_dir / "PyQt6/Qt6/bin/Qt6Network.dll", app_dir / "Qt6Network.dll"),
        
        # Platform plugin
        (internal_dir / "PyQt6/Qt6/plugins/platforms/qwindows.dll", 
         app_dir / "platforms" / "qwindows.dll"),
        
        # Python DLL - try both python313.dll and python312.dll
        (internal_dir / "python313.dll", app_dir / "python313.dll"),
        (internal_dir / "python312.dll", app_dir / "python312.dll"),
        
        # Windows API dependencies often needed by Qt
        (internal_dir / "PyQt6/Qt6/bin/Qt6OpenGL.dll", app_dir / "Qt6OpenGL.dll"),
        (internal_dir / "PyQt6/Qt6/bin/Qt6DBus.dll", app_dir / "Qt6DBus.dll")
    ]
    
    # Copy essential DLLs
    for src, dst in essential_dlls:
        if src.exists():
            print(f"Copying {src} to {dst}")
            shutil.copy2(src, dst)
        else:
            print(f"Warning: Source file not found: {src}")
    
    # Copy Qt plugins to app directories
    plugin_mapping = {
        "platforms": "platforms",
        "imageformats": "imageformats",
        "styles": "styles",
        "iconengines": "iconengines"
    }
    
    qt_plugins_src = internal_dir / "PyQt6" / "Qt6" / "plugins"
    print(f"Checking Qt plugins directory: {qt_plugins_src.exists()}")
    
    if qt_plugins_src.exists():
        for plugin_type, target_dir_name in plugin_mapping.items():
            src_dir = qt_plugins_src / plugin_type
            
            if src_dir.exists():
                target_dir = app_dir / target_dir_name
                os.makedirs(target_dir, exist_ok=True)
                
                dll_files = list(src_dir.glob("*.dll"))
                print(f"Found {len(dll_files)} DLLs in {src_dir}")
                
                for file in dll_files:
                    dst_file = target_dir / file.name
                    print(f"Copying plugin {file} to {dst_file}")
                    shutil.copy2(file, dst_file)
            else:
                print(f"Warning: Plugin directory not found: {src_dir}")
    else:
        print(f"Warning: Qt plugins directory not found: {qt_plugins_src}")
    
    return True

def create_runtime_hook():
    """Create a PyQt6 runtime hook for ARM64"""
    print("\n=== Creating PyQt6 runtime hook ===")
    
    hook_content = """
# PyQt6 Runtime Hook for ARM64
import os
import sys
import ctypes

def qt_debug(msg):
    if os.environ.get('QT_DEBUG_PLUGINS', '0') == '1':
        with open('qt_debug.log', 'a') as f:
            f.write(f'{msg}\\n')

qt_debug('PyQt6 Runtime Hook starting')

# If running from PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    qt_debug(f'Running in PyInstaller bundle: {sys._MEIPASS}')
    
    # Force-load critical Windows API DLLs first
    # This helps prevent FORMAT MESSAGE W failed errors
    try:
        kernel32 = ctypes.WinDLL('kernel32.dll')
        user32 = ctypes.WinDLL('user32.dll')
        gdi32 = ctypes.WinDLL('gdi32.dll')
        
        # Pre-load FormatMessageW function
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
            qt_debug('Successfully loaded FormatMessageW function')
        except Exception as e:
            qt_debug(f'Failed to load FormatMessageW: {e}')
    except Exception as e:
        qt_debug(f'Failed to load Windows API DLLs: {e}')
    
    # Set up directories
    base_dir = sys._MEIPASS
    qt_debug(f'Base directory: {base_dir}')
    
    # Update PATH environment variable
    paths = [
        base_dir,
        os.path.join(base_dir, 'platforms'),
        os.path.join(base_dir, 'imageformats'),
        os.path.join(base_dir, 'styles'),
        os.path.join(base_dir, 'iconengines'),
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'bin'),
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'plugins')
    ]
    
    # Add our paths to the beginning of PATH
    os.environ['PATH'] = os.pathsep.join(paths) + os.pathsep + os.environ.get('PATH', '')
    qt_debug(f'Updated PATH: {os.environ["PATH"]}')
    
    # Set Qt environment variables
    qt_plugin_paths = [
        os.path.join(base_dir, 'platforms'),
        os.path.join(base_dir, 'imageformats'),
        os.path.join(base_dir, 'styles'),
        os.path.join(base_dir, 'iconengines'),
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'plugins')
    ]
    
    os.environ['QT_PLUGIN_PATH'] = os.pathsep.join(qt_plugin_paths)
    qt_debug(f'Set QT_PLUGIN_PATH to: {os.environ["QT_PLUGIN_PATH"]}')
    
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(base_dir, 'platforms')
    qt_debug(f'Set QT_QPA_PLATFORM_PLUGIN_PATH to: {os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]}')
    
    # Pre-load Qt6Core.dll from the app directory
    try:
        qt_core_path = os.path.join(base_dir, 'Qt6Core.dll')
        if os.path.exists(qt_core_path):
            qt_core = ctypes.CDLL(qt_core_path)
            qt_debug(f'Successfully loaded Qt6Core.dll from {qt_core_path}')
    except Exception as e:
        qt_debug(f'Failed to pre-load Qt6Core.dll: {e}')
    
    qt_debug('PyQt6 Runtime Hook completed')
"""
    
    # Write the hook file
    hook_file = Path("pyqt6_arm64_hook.py")
    with open(hook_file, "w") as f:
        f.write(hook_content)
    
    print(f"Created runtime hook: {hook_file}")
    return hook_file

def create_launcher_batch(app_dir=None):
    """Create a comprehensive launcher batch file"""
    print("\n=== Creating launcher batch file ===")
    
    # If app_dir is not provided, use the default path
    if app_dir is None:
        app_dir_str = "%~dp0WIN_BUILD\\ARM\\dist\\Echelon"
    else:
        app_dir_str = app_dir if isinstance(app_dir, str) else str(app_dir)
        # Convert to Windows path format
        app_dir_str = app_dir_str.replace('/', '\\')
    
    batch_content = f"""@echo off
echo Running Echelon ARM64 Edition with comprehensive fixes...

:: Set the path to the application directory
set APP_DIR={app_dir_str}
cd "%APP_DIR%"

:: Enable Qt debugging
set QT_DEBUG_PLUGINS=1

:: Clean environment (remove any existing Qt variables that might interfere)
set QT_PLUGIN_PATH=
set QT_QPA_PLATFORM_PLUGIN_PATH=

:: Set up comprehensive PATH with all necessary directories
set PATH=%APP_DIR%;%APP_DIR%\\platforms;%APP_DIR%\\imageformats;%APP_DIR%\\styles;%APP_DIR%\\iconengines;%APP_DIR%\\_internal;%APP_DIR%\\_internal\\PyQt6\\Qt6\\bin;%PATH%

:: Set Qt environment variables with multiple paths
set QT_PLUGIN_PATH=%APP_DIR%\\platforms;%APP_DIR%\\imageformats;%APP_DIR%\\styles;%APP_DIR%\\iconengines;%APP_DIR%\\_internal\\PyQt6\\Qt6\\plugins
set QT_QPA_PLATFORM_PLUGIN_PATH=%APP_DIR%\\platforms

:: Create debug log directory
if not exist "%APP_DIR%\\logs" mkdir "%APP_DIR%\\logs"

:: Create a debug log file with environment information
echo ===== ENVIRONMENT VARIABLES ===== > "%APP_DIR%\\logs\\environment.log"
echo PATH=%PATH% >> "%APP_DIR%\\logs\\environment.log"
echo QT_PLUGIN_PATH=%QT_PLUGIN_PATH% >> "%APP_DIR%\\logs\\environment.log"
echo QT_QPA_PLATFORM_PLUGIN_PATH=%QT_QPA_PLATFORM_PLUGIN_PATH% >> "%APP_DIR%\\logs\\environment.log"
echo. >> "%APP_DIR%\\logs\\environment.log"

echo ===== DLL FILES ===== >> "%APP_DIR%\\logs\\environment.log"
dir /b /s "%APP_DIR%\\*.dll" >> "%APP_DIR%\\logs\\environment.log"
echo. >> "%APP_DIR%\\logs\\environment.log"

:: Run the application with full error output
echo Environment set. Starting application...
echo Running: %APP_DIR%\\Echelon.exe > "%APP_DIR%\\logs\\app_log.txt"
%APP_DIR%\\Echelon.exe >> "%APP_DIR%\\logs\\app_log.txt" 2>&1
set EXIT_CODE=%ERRORLEVEL%

:: Display the exit code
echo Application exited with code: %EXIT_CODE%

:: Show the log file if there was an error
if %EXIT_CODE% NEQ 0 (
    echo Application failed to start. Here's the log:
    type "%APP_DIR%\\logs\\app_log.txt"
    echo.
    echo Environment debug information:
    type "%APP_DIR%\\logs\\environment.log"
    pause
) else (
    echo Application started successfully.
)
"""
    
    # Write the batch file
    batch_file = Path("run_echelon_arm64_unified.bat")
    with open(batch_file, "w") as f:
        f.write(batch_content)
    
    print(f"Created launcher batch file: {batch_file}")
    return batch_file

def create_python_launcher(app_dir=None):
    """Create a Python-based launcher script"""
    print("\n=== Creating Python launcher ===")
    
    # If app_dir is not provided, use the default path
    if app_dir is None:
        app_dir_str = "WIN_BUILD/ARM/dist/Echelon"
    else:
        app_dir_str = app_dir if isinstance(app_dir, str) else str(app_dir)
    
    # Use triple quotes with proper escaping for the launcher content
    launcher_content = """#!/usr/bin/env python3
# Echelon ARM64 Python Launcher
# This script sets up the environment and launches Echelon.exe

import os
import sys
import ctypes
import subprocess
from pathlib import Path

def launch_echelon():
    \"\"\"Set up the environment and launch Echelon.exe\"\"\"
    print("=== Echelon ARM64 Python Launcher ===")
    
    # Get paths
    base_dir = Path(os.getcwd())
    app_dir = base_dir / "{0}"
    
    if not app_dir.exists():
        print(f"ERROR: Application directory not found: {{app_dir}}")
        return 1
    
    # Create logs directory
    logs_dir = app_dir / "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
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
    
    # Preload Windows API DLLs
    windows_dlls = ["kernel32.dll", "user32.dll", "gdi32.dll"]
    for dll_name in windows_dlls:
        try:
            dll = ctypes.WinDLL(dll_name)
            print(f"Loaded {{dll_name}}")
        except Exception as e:
            print(f"Failed to load {{dll_name}}: {{e}}")
    
    # Preload critical Qt DLLs
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
                print(f"Loaded {{dll_name}} DLL")
            except Exception as e:
                print(f"Failed to load {{dll_name}} DLL: {{e}}")
        else:
            print(f"{{dll_name}} DLL not found at {{dll_path}}")
    
    # Change to the application directory
    os.chdir(app_dir)
    
    # Launch the application
    print(f"Launching Echelon.exe from {{app_dir}}")
    app_exe = app_dir / "Echelon.exe"
    
    try:
        result = subprocess.run([str(app_exe)], capture_output=True, text=True)
        return result.returncode
    except Exception as e:
        print(f"Error launching application: {{e}}")
        return 1

if __name__ == "__main__":
    sys.exit(launch_echelon())
""".format(app_dir_str)
    
    # Write the launcher script
    launcher_file = Path("run_echelon_arm64_unified.py")
    with open(launcher_file, "w") as f:
        f.write(launcher_content)
    
    print(f"Created Python launcher: {launcher_file}")
    return launcher_file

def main():
    """Main function to fix Echelon ARM64 issues"""
    print("===== Unified ARM64 Fix for PyQt6 Applications =====")
    
    # Check architecture
    is_arm64 = check_architecture()
    if not is_arm64:
        print("WARNING: Not running on ARM64 architecture!")
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            print("Aborted.")
            return 1
    
    # Preload Windows API DLLs
    preload_windows_api()
    
    # Check PyQt6 installation
    is_installed, pyqt6_path = check_pyqt6_installation()
    
    # Prompt for application directory
    default_app_dir = "WIN_BUILD/ARM/dist/Echelon"
    print(f"\nDefault application directory: {default_app_dir}")
    custom_dir = input("Enter custom application directory or press Enter for default: ")
    
    app_dir = Path(custom_dir) if custom_dir.strip() else Path(default_app_dir)
    print(f"Using application directory: {app_dir}")
    
    # Fix DLLs
    if not fix_dll_loading(app_dir):
        print("Failed to fix DLLs.")
        return 1
    
    # Create runtime hook
    hook_file = create_runtime_hook()
    
    # Create launcher batch file
    batch_file = create_launcher_batch(app_dir)
    
    # Create Python launcher
    python_launcher = create_python_launcher(app_dir)
    
    print("\n===== Fix Complete =====")
    print("The following files were created:")
    print(f"1. {hook_file} - PyQt6 runtime hook for ARM64")
    print(f"2. {batch_file} - Batch file launcher")
    print(f"3. {python_launcher} - Python-based launcher")
    print("\nTo run the application:")
    print(f"1. Run the batch file: .\\{batch_file}")
    print(f"2. Or use the Python launcher: python {python_launcher}")
    
    # Ask if user wants to run the application now
    run_now = input("\nDo you want to run the application now? (y/n): ").lower()
    if run_now == 'y':
        print("\nRunning the application...")
        try:
            subprocess.run([batch_file], shell=True)
        except Exception as e:
            print(f"Error running application: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 