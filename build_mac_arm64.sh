#!/bin/bash
# Build script for Echelon v1.0.X - ARM64 Apple Silicon build for macOS

echo "==== Echelon ARM64 Build Script ===="
echo "Building Echelon application for Apple Silicon (ARM64)"

# 1. Verify the build number was incremented
echo "Build number updated to: $(grep APP_BUILD_NUMBER app/constants.py | cut -d'=' -f2 | tr -d ' ')"

# 2. Resource path handling is already updated in all required files:
# - app/ui/color_scheme_pyqt.py
# - app/ui/structure_editor/ui_components.py
# - app/dialogs/template_creation_form.py
# - app/ui/tree_styling.py

# 3. Clean previous build
echo "Cleaning previous build artifacts..."
mkdir -p "MAC BUILD/old_builds" 
mv "MAC BUILD/build" "MAC BUILD/dist" "MAC BUILD/old_builds/" 2>/dev/null || echo 'No existing build/dist to move'

# 4. Build application
echo "Building ARM64-only application with PyInstaller..."
pyinstaller --clean --target-arch arm64 --name Echelon --icon=ICONS/Echelon.icns --windowed --noupx \
  --distpath "MAC BUILD/dist" --workpath "MAC BUILD/build" --noconfirm \
  --hidden-import json \
  --hidden-import webbrowser \
  --hidden-import uuid \
  --hidden-import requests \
  --hidden-import packaging \
  --hidden-import PyQt5.QtCore \
  --hidden-import PyQt5.QtSvg \
  --hidden-import rubicon.objc \
  --add-data "app:app" \
  --add-data "app/assets/css:app/assets/css" \
  --add-data "app/assets/icons:app/assets/icons" \
  --add-data "EULA.txt:." \
  main.py

# 5. Verify application
echo "Verifying application size and structure..."
du -sh "MAC BUILD/dist/Echelon.app"
echo "Expected size: ~88MB"
echo "Opening app to verify UI elements..."
open "MAC BUILD/dist/Echelon.app"
echo "Please verify dropdown and twirl arrows appear correctly in UI"
read -p "Press Enter to continue with signing or Ctrl+C to abort..."

# 6. Sign individual components
echo "Signing individual components..."
find "MAC BUILD/dist/Echelon.app" -type f \( -name '*.so' -o -name '*.dylib' -o -perm +111 \) -exec codesign --force --sign "Developer ID Application: craig russo (5926DW86QY)" --options=runtime --timestamp {} \;

# 7. Sign main app bundle
echo "Signing main application bundle..."
codesign --force --sign "Developer ID Application: craig russo (5926DW86QY)" --options=runtime --timestamp "MAC BUILD/dist/Echelon.app"

# 8. Update modification time
echo "Updating modification time..."
touch "MAC BUILD/dist/Echelon.app"

# 9. Verify signatures
echo "Verifying code signatures..."
codesign -dv --verbose=4 "MAC BUILD/dist/Echelon.app"
echo "Validating with Gatekeeper (will show 'rejected' until notarized)..."
spctl --assess -vv "MAC BUILD/dist/Echelon.app"

# 10. Prepare for notarization
echo "Preparing for notarization..."
rm -f "MAC BUILD/Echelon_for_notarization.zip"
ditto -c -k --sequesterRsrc --keepParent "MAC BUILD/dist/Echelon.app" "MAC BUILD/Echelon_for_notarization.zip"

# 11. Submit for notarization
echo "Submitting for notarization..."
xcrun notarytool submit "MAC BUILD/Echelon_for_notarization.zip" --keychain-profile "EchelonNotaryProfile" --wait

# 12. Staple notarization ticket
echo "Stapling notarization ticket..."
xcrun stapler staple "MAC BUILD/dist/Echelon.app"

# 13. Create DMG installer
echo "Creating DMG installer..."
rm -f "MAC BUILD/EchelonInstaller.dmg"
create-dmg --volname "Echelon Installer" --window-pos 200 120 --window-size 600 420 --icon-size 100 --icon "Echelon.app" 150 180 --app-drop-link 450 180 --format UDBZ "MAC BUILD/EchelonInstaller.dmg" "MAC BUILD/dist/Echelon.app"

# 14. Sign DMG
echo "Signing DMG installer..."
codesign --force --sign "Developer ID Application: craig russo (5926DW86QY)" "MAC BUILD/EchelonInstaller.dmg"

echo "==== Build Complete ===="
echo "Final product: MAC BUILD/EchelonInstaller.dmg (signed and notarized ARM64-only application)"
echo "Size: $(du -sh "MAC BUILD/EchelonInstaller.dmg" | cut -f1)"

# TROUBLESHOOTING NOTES
echo ""
echo "Troubleshooting Notes:"
echo "- If UI elements like dropdown arrows or twirl arrows are missing, verify the resource path fixes"
echo "- If the app fails to launch, run directly from terminal to see error messages"
echo "- Common issues involve missing PyQt5 modules or Python libraries"
echo "- For module import errors, add them to the --hidden-import list"
echo "- For resource file issues, ensure they're properly included with --add-data"
echo "- Be sure to include PyQt5.QtSvg in hidden imports for SVG rendering support" 