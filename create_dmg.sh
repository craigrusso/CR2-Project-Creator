#!/bin/bash

# Variables
APP_NAME="Echelon"
DMG_NAME="Echelon-Installer"
DEVELOPER_ID="Developer ID Application: Craig Russo (V6NX986L8G)"
NOTARIZATION_PROFILE="EchelonNotaryProfile"

# Function to print headers
function print_header() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
}

# Create DMG
print_header "Creating DMG with Applications link"
mkdir -p dmg_temp
cp -r "dist/$APP_NAME.app" dmg_temp/
# Create a symbolic link to /Applications in the DMG
ln -s /Applications dmg_temp/

# Create the DMG
print_header "Creating DMG file"
hdiutil create -volname "$APP_NAME" -srcfolder dmg_temp -ov -format UDZO "$DMG_NAME.dmg"

# Sign the DMG
print_header "Signing DMG"
codesign --force --timestamp --sign "$DEVELOPER_ID" "$DMG_NAME.dmg"

# Notarize the DMG
print_header "Notarizing DMG"
xcrun notarytool submit "$DMG_NAME.dmg" --keychain-profile "$NOTARIZATION_PROFILE" --wait

# Staple the DMG
print_header "Stapling DMG"
xcrun stapler staple "$DMG_NAME.dmg"

# Clean up temporary files
rm -rf dmg_temp

print_header "DMG Creation Complete"
echo "Your DMG is located at: $(pwd)/$DMG_NAME.dmg" 