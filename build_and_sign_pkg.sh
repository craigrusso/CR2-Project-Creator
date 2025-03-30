#!/bin/bash
# Script to build PKG from current app and sign with distribution certificate

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.094"
APP_BUNDLE="dist/$APP_NAME.app"
PKG_NAME="$APP_NAME-$APP_VERSION.pkg"
DISTRIBUTION_CERT="Apple Distribution: craig russo (5926DW86QY)"

# Check if the app exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: $APP_BUNDLE does not exist!"
    echo "Please build the app first using ./build_echelon_apple_silicon.sh"
    exit 1
fi

echo "===== Building and Signing PKG for $APP_NAME $APP_VERSION ====="

# Step 1: Create the PKG from the current app
echo "=== Creating PKG from current app ==="
productbuild --component "$APP_BUNDLE" /Applications "${PKG_NAME}.unsigned"

echo "Unsigned PKG created: ${PKG_NAME}.unsigned"

# Step 2: Sign the PKG with the distribution certificate
echo "=== Signing PKG with distribution certificate ==="
productsign --sign "$DISTRIBUTION_CERT" "${PKG_NAME}.unsigned" "$PKG_NAME"

# Remove the unsigned PKG
rm "${PKG_NAME}.unsigned"

echo "Signed PKG created: $PKG_NAME"
echo ""
echo "PKG has been created and signed with: $DISTRIBUTION_CERT"
echo ""

# Ask if user wants to notarize the PKG
read -p "Do you want to notarize the PKG now? (yes/no): " NOTARIZE_NOW

if [[ "$NOTARIZE_NOW" == "yes" ]]; then
    # Notarization parameters
    APPLE_ID="craig_russo@me.com"
    TEAM_ID="5926DW86QY"
    APP_PASSWORD="oowc-uxos-pidi-qqli"
    
    echo "=== Notarizing PKG ==="
    # Create a ZIP for notarization
    ditto -c -k --keepParent "$PKG_NAME" "${PKG_NAME}.zip"
    
    # Submit for notarization
    echo "Submitting for notarization (this may take several minutes)..."
    xcrun notarytool submit "${PKG_NAME}.zip" \
        --apple-id "$APPLE_ID" \
        --password "$APP_PASSWORD" \
        --team-id "$TEAM_ID" \
        --wait
    
    # Staple the notarization ticket
    echo "Stapling notarization ticket..."
    xcrun stapler staple "$PKG_NAME"
    
    # Clean up
    rm -f "${PKG_NAME}.zip"
    
    echo "Notarization complete!"
else
    echo "Skipping notarization. You can notarize later with ./notarize_pkg.sh"
fi

echo ""
echo "===== Process complete! ====="
echo "Your PKG is ready at: $PKG_NAME" 