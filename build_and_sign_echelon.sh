#!/bin/bash
# Script to build and sign Echelon app for Apple Silicon

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}    Building and Signing Echelon for Apple Silicon${NC}"
echo -e "${BLUE}=======================================================${NC}"

# Ask for the signing identity to use
echo -e "\n${YELLOW}Available code signing identities:${NC}"
security find-identity -v -p codesigning

echo -e "\n${GREEN}Enter the name of the signing identity to use (e.g., 'CR2 Code Signing'):${NC}"
read SIGNING_IDENTITY

if [ -z "$SIGNING_IDENTITY" ]; then
    echo -e "${RED}No signing identity provided. Will build without signing.${NC}"
    DO_SIGN=false
else
    DO_SIGN=true
    echo -e "${GREEN}Will use signing identity: ${YELLOW}$SIGNING_IDENTITY${NC}"
fi

# Clean previous builds
echo -e "\n${YELLOW}Cleaning previous builds...${NC}"
rm -rf build dist

# Build the app for Apple Silicon
echo -e "\n${YELLOW}Building Echelon for Apple Silicon...${NC}"
pyinstaller --target-architecture arm64 --clean --windowed \
    --icon="Echelon.icns" \
    --name="Echelon" \
    --osx-bundle-identifier="com.cr2creative.echelon" \
    --add-data="app:app" \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    main.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

# Update Info.plist
echo -e "\n${YELLOW}Updating Info.plist...${NC}"
PLIST_PATH="dist/Echelon.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :NSPrincipalClass string NSApplication" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSPrincipalClass NSApplication" "$PLIST_PATH"
/usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.'" "$PLIST_PATH" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSHumanReadableCopyright 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.'" "$PLIST_PATH"

# Sign the app if a signing identity was provided
if [ "$DO_SIGN" = true ]; then
    echo -e "\n${YELLOW}Signing the application with '$SIGNING_IDENTITY'...${NC}"
    
    # Try to sign with strict validation first
    echo "Attempting to sign with strict validation..."
    if codesign --force --deep --options runtime --sign "$SIGNING_IDENTITY" "dist/Echelon.app"; then
        echo -e "${GREEN}App signed successfully with strict validation!${NC}"
    else
        echo -e "${YELLOW}Strict validation signing failed. Trying with relaxed validation...${NC}"
        
        # Try signing with relaxed validation
        if codesign --force --deep --options runtime --no-strict --sign "$SIGNING_IDENTITY" "dist/Echelon.app"; then
            echo -e "${GREEN}App signed successfully with relaxed validation!${NC}"
        else
            echo -e "${RED}App signing failed. Will continue without signing.${NC}"
        fi
    fi
    
    # Verify the signature
    echo -e "\n${YELLOW}Verifying signature...${NC}"
    codesign -vvv --deep --strict "dist/Echelon.app" || echo -e "${YELLOW}Verification showed issues but may still work.${NC}"
else
    echo -e "\n${YELLOW}Skipping code signing as no identity was provided.${NC}"
fi

# Create DMG
echo -e "\n${YELLOW}Creating DMG with Applications folder shortcut...${NC}"
create-dmg \
  --volname "Echelon" \
  --volicon "Echelon.icns" \
  --window-pos 200 120 \
  --window-size 800 500 \
  --icon-size 128 \
  --icon "Echelon.app" 200 240 \
  --hide-extension "Echelon.app" \
  --app-drop-link 600 240 \
  --no-internet-enable \
  "dist/Echelon_AppleSilicon.dmg" \
  "dist/Echelon.app"

if [ $? -ne 0 ]; then
    echo -e "${RED}DMG creation failed!${NC}"
    exit 1
fi

echo -e "\n${GREEN}Build complete!${NC}"
echo -e "Application bundle: ${YELLOW}dist/Echelon.app${NC}"
echo -e "DMG package: ${YELLOW}dist/Echelon_AppleSilicon.dmg${NC}"
echo -e "\n${BLUE}=======================================================${NC}"
echo -e "${GREEN}To install, open the DMG and drag the app to the Applications shortcut.${NC}"
echo -e "${BLUE}=======================================================${NC}" 