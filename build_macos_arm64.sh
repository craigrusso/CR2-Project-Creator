#!/bin/bash
# Script to build Echelon for Apple Silicon (ARM64)

# Exit on error
set -e

echo "=== Building Echelon macOS App Bundle for Apple Silicon ==="
echo "Checking architecture..."

# Check if we're on Apple Silicon
if [ "$(uname -m)" != "arm64" ]; then
    echo "WARNING: You are not running on Apple Silicon."
    echo "This script will still attempt to build, but the result may not be optimized for M1/M2/M3 Macs."
    echo "For best results, run this script on an Apple Silicon Mac."
    echo ""
    echo "Press Enter to continue or Ctrl+C to abort..."
    read
fi

# Get the app name from constants.py
APP_NAME=$(python3 -c "import sys; sys.path.insert(0, '.'); from app.constants import APP_NAME; print(APP_NAME)")
echo "Building app: $APP_NAME"

# Create a clean build environment
echo "Cleaning previous builds..."
rm -rf build dist

# Ensure we have the latest pip and setuptools
echo "Updating pip and setuptools..."
python3 -m pip install --upgrade pip setuptools wheel

# Install requirements
echo "Installing requirements..."
python3 -m pip install -r requirements.txt

# Install py2app
echo "Installing py2app..."
python3 -m pip install py2app

# Build the application
echo "Building the application..."
python3 setup.py py2app

echo "=== Build Complete ==="
echo "The application bundle is located at: dist/${APP_NAME}.app"
echo ""
echo "To create a DMG for distribution:"
echo "1. Open Disk Utility"
echo "2. File > New Image > Blank Image"
echo "3. Set a name (e.g., '${APP_NAME}')"
echo "4. Select a destination folder"
echo "5. Set size to at least 200MB"
echo "6. Format: Mac OS Extended (Journaled)"
echo "7. Partition: Single Partition - GUID Partition Map"
echo "8. Image Format: read/write disk image"
echo "9. Create the image"
echo "10. Copy the .app from dist/ to the mounted disk image"
echo "11. Eject the disk image"
echo "12. In Disk Utility, select the .dmg file and choose Images > Convert"
echo "13. Save the final .dmg with a new name"
echo ""
echo "Or use create-dmg tool: https://github.com/create-dmg/create-dmg" 