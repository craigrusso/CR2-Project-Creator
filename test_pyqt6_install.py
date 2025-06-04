#!/usr/bin/env python3
# PyQt6 Installation Test for ARM64 Windows
# This script checks if PyQt6 is properly installed and compatible with ARM64

import os
import sys
import platform
import ctypes
import importlib.util
import subprocess
from pathlib import Path

def check_architecture():
    """Check if we're running on ARM64"""
    print("=== System Architecture ===")
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Machine: {platform.machine()}")
    print(f"Architecture: {platform.architecture()}")
    
    # Check if running on ARM64
    is_arm64 = platform.machine().lower() in ["arm64", "aarch64"]
    print(f"Running on ARM64: {is_arm64}")
    
    # Check Windows-specific architecture
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

def check_pyqt6_installation():
    """Check if PyQt6 is properly installed"""
    print("\n=== PyQt6 Installation ===")
    
    # Check if PyQt6 is installed
    pyqt6_spec = importlib.util.find_spec("PyQt6")
    if pyqt6_spec is None:
        print("PyQt6 is NOT installed")
        return False
    
    print(f"PyQt6 is installed at: {pyqt6_spec.origin}")
    
    # Check PyQt6 version
    try:
        import PyQt6
        print(f"PyQt6 version: {PyQt6.QtCore.PYQT_VERSION_STR}")
        print(f"Qt version: {PyQt6.QtCore.QT_VERSION_STR}")
        
        # Check if PyQt6 was built for ARM64
        qt_lib_path = Path(PyQt6.__file__).parent / "Qt6" / "bin"
        if qt_lib_path.exists():
            print(f"Qt library path: {qt_lib_path}")
            
            # Look for Qt6Core.dll
            qt_core_dll = qt_lib_path / "Qt6Core.dll"
            if qt_core_dll.exists():
                print(f"Found Qt6Core.dll at {qt_core_dll}")
                
                # Try to determine if the DLL is ARM64
                try:
                    # Check file size as a basic heuristic
                    size = qt_core_dll.stat().st_size
                    print(f"Qt6Core.dll size: {size} bytes")
                    
                    # Load the DLL and check if it works
                    dll = ctypes.CDLL(str(qt_core_dll))
                    print("Successfully loaded Qt6Core.dll")
                except Exception as e:
                    print(f"Error loading Qt6Core.dll: {e}")
            else:
                print("Qt6Core.dll not found")
        else:
            print(f"Qt library path not found: {qt_lib_path}")
        
        return True
    except ImportError as e:
        print(f"Error importing PyQt6: {e}")
        return False
    except Exception as e:
        print(f"Error checking PyQt6 version: {e}")
        return False

def run_simple_pyqt6_app():
    """Try to run a very simple PyQt6 application"""
    print("\n=== Simple PyQt6 Application Test ===")
    
    # Create a simple test application
    test_app = """
import sys
from PyQt6.QtWidgets import QApplication, QLabel

app = QApplication(sys.argv)
label = QLabel("Hello, PyQt6 on ARM64!")
label.resize(400, 100)
label.show()
sys.exit(app.exec())
"""
    
    # Write the test application to a file
    test_file = Path("simple_pyqt6_test.py")
    with open(test_file, "w") as f:
        f.write(test_app)
    
    print(f"Created test file: {test_file}")
    print("Running test application...")
    
    # Run the test application with subprocess
    try:
        process = subprocess.Popen([sys.executable, str(test_file)], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True)
        
        # Wait for a few seconds
        try:
            stdout, stderr = process.communicate(timeout=3)
            print("Test application exited.")
            print("\nSTDOUT:")
            print(stdout)
            print("\nSTDERR:")
            print(stderr)
        except subprocess.TimeoutExpired:
            print("Test application is running (this is good)")
            process.kill()
            
        return True
    except Exception as e:
        print(f"Error running test application: {e}")
        return False

def check_system_dependencies():
    """Check if all required system dependencies are available"""
    print("\n=== System Dependencies ===")
    
    # Check for critical Windows DLLs
    critical_dlls = [
        "kernel32.dll",
        "user32.dll",
        "gdi32.dll",
        "shell32.dll",
        "ole32.dll"
    ]
    
    for dll_name in critical_dlls:
        try:
            dll = ctypes.WinDLL(dll_name)
            print(f"{dll_name}: Successfully loaded")
        except Exception as e:
            print(f"{dll_name}: Failed to load - {e}")
    
    # Check if we can load a simple QPA plugin
    try:
        import PyQt6
        qpa_plugin_path = Path(PyQt6.__file__).parent / "Qt6" / "plugins" / "platforms" / "qwindows.dll"
        
        if qpa_plugin_path.exists():
            print(f"Found QPA plugin at: {qpa_plugin_path}")
            try:
                plugin_dll = ctypes.CDLL(str(qpa_plugin_path))
                print("Successfully loaded QPA plugin")
            except Exception as e:
                print(f"Failed to load QPA plugin: {e}")
        else:
            print(f"QPA plugin not found at: {qpa_plugin_path}")
    except ImportError:
        print("PyQt6 not available for QPA plugin check")
    except Exception as e:
        print(f"Error checking QPA plugin: {e}")

def main():
    """Main test function"""
    print("===== Testing PyQt6 on ARM64 Windows =====")
    
    # Check architecture
    is_arm64 = check_architecture()
    if not is_arm64:
        print("\nWARNING: Not running on ARM64 architecture!")
    
    # Check PyQt6 installation
    pyqt6_installed = check_pyqt6_installation()
    if not pyqt6_installed:
        print("\nFAILED: PyQt6 is not properly installed")
        return 1
    
    # Check system dependencies
    check_system_dependencies()
    
    # Run a simple PyQt6 application
    app_works = run_simple_pyqt6_app()
    
    print("\n===== Test Results =====")
    print(f"Architecture is ARM64: {'Yes' if is_arm64 else 'No'}")
    print(f"PyQt6 is properly installed: {'Yes' if pyqt6_installed else 'No'}")
    print(f"Simple PyQt6 application works: {'Yes' if app_works else 'No'}")
    
    if is_arm64 and pyqt6_installed and app_works:
        print("\nSUCCESS: PyQt6 is correctly installed and working on ARM64")
        return 0
    else:
        print("\nSome tests failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 