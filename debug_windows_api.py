import os
import sys
import ctypes
from pathlib import Path
import subprocess

def debug_format_message_error():
    """
    Debug the 'FORMAT MESSAGE W failed' error by loading critical Windows API DLLs 
    and directly testing FormatMessageW function
    """
    print("==== Debugging FORMAT MESSAGE W Error ====")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Get paths
    base_dir = Path(os.getcwd())
    app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
    
    # Critical Windows API DLLs involved in FormatMessage calls
    critical_dlls = [
        "kernel32.dll",
        "user32.dll", 
        "gdi32.dll",
        "advapi32.dll",
        "shell32.dll",
        "ole32.dll",
        "oleaut32.dll",
        "version.dll",
        "winspool.drv"
    ]
    
    # Try to load each critical DLL
    dll_results = {}
    for dll_name in critical_dlls:
        try:
            dll = ctypes.WinDLL(dll_name)
            dll_results[dll_name] = "Loaded successfully"
            
            # If it's kernel32.dll, try to call FormatMessageW directly
            if dll_name == "kernel32.dll":
                try:
                    # Attempt to call FormatMessageW directly
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
                        dll_results[dll_name] = f"FormatMessageW works: '{buffer.value}'"
                    else:
                        dll_results[dll_name] = "FormatMessageW call failed"
                except Exception as e:
                    dll_results[dll_name] = f"FormatMessageW test failed: {e}"
        except Exception as e:
            dll_results[dll_name] = f"Failed to load: {e}"
    
    # Print results
    print("\n=== Critical Windows DLL Test Results ===")
    for dll_name, result in dll_results.items():
        print(f"{dll_name}: {result}")
    
    print("\n=== Testing PyQt6 directly ===")
    # Now try importing PyQt6 in a separate process to isolate errors
    qt_test_script = """
import sys
try:
    print(f"Python: {sys.version}")
    from PyQt6.QtWidgets import QApplication
    print("Successfully imported QApplication")
    app = QApplication([])
    print("Successfully created QApplication instance")
    from PyQt6.QtCore import QCoreApplication
    print(f"Qt version: {QCoreApplication.applicationVersion()}")
    from PyQt6.QtGui import QIcon
    print("Successfully imported QIcon")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    qt_test_file = base_dir / "qt_test.py"
    with open(qt_test_file, "w") as f:
        f.write(qt_test_script)
    
    print(f"Running PyQt6 test...")
    
    # Set environment variables first
    env = os.environ.copy()
    env["QT_DEBUG_PLUGINS"] = "1"
    env["PATH"] = str(app_dir) + os.pathsep + \
                 str(app_dir / "platforms") + os.pathsep + \
                 str(app_dir / "_internal") + os.pathsep + \
                 str(app_dir / "_internal" / "PyQt6" / "Qt6" / "bin") + os.pathsep + \
                 env.get("PATH", "")
    
    result = subprocess.run([sys.executable, str(qt_test_file)], 
                            capture_output=True, text=True, env=env)
    
    print("\nPyQt6 Test STDOUT:")
    print(result.stdout)
    
    print("\nPyQt6 Test STDERR:")
    print(result.stderr)
    
    print("\n=== Summary ===")
    if "FORMAT_MESSAGE_W" in result.stderr or "FORMAT MESSAGE W" in result.stderr:
        print("FORMAT MESSAGE W error detected in PyQt6 test!")
        
        # Now try to fix by directly injecting kernel32.dll FormatMessageW into the process
        print("\nAttempting direct Windows API injection fix...")
        
        # Create a special test with Windows API preloading
        api_fix_script = """
import os
import sys
import ctypes

# Directly load kernel32.dll and other critical DLLs
print("Preloading Windows API DLLs...")
kernel32 = ctypes.WinDLL("kernel32.dll")
user32 = ctypes.WinDLL("user32.dll")
gdi32 = ctypes.WinDLL("gdi32.dll")

# Verify FormatMessageW is accessible
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
    
    # Test with a simple system error code (ERROR_FILE_NOT_FOUND = 2)
    error_code = 2
    buffer_size = 1024
    buffer = ctypes.create_unicode_buffer(buffer_size)
    
    # FORMAT_MESSAGE_FROM_SYSTEM = 0x1000
    result = FormatMessageW(0x1000, None, error_code, 0, buffer, buffer_size, None)
    print(f"FormatMessageW test result: {result} - '{buffer.value if result else 'Failed'}'")
except Exception as e:
    print(f"FormatMessageW setup failed: {e}")
    import traceback
    traceback.print_exc()

# Now try to import and use PyQt6
try:
    print("\\nImporting PyQt6...")
    from PyQt6.QtWidgets import QApplication
    print("Successfully imported QApplication")
    app = QApplication([])
    print("Successfully created QApplication instance")
    from PyQt6.QtCore import QCoreApplication
    print(f"Qt version: {QCoreApplication.applicationVersion()}")
except Exception as e:
    print(f"PyQt6 error after Windows API preloading: {e}")
    import traceback
    traceback.print_exc()
"""
        
        api_fix_file = base_dir / "api_fix_test.py"
        with open(api_fix_file, "w") as f:
            f.write(api_fix_script)
        
        print(f"Running Windows API fix test...")
        
        result = subprocess.run([sys.executable, str(api_fix_file)], 
                                capture_output=True, text=True, env=env)
        
        print("\nAPI Fix Test STDOUT:")
        print(result.stdout)
        
        print("\nAPI Fix Test STDERR:")
        print(result.stderr)
        
        if result.returncode == 0 and "Successfully created QApplication instance" in result.stdout:
            print("\nAPI PRELOADING FIX WORKED!")
            print("The issue is related to Windows API function resolution.")
            print("Create a modified launcher that preloads Windows API DLLs before PyQt6.")
        else:
            print("\nAPI preloading did not fix the issue.")
    else:
        print("FORMAT MESSAGE W error not detected in direct PyQt6 test.")
        print("The error might be specific to the application code.")
    
    print("\n==== Debug Complete ====")

if __name__ == "__main__":
    debug_format_message_error() 