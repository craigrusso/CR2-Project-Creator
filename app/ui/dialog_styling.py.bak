#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Enhanced dialog styling for the application.
This file provides specialized dialog classes with consistent styling.
"""

from PyQt6.QtWidgets import QMessageBox, QPushButton, QDialogButtonBox, QInputDialog, QLineEdit, QDialog
from PyQt6.QtCore import Qt, QTimer
from app.ui.color_scheme_pyqt import colors

class StyledMessageBox(QMessageBox):
    """
    A QMessageBox subclass that ensures consistent button styling
    across all platforms and themes, especially for Windows light theme.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set window flag to ensure proper styling
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Schedule this to run after the dialog is created but before it's shown
        QTimer.singleShot(0, self.style_buttons)
    
    def style_buttons(self):
        """Apply consistent styling to all buttons in the message box"""
        # Style the buttons after they've been created
        for button in self.findChildren(QPushButton):
            self.apply_button_style(button)
    
    def apply_button_style(self, button):
        """Apply appropriate style based on button role and text"""
        # Get button text and role
        text = button.text()
        
        # Apply appropriate styling based on button text
        if text in ["Yes", "OK", "&Yes"]:
            # Style "Yes" and "OK" buttons as blue accent buttons
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent']};
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 10px;
                    min-width: 80px;
                    min-height: 22px;
                }}
                QPushButton:hover {{
                    background-color: {colors['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['highlight_darker']};
                }}
            """)
        elif text in ["No", "Cancel", "&No"]:
            # Style "No" and "Cancel" buttons as gray buttons
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    padding: 5px 10px;
                    min-width: 80px;
                    min-height: 22px;
                }}
                QPushButton:hover {{
                    background-color: {colors['hover_bg']};
                    border: 1px solid {colors['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['hover_bg']};
                    color: {colors['highlight_text']};
                }}
            """)
    
    @staticmethod
    def show_question(parent, title, text, informative_text=""):
        """Show a styled question dialog with Yes/No buttons"""
        msgbox = StyledMessageBox(parent)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        if informative_text:
            msgbox.setInformativeText(informative_text)
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        msgbox.setIcon(QMessageBox.Question)
        return msgbox.exec()
    
    @staticmethod
    def show_information(parent, title, text, informative_text=""):
        """Show a styled information dialog with OK button"""
        msgbox = StyledMessageBox(parent)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        if informative_text:
            msgbox.setInformativeText(informative_text)
        msgbox.setStandardButtons(QMessageBox.Ok)
        msgbox.setIcon(QMessageBox.Information)
        return msgbox.exec()
    
    @staticmethod
    def show_warning(parent, title, text, informative_text=""):
        """Show a styled warning dialog with OK button"""
        msgbox = StyledMessageBox(parent)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        if informative_text:
            msgbox.setInformativeText(informative_text)
        msgbox.setStandardButtons(QMessageBox.Ok)
        msgbox.setIcon(QMessageBox.Warning)
        return msgbox.exec()
    
    @staticmethod
    def show_error(parent, title, text, informative_text=""):
        """Show a styled error dialog with OK button"""
        msgbox = StyledMessageBox(parent)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        if informative_text:
            msgbox.setInformativeText(informative_text)
        msgbox.setStandardButtons(QMessageBox.Ok)
        msgbox.setIcon(QMessageBox.Critical)
        return msgbox.exec()

class StyledInputDialog:
    """
    Static class that provides styled input dialogs with consistent button styling
    across all platforms and themes, especially for Windows light theme.
    """
    
    @staticmethod
    def get_text(parent, title, label, text="", modal=True):
        """Show a styled text input dialog with consistent styling"""
        # Create standard input dialog
        dialog = QInputDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextValue(text)
        dialog.setWindowModality(Qt.ApplicationModal if modal else Qt.NonModal)
        
        # Get the buttons after creation using a timer
        # This is necessary because the buttons aren't created until the dialog is shown
        def style_buttons():
            # Apply styling to all QPushButton widgets in the dialog
            for button in dialog.findChildren(QPushButton):
                # Check button text
                if button.text() in ["OK", "&OK"]:
                    button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['accent']};
                            color: white;
                            border: none;
                            border-radius: 3px;
                            padding: 5px 10px;
                            min-width: 80px;
                            min-height: 22px;
                        }}
                        QPushButton:hover {{
                            background-color: {colors['accent_hover']};
                        }}
                        QPushButton:pressed {{
                            background-color: {colors['highlight_darker']};
                        }}
                    """)
                elif button.text() in ["Cancel", "&Cancel"]:
                    button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['card_bg']};
                            color: {colors['text']};
                            border: 1px solid {colors['border']};
                            border-radius: 3px;
                            padding: 5px 10px;
                            min-width: 80px;
                            min-height: 22px;
                        }}
                        QPushButton:hover {{
                            background-color: {colors['hover_bg']};
                            border: 1px solid {colors['accent']};
                        }}
                        QPushButton:pressed {{
                            background-color: {colors['hover_bg']};
                            color: {colors['highlight_text']};
                        }}
                    """)
        
        # Apply styling after dialog is created but before it's shown
        QTimer.singleShot(0, style_buttons)
        
        # Execute dialog and return results
        if dialog.exec() == QDialog.Accepted:
            return dialog.textValue(), True
        else:
            return "", False
            
    @staticmethod
    def get_int(parent, title, label, value=0, min_val=-2147483647, max_val=2147483647, step=1, modal=True):
        """Show a styled integer input dialog with consistent styling"""
        # Create standard input dialog
        dialog = QInputDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setIntValue(value)
        dialog.setIntMinimum(min_val)
        dialog.setIntMaximum(max_val)
        dialog.setIntStep(step)
        dialog.setInputMode(QInputDialog.IntInput)
        dialog.setWindowModality(Qt.ApplicationModal if modal else Qt.NonModal)
        
        # Style buttons using the same technique as in get_text
        def style_buttons():
            for button in dialog.findChildren(QPushButton):
                if button.text() in ["OK", "&OK"]:
                    button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['accent']};
                            color: white;
                            border: none;
                            border-radius: 3px;
                            padding: 5px 10px;
                            min-width: 80px;
                            min-height: 22px;
                        }}
                        QPushButton:hover {{
                            background-color: {colors['accent_hover']};
                        }}
                        QPushButton:pressed {{
                            background-color: {colors['highlight_darker']};
                        }}
                    """)
                elif button.text() in ["Cancel", "&Cancel"]:
                    button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {colors['card_bg']};
                            color: {colors['text']};
                            border: 1px solid {colors['border']};
                            border-radius: 3px;
                            padding: 5px 10px;
                            min-width: 80px;
                            min-height: 22px;
                        }}
                        QPushButton:hover {{
                            background-color: {colors['hover_bg']};
                            border: 1px solid {colors['accent']};
                        }}
                        QPushButton:pressed {{
                            background-color: {colors['hover_bg']};
                            color: {colors['highlight_text']};
                        }}
                    """)
                    
        # Apply styling after dialog creation
        QTimer.singleShot(0, style_buttons)
        
        # Execute dialog and return results
        if dialog.exec() == QDialog.Accepted:
            return dialog.intValue(), True
        else:
            return 0, False 