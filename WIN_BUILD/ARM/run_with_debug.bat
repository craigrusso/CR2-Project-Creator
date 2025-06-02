@echo off
echo Running Echelon with debug output...
set PYTHONVERBOSE=1
set PYINSTALLER_DO_TRACE=1
cd Y:\WIN_BUILD\ARM\Echelon
Echelon.exe
if %ERRORLEVEL% NEQ 0 echo Error code: %ERRORLEVEL%
pause 