@echo off
SETLOCAL

echo Launching Echelon with ARM64 Python...

REM Use the specific ARM64 Python path
SET "PYTHON_PATH=C:\Users\craigrusso\AppData\Local\Programs\Python\Python313-arm64\python.exe"

IF NOT EXIST "%PYTHON_PATH%" (
    echo ERROR: Python not found at %PYTHON_PATH%
    echo Please verify the Python installation path.
    pause
    exit /b 1
)

echo Found Python at: %PYTHON_PATH%
echo.

REM Run the main application directly
"%PYTHON_PATH%" "%~dp0main.py" %*

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo The application exited with an error code: %ERRORLEVEL%
    echo.
    pause
)

exit /b %ERRORLEVEL% 