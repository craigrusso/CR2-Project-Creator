from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Add standard library modules that might be missing
hiddenimports = [
    'webbrowser',
    'http.cookies',
    'http.client',
    'urllib.request',
    'urllib.parse',
    'urllib.error',
    'urllib.robotparser',
    'html',
    'html.parser',
    'html.entities',
    'xml.etree',
    'xml.etree.ElementTree',
    'json',
    'email',
    'csv',
    'logging',
    'fnmatch',
    'pathlib',
    'shutil',
    'tempfile',
    'platform',
    'subprocess',
    'threading',
    'time',
    'os.path',
    're',
    'random'
]

# Collect all data files
datas = collect_data_files('app')
