#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Exit if any command in a pipeline fails
set -o pipefail

# --- Configuration ---
APP_NAME="Echelon Project"
MAIN_SCRIPT="main.py"
ICON_PATH="Icons/Echelon.icns"
BUNDLE_ID="com.cr2creative.echelon"
# Use the App Store distribution certificate for the .app bundle
APP_CERT_IDENTITY="Apple Distribution: craig russo (5926DW86QY)"
# Use the Installer certificate for the .pkg installer
INSTALLER_CERT_IDENTITY="3rd Party Mac Developer Installer: craig russo (5926DW86QY)"
# TARGET_ARCH="arm64" # Specified in setup.py and forced via arch command
ENTITLEMENTS_FILE="build-tools/entitlements/entitlements.plist"
APP_VERSION="0.95" # Fetched from constants.py

# --- Virtual Environment Path ---
# Assuming the script is run from the project root where 'venv' exists
VENV_PYTHON="./venv/bin/python3"
VENV_PIP="./venv/bin/pip"

if [ ! -f "$VENV_PYTHON" ]; then
    echo >&2 "Error: Virtual environment python not found at $VENV_PYTHON. Please create/activate it. Aborting."
    exit 1
fi

# --- Build Process ---

echo "--- Starting macOS App Store Build for $APP_NAME using py2app (in venv, forced arm64) + pkgbuild ---"

# Check for required tools (codesign, pkgbuild outside venv)
command -v arch >/dev/null 2>&1 || { echo >&2 "arch command not found. Aborting."; exit 1; }
command -v codesign >/dev/null 2>&1 || { echo >&2 "codesign (Xcode Command Line Tools) not found. Install using 'xcode-select --install'. Aborting."; exit 1; }
command -v pkgbuild >/dev/null 2>&1 || { echo >&2 "pkgbuild (Xcode Command Line Tools) not found. Install using 'xcode-select --install'. Aborting."; exit 1; }

# Check for required files
if [ ! -f "setup.py" ]; then echo >&2 "Configuration file 'setup.py' not found. Aborting."; exit 1; fi
if [ ! -f "$MAIN_SCRIPT" ]; then echo >&2 "Main script '$MAIN_SCRIPT' not found. Aborting."; exit 1; fi
if [ ! -f "$ICON_PATH" ]; then echo >&2 "Icon file '$ICON_PATH' not found. Aborting."; exit 1; fi
if [ ! -f "$ENTITLEMENTS_FILE" ]; then echo >&2 "Entitlements file '$ENTITLEMENTS_FILE' not found. Aborting."; exit 1; fi
if [ ! -d "app" ]; then echo >&2 "Required 'app' directory not found. Aborting."; exit 1; fi

echo "1. Cleaning up previous builds..."
rm -rf ./build ./dist "$APP_NAME.pkg" # Remove top-level pkg too

echo "2. Building .app bundle with py2app using venv Python (forced arm64)..."
arch -arm64 "$VENV_PYTHON" setup.py py2app

# Path to the app bundle created by py2app
APP_BUNDLE_PATH="dist/$APP_NAME.app"

if [ ! -d "$APP_BUNDLE_PATH" ]; then
    echo >&2 "Error: py2app did not create the expected app bundle at $APP_BUNDLE_PATH. Aborting."
    exit 1
fi

echo "3. Code signing the .app bundle for App Store..."
codesign --force --deep --options runtime \
    --entitlements "$ENTITLEMENTS_FILE" \
    --sign "$APP_CERT_IDENTITY" \
    "$APP_BUNDLE_PATH"

echo "*** Manual Verification Required ***"
echo "Please manually test the application bundle located at:"
echo "$APP_BUNDLE_PATH"
echo "Verify that it launches (arm64 only), has the correct icon, and functions correctly (check for dlopen errors!)."
read -p "Press Enter to continue after testing..."

echo "4. Creating .pkg installer using pkgbuild..."
pkgbuild --component "$APP_BUNDLE_PATH" \
    --install-location /Applications \
    --sign "$INSTALLER_CERT_IDENTITY" \
    "dist/$APP_NAME.pkg"

PKG_PATH="dist/$APP_NAME.pkg"

echo "--- Build Complete ---"
echo "Signed package ready for upload:"
echo "$PKG_PATH"
echo ""
echo "App Store Connect Details:"
echo "  Bundle ID: $BUNDLE_ID"
echo "  SKU: 001"
echo "  Apple ID: 6743944821"
echo ""
echo "Upload '$PKG_PATH' using the Transporter app or Xcode."

exit 0 