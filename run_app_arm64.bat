@echo off
SETLOCAL

echo Running Echelon in the foreground...

REM Use the specific ARM64 Python path directly
SET "PYTHON_PATH=C:\Users\craigrusso\AppData\Local\Programs\Python\Python313-arm64\python.exe"

IF NOT EXIST "%PYTHON_PATH%" (
    echo ERROR: Python not found at %PYTHON_PATH%
    echo Please verify the Python installation path.
    pause
    exit /b 1
)

echo Found Python at: %PYTHON_PATH%
echo.

REM Run main.py directly in the foreground (no background processes)
"%PYTHON_PATH%" "%~dp0main.py" %*

REM If we get here, the app has exited
exit /b %ERRORLEVEL% 