# PowerShell script to create a shortcut for Echelon
# This ensures the shortcut has the correct icon and properties

# Get the full path to the executable
$exePath = Join-Path -Path $PSScriptRoot -ChildPath "WIN_BUILD\ARM\Echelon.exe"
$shortcutPath = Join-Path -Path ([Environment]::GetFolderPath("Desktop")) -ChildPath "Echelon.lnk"

# Create a WScript Shell object to create the shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $exePath
$Shortcut.IconLocation = $exePath + ",0"
$Shortcut.Description = "Echelon Project Template Manager"
$Shortcut.WorkingDirectory = Split-Path $exePath
$Shortcut.Save()

Write-Host "Shortcut created at: $shortcutPath"

# Optionally, clear the icon cache to ensure Windows displays the correct icon
Write-Host "Clearing icon cache to ensure proper icon display..."
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
$iconCachePath = "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache*"
Remove-Item -Path $iconCachePath -Force -ErrorAction SilentlyContinue
Start-Process explorer

Write-Host "Icon cache cleared. The Echelon icon should now display correctly." 