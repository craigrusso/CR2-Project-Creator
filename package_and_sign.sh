#!/bin/bash
# Script to package and sign Echelon.app

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.081"
DMG_NAME="${APP_NAME}_${APP_VERSION}_AppleSilicon"
BUNDLE_ID="com.cr2creative.echelon"
TEAM_ID="5926DW86QY"
DEVELOPER_ID="Developer ID Application: craig russo (5926DW86QY)"
APPLE_ID="craig_russo@me.com"
APP_PASSWORD="oowc-uxos-pidi-qqli"

# Directory paths
APP_PATH="dist/Echelon/Echelon.app"
DMG_PATH="dist/${DMG_NAME}.dmg"
TEMP_DMG_DIR="tmp_dmg"
BG_IMAGE="ICONS/Echelon_DMG_BG.png"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH does not exist!"
    exit 1
fi

echo "===== Packaging and Signing $APP_NAME $APP_VERSION ====="

# Step 1: Remove extended attributes that might cause signing issues
echo "=== Removing extended attributes ==="
xattr -cr "$APP_PATH"

# Step 2: Sign the app with entitlements
echo "=== Signing Application ==="
echo "Signing application bundle..."

# Sign all executable files inside the app bundle
find "$APP_PATH" -type f -name "*.so" -o -name "*.dylib" | while read file; do
    echo "Signing $file"
    codesign --force --options runtime --sign "$DEVELOPER_ID" "$file"
done

# Then sign the main bundle
codesign --deep --force --options runtime --sign "$DEVELOPER_ID" "$APP_PATH"

echo "Verifying application signature..."
codesign -vvv --deep --strict "$APP_PATH" || true

# Step 3: Prepare for DMG creation
echo "=== Preparing DMG creation ==="
rm -rf "$TEMP_DMG_DIR"
mkdir -p "$TEMP_DMG_DIR"

# Copy the app to the temporary directory
cp -R "$APP_PATH" "$TEMP_DMG_DIR/"

# Create a symbolic link to /Applications folder
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# Step 4: Create DMG with background
echo "=== Creating DMG with background ==="

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "The 'create-dmg' tool is not installed. Installing..."
    brew install create-dmg
fi

# Remove existing DMG if it exists
if [ -f "$DMG_PATH" ]; then
    rm "$DMG_PATH"
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

# Step 5: Sign the DMG
echo "=== Signing DMG ==="
codesign --force --sign "$DEVELOPER_ID" "$DMG_PATH"
echo "Verifying DMG signature..."
codesign -vvv "$DMG_PATH"

# Step 6: Notarize and staple the DMG
echo "=== Notarizing DMG ==="
echo "This may take several minutes..."

# Create a temporary ZIP of the DMG for notarization
TEMP_ZIP="dist/${DMG_NAME}.zip"
ditto -c -k --keepParent "$DMG_PATH" "$TEMP_ZIP"

# Submit for notarization
echo "Submitting to Apple notarization service..."
xcrun notarytool submit "$TEMP_ZIP" \
    --apple-id "$APPLE_ID" \
    --password "$APP_PASSWORD" \
    --team-id "$TEAM_ID" \
    --wait

# Staple the notarization ticket to the DMG
echo "=== Stapling notarization ticket to DMG ==="
xcrun stapler staple "$DMG_PATH"

# Verify stapling
echo "=== Verifying stapling ==="
xcrun stapler validate "$DMG_PATH"

# Cleanup
echo "=== Cleaning up ==="
rm -f "$TEMP_ZIP"
rm -rf "$TEMP_DMG_DIR"

echo ""
echo "=== Process complete! ==="
echo "Your app has been signed, packaged in a DMG with background,"
echo "and the DMG has been signed, notarized, and stapled."
echo ""
echo "Final DMG location: $DMG_PATH" 