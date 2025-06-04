@echo off
echo Rebuilding Echelon with ARM64 fixes...

REM Clean build directories
rmdir /s /q "WIN_BUILD\ARM\build" 2>nul
rmdir /s /q "WIN_BUILD\ARM\dist" 2>nul
mkdir "WIN_BUILD\ARM\build"
mkdir "WIN_BUILD\ARM\dist"

REM Run PyInstaller with the runtime hook
pyinstaller --clean --name Echelon --icon=ICONS\Echelon.ico --windowed --noupx ^
  --runtime-hook="Y:\pyqt6_arm64_hook.py" ^
  --distpath "WIN_BUILD\ARM\dist" --workpath "WIN_BUILD\ARM\build" --noconfirm ^
  --hidden-import json ^
  --hidden-import webbrowser ^
  --hidden-import uuid ^
  --hidden-import requests ^
  --hidden-import packaging ^
  --hidden-import PyQt6.QtCore ^
  --hidden-import PyQt6.QtSvg ^
  --hidden-import PyQt6.QtWidgets ^
  --hidden-import PyQt6.QtGui ^
  --hidden-import logging ^
  --hidden-import logging.handlers ^
  --hidden-import logging.config ^
  --collect-submodules logging ^
  --add-data "app;app" ^
  --add-data "app/assets/css;app/assets/css" ^
  --add-data "app/assets/icons;app/assets/icons" ^
  --add-data "app/assets/bundled_example_templates;app/assets/bundled_example_templates" ^
  --add-data "EULA.txt;." ^
  main.py

echo Build completed. Running application...
cd "WIN_BUILD\ARM\dist\Echelon"
start Echelon.exe

pause
