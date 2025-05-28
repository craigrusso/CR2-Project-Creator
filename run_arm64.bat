@echo off
SETLOCAL

echo Starting Echelon on ARM64...

REM Try to use the virtual environment Python first
IF EXIST ".venv\Scripts\python.exe" (
    echo Using virtual environment Python
    .venv\Scripts\python.exe run_arm64.py %*
    exit /b %ERRORLEVEL%
)

REM Try the system Python
echo Trying system Python...
python run_arm64.py %*
IF %ERRORLEVEL% NEQ 9009 exit /b %ERRORLEVEL%

REM Try the Python launcher
echo Trying Python launcher...
py -3 run_arm64.py %*
IF %ERRORLEVEL% NEQ 9009 exit /b %ERRORLEVEL%

REM If all attempts failed, show an error
echo.
echo ERROR: Could not find a Python installation to run the application.
echo Please make sure Python is installed and in your PATH, or that the virtual
echo environment is properly set up.
echo.
pause
exit /b 1 