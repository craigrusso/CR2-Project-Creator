@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo ================================================
echo  Setting up Windows ARM64 Environment for Echelon
echo ================================================
echo.

REM Check if running on ARM64
powershell -Command "$arch = $env:PROCESSOR_ARCHITECTURE; if ($arch -eq 'ARM64') { exit 0 } else { exit 1 }"
IF %ERRORLEVEL% NEQ 0 (
    echo WARNING: This does not appear to be an ARM64 system.
    echo This script is intended for ARM64 Windows environments.
    echo.
    pause
    exit /b 1
)

REM Check for Python installation
SET PYTHON_FOUND=0
SET PYTHON_PATH=

echo Checking for Python installations...

REM Check common ARM64 Python locations
IF EXIST "C:\Program Files\Python\python.exe" (
    SET "PYTHON_PATH=C:\Program Files\Python\python.exe"
    SET PYTHON_FOUND=1
    echo Found Python at C:\Program Files\Python\python.exe
)

REM Check virtual environment
IF EXIST "%~dp0.venv\Scripts\python.exe" (
    SET "PYTHON_PATH=%~dp0.venv\Scripts\python.exe"
    SET PYTHON_FOUND=1
    echo Found Python in virtual environment
)

REM Check Python in PATH
WHERE python >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    FOR /F "tokens=*" %%i IN ('where python') DO (
        SET "PYTHON_PATH=%%i"
        SET PYTHON_FOUND=1
        echo Found Python in PATH: %%i
        goto :PYTHON_CHECK_DONE
    )
)

:PYTHON_CHECK_DONE
IF %PYTHON_FOUND% EQU 0 (
    echo.
    echo ERROR: No Python installation found.
    echo Please install Python for ARM64 Windows.
    echo.
    echo You can download Python from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Check for Clang installation
echo.
echo Checking for Clang installation...
WHERE clang >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    FOR /F "tokens=*" %%i IN ('clang --version') DO (
        echo Found Clang: %%i
        goto :CLANG_CHECK_DONE
    )
) ELSE (
    echo WARNING: Clang not found in PATH.
    echo You mentioned you've installed Clang 20.1.5, but it's not in your PATH.
    echo Please ensure Clang is properly installed and in your PATH.
)

:CLANG_CHECK_DONE

REM Create a virtual environment if one doesn't exist
IF NOT EXIST "%~dp0.venv" (
    echo.
    echo Creating virtual environment in .venv directory...
    "%PYTHON_PATH%" -m venv "%~dp0.venv"
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

REM Activate the virtual environment and install dependencies
echo.
echo Activating virtual environment and installing dependencies...
call "%~dp0.venv\Scripts\activate.bat"

echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install PyQt5 requests

REM Run the environment check script
echo.
echo Running environment check...
python "%~dp0check_arm64_env.py"

echo.
echo ================================================
echo Environment setup complete.
echo.
echo To run the application, use:
echo   launch_echelon_arm64.bat
echo.
echo ================================================

pause 