from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all app modules
hiddenimports = collect_submodules('app')

# Collect all data files from app
datas = collect_data_files('app')

# Add specific PyQt6 modules
hiddenimports.extend([
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.QtNetwork',
    'PyQt6.uic',
    'PyQt6.QtPrintSupport',
    'json',
    'webbrowser',
    'shutil',
    'logging',
    'platform',
    'struct',
    'subprocess',
    'faulthandler',
    'ctypes',
    'datetime',
    'os.path',
]) 