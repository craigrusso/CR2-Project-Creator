import sys
from setuptools import setup
import os # Import os to use os.walk

# --- App Information ---
APP = ['main.py']
PACKAGES = ['PyQt5', 'app', 'json', 'webbrowser'] # Include necessary packages

# --- Data Files --- 
# Function to recursively find all files in a directory
def find_data_files(source_dir):
    data_files_list = []
    for root, dirs, files in os.walk(source_dir):
        # Filter out __pycache__ directories and .pyc files
        dirs[:] = [d for d in dirs if d != '__pycache__']
        files = [f for f in files if not f.endswith('.pyc')]
        if files:
            # The destination path should be relative to the bundle's Resources dir
            dest_path = os.path.join('app', os.path.relpath(root, 'app'))
            sources = [os.path.join(root, f) for f in files]
            data_files_list.append((dest_path, sources))
    return data_files_list

# Automatically include all files within app/assets
DATA_FILES = find_data_files('app/assets')
# Also include the top-level icon file directly
# DATA_FILES.append( ('.', ['Icons/Echelon.icns']) ) # Removed - iconfile option handles this


# --- Plist Configuration ---
# Extract main version components for Plist
app_version_full = "0.95.14" # Incremented patch version, removing runtime option
version_parts = app_version_full.split('.')
major_version = version_parts[0]
minor_version = version_parts[1] if len(version_parts) > 1 else '0'
patch_version = version_parts[2] if len(version_parts) > 2 else '0' # Assuming SemVer X.Y.Z
bundle_version = f"{major_version}.{minor_version}.{patch_version}"

# Info Plist configuration
PLIST = {
    'CFBundleName': 'Echelon Project', # Your App Name
    'CFBundleDisplayName': 'Echelon Project',
    'CFBundleGetInfoString': 'Echelon batch project creator',
    'CFBundleIdentifier': 'com.cr2creative.echelon', # Your Bundle ID
    'CFBundleVersion': app_version_full, # Build version (must increment)
    'CFBundleShortVersionString': bundle_version, # Marketing version
    'CFBundlePackageType': 'APPL',
    'CFBundleSignature': '????', # Usually not needed for modern apps
    'LSApplicationCategoryType': 'public.app-category.productivity', # Added Category
    'LSMinimumSystemVersion': '11.0', # Changed back to 11.0 for universal2
    'NSHumanReadableCopyright': 'Copyright © 2023-present Craig P. Russo and CR2 Creative',
    'NSHighResolutionCapable': True,
    'NSPrincipalClass': 'NSApplication',
    'NSMainNibFile': 'MainMenu', # Standard for Cocoa apps
    'PyRuntimeLocations': [ # Help py2app find the Python framework
        '@executable_path/../Frameworks/libpython3.12.dylib', # Updated to specific Python version
        '/Library/Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib' # Updated to specific Python version
    ]
}

# --- py2app Options ---
OPTIONS = {
    'argv_emulation': False, # Pass command line args directly
    'packages': PACKAGES,
    'includes': ['sip', 'json', 'webbrowser'], # sip is needed for PyQt5, include others explicitly
    'excludes': ['unittest', 'PyQt5.QtDesigner', 'PyQt5.QtHelp', 'PyQt5.QtNetwork', 
                 'PyQt5.QtOpenGL', 'PyQt5.QtScript', 'PyQt5.QtSql', 'PyQt5.QtSvg', 
                 'PyQt5.QtTest', 'PyQt5.QtXml', 'PyQt5.QtXmlPatterns', 'PyQt5.uic',
                 # Add other PyQt modules you are SURE you don't use
                ], 
    'iconfile': 'Icons/Echelon.icns', # Path to your .icns file
    'plist': PLIST,
    'arch': 'universal2', # Build for Intel (x86_64) and Apple Silicon (arm64)
    'optimize': 2, # Basic optimization
    'strip': True, # Strip unneeded symbols
    'resources': DATA_FILES, # Use the dynamically generated DATA_FILES list
    'no_strip': False,
    'bdist_base': 'build', # Specify build directory
    'dist_dir': 'dist', # Specify distribution directory
    # Removed '--alias': True for release build
}

# --- Setup Function ---
setup(
    app=APP,
    data_files=[], # Data files are handled by 'resources' in OPTIONS now
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name='Echelon Project',
    version=app_version_full,
    author='Craig P. Russo',
    author_email='craig@cr2creative.com',
    url='https://www.cr2creative.com', # Optional: your website
)