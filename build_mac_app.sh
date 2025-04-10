#!/bin/bash
# Build script for creating macOS application bundle for Echelon

# Variables
APP_NAME="Echelon"
DMG_NAME="Echelon-Installer"
BUNDLE_ID="com.echelon.app"
DEVELOPER_ID="Developer ID Application: Craig Russo (V6NX986L8G)"
NOTARIZATION_PROFILE="EchelonNotaryProfile"
ENTITLEMENTS="echelon.entitlements"
BACKGROUND_IMAGE="../ICONS/Echelon.png" # Set to your background image path

# Print a section header
function print_header() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
}

# Clean previous builds
print_header "Cleaning previous builds"
rm -rf build dist

# Make sure required packages are installed
print_header "Ensuring required packages are installed"
pip3 install -U py2app

# Build the application bundle
print_header "Building application bundle"
python3 setup.py py2app

# Sign the helper binaries, frameworks and dylibs
function sign_binary() {
    local binary="$1"
    
    # Check if the file is a Mach-O binary or dylib
    if file "$binary" | grep -q "Mach-O"; then
        echo "Signing: $binary"
        
        # Remove quarantine attribute if present
        xattr -d com.apple.quarantine "$binary" 2>/dev/null || true
        
        # Sign with hardened runtime and timestamp
        codesign --force --options runtime --timestamp --verbose --sign "$DEVELOPER_ID" "$binary"
        
        if [ $? -ne 0 ]; then
            echo "Warning: Failed to sign $binary"
        fi
    fi
}

print_header "Signing all frameworks and binaries"
echo "This may take a few minutes..."

# Sign all dylibs and framework executables recursively
cd "dist/$APP_NAME.app/Contents"

# First, sign all .dylib files recursively
find . -name "*.dylib" -type f | while read -r dylib; do
    sign_binary "$dylib"
done

# Sign all .so files recursively
find . -name "*.so" -type f | while read -r so_file; do
    sign_binary "$so_file"
done

# Sign all binaries in MacOS folder
find ./MacOS -type f | while read -r binary; do
    sign_binary "$binary"
done

# Sign Python.framework binaries
find ./Frameworks -name "Python*" -type f | while read -r binary; do
    sign_binary "$binary"
done

# Sign all libraries in lib-dynload
find ./Resources/lib/python3.12/lib-dynload -type f | while read -r binary; do
    sign_binary "$binary"
done

# Sign any executable files in Resources
find ./Resources -type f -perm +111 | while read -r binary; do
    sign_binary "$binary"
done

# Sign the main app bundle
print_header "Signing the application bundle"
cd ../.. # Return to dist directory
codesign --force --options runtime --timestamp --entitlements "$ENTITLEMENTS" --verbose --sign "$DEVELOPER_ID" "$APP_NAME.app"

# Verify the signature
print_header "Verifying code signature"
codesign --verify --verbose "$APP_NAME.app"

# Create a ZIP archive for notarization
print_header "Creating ZIP archive for notarization"
ditto -c -k --keepParent "$APP_NAME.app" "$APP_NAME.zip"

# Submit the app for notarization
print_header "Submitting app for notarization"
xcrun notarytool submit "$APP_NAME.zip" --keychain-profile "$NOTARIZATION_PROFILE" --wait

# Staple the notarization ticket to the app
print_header "Stapling notarization ticket to the app"
xcrun stapler staple "$APP_NAME.app"

# Verify the stapling
xcrun stapler validate "$APP_NAME.app"

# Create DMG (optional but recommended)
print_header "Creating DMG with background and Applications link"
mkdir -p dmg_temp
cp -r "$APP_NAME.app" dmg_temp/
# Create a symbolic link to /Applications in the DMG
ln -s /Applications dmg_temp/

# Create the DMG
hdiutil create -volname "$APP_NAME" -srcfolder dmg_temp -ov -format UDZO "$DMG_NAME.dmg"

# Sign the DMG
codesign --force --timestamp --sign "$DEVELOPER_ID" "$DMG_NAME.dmg"

# Notarize the DMG
xcrun notarytool submit "$DMG_NAME.dmg" --keychain-profile "$NOTARIZATION_PROFILE" --wait

# Staple the DMG
xcrun stapler staple "$DMG_NAME.dmg"

# Clean up temporary files
rm -rf dmg_temp
rm -f "$APP_NAME.zip"

print_header "Build Completed!"
echo "The DMG is located at: dist/$DMG_NAME.dmg" 