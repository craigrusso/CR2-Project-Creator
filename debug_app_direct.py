import os
import sys
import subprocess
import traceback
from pathlib import Path

def copy_system_dlls():
    """Copy needed system DLLs to the application directory"""
    try:
        # Get paths
        base_dir = Path(os.getcwd())
        app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
        internal_dir = app_dir / "_internal"
        
        # Check Python installation directory
        python_dir = Path(sys.executable).parent
        python_dll = python_dir / "python313.dll"
        
        print(f"Python directory: {python_dir}")
        print(f"Python DLL exists: {python_dll.exists()}")
        
        # Copy the Python DLL if needed
        if python_dll.exists():
            target = app_dir / "python313.dll"
            if not target.exists():
                print(f"Copying {python_dll} to {target}")
                import shutil
                shutil.copy2(python_dll, target)
                print("Copy complete")
    except Exception as e:
        print(f"Error copying DLLs: {e}")
        traceback.print_exc()

def run_with_cmd():
    """Run the Echelon app with cmd.exe to capture all console output"""
    try:
        # Set paths
        base_dir = Path(os.getcwd())
        app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
        exe_path = app_dir / "Echelon.exe"
        
        if not exe_path.exists():
            print(f"ERROR: Executable not found at {exe_path}")
            return
        
        # Create a batch file to run the app with environment variables
        batch_file = base_dir / "run_debug.bat"
        batch_content = f"""@echo off
echo Running Echelon with debugging...
cd /d "{app_dir}"
set PATH="{app_dir}\\\_internal";"{app_dir}\\\_internal\\PyQt6\\Qt6\\bin";"%PATH%"
set QT_DEBUG_PLUGINS=1
set QT_PLUGIN_PATH="{app_dir}\\\_internal\\PyQt6\\Qt6\\plugins"
set QT_QPA_PLATFORM_PLUGIN_PATH="{app_dir}\\\_internal\\PyQt6\\Qt6\\plugins\\platforms"
echo Environment set. Starting application...
"{exe_path}" > app_output.txt 2>&1
echo Exit code: %ERRORLEVEL%
pause
"""
        
        with open(batch_file, "w") as f:
            f.write(batch_content)
        
        print(f"Created batch file: {batch_file}")
        print("Running batch file - check the command window for output")
        
        # Run the batch file
        os.startfile(batch_file)
        
    except Exception as e:
        print(f"Error running diagnostic: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    copy_system_dlls()
    run_with_cmd() 