#!/bin/bash
# Build script for Echelon Apple Silicon package
# Creates a DMG with Applications shortcut

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from app.core.app_config import APP_VERSION; print(APP_VERSION)" 2>/dev/null || echo "2.1.0")
DMG_NAME="${APP_NAME}_${APP_VERSION}_AppleSilicon"

# Paths
ICON_PATH="ICONS/Echelon.icns"

echo "=== Building $APP_NAME $APP_VERSION for Apple Silicon ==="

# Check if we're on Apple Silicon
if [ "$(uname -m)" != "arm64" ]; then
    echo "WARNING: You are not running on Apple Silicon."
    echo "This script will still attempt to build, but for best results, run on an M1/M2/M3 Mac."
    echo ""
    echo "Press Enter to continue or Ctrl+C to abort..."
    read
fi

# Check for required tools
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    python3 -m pip install pyinstaller
fi

if ! command -v create-dmg &> /dev/null; then
    echo "create-dmg not found. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first (https://brew.sh)"
        exit 1
    fi
    brew install create-dmg
fi

# Check for icon
if [ ! -f "$ICON_PATH" ]; then
    echo "Error: Icon file not found at $ICON_PATH"
    exit 1
fi

# Clean up previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Install requirements
echo "Installing requirements..."
python3 -m pip install -r requirements.txt

# Step 1: Build the application for Apple Silicon only
echo "Building the application for Apple Silicon..."
pyinstaller --target-architecture arm64 --clean --windowed \
    --icon="$ICON_PATH" \
    --name="$APP_NAME" \
    --osx-bundle-identifier="com.cr2creative.echelon" \
    --add-data="app:app" \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    main.py

# Step 2: Modify Info.plist for high-resolution display
echo "Updating Info.plist..."
PLIST_PATH="dist/$APP_NAME.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :NSPrincipalClass string NSApplication" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSPrincipalClass NSApplication" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.'" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSHumanReadableCopyright 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.'" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $APP_VERSION" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $APP_VERSION" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :LSApplicationCategoryType string 'public.app-category.developer-tools'" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :LSApplicationCategoryType 'public.app-category.developer-tools'" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 11.0.0" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion 11.0.0" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :LSArchitecturePriority array" "$PLIST_PATH" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :LSArchitecturePriority:0 string arm64" "$PLIST_PATH" 2>/dev/null || true

# Step 3: Create DMG with Applications folder shortcut
echo "=== Creating DMG ==="
echo "Creating DMG with Applications folder shortcut..."
create-dmg \
  --volname "$APP_NAME $APP_VERSION" \
  --volicon "$ICON_PATH" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "$APP_NAME.app" 200 190 \
  --hide-extension "$APP_NAME.app" \
  --app-drop-link 600 185 \
  --no-internet-enable \
  "dist/$DMG_NAME.dmg" \
  "dist/$APP_NAME.app" || {
    echo "Standard DMG creation failed. Trying simpler method..."
    create-dmg \
      --volname "$APP_NAME $APP_VERSION" \
      --volicon "$ICON_PATH" \
      --no-internet-enable \
      "dist/$DMG_NAME.dmg" \
      "dist/$APP_NAME.app"
  }

echo "=== Build Complete ==="
echo "Application bundle: dist/$APP_NAME.app"
echo "DMG package: dist/$DMG_NAME.dmg"
echo ""
echo "The DMG includes a shortcut to the Applications folder."
echo "To install, open the DMG and drag the app to the Applications shortcut."
echo "NOTE: The application and DMG are not signed."
echo "To sign them, use the sign_app.sh script." 