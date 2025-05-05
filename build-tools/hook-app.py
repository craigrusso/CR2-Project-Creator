# hook-app.py
# This is a PyInstaller hook to collect all the modules in the 'app' package
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all app submodules
hiddenimports = collect_submodules('app')

# Collect all data files
datas = collect_data_files('app') 