@echo off
echo Testing Python environment...

REM Try to use Python from the virtual environment
IF EXIST ".venv\Scripts\python.exe" (
    echo Using Python from virtual environment
    .venv\Scripts\python.exe test_python_env.py
    goto :EOF
)

REM Try system Python
echo Trying system Python...
python test_python_env.py
IF %ERRORLEVEL% EQU 0 goto :EOF

REM Try Python Launcher
echo Trying Python Launcher...
py -3 test_python_env.py
IF %ERRORLEVEL% EQU 0 goto :EOF

echo.
echo ERROR: Could not find a working Python installation.
echo. 