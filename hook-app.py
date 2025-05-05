# PyInstaller runtime hook to ensure the app module is available
import os
import sys

# Adjust the Python path to include the app directory
def install_hook():
    # Get the base directory where the executable is located
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    
    # Add paths to sys.path to make the app module importable
    app_dir = os.path.join(base_dir, 'app')
    if os.path.exists(app_dir) and app_dir not in sys.path:
        sys.path.insert(0, app_dir)
        print(f"Added {app_dir} to sys.path")

    # Also add the base directory itself to ensure main.py can find 'app'
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
        print(f"Added {base_dir} to sys.path")

    # Print the current sys.path for debugging
    print(f"sys.path = {sys.path}")

    # Also check if app directories exist
    print(f"app directory exists: {os.path.exists(app_dir)}")
    print(f"app/core exists: {os.path.exists(os.path.join(app_dir, 'core'))}")

# Install the hook
install_hook() 