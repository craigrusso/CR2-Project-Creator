#!/bin/bash
# Script to notarize the Echelon app and DMG with Apple

# Exit on error
set -e

# Configuration
APP_NAME="Echelon"
APP_VERSION="0.08"
DMG_NAME="Echelon_0.08_AppleSilicon.dmg"
BUNDLE_ID="com.cr2creative.echelon"
TEAM_ID="5926DW86QY"

# Check if app exists
if [ ! -d "dist/Echelon.app" ]; then
    echo "Error: dist/Echelon.app does not exist!"
    exit 1
fi

# Check if DMG exists
if [ ! -f "dist/$DMG_NAME" ]; then
    echo "Error: dist/$DMG_NAME does not exist!"
    exit 1
fi

echo "===== Apple Notarization for $APP_NAME $APP_VERSION ====="
echo "This process will:"
echo "1. Create a ZIP archive of your app (if not already created)"
echo "2. Submit it to Apple's notarization service"
echo "3. Wait for notarization to complete (5-15 minutes)"
echo "4. Staple the notarization ticket to both the app and DMG"
echo ""
echo "You will need your Apple ID email and an app-specific password."
echo "If you don't have an app-specific password, create one at https://appleid.apple.com"
echo "under Security > App-Specific Passwords"
echo ""

# Prompt for Apple ID credentials
read -p "Enter your Apple ID email: " APPLE_ID
read -s -p "Enter your app-specific password: " APP_PASSWORD
echo ""
echo ""

# Check if ZIP already exists
if [ ! -f "${APP_NAME}.zip" ]; then
    # Create temporary ZIP of the app for notarization
    echo "=== Creating ZIP archive of the app ==="
    cd dist
    zip -r "../${APP_NAME}.zip" "${APP_NAME}.app"
    cd ..
    echo "ZIP archive created: ${APP_NAME}.zip"
else
    echo "=== Using existing ZIP archive: ${APP_NAME}.zip ==="
fi

# Submit app for notarization
echo ""
echo "=== Submitting app for notarization ==="
echo "This may take several minutes..."
SUBMISSION_RESULT=$(xcrun notarytool submit "${APP_NAME}.zip" --apple-id "$APPLE_ID" --password "$APP_PASSWORD" --team-id "$TEAM_ID" --wait)
echo "$SUBMISSION_RESULT"

# Extract submission ID from output
SUBMISSION_ID=$(echo "$SUBMISSION_RESULT" | grep "id:" | awk '{print $2}')
if [ -z "$SUBMISSION_ID" ]; then
    echo "Error: Could not extract submission ID. Please check the output above."
    exit 1
fi

echo "Submission ID: $SUBMISSION_ID"

# Check notarization status
echo ""
echo "=== Checking notarization status ==="
xcrun notarytool info "$SUBMISSION_ID" --apple-id "$APPLE_ID" --password "$APP_PASSWORD" --team-id "$TEAM_ID"

echo ""
read -p "Did the notarization succeed? (type 'yes' to continue): " NOTARIZATION_SUCCESS

if [[ "$NOTARIZATION_SUCCESS" != "yes" ]]; then
    echo "Notarization did not succeed. Exiting without stapling."
    exit 1
fi

# Staple the notarization ticket to the app and DMG
echo ""
echo "=== Stapling notarization ticket to the app and DMG ==="
xcrun stapler staple "dist/${APP_NAME}.app"
xcrun stapler staple "dist/${DMG_NAME}"

# Verify stapling
echo ""
echo "=== Verifying stapling ==="
xcrun stapler validate "dist/${APP_NAME}.app"
xcrun stapler validate "dist/${DMG_NAME}"

echo ""
echo "=== Notarization and stapling complete! ==="
echo "Your app and DMG are now notarized and ready for distribution."
echo "The following files have been notarized and stapled:"
echo "- dist/${APP_NAME}.app"
echo "- dist/${DMG_NAME}"
echo ""
echo "Cleanup: Removing temporary ZIP file"
rm "${APP_NAME}.zip"

echo "Done!" 