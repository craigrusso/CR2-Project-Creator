!include "MUI2.nsh"
!include "x64.nsh"

Name "Echelon"
OutFile "Echelon_Setup_ARM64.exe"
InstallDir "$PROGRAMFILES64\Echelon"
RequestExecutionLevel admin

!define MUI_ICON "ICONS\Echelon.ico"
!define MUI_UNICON "ICONS\Echelon.ico"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Main Application"
    SetOutPath "$INSTDIR"
    File /r "WIN_BUILD\ARM\Echelon\*"
    
    # Create shortcuts
    CreateShortCut "$SMPROGRAMS\Echelon.lnk" "$INSTDIR\Echelon.exe" "" "$INSTDIR\Echelon.exe" 0
    CreateShortCut "$DESKTOP\Echelon.lnk" "$INSTDIR\Echelon.exe" "" "$INSTDIR\Echelon.exe" 0
    
    # Write registry for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon" "DisplayName" "Echelon"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon" "DisplayIcon" "$\"$INSTDIR\Echelon.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon" "Publisher" "CR2 Creative"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon" "DisplayVersion" "${VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon" "NoRepair" 1
    
    # Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\Echelon.lnk"
    Delete "$DESKTOP\Echelon.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Echelon"
SectionEnd 