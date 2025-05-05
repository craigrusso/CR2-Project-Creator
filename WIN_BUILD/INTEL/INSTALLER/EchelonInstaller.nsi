; Echelon Installer Script for NSIS
; Written for Echelon 1.0

; Define constants
!define APPNAME "Echelon"
!define APPVERSION "1.0"
!define PUBLISHER "CR2 Creative"
!define DESCRIPTION "Echelon Project Manager"
!define HELPURL "https://cr2creative.com"
!define UPDATEURL "https://cr2creative.com"
!define ABOUTURL "https://cr2creative.com"

; Set compression options
SetCompressor lzma

; Include Modern UI
!include "MUI2.nsh"

; General
Name "${APPNAME} ${APPVERSION}"
OutFile "EchelonSetup.exe"
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "Install_Dir"
RequestExecutionLevel admin

; Digital signature settings
; Uncomment and configure these lines when you have a code signing certificate
;!define SIGNTOOL '"C:\Program Files (x86)\Windows Kits\10\bin\x86\signtool.exe"'
;!define CERTPATH "C:\path\to\your\certificate.pfx"
;!define CERTPASSWORD "your_certificate_password"
;!finalize '${SIGNTOOL} sign /t http://timestamp.digicert.com /f ${CERTPATH} /p ${CERTPASSWORD} "%1"'

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "C:\Users\craig\SynologyDrive\V4\ICONS\Echelon.ico"
!define MUI_UNICON "C:\Users\craig\SynologyDrive\V4\ICONS\Echelon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installation sections
Section "Echelon" SecMain
  SetOutPath "$INSTDIR"
  
  ; Copy main executable
  File "..\dist\Echelon\Echelon.exe"
  File "..\dist\Echelon\template_structure_icon.svg"
  
  ; Copy internal files (all subdirectories)
  SetOutPath "$INSTDIR\_internal"
  File /r "..\dist\Echelon\_internal\*.*"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${APPNAME}.exe"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  ; Optional desktop shortcut
  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${APPNAME}.exe"
  
  ; Write registry keys for uninstaller
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME} ${APPVERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${APPVERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\${APPNAME}.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
  
  ; Create the uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
  ; Remove Start Menu shortcuts
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  
  ; Remove desktop shortcut
  Delete "$DESKTOP\${APPNAME}.lnk"
  
  ; Remove files and directories
  Delete "$INSTDIR\${APPNAME}.exe"
  Delete "$INSTDIR\template_structure_icon.svg"
  Delete "$INSTDIR\uninstall.exe"
  RMDir /r "$INSTDIR\_internal"
  RMDir "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
  DeleteRegKey HKLM "Software\${APPNAME}"
SectionEnd 