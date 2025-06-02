#!/usr/bin/env python3
# Build script for Windows ARM64 Echelon application

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from app.config.app_config import APP_VERSION, APP_BUILD_NUMBER

def main():
    print(f"Building Echelon Windows ARM64 version {APP_VERSION} (build {APP_BUILD_NUMBER})")
    
    # Create build directories if they don't exist
    build_dir = Path("WIN_BUILD/ARM")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Update the manifest with the correct version and build number
    update_manifest_version()
    update_version_info()
    
    # Ensure template_structure_icon.svg exists in both locations
    ensure_template_icons()
    
    # Run PyInstaller
    print("Running PyInstaller...")
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "Echelon_windows_arm64.spec"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("PyInstaller build completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed: {e}")
        return 1
    
    # Create Windows shortcut
    create_windows_shortcut()
    
    # Create NSIS installer
    create_nsis_installer()
    
    # Code sign the executable and installer
    code_sign_executables()
    
    print("Build process completed successfully")
    return 0

def update_manifest_version():
    """Update the manifest file with the correct AppUserModelID"""
    manifest_path = "manifest.xml"
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace placeholder with actual version and build number
        app_id = f"cr2creative.echelon.{APP_VERSION.replace('.', '_')}.{APP_BUILD_NUMBER}"
        content = content.replace("cr2creative.echelon.APP_VERSION.APP_BUILD_NUMBER", app_id)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated manifest with AppUserModelID: {app_id}")
    except Exception as e:
        print(f"Error updating manifest: {e}")

def update_version_info():
    """Update the version info file with the correct version numbers"""
    version_info_path = "version_info.txt"
    
    try:
        with open(version_info_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace APP_VERSION placeholder
        content = content.replace("APP_VERSION", APP_VERSION)
        content = content.replace("APP_BUILD_NUMBER", APP_BUILD_NUMBER)
        
        with open(version_info_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated version info with version: {APP_VERSION}, build: {APP_BUILD_NUMBER}")
    except Exception as e:
        print(f"Error updating version info: {e}")

def ensure_template_icons():
    """Ensure template_structure_icon.svg exists in both required locations"""
    src_icon_path = "app/assets/icons/template_structure_icon.svg"
    dest_icon_path = "ICONS/templates/template_structure_icon.svg"
    
    # Create the destination directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_icon_path), exist_ok=True)
    
    # If source exists, copy to destination
    if os.path.exists(src_icon_path):
        shutil.copy2(src_icon_path, dest_icon_path)
        print(f"Copied template icon to {dest_icon_path}")
    # If destination exists, copy to source
    elif os.path.exists(dest_icon_path):
        os.makedirs(os.path.dirname(src_icon_path), exist_ok=True)
        shutil.copy2(dest_icon_path, src_icon_path)
        print(f"Copied template icon to {src_icon_path}")
    else:
        print("WARNING: template_structure_icon.svg not found in either location")

def create_windows_shortcut():
    """Create a Windows shortcut for the Echelon executable"""
    try:
        dist_dir = Path("dist")
        executable_path = dist_dir / "Echelon.exe"
        shortcut_path = Path("WIN_BUILD/ARM/Echelon.lnk")
        
        if not executable_path.exists():
            print(f"ERROR: Executable not found at {executable_path}")
            return
        
        # Use PowerShell to create the shortcut
        ps_command = f"""
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{executable_path}"
        $Shortcut.IconLocation = "{executable_path},0"
        $Shortcut.Description = "Echelon Project Template Manager"
        $Shortcut.Save()
        """
        
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        print(f"Created shortcut at {shortcut_path}")
    except Exception as e:
        print(f"Error creating Windows shortcut: {e}")

def create_nsis_installer():
    """Create an NSIS installer package"""
    try:
        # Create NSIS script
        nsis_script = """
; Echelon Installer Script
Unicode True

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Define application name and version
!define PRODUCT_NAME "Echelon"
!define PRODUCT_VERSION "{APP_VERSION}"
!define PRODUCT_PUBLISHER "CR2 Creative"
!define PRODUCT_WEB_SITE "https://cr2creative.com"
!define PRODUCT_DIR_REGKEY "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\Echelon.exe"
!define PRODUCT_UNINST_KEY "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${PRODUCT_NAME}"

; Use modern UI
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "EULA.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; Installation details
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "WIN_BUILD\\ARM\\EchelonSetup_ARM64_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES64\\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite on
  
  ; Copy the main executable
  File "dist\\Echelon.exe"
  
  ; Create desktop shortcut
  CreateShortcut "$DESKTOP\\${PRODUCT_NAME}.lnk" "$INSTDIR\\Echelon.exe"
  
  ; Create start menu shortcut
  CreateDirectory "$SMPROGRAMS\\${PRODUCT_NAME}"
  CreateShortcut "$SMPROGRAMS\\${PRODUCT_NAME}\\${PRODUCT_NAME}.lnk" "$INSTDIR\\Echelon.exe"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\\uninstall.exe"
  
  ; Write registry keys for uninstaller
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\\Echelon.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\\uninstall.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\\Echelon.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  
  ; Get estimated size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Section Uninstall
  ; Remove shortcuts
  Delete "$DESKTOP\\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\\${PRODUCT_NAME}\\${PRODUCT_NAME}.lnk"
  RMDir "$SMPROGRAMS\\${PRODUCT_NAME}"
  
  ; Remove files and uninstaller
  Delete "$INSTDIR\\Echelon.exe"
  Delete "$INSTDIR\\uninstall.exe"
  
  ; Remove directories
  RMDir "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
SectionEnd
""".replace("{APP_VERSION}", APP_VERSION)

        # Write NSIS script to file
        nsis_script_path = Path("WIN_BUILD/ARM/installer.nsi")
        with open(nsis_script_path, 'w', encoding='utf-8') as f:
            f.write(nsis_script)
        
        # Run NSIS compiler
        subprocess.run(["makensis", str(nsis_script_path)], check=True)
        print("NSIS installer created successfully")
    except Exception as e:
        print(f"Error creating NSIS installer: {e}")

def code_sign_executables():
    """Code sign the executable and installer using SSL.com CodeSignTool"""
    try:
        # Paths to executables to sign
        executables = [
            Path("dist/Echelon.exe"),
            Path(f"WIN_BUILD/ARM/EchelonSetup_ARM64_{APP_VERSION}.exe")
        ]
        
        codesign_tool_path = Path("C:/Users/craigrusso/AppData/Local/Programs/CodeSignTool-v1.3.2-windows/CodeSignTool.bat")
        
        for exe_path in executables:
            if not exe_path.exists():
                print(f"WARNING: File to sign not found: {exe_path}")
                continue
            
            print(f"Signing {exe_path}...")
            
            # Use the SSL.com CodeSignTool
            cmd = [
                str(codesign_tool_path),
                "sign",
                "-credential_id=25312c27-34a7-4680-925c-a6082eb85884",
                "-username=craig_russo@me.com",
                "-password=", # Prompt for password for security
                f"-input_file_path={exe_path}",
                "-override=true"
            ]
            
            # Run the command and allow password input
            subprocess.run(cmd)
            
            # Give a small delay between signing operations
            time.sleep(2)
        
        print("Code signing completed")
    except Exception as e:
        print(f"Error during code signing: {e}")
        print("NOTE: You may need to sign the executables manually")

if __name__ == "__main__":
    sys.exit(main()) 