#!/bin/bash

# Script to ONLY check notarization status
SUBMISSION_ID="4ae36d54-f3f2-4682-89bd-ef2374f760ea"

echo "===== Just Checking Notarization Status ====="
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

echo ""
echo "If status is 'Accepted', you can run this command to staple the ticket:"
echo ""
echo "xcrun stapler staple \"dist/Echelon.app\""
echo "xcrun stapler staple \"dist/Echelon_0.08_AppleSilicon.dmg\""
echo "" 