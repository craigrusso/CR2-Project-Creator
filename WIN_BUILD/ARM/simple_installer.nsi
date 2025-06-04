; Simple installer for Echelon

Name "Echelon"
OutFile "Echelon_Setup_ARM64.exe"
InstallDir "$PROGRAMFILES64\Echelon"
RequestExecutionLevel admin

Section "Install"
  SetOutPath $INSTDIR
  File "Echelon.exe"
  
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  CreateDirectory "$SMPROGRAMS\Echelon"
  CreateShortCut "$SMPROGRAMS\Echelon\Echelon.lnk" "$INSTDIR\Echelon.exe"
  CreateShortCut "$DESKTOP\Echelon.lnk" "$INSTDIR\Echelon.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\Echelon.exe"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\Echelon\Echelon.lnk"
  RMDir "$SMPROGRAMS\Echelon"
  Delete "$DESKTOP\Echelon.lnk"
SectionEnd 