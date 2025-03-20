#!/bin/bash
# Script to build Echelon for Apple Silicon (ARM64) and sign it with a developer certificate
# This script creates ONLY the .app package, no DMG, for later notarization

# Exit on error
set -e

APP_NAME="Echelon"
APP_VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from app.constants import APP_VERSION; print(APP_VERSION)" 2>/dev/null || echo "0.081")
ICNS_FILE="ICONS/Echelon.icns"

echo "=== Building $APP_NAME $APP_VERSION for Apple Silicon ==="

# Check if we're on Apple Silicon
if [ "$(uname -m)" != "arm64" ]; then
    echo "WARNING: You are not running on Apple Silicon."
    echo "This script will still attempt to build, but for best results, run on an M1/M2/M3 Mac."
    echo ""
    echo "Press Enter to continue or Ctrl+C to abort..."
    read
fi

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    python3 -m pip install pyinstaller
fi

# Check for icon file
if [ ! -f "$ICNS_FILE" ]; then
    echo "Icon file $ICNS_FILE not found. Please make sure it's in the ICONS directory."
    exit 1
fi

# Clean up previous builds
echo "Cleaning previous builds..."
rm -rf build
if [ -d "dist" ]; then
    echo "Removing dist directory..."
    rm -rf dist/*
else
    mkdir -p dist
fi

# Install requirements
echo "Installing requirements..."
python3 -m pip install -r requirements.txt

# Build the application for Apple Silicon only using our custom spec file
echo "Building the application for Apple Silicon using custom spec file..."
pyinstaller --clean Echelon_custom.spec

# Sign the application with the developer certificate from keychain
echo "Signing the application with developer identity from keychain..."
# Get the first Developer ID Application certificate from keychain
CERT_ID=$(security find-identity -p codesigning -v | grep "Developer ID Application" | head -1 | awk -F '"' '{print $2}')

if [ -z "$CERT_ID" ]; then
    echo "No Developer ID Application certificate found in keychain."
    echo "Please specify the identity to use for signing (e.g., 'Developer ID Application: Your Name (TEAMID)'):"
    read CERT_ID
    
    if [ -z "$CERT_ID" ]; then
        echo "No certificate specified. Skipping signing."
        exit 1
    fi
fi

echo "Using certificate: $CERT_ID"

# Create entitlements file if it doesn't exist
if [ ! -f "entitlements.plist" ]; then
    cat > entitlements.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <false/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
EOF
fi

# Sign the application
echo "Signing the application..."
codesign --force --options runtime --entitlements entitlements.plist --deep --sign "$CERT_ID" "dist/$APP_NAME.app"

# Verify the signature
echo "Verifying signature..."
codesign -vvv --deep --strict "dist/$APP_NAME.app"

echo "=== Build Complete ==="
echo "Application bundle: dist/$APP_NAME.app"
echo ""
echo "Testing the app now..."
echo "---------------------"
echo "Running from Terminal to show any errors:"
./dist/$APP_NAME.app/Contents/MacOS/$APP_NAME || LAST_EXIT_CODE=$?
if [ -n "$LAST_EXIT_CODE" ]; then
    echo "App exited with error code $LAST_EXIT_CODE"
    # Only try to open the app if it doesn't seem to crash immediately
    if [ $LAST_EXIT_CODE -ne 1 ] && [ $LAST_EXIT_CODE -ne 139 ] && [ $LAST_EXIT_CODE -ne 134 ]; then
        echo "---------------------"
        echo ""
        echo "Attempting to open the app to test the UI:"
        open dist/$APP_NAME.app
    else
        echo "App seems to be crashing, not attempting to open UI."
    fi
else
    echo "App seems to have launched successfully in Terminal mode."
    echo "---------------------"
    echo ""
    echo "Opening the app to test the UI:"
    open dist/$APP_NAME.app
fi

echo ""
echo "If the app is working correctly, you can create a zip file for notarization:"
echo "ditto -c -k --keepParent dist/$APP_NAME.app dist/${APP_NAME}_${APP_VERSION}_arm64.zip" 