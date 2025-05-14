#!/bin/bash
# Comprehensive build script for Echelon macOS application
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

# Exit on any error
set -e

echo "=========================================="
echo "Echelon macOS Build Script (Universal Binary)"
echo "Build, Sign, Notarize, and Package"
echo "=========================================="

# Configuration
APP_NAME="Echelon"
DEV_ID="Developer ID Application: craig russo (5926DW86QY)"
TEAM_ID="5926DW86QY"
BUILD_DIR="MAC BUILD/build"
DIST_DIR="MAC BUILD/dist"
APP_PATH="$DIST_DIR/$APP_NAME.app"
NOTARIZATION_ZIP="MAC BUILD/Echelon_for_notarization.zip"
DMG_PATH="MAC BUILD/EchelonInstaller.dmg"
KEYCHAIN_PROFILE="EchelonNotaryProfile"

# Step 1: Build Number has been incremented in app/constants.py and app/config/app_config.py

# Step 2: Clean previous build directories
echo "Step 2: Cleaning previous build directories..."
mkdir -p "MAC BUILD/old_builds" 
mv "MAC BUILD/build" "MAC BUILD/dist" "MAC BUILD/old_builds/" 2>/dev/null || echo 'No existing build/dist to move'
mkdir -p "$BUILD_DIR" "$DIST_DIR"
rm -f "$NOTARIZATION_ZIP" "$DMG_PATH"

# Step 3: Build the app with py2app (setup.py has all the necessary configuration)
echo "Step 3: Building the app with py2app..."
python3 setup.py py2app

# Check if build was successful
if [ ! -d "$APP_PATH" ]; then
    echo "Build failed! Application not found at $APP_PATH"
    exit 1
fi

echo "Build completed. App bundle size:"
du -sh "$APP_PATH"

# Step 4: Sign all individual components in the app bundle
echo "Step 4: Signing all individual components..."
find "$APP_PATH" -type f -name "*.so" -o -name "*.dylib" -o -path "*/MacOS/*" | while read file; do
    echo "Signing $file"
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$file"
done

# Step 5: Sign the main app bundle
echo "Step 5: Signing the main app bundle..."
codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$APP_PATH"

# Step 6: Update app modification time (for icon)
echo "Step 6: Updating app modification time..."
touch "$APP_PATH"

# Step 7: Verify signature
echo "Step 7: Verifying signature..."
echo "Detailed signature verification:"
codesign -dv --verbose=4 "$APP_PATH"
echo "Security assessment verification:"
spctl --assess -vv "$APP_PATH"

# Step 8: Create zip for notarization
echo "Step 8: Creating zip for notarization..."
rm -f "$NOTARIZATION_ZIP"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$NOTARIZATION_ZIP"

# Step 9: Submit app for notarization
echo "Step 9: Submitting app for notarization..."
xcrun notarytool submit "$NOTARIZATION_ZIP" --keychain-profile "$KEYCHAIN_PROFILE" --wait

# Step 10: Staple the app
echo "Step 10: Stapling the app..."
xcrun stapler staple "$APP_PATH"
echo "Verifying stapling:"
stapler validate "$APP_PATH"

# Step 11: Create DMG
echo "Step 11: Creating DMG..."
rm -f "$DMG_PATH"
create-dmg \
  --volname "Echelon Installer" \
  --window-pos 200 120 \
  --window-size 600 420 \
  --icon-size 100 \
  --icon "$APP_NAME.app" 150 180 \
  --app-drop-link 450 180 \
  --format UDBZ \
  "$DMG_PATH" \
  "$APP_PATH"

# Check if DMG creation was successful
if [ ! -f "$DMG_PATH" ]; then
    echo "DMG creation failed! DMG not found at $DMG_PATH"
    exit 1
fi

# Step 12: Sign the DMG
echo "Step 12: Signing the DMG..."
codesign --force --sign "$DEV_ID" --timestamp "$DMG_PATH"

# Step 13: Notarize the DMG
echo "Step 13: Notarizing the DMG..."
xcrun notarytool submit "$DMG_PATH" --keychain-profile "$KEYCHAIN_PROFILE" --wait

# Step 14: Staple the DMG
echo "Step 14: Stapling the DMG..."
xcrun stapler staple "$DMG_PATH"

# Step 15: Final verification
echo "Step 15: Final verification of DMG..."
spctl --assess -vv "$DMG_PATH"

# Done
echo "=========================================="
echo "Build process completed successfully!"
echo "App location: $APP_PATH"
echo "DMG location: $DMG_PATH"
echo "App build number: $(grep APP_BUILD_NUMBER app/constants.py | awk '{print $3}')"
echo "==========================================" 