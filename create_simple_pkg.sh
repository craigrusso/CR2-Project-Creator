#!/bin/bash
# Script to create a simple PKG installer without resigning

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

echo "===== Creating simple PKG for $APP_NAME $APP_VERSION ====="

# Create a simple distribution package without signing
echo "=== Creating PKG installer (unsigned) ==="
productbuild --component "$APP_BUNDLE" /Applications "$PKG_NAME"

echo "PKG file created: $PKG_NAME"
echo ""
echo "This is an unsigned PKG. Users can install it by right-clicking and selecting Open." 