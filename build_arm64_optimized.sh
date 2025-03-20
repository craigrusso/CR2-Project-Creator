#!/bin/bash
# Script to build an optimized Echelon app for Apple Silicon (ARM64) with minimal dependencies
# Exit on error
set -e

APP_NAME="Echelon"
APP_VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from app.core.app_config import APP_VERSION; print(APP_VERSION)" 2>/dev/null || echo "0.081")
ICNS_FILE="ICONS/Echelon.icns"

echo "=== Building $APP_NAME $APP_VERSION for Apple Silicon (Optimized Size) ==="

# Check if we're on Apple Silicon
if [ "$(uname -m)" != "arm64" ]; then
    echo "WARNING: You are not running on Apple Silicon."
    echo "This script will still attempt to build, but for best results, run on an M1/M2/M3 Mac."
    echo ""
    echo "Press Enter to continue or Ctrl+C to abort..."
    read
fi

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    python3 -m pip install pyinstaller
fi

# Check for icon file
if [ ! -f "$ICNS_FILE" ]; then
    echo "Icon file $ICNS_FILE not found. Please make sure it's in the ICONS directory."
    exit 1
fi

# Clean up previous builds
echo "Cleaning previous builds..."
rm -rf build
if [ -d "dist" ]; then
    echo "Removing dist directory..."
    rm -rf dist/*
else
    mkdir -p dist
fi

# Install requirements
echo "Installing requirements..."
python3 -m pip install -r requirements.txt

# Create optimized spec file for minimal dependencies
echo "Creating optimized spec file..."
cat > echelon_optimized.spec << EOF
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Minimal required modules - explicitly including json and webbrowser as requested
REQUIRED_MODULES = [
    'json', 'webbrowser', 'http', 'urllib', 'platform', 'subprocess', 
    'shutil', 'tempfile', 'os', 'sys', 'random', 're', 'datetime', 
    'time', 'pathlib', 'glob', 'fnmatch'
]

# Only include essential PyQt5 modules that are actually used by the app
ESSENTIAL_PACKAGES = ['PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui']

hidden_imports = REQUIRED_MODULES.copy()
hidden_imports.extend(ESSENTIAL_PACKAGES)

# Add modules we know are explicitly imported
hidden_imports.extend([
    'PyQt5.QtPrintSupport',  # Needed for printing functionality
    'PyQt5.QtSvg',  # Needed for SVG template icons
])

# Exclude unnecessary Qt plugins to reduce size
qt_excludes = [
    # Exclude unnecessary plugins
    ('qmltooling', None),
    ('playlistformats', None), 
    ('sceneparsers', None),
    ('renderers', None),
    ('renderplugins', None),
    ('virtualkeyboard', None),
    ('wayland-*', None),
    ('webview', None),
    ('gamepads', None),
    ('canbus', None),
    ('xcbglintegrations', None),
    
    # Exclude modules not used by your app
    ('QtQuick3D*', None),
    ('QtLocation*', None),
    ('QtPositioning*', None),
    ('QtSensors*', None),
    ('QtWebEngine*', None),
    ('QtWebView*', None),
    ('QtWebSockets*', None),
    ('QtNfc*', None),
    ('QtTest*', None),
    ('QtBluetooth*', None),
    ('QtDesigner*', None),
    ('QtSerialPort*', None),
    ('QtSql*', None),
    ('QtTextToSpeech*', None),
    ('QtXml*', None)
]

excludes = [
    'tkinter', 'matplotlib', 'numpy', 'PIL', 'pandas', 'scipy', 'PyQt5.uic.port_v3',
    'jinja2', 'pytz', 'IPython', 'pygments', 'sphinx', 'cryptography',
    'win32com', 'win32wnet', 'win32api', 'win32con', 'OpenGL', 'OpenGL_accelerate'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('app', 'app')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    exclude_binaries=True,
)

# Ensure json module is explicitly included
a.binaries += TOC([
    ('json/__init__.py', os.path.join(sys.prefix, 'lib/python{}.{}/json/__init__.py'.format(sys.version_info.major, sys.version_info.minor)), 'DATA'),
    ('json/decoder.py', os.path.join(sys.prefix, 'lib/python{}.{}/json/decoder.py'.format(sys.version_info.major, sys.version_info.minor)), 'DATA'),
    ('json/encoder.py', os.path.join(sys.prefix, 'lib/python{}.{}/json/encoder.py'.format(sys.version_info.major, sys.version_info.minor)), 'DATA'),
    ('json/scanner.py', os.path.join(sys.prefix, 'lib/python{}.{}/json/scanner.py'.format(sys.version_info.major, sys.version_info.minor)), 'DATA')
])

# Remove unnecessary Qt modules/plugins
for qt_exclude in qt_excludes:
    module, file_filter = qt_exclude
    a.binaries = [x for x in a.binaries if not x[0].startswith(f'PyQt5/Qt5/plugins/{module}/')]
    if file_filter:
        a.binaries = [x for x in a.binaries if not x[0].endswith(file_filter)]

# Check if Qt translations are included (they're usually not needed)
a.datas = [x for x in a.datas if not x[0].startswith('PyQt5/Qt5/translations/')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='$APP_NAME',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols to reduce size
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,  # Strip debug symbols to reduce size 
    upx=True,
    upx_exclude=[],
    name='$APP_NAME',
)

app = BUNDLE(
    coll,
    name='$APP_NAME.app',
    icon='$ICNS_FILE',
    bundle_identifier='com.cr2creative.echelon',
    info_plist={
        'CFBundleShortVersionString': '$APP_VERSION',
        'CFBundleVersion': '$APP_VERSION',
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'NSHumanReadableCopyright': 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.',
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
        'LSMinimumSystemVersion': '11.0.0',
        'LSRequiresNativeExecution': True,
        'NSAppleEventsUsageDescription': 'This app needs access to send Apple Events to display dialogs and handle file operations.',
        'LSArchitecturePriority': ['arm64']
    }
)
EOF

# Create entitlements file if it doesn't exist
if [ ! -f "entitlements.plist" ]; then
    echo "Creating entitlements file..."
    cat > entitlements.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <false/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
EOF
fi

# Install UPX for additional compression if not already available
if ! command -v upx &> /dev/null; then
    echo "UPX not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install upx
    else
        echo "Homebrew not found. Please install UPX manually for better compression."
    fi
fi

# Build the application for Apple Silicon using our custom spec file
echo "Building the application for Apple Silicon using optimized spec file..."
pyinstaller --clean echelon_optimized.spec

# Sign the application with the developer certificate from keychain
echo "Signing the application with developer identity from keychain..."
# Get the first Developer ID Application certificate from keychain
CERT_ID=$(security find-identity -p codesigning -v | grep "Developer ID Application" | head -1 | awk -F '"' '{print $2}')

if [ -z "$CERT_ID" ]; then
    echo "No Developer ID Application certificate found in keychain."
    echo "Please specify the identity to use for signing (e.g., 'Developer ID Application: Your Name (TEAMID)'):"
    read CERT_ID
    
    if [ -z "$CERT_ID" ]; then
        echo "No certificate specified. Skipping signing."
        exit 1
    fi
fi

echo "Using certificate: $CERT_ID"

# Sign the application
echo "Signing the application..."
codesign --force --options runtime --entitlements entitlements.plist --deep --sign "$CERT_ID" "dist/$APP_NAME.app"

# Verify the signature
echo "Verifying signature..."
codesign -vvv --deep --strict "dist/$APP_NAME.app"

echo "=== Build Complete ==="
echo "Application bundle: dist/$APP_NAME.app"
echo ""
echo "Testing the app now..."
echo "---------------------"
echo "Running from Terminal to show any errors:"
./dist/"$APP_NAME.app/Contents/MacOS/$APP_NAME" || LAST_EXIT_CODE=$?

if [ -n "$LAST_EXIT_CODE" ]; then
    echo "App exited with error code $LAST_EXIT_CODE"
    # Only try to open the app if it doesn't seem to crash immediately
    if [ $LAST_EXIT_CODE -ne 1 ] && [ $LAST_EXIT_CODE -ne 139 ] && [ $LAST_EXIT_CODE -ne 134 ]; then
        echo "---------------------"
        echo ""
        echo "Attempting to open the app to test the UI:"
        open "dist/$APP_NAME.app"
    else
        echo "App seems to be crashing, not attempting to open UI."
    fi
else
    echo "App seems to have launched successfully in Terminal mode."
    echo "---------------------"
    echo ""
    echo "Opening the app to test the UI:"
    open "dist/$APP_NAME.app"
fi

echo ""
echo "If the app is working correctly, you can create a zip file for distribution:"
echo "ditto -c -k --keepParent dist/$APP_NAME.app dist/${APP_NAME// /_}_${APP_VERSION}_arm64.zip" 