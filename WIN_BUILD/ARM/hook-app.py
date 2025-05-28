
# hook-app.py - PyInstaller hook for Windows ARM64
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

# Collect all data files from the app module
datas = collect_data_files('app')

# Add submodules for app
hiddenimports = collect_submodules('app')

# Add submodules for logging
hiddenimports.extend(collect_submodules('logging'))
