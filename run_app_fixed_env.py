#!/usr/bin/env python3
# Direct runner that sets up environment for PyQt6 on ARM64
import os
import sys
import subprocess
from pathlib import Path

def setup_env_and_run():
    # Get paths
    base_dir = Path(os.getcwd())
    app_dir = base_dir / "WIN_BUILD" / "ARM" / "dist" / "Echelon"
    
    # Check if app exists
    if not app_dir.exists() or not (app_dir / "Echelon.exe").exists():
        print(f"Error: Application not found at {app_dir}")
        return 1
    
    # Set up environment variables
    os.environ["QT_DEBUG_PLUGINS"] = "1"
    
    # Set PATH to include all necessary directories
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
    
    # Set Qt-specific environment variables
    qt_plugin_paths = [
        str(app_dir / "platforms"),
        str(app_dir / "imageformats"),
        str(app_dir / "styles"),
        str(app_dir / "iconengines"),
        str(app_dir / "_internal" / "PyQt6" / "Qt6" / "plugins")
    ]
    os.environ["QT_PLUGIN_PATH"] = os.pathsep.join(qt_plugin_paths)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(app_dir / "platforms")
    
    # Change to app directory
    os.chdir(app_dir)
    
    # Run the application
    print(f"Running application from {app_dir}")
    result = subprocess.run([str(app_dir / "Echelon.exe")], capture_output=True, text=True)
    
    # Print output
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(setup_env_and_run())
