import os
import sys
import subprocess
import ctypes
from pathlib import Path

def check_dll_architecture(dll_path):
    """Check if a DLL is compiled for ARM64 architecture"""
    try:
        # Constants for machine types
        IMAGE_FILE_MACHINE_AMD64 = 0x8664  # x64
        IMAGE_FILE_MACHINE_I386 = 0x014c   # x86
        IMAGE_FILE_MACHINE_ARM64 = 0xAA64  # ARM64
        
        # Open the DLL file
        dll_file = open(dll_path, 'rb')
        
        # Read the first 2 bytes to check for MZ signature
        dll_data = dll_file.read(2)
        if dll_data != b'MZ':
            dll_file.close()
            return "Not a valid PE file (no MZ signature)"
        
        # Seek to e_lfanew field (offset 60)
        dll_file.seek(60)
        e_lfanew = int.from_bytes(dll_file.read(4), byteorder='little')
        
        # Seek to the PE header
        dll_file.seek(e_lfanew)
        signature = dll_file.read(4)
        if signature != b'PE\0\0':
            dll_file.close()
            return "Not a valid PE file (no PE signature)"
        
        # Read the machine type field
        machine = int.from_bytes(dll_file.read(2), byteorder='little')
        dll_file.close()
        
        # Return the architecture based on machine type
        if machine == IMAGE_FILE_MACHINE_ARM64:
            return "ARM64"
        elif machine == IMAGE_FILE_MACHINE_AMD64:
            return "x64"
        elif machine == IMAGE_FILE_MACHINE_I386:
            return "x86"
        else:
            return f"Unknown architecture: 0x{machine:04x}"
    except Exception as e:
        return f"Error checking DLL: {e}"

def main():
    print("Echelon ARM64 Diagnostic Tool")
    print("=============================")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Architecture: {os.environ.get('PROCESSOR_ARCHITECTURE', 'Unknown')}")
    
    # Set paths
    base_dir = Path(os.getcwd())
    app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
    internal_dir = app_dir / "_internal"
    
    print(f"\nChecking paths:")
    print(f"Base directory: {base_dir} (exists: {base_dir.exists()})")
    print(f"App directory: {app_dir} (exists: {app_dir.exists()})")
    print(f"Internal directory: {internal_dir} (exists: {internal_dir.exists()})")
    
    # Check if the executable exists
    exe_path = app_dir / "Echelon.exe"
    print(f"\nEchelon.exe: {exe_path} (exists: {exe_path.exists()})")
    
    # Check critical DLLs
    print("\nChecking critical DLLs:")
    critical_dlls = [
        internal_dir / "python313.dll",
        internal_dir / "python3.dll",
        internal_dir / "PyQt6" / "Qt6" / "bin" / "Qt6Core.dll",
        internal_dir / "PyQt6" / "Qt6" / "bin" / "Qt6Gui.dll",
        internal_dir / "PyQt6" / "Qt6" / "bin" / "Qt6Widgets.dll"
    ]
    
    for dll_path in critical_dlls:
        if dll_path.exists():
            arch = check_dll_architecture(str(dll_path))
            print(f"{dll_path.name}: Found - Architecture: {arch}")
        else:
            print(f"{dll_path.name}: NOT FOUND at {dll_path}")
    
    # Try running the app with different settings
    print("\nAttempting to run Echelon with modified environment...")
    try:
        env = os.environ.copy()
        env["PATH"] = f"{internal_dir};{internal_dir / 'PyQt6' / 'Qt6' / 'bin'};{env.get('PATH', '')}"
        
        # Run the executable with the modified environment
        process = subprocess.Popen(
            [str(exe_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for a short time to see if it starts
        try:
            stdout, stderr = process.communicate(timeout=5)
            print(f"Process exited with code: {process.returncode}")
            if stdout:
                print(f"Standard output: {stdout}")
            if stderr:
                print(f"Standard error: {stderr}")
        except subprocess.TimeoutExpired:
            print("Process is running (no immediate crash)")
            process.kill()
    except Exception as e:
        print(f"Error running executable: {e}")
    
    print("\nDiagnostic complete.")

if __name__ == "__main__":
    main() 