#!/bin/bash
# Build and notarize macOS script for Echelon app using py2app
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

set -e  # Exit on error

# CONFIG VARIABLES
APP_NAME="Echelon"
# py2app places the app directly in the specified dist_dir
APP_PATH="MAC BUILD/dist/Echelon.app"
DMG_NAME="EchelonInstaller.dmg"
DMG_PATH="MAC BUILD/${DMG_NAME}"
KEYCHAIN_PROFILE="EchelonNotaryProfile"
DEV_ID="Developer ID Application: craig russo (5926DW86QY)"
TEAM_ID="5926DW86QY"
BG_IMAGE="Icons/Echelon_DMG_BG_dark.png"
DMG_SIZE="300m" # Increased slightly for universal binary
BUNDLE_ID="com.cr2creative.echelon"
BUILD_DIR="MAC BUILD/build"
DIST_DIR="MAC BUILD/dist"

# Ensure working directory is the project root
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"

# Create build directory if it doesn't exist
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# Clean previous builds if they exist
echo "Cleaning previous builds..."
sudo rm -rf "$BUILD_DIR" "$DIST_DIR" "MAC BUILD/Echelon.zip" "$DMG_PATH"

# Build the app with py2app
echo "Building Echelon with py2app..."
python3 setup.py py2app

# Check if build was successful
if [ ! -d "$APP_PATH" ]; then
    echo "Build failed! Application not found at $APP_PATH"
    exit 1
fi

echo "Build completed successfully. App size:"
du -sh "$APP_PATH"

# Sign the application (py2app already signs based on setup.py, but let's ensure runtime option)
echo "Applying additional signing options (runtime)..."
codesign --force --options runtime --timestamp --sign "$DEV_ID" "$APP_PATH"

# Verify signature
echo "Verifying signature..."
codesign --verify --verbose "$APP_PATH"
spctl --assess --type execute "$APP_PATH"

# --- Run the app directly to test ---
echo "Attempting to run the application directly in foreground..."
"$APP_PATH/Contents/MacOS/$APP_NAME"
echo "Application finished running or failed to launch."

# --- Exit after running for testing purposes ---
echo "Exiting script after test run."
exit 0

# Create a zip file for notarization
echo "Creating zip file for notarization..."
cd "$DIST_DIR"
zip -r "../Echelon.zip" "$(basename "$APP_PATH")"
cd ..

# Submit for notarization
echo "Submitting for notarization..."
xcrun notarytool submit "Echelon.zip" --keychain-profile "$KEYCHAIN_PROFILE" --wait

# Staple the notarization ticket
echo "Stapling the notarization ticket to the app..."
xcrun stapler staple "$APP_PATH"

# Verify stapling
echo "Verifying stapling..."
stapler validate "$APP_PATH"

# --- Create DMG --- 
echo "Creating DMG..."
rm -f "$DMG_PATH" # Remove existing DMG if any

create-dmg \
  --volname "$APP_NAME" \
  --volicon "Icons/Echelon.icns" \
  --background "$BG_IMAGE" \
  --window-pos 200 120 \
  --window-size 600 380 \
  --icon-size 100 \
  --text-size 14 \
  --icon "Echelon.app" 150 190 \
  --hide-extension "Echelon.app" \
  --app-drop-link 450 190 \
  --no-internet-enable \
  --format UDBZ \
  "$DMG_PATH" \
  "$APP_PATH"
  
# Adjust DMG settings to ensure white text if create-dmg fails
# The 'create-dmg' tool is preferred as it handles appearance automatically.
# This fallback with hdiutil is less reliable for appearance settings.
if [ $? -ne 0 ]; then
    echo "create-dmg failed, attempting with hdiutil..."
    
    TMP_DMG_DIR=$(mktemp -d)
    cp -R "$APP_PATH" "$TMP_DMG_DIR/"
    ln -s /Applications "$TMP_DMG_DIR/Applications"
    
    hdiutil create -volname "$APP_NAME" -srcfolder "$TMP_DMG_DIR" -ov -format UDBZ "$DMG_PATH"
    rm -rf "$TMP_DMG_DIR"
fi


echo "DMG created at $DMG_PATH"

# Sign the DMG
echo "Signing the DMG..."
codesign --force --sign "$DEV_ID" "$DMG_PATH"

# Notarize the DMG
echo "Notarizing the DMG..."
xcrun notarytool submit "$DMG_PATH" --keychain-profile "$KEYCHAIN_PROFILE" --wait

# Staple the DMG
echo "Stapling the DMG..."
xcrun stapler staple "$DMG_PATH"

# Verify DMG
echo "Verifying DMG signature and notarization..."
codesign --verify --verbose "$DMG_PATH"
spctl --assess --verbose=4 "$DMG_PATH"

echo "py2app Build, sign, and notarization process complete!"
echo "App available at: $APP_PATH"
echo "DMG available at: $DMG_PATH"