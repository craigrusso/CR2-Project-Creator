@echo off
echo Running Echelon ARM64 with detailed error logging...

:: Set the path to the application directory
set APP_DIR=%~dp0WIN_BUILD\ARM\dist\Echelon
cd "%APP_DIR%"

:: Enable Qt debugging
set QT_DEBUG_PLUGINS=1

:: Set up PATH with necessary directories
set PATH=%APP_DIR%;%APP_DIR%\platforms;%APP_DIR%\_internal;%APP_DIR%\_internal\PyQt6\Qt6\bin;%PATH%

:: Set Qt environment variables
set QT_PLUGIN_PATH=%APP_DIR%\platforms;%APP_DIR%\_internal\PyQt6\Qt6\plugins
set QT_QPA_PLATFORM_PLUGIN_PATH=%APP_DIR%\platforms

:: Create logs directory if it doesn't exist
if not exist "%APP_DIR%\logs" mkdir "%APP_DIR%\logs"

:: Write environment info to log
echo ===== ENVIRONMENT VARIABLES ===== > "%APP_DIR%\logs\debug_env.log"
echo PATH=%PATH% >> "%APP_DIR%\logs\debug_env.log"
echo QT_PLUGIN_PATH=%QT_PLUGIN_PATH% >> "%APP_DIR%\logs\debug_env.log"
echo QT_QPA_PLATFORM_PLUGIN_PATH=%QT_QPA_PLATFORM_PLUGIN_PATH% >> "%APP_DIR%\logs\debug_env.log"

:: List DLLs to see what's available
echo ===== AVAILABLE DLLs ===== >> "%APP_DIR%\logs\debug_env.log"
dir /s /b "%APP_DIR%\*.dll" >> "%APP_DIR%\logs\debug_env.log"

:: Run the application with full error capture
echo Running application...
"%APP_DIR%\Echelon.exe" > "%APP_DIR%\logs\debug_stdout.log" 2> "%APP_DIR%\logs\debug_stderr.log"
set EXIT_CODE=%ERRORLEVEL%

:: Display the exit code
echo Application exited with code: %EXIT_CODE%
if %EXIT_CODE% NEQ 0 (
    echo Application failed to start
    echo STDOUT:
    type "%APP_DIR%\logs\debug_stdout.log"
    echo.
    echo STDERR:
    type "%APP_DIR%\logs\debug_stderr.log"
)

pause 