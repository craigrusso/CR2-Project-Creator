# Echelon macOS ARM64 Build Guide

This guide outlines the process for building, signing, notarizing, and packaging Echelon for macOS as an ARM64-only binary.

## Prerequisites

- macOS development environment with Xcode tools installed
- Python 3.9+ installed
- PyInstaller installed: `pip install pyinstaller`
- create-dmg utility installed: `brew install create-dmg`
- Valid Apple Developer ID for signing
- Keychain profile configured for notarization

## Build Process

The build process is automated with scripts that perform the following steps:

1. **Increment Build Number**: The scripts update `APP_BUILD_NUMBER` in `app/constants.py`.
2. **Clean Previous Build**: Moves any existing build artifacts to an 'old_builds' directory.
3. **Build Application**: Uses PyInstaller to create an ARM64-only build with all necessary modules and data files.
4. **Verify Application**: Displays the size of the built application and prompts for manual verification.
5. **Sign Components**: Signs all executable components within the application bundle.
6. **Sign Main App Bundle**: Signs the overall application bundle.
7. **Verify Signatures**: Verifies the code signatures and checks with Gatekeeper.
8. **Prepare for Notarization**: Creates a ZIP archive for notarization.
9. **Submit for Notarization**: Submits the application to Apple for notarization.
10. **Staple Notarization Ticket**: Staples the notarization ticket to the application.
11. **Create DMG Installer**: Creates a DMG installer with a nice layout.
12. **Sign DMG**: Signs the DMG installer.

## Build Options

There are two ways to build Echelon:

### Option 1: Using Command-Line Arguments

Run the `build_macos_arm64.sh` script, which uses command-line arguments with PyInstaller:

```bash
./build_macos_arm64.sh
```

### Option 2: Using Spec File

Run the `build_with_spec.sh` script, which uses the PyInstaller spec file `Echelon_macos_arm64.spec`:

```bash
./build_with_spec.sh
```

The spec file approach is more maintainable and allows for more complex configurations.

## Manual Building

If you prefer to run PyInstaller manually:

1. Using command-line arguments:
   ```bash
   pyinstaller --clean --target-arch arm64 --name Echelon --icon=ICONS/Echelon.icns --windowed --noupx --distpath "MAC BUILD/dist" --workpath "MAC BUILD/build" --noconfirm --hidden-import json --hidden-import webbrowser --hidden-import uuid --hidden-import requests --hidden-import packaging --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtSvg --hidden-import rubicon.objc --hidden-import logging --hidden-import logging.handlers --hidden-import logging.config --collect-submodules logging --add-data "app:app" --add-data "app/assets/css:app/assets/css" --add-data "app/assets/icons:app/assets/icons" --add-data "app/assets/bundled_example_templates:app/assets/bundled_example_templates" --add-data "EULA.txt:." main.py
   ```

2. Using the spec file:
   ```bash
   pyinstaller --clean --noconfirm Echelon_macos_arm64.spec
   ```

## Troubleshooting

- **Missing UI Elements**: If dropdown arrows or twirl arrows are missing, verify the resource path fixes in:
  - `app/ui/color_scheme_pyqt.py`
  - `app/ui/structure_editor/ui_components.py`
  - `app/dialogs/template_creation_form.py`
  - `app/ui/tree_styling.py`

- **Launch Failures**: Run the app directly from the terminal to see error messages:
  ```bash
  /MAC\ BUILD/dist/Echelon.app/Contents/MacOS/Echelon
  ```

- **Module Import Errors**: Add missing modules to the `--hidden-import` list in the build script or spec file.

- **Resource File Issues**: Ensure all resource files are properly included with `--add-data` or in the spec file.

- **System Icon Display Issues**: Ensure `rubicon.objc` is included in hidden imports.

## Build Output

The final product is a signed and notarized DMG file containing an ARM64-only macOS application, approximately 88MB in size, located at `MAC BUILD/EchelonInstaller.dmg`.

## License

Copyright (c) 2023-present Craig P. Russo and CR2 Creative 