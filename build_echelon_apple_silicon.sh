#!/bin/bash
# Script to build Echelon for Apple Silicon (ARM64), sign it with a developer certificate,
# create a DMG with Applications folder shortcut, and handle notarization

# Exit on error
set -e

# Check if running on Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "This script must be run on Apple Silicon (M1/M2) Mac"
    exit 1
fi

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.95"
APP_BUNDLE="$APP_NAME.app"
APP_BUNDLE_PATH="dist/$APP_BUNDLE"
DMG_NAME="$APP_NAME-$APP_VERSION.dmg"
ICNS_FILE="ICONS/$APP_NAME.icns"
ZIP_NAME="$APP_NAME.zip"
ENTRY_POINT="main.py"
ICON_FILE="assets/icons/echelon_logo.icns"

# Developer identity and notarization credentials
DEVELOPER_ID="Developer ID Application: Craig Russo (5926DW86QY)"
TEAM_ID="5926DW86QY"  # Your Team ID
APPLE_ID="craig_russo@me.com"  # Your Apple ID
APP_PASSWORD="oowc-uxos-pidi-qqli"  # Your app-specific password

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "pip3 is required but not installed. Aborting." >&2; exit 1; }
command -v pyinstaller >/dev/null 2>&1 || { echo "Installing PyInstaller..."; pip3 install pyinstaller; }

# Check for create-dmg
if ! command -v create-dmg >/dev/null 2>&1; then
    echo "Installing create-dmg..."
    brew install create-dmg
fi

# Clean previous builds
rm -rf build dist *.dmg *.zip

# Install requirements
pip3 install -r requirements.txt

# Create PyInstaller spec file
cat > "$APP_NAME.spec" << EOL
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[('ICONS/Echelon.icns', 'ICONS'),
                    ('app/assets', 'app/assets'),
                    ('app/templates', 'app/templates'),
                    ('app/ui', 'app/ui')],
             hiddenimports=['json', 'webbrowser'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['PyQt5.QtBluetooth',
                      'PyQt5.QtLocation',
                      'PyQt5.QtMultimedia',
                      'PyQt5.QtMultimediaWidgets',
                      'PyQt5.QtNfc',
                      'PyQt5.QtOpenGL',
                      'PyQt5.QtPositioning',
                      'PyQt5.QtSensors',
                      'PyQt5.QtSerialPort',
                      'PyQt5.QtWebChannel',
                      'PyQt5.QtWebEngine',
                      'PyQt5.QtWebEngineCore',
                      'PyQt5.QtWebEngineWidgets',
                      'PyQt5.QtWebKit',
                      'PyQt5.QtWebKitWidgets',
                      'PyQt5.QtWebSockets'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='$APP_NAME',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False,
          disable_windowed_traceback=False,
          target_arch='arm64',
          codesign_identity=None,
          entitlements_file=None)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='$APP_NAME')

app = BUNDLE(coll,
            name='$APP_BUNDLE',
            icon='$ICNS_FILE',
            bundle_identifier='com.echelon.app',
            version='$APP_VERSION',
            info_plist={
                'LSMinimumSystemVersion': '11.0',
                'NSHighResolutionCapable': True,
                'CFBundleShortVersionString': '$APP_VERSION',
                'CFBundleVersion': '$APP_VERSION',
                'NSRequiresAquaSystemAppearance': False,
            })
EOL

# Create entitlements file
cat > "entitlements.plist" << EOL
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
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
    <key>com.apple.security.get-task-allow</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
EOL

# Build the application
echo "Building $APP_NAME for Apple Silicon..."
pyinstaller "$APP_NAME.spec" --clean --noconfirm

# Sign the application with hardened runtime and entitlements
echo "Signing $APP_NAME.app..."
codesign --force --options runtime --deep --sign "$DEVELOPER_ID" \
    --entitlements "entitlements.plist" \
    --timestamp \
    "$APP_BUNDLE_PATH"

# Verify code signing
echo "Verifying code signature..."
codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE_PATH"

# Create a DMG
echo "Creating DMG..."
create-dmg \
    --volname "$APP_NAME" \
    --volicon "$ICNS_FILE" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "$APP_BUNDLE" 200 190 \
    --hide-extension "$APP_BUNDLE" \
    --app-drop-link 600 185 \
    "$DMG_NAME" \
    "$APP_BUNDLE_PATH"

# Sign the DMG
echo "Signing DMG..."
codesign --force --sign "$DEVELOPER_ID" --timestamp "$DMG_NAME"

# Create ZIP for notarization
echo "Creating ZIP for notarization..."
ditto -c -k --keepParent "$APP_BUNDLE_PATH" "$ZIP_NAME"

# Submit for notarization
echo "Submitting for notarization..."
xcrun notarytool submit "$ZIP_NAME" \
    --apple-id "$APPLE_ID" \
    --password "$APP_PASSWORD" \
    --team-id "$TEAM_ID" \
    --wait

# Staple the notarization ticket
echo "Stapling notarization ticket..."
xcrun stapler staple "$APP_BUNDLE_PATH"
xcrun stapler staple "$DMG_NAME"

echo "Build process complete!"
echo "Application bundle: $APP_BUNDLE_PATH"
echo "DMG file: $DMG_NAME" 