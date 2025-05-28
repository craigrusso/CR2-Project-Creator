# PowerShell script to launch Echelon on ARM64 Windows
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

Write-Host "Launching Echelon on ARM64 Windows..." -ForegroundColor Cyan

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Define potential Python paths
$pythonPaths = @(
    # Virtual environment Python
    (Join-Path -Path $scriptDir -ChildPath ".venv\Scripts\python.exe"),
    # Common ARM64 Windows Python locations
    "C:\Program Files\Python\python.exe",
    # PATH-based Python executables
    "python.exe"
)

# Try to find a valid Python executable
$pythonExe = $null

foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        $pythonExe = $path
        Write-Host "Found Python at: $pythonExe" -ForegroundColor Green
        break
    }
}

# If no Python found in paths, try the Python launcher
if ($null -eq $pythonExe) {
    try {
        $pythonLauncherTest = & py -3 -c "print('Python launcher works')" 2>$null
        if ($pythonLauncherTest -eq "Python launcher works") {
            Write-Host "Using Python launcher (py -3)" -ForegroundColor Green
            # Launch the app with the Python launcher
            & py -3 (Join-Path -Path $scriptDir -ChildPath "main.py") $args
            exit $LASTEXITCODE
        }
    } catch {
        # Python launcher not available or failed
    }
}

# If we found a Python executable, use it
if ($null -ne $pythonExe) {
    $mainScript = Join-Path -Path $scriptDir -ChildPath "main.py"
    Write-Host "Running: $pythonExe $mainScript" -ForegroundColor Cyan
    
    try {
        & $pythonExe $mainScript $args
        exit $LASTEXITCODE
    } catch {
        Write-Host "Error running Python: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ERROR: Could not find a suitable Python installation." -ForegroundColor Red
    Write-Host "Please install Python and ensure it's in your PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
} 