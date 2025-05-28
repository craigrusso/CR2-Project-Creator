@echo off
SETLOCAL

echo Setting up virtual environment with ARM64 Python...
echo.

REM Use the specific ARM64 Python path
SET "PYTHON_PATH=C:\Users\craigrusso\AppData\Local\Programs\Python\Python313-arm64\python.exe"

IF NOT EXIST "%PYTHON_PATH%" (
    echo ERROR: Python not found at %PYTHON_PATH%
    echo Please verify the Python installation path.
    pause
    exit /b 1
)

echo Found Python at: %PYTHON_PATH%

REM Check if virtual environment exists
IF EXIST "%~dp0.venv" (
    echo.
    echo Virtual environment already exists at %~dp0.venv
    
    echo Do you want to recreate it? (Y/N)
    choice /C YN /M "Recreate virtual environment"
    IF %ERRORLEVEL% EQU 1 (
        echo.
        echo Removing existing virtual environment...
        rmdir /S /Q "%~dp0.venv"
    ) ELSE (
        goto :VENV_EXISTS
    )
)

echo.
echo Creating virtual environment...
"%PYTHON_PATH%" -m venv "%~dp0.venv"

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Virtual environment created successfully.

:VENV_EXISTS
echo.
echo Activating virtual environment...
call "%~dp0.venv\Scripts\activate.bat"

echo.
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install PyQt5 requests

echo.
echo Virtual environment setup complete.
echo.
echo To run your application, use run_echelon_arm64_direct.bat
echo.

pause
exit /b 0 