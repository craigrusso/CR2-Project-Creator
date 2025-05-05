@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo --- Starting Build Script ---

REM --- Configuration ---
echo Setting up configuration variables...
SET "BUILD_DIR_NAME=WIN_BUILD"
SET "SPEC_FILE=%BUILD_DIR_NAME%\echelon_windows.spec"
SET "NSIS_SCRIPT=%BUILD_DIR_NAME%\installer.nsi"
SET "PYINSTALLER_DIST_DIR=%BUILD_DIR_NAME%\dist"
SET "PYINSTALLER_WORK_DIR=%BUILD_DIR_NAME%\build"
SET "FINAL_INSTALLER_DIR=%BUILD_DIR_NAME%"
echo Configuration variables set.

REM --- Clean Previous Build ---
echo Cleaning previous build directories (if they exist)...
IF EXIST "%PYINSTALLER_DIST_DIR%" (
    echo Removing "%PYINSTALLER_DIST_DIR%"...
    RMDIR /S /Q "%PYINSTALLER_DIST_DIR%"
    IF %ERRORLEVEL% NEQ 0 echo WARNING: Failed to remove %PYINSTALLER_DIST_DIR%
)
IF EXIST "%PYINSTALLER_WORK_DIR%" (
    echo Removing "%PYINSTALLER_WORK_DIR%"...
    RMDIR /S /Q "%PYINSTALLER_WORK_DIR%"
    IF %ERRORLEVEL% NEQ 0 echo WARNING: Failed to remove %PYINSTALLER_WORK_DIR%
)
IF EXIST "%FINAL_INSTALLER_DIR%\Echelon_Installer_*.exe" (
    echo Removing previous installer...
    DEL /Q "%FINAL_INSTALLER_DIR%\Echelon_Installer_*.exe"
    IF %ERRORLEVEL% NEQ 0 echo WARNING: Failed to remove previous installer.
)
echo Cleaning done.

REM --- Create Build Directory (if needed) ---
echo Checking if build directory needs creation...
IF NOT EXIST "%BUILD_DIR_NAME%" (
    echo Creating "%BUILD_DIR_NAME%"...
    MKDIR "%BUILD_DIR_NAME%"
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create directory %BUILD_DIR_NAME%.
        goto :EOF REM Use :EOF for standard exit
    )
) ELSE (
    echo Build directory "%BUILD_DIR_NAME%" already exists.
)

REM --- Create Spec File ---
echo Creating PyInstaller spec file: "%SPEC_FILE%"
(
    echo # -*- mode: python ; coding: utf-8 -*-
    echo # echelon_windows.spec
    echo.
    echo import sys
    echo import os
    echo.
    echo block_cipher = None
    echo.
    echo '# --- Determine Project Root ---'
    echo '# Assuming this spec file is in ^'%BUILD_DIR_NAME%^' inside the project root'
    echo project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    echo print(f"Project Root: {project_root}")
    echo.
    echo '# --- Data Files ---'
    echo '# PyInstaller expects tuples of (^'source_path^', ^'destination_in_bundle^')'
    echo '# Based on get_resource_path, assets should be placed relative to the bundle root (_MEIPASS)'
    echo datas = [
    echo     # Copy the entire app/templates directory to app/templates in the bundle
    echo     (os.path.join(project_root, 'app', 'templates'), os.path.join('app', 'templates')),
    echo     # Copy the entire app/assets directory to app/assets in the bundle
    echo     (os.path.join(project_root, 'app', 'assets'), os.path.join('app', 'assets')),
    echo     # Copy the entire icons/templates directory to icons/templates in the bundle
    echo     (os.path.join(project_root, 'icons', 'templates'), os.path.join('icons', 'templates')),
    echo     # Include the main icon file itself IF needed at runtime (unlikely for window icon)
    echo     # (os.path.join(project_root, 'icons', 'Echelon.ico'), 'icons')
    echo ]
    echo print(f"Data Files: {datas}")
    echo.
    echo '# --- Hidden Imports ---'
    echo '# Sometimes PyInstaller doesn^'ts detect all imports, especially with frameworks like PyQt'
    echo hiddenimports = [
    echo     'PyQt5.sip',
    echo     'PyQt5.QtCore',
    echo     'PyQt5.QtGui',
    echo     'PyQt5.QtWidgets',
    echo     # Add other potential hidden imports if needed, e.g., specific plugins or modules
    echo     'pkg_resources.py2_warn', # Often needed
    echo ]
    echo print(f"Hidden Imports: {hiddenimports}")
    echo.
    echo '# --- Main Analysis ---'
    echo a = Analysis(
    echo     [os.path.join(project_root, 'main.py')], # Path to your main script
    echo     pathex=[project_root], # Add project root to Python path for analysis
    echo     binaries=[],
    echo     datas=datas,
    echo     hiddenimports=hiddenimports,
    echo     hookspath=[],
    echo     runtime_hooks=[],
    echo     excludes=[],
    echo     win_no_prefer_redirects=False,
    echo     win_private_assemblies=False,
    echo     cipher=block_cipher,
    echo     noarchive=False
    echo )
    echo.
    echo '# --- PYZ (Python Archive) ---'
    echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
    echo.
    echo '# --- EXE (Executable) ---'
    echo exe = EXE(
    echo     pyz,
    echo     a.scripts,
    echo     [],
    echo     exclude_binaries=True,
    echo     name='Echelon', # Name of the final executable
    echo     debug=False,
    echo     bootloader_ignore_signals=False,
    echo     strip=False,
    echo     upx=True, # Use UPX for compression if available (reduces size)
    echo     console=False, # IMPORTANT: Set to False for GUI apps (no console window)
    echo     disable_windowed_traceback=False,
    echo     target_arch=None,
    echo     codesign_identity=None,
    echo     entitlements_file=None,
    echo     icon=os.path.join(project_root, 'icons', 'Echelon.ico') # Path to the application icon
    echo )
    echo.
    echo '# --- COLLECT (Bundle directory) ---'
    echo coll = COLLECT(
    echo     exe,
    echo     a.binaries,
    echo     a.zipfiles,
    echo     a.datas,
    echo     strip=False,
    echo     upx=True,
    echo     upx_exclude=[],
    echo     name='Echelon' # Name of the folder inside 'dist' containing the app
    echo )
    echo.
    echo print("Spec file generation complete.")
) > "%SPEC_FILE%"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to write spec file "%SPEC_FILE%".
    goto EndScript
)
echo Spec file created.

REM --- Create NSIS Script ---
echo Creating NSIS installer script: "%NSIS_SCRIPT%"
(
    echo ; installer.nsi
    echo ; NSIS script for Echelon
    echo.
    echo !define APPNAME "Echelon"
    echo !define COMPANYNAME "CR2 Creative"
    echo !define DESCRIPTION "Echelon Project Creator"
    echo !define VERSION "1.0" ; Make sure this matches your app version
    echo !define BUILD "250" ; Optional build number
    echo !define EXENAME "Echelon.exe"
    echo !define INSTALLER_NAME "Echelon_Installer_v${VERSION}.exe"
    echo.
    echo '; --- Paths ---'
    echo '; Assuming this script is in ^'%BUILD_DIR_NAME%^' and icons are in ^'..\icons^''
    echo !define ICONFILE "..\icons\Echelon.ico"
    echo !define UNICONFILE "..\icons\Echelon.ico"
    echo !define LICENSEFILE "..\LICENSE" ; Assuming LICENSE file exists in root
    echo '; PyInstaller output directory relative to this script'
    echo !define SOURCE_APP_DIR "dist\Echelon" ; This MUST match the ^'name^' in COLLECT in the spec file
    echo.
    echo '; --- General ---'
    echo Name "${APPNAME} ${VERSION}"
    echo OutFile "%BUILD_DIR_NAME%\${INSTALLER_NAME}" 
    echo InstallDir "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"
    echo InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "Install_Dir"
    echo RequestExecutionLevel admin ; Request admin privileges for Program Files installation
    echo BrandingText "${COMPANYNAME}"
    echo SetCompressor /SOLID lzma ; Good compression
    echo.
    echo VIProductVersion "${VERSION}.0.${BUILD}"
    echo VIAddVersionKey "ProductName" "${APPNAME}"
    echo VIAddVersionKey "CompanyName" "${COMPANYNAME}"
    echo VIAddVersionKey "LegalCopyright" "Copyright (c) 2023-present Craig P. Russo and CR2 Creative"
    echo VIAddVersionKey "FileDescription" "${DESCRIPTION}"
    echo VIAddVersionKey "FileVersion" "${VERSION}"
    echo.
    echo '; --- Interface ---'
    echo Icon "${ICONFILE}"
    echo UninstallIcon "${UNICONFILE}"
    echo.
    echo !include "MUI2.nsh" ; Modern UI 2
    echo !define MUI_ABORTWARNING ; Warn user if they exit setup
    echo !define MUI_ICON "${ICONFILE}"
    echo !define MUI_UNICON "${UNICONFILE}"
    echo.
    echo '; --- Pages ---'
    echo !insertmacro MUI_PAGE_WELCOME
    echo '!ifdef LICENSEFILE'
    echo '    !insertmacro MUI_PAGE_LICENSE "${LICENSEFILE}"'
    echo '!endif'
    echo !insertmacro MUI_PAGE_DIRECTORY
    echo !insertmacro MUI_PAGE_INSTFILES
    echo !insertmacro MUI_PAGE_FINISH
    echo.
    echo '; --- Uninstaller Pages ---'
    echo !insertmacro MUI_UNPAGE_CONFIRM
    echo !insertmacro MUI_UNPAGE_INSTFILES
    echo.
    echo '; --- Language ---'
    echo !insertmacro MUI_LANGUAGE "English"
    echo.
    echo '; --- Installation Section ---'
    echo Section "Install ${APPNAME}" SEC_INSTALL
    echo     SetOutPath "$INSTDIR"
    echo.
    echo     '; --- CHECK if source files exist ---'
    echo     'IfFileExists "${SOURCE_APP_DIR}\${EXENAME}" FilesOK NoFilesError'
    echo     NoFilesError:
    echo         MessageBox MB_OK^|MB_ICONSTOP "Cannot find required installation files in ^'${SOURCE_APP_DIR}^'.$\r$\nPlease ensure the application was built correctly before running the installer."
    echo         Abort
    echo     FilesOK:
    echo.
    echo     '; Copy all files from the PyInstaller output directory'
    echo     File /r "${SOURCE_APP_DIR}\*.*"
    echo.
    echo     '; --- Create Shortcuts ---'
    echo     CreateDirectory "$SMPROGRAMS\${APPNAME}"
    echo     CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXENAME}" "" "$INSTDIR\${EXENAME}" 0
    echo     CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXENAME}" "" "$INSTDIR\${EXENAME}" 0 '; Optional Desktop Shortcut'
    echo.
    echo     '; --- Write Registry / Uninstaller ---'
    echo     WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" "Install_Dir" "$INSTDIR"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" '^"$INSTDIR\Uninstall.exe^"'
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" '^"$INSTDIR\${EXENAME}",0^'
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSION}"
    echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    echo.
    echo     '; Write the uninstaller'
    echo     WriteUninstaller "$INSTDIR\Uninstall.exe"
    echo.
    echo SectionEnd
    echo.
    echo '; --- Uninstallation Section ---'
    echo Section "Uninstall" SEC_UNINSTALL
    echo     '; --- Remove Files ---'
    echo     Delete "$INSTDIR\Uninstall.exe"
    echo     RMDir /r "$INSTDIR" ; Remove the installation directory
    echo.
    echo     '; --- Remove Shortcuts ---'
    echo     Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    echo     Delete "$DESKTOP\${APPNAME}.lnk" ; If created
    echo     RMDir "$SMPROGRAMS\${APPNAME}"
    echo.
    echo     '; --- Remove Registry Keys ---'
    echo     DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    echo     DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"
    echo SectionEnd
    echo.
    echo '; --- Functions ---'
    echo Function .onInit
    echo     '; Optional: Check for existing installations, etc.'
    echo FunctionEnd
    echo.
    echo Function un.onInit
    echo     '; Optional: Check if okay to uninstall (e.g., app not running)'
    echo FunctionEnd
) > "%NSIS_SCRIPT%"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to write NSIS script "%NSIS_SCRIPT%".
    goto EndScript
)
echo NSIS script created.

REM --- Run PyInstaller ---
echo Running PyInstaller...
REM Add full path quoting for safety
pyinstaller --noconfirm --distpath "%PYINSTALLER_DIST_DIR%" --workpath "%PYINSTALLER_WORK_DIR%" "%SPEC_FILE%"

IF %ERRORLEVEL% NEQ 0 (
    echo PyInstaller build FAILED. Check the output above.
    goto EndScript
) ELSE (
    echo PyInstaller build successful. Output in "%PYINSTALLER_DIST_DIR%\Echelon"
)

REM --- Run NSIS ---
echo Compiling NSIS installer...
REM Add full path quoting for safety
makensis /V2 "%NSIS_SCRIPT%"

IF %ERRORLEVEL% NEQ 0 (
    echo NSIS compilation FAILED. Check the output above.
    goto EndScript
) ELSE (
    echo NSIS installer created successfully: "%BUILD_DIR_NAME%\Echelon_Installer_v1.0.exe"
)

echo Build process completed successfully.
echo You can find the bundled application in: "%PYINSTALLER_DIST_DIR%\Echelon"
echo You can find the installer executable in: "%BUILD_DIR_NAME%"

:EndScript
echo --- Build Script Finished ---

:EOF
ENDLOCAL
pause 