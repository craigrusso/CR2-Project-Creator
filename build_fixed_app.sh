#!/bin/bash
# Simplified build script to create a working app bundle

# Create MAC BUILD directory if it doesn't exist
mkdir -p "MAC BUILD"
echo "Working directory: $(pwd)"

# Variables
APP_NAME="Echelon"
DMG_NAME="Echelon-Installer"
# Use the correct developer ID
DEVELOPER_ID="Developer ID Application: craig russo (5926DW86QY)"
NOTARIZATION_PROFILE="EchelonNotaryProfile"

# Function to print headers
function print_header() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
}

print_header "Building application with PyInstaller"
pyinstaller --clean --noconfirm fix_app.spec

# Test if app was created
if [ ! -d "dist/Echelon.app" ]; then
    print_header "ERROR: App bundle was not created"
    exit 1
fi

# Test app from command line
print_header "Testing app"
cd dist/Echelon.app/Contents/MacOS
echo "Running app to capture errors..."
./Echelon > ../../../app_output.log 2>&1 &
APP_PID=$!
sleep 5

# Check if app is running
if ps -p $APP_PID > /dev/null; then
    print_header "App is running successfully!"
    # Kill the app after a few seconds
    sleep 3
    kill $APP_PID 2>/dev/null || true
else
    print_header "App failed to start. Check log:"
    cat ../../../app_output.log
fi

cd ../../../ # Return to dist directory

print_header "App has been built"
echo "The app is located at: $(pwd)/Echelon.app"
echo "App size: $(du -sh Echelon.app | cut -f1)" 