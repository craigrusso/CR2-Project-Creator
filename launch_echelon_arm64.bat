@echo off
SETLOCAL

echo Launching Echelon on ARM64 Windows...

REM Set path to the Python executable
SET "PYTHON_PATH="

REM Look for Python in common ARM64 locations
IF EXIST "C:\Program Files\Python\python.exe" (
    SET "PYTHON_PATH=C:\Program Files\Python\python.exe"
    echo Found Python at C:\Program Files\Python\python.exe
    goto :RUN_APP
)

REM Check for Python in virtual environment
IF EXIST "%~dp0.venv\Scripts\python.exe" (
    SET "PYTHON_PATH=%~dp0.venv\Scripts\python.exe"
    echo Found Python in virtual environment
    goto :RUN_APP
)

REM Check for any Python in PATH
WHERE python >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    SET "PYTHON_PATH=python"
    echo Found Python in PATH
    goto :RUN_APP
)

REM Check for Python launcher
WHERE py >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    echo Found Python launcher, will try to use it
    SET "PYTHON_PATH=py -3"
    goto :RUN_APP
)

echo ERROR: Could not find a suitable Python installation.
echo Please install Python and ensure it's in your PATH.
echo.
pause
exit /b 1

:RUN_APP
echo.
echo Running application with: %PYTHON_PATH%
echo.

REM Run the main application directly
IF "%PYTHON_PATH%"=="py -3" (
    py -3 "%~dp0main.py" %*
) ELSE (
    "%PYTHON_PATH%" "%~dp0main.py" %*
)

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo The application exited with an error code: %ERRORLEVEL%
    echo.
    pause
)

exit /b %ERRORLEVEL% 