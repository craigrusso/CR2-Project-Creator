#!/bin/bash
# Script to build final PKG from current app

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.094"
APP_BUNDLE="dist/$APP_NAME.app"
PKG_NAME="$APP_NAME-$APP_VERSION.pkg"

# Check if the app exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: $APP_BUNDLE does not exist!"
    echo "Please build the app first using ./build_echelon_apple_silicon.sh"
    exit 1
fi

echo "===== Building Final PKG for $APP_NAME $APP_VERSION ====="

# Create the PKG from the current app
echo "=== Creating PKG from current app ==="

# Add a custom background image and welcome message
mkdir -p resources
# Create a Distribution XML file with welcome message
cat > resources/distribution.xml << EOL
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>$APP_NAME $APP_VERSION</title>
    <organization>CR2 Creative</organization>
    <domains enable_anywhere="true" enable_currentUserHome="true" enable_localSystem="true"/>
    <options customize="never" require-scripts="false" rootVolumeOnly="true"/>
    <welcome file="welcome.html"/>
    <license file="license.txt"/>
    <allowed-os-versions>
        <os-version min="11.0"/>
    </allowed-os-versions>
    <pkg-ref id="com.cr2creative.echelon"/>
    <choices-outline>
        <line choice="default">
            <line choice="com.cr2creative.echelon"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.cr2creative.echelon" visible="false">
        <pkg-ref id="com.cr2creative.echelon"/>
    </choice>
    <pkg-ref id="com.cr2creative.echelon" version="$APP_VERSION" onConclusion="none">component.pkg</pkg-ref>
</installer-gui-script>
EOL

# Create welcome.html
cat > resources/welcome.html << EOL
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to $APP_NAME</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            padding: 10px 20px;
            color: #333;
        }
        h1 {
            color: #333;
        }
    </style>
</head>
<body>
    <h1>Welcome to $APP_NAME $APP_VERSION</h1>
    <p>
        Thank you for downloading $APP_NAME, a powerful project creator tool by CR2 Creative.
    </p>
    <p>
        This installer will guide you through the installation of $APP_NAME on your computer.
        Click "Continue" to proceed.
    </p>
    <p>
        &copy; 2025 CR2 Creative. All rights reserved.
    </p>
</body>
</html>
EOL

# Create license.txt
cat > resources/license.txt << EOL
END USER LICENSE AGREEMENT

IMPORTANT: PLEASE READ THIS LICENSE CAREFULLY BEFORE USING THIS SOFTWARE.

1. LICENSE

This End-User License Agreement ("EULA") is a legal agreement between you (either an individual or a single entity) and CR2 Creative regarding the use of the $APP_NAME software. By installing, copying, or otherwise using the $APP_NAME software, you agree to be bound by the terms of this EULA.

2. COPYRIGHT

The $APP_NAME software is protected by copyright laws and international copyright treaties, as well as other intellectual property laws and treaties. The $APP_NAME software is licensed, not sold.

3. GRANT OF LICENSE

CR2 Creative grants you a non-exclusive, non-transferable license to use the $APP_NAME software on a single computer.

4. DISCLAIMER OF WARRANTY

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

5. LIMITATION OF LIABILITY

IN NO EVENT SHALL CR2 CREATIVE BE LIABLE FOR ANY DAMAGES (INCLUDING, WITHOUT LIMITATION, LOST PROFITS, BUSINESS INTERRUPTION, OR LOST INFORMATION) ARISING OUT OF THE USE OF OR INABILITY TO USE THE $APP_NAME SOFTWARE.

© 2025 CR2 Creative
EOL

# Create a component package first
pkgbuild --root "$(dirname "$APP_BUNDLE")" \
    --install-location /Applications \
    --identifier "com.cr2creative.echelon" \
    --version "$APP_VERSION" \
    --filter "\.DS_Store" \
    --filter "\.git" \
    "resources/component.pkg"

# Create a distribution package with the component
productbuild --distribution "resources/distribution.xml" \
    --resources "resources" \
    --package-path "resources" \
    "$PKG_NAME"

# Clean up temporary files
rm -rf resources

echo "PKG file created: $PKG_NAME"
echo ""
echo "This PKG includes a custom welcome message and license agreement."
echo "Users can install it by double-clicking."
echo ""
echo "Note: This PKG is not signed. To distribute outside the App Store,"
echo "you would need a 'Developer ID Installer' certificate for signing." 