import os
import sys
import subprocess
import traceback
from pathlib import Path

def run_with_detailed_logging():
    """Run the Echelon app with detailed error logging"""
    try:
        # Set paths
        base_dir = Path(os.getcwd())
        app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
        exe_path = app_dir / "Echelon.exe"
        internal_dir = app_dir / "_internal"
        
        print(f"Current directory: {base_dir}")
        print(f"Application directory: {app_dir}")
        print(f"Executable path: {exe_path}")
        
        if not exe_path.exists():
            print(f"ERROR: Executable not found at {exe_path}")
            return
        
        # Create environment with proper paths
        env = os.environ.copy()
        
        # Add paths to DLLs
        path_additions = [
            str(internal_dir),
            str(internal_dir / "PyQt6" / "Qt6" / "bin"),
            str(internal_dir / "PyQt6" / "Qt6" / "plugins" / "platforms")
        ]
        
        env["PATH"] = os.pathsep.join(path_additions) + os.pathsep + env.get("PATH", "")
        
        # Set Qt environment variables
        env["QT_PLUGIN_PATH"] = str(internal_dir / "PyQt6" / "Qt6" / "plugins")
        env["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(internal_dir / "PyQt6" / "Qt6" / "plugins" / "platforms")
        env["QT_DEBUG_PLUGINS"] = "1"  # Enable Qt plugin debugging
        
        print("\nEnvironment variables:")
        print(f"PATH additions: {os.pathsep.join(path_additions)}")
        print(f"QT_PLUGIN_PATH: {env['QT_PLUGIN_PATH']}")
        print(f"QT_QPA_PLATFORM_PLUGIN_PATH: {env['QT_QPA_PLATFORM_PLUGIN_PATH']}")
        
        # Check platform plugin exists
        platforms_dir = internal_dir / "PyQt6" / "Qt6" / "plugins" / "platforms"
        qwindows_dll = platforms_dir / "qwindows.dll"
        print(f"\nChecking platforms plugin:")
        print(f"Platforms directory exists: {platforms_dir.exists()}")
        print(f"qwindows.dll exists: {qwindows_dll.exists()}")
        
        # Create error log file
        error_log = base_dir / "app_error_log.txt"
        
        print(f"\nRunning the application and logging errors to: {error_log}")
        
        # Execute the application with redirected output
        with open(error_log, "w") as log:
            # First, write some diagnostic info to the log
            log.write(f"Echelon ARM64 Error Log\n")
            log.write(f"======================\n\n")
            log.write(f"Executable: {exe_path}\n")
            log.write(f"PATH: {env['PATH']}\n")
            log.write(f"QT_PLUGIN_PATH: {env['QT_PLUGIN_PATH']}\n")
            log.write(f"QT_QPA_PLATFORM_PLUGIN_PATH: {env['QT_QPA_PLATFORM_PLUGIN_PATH']}\n\n")
            log.write(f"--- Application Output ---\n\n")
            log.flush()
            
            # Now run the process
            process = subprocess.Popen(
                [str(exe_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(app_dir)
            )
            
            # Wait for process to complete
            stdout, stderr = process.communicate(timeout=15)
            
            # Write output to log
            log.write("STDOUT:\n")
            log.write(stdout if stdout else "No output\n")
            log.write("\nSTDERR:\n")
            log.write(stderr if stderr else "No errors\n")
            
            # Write exit code
            log.write(f"\nExit code: {process.returncode}\n")
        
        # Display results
        print(f"\nApplication exited with code: {process.returncode}")
        print("Check the error log for details.")
        
        # Print the contents of the error log
        print("\nError log contents:")
        with open(error_log, "r") as log:
            print(log.read())
    
    except Exception as e:
        print(f"Error running diagnostic: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_with_detailed_logging() 