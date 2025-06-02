# Echelon Windows ARM64 Build Instructions

This document provides instructions for building Echelon as a Windows ARM64 application.

## Prerequisites

- Python 3.10+ for Windows ARM64
- PyQt6 installed (`pip install PyQt6`)
- PyInstaller installed (`pip install pyinstaller`)
- NSIS (Nullsoft Scriptable Install System) for creating the installer
- SSL.com CodeSignTool for code signing

## Build Files

The build process uses the following files:

1. `Echelon_windows_arm64.spec` - PyInstaller specification file
2. `manifest.xml` - Windows application manifest with AppUserModelID
3. `version_info.txt` - Windows executable metadata
4. `hooks/hook-app.py` - PyInstaller hook for importing app modules
5. `build_windows_arm64.py` - Build script that runs the entire process
6. `build_arm64.bat` - Batch file for easy execution

## Building the Application

1. Ensure all prerequisites are installed
2. Run the build_arm64.bat file or execute `python build_windows_arm64.py`
3. The build process will:
   - Create a single-file executable in `dist/Echelon.exe`
   - Create a Windows shortcut in `WIN_BUILD/ARM/Echelon.lnk`
   - Create an NSIS installer in `WIN_BUILD/ARM/EchelonSetup_ARM64_X.X.X.exe`
   - Sign both the executable and installer if possible

## Code Signing

The build script will attempt to sign the executable and installer using SSL.com CodeSignTool.
You'll need to enter your password when prompted.

If automatic signing fails, you can manually sign the files with:

```
CodeSignTool sign -credential_id=25312c27-34a7-4680-925c-a6082eb85884 -username=craig_russo@me.com -password="YOUR_PASSWORD" -input_file_path=dist/Echelon.exe -override=true
```

## Troubleshooting

### Common Issues

1. **Missing modules**: If the build fails due to missing modules, add them to the hiddenimports in the spec file.
2. **Missing icons**: Ensure template_structure_icon.svg exists in both app/assets/icons and ICONS/templates.
3. **Code signing fails**: Check the path to CodeSignTool.bat in build_windows_arm64.py and update if necessary.

### Testing the Build

1. Run the generated executable directly to test functionality.
2. Verify the application icon appears correctly in the taskbar.
3. Verify that template icons are displayed correctly. 