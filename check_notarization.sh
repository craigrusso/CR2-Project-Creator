#!/bin/bash

# A simple script to check notarization status without submitting anything new

TEAM_ID="5926DW86QY"

echo "===== Check Apple Notarization Status ====="
echo "This script will check the status of recent notarization submissions."
echo ""

# Prompt for Apple ID credentials
read -p "Enter your Apple ID email: " APPLE_ID
read -s -p "Enter your app-specific password: " APP_PASSWORD
echo ""
echo ""

echo "=== Fetching recent notarization history ==="
xcrun notarytool history --apple-id "$APPLE_ID" --password "$APP_PASSWORD" --team-id "$TEAM_ID"

echo ""
echo "To check details for a specific submission, enter the ID below."
read -p "Enter submission ID (or leave empty to exit): " SUBMISSION_ID

if [ -n "$SUBMISSION_ID" ]; then
    echo ""
    echo "=== Checking details for submission $SUBMISSION_ID ==="
    xcrun notarytool info "$SUBMISSION_ID" --apple-id "$APPLE_ID" --password "$APP_PASSWORD" --team-id "$TEAM_ID"
    
    echo ""
    read -p "Did the notarization succeed? Would you like to staple tickets to the app and DMG? (yes/no): " STAPLE
    
    if [[ "$STAPLE" == "yes" ]]; then
        echo ""
        echo "=== Stapling notarization ticket to the app and DMG ==="
        xcrun stapler staple "dist/Echelon.app"
        xcrun stapler staple "dist/Echelon_0.08_AppleSilicon.dmg"
        
        echo ""
        echo "=== Verifying stapling ==="
        xcrun stapler validate "dist/Echelon.app"
        xcrun stapler validate "dist/Echelon_0.08_AppleSilicon.dmg"
        
        echo ""
        echo "=== Notarization and stapling complete! ==="
    fi
fi

echo "Done!" 