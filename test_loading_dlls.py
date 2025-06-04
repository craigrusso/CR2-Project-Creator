import os
import sys
import ctypes
from pathlib import Path

def test_dll_loading():
    """Test loading Qt DLLs directly to diagnose issues"""
    try:
        print("==== Testing DLL Loading for ARM64 ====")
        print(f"Python version: {sys.version}")
        print(f"Platform: {sys.platform}")
        
        # Get paths
        base_dir = Path(os.getcwd())
        app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
        internal_dir = app_dir / "_internal"
        
        # List of DLLs to test
        dlls_to_test = [
            app_dir / "Qt6Core.dll",
            app_dir / "Qt6Gui.dll",
            app_dir / "Qt6Widgets.dll",
            app_dir / "platforms" / "qwindows.dll",
            internal_dir / "python313.dll",
            internal_dir / "PyQt6" / "Qt6" / "bin" / "Qt6Core.dll",
            internal_dir / "PyQt6" / "Qt6" / "bin" / "Qt6Gui.dll",
            internal_dir / "PyQt6" / "Qt6" / "bin" / "Qt6Widgets.dll",
            internal_dir / "PyQt6" / "Qt6" / "plugins" / "platforms" / "qwindows.dll"
        ]
        
        # Update PATH to include necessary directories
        os.environ["PATH"] = str(app_dir) + os.pathsep + \
                            str(app_dir / "platforms") + os.pathsep + \
                            str(internal_dir) + os.pathsep + \
                            str(internal_dir / "PyQt6" / "Qt6" / "bin") + os.pathsep + \
                            os.environ.get("PATH", "")
        
        print(f"\nUpdated PATH: {os.environ['PATH']}")
        
        # Try to load each DLL
        print("\nTesting DLL loading...")
        for dll_path in dlls_to_test:
            print(f"\nTrying to load: {dll_path}")
            
            if not dll_path.exists():
                print(f"  ERROR: File does not exist")
                continue
            
            try:
                # Get file size to check if it's a valid file
                size = dll_path.stat().st_size
                print(f"  File size: {size} bytes")
                
                # Try to load the DLL
                dll = ctypes.WinDLL(str(dll_path))
                print(f"  SUCCESS: DLL loaded successfully")
                
                # For Qt DLLs, try to get version if possible
                if "Qt6" in dll_path.name:
                    try:
                        # This might fail but it's worth trying
                        if hasattr(dll, 'qVersion'):
                            version = dll.qVersion()
                            print(f"  Qt version: {version}")
                    except Exception as e:
                        print(f"  Could not get Qt version: {e}")
                
            except Exception as e:
                print(f"  FAILED: {e}")
        
        print("\n==== DLL Loading Test Complete ====")
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dll_loading() 