"""
This is a setup.py script for packaging the application using py2app
Run with:
    python setup.py py2app
"""

from setuptools import setup
import os
import sys
import platform

# Determine the current platform architecture
current_arch = platform.machine()
print(f"Packaging for architecture: {current_arch}")

# Add all modules in the app directory
# This approach ensures we include all Python modules in your application
packages = ['PyQt5']
includes = ['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets']

# Recursively walk app/ directory to find all Python packages
for root, dirs, files in os.walk('app'):
    if '__pycache__' in dirs:
        dirs.remove('__pycache__')  # Don't visit __pycache__ directories
    
    if '__init__.py' in files:
        # This is a package - add it to our list
        package = root.replace(os.path.sep, '.')
        packages.append(package)
        print(f"Found package: {package}")

APP = ['main.py']
DATA_FILES = [
    ('', ['requirements.txt']),  # Include requirements.txt at the root
]

OPTIONS = {
    'argv_emulation': False,  # Don't use argv emulation
    'packages': packages,
    'includes': includes,
    'iconfile': 'Creator.icns',
    'excludes': ['tkinter', 'numpy', 'scipy', 'pandas', 'matplotlib'],  # Exclude unnecessary large packages
    'plist': {
        'CFBundleName': 'Echelon',
        'CFBundleDisplayName': 'Echelon',
        'CFBundleIdentifier': 'com.cr2creative.echelon',
        'CFBundleShortVersionString': '2.1.0',
        'CFBundleVersion': '2.1.0', 
        'NSHumanReadableCopyright': 'Copyright © 2023-present Craig P. Russo and CR2 Creative. All rights reserved.',
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'CFBundleDocumentTypes': [],
    },
    # Tell py2app to create a better bundle structure that's more compatible with modern macOS
    'site_packages': True,  # Include site-packages in the final bundle
    'strip': True,  # Strip debug symbols to create a smaller app
    'optimize': 2,  # Optimize Python bytecode
    'resources': ['app/assets'],  # Additional resources to include in the bundle
}

setup(
    name='Echelon',
    version='2.1.0',
    description='Smart Folder Templates & Batch File Organizer',
    author='Craig P. Russo',
    author_email='contact@cr2creative.com',
    url='https://www.cr2creative.com',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 