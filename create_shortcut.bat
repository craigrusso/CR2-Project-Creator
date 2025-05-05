@echo off
echo Creating Echelon shortcut with correct icon...

:: Path to the executable
set EXE_PATH=%~dp0WIN_BUILD\INTEL\dist\Echelon\Echelon.exe
:: Path to the icon
set ICON_PATH=%~dp0ICONS\Echelon.ico

:: Create VBScript to make the shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Echelon.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%EXE_PATH%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%ICON_PATH%" >> CreateShortcut.vbs
echo oLink.Description = "Echelon Project Manager" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%~dp0WIN_BUILD\INTEL\dist\Echelon" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

:: Run the VBScript
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo Shortcut created on your desktop! Use this shortcut for correct icon display.

pause 