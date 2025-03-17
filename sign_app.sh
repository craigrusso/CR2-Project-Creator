#!/bin/bash
# Script to sign the Echelon app and DMG

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from app.core.app_config import APP_VERSION; print(APP_VERSION)" 2>/dev/null || echo "2.1.0")
DMG_NAME="${APP_NAME}_${APP_VERSION}_AppleSilicon"

# Certificate identity
CERT_ID="Developer ID Application: craig russo (5926DW86QY)"

# Check if app exists
if [ ! -d "dist/$APP_NAME.app" ]; then
    echo "Error: Application not found at dist/$APP_NAME.app"
    echo "Please run build_echelon_arm64_signed.sh first"
    exit 1
fi

echo "=== Signing Application ==="
echo "Signing application bundle..."
codesign --deep --force --options runtime --sign "$CERT_ID" "dist/$APP_NAME.app"

echo "Verifying application signature..."
codesign -vvv --deep --strict "dist/$APP_NAME.app"

# Check if DMG exists
if [ -f "dist/$DMG_NAME.dmg" ]; then
    echo "=== Signing DMG ==="
    echo "Signing the DMG..."
    codesign --force --sign "$CERT_ID" "dist/$DMG_NAME.dmg"
    
    echo "Verifying DMG signature..."
    codesign -vvv "dist/$DMG_NAME.dmg"
fi

echo "=== Signing Complete ===" 