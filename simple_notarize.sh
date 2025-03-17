#!/bin/bash

# Simple notarization script
set -e

echo "===== Simple Apple Notarization for Echelon ====="
echo "Before continuing, make sure you have:"
echo "1. An Apple Developer ID account"
echo "2. An app-specific password generated at appleid.apple.com"
echo ""

# Prompt for Apple ID credentials
read -p "Enter your Apple ID email: " APPLE_ID
read -s -p "Enter your app-specific password: " APP_PASSWORD
echo ""
echo ""

# Check if app exists
if [ ! -d "dist/Echelon.app" ]; then
    echo "Error: dist/Echelon.app not found!"
    exit 1
fi

# Check if DMG exists
if [ ! -f "dist/Echelon_0.08_AppleSilicon.dmg" ]; then
    echo "Error: dist/Echelon_0.08_AppleSilicon.dmg not found!"
    exit 1
fi

# Create ZIP if it doesn't exist or if user wants to recreate it
if [ -f "Echelon.zip" ]; then
    read -p "Echelon.zip already exists. Recreate it? (y/n): " RECREATE_ZIP
    if [ "$RECREATE_ZIP" == "y" ]; then
        rm Echelon.zip
        echo "Creating new ZIP archive..."
        cd dist
        zip -r "../Echelon.zip" "Echelon.app"
        cd ..
    fi
else
    echo "Creating ZIP archive..."
    cd dist
    zip -r "../Echelon.zip" "Echelon.app"
    cd ..
fi

# Submit for notarization
echo ""
echo "Submitting app for notarization to Apple..."
echo "This may take a few minutes..."

xcrun notarytool submit Echelon.zip \
    --apple-id "$APPLE_ID" \
    --password "$APP_PASSWORD" \
    --team-id "5926DW86QY" \
    --wait

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