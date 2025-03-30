#!/bin/bash
# Script to help set up certificates for Mac App Store submission

echo "==== Mac App Store Certificate Setup Guide ===="
echo ""
echo "To submit apps to the Mac App Store, you need two special certificates:"
echo "1. Mac App Distribution (3rd Party Mac Developer Application)"
echo "2. Mac Installer Distribution (3rd Party Mac Developer Installer)"
echo ""
echo "You currently have this certificate for non-App Store distribution:"
echo "- Developer ID Application: craig russo (5926DW86QY)"
echo ""
echo "===== Step 1: Create Certificate Signing Requests ====="
echo "To create the required certificates, you first need to create Certificate Signing Requests (CSR)."
echo ""
echo "Opening Keychain Access to help you create a CSR..."
open -a "Keychain Access"
echo ""
echo "In Keychain Access, please:"
echo "1. Go to Keychain Access > Certificate Assistant > Request a Certificate From a Certificate Authority"
echo "2. Enter your email address: craig_russo@me.com"
echo "3. Enter your name: Craig Russo"
echo "4. Select 'Saved to disk' and continue"
echo "5. Save the CSR file (CertificateSigningRequest.certSigningRequest) to your desktop"
echo ""
read -p "Press Enter once you've created and saved your CSR..." 
echo ""

echo "===== Step 2: Obtain Certificates from Apple Developer Portal ====="
echo ""
echo "Now, you need to obtain the certificates from the Apple Developer Portal:"
echo ""
echo "1. Go to https://developer.apple.com/account/resources/certificates/list"
echo "2. Click the + button to add a new certificate"
echo "3. Under Software, select 'Mac App Distribution'"
echo "4. Upload the CSR file you just created and click Continue"
echo "5. Download the certificate and double-click to install it in your keychain"
echo ""
echo "6. Return to the certificates page and add another certificate"
echo "7. Under Software, select 'Mac Installer Distribution'"
echo "8. Upload the same CSR file and continue"
echo "9. Download this certificate and install it too"
echo ""
read -p "Press Enter after you've downloaded and installed both certificates..." 
echo ""

echo "===== Step 3: Verify Certificates ====="
echo "Checking for App Store certificates in your keychain..."
echo ""

# Check for Mac App Distribution certificate
if security find-identity -p codesigning | grep -q "3rd Party Mac Developer Application"; then
    echo "✅ Mac App Distribution certificate found!"
else
    echo "❌ Mac App Distribution certificate not found."
    echo "   Please complete the steps to obtain this certificate."
fi

# Check for Mac Installer Distribution certificate
if security find-identity -p codesigning | grep -q "3rd Party Mac Developer Installer"; then
    echo "✅ Mac Installer Distribution certificate found!"
else
    echo "❌ Mac Installer Distribution certificate not found."
    echo "   Please complete the steps to obtain this certificate."
fi

echo ""
echo "===== Step 4: Update App Store Build Script ====="
echo ""
echo "Once you have both certificates, you'll need to update the build_for_app_store.sh script"
echo "with the exact certificate names shown in your keychain."
echo ""
echo "To view your certificates, run:"
echo "security find-identity -p codesigning"
echo ""
echo "Then update the codesign and productbuild commands in build_for_app_store.sh with the exact certificate names."
echo ""
echo "After obtaining your certificates, run ./build_for_app_store.sh again to build your app for the App Store." 