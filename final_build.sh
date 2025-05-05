#!/bin/bash
# Final build script for Echelon - Builds directly into MAC BUILD/dist

# Define base directory (project root)
BASE_DIR=$(pwd)
echo "Project base directory: $BASE_DIR"

# Define target build directories
BUILD_DIR="$BASE_DIR/MAC BUILD/build"
DIST_DIR="$BASE_DIR/MAC BUILD/dist"

# Create directories if they don't exist
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"
echo "Using build directory: $BUILD_DIR"
echo "Using dist directory: $DIST_DIR"

# Variables
APP_NAME="Echelon"
DMG_NAME="Echelon-Installer"
APP_PATH="$DIST_DIR/$APP_NAME.app"
ZIP_PATH="$DIST_DIR/$APP_NAME.zip"
DMG_PATH="$DIST_DIR/$DMG_NAME.dmg"
SPEC_FILE="fix_app.spec" # Assumes spec file is in the base directory

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

# Clean previous builds within MAC BUILD
print_header "Cleaning previous builds in MAC BUILD"
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# Build the application with PyInstaller directly into MAC BUILD/dist
print_header "Building application with PyInstaller"
pyinstaller --clean --noconfirm \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR" \
    "$SPEC_FILE"

# Test if app was created
if [ ! -d "$APP_PATH" ]; then
    print_header "ERROR: App bundle was not created at $APP_PATH"
    exit 1
fi
print_header "App bundle created at $APP_PATH"

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
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to sign $binary"
            # Optionally exit on signing failure
            # exit 1
        fi
    fi
}

cd "$APP_PATH/Contents"

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

cd "$BASE_DIR" # Return to base directory

# Sign the main app bundle
print_header "Signing the application bundle"
codesign --force --options runtime --timestamp --verbose --sign "$DEVELOPER_ID" "$APP_PATH"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to sign the main app bundle $APP_PATH"
    exit 1
fi

# Verify the signature
print_header "Verifying code signature"
codesign --verify --verbose "$APP_PATH"
if [ $? -ne 0 ]; then
    echo "ERROR: Code signature verification failed for $APP_PATH"
    exit 1
fi

# Test the app from command line
print_header "Testing the app"
MACOS_DIR="$APP_PATH/Contents/MacOS"
APP_EXECUTABLE="$MACOS_DIR/$APP_NAME"
LOG_FILE="$DIST_DIR/app_output.log"
echo "Running app to capture errors ($APP_EXECUTABLE)..."
rm -f "$LOG_FILE" # Clear previous log

# Run in background and capture PID
"$APP_EXECUTABLE" > "$LOG_FILE" 2>&1 &
APP_PID=$!
sleep 5

# Check if app is running
if ps -p $APP_PID > /dev/null; then
    print_header "App process ($APP_PID) is running. Assuming success."
    echo "Log file created at: $LOG_FILE"
    # Kill the app after a few seconds
    sleep 3
    kill $APP_PID 2>/dev/null || true
else
    print_header "ERROR: App process ($APP_PID) failed to start or terminated quickly. Check log:"
    cat "$LOG_FILE"
    exit 1 # Exit if the app test fails
fi

# Create a ZIP archive for notarization
print_header "Creating ZIP archive for notarization"
cd "$DIST_DIR"
ditto -c -k --keepParent "$APP_NAME.app" "$APP_NAME.zip"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create ZIP archive $APP_NAME.zip"
    cd "$BASE_DIR"
    exit 1
fi
cd "$BASE_DIR"

# Submit the app for notarization
print_header "Submitting app for notarization"
SUBMISSION_OUTPUT=$(xcrun notarytool submit "$ZIP_PATH" --keychain-profile "$NOTARIZATION_PROFILE" --wait --output-format json)
if [ $? -ne 0 ]; then
    echo "ERROR: notarytool submit command failed."
    echo "Output: $SUBMISSION_OUTPUT"
    exit 1
fi

SUBMISSION_ID=$(echo "$SUBMISSION_OUTPUT" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/"id"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/')
SUBMISSION_STATUS=$(echo "$SUBMISSION_OUTPUT" | grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/"status"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/')

echo "Notarization Submission ID: $SUBMISSION_ID"
echo "Notarization Submission Status: $SUBMISSION_STATUS"

if [ "$SUBMISSION_STATUS" != "Accepted" ]; then
    print_header "ERROR: Notarization failed (Status: $SUBMISSION_STATUS). Getting log..."
    xcrun notarytool log "$SUBMISSION_ID" --keychain-profile "$NOTARIZATION_PROFILE"
    exit 1
fi

# Staple the notarization ticket to the app
print_header "Stapling notarization ticket to the app"
xcrun stapler staple "$APP_PATH"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to staple notarization ticket to $APP_PATH"
    # Stapling failures might not be critical, decide whether to exit
    # exit 1
fi

# Verify the stapling
xcrun stapler validate "$APP_PATH"
if [ $? -ne 0 ]; then
    echo "WARNING: Staple validation failed for $APP_PATH"
fi

# Create DMG only after app is successfully notarized and stapled
print_header "Creating DMG with Applications link"
DMG_TEMP_DIR="$DIST_DIR/dmg_temp"
mkdir -p "$DMG_TEMP_DIR"
cp -R "$APP_PATH" "$DMG_TEMP_DIR/"
# Create a symbolic link to /Applications in the DMG
ln -s /Applications "$DMG_TEMP_DIR/"

# Create the DMG
print_header "Creating DMG file"
hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_TEMP_DIR" -ov -format UDZO "$DMG_PATH"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create DMG file $DMG_PATH"
    rm -rf "$DMG_TEMP_DIR"
    exit 1
fi

# Sign the DMG
print_header "Signing DMG"
codesign --force --timestamp --sign "$DEVELOPER_ID" "$DMG_PATH"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to sign DMG $DMG_PATH"
    rm -rf "$DMG_TEMP_DIR"
    exit 1
fi

# Clean up temporary files
rm -rf "$DMG_TEMP_DIR"

print_header "Build Completed Successfully!"
echo "The app is located at: $APP_PATH"
echo "The DMG is located at: $DMG_PATH"
echo "App size: $(du -sh "$APP_PATH" | cut -f1)"
echo "DMG size: $(du -sh "$DMG_PATH" | cut -f1)" 