#!/bin/bash
# Script to sign all Qt plugins for notarization
# This addresses notarization failures caused by unsigned plugin dylibs

set -e

APP_PATH="MAC BUILD/dist/Echelon.app"
DEV_ID="Developer ID Application: craig russo (5926DW86QY)"
PLUGINS_PATH="$APP_PATH/Contents/Resources/lib/python3.12/PyQt5/Qt5/plugins"

echo "===== Signing Qt plugins for notarization ====="

# Sign all plugin dylibs
find "$PLUGINS_PATH" -name "*.dylib" | while read file; do
    echo "Signing plugin: $file"
    codesign --force --options=runtime --sign "$DEV_ID" "$file"
done

# Sign Qt QML plugins (from previous script)
find "$APP_PATH" -path "*/qml/*" -name "*.dylib" | while read file; do
    echo "Signing QML plugin: $file"
    codesign --force --options=runtime --sign "$DEV_ID" "$file"
done

# Re-sign the main app bundle
echo "Re-signing full app..."
codesign --force --deep --sign "$DEV_ID" --options=runtime "$APP_PATH"

echo "===== Signing complete =====
Run the app again for testing before creating the DMG." 