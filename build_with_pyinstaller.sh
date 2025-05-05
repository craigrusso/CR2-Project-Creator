#!/bin/bash
# PyInstaller build script for Echelon
# Creates a smaller, optimized macOS app bundle

# Move to the MAC BUILD directory
cd "$(dirname "$0")/MAC BUILD" || mkdir -p "$(dirname "$0")/MAC BUILD" && cd "$(dirname "$0")/MAC BUILD"
echo "Working directory: $(pwd)"

# Variables
APP_NAME="Echelon"
DMG_NAME="Echelon-Installer"
# Use the correct developer ID
DEVELOPER_ID="Developer ID Application: craig russo (5926DW86QY)"
NOTARIZATION_PROFILE="EchelonNotaryProfile"

# Function to print headers
function print_header() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
}

print_header "Using certificate: $DEVELOPER_ID"

# Clean previous builds
print_header "Cleaning previous builds"
rm -rf build dist

# Make sure required packages are installed
print_header "Installing/Updating required packages"
pip3 install -U pyinstaller

# Create a spec file for PyInstaller
print_header "Creating optimized spec file"
cat > echelon.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../app/assets', 'app/assets'),
        ('../ICONS', 'ICONS'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',
        'json',
        'webbrowser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy', 'scipy', 'matplotlib', 'pandas', 'PIL', 'tkinter',
        'unittest', 'test', 'pydoc', 'doctest', 'pdb', 'difflib',
        # Exclude unnecessary PyQt5 modules
        'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineCore', 'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets', 'PyQt5.QtQml',
        'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtBluetooth', 'PyQt5.QtSensors', 'PyQt5.QtSerialPort',
        'PyQt5.QtDesigner', 'PyQt5.QtHelp', 'PyQt5.QtLocation',
        'PyQt5.QtNfc', 'PyQt5.QtPositioning', 'PyQt5.QtSvg',
        'PyQt5.QtTest', 'PyQt5.QtWebChannel', 'PyQt5.QtXml',
        'PyQt5.QtXmlPatterns', 'PyQt5.QtSql'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Echelon',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../ICONS/Echelon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='Echelon',
)

app = BUNDLE(
    coll,
    name='Echelon.app',
    icon='../ICONS/Echelon.icns',
    bundle_identifier='com.echelon.app',
    info_plist={
        'CFBundleName': 'Echelon',
        'CFBundleDisplayName': 'Echelon',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': '© 2023 Echelon',
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
    },
)
EOF

# Build the application
print_header "Building application with PyInstaller"
pyinstaller --clean --noconfirm echelon.spec

# Verify the app exists before continuing
if [ ! -d "dist/$APP_NAME.app" ]; then
    print_header "ERROR: App bundle was not created"
    exit 1
fi

# Sign all the binaries
print_header "Signing all binaries"
function sign_binary() {
    local binary="$1"
    
    # Check if the file is a Mach-O binary or dylib
    if file "$binary" | grep -q "Mach-O"; then
        echo "Signing: $binary"
        
        # Remove quarantine attribute if present
        xattr -d com.apple.quarantine "$binary" 2>/dev/null || true
        
        # Sign with hardened runtime and timestamp
        codesign --force --options runtime --timestamp --verbose --sign "$DEVELOPER_ID" "$binary"
    fi
}

cd "dist/$APP_NAME.app/Contents"

# Sign all .dylib files recursively
find . -name "*.dylib" -type f | while read -r dylib; do
    sign_binary "$dylib"
done

# Sign all .so files recursively
find . -name "*.so" -type f | while read -r so_file; do
    sign_binary "$so_file"
done

# Sign all binaries in MacOS folder
find MacOS -type f 2>/dev/null | while read -r binary; do
    sign_binary "$binary"
done

# Sign any other executables
find . -type f -perm +111 2>/dev/null | while read -r binary; do
    sign_binary "$binary"
done

# Sign the main app bundle
print_header "Signing the application bundle"
cd ../.. # Return to dist directory
codesign --force --options runtime --timestamp --verbose --sign "$DEVELOPER_ID" "$APP_NAME.app"

# Verify the signature
print_header "Verifying code signature"
codesign --verify --verbose "$APP_NAME.app"

# Run the app from command line to see any errors
print_header "Testing the app from command line"
echo "Running app to catch any errors..."
cd "$APP_NAME.app/Contents/MacOS"
./$APP_NAME > ../../../app_log.txt 2>&1 &
APP_PID=$!
sleep 5

# Check if the app is running
if ps -p $APP_PID > /dev/null; then
    echo "App is running correctly. Continuing..."
    echo "Log file created at: $(pwd)/../../../app_log.txt"
    # Kill the app after a few seconds
    sleep 3
    kill $APP_PID 2>/dev/null || true
else
    echo "WARNING: App may not have started correctly. Check the log file:"
    cat ../../../app_log.txt
    # Continue anyway
fi

cd ../../.. # Return to dist directory

# Create a ZIP archive for notarization
print_header "Creating ZIP archive for notarization"
ditto -c -k --keepParent "$APP_NAME.app" "$APP_NAME.zip"

# Submit the app for notarization
print_header "Submitting app for notarization"
SUBMISSION_ID=$(xcrun notarytool submit "$APP_NAME.zip" --keychain-profile "$NOTARIZATION_PROFILE" --wait --output-format json | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/"id"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/')
echo "Notarization Submission ID: $SUBMISSION_ID"

# Check notarization status
print_header "Checking notarization status"
if [ -z "$SUBMISSION_ID" ]; then
    print_header "ERROR: Failed to get submission ID"
    exit 1
fi

NOTARIZATION_STATUS=$(xcrun notarytool info "$SUBMISSION_ID" --keychain-profile "$NOTARIZATION_PROFILE" | grep "status" | awk '{print $2}')
echo "Notarization status: $NOTARIZATION_STATUS"

if [ "$NOTARIZATION_STATUS" != "Accepted" ]; then
    print_header "ERROR: Notarization failed. Getting log..."
    xcrun notarytool log "$SUBMISSION_ID" --keychain-profile "$NOTARIZATION_PROFILE"
    exit 1
fi

# Staple the notarization ticket to the app
print_header "Stapling notarization ticket to the app"
xcrun stapler staple "$APP_NAME.app"

# Verify the stapling
xcrun stapler validate "$APP_NAME.app"

# Run the app again to verify it works after notarization
print_header "Testing the notarized app from command line"
cd "$APP_NAME.app/Contents/MacOS"
./$APP_NAME > ../../../app_log_notarized.txt 2>&1 &
APP_PID=$!
sleep 5

# Check if the app is running
if ps -p $APP_PID > /dev/null; then
    echo "Notarized app is running correctly. Continuing with DMG creation..."
    echo "Log file created at: $(pwd)/../../../app_log_notarized.txt"
    # Kill the app after a few seconds
    sleep 3
    kill $APP_PID 2>/dev/null || true
else
    echo "WARNING: Notarized app may not have started correctly. Check the log file:"
    cat ../../../app_log_notarized.txt
    # Continue anyway
fi

cd ../../.. # Return to dist directory

# Create DMG only after app is successfully notarized and stapled
print_header "Creating DMG with Applications link"
mkdir -p dmg_temp
cp -r "$APP_NAME.app" dmg_temp/
# Create a symbolic link to /Applications in the DMG
ln -s /Applications dmg_temp/

# Create the DMG
print_header "Creating DMG file"
hdiutil create -volname "$APP_NAME" -srcfolder dmg_temp -ov -format UDZO "$DMG_NAME.dmg"

# Sign the DMG
print_header "Signing DMG"
codesign --force --timestamp --sign "$DEVELOPER_ID" "$DMG_NAME.dmg"

# Clean up temporary files
rm -rf dmg_temp

print_header "Build Completed"
echo "The app is located at: $(pwd)/$APP_NAME.app"
echo "The DMG is located at: $(pwd)/$DMG_NAME.dmg"
echo "App size: $(du -sh $APP_NAME.app | cut -f1)" 