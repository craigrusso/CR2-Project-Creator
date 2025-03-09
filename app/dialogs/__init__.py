# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog window modules
"""

# Check which UI framework is being used
import sys
try:
    # Try to import a PyQt-specific module to see if PyQt is in use
    from PyQt5.QtWidgets import QApplication
    UI_FRAMEWORK = 'pyqt'
except ImportError:
    UI_FRAMEWORK = 'tkinter'

# Import dialog modules based on UI framework
if UI_FRAMEWORK == 'tkinter':
    try:
        # Import Tkinter dialog modules
        from dialog.batch_dialog import BatchDialog
        from dialog.about_dialog import AboutDialog
        from dialog.preferences_dialog import PreferencesDialog
        from dialog.preview_dialog import PreviewDialog
        from dialog.tutorial_dialog import TutorialDialog
        from dialog.template_dialogs import AddTemplateDialog, EditTemplateDialog
    except ImportError:
        # If imports fail, provide empty declarations
        pass
else:
    # PyQt version doesn't need these imports as it uses separate modules
    pass
