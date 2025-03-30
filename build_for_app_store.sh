#!/bin/bash
# Script to build a PKG installer for the Mac App Store

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.094"  # Update this to match your current version
APP_BUNDLE="dist/$APP_NAME.app"
PKG_NAME="$APP_NAME-$APP_VERSION.pkg"
BUNDLE_ID="com.cr2creative.echelon"
TEAM_ID="5926DW86QY"
APPLE_ID="craig_russo@me.com"
APP_PASSWORD="oowc-uxos-pidi-qqli"
DISTRIBUTION_CERT="Apple Distribution: craig russo (5926DW86QY)"

# Check if the app exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: $APP_BUNDLE does not exist!"
    echo "Please build the app first using ./build_echelon_apple_silicon.sh"
    exit 1
fi

echo "===== Building Mac App Store Package for $APP_NAME $APP_VERSION ====="
echo "Using Apple ID: $APPLE_ID"
echo "Using certificate: $DISTRIBUTION_CERT"

# Step 1: Re-sign the app specifically for Mac App Store
echo "=== Re-signing app for Mac App Store ==="

# Create a distribution entitlements file for App Store
cat > "app_store_entitlements.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
EOL

# Sign with Distribution certificate
codesign --force --options runtime --deep --sign "$DISTRIBUTION_CERT" \
    --entitlements "app_store_entitlements.plist" \
    --timestamp \
    "$APP_BUNDLE"

# Verify code signing
echo "Verifying code signature..."
codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"

# Step 2: Create PKG installer for Mac App Store
echo "=== Creating PKG for Mac App Store ==="
# Create an unsigned PKG since we don't have a Mac Installer Distribution certificate
productbuild --component "$APP_BUNDLE" /Applications \
    --product "$APP_BUNDLE/Contents/Info.plist" \
    "$PKG_NAME"

echo "PKG file created: $PKG_NAME"

# Step 3: Validate the PKG
echo "=== Validating PKG for Mac App Store ==="
xcrun altool --validate-app -f "$PKG_NAME" -t osx -u "$APPLE_ID" -p "$APP_PASSWORD"

# Step 4: Submit to App Store (optional)
echo ""
read -p "Do you want to submit the package to the App Store now? (yes/no): " SUBMIT_NOW

if [[ "$SUBMIT_NOW" == "yes" ]]; then
    echo "=== Submitting to Mac App Store ==="
    xcrun altool --upload-app -f "$PKG_NAME" -t osx -u "$APPLE_ID" -p "$APP_PASSWORD"
    echo "Submission complete. Check App Store Connect for status."
else
    echo "Not submitting to Mac App Store. You can submit later with:"
    echo "xcrun altool --upload-app -f \"$PKG_NAME\" -t osx -u \"$APPLE_ID\" -p YOUR_APP_PASSWORD"
fi

echo ""
echo "=== Mac App Store package preparation complete! ==="
echo "Your package is ready at: $PKG_NAME"
echo ""
echo "Note: This PKG is unsigned for the installer because you don't have a Mac Installer Distribution certificate."
echo "Apple may reject the submission if they require a signed installer."
echo ""
echo "Next steps:"
echo "1. If you didn't submit now, upload the package to App Store Connect using altool"
echo "2. Complete the app listing details in App Store Connect"
echo "3. Submit for review" 