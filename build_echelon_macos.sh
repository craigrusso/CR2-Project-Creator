#!/bin/bash
# Script to build a macOS app bundle for Echelon specifically optimized for Apple Silicon
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

# Ensure the script exits if any command fails
set -e

echo "=== Echelon macOS App Builder ==="

# Get the current architecture and ensure we're building for Apple Silicon
CURRENT_ARCH=$(uname -m)
echo "Current system architecture: $CURRENT_ARCH"

if [ "$CURRENT_ARCH" != "arm64" ]; then
    echo "⚠️  Warning: Building on non-Apple Silicon machine."
    echo "   The build will produce an app optimized for your current architecture."
fi

# Set variables
APP_NAME="Echelon"
APP_VERSION="0.081"
DMG_NAME="${APP_NAME}_${APP_VERSION}_AppleSilicon.dmg"

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf build dist

# Install required packages
echo "Installing required packages..."
python3 -m pip install --upgrade pip
python3 -m pip install PyInstaller PyQt5

# Install any other project dependencies
echo "Installing project dependencies..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo "No requirements.txt found. Continuing without installing dependencies."
fi

# Create a PyInstaller spec file for Apple Silicon
echo "Creating PyInstaller spec file for Apple Silicon..."
cat > "${APP_NAME}.spec" << EOF
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
    name='${APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,  # Let PyInstaller use the native architecture
    codesign_identity=None,
    entitlements_file=None,
    icon='Echelon.icns',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='${APP_NAME}',
)
app = BUNDLE(
    coll,
    name='${APP_NAME}.app',
    icon='Echelon.icns',
    bundle_identifier='com.cr2creative.echelon',
    version='${APP_VERSION}',
    info_plist={
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'CFBundleShortVersionString': '${APP_VERSION}',
        'CFBundleVersion': '${APP_VERSION}',
        'NSHumanReadableCopyright': 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.',
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
    },
)
EOF

# Run PyInstaller to build the app for Apple Silicon
echo "Building app bundle with PyInstaller targeting Apple Silicon..."
python3 -m PyInstaller "${APP_NAME}.spec"

# Verify the app bundle
APP_DIR="dist/${APP_NAME}.app"
if [ -d "$APP_DIR" ]; then
    echo "----------------------------------------"
    echo "✅ App bundle created successfully at $APP_DIR"
    
    # Verify PyQt5 is included
    PYQT_FOUND=false
    for PYQT_LOCATION in "$APP_DIR/Contents/MacOS/PyQt5" "$APP_DIR/Contents/Resources/PyQt5" "$APP_DIR/Contents/Frameworks/PyQt5"; do
        if [ -d "$PYQT_LOCATION" ]; then
            echo "✅ PyQt5 found at: $PYQT_LOCATION"
            PYQT_FOUND=true
        fi
    done
    
    if [ "$PYQT_FOUND" = false ]; then
        echo "⚠️  WARNING: PyQt5 may not be properly included in the app bundle"
    fi
    
    # Show the Python executable architecture
    PYTHON_PATH=$(find "$APP_DIR" -name "python" -type f -o -name "python3" -type f | head -1)
    if [ -n "$PYTHON_PATH" ]; then
        echo "Python executable: $PYTHON_PATH"
        ARCH=$(file "$PYTHON_PATH" | grep -o "x86_64\|arm64\|universal binary" || echo "unknown")
        echo "Python architecture: $ARCH"
        if [[ "$ARCH" == *"arm64"* ]]; then
            echo "✅ App bundle includes Apple Silicon (ARM64) support"
        else
            echo "⚠️  WARNING: App bundle may not support Apple Silicon natively"
        fi
    fi
    
    # Create a DMG with Applications folder shortcut
    echo "----------------------------------------"
    echo "Creating DMG file with Applications folder shortcut..."
    
    # Create a temporary directory for DMG contents
    TMP_DIR=$(mktemp -d)
    echo "Creating temporary staging directory at $TMP_DIR"
    
    # Copy the app to the temporary directory
    cp -R "$APP_DIR" "$TMP_DIR/"
    
    # Create a symbolic link to /Applications
    echo "Creating symbolic link to Applications folder"
    ln -s /Applications "$TMP_DIR/Applications"
    
    # Create a background image directory
    mkdir -p "$TMP_DIR/.background"
    
    # Optional: Create a simple background image (could be improved with a proper background)
    # Use any existing background image if available
    
    # Use hdiutil to create the DMG from the temporary directory
    echo "Creating DMG image..."
    hdiutil create -volname "${APP_NAME} ${APP_VERSION}" -srcfolder "$TMP_DIR" -ov -format UDZO "${DMG_NAME}"
    
    # Clean up
    echo "Cleaning up temporary files"
    rm -rf "$TMP_DIR"
    
    echo "----------------------------------------"
    echo "✅ DMG file created at ${DMG_NAME}"
    echo "You can distribute this file to install the application."
    echo "Users can drag the app to the Applications folder shortcut to install."
    echo "Current directory is: $(pwd)"
    ls -la "${DMG_NAME}"
else
    echo "❌ ERROR: App bundle was not created successfully. Check the build output for errors."
    exit 1
fi 