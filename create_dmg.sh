#!/bin/bash
# Script to create a DMG for Echelon

# Exit on error
set -e

# Get the app name from constants.py
APP_NAME=$(python3 -c "import sys; sys.path.insert(0, '.'); from app.constants import APP_NAME; print(APP_NAME)")
APP_VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from app.constants import APP_VERSION; print(APP_VERSION)")

echo "=== Creating DMG for $APP_NAME $APP_VERSION ==="

# Check if the app bundle exists
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "Error: Application bundle not found at dist/${APP_NAME}.app"
    echo "Please run build_macos_arm64.sh first"
    exit 1
fi

# Determine architecture
ARCH=$(uname -m)
DMG_NAME="${APP_NAME}-${APP_VERSION}-${ARCH}"

echo "Creating DMG: $DMG_NAME.dmg"

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "The 'create-dmg' tool is not installed."
    echo "Would you like to install it via Homebrew? (y/n)"
    read answer
    if [ "$answer" != "${answer#[Yy]}" ]; then
        echo "Installing create-dmg..."
        if ! command -v brew &> /dev/null; then
            echo "Homebrew is required but not installed."
            echo "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
        brew install create-dmg
    else
        echo "Please install create-dmg manually:"
        echo "brew install create-dmg"
        echo "Or follow the manual DMG creation steps in build_macos_arm64.sh"
        exit 1
    fi
fi

# Check for DMG background image
BACKGROUND_IMAGE="app/assets/dmg-background.png"
if [ ! -f "$BACKGROUND_IMAGE" ]; then
    echo "DMG background image not found. Creating a simple DMG without background."
    
    # Create a simple DMG without background
    create-dmg \
      --volname "$APP_NAME" \
      --volicon "app/assets/icon.icns" \
      --window-pos 200 120 \
      --window-size 600 400 \
      --icon-size 100 \
      --icon "${APP_NAME}.app" 200 190 \
      --app-drop-link 400 185 \
      --no-internet-enable \
      "dist/${DMG_NAME}.dmg" \
      "dist/${APP_NAME}.app"
else
    # Create DMG with background
    echo "Creating DMG with background image..."
    create-dmg \
      --volname "$APP_NAME" \
      --volicon "app/assets/icon.icns" \
      --background "$BACKGROUND_IMAGE" \
      --window-pos 200 120 \
      --window-size 800 400 \
      --icon-size 100 \
      --icon "${APP_NAME}.app" 200 190 \
      --hide-extension "${APP_NAME}.app" \
      --app-drop-link 600 185 \
      --no-internet-enable \
      "dist/${DMG_NAME}.dmg" \
      "dist/${APP_NAME}.app"
fi

# Check if there was an error during DMG creation
if [ $? -ne 0 ]; then
    echo "Failed to create DMG. Trying simpler DMG creation..."
    
    # Create a very simple DMG as fallback
    create-dmg \
      --volname "$APP_NAME" \
      --no-internet-enable \
      "dist/${DMG_NAME}.dmg" \
      "dist/${APP_NAME}.app"
fi

echo "=== DMG Creation Complete ==="
echo "DMG file created at: dist/${DMG_NAME}.dmg" 