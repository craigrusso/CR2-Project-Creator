#!/bin/bash
# Script to properly sign all QML dylibs in a PyQt5 application
# This addresses notarization failures caused by unsigned QML plugins

set -e

APP_PATH="MAC BUILD/dist/Echelon.app"
DEV_ID="Developer ID Application: craig russo (5926DW86QY)"

echo "===== Signing QML dylibs for notarization ====="

# Try to sign with timestamp first, but if it fails, try without
find "$APP_PATH" -path "*/qml/*" -name "*.dylib" | while read file; do
    echo "Signing QML dylib: $file"
    codesign --force --options=runtime --sign "$DEV_ID" "$file"
done

# Main app signature
echo "Re-signing full app..."
codesign --force --deep --sign "$DEV_ID" --options=runtime "$APP_PATH"

echo "===== Signing complete =====" 