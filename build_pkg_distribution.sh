#!/bin/bash
# Script to build a PKG installer for distribution outside the Mac App Store

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.094"  # Update this to match your current version
APP_BUNDLE="dist/$APP_NAME.app"
PKG_NAME="$APP_NAME-$APP_VERSION.pkg"
DEVELOPER_ID="Developer ID Application: craig russo (5926DW86QY)"

# Check if the app exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: $APP_BUNDLE does not exist!"
    echo "Please build the app first using ./build_echelon_apple_silicon.sh"
    exit 1
fi

echo "===== Building Distribution Package for $APP_NAME $APP_VERSION ====="

# Step 1: Create a distribution entitlements file
echo "=== Creating entitlements file ==="
cat > "developer_id_entitlements.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
EOL

# Step 2: Sign the app with Developer ID
echo "=== Signing app with Developer ID ==="
codesign --force --options runtime --deep --sign "$DEVELOPER_ID" \
    --entitlements "developer_id_entitlements.plist" \
    --timestamp \
    "$APP_BUNDLE"

# Verify code signing
echo "Verifying code signature..."
codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"

# Step 3: Create PKG installer without signing
echo "=== Creating PKG installer (unsigned) ==="
# Create a simplified distribution package without signing
productbuild --component "$APP_BUNDLE" /Applications "$PKG_NAME"

echo "PKG file created: $PKG_NAME"

# Step 4: Notarize the package
echo ""
read -p "Do you want to notarize the package now? (yes/no): " NOTARIZE_NOW

if [[ "$NOTARIZE_NOW" == "yes" ]]; then
    echo "=== Notarizing package ==="
    # Apple ID credentials
    APPLE_ID="craig_russo@me.com"
    TEAM_ID="5926DW86QY"
    
    # Prompt for app-specific password as it's sensitive
    read -s -p "Enter your app-specific password: " APP_PASSWORD
    echo ""
    
    # Create temporary ZIP for notarization
    echo "Creating ZIP for notarization..."
    ditto -c -k --keepParent "$PKG_NAME" "${PKG_NAME}.zip"
    
    # Submit for notarization
    echo "Submitting for notarization (this may take several minutes)..."
    xcrun notarytool submit "${PKG_NAME}.zip" \
        --apple-id "$APPLE_ID" \
        --password "$APP_PASSWORD" \
        --team-id "$TEAM_ID" \
        --wait
    
    # Staple the notarization ticket
    echo "Stapling notarization ticket to package..."
    xcrun stapler staple "$PKG_NAME"
    
    # Verify stapling
    echo "Verifying stapling..."
    xcrun stapler validate "$PKG_NAME"
    
    # Clean up
    rm -f "${PKG_NAME}.zip"
    
    echo "Notarization complete!"
else
    echo "Skipping notarization. To notarize later, use:"
    echo "ditto -c -k --keepParent \"$PKG_NAME\" \"${PKG_NAME}.zip\""
    echo "xcrun notarytool submit \"${PKG_NAME}.zip\" --apple-id \"$APPLE_ID\" --team-id \"$TEAM_ID\" --wait"
    echo "xcrun stapler staple \"$PKG_NAME\""
fi

echo ""
echo "=== Distribution package preparation complete! ==="
echo "Your package is ready at: $PKG_NAME"
echo ""
echo "Note: This PKG is unsigned because you need a Developer ID Installer certificate to sign PKGs."
echo "To obtain this certificate, go to https://developer.apple.com/account/resources/certificates/add"
echo "and create a 'Developer ID Installer' certificate."
echo ""
echo "Users can install this package by right-clicking it and selecting Open." 