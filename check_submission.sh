#!/bin/bash

# Script to check a specific notarization submission
SUBMISSION_ID="4ae36d54-f3f2-4682-89bd-ef2374f760ea"

echo "===== Checking Notarization Status ====="
echo "This will check the status of submission ID: $SUBMISSION_ID"
echo ""

# Prompt for Apple ID credentials
read -p "Enter your Apple ID email: " APPLE_ID
read -s -p "Enter your app-specific password: " APP_PASSWORD
echo ""
echo ""

# Check status
echo "Checking notarization status..."
xcrun notarytool info "$SUBMISSION_ID" \
    --apple-id "$APPLE_ID" \
    --password "$APP_PASSWORD" \
    --team-id "5926DW86QY"

# Check if user wants to staple
echo ""
read -p "Did notarization succeed? Do you want to staple the ticket? (y/n): " STAPLE

if [ "$STAPLE" == "y" ]; then
    echo "Stapling notarization ticket to app..."
    xcrun stapler staple "dist/Echelon.app"
    
    echo "Stapling notarization ticket to DMG..."
    xcrun stapler staple "dist/Echelon_0.08_AppleSilicon.dmg"
    
    echo "Verifying app stapling..."
    xcrun stapler validate "dist/Echelon.app"
    
    echo "Verifying DMG stapling..."
    xcrun stapler validate "dist/Echelon_0.08_AppleSilicon.dmg"
    
    echo "All done! Your app is now notarized and stapled."
fi

echo "Process complete." 