#!/bin/bash

# Set the path to your application
APP_PATH="dist/Echelon.app"

# Set the signing identities
SIGNING_IDENTITY_INTERNAL="Developer ID Application: craig russo (5926DW86QY)" # Use Developer ID for everything in this step
SIGNING_IDENTITY_APP="Developer ID Application: craig russo (5926DW86QY)"    # Use Developer ID for everything in this step
# INSTALLER_IDENTITY="3rd Party Mac Developer Installer: craig russo (5926DW86QY)" # Not needed for zip
# ENTITLEMENTS_FILE="app_store_entitlements.plist" # Use minimal/no entitlements for Developer ID signing initially
ENTITLEMENTS_FILE="build-tools/entitlements/developer_id_entitlements.plist" # Updated path to entitlements file

# Check if the app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: Application bundle not found at $APP_PATH"
    exit 1
fi

# Check if entitlements file exists
if [ ! -f "$ENTITLEMENTS_FILE" ]; then
    echo "Error: Entitlements file not found at $ENTITLEMENTS_FILE"
    exit 1
fi

echo "Signing application bundle..."

# Replace previous signing loops with a more comprehensive approach

echo "Signing application bundle contents comprehensively..."

# Find and sign all frameworks first (deepest first implicitly due to find)
find "$APP_PATH/Contents" -depth -type d -name "*.framework" -print0 | while IFS= read -r -d $'\0' framework; do
    # Check if it's a Mach-O binary first (frameworks directory might contain non-code files)
    codesign_target="$framework/Versions/Current/$(basename "$framework" .framework)"
    if [ ! -f "$codesign_target" ]; then
      # Fallback for frameworks without standard structure? Or just sign the directory? Let's sign the dir for now.
      codesign_target="$framework"
    fi

    # Check if the target actually exists and is signable before attempting
    if [ -e "$codesign_target" ]; then
         if file "$codesign_target" | grep -qE 'Mach-O.*executable|Mach-O.*dylib|Mach-O.*bundle|directory$'; then
            echo "Signing framework: $framework"
            # Sign framework with INTERNAL identity
            codesign --force --sign "$SIGNING_IDENTITY_INTERNAL" --timestamp --options runtime "$framework" || echo "Failed to sign framework $framework"
            # Add verification
            echo "Verifying signature for $framework"
            codesign -dv --verbose=4 "$framework"
         else
             echo "Skipping signing non-Mach-O framework component: $codesign_target"
         fi
    else
        # If even the base framework directory doesn't exist, skip.
         echo "Skipping signing potentially invalid framework path: $framework"
    fi
done

# Find and sign all dylibs, shared objects, and executables
find "$APP_PATH/Contents" -type f \( -name "*.dylib" -o -name "*.so" -o -perm +111 \) -print0 | while IFS= read -r -d $'\0' file; do
    # Exclude files within already signed frameworks/apps if possible? Maybe not needed with --force
    # Check if it's a Mach-O binary before signing
    if file "$file" | grep -qE 'Mach-O.*executable|Mach-O.*dylib|Mach-O.*bundle'; then
        echo "Signing binary: $file"
        # Sign binary with INTERNAL identity
        codesign --force --sign "$SIGNING_IDENTITY_INTERNAL" --timestamp --options runtime "$file" || echo "Failed to sign binary $file"
        # Add verification for a specific binary example (adjust path if needed)
        if [[ "$file" == *"libqcocoa.dylib"* ]]; then
             echo "Verifying signature for $file"
             codesign -dv --verbose=4 "$file"
        fi
    else
        # Don't echo skip for non-binaries found by perm +111 unless verbose needed
        # echo "Skipping non-binary file: $file"
        : # No-op
    fi
done

# Find and sign helper apps
find "$APP_PATH/Contents" -depth -type d -name "*.app" -print0 | while IFS= read -r -d $'\0' helper_app; do
    echo "Signing helper app: $helper_app"
    # Sign helper app with INTERNAL identity, NO specific entitlements needed usually for DevID unless hardened runtime etc.
    codesign --force --sign "$SIGNING_IDENTITY_INTERNAL" --timestamp --options runtime "$helper_app" || echo "Failed to sign helper app $helper_app"
    # Optional: Add verification codesign -dv --verbose=4 "$helper_app"
done

# Sign the main application executable
MAIN_EXEC_PATH="$APP_PATH/Contents/MacOS/Echelon"
if [ -f "$MAIN_EXEC_PATH" ]; then
    echo "Signing main application executable..."
    # Sign main executable with INTERNAL identity, NO specific entitlements needed usually for DevID unless hardened runtime etc.
    codesign --force --sign "$SIGNING_IDENTITY_INTERNAL" --timestamp --options runtime "$MAIN_EXEC_PATH" || echo "Failed to sign main executable"
    # Optional: Add verification
    # echo "Verifying signature for $MAIN_EXEC_PATH"
    # codesign -dv --verbose=4 "$MAIN_EXEC_PATH"
else
     echo "Warning: Main executable not found at expected path: $MAIN_EXEC_PATH"
fi

# Sign the main application bundle last (seals the deal)
echo "Signing main application bundle..."
# Sign main bundle with APP identity (Developer ID) and minimal entitlements
codesign --force --sign "$SIGNING_IDENTITY_APP" --entitlements "$ENTITLEMENTS_FILE" --timestamp --options runtime "$APP_PATH" || echo "Failed to sign main app bundle"
# Add verification for final bundle
echo "Verifying signature for final $APP_PATH"
codesign -dv --verbose=4 "$APP_PATH"

# Verify the signature (will verify against the final APP identity - Developer ID)
echo "Verifying signature..."
codesign --verify --deep --strict --verbose=4 "$APP_PATH"
if [ $? -ne 0 ]; then
    echo "Error: Code signature verification failed."
    exit 1 # Exit if verification fails before notarization attempt
fi

# Create a zip archive for notarization
ZIP_NAME="Echelon_Notarize.zip"
echo "Creating zip archive $ZIP_NAME for notarization..."
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_NAME"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create zip archive $ZIP_NAME"
    exit 1
fi

echo "Zip archive created. Submitting for notarization..."

# Submit the zip for notarization
xcrun notarytool submit "$ZIP_NAME" --keychain-profile "EchelonNotaryProfile" --wait
NOTARY_EXIT_CODE=$?

if [ $NOTARY_EXIT_CODE -ne 0 ]; then
    echo "Error: Notarization submission failed with exit code $NOTARY_EXIT_CODE."
    # Consider fetching the log here
    # xcrun notarytool log <submission_id> --keychain-profile "EchelonNotaryProfile"
    exit 1
fi

# If submission command seems successful (exit 0), check the actual status from notarytool output (requires parsing or separate check)
# For simplicity, assume success if exit code is 0 for now, needs refinement based on actual notarytool --wait behavior

echo "Notarization submission completed (Check status above). Attempting to staple ticket..."

# Staple the notarization ticket to the app
xcrun stapler staple "$APP_PATH"
if [ $? -ne 0 ]; then
    echo "Warning: Failed to staple notarization ticket. You may need to do this manually after confirmed success."
else
    echo "Notarization ticket stapled successfully to $APP_PATH"
fi

echo "Notarization and stapling process complete for Developer ID signed app."
echo "Next steps: Re-sign $APP_PATH with Apple Distribution cert and entitlements, then package using pkgbuild."

# Remove pkgbuild section for now
# PKG_IDENTIFIER="com.craigrusso.echelon" 
# PKG_VERSION="1.0" 
# OUTPUT_PKG_NAME="Echelon_AppStore.pkg" 

# pkgbuild --component "$APP_PATH" \
#          --install-location "/Applications" \
#          --identifier "$PKG_IDENTIFIER" \
#          --version "$PKG_VERSION" \
#          --sign "$INSTALLER_IDENTITY" \
#          "$OUTPUT_PKG_NAME"

# if [ $? -eq 0 ]; then
#     echo "Package created successfully as $OUTPUT_PKG_NAME"
# else
#     echo "Error: Failed to create package $OUTPUT_PKG_NAME"
#     exit 1
# fi 