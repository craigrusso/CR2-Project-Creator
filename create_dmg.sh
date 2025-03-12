#!/bin/bash
# Script to create a DMG file for distribution

# Set variables
APP_NAME="CR2 Creative Pro"
APP_VERSION="2.1.0"
DMG_NAME="CR2_Creative_Pro_${APP_VERSION}.dmg"

# Ensure the app bundle exists
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "ERROR: App bundle not found at dist/${APP_NAME}.app"
    echo "Please run package_macos_app.sh first to create the app bundle."
    exit 1
fi

echo "Creating DMG file for ${APP_NAME}..."

# Create a temporary directory for DMG contents
TMP_DIR=$(mktemp -d)
echo "Creating temporary staging directory at $TMP_DIR"

# Copy the app to the temporary directory
cp -R "dist/${APP_NAME}.app" "$TMP_DIR/"

# Create a symbolic link to /Applications
echo "Creating symbolic link to Applications folder"
ln -s /Applications "$TMP_DIR/Applications"

# Use hdiutil to create the DMG from the temporary directory
echo "Creating DMG image..."
hdiutil create -volname "${APP_NAME} ${APP_VERSION}" -srcfolder "$TMP_DIR" -ov -format UDZO "${DMG_NAME}"

# Clean up
echo "Cleaning up temporary files"
rm -rf "$TMP_DIR"

echo "DMG file created at ${DMG_NAME}"
echo "You can distribute this file to install the application."
echo "Users can now drag the app to the Applications folder shortcut to install." 