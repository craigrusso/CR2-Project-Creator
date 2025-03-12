#!/bin/bash
# Script to package the Python app as a macOS app bundle using PyInstaller

# Ensure the script exits if any command fails
set -e

# Get the current architecture
CURRENT_ARCH=$(uname -m)
echo "Current system architecture: $CURRENT_ARCH"

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf build dist

# Install PyInstaller and PyQt5
echo "Installing PyInstaller and PyQt5..."
python3 -m pip install --upgrade pip
python3 -m pip install PyInstaller PyQt5

# Install any other project dependencies
echo "Installing project dependencies..."
python3 -m pip install -r requirements.txt

# Create a simple PyInstaller spec file
echo "Creating PyInstaller spec file..."
cat > CR2_Creative_Pro.spec << EOF
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('app', 'app')],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CR2 Creative Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Creator.icns',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CR2 Creative Pro',
)
app = BUNDLE(
    coll,
    name='CR2 Creative Pro.app',
    icon='Creator.icns',
    bundle_identifier='com.cr2creative.projectcreator',
    version='2.1.0',
    info_plist={
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'CFBundleShortVersionString': '2.1.0',
        'CFBundleVersion': '2.1.0',
        'NSHumanReadableCopyright': 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.',
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
    },
)
EOF

# Run PyInstaller to build the app
echo "Building app bundle with PyInstaller..."
python3 -m PyInstaller CR2_Creative_Pro.spec

# Verify the app bundle
APP_DIR="dist/CR2 Creative Pro.app"
if [ -d "$APP_DIR" ]; then
    echo "----------------------------------------"
    echo "App bundle created successfully at $APP_DIR"
    
    # Verify PyQt5 is included - check multiple locations
    PYQT_FOUND=false
    for PYQT_LOCATION in "$APP_DIR/Contents/MacOS/PyQt5" "$APP_DIR/Contents/Resources/PyQt5" "$APP_DIR/Contents/Frameworks/PyQt5"; do
        if [ -d "$PYQT_LOCATION" ]; then
            echo "PyQt5 found at: $PYQT_LOCATION ✅"
            PYQT_FOUND=true
        fi
    done
    
    if [ "$PYQT_FOUND" = false ]; then
        echo "WARNING: PyQt5 may not be properly included in the app bundle ❌"
    fi
    
    # Show the Python executable architecture
    PYTHON_PATH=$(find "$APP_DIR" -name "python" -type f -o -name "python3" -type f | head -1)
    if [ -n "$PYTHON_PATH" ]; then
        echo "Python executable: $PYTHON_PATH"
        echo "Python architecture: $(file "$PYTHON_PATH" | grep -o "x86_64\|arm64" || echo "unknown")"
    fi
    
    echo "----------------------------------------"
    echo "App bundle created at $APP_DIR"
    echo "You can now run the app by double-clicking it in Finder"
    echo "This is a self-contained app bundle that includes Python and all dependencies."
    echo "No separate installation of Python or PyQt5 is required."
else
    echo "ERROR: App bundle was not created successfully. Check the build output for errors."
    exit 1
fi 