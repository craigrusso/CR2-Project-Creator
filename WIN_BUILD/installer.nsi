; installer.nsi
; NSIS script for Echelon

!define APPNAME "Echelon"
!define COMPANYNAME "CR2 Creative"
!define DESCRIPTION "Echelon Project Creator"
!define VERSION "1.0" ; Make sure this matches your app version
!define BUILD "250" ; Optional build number
!define EXENAME "Echelon.exe"
!define INSTALLER_NAME "Echelon_Installer_v${VERSION}.exe"

; --- Paths ---
; Assuming this script is in 'WIN_BUILD' and icons are in '../icons'
!define ICONFILE "..\icons\Echelon.ico"
!define UNICONFILE "..\icons\Echelon.ico"
!define LICENSEFILE "..\LICENSE" ; Assuming LICENSE file exists in root
; PyInstaller output directory relative to this script
!define SOURCE_APP_DIR "dist\Echelon" ; This MUST match the 'name' in COLLECT in the spec file

; --- General ---
Name "${APPNAME} ${VERSION}"
OutFile "${INSTALLER_NAME}" ; Output installer in the same dir as this script
InstallDir "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "Install_Dir"
RequestExecutionLevel admin ; Request admin privileges for Program Files installation
BrandingText "${COMPANYNAME}"
SetCompressor /SOLID lzma ; Good compression

VIProductVersion "${VERSION}.0.${BUILD}"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "CompanyName" "${COMPANYNAME}"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2023-present Craig P. Russo and CR2 Creative"
VIAddVersionKey "FileDescription" "${DESCRIPTION}"
VIAddVersionKey "FileVersion" "${VERSION}"

; --- Interface ---
Icon "${ICONFILE}"
UninstallIcon "${UNICONFILE}"

!include "MUI2.nsh" ; Modern UI 2
!define MUI_ABORTWARNING ; Warn user if they exit setup
!define MUI_ICON "${ICONFILE}"
!define MUI_UNICON "${UNICONFILE}"

; --- Pages ---
!insertmacro MUI_PAGE_WELCOME
!ifdef LICENSEFILE
    !insertmacro MUI_PAGE_LICENSE "${LICENSEFILE}"
!endif
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; --- Uninstaller Pages ---
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; --- Language ---
!insertmacro MUI_LANGUAGE "English"

; --- Installation Section ---
Section "Install ${APPNAME}" SEC_INSTALL
    SetOutPath "$INSTDIR"

    ; --- CHECK if source files exist ---
    IfFileExists "${SOURCE_APP_DIR}\${EXENAME}" FilesOK NoFilesError
    NoFilesError:
        MessageBox MB_OK|MB_ICONSTOP "Cannot find required installation files in '${SOURCE_APP_DIR}'.$\r$\nPlease ensure the application was built correctly (e.g., using PyInstaller) before running this script."
        Abort
    FilesOK:

    ; Copy all files from the PyInstaller output directory
    File /r "${SOURCE_APP_DIR}\*.*"

    ; --- Create Shortcuts ---
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXENAME}" "" "$INSTDIR\${EXENAME}" 0
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXENAME}" "" "$INSTDIR\${EXENAME}" 0 ; Optional Desktop Shortcut

    ; --- Write Registry / Uninstaller ---
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" '"$INSTDIR\${EXENAME}",0'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1

    ; Write the uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

; --- Uninstallation Section ---
Section "Uninstall" SEC_UNINSTALL
    ; --- Remove Files ---
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR" ; Remove the installation directory

    ; --- Remove Shortcuts ---
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$DESKTOP\${APPNAME}.lnk" ; If created
    RMDir "$SMPROGRAMS\${APPNAME}"

    ; --- Remove Registry Keys ---
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"
SectionEnd

; --- Functions ---
Function .onInit
    ; Optional: Check for existing installations, etc.
FunctionEnd

Function un.onInit
    ; Optional: Check if okay to uninstall (e.g., app not running)
FunctionEnd 