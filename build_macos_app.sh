#!/bin/bash
# Script to build a macOS app bundle using py2app

# Ensure the script exits if any command fails
set -e

echo "=== CR2 Creative Pro macOS App Builder ==="
echo "Building macOS app bundle using py2app..."

# Check if py2app is installed
if ! pip3 show py2app > /dev/null 2>&1; then
    echo "Installing py2app..."
    pip3 install py2app
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Copy the Creator.icns file to be used
echo "Using Creator.icns as app icon..."

# Build the app bundle in alias mode for testing
if [ "$1" == "--alias" ]; then
    echo "Building app bundle in alias mode (for development)..."
    python3 setup.py py2app -A
    echo "App bundle created in alias mode at dist/CR2\ Creative\ Pro.app"
    echo "This is a development version that links to your source files."
# Build the app bundle for distribution
else
    echo "Building app bundle for distribution..."
    python3 setup.py py2app
    echo "App bundle created at dist/CR2\ Creative\ Pro.app"
    echo "This is a standalone version that can be distributed."
    
    # Optional: Create a DMG for distribution
    if [ "$1" == "--dmg" ]; then
        echo "Creating DMG file..."
        DMG_NAME="CR2_Creative_Pro_2.1.0.dmg"
        hdiutil create -volname "CR2 Creative Pro" -srcfolder "dist/CR2 Creative Pro.app" -ov -format UDZO "$DMG_NAME"
        echo "DMG created: $DMG_NAME"
    fi
fi

echo "Build process completed!"
echo "You can run the app by double-clicking it in Finder." 