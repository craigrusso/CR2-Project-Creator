#!/bin/bash
# Comprehensive script for building, signing, and notarizing Echelon for macOS
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

# Exit on any error
set -e

echo "==========================================="
echo "Echelon macOS Build & Notarization Script"
echo "==========================================="

# Configuration
APP_NAME="Echelon"
DEV_ID="Developer ID Application: craig russo (5926DW86QY)"
TEAM_ID="5926DW86QY"
BUILD_DIR="MAC BUILD/build"
DIST_DIR="MAC BUILD/dist"
APP_PATH="$DIST_DIR/$APP_NAME.app"
NOTARIZATION_ZIP="MAC BUILD/Echelon_for_notarization.zip"
DMG_PATH="MAC BUILD/EchelonInstaller.dmg"

# Clean build directories
echo "Cleaning build directories..."
mkdir -p "MAC BUILD/old_builds"
mv "MAC BUILD/build" "MAC BUILD/dist" "MAC BUILD/old_builds/$(date +%Y%m%d_%H%M%S)" 2>/dev/null || echo "No existing build/dist to move"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Build the application using py2app
echo "Building application using py2app..."
python3 setup.py py2app

# Verify app was created
if [ ! -d "$APP_PATH" ]; then
    echo "Error: App build failed, $APP_PATH not found!"
    exit 1
fi

# =====================================
# STEP 1: Remove quarantine attributes
# =====================================
echo "Removing quarantine attributes..."
xattr -cr "$APP_PATH"

# =====================================
# STEP 2: Sign all embedded binaries first
# =====================================
echo "Signing all frameworks, libraries and binaries..."

# Sign all the Qt framework and dylib files within Resources
echo "Signing Qt framework files in Resources..."
find "$APP_PATH/Contents/Resources" -type f -name "*.dylib" | while read file; do
    echo "Signing $file"
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$file"
done

# Sign all the .so files
echo "Signing Python .so files..."
find "$APP_PATH" -type f -name "*.so" | while read file; do
    echo "Signing $file"
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$file"
done

# Sign framework files
echo "Signing framework files..."
find "$APP_PATH/Contents/Frameworks" -type f -name "Qt*" | while read file; do
    echo "Signing $file"
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$file"
done

# Sign Python framework
echo "Signing Python framework..."
codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$APP_PATH/Contents/Frameworks/Python.framework/Versions/Current/Python"

# Sign plugin files
echo "Signing plugin files..."
find "$APP_PATH" -path "*/plugins/*" -type f | while read file; do
    echo "Signing $file"
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$file"
done

# Sign all QML plugins (these were mentioned in the notarization error)
echo "Signing QML plugins..."
find "$APP_PATH" -path "*/qml/*" -type f | while read file; do
    echo "Signing QML file: $file"
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$file"
done

# Sign QtWebEngineProcess separately
WEBENGINE_PROCESS=$(find "$APP_PATH" -name "QtWebEngineProcess" 2>/dev/null)
if [ -n "$WEBENGINE_PROCESS" ]; then
    echo "Signing QtWebEngineProcess..."
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$WEBENGINE_PROCESS"
fi

# Sign all executables in MacOS directory
echo "Signing executables in MacOS directory..."
find "$APP_PATH/Contents/MacOS" -type f | while read file; do
    echo "Signing $file"
    codesign --force --sign "$DEV_ID" --options=runtime --timestamp "$file"
done

# =====================================
# STEP 3: Sign the entire app
# =====================================
echo "Signing main app bundle..."
codesign --force --deep --sign "$DEV_ID" --options=runtime --timestamp "$APP_PATH"

# =====================================
# STEP 4: Check signature
# =====================================
echo "Verifying signature..."
codesign -dvv "$APP_PATH"
echo "Verifying with spctl..."
spctl --assess -vv "$APP_PATH" || echo "Note: The app may need to be notarized before this check passes"

# Run the app in the foreground for testing
echo "Running app for testing..."
open "$APP_PATH"

# Prompt user to verify the app works before proceeding
read -p "Does the app run correctly? (y/n): " app_works
if [ "$app_works" != "y" ]; then
    echo "Aborting because app doesn't run correctly. Fix issues before continuing."
    exit 1
fi

# =====================================
# STEP 5: Create DMG
# =====================================
echo "Creating DMG..."
rm -f "$DMG_PATH"
create-dmg \
    --volname "$APP_NAME Installer" \
    --window-pos 200 120 \
    --window-size 600 420 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 150 180 \
    --app-drop-link 450 180 \
    --format UDBZ \
    "$DMG_PATH" \
    "$APP_PATH"

# =====================================
# STEP 6: Sign DMG
# =====================================
echo "Signing DMG..."
codesign --force --sign "$DEV_ID" --timestamp "$DMG_PATH"

# =====================================
# STEP 7: Notarize app
# =====================================
echo "Submitting for notarization..."
echo "Creating notarization ZIP file..."
ditto -c -k --keepParent "$APP_PATH" "$NOTARIZATION_ZIP"

echo "Submitting to Apple for notarization..."
xcrun notarytool submit "$NOTARIZATION_ZIP" --keychain-profile "EchelonNotaryProfile" --wait

echo "Stapling app..."
xcrun stapler staple "$APP_PATH"

echo "Stapling DMG..."
xcrun stapler staple "$DMG_PATH"

echo "==========================================="
echo "Build process completed!"
echo "DMG installer is at: $DMG_PATH"
echo "===========================================" 