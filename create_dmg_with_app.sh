#!/bin/bash
# Script to create a DMG with background image for the Echelon app

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.081"
DMG_NAME="${APP_NAME}_${APP_VERSION}_AppleSilicon"
APP_PATH="dist/Echelon/Echelon.app"
DMG_PATH="dist/${DMG_NAME}.dmg"
TEMP_DMG_DIR="tmp_dmg"
BG_IMAGE="ICONS/Echelon_DMG_BG.png"
DEVELOPER_ID="Developer ID Application: craig russo (5926DW86QY)"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH does not exist!"
    exit 1
fi

echo "===== Creating DMG for $APP_NAME $APP_VERSION ====="

# Step 1: Clean up existing files
echo "=== Cleaning up existing files ==="
rm -rf "$TEMP_DMG_DIR"
mkdir -p "$TEMP_DMG_DIR"
[ -f "$DMG_PATH" ] && rm "$DMG_PATH"

# Step 2: Prepare files for DMG
echo "=== Preparing DMG contents ==="
# Copy the app to the temporary directory
cp -R "$APP_PATH" "$TEMP_DMG_DIR/"

# Create a symbolic link to /Applications folder
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# Step 3: Create DMG with background
echo "=== Creating DMG with background ==="

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "The 'create-dmg' tool is not installed. Installing..."
    brew install create-dmg
fi

# Create DMG with background
create-dmg \
  --volname "$APP_NAME" \
  --background "$BG_IMAGE" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 128 \
  --icon "$APP_NAME.app" 200 190 \
  --hide-extension "$APP_NAME.app" \
  --app-drop-link 600 190 \
  --no-internet-enable \
  "$DMG_PATH" \
  "$TEMP_DMG_DIR" || {
    echo "Failed to create DMG with background. Creating without background..."
    create-dmg \
      --volname "$APP_NAME" \
      --window-pos 200 120 \
      --window-size 600 400 \
      --icon-size 128 \
      --icon "$APP_NAME.app" 200 190 \
      --hide-extension "$APP_NAME.app" \
      --app-drop-link 400 190 \
      --no-internet-enable \
      "$DMG_PATH" \
      "$TEMP_DMG_DIR"
  }

# Step 4: Sign the DMG
echo "=== Signing DMG ==="
codesign --force --sign "$DEVELOPER_ID" "$DMG_PATH"
echo "Verifying DMG signature..."
codesign -vvv "$DMG_PATH"

# Cleanup
echo "=== Cleaning up ==="
rm -rf "$TEMP_DMG_DIR"

echo ""
echo "=== Process complete! ==="
echo "DMG location: $DMG_PATH"
echo ""
echo "To notarize the DMG, run the following commands manually:"
echo "xcrun notarytool submit \"$DMG_PATH\" --apple-id \"craig_russo@me.com\" --password \"oowc-uxos-pidi-qqli\" --team-id \"5926DW86QY\" --wait"
echo "xcrun stapler staple \"$DMG_PATH\"" 