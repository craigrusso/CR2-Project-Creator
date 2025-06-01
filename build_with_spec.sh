#!/bin/bash
# Echelon macOS ARM64 Build Script (using spec file)
# Copyright (c) 2024 Craig P. Russo and CR2 Creative

set -e  # Exit on any error

# Display section header
section() {
  echo ""
  echo "================================================================================"
  echo "  $1"
  echo "================================================================================"
  echo ""
}

# 1. CLEAN PREVIOUS BUILD
section "CLEANING PREVIOUS BUILD"
mkdir -p "MAC BUILD/old_builds" 
mv "MAC BUILD/build" "MAC BUILD/dist" "MAC BUILD/old_builds/" 2>/dev/null || echo 'No existing build/dist to move'

# 2. BUILD APPLICATION USING SPEC FILE
section "BUILDING APPLICATION (ARM64) USING SPEC FILE"
pyinstaller --clean \
  --distpath "MAC BUILD/dist" \
  --workpath "MAC BUILD/build" \
  --noconfirm \
  Echelon_macos_arm64.spec

# 3. VERIFY APPLICATION
section "VERIFYING APPLICATION"
du -sh "MAC BUILD/dist/Echelon.app"
echo "Expected size: ~88MB"
echo ""
echo "IMPORTANT: Please manually run the application to verify UI elements"
echo "open \"MAC BUILD/dist/Echelon.app\""
echo ""
echo "Once verified, press Enter to continue with signing..."
read -p "Press Enter to continue..."

# 4. SIGN INDIVIDUAL COMPONENTS
section "SIGNING INDIVIDUAL COMPONENTS"
find "MAC BUILD/dist/Echelon.app" -type f \( -name '*.so' -o -name '*.dylib' -o -perm +111 \) -exec codesign --force --sign "Developer ID Application: craig russo (5926DW86QY)" --options=runtime --timestamp {} \;

# 5. SIGN MAIN APP BUNDLE
section "SIGNING MAIN APP BUNDLE"
codesign --force --sign "Developer ID Application: craig russo (5926DW86QY)" --options=runtime --timestamp "MAC BUILD/dist/Echelon.app"

# 6. UPDATE MODIFICATION TIME
section "UPDATING MODIFICATION TIME"
touch "MAC BUILD/dist/Echelon.app"

# 7. VERIFY SIGNATURES
section "VERIFYING SIGNATURES"
codesign -dv --verbose=4 "MAC BUILD/dist/Echelon.app"
echo ""
echo "Validating with Gatekeeper (will show 'rejected' until notarized)"
spctl --assess -vv "MAC BUILD/dist/Echelon.app"

# 8. PREPARE FOR NOTARIZATION
section "PREPARING FOR NOTARIZATION"
rm -f "MAC BUILD/Echelon_for_notarization.zip" && ditto -c -k --sequesterRsrc --keepParent "MAC BUILD/dist/Echelon.app" "MAC BUILD/Echelon_for_notarization.zip"

# 9. SUBMIT FOR NOTARIZATION
section "SUBMITTING FOR NOTARIZATION"
xcrun notarytool submit "MAC BUILD/Echelon_for_notarization.zip" --keychain-profile "EchelonNotaryProfile" --wait

# 10. STAPLE NOTARIZATION TICKET
section "STAPLING NOTARIZATION TICKET"
xcrun stapler staple "MAC BUILD/dist/Echelon.app"

# 11. CREATE DMG INSTALLER
section "CREATING DMG INSTALLER"
rm -f "MAC BUILD/EchelonInstaller.dmg" && create-dmg \
  --volname "Echelon Installer" \
  --window-pos 200 120 \
  --window-size 600 420 \
  --icon-size 100 \
  --icon "Echelon.app" 150 180 \
  --app-drop-link 450 180 \
  --format UDBZ \
  "MAC BUILD/EchelonInstaller.dmg" \
  "MAC BUILD/dist/Echelon.app"

# 12. SIGN DMG
section "SIGNING DMG"
codesign --force --sign "Developer ID Application: craig russo (5926DW86QY)" "MAC BUILD/EchelonInstaller.dmg"

section "BUILD COMPLETE"
echo "Signed and notarized DMG installer created successfully:"
echo "MAC BUILD/EchelonInstaller.dmg"
echo ""
echo "FINAL VERIFICATION:"
echo "Please test the DMG installer on a clean system."
echo "" 