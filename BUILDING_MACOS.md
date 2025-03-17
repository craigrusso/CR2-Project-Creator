# Building Echelon for macOS on Apple Silicon

This document provides instructions for building Echelon as a native macOS application specifically optimized for Apple Silicon (M1/M2/M3) Macs.

## Prerequisites

- Apple Silicon Mac (M1/M2/M3) for best results
- Python 3.9+ installed
- pip and virtualenv
- Homebrew (optional, for installing create-dmg)

## Building the Application

The build process has been automated with scripts. There are two main steps:

1. Building the app bundle
2. Creating a DMG for distribution (optional)

### Step 1: Build the App Bundle

Run the following command to build the app bundle:

```bash
./build_macos_arm64.sh
```

This script will:
- Ensure you're on Apple Silicon (or warn you if not)
- Clean previous builds
- Update pip, setuptools and wheel
- Install project requirements
- Build the app bundle with py2app specifically for Apple Silicon
- Place the built app in `dist/Echelon.app`

### Step 2: Create a DMG (Optional)

To create a DMG file for easy distribution:

```bash
./create_dmg.sh
```

This script will:
- Check that the app bundle exists
- Install create-dmg via Homebrew if not already installed
- Create a nicely formatted DMG with the Echelon icon
- Name the DMG using the app name, version, and architecture
- Place the DMG in the `dist/` directory

## Manual Installation

If you prefer not to create a DMG, you can manually copy the app bundle from `dist/Echelon.app` to your Applications folder.

## Troubleshooting

### Python Environment Issues

If you encounter Python environment issues, try using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Then run the build script from within the virtual environment.

### Missing Libraries

If the app crashes due to missing libraries, check that all dependencies are correctly listed in the `setup.py` file and that they're being included in the app bundle.

### Architecture Issues

The app is built specifically for Apple Silicon. If you're running on an Intel Mac:
- You'll see a warning during the build process
- The resulting app will run through Rosetta translation

For universal binaries that run natively on both Intel and Apple Silicon Macs, you would need to:
1. Build on an Intel Mac for Intel architecture
2. Build on an Apple Silicon Mac for ARM64 architecture
3. Use `lipo` to combine the binaries into a universal binary

## License

Echelon is copyright (c) 2023-present Craig P. Russo and CR2 Creative. All rights reserved. 