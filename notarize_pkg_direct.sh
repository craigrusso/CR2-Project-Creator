#!/bin/bash
# Script to directly notarize the PKG with provided credentials

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.094"
PKG_NAME="$APP_NAME-$APP_VERSION.pkg"
APPLE_ID="craig_russo@me.com"
TEAM_ID="5926DW86QY"
APP_PASSWORD="oowc-uxos-pidi-qqli"

# Check if the PKG exists
if [ ! -f "$PKG_NAME" ]; then
    echo "Error: $PKG_NAME does not exist!"
    exit 1
fi

echo "===== Notarizing $PKG_NAME ====="
echo "Using: $APPLE_ID / $TEAM_ID"

# Create a ZIP for notarization
echo "=== Creating ZIP for notarization ==="
ditto -c -k --keepParent "$PKG_NAME" "${PKG_NAME}.zip"

# Submit for notarization
echo "=== Submitting for notarization (this may take several minutes) ==="
xcrun notarytool submit "${PKG_NAME}.zip" \
    --apple-id "$APPLE_ID" \
    --password "$APP_PASSWORD" \
    --team-id "$TEAM_ID" \
    --wait

# Staple the notarization ticket
echo "=== Stapling notarization ticket to PKG ==="
xcrun stapler staple "$PKG_NAME"

# Verify stapling
echo "=== Verifying stapling ==="
xcrun stapler validate "$PKG_NAME"

# Clean up
rm -f "${PKG_NAME}.zip"

echo ""
echo "===== Notarization complete! ====="
echo "Your PKG is now notarized and ready for distribution: $PKG_NAME" 