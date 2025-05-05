Echelon 1.0 Installer Build Instructions
=====================================

This folder contains an NSIS script (EchelonInstaller.nsi) to create the Windows installer for Echelon 1.0.

To build the installer:

1. Install NSIS (Nullsoft Scriptable Install System)
   - Download from: https://nsis.sourceforge.io/Download
   - Install with the default options

2. Right-click on "EchelonInstaller.nsi" in this folder
   - Select "Compile NSIS Script" from the context menu
   - This will create "EchelonSetup.exe" in this folder

3. Alternatively, if you installed NSIS in the standard location:
   - Open a command prompt in this folder
   - Run: "C:\Program Files (x86)\NSIS\makensis.exe" EchelonInstaller.nsi

About the installer:
- The installer packages the Echelon 1.0 application with all necessary files
- It uses the icon from the ICONS folder
- It creates shortcuts in the Start Menu and Desktop (optional)
- It registers the application for Add/Remove Programs
- It creates an uninstaller

The installer includes the following files from the dist folder:
- Echelon.exe (the main application)
- template_structure_icon.svg
- All files in the _internal folder 