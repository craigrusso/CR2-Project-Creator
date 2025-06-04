
# PyQt6 ARM64 Runtime Hook
import os
import sys
import ctypes

def debug_print(msg):
    with open("qt_debug.log", "a") as f:
        f.write(msg + "\n")

debug_print("PyQt6 ARM64 Runtime Hook starting")

# If running from PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    debug_print(f"Running in PyInstaller bundle: {sys._MEIPASS}")
    
    # Add _internal directory to PATH
    os.environ['PATH'] = os.path.join(sys._MEIPASS) + os.pathsep +                         os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'bin') + os.pathsep +                         os.environ.get('PATH', '')
    
    debug_print(f"Updated PATH: {os.environ['PATH']}")
    
    # Set Qt environment variables
    plugin_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'plugins')
    if os.path.exists(plugin_path):
        os.environ['QT_PLUGIN_PATH'] = plugin_path
        debug_print(f"Set QT_PLUGIN_PATH to: {plugin_path}")
    
    platforms_path = os.path.join(plugin_path, 'platforms')
    if os.path.exists(platforms_path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms_path
        debug_print(f"Set QT_QPA_PLATFORM_PLUGIN_PATH to: {platforms_path}")
    
    # Try loading Qt6Core.dll explicitly
    try:
        qt_core_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'bin', 'Qt6Core.dll')
        if os.path.exists(qt_core_path):
            debug_print(f"Loading Qt6Core.dll from: {qt_core_path}")
            ctypes.WinDLL(qt_core_path)
            debug_print("Successfully loaded Qt6Core.dll")
    except Exception as e:
        debug_print(f"Error loading Qt6Core.dll: {e}")
        
    # List DLLs in _internal directory
    internal_dir = os.path.join(sys._MEIPASS)
    debug_print(f"Files in _internal directory:")
    for root, dirs, files in os.walk(internal_dir):
        for file in files:
            if file.endswith('.dll'):
                debug_print(f"  {os.path.join(root, file)}")
    
    debug_print("PyQt6 ARM64 Runtime Hook completed")
