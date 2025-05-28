# PowerShell script to fix Cursor theme settings
# This script will help reset Cursor's theme to dark mode

Write-Host "Fixing Cursor theme settings..." -ForegroundColor Cyan

# Check if we're running on ARM64
$isArm64 = $env:PROCESSOR_ARCHITECTURE -eq "ARM64"
Write-Host "ARM64 System: $isArm64" -ForegroundColor Cyan

# Common locations for Cursor settings
$settingsLocations = @(
    "$env:APPDATA\Cursor\User\settings.json",
    "$env:USERPROFILE\AppData\Roaming\Cursor\User\settings.json"
)

$settingsFound = $false

foreach ($settingsPath in $settingsLocations) {
    if (Test-Path $settingsPath) {
        Write-Host "Found Cursor settings at: $settingsPath" -ForegroundColor Green
        $settingsFound = $true
        
        try {
            # Backup original settings
            $backupPath = "$settingsPath.backup"
            Copy-Item -Path $settingsPath -Destination $backupPath -Force
            Write-Host "Created backup at: $backupPath" -ForegroundColor Green
            
            # Read settings
            $settings = Get-Content -Path $settingsPath -Raw | ConvertFrom-Json
            
            # Modify theme settings
            $settings.workbench.colorTheme = "Default Dark+"
            $settings."workbench.preferredDarkColorTheme" = "Default Dark+"
            
            # Set additional theme-related settings
            $settings."workbench.colorCustomizations" = @{}
            $settings."window.titleBarStyle" = "custom"
            $settings."window.menuBarVisibility" = "visible"
            
            # Save modified settings
            $settings | ConvertTo-Json -Depth 10 | Set-Content -Path $settingsPath
            Write-Host "Theme settings restored to dark mode" -ForegroundColor Green
        }
        catch {
            Write-Host "Error updating settings: $_" -ForegroundColor Red
        }
    }
}

if (-not $settingsFound) {
    Write-Host "Could not find Cursor settings. You may need to manually adjust theme settings." -ForegroundColor Yellow
    Write-Host "Look for Settings > Color Theme in the Cursor application." -ForegroundColor Yellow
}

# Display instructions for manual theme change
Write-Host "`nIf automatic fix doesn't work, try these manual steps:" -ForegroundColor Cyan
Write-Host "1. Open Cursor" -ForegroundColor White
Write-Host "2. Press Ctrl+Shift+P to open the command palette" -ForegroundColor White
Write-Host "3. Type 'Color Theme' and select 'Preferences: Color Theme'" -ForegroundColor White
Write-Host "4. Select 'Default Dark+' or your preferred dark theme" -ForegroundColor White
Write-Host "`nPress Enter to continue..." -ForegroundColor Cyan
Read-Host 