
# PyQt6 Runtime Hook for ARM64
import os
import sys
import ctypes

def qt_debug(msg):
    if os.environ.get('QT_DEBUG_PLUGINS', '0') == '1':
        with open('qt_debug.log', 'a') as f:
            f.write(f'{msg}\n')

qt_debug('PyQt6 Runtime Hook starting')

# If running from PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    qt_debug(f'Running in PyInstaller bundle: {sys._MEIPASS}')
    
    # Set up directories
    base_dir = sys._MEIPASS
    qt_debug(f'Base directory: {base_dir}')
    
    # Update PATH environment variable
    paths = [
        base_dir,
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'bin'),
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'plugins')
    ]
    
    # Add our paths to the beginning of PATH
    os.environ['PATH'] = os.pathsep.join(paths) + os.pathsep + os.environ.get('PATH', '')
    qt_debug(f'Updated PATH: {os.environ["PATH"]}')
    
    # Set Qt environment variables
    plugins_dir = os.path.join(base_dir, 'PyQt6', 'Qt6', 'plugins')
    if os.path.exists(plugins_dir):
        os.environ['QT_PLUGIN_PATH'] = plugins_dir
        qt_debug(f'Set QT_PLUGIN_PATH to: {plugins_dir}')
    
    platforms_dir = os.path.join(plugins_dir, 'platforms')
    if os.path.exists(platforms_dir):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms_dir
        qt_debug(f'Set QT_QPA_PLATFORM_PLUGIN_PATH to: {platforms_dir}')
    
    # List all DLLs we found for debugging
    qt_debug('Found DLLs:')
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.dll'):
                qt_debug(f'  {os.path.join(root, file)}')
    
    qt_debug('PyQt6 Runtime Hook completed')
