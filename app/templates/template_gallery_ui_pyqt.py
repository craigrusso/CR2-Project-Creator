#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Template Gallery UI - PyQt Implementation
"""

import os
import json
import platform
import time
import random
import shutil
import sys
import sip
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QFileDialog, QMessageBox,
                           QInputDialog, QMenu, QAction, QApplication, QComboBox, QSizePolicy,
                           QSlider, QButtonGroup, QToolButton, QLineEdit, QSplitter, QRadioButton, QStyle,
                           QDialog, QStackedWidget, QListWidgetItem, QListWidget, QTextEdit)
from PyQt5.QtCore import (Qt, pyqtSignal, QSize, QPoint, QEvent, QMimeData, 
                        QByteArray, QTimer, QObject, QRect)
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QCursor, QDrag, QPixmap, QPainter, QFontMetrics

from app.ui.color_scheme_pyqt import colors, get_color, BUTTON_STYLE, ACCENT_BUTTON_STYLE, LABEL_STYLE, COMBOBOX_STYLE
from app.ui.ui_components_pyqt import ScrollableFrame, CardFrame, ToolTip, SearchBox, UI_FONT
from app.templates.template_manager import TemplateManager
from app.templates.components import TemplateCard, CARD_NORMAL, CARD_HOVER, CARD_SELECTED
from app.dialogs.dialog_windows_pyqt import show_edit_template, show_manage_templates
from app.templates.template_gallery_refactored import TemplateGallery
from app.templates.gallery_events import GalleryEvents, StyledItemDialog

# Constants for styling
BLUE_HIGHLIGHT = colors["highlight_bg"]
CARD_NORMAL = colors["card_bg"]
CARD_HOVER = colors["hover_bg"]
CARD_SELECTED = colors["highlight_bg"]

# System font to use throughout the app
GALLERY_FONT = UI_FONT

class TemplateFolderCard(QFrame):
    """Template folder card widget for displaying a folder in the gallery"""
    
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)  # Re-enable double-click
    renameRequested = pyqtSignal(str)
    renameDone = pyqtSignal(str, str)  # Signal for when renaming is done (old_name, new_name)
    
    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.setInterval(250)  # 250ms to differentiate single from double click
        self.click_timer.timeout.connect(self._handle_single_click)
        self.click_pending = False
        self.editing = False  # Track if we're currently editing the name
        
        # Setup styling
        self.setFrameShape(QFrame.NoFrame)  # No frame/container around the folder
        self.setFixedSize(120, 120)  # Make even smaller for higher density
        self.setCursor(Qt.PointingHandCursor)
        
        # Enable drop functionality
        self.setAcceptDrops(True)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 0)  # Minimal margins
        self.layout.setSpacing(0)  # No spacing between elements
        
        # Icon - Make folder icon larger and more distinct
        self.icon_layout = QHBoxLayout()
        self.icon_layout.setAlignment(Qt.AlignCenter)
        self.icon_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Folder icon - more obvious folder appearance
        self.icon_label = QLabel("📁")  # Using a folder emoji
        self.icon_label.setFont(QFont(GALLERY_FONT, 40))  # Smaller font to match smaller card
        self.icon_label.setStyleSheet("color: goldenrod; background: transparent; padding-bottom: 0;")
        self.icon_layout.addWidget(self.icon_label)
        self.layout.addLayout(self.icon_layout)
        
        # Folder name - simpler display directly under the icon
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(GALLERY_FONT, 12))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: white; background: transparent; margin-top: -8px;")  # Force white color
        self.title.setWordWrap(True)
        self.title.setCursor(Qt.IBeamCursor)  # Change cursor to indicate text editability
        self.title.setToolTip("Click the name to rename")
        self.title.installEventFilter(self)  # Install event filter for the title specifically
        self.layout.addWidget(self.title)
        
        # Create the edit widget but don't add it to layout yet
        self.name_edit = QLineEdit(folder_name)
        self.name_edit.setFont(QFont(GALLERY_FONT, 12))
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.setStyleSheet("color: white; background: rgba(60, 60, 60, 0.8); border: 1px solid gray; border-radius: 3px;")
        self.name_edit.editingFinished.connect(self._finish_rename)
        self.name_edit.hide()  # Hide by default
        self.layout.addWidget(self.name_edit)
        
        # Install event filter for mouse events
        self.installEventFilter(self)
        self._update_styling()
    
    def _handle_single_click(self):
        """Handle single click after timer expires"""
        if self.click_pending:
            self.click_pending = False
            self.clicked.emit(self.folder_name)
    
    # Remove the _on_enter_button_clicked method
    
    # Implement drag and drop events
    def dragEnterEvent(self, event):
        """Handle when a drag enters the folder card"""
        # Only accept if it's dragging a template (text or JSON data)
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            print(f"[DEBUG] DragEnter: Drag entered folder '{self.folder_name}'")
            # Visual feedback for valid drag target
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["accent_hover"]};
                    border: 2px dashed {colors["accent"]};
                    border-radius: 8px;
                }}
                QLabel {{
                    color: {colors["highlight_text"]};
                }}
            """)
            self.icon_label.setStyleSheet("color: white; background: transparent;")
            # Ensure we accept the drag action
            event.accept()
            event.acceptProposedAction()
        else:
            print(f"[DEBUG] DragEnter: Rejected drag for folder '{self.folder_name}' - invalid mime data")
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle when drag moves over the folder card"""
        # Continue accepting the drag as it moves
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            event.accept()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle when a template is dropped on the folder"""
        try:
            # Extract template name from the drag data
            mime_data = event.mimeData()
            if mime_data.hasText():
                text_data = mime_data.text()
                
                # Check if this contains multiple templates (newline-separated)
                has_multi_data = '\n' in text_data
                is_multi_drag = has_multi_data or mime_data.hasFormat("application/x-template-multi-drag")
                
                if is_multi_drag and has_multi_data:
                    # This is a drop of multiple templates
                    template_names = text_data.strip().split('\n')
                    template_count = len(template_names)
                    print(f"[DEBUG] Card: Handling multi-template drop of {template_count} templates")
                    
                    # Move each template to this folder
                    for template_name in template_names:
                        if template_name.strip():  # Skip empty names
                            self._add_template_to_folder(template_name)
                    
                    # Show success message
                    if hasattr(self.app, 'show_status_message'):
                        self.app.show_status_message(f"Added {template_count} templates to folder '{self.folder_name}'", "info")
                    
                    # Refresh the gallery
                    if hasattr(self.parent(), 'populate_gallery'):
                        self.parent().populate_gallery(force_refresh=True)
                        
                    event.acceptProposedAction()
                    return True
                else:
                    # Single template drop
                    template_name = text_data
                    result = self._add_template_to_folder(template_name)
                    
                    if result:
                        print(f"[DEBUG] Card: Successfully moved template")
                        # Show success message in status bar instead of popup
                        if hasattr(self.app, 'show_status_message'):
                            print(f"[DEBUG] Card: Showing status message")
                            self.app.show_status_message(f"Template '{template_name}' added to folder '{self.folder_name}'", "info")
                        else:
                            # Fallback if status bar method not available
                            print(f"[DEBUG] Card: Status message method not available")
                            print(f"Template '{template_name}' added to folder '{self.folder_name}'")
                        
                        # Refresh the gallery to make the template disappear from the current view
                        print(f"[DEBUG] Card: Refreshing gallery")
                        if hasattr(self.parent(), 'populate_gallery'):
                            # Force a complete refresh when adding templates to folders
                            self.parent().populate_gallery(force_refresh=True)
                    else:
                        print(f"[DEBUG] Card: Failed to move template")
                    
                    event.acceptProposedAction()
                    return result
        except Exception as e:
            print(f"[DEBUG] Card: Error in drop event: {e}")
            import traceback
            traceback.print_exc()
        
        event.ignore()
        return False
        
    def _add_template_to_folder(self, template_name):
        """Add a template to this folder"""
        try:
            # Determine actual template name (handle special prefix case)
            actual_template_name = template_name
            if ">" in template_name:
                parts = template_name.split(">", 1)
                if len(parts) > 1:
                    # Get the actual template name part
                    actual_template_name = parts[1].strip()
            
            print(f"[DEBUG] Card: Adding template '{actual_template_name}' to folder '{self.folder_name}'")
            
            # Find the template manager
            if not hasattr(self.app, 'template_manager'):
                print("[DEBUG] Card: No template manager available")
                return False
                
            # Get the folder dictionary
            if not hasattr(self.app.template_manager, 'folders'):
                print("[DEBUG] Card: No folders dictionary available")
                return False
                
            # Get or create the folder entry
            if self.folder_name not in self.app.template_manager.folders:
                self.app.template_manager.folders[self.folder_name] = []
                
            # Add the template to the folder if not already there
            if actual_template_name not in self.app.template_manager.folders[self.folder_name]:
                self.app.template_manager.folders[self.folder_name].append(actual_template_name)
                
                # Save the folders data
                if hasattr(self.app.template_manager, 'save_folders'):
                    self.app.template_manager.save_folders()
                    
                return True
            else:
                print(f"[DEBUG] Card: Template '{actual_template_name}' already in folder '{self.folder_name}'")
                return False
        except Exception as e:
            print(f"[DEBUG] Card: Error adding template to folder: {e}")
            return False
    
    def eventFilter(self, obj, event):
        """Handle mouse events for hover effects only now"""
        try:
            # Check if the widget still exists and is valid
            if not obj or sip.isdeleted(obj):
                return False
                
            if obj == self:
                if event.type() == QEvent.Enter:
                    self._on_hover_enter()
                elif event.type() == QEvent.Leave:
                    self._on_hover_leave()
                    
            elif obj == self.title and hasattr(self, 'title'):
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    # When clicking directly on the title, start inline editing
                    self._start_rename()
                    return True  # Stop event propagation
                    
            return super().eventFilter(obj, event)
        except Exception as e:
            print(f"Error in event filter: {e}")
            return False
    
    def _on_hover_enter(self):
        self.hover = True
        self._update_styling()
    
    def _on_hover_leave(self):
        self.hover = False
        self._update_styling()
    
    def set_selected(self, selected):
        self.selected = selected
        self._update_styling()
    
    def _update_styling(self):
        """Update folder card styling based on state"""
        if self.selected:
            # Selected style - file browser selection highlight
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['accent']};
                    border: none;
                    border-radius: 6px;
                }}
                QLabel {{
                    color: white;
                    background: transparent;
                }}
            """)
            self.icon_label.setStyleSheet("color: white; background: transparent;")
        elif self.hover:
            # Hover style - more subtle than before
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['highlight_bg']};
                    border: none;
                    border-radius: 6px;
                }}
                QLabel {{
                    color: white;
                    background: transparent;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['accent']}; background: transparent;")
        else:
            # Default style - cleaner, more minimal
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                }}
                QLabel {{
                    color: white;
                    background: transparent;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent;")

    def leaveEvent(self, event):
        """Explicit leave event handler to ensure hover state is reset"""
        # Force hover state to False
        self.hover = False
        
        # Explicit styling reset
        if self.property("row_type") == "odd":
            bg_color = colors["card_bg"]  # Darker for odd rows
        else:
            bg_color = colors["bg"]  # Lighter for even rows
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 0px;
            }}
        """)
        
        # Complete update of all labels
        self._update_styling()
        
        # Call the base class method using explicit QFrame.leaveEvent instead of super()
        QFrame.leaveEvent(self, event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events to update hover state"""
        # Only set hover state if the mouse is actually over the widget
        rect = self.rect()
        if rect.contains(event.pos()):
            if not self.hover:
                self.hover = True
                self._update_styling()
        else:
            if self.hover:
                self.hover = False
                self._update_styling()
        QFrame.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        """Handle mouse press directly instead of through event filter"""
        if event.button() == Qt.LeftButton:
            # Handle clicks on the title separately
            if hasattr(self, 'title') and self.title.geometry().contains(event.pos()):
                try:
                    self.renameRequested.emit(self.folder_name)
                    event.accept()
                except Exception as e:
                    print(f"Error when requesting rename: {e}")
            else:
                # Start timer to wait for possible double click
                self.click_pending = True
                self.click_timer.start()
                event.accept()
        # Do not call super().mousePressEvent(event) as it may lead to crashes
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click directly instead of through event filter"""
        if event.button() == Qt.LeftButton:
            # Cancel any pending single click
            self.click_pending = False
            self.click_timer.stop()
            
            # Only emit double click if not clicking on title
            if hasattr(self, 'title') and not self.title.geometry().contains(event.pos()):
                try:
                    self.doubleClicked.emit(self.folder_name)
                    # Mark event as accepted
                    event.accept()
                except Exception as e:
                    print(f"Error when double-clicking folder: {e}")
        # Do not call super().mouseDoubleClickEvent(event) as it may lead to crashes

    def _start_rename(self):
        """Start inline renaming of folder"""
        try:
            print(f"Starting rename for folder: {self.folder_name}")
            # Check if this is a default folder that cannot be renamed
            if self.folder_name in ["General", "Development", "Business"]:
                print(f"Cannot rename default folder: {self.folder_name}")
                if hasattr(self.app, 'show_message'):
                    self.app.show_message(f"'{self.folder_name}' is a default folder and cannot be renamed.")
                else:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "Error", f"'{self.folder_name}' is a default folder and cannot be renamed.")
                return
                
            # Switch to edit mode
            print("Switching to edit mode")
            self.editing = True
            
            # Hide label, show edit field
            self.title.hide()
            self.name_edit.setText(self.folder_name)
            self.name_edit.show()
            self.name_edit.setFocus()
            self.name_edit.selectAll()
            print("Rename UI setup complete")
        except Exception as e:
            print(f"Error in _start_rename: {e}")
            import traceback
            traceback.print_exc()
        
    def _finish_rename(self):
        """Finish inline renaming and apply the change"""
        try:
            print("Finishing rename")
            if not self.editing:
                print("Not in editing mode, ignoring")
                return
                
            self.editing = False
            new_name = self.name_edit.text().strip()
            print(f"New name: '{new_name}'")
            
            # Hide edit field, show label
            self.name_edit.hide()
            self.title.show()
            
            # If name is empty or unchanged, do nothing
            if not new_name or new_name == self.folder_name:
                print("Name unchanged or empty, not applying")
                return
                
            # Emit signal with old and new name
            print(f"Emitting renameDone signal with old_name='{self.folder_name}', new_name='{new_name}'")
            self.renameDone.emit(self.folder_name, new_name)
            print("Rename signal emitted")
        except Exception as e:
            print(f"Error in _finish_rename: {e}")
            import traceback
            traceback.print_exc()

    def keyPressEvent(self, event):
        """Handle escape key to cancel editing"""
        if self.editing and event.key() == Qt.Key_Escape:
            self.editing = False
            self.name_edit.hide()
            self.title.show()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right click"""
        # Create context menu
        context_menu = QMenu(self)
        
        # Add rename action
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self._start_rename)
        context_menu.addAction(rename_action)
        
        # Add delete action (unless it's a default folder)
        if self.folder_name not in ["General", "Development", "Business"]:
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self._delete_folder())
            context_menu.addAction(delete_action)
        
        # Show the menu
        context_menu.exec_(event.globalPos())
    
    def _delete_folder(self):
        """Delete this folder"""
        if not self.app:
            return
            
        # Don't allow deleting default folders
        if self.folder_name in ["General", "Development", "Business"]:
            QMessageBox.warning(self, "Error", f"'{self.folder_name}' is a default folder and cannot be deleted.")
            return
            
        # Delete folder without confirmation dialog
        success = self.app.template_manager.delete_folder(self.folder_name)
        
        if success:
            # Refresh the gallery
            parent = self.parent()
            if parent and hasattr(parent, 'populate_gallery'):
                parent.populate_gallery()
        else:
            QMessageBox.warning(self, "Error", f"Failed to delete folder '{self.folder_name}'.")

class TemplateFolderListItem(QFrame):
    """Template folder list item widget for displaying a folder in list view"""
    
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)  # Re-enable double-click
    renameRequested = pyqtSignal(str)
    renameDone = pyqtSignal(str, str)  # Signal for when renaming is done (old_name, new_name)
    
    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        self.editing = False  # Track editing state
        
        # Setup styling
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(36)  # Fixed height for compact list view
        self.setCursor(Qt.PointingHandCursor)
        
        # Click handling
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.setInterval(250)  # 250ms to differentiate single from double click
        self.click_timer.timeout.connect(self._handle_single_click)
        self.click_pending = False
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)  # More padding
        
        # Folder icon
        self.icon_label = QLabel("📁")  # Using a folder emoji
        self.icon_label.setFont(QFont(GALLERY_FONT, 18))
        self.icon_label.setStyleSheet("color: goldenrod; background: transparent;")
        self.layout.addWidget(self.icon_label)
        
        # Folder name
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(GALLERY_FONT, 12))
        self.title.setStyleSheet("color: white; background: transparent;")
        self.title.setCursor(Qt.IBeamCursor)  # Change cursor to indicate text editability
        self.title.setToolTip("Click the name to rename")
        self.title.installEventFilter(self)  # Install event filter for the title
        self.layout.addWidget(self.title, 1)  # Give it stretch factor
        
        # Create the edit widget but don't add it to layout yet
        self.name_edit = QLineEdit(folder_name)
        self.name_edit.setFont(QFont(GALLERY_FONT, 12))
        self.name_edit.setStyleSheet("color: white; background: rgba(60, 60, 60, 0.8); border: 1px solid gray; border-radius: 3px;")
        self.name_edit.editingFinished.connect(self._finish_rename)
        self.name_edit.hide()  # Hide by default
        self.layout.addWidget(self.name_edit, 1)  # Same stretch as title
        
        # Install event filter for mouse events
        self.installEventFilter(self)
        self._update_styling()
    
    def _handle_single_click(self):
        """Handle single click after timer expires"""
        if self.click_pending:
            self.click_pending = False
            self.clicked.emit(self.folder_name)
    
    # Remove the _on_enter_button_clicked method
    
    # Implement drag and drop events
    def dragEnterEvent(self, event):
        """Handle when a drag enters the folder list item"""
        # Only accept if it's dragging a template (text or JSON data)
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            print(f"[DEBUG] DragEnter: Drag entered folder list item '{self.folder_name}'")
            # Visual feedback for valid drag target
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["accent_hover"]};
                    border: 2px dashed {colors["accent"]};
                    border-radius: 5px;
                }}
                QLabel {{
                    color: {colors["highlight_text"]};
                }}
            """)
            # Force update
            self.update()
            # Ensure we accept the drag action
            event.accept()
            event.acceptProposedAction()
        else:
            print(f"[DEBUG] DragEnter: Rejected drag for folder list item '{self.folder_name}' - invalid mime data")
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle when drag moves over the folder list item"""
        # Continue accepting the drag as it moves
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            event.accept()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle when a drag leaves the folder list item"""
        # Reset appearance when drag leaves
        self._update_styling()
        event.accept()

    def dropEvent(self, event):
        """Handle when a template is dropped on the folder list item"""
        try:
            # Extract template name from the drag data
            mime_data = event.mimeData()
            if mime_data.hasText():
                text_data = mime_data.text()
                
                # Check if this contains multiple templates (newline-separated)
                has_multi_data = '\n' in text_data
                is_multi_drag = has_multi_data or mime_data.hasFormat("application/x-template-multi-drag")
                
                if is_multi_drag and has_multi_data:
                    # This is a drop of multiple templates
                    template_names = text_data.strip().split('\n')
                    template_count = len(template_names)
                    print(f"[DEBUG] ListItem: Handling multi-template drop of {template_count} templates")
                    
                    # Move each template to this folder
                    for template_name in template_names:
                        if template_name.strip():  # Skip empty names
                            self._add_template_to_folder(template_name)
                    
                    # Show success message
                    if hasattr(self.app, 'show_status_message'):
                        self.app.show_status_message(f"Added {template_count} templates to folder '{self.folder_name}'", "info")
                    
                    # Refresh the gallery
                    if hasattr(self.parent().parent(), 'populate_gallery'):
                        self.parent().parent().populate_gallery(force_refresh=True)
                        
                    event.acceptProposedAction()
                    return True
                else:
                    # Single template drop
                    template_name = text_data
                    result = self._add_template_to_folder(template_name)
                    
                    if result:
                        print(f"[DEBUG] ListItem: Successfully moved template")
                        # Show status message instead of popup
                        if hasattr(self.app, 'show_status_message'):
                            print(f"[DEBUG] ListItem: Showing status message")
                            self.app.show_status_message(f"Template '{template_name}' added to folder '{self.folder_name}'", "info")
                        else:
                            # Fallback if status bar method not available
                            print(f"[DEBUG] ListItem: Status message method not available")
                            print(f"Template '{template_name}' added to folder '{self.folder_name}'")
                        
                        # Refresh the gallery to make the template disappear from current view
                        print(f"[DEBUG] ListItem: Refreshing gallery")
                        if hasattr(self.parent().parent(), 'populate_gallery'):
                            # Force a complete refresh when adding templates to folders
                            self.parent().parent().populate_gallery(force_refresh=True)
                    else:
                        print(f"[DEBUG] ListItem: Failed to move template")
                        
                    event.acceptProposedAction()
                    return result
        except Exception as e:
            print(f"[DEBUG] ListItem: Error in drop event: {e}")
            import traceback
            traceback.print_exc()
            
        event.ignore()
        return False
        
    def _add_template_to_folder(self, template_name):
        """Add a template to this folder"""
        try:
            # Determine actual template name (handle special prefix case)
            actual_template_name = template_name
            if ">" in template_name:
                parts = template_name.split(">", 1)
                if len(parts) > 1:
                    # Get the actual template name part
                    actual_template_name = parts[1].strip()
            
            print(f"[DEBUG] ListItem: Adding template '{actual_template_name}' to folder '{self.folder_name}'")
            
            # Find the template manager
            if not hasattr(self.app, 'template_manager'):
                print("[DEBUG] ListItem: No template manager available")
                return False
                
            # Get the folder dictionary
            if not hasattr(self.app.template_manager, 'folders'):
                print("[DEBUG] ListItem: No folders dictionary available")
                return False
                
            # Get or create the folder entry
            if self.folder_name not in self.app.template_manager.folders:
                self.app.template_manager.folders[self.folder_name] = []
                
            # Add the template to the folder if not already there
            if actual_template_name not in self.app.template_manager.folders[self.folder_name]:
                self.app.template_manager.folders[self.folder_name].append(actual_template_name)
                
                # Save the folders data
                if hasattr(self.app.template_manager, 'save_folders'):
                    self.app.template_manager.save_folders()
                    
                return True
            else:
                print(f"[DEBUG] ListItem: Template '{actual_template_name}' already in folder '{self.folder_name}'")
                return False
        except Exception as e:
            print(f"[DEBUG] ListItem: Error adding template to folder: {e}")
            return False
    
    def eventFilter(self, obj, event):
        """Filter events for mouse hover only now"""
        try:
            # Check if the widget still exists and is valid
            if not obj or sip.isdeleted(obj):
                return False
                
            if obj is self:
                if event.type() == QEvent.Enter:
                    if not self.hover:  # Only update if hover state changes
                        self.hover = True
                        self._update_styling()
                    return True  # Return True to handle the event completely
                elif event.type() == QEvent.Leave:
                    if self.hover:  # Only update if hover state changes
                        self.hover = False
                        
                        # Explicit reset to the correct background color
                        if self.property("row_type") == "odd":
                            bg_color = colors["card_bg"]  # Darker for odd rows
                        else:
                            bg_color = colors["bg"]  # Lighter for even rows
                            
                        self.setStyleSheet(f"""
                            QFrame {{
                                background-color: {bg_color};
                                border: none;
                                border-radius: 0px;
                            }}
                        """)
                        
                        self._update_styling()
                    return True  # Return True to handle the event completely
            elif obj is self.title and hasattr(self, 'title'):
                if event.type() == QEvent.MouseButtonPress:
                    # When clicking directly on the title, start inline editing
                    self._start_rename()
                    return True  # Stop event propagation
                    
            return super().eventFilter(obj, event)
        except Exception as e:
            print(f"Error in list item event filter: {e}")
            return False
    
    def _on_hover_enter(self):
        self.hover = True
        self._update_styling()
    
    def _on_hover_leave(self):
        self.hover = False
        self._update_styling()
    
    def set_selected(self, selected):
        self.selected = selected
        self._update_styling()
    
    def _update_styling(self):
        """Update the styling based on current state - macOS style"""
        if self.selected:
            # Selected style (blue background, white text)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["highlight_bg"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            # Update other labels safely
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet(f"color: {colors['highlight_text']}; font-weight: bold; background: transparent;")
        elif self.hover:
            # Hover style (slightly lighter background)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["hover_bg"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            # Update other labels safely
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet(f"color: white; font-weight: bold; background: transparent;")
        else:
            # Normal style - use clean macOS style (no borders, alternate row colors for list)
            # Use proper colors based on row type for consistent appearance
            if self.property("row_type") == "odd":
                bg_color = colors["card_bg"]  # Darker for odd rows
            else:
                bg_color = colors["bg"]  # Lighter for even rows
                
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            # Update other labels safely
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet("color: white; font-weight: bold; background: transparent;")

    def leaveEvent(self, event):
        """Explicit leave event handler to ensure hover state is reset when mouse exits the widget"""
        # Force hover state to False
        self.hover = False
        
        # Explicit styling reset
        if self.property("row_type") == "odd":
            bg_color = colors["card_bg"]  # Darker for odd rows
        else:
            bg_color = colors["bg"]  # Lighter for even rows
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 0px;
            }}
        """)
        
        # Complete update of all labels
        self._update_styling()
        
        # Call the base class method using explicit QFrame.leaveEvent instead of super()
        QFrame.leaveEvent(self, event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events to update hover state"""
        # Only set hover state if the mouse is actually over the widget
        rect = self.rect()
        if rect.contains(event.pos()):
            if not self.hover:
                self.hover = True
                self._update_styling()
        else:
            if self.hover:
                self.hover = False
                self._update_styling()
        QFrame.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        """Handle mouse press directly instead of through event filter"""
        if event.button() == Qt.LeftButton:
            # Handle clicks on the title separately
            if hasattr(self, 'title') and self.title.geometry().contains(event.pos()):
                try:
                    self.renameRequested.emit(self.folder_name)
                    event.accept()
                except Exception as e:
                    print(f"Error when requesting rename: {e}")
            else:
                # Start timer to wait for possible double click
                self.click_pending = True
                self.click_timer.start()
                event.accept()
        # Do not call super().mousePressEvent(event) as it may lead to crashes
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click directly instead of through event filter"""
        if event.button() == Qt.LeftButton:
            # Cancel any pending single click
            self.click_pending = False
            self.click_timer.stop()
            
            # Only emit double click if not clicking on title
            if hasattr(self, 'title') and not self.title.geometry().contains(event.pos()):
                try:
                    self.doubleClicked.emit(self.folder_name)
                    # Mark event as accepted
                    event.accept()
                except Exception as e:
                    print(f"Error when double-clicking folder: {e}")
        # Do not call super().mouseDoubleClickEvent(event) as it may lead to crashes

    def _start_rename(self):
        """Start inline renaming of folder"""
        try:
            print(f"Starting rename for folder: {self.folder_name}")
            # Check if this is a default folder that cannot be renamed
            if self.folder_name in ["General", "Development", "Business"]:
                print(f"Cannot rename default folder: {self.folder_name}")
                if hasattr(self.app, 'show_message'):
                    self.app.show_message(f"'{self.folder_name}' is a default folder and cannot be renamed.")
                else:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "Error", f"'{self.folder_name}' is a default folder and cannot be renamed.")
                return
                
            # Switch to edit mode
            print("Switching to edit mode")
            self.editing = True
            
            # Hide label, show edit field
            self.title.hide()
            self.name_edit.setText(self.folder_name)
            self.name_edit.show()
            self.name_edit.setFocus()
            self.name_edit.selectAll()
            print("Rename UI setup complete")
        except Exception as e:
            print(f"Error in _start_rename: {e}")
            import traceback
            traceback.print_exc()
        
    def _finish_rename(self):
        """Finish inline renaming and apply the change"""
        try:
            print("Finishing rename")
            if not self.editing:
                print("Not in editing mode, ignoring")
                return
                
            self.editing = False
            new_name = self.name_edit.text().strip()
            print(f"New name: '{new_name}'")
            
            # Hide edit field, show label
            self.name_edit.hide()
            self.title.show()
            
            # If name is empty or unchanged, do nothing
            if not new_name or new_name == self.folder_name:
                print("Name unchanged or empty, not applying")
                return
                
            # Emit signal with old and new name
            print(f"Emitting renameDone signal with old_name='{self.folder_name}', new_name='{new_name}'")
            self.renameDone.emit(self.folder_name, new_name)
            print("Rename signal emitted")
        except Exception as e:
            print(f"Error in _finish_rename: {e}")
            import traceback
            traceback.print_exc()

    def keyPressEvent(self, event):
        """Handle escape key to cancel editing"""
        if self.editing and event.key() == Qt.Key_Escape:
            self.editing = False
            self.name_edit.hide()
            self.title.show()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right click"""
        # Create context menu
        context_menu = QMenu(self)
        
        # Add rename action
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self._start_rename)
        context_menu.addAction(rename_action)
        
        # Add delete action (unless it's a default folder)
        if self.folder_name not in ["General", "Development", "Business"]:
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self._delete_folder())
            context_menu.addAction(delete_action)
        
        # Show the menu
        context_menu.exec_(event.globalPos())
    
    def _delete_folder(self):
        """Delete this folder"""
        if not self.app:
            return
            
        # Don't allow deleting default folders
        if self.folder_name in ["General", "Development", "Business"]:
            QMessageBox.warning(self, "Error", f"'{self.folder_name}' is a default folder and cannot be deleted.")
            return
            
        # Delete folder without confirmation dialog
        success = self.app.template_manager.delete_folder(self.folder_name)
        
        if success:
            # Refresh the gallery
            parent = self.parent()
            if parent and hasattr(parent, 'populate_gallery'):
                parent.populate_gallery()
        else:
            QMessageBox.warning(self, "Error", f"Failed to delete folder '{self.folder_name}'.")

class TemplateListItem(QFrame):
    """Template list item widget for displaying a template in list view"""
    
    clicked = pyqtSignal(object)
    doubleClicked = pyqtSignal(object)  # Add signal for double-click
    editRequested = pyqtSignal(str)     # Signal for edit request
    deleteRequested = pyqtSignal(str)   # Signal for delete request
    moveToFolderRequested = pyqtSignal(str, str)  # Signal for move to folder request
    
    def __init__(self, gallery, template=None, app=None):
        super().__init__()
        self.gallery = gallery
        self.template = template
        self.app = app
        self.selected = False
        self.multi_selected = False
        self.hover = False  # Add hover state
        self.is_odd_row = False
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background-color: transparent; border: none;")
        
        # Set up layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(22, 22)
        self.icon_label.setStyleSheet(f"color: {colors['accent']}; background: transparent;")
        # Use document icon for templates
        self.icon_label.setText("📄")
        layout.addWidget(self.icon_label)
        
        # Name label
        self.name_label = QLabel()
        self.name_label.setStyleSheet(f"color: {colors['primary_text']}; background: transparent;")
        
        # Ensure name label gets priority in sizing
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_label, 1)  # Give it stretch priority
        
        # Format the creation date (fallback to current time if not available)
        created_timestamp = template.get('created', time.time()) if template else time.time()
        created_date_str = self._format_timestamp(created_timestamp)
        
        # Create the created date label
        self.created_date_label = QLabel(created_date_str)
        self.created_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.created_date_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        self.created_date_label.setFixedWidth(130)  # Fixed width to prevent resizing issues
        layout.addWidget(self.created_date_label)
        
        # Format the modified date (fallback to creation date if not available)
        modified_timestamp = template.get('modified', created_timestamp) if template else time.time()
        modified_date_str = self._format_timestamp(modified_timestamp)
        
        # Create the modified date label
        self.modified_date_label = QLabel(modified_date_str)
        self.modified_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.modified_date_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        self.modified_date_label.setFixedWidth(130)  # Fixed width to prevent resizing issues
        layout.addWidget(self.modified_date_label)
        
        # Set fixed height for the list item
        self.setFixedHeight(40)
        
        # Load template data
        if template:
            self._load_template_data(template)
        
        # Connect signals for hover effects
        self.installEventFilter(self)

    def _format_timestamp(self, timestamp):
        """Format a timestamp into a readable date string"""
        try:
            if isinstance(timestamp, (int, float)):
                # Convert timestamp to datetime
                dt = datetime.datetime.fromtimestamp(timestamp)
                # Format as YYYY-MM-DD HH:MM
                return dt.strftime("%Y-%m-%d %H:%M")
            return "Unknown"
        except Exception as e:
            print(f"Error formatting timestamp: {e}")
            return "Unknown"
    
    def mousePressEvent(self, event):
        """Handle mouse press events - emit clicked signal with template data"""
        # Print debug statement
        print(f"⭐ List item clicked for template: {self.template.get('name', 'Unknown')}")
        
        # Emit the clicked signal with the template data
        self.clicked.emit(self.template)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events - emit doubleClicked signal with template data"""
        self.doubleClicked.emit(self.template)
        super().mouseDoubleClickEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter events - update hover state"""
        self.hover = True
        self._update_styling()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events - update hover state"""
        self.hover = False
        self._update_styling()
        super().leaveEvent(event)
    
    def set_selected(self, selected):
        """Set the selected state of the list item"""
        # Debug output
        print(f"⭐ TemplateListItem.set_selected({selected}) called for {self.template.get('name', 'Unknown')}")
        
        # Track changed state 
        old_state = self.selected
        self.selected = selected
        
        # Update styling
        self._update_styling()
        
        # Debug output
        print(f"⭐ TemplateListItem selection changed: {old_state} -> {selected} for {self.template.get('name', 'Unknown')}")
    
    def _update_styling(self):
        """Update styling based on selection and hover state"""
        if self.selected:
            # Selected state
            self.setStyleSheet(f"background-color: {colors['highlight_bg']}; border-radius: 4px;")
            self.name_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent; font-weight: bold;")
            self.icon_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            self.created_date_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            self.modified_date_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
        elif self.hover:
            # Hover state
            self.setStyleSheet(f"background-color: {colors['hover_bg']}; border-radius: 4px;")
            self.name_label.setStyleSheet(f"color: {colors['primary_text']}; background: transparent; font-weight: bold;")
            self.icon_label.setStyleSheet(f"color: {colors['accent']}; background: transparent;")
            self.created_date_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            self.modified_date_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        else:
            # Normal state
            self.setStyleSheet(f"background-color: transparent; border-radius: 4px;")
            self.name_label.setStyleSheet(f"color: {colors['primary_text']}; background: transparent; font-weight: bold;")
            self.icon_label.setStyleSheet(f"color: {colors['accent']}; background: transparent;")
            self.created_date_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            self.modified_date_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        
        # Force immediate update
        self.update()
    
    def _on_template_select(self, template):
        """Handle template selection with enhanced debugging"""
        try:
            # Handle case where same template is clicked
            if hasattr(self, 'selected_template') and self.selected_template == template:
                print("Same template selected, no change needed")
                return
                
            # Visual debug indicator for clicks
            print("\n\n")
            print(f"🔵 TEMPLATE CLICK DETECTED: {template.get('name', 'Unnamed')}")
            
            # Store the template first
            self.selected_template = template
            selected_name = template.get('name', 'Unnamed')
            print(f"App-level selected_template has been updated")
            print(f"Selected template set to: {template}")
            
            # Update the app-level selected template
            if hasattr(self.app, 'set_selected_template'):
                self.app.set_selected_template(template)
            
            # Update UI buttons state
            self._update_button_state()
            
            # Apply template highlighting to all cards
            print(f"Updating card styling for {len(self.template_cards)} cards")
            
            # First, unselect all cards
            for card in self.template_cards:
                if hasattr(card, 'set_selected'):
                    card.set_selected(False)
            
            # Then select only the matching card
            for card in self.template_cards:
                try:
                    # Get card template name
                    card_template = None
                    card_name = "Unknown"
                    
                    if hasattr(card, 'template'):
                        card_template = card.template
                        if isinstance(card_template, dict):
                            card_name = card_template.get('name', 'Unknown')
                        else:
                            card_name = str(card_template)
                    
                    # Check if this card matches our selected template
                    is_match = False
                    
                    # Check if the card template matches our selected template
                    if card_template == template:
                        is_match = True
                    # Or if the card name matches our selected template name
                    elif card_name == selected_name:
                        is_match = True
                    
                    # Apply selection state - should work for both card and list items
                    if is_match:
                        print(f"Setting card selected for template: {template}")
                        if hasattr(card, 'set_selected'):
                            card.set_selected(True)
                        
                except Exception as e:
                    print(f"Error updating card styling: {e}")
            
            # Force UI updates
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Emit selection signal
            self.template_selected.emit(template)
            
        except Exception as e:
            print(f"🔴 CRITICAL ERROR in template selection: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _on_add_template(self):
        """Open the template creation dialog"""
        try:
            if not self.app or not hasattr(self.app, 'template_manager'):
                print("No template manager available")
                return
            
            # Get template manager
            template_manager = self.app.template_manager
            
            # Get structure types (project types)
            template_manager.structure_types = []
            if hasattr(template_manager, 'get_structure_types'):
                template_manager.structure_types = template_manager.get_structure_types()
            
            # Setup import path
            import_path = os.path.expanduser("~/Documents")
            if hasattr(self.app, 'settings'):
                if self.app.settings.value("last_import_path"):
                    import_path = self.app.settings.value("last_import_path")
                else:
                    self.app.settings.setValue("last_import_path", import_path)
            
            # Get categories using our custom styled dialog
            # Remove category dialog and related code
            
            # Show file dialog to select a folder or zip file
            folder_name, ok = QInputDialog.getText(
                self,
                "New Template",
                "Enter template name:"
            )
            
            if not ok or not folder_name:
                return
            
            # Check if the template exists
            if not import_path or not os.path.exists(import_path):
                QMessageBox.warning(self, "Invalid Path", "Please select a valid folder or ZIP file.")
                return
            
            # Remove category parameter from save_template call
            template_data = {
                "name": folder_name,
                "structure": import_path,
                "type": "Standard"
            }
            template_manager.save_template(template_data)
            
            # Get the newly created template
            new_template = template_manager.get_template_by_name(folder_name)
            
            if not new_template:
                QMessageBox.warning(self, "Error", f"Failed to retrieve template '{folder_name}' after creation.")
                self.populate_gallery()
                return
            
            # If we're in a folder, add the new template to the current folder
            if hasattr(self, 'current_folder') and self.current_folder:
                print(f"[DEBUG] Adding new template '{folder_name}' to current folder '{self.current_folder}'")
                
                # Use the move_template_to_folder method which removes it from any other folders first
                if hasattr(template_manager, 'move_template_to_folder'):
                    success = template_manager.move_template_to_folder(folder_name, self.current_folder)
                    if success:
                        print(f"[DEBUG] Successfully added template '{folder_name}' to folder '{self.current_folder}'")
                    else:
                        print(f"[DEBUG] Failed to add template '{folder_name}' to folder '{self.current_folder}'")
                # Fallback to add_to_folder if move_template_to_folder isn't available
                elif hasattr(template_manager, 'add_to_folder'):
                    success = template_manager.add_to_folder(self.current_folder, folder_name)
                    if success:
                        print(f"[DEBUG] Successfully added template '{folder_name}' to folder '{self.current_folder}'")
                    else:
                        print(f"[DEBUG] Failed to add template '{folder_name}' to folder '{self.current_folder}'")
            
            # Open the editor immediately so user can add files and set up structure
            from app.dialogs.dialog_windows_pyqt import show_edit_template
            show_edit_template(self, new_template, self._on_template_edited)
            
            # Refresh the gallery to show the new template
            self.populate_gallery()
        except Exception as e:
            print(f"Error in _on_add_template: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_edit_template(self):
        """Handle edit template button click"""
        if self.selected_template:
            show_edit_template(self, self.selected_template, self._on_template_edited)
    
    def _on_edit_template_by_name(self, template_name):
        """Handle editing a template when double-clicked by its name"""
        # Find the template by name
        template = self.template_manager.get_template_by_name(template_name)
        if template:
            # Select the template first (updates UI state)
            self._on_template_select(template)
            # Open the template editor
            from app.dialogs.dialog_windows_pyqt import show_edit_template
            show_edit_template(self, template, self._on_template_edited)
        else:
            print(f"ERROR: Template not found: {template_name}")
    
    def _on_template_edited(self, template):
        """Handle when a template is edited"""
        if not template or not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        # Get template details
        template_name = template.get('name', '')
        # Remove category reference
        category = template.get('category', '')
        path = template.get('path', '')
        template_type = template.get('type', '')
        
        if not template_name or not path:
            return
            
        # Save the updated template
        template_data = {
            "name": template_name,
            "structure": path,  # In this context, path appears to be the structure
            "type": template_type
        }
        
        # Check if this is a rename operation
        original_name = template.get('original_name', None)
        if original_name and original_name != template_name:
            # print(f"DEBUG: This is a rename operation from '{original_name}' to '{template_name}'")
            template_data["original_name"] = original_name
        
        # Call save_template with the template data
        self.template_manager.save_template(template_data)
    
    def _on_delete_template(self):
        """Delete the selected template"""
        try:
            # Get template name and category
            template_name = self.template.get('name', '')
            # Remove category reference
            
            if not template_name:
                return
            
            confirm = QMessageBox.question(
                self, 
                "Confirm Delete", 
                f"Are you sure you want to delete template '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                success = self.template_manager.delete_template(template_name)
                if success:
                    QMessageBox.information(self, "Success", f"Template '{template_name}' deleted successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete template '{template_name}'.")
                
                self.selected_template = None
                self.populate_gallery()
        except Exception as e:
            print(f"Error in _on_delete_template: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_manage_templates(self):
        """Handle manage templates button click
        
        Note: The "Manage All" button has been removed from the UI as its functionality
        is redundant with other UI elements, but this method is kept for programmatic use
        or in case it's called from elsewhere in the codebase.
        """
        show_manage_templates(self, self.template_manager, self.populate_gallery)
    
    def _on_folder_select(self, folder_name):
        """Handle folder selection - only selects the folder, enabling rename and delete buttons"""
        try:
            # DEBUG - VISUAL INDICATOR FOR FOLDER SELECTION
            print("\n\n")
            print("🟢" * 50)
            print(f"🟩 FOLDER SELECTION: {folder_name}")
            
            # Show where in the code this was called from
            import traceback
            frames = traceback.extract_stack()
            caller = frames[-2]  # The caller of this function
            print(f"🟩 Called from: {caller.filename}:{caller.lineno}")
            
            # Clear any previously selected template
            self.selected_template = None
            
            # Store the selected folder name
            self.selected_folder = folder_name
            
            # Add debug visualization
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
            debug_dialog = QDialog(self)
            debug_dialog.setWindowTitle("Folder Selection Debug")
            debug_dialog.setMinimumWidth(600)
            
            debug_layout = QVBoxLayout(debug_dialog)
            
            # Show what folder was clicked
            debug_layout.addWidget(QLabel(f"Selected folder: {folder_name}"))
            debug_layout.addWidget(QLabel(f"Folder card count: {len(self.folder_cards)}"))
            
            # Add a list of all folder cards for debugging
            folder_list = QLabel("Folder cards: " + ", ".join(
                [f.folder_name if hasattr(f, 'folder_name') else "Unknown" for f in self.folder_cards]))
            folder_list.setWordWrap(True)
            debug_layout.addWidget(folder_list)
            
            # Add close button
            close_button = QPushButton("Continue (Close Debug)")
            close_button.clicked.connect(debug_dialog.accept)
            debug_layout.addWidget(close_button)
            
            # Show the debug dialog
            debug_dialog.exec_()
            
            # Deselect all folders and then select the right one
            print("🟩 Highlighting folder...")
            
            # Track what gets updated
            updated_count = 0
            
            for folder_card in self.folder_cards:
                if folder_card and not sip.isdeleted(folder_card):
                    is_match = hasattr(folder_card, 'folder_name') and folder_card.folder_name == folder_name
                    
                    print(f"🟩 Checking folder card: {getattr(folder_card, 'folder_name', 'Unknown')} {'[MATCH]' if is_match else ''}")
                    
                    if hasattr(folder_card, 'set_selected'):
                        try:
                            folder_card.set_selected(is_match)
                            if is_match:
                                print(f"🟩 Applied set_selected(True) to {folder_card.folder_name}")
                                # Capture the styling to see what's being applied 
                                print(f"🟩 Folder card style: {folder_card.styleSheet()}")
                                updated_count += 1
                            else:
                                print(f"🟩 Applied set_selected(False) to {getattr(folder_card, 'folder_name', 'Unknown')}")
                        except Exception as e:
                            print(f"🔴 Error in folder card set_selected: {e}")
            
            print(f"🟩 Updated {updated_count} folder cards")
            
            # Enable rename button only
            self.rename_folder_button.setEnabled(True)
            
            # Update UI to show folder is selected but don't enter it
            self._update_button_state()
            
            print("🟢" * 50 + "\n\n")
        except Exception as e:
            print(f"🔴 Error in _on_folder_select: {e}")
            import traceback
            traceback.print_exc()

    def _on_folder_enter(self, folder_name):
        """Handle folder navigation - actually enter the folder"""
        try:
            # Validate input
            if not folder_name or not isinstance(folder_name, str):
                print(f"Invalid folder name: {folder_name}")
                return
                
            # Get valid folders 
            folders = self.template_manager.get_folders()
            
            # Check if folder exists - handle both list and dict
            folder_exists = False
            if isinstance(folders, list):
                folder_exists = folder_name in folders
            elif isinstance(folders, dict):
                folder_exists = folder_name in folders.keys()
                
            if not folder_exists:
                print(f"Folder not found: {folder_name}")
                return
                
            # Update the current folder
            self.current_folder = folder_name
            self.folder_label.setText(f"Current Folder: {folder_name}")
            
            # Refresh the gallery with the folder contents
            QApplication.processEvents()  # Process pending events to avoid UI freezes
            self.populate_gallery()
        except Exception as e:
            print(f"Error in _on_folder_enter: {e}")
            import traceback
            traceback.print_exc()
            
    def get_templates_in_folder(self, folder_name):
        """Get templates in a specific folder - fallback implementation"""
        # If template manager has its own implementation, use that
        if hasattr(self.template_manager, 'get_templates_in_folder'):
            return self.template_manager.get_templates_in_folder(folder_name)
            
        # Otherwise use our fallback implementation
        templates = self.template_manager.get_all_templates()
        
        # Check if folders are stored as a dict with folder contents
        folders = self.template_manager.get_folders()
        if isinstance(folders, dict) and folder_name in folders:
            # Get the templates in this folder
            folder_templates = []
            for template_name in folders[folder_name]:
                # Find the template with this name
                for template in templates:
                    if template.get('name') == template_name:
                        folder_templates.append(template)
                        break
            return folder_templates
        
        # If folders are not a dict or don't contain this folder,
        # look for templates that have this folder in their 'folder' attribute
        return [t for t in templates if t.get('folder') == folder_name]
    
    def _on_back_to_all(self):
        """Handle clicking the "Back to All" button"""
        # Clear current folder
        self.current_folder = None
        
        # Clear folder label
        self.folder_label.setText("")
        
        # Reset templates header
        self.templates_header.setText("Templates")
        
        # Make sure the folders section is visible again
        self.folders_section.setVisible(True)
        
        # Refresh the gallery
        self.populate_gallery()
    
    def _update_folder_ui(self):
        """Update the folder management UI based on current state"""
        if self.current_folder is None:
            # Root view - show only add folder
            self.folder_nav.hide()
            self.folder_label.hide()
            self.add_folder_button.show()
            # Don't show rename button: self.rename_folder_button.hide()
        else:
            # Folder view - show all folder management except rename
            # (we're using in-place renaming and keyboard/context menu for deletion now)
            self.folder_nav.show()
            self.folder_label.show()
            self.add_folder_button.show()
            # Don't show rename button: self.rename_folder_button.show()
    
    def _on_add_folder(self):
        """Handle add folder button click"""
        folder_name, ok = QInputDialog.getText(
            self,
            "New Folder",
            "Enter folder name:"
        )
        
        if ok and folder_name:
            # Check if folder already exists
            folders = self.template_manager.get_folders()
            if folder_name in folders:
                QMessageBox.warning(self, "Error", f"Folder '{folder_name}' already exists.")
                return
                
            # Create folder
            self.template_manager.add_folder(folder_name)
            
            # If we're in a folder, move to new folder
            if self.current_folder is not None:
                self.current_folder = folder_name
                
            self.populate_gallery()
            
    def _on_rename_folder(self):
        """Handle rename folder button click - kept for compatibility"""
        if self.current_folder is None:
            return
            
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "Enter new folder name:",
            text=self.current_folder
        )
        
        if ok and new_name and new_name != self.current_folder:
            # Check if new folder name already exists
            folders = self.template_manager.get_folders()
            if new_name in folders:
                QMessageBox.warning(self, "Error", f"Folder '{new_name}' already exists.")
                return
                
            # Rename folder
            self.template_manager.rename_folder(self.current_folder, new_name)
            self.current_folder = new_name
            self.populate_gallery()
    
    def _on_rename_folder_requested(self, folder_name):
        """Handle rename folder request from folder card - kept for compatibility"""
        # We're now using inline editing, so this method is just a fallback
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "Enter new folder name:",
            text=folder_name
        )
        
        if ok and new_name and new_name != folder_name:
            self._rename_folder(folder_name, new_name)
    
    def _on_rename_folder_done(self, old_name, new_name):
        """Handle folder rename completion from inline editing"""
        try:
            print(f"Folder rename requested from '{old_name}' to '{new_name}'")
            
            # Check if new folder name already exists
            folders = self.template_manager.get_folders()
            print(f"Current folders: {folders}")
            
            # Check if the folder already exists
            folder_exists = False
            if isinstance(folders, list):
                folder_exists = new_name in folders
            elif isinstance(folders, dict):
                folder_exists = new_name in folders.keys()
                
            if folder_exists:
                print(f"Folder '{new_name}' already exists, cancelling rename")
                QMessageBox.warning(self, "Error", f"Folder '{new_name}' already exists.")
                return
                
            # Proceed with renaming
            print(f"Proceeding with rename '{old_name}' to '{new_name}'")
            self._rename_folder(old_name, new_name)
        except Exception as e:
            print(f"Error in _on_rename_folder_done: {e}")
            import traceback
            traceback.print_exc()
            
    def _rename_folder(self, old_name, new_name):
        """Common method to handle folder renaming"""
        try:
            print(f"Renaming folder from '{old_name}' to '{new_name}'")
            
            # Rename folder
            success = self.template_manager.rename_folder(old_name, new_name)
            print(f"Rename result: {success}")
            
            if success:
                # Update current folder if needed
                if self.current_folder == old_name:
                    print(f"Updating current folder from '{old_name}' to '{new_name}'")
                    self.current_folder = new_name
                    self.folder_label.setText(f"Current Folder: {new_name}")
                
                # Refresh the gallery
                print("Refreshing gallery after rename")
                self.populate_gallery()
            else:
                print(f"Failed to rename folder '{old_name}'")
                QMessageBox.warning(self, "Error", f"Failed to rename folder '{old_name}'.")
        except Exception as e:
            print(f"Error in _rename_folder: {e}")
            import traceback
            traceback.print_exc()

    def _on_delete_folder(self):
        """Handle delete folder button click"""
        if self.current_folder is None:
            return
            
        # Check if this is a default folder
        if self.current_folder in ["General", "Development", "Business"]:
            QMessageBox.warning(self, "Error", f"'{self.current_folder}' is a default folder and cannot be deleted.")
            return
            
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{self.current_folder}'?\n"
            "Templates in this folder will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete folder
            self.template_manager.delete_folder(self.current_folder)
            self.current_folder = None
            self.populate_gallery()
    
    def _update_button_state(self):
        """Update button states based on selection"""
        has_selection = self.selected_template is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Handle delete or backspace key when a folder is selected
        if self.selected_folder and (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace):
            # Don't allow deleting default folders
            if self.selected_folder in ["General", "Development", "Business"]:
                QMessageBox.warning(self, "Error", f"'{self.selected_folder}' is a default folder and cannot be deleted.")
                return
                
            # Delete folder without confirmation dialog
            success = self.template_manager.delete_folder(self.selected_folder)
            
            if success:
                # Show status message for success
                if hasattr(self, 'app') and hasattr(self.app, 'show_status_message'):
                    self.app.show_status_message(f"Folder '{self.selected_folder}' deleted", "info")
                    
                # Clear selected folder and refresh gallery
                folder_name = self.selected_folder
                self.selected_folder = None
                self.populate_gallery(force_refresh=True)
                
                # Consume the event
                event.accept()
                return
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Override resize event to adjust layout dynamically but prevent excessive redraws"""
        super().resizeEvent(event)
        
        # Instead of updating immediately, use a timer to prevent excessive redraws
        if self.resize_timer.isActive():
            self.resize_timer.stop()
        
        # Schedule a single update after the user has stopped resizing for a short time
        self.resize_timer.start(50)  # 50ms debounce
    
    def _handle_resize_timeout(self):
        """Handle the resize timeout after resizing has stopped"""
        # Calculate minimum width needed for controls
        min_width_needed = self._calculate_min_width_needed()
        
        # If window is too small, enforce minimum size
        current_width = self.width()
        if current_width < min_width_needed:
            self.setMinimumWidth(min_width_needed)
        
        # Update layouts now that resizing has stopped
        self._update_layout_after_resize()
    
    def _calculate_min_width_needed(self):
        """Calculate minimum width needed to display all controls properly"""
        # Use fixed values instead of calculating sizeHints which can cause repaints
        min_width = 400  # Base minimum width
        
        # Add container margins
        min_width += 60  # Side margins with some extra padding
        
        return min_width
        
    def _update_layout_after_resize(self):
        """Update layout after resizing is complete"""
        try:
            print(f"[DEBUG] Gallery resize complete, width = {self.width()}")
            
            # Only continue if the width is reasonable
            if self.width() < 50:
                return
                
            # Update main sections width if necessary
            if hasattr(self, 'folders_container') and hasattr(self, 'templates_container'):
                
                # Calculate available width for content, leaving space for margins
                available_width = self.width() - 30  # Account for margins
                
                # Update folder grid layout - this will handle row width calculations
                folders_width = min(available_width, 1200)  # Cap at a reasonable max
                self.folders_container.setMinimumWidth(folders_width)
                
                # Update templates grid layout
                templates_width = min(available_width, 1200)  # Cap at a reasonable max
                self.templates_container.setMinimumWidth(templates_width)
                
                # Look for list container if in list view and update its width
                if self.template_view_mode == "list":
                    # Find list container widget in templates grid
                    for i in range(self.templates_grid.count()):
                        item = self.templates_grid.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, QFrame):
                                # This is likely our list container
                                widget.setMinimumWidth(templates_width)
                                # Ensure the scroll policy is set correctly for list view
                                # Don't allow horizontal scrolling for list items
                                for j in range(widget.layout().count()):
                                    child = widget.layout().itemAt(j)
                                    if child and child.widget() and isinstance(child.widget(), QScrollArea):
                                        child.widget().setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                                        child.widget().setMinimumWidth(templates_width)
                                
                                # Force immediate update and repaint
                                widget.updateGeometry()
                                widget.update()
                
                # Force update
                self.folders_container.updateGeometry()
                self.templates_container.updateGeometry()
                
            # Update icon and list size based on current settings
            self._update_card_sizes()
            
            # Force an immediate repaint to prevent visual glitches
            self.update()
            
            # Force immediate processing of all pending UI events
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error in _update_layout_after_resize: {e}")
            import traceback
            traceback.print_exc()

    def _on_icon_scale_changed(self, value):
        """Handle icon scale slider changes"""
        print(f"[DEBUG] Icon scale changed to {value}")
        
        # Update the icon_scale property for all sizing
        self.icon_scale = value
        
        # Only update folder card sizes, not template card sizes
        self._update_folder_card_sizes(value)

    def _update_folder_card_sizes(self, value):
        """Update folder card sizes based on icon scale"""
        print(f"[DEBUG] Updating folder card sizes with scale value: {value}")
        print(f"[DEBUG] Current folder view mode: {self.folder_view_mode}")
        print(f"[DEBUG] Number of folder cards: {len(self.folder_cards)}")
        
        # Default sizes should match the sizes we use in initialization
        folder_base_width = 120
        folder_base_height = 120
        
        # Calculate new sizes
        scale_factor = value / 100.0
        
        # New folder sizes
        new_folder_width = int(folder_base_width * scale_factor)
        new_folder_height = int(folder_base_height * scale_factor)
        print(f"[DEBUG] New folder size: {new_folder_width}x{new_folder_height}")
        
        # Update folder cards in grid or icon view (any mode that's not list)
        if self.folder_view_mode != "list":
            resized_count = 0
            for card in self.folder_cards:
                if isinstance(card, TemplateFolderCard):  # Only scale icon/grid view cards
                    card.setFixedSize(new_folder_width, new_folder_height)
                    # Adjust font size of icon - use 40 to match the default in TemplateFolderCard
                    icon_font_size = int(40 * scale_factor)
                    card.icon_label.setFont(QFont(GALLERY_FONT, icon_font_size))
                    resized_count += 1
            print(f"[DEBUG] Resized {resized_count} folder cards")
        else:
            print(f"[DEBUG] Not resizing folders in list view mode")
        
        # Update layout but don't repopulate to avoid recursive loops
        self.folders_grid.update()
        if hasattr(self, 'folders_container'):
            self.folders_container.updateGeometry()
            self.folders_container.update()
    
    def _update_template_card_sizes(self, value):
        """Update template card sizes based on icon scale"""
        print(f"[DEBUG] Updating template card sizes with scale value: {value}")
        
        # Default sizes should match the sizes we use in initialization
        template_base_width = 200
        template_base_height = 250  # Adjusted to match typical card height
        
        # Calculate new sizes
        scale_factor = value / 100.0
        
        # New template sizes
        new_template_width = int(template_base_width * scale_factor)
        new_template_height = int(template_base_height * scale_factor)
        
        # Update template cards if in icon/grid view
        if self.template_view_mode != "list":
            resized_count = 0
            for card in self.template_cards:
                if hasattr(card, 'setFixedSize'):  # Check for the required method
                    # Set the size on the card
                    card.setFixedSize(new_template_width, new_template_height)
                    resized_count += 1
            print(f"[DEBUG] Resized {resized_count} template cards")
        else:
            print(f"[DEBUG] Not resizing templates in list view mode")
            
        # Update layout but don't repopulate to avoid recursive loops
        self.templates_grid.update()
        if hasattr(self, 'templates_container'):
            self.templates_container.updateGeometry()
            self.templates_container.update()

    def _set_folder_view_mode(self, mode):
        """Set the folder view mode"""
        print(f"Changing folder view mode to: {mode}")
        if mode in ["icon", "grid", "list"]:
            prev_mode = self.folder_view_mode
            self.folder_view_mode = mode
            
            # Update button states
            self.folder_icon_view_btn.setChecked(mode in ["icon", "grid"])
            self.folder_list_view_btn.setChecked(mode == "list")
            
            # When in list mode, hide the slider but keep the container visible
            # This prevents layout shifts when toggling between modes
            if hasattr(self, 'folder_size_control'):
                if mode == "list":
                    self.folder_size_slider.setVisible(False)
                else:
                    self.folder_size_slider.setVisible(True)
            
            # Only refresh if the view mode actually changed
            if prev_mode != mode:
                print(f"Folder view mode changed from {prev_mode} to {mode}, refreshing...")
                self.populate_gallery(force_refresh=True)
        else:
            print(f"Invalid folder view mode: {mode}")

    def _set_template_view_mode(self, mode):
        """Set the template view mode"""
        print(f"Changing template view mode to: {mode}")
        if mode in ["icon", "grid", "list"]:
            prev_mode = self.template_view_mode
            self.template_view_mode = mode
            
            # Update button states
            self.template_icon_view_btn.setChecked(mode in ["icon", "grid"])
            self.template_list_view_btn.setChecked(mode == "list")
            
            # Only refresh if the view mode actually changed
            if prev_mode != mode:
                print(f"View mode changed from {prev_mode} to {mode}, refreshing...")
                self.populate_gallery(force_refresh=True)
        else:
            print(f"Invalid template view mode: {mode}")

    def _update_card_sizes(self):
        """Legacy method to update all card sizes - kept for backward compatibility"""
        # Forward to the specific method using current slider value
        self._update_folder_card_sizes(self.folder_size_slider.value())
        # We no longer update template cards with the folder size slider

    def init_ui(self):
        """Initialize the UI for the gallery"""
        try:
            print("Initializing template gallery UI")
            # Set up basic layout
            from .gallery_ui_setup import GalleryUISetup
            GalleryUISetup.setup_ui(self)
            
            # Connect signals to slots
            self.connect_signals()
            
            # Initialize the categories (modified to handle removal of dropdown)
            self._update_categories()
            
            # Populate the gallery
            self.populate_gallery()
        except Exception as e:
            print(f"Error in init_ui: {e}")
            import traceback
            traceback.print_exc()

    def show_project_type_info(self):
        """Show information about project types vs folders"""
        QMessageBox.information(
            self, 
            "Project Types vs Folders",
            "<h3>How Template Organization Works</h3>"
            "<p><b>Project Types</b> determine the default folder structure when creating projects. "
            "Each project type (like 'Video Editing' or 'Design') has a preferred folder structure.</p>"
            "<p><b>Folders</b> are just for organizing your templates in the gallery. "
            "They don't affect the structure of projects you create.</p>"
            "<p>You can use both systems together - organize templates in folders while "
            "still benefiting from the default structures provided by project types.</p>"
        )

    def _on_category_select(self, category):
        """Handle project type selection"""
        self.current_category = category
        self.populate_gallery()

    def _on_project_type_changed(self, index):
        """Handle project type change (modified to handle absence of project type dropdown)"""
        # Since the project type dropdown has been removed, we'll just set the current category to "All"
        self.current_category = "All"
        self.populate_gallery()
    
    def _update_categories(self):
        """Update categories (modified to handle absence of project type dropdown)"""
        # Since the project type dropdown has been removed, we'll just set the current category to "All"
        self.current_category = "All"
        
    def on_project_type_changed(self, index):
        """Handle project type selection (modified to handle absence of project type dropdown)"""
        # This method is no longer connected to any UI element, but keeping it for compatibility
        # Set default category to "All"
        self.current_category = "All"
        self._on_category_select("All")

    def parent(self):
        """Get parent window"""
        return self.app
        
    def show_structure_editor(self, parent, structure_type=None, callback=None, is_new=False):
        """Show the structure editor with the correct project type"""
        # Get the current project type
        project_type = self.current_category if hasattr(self, 'current_category') and self.current_category != "All" else None
        
        # If no specific project type is selected, use the first available
        if not project_type and hasattr(self, 'category_combo') and self.category_combo.count() > 1:
            project_type = self.category_combo.itemText(1)  # Skip "All" at index 0
            
        # Get the associated structure for this project type
        from app.constants import PROJECT_TYPE_TO_STRUCTURE
        if project_type and project_type in PROJECT_TYPE_TO_STRUCTURE:
            structure_name = PROJECT_TYPE_TO_STRUCTURE.get(project_type)
        else:
            structure_name = None
            
        # Open the structure editor with the correct structure selected
        return parent.show_structure_editor(parent, structure_name, callback, is_new, project_type)

    def connect_signals(self):
        """Connect UI signals to slots"""
        try:
            # Connect the category dropdown to the on_project_type_changed method
            if hasattr(self, 'category_combo'):
                self.category_combo.currentIndexChanged.connect(self._on_project_type_changed)
                
            # Connect other signals that might be needed
            if hasattr(self, 'search_box'):
                self.search_box.textChanged.connect(self._on_search)
                
        except Exception as e:
            print(f"Error connecting signals: {e}")
            import traceback
            traceback.print_exc()

    def get_selected_template(self):
        """Return the currently selected template"""
        return self.selected_template
    
    def set_selected_template(self, template):
        """Set the currently selected template"""
        self.selected_template = template

    def _load_template_data(self, template):
        """Load template data into the widget"""
        try:
            if not template:
                return
                
            # Set name
            if isinstance(template, dict):
                name = template.get('name', 'Untitled Template')
                self.name_label.setText(name)
            elif isinstance(template, str):
                self.name_label.setText(template)
                
            # Apply default styling
            self._update_styling()
        except Exception as e:
            print(f"Error loading template data: {e}")
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.hover = True
        self._update_styling()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.hover = False
        self._update_styling()
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        """Filter events for hover effects"""
        if obj == self:
            if event.type() == QEvent.Enter:
                self.hover = True
                self._update_styling()
            elif event.type() == QEvent.Leave:
                self.hover = False
                self._update_styling()
        return super().eventFilter(obj, event)

    def select_template(self, template_name):
        """Select a template by name in the gallery
        
        Args:
            template_name: Name of the template to select
            
        Returns:
            bool: True if template was found and selected, False otherwise
        """
        try:
            if not template_name:
                return False
                
            print(f"🔍 LISTENER: Template selection request for '{template_name}'")
            
            # Find the template in the template manager
            template = None
            if hasattr(self, 'template_manager') and hasattr(self.template_manager, 'get_template_by_name'):
                template = self.template_manager.get_template_by_name(template_name)
                if template:
                    print(f"🔍 LISTENER: Found template by name match: {template_name}")
            
            # If not found, try a case-insensitive search
            if not template and hasattr(self, 'template_manager'):
                for t in self.template_manager.get_all_templates():
                    if t.get('name', '').lower() == template_name.lower():
                        template = t
                        print(f"🔍 LISTENER: Found template by case-insensitive match: {template_name}")
                        break
            
            # If we found the template, select it
            if template:
                # Update the app-level selected template
                if hasattr(self, 'app'):
                    print(f"🔍 LISTENER: Updated app-level selected template to '{template_name}'")
                    self.app.selected_template = template
                    
                    # Also update template_file_path if available
                    if isinstance(template, dict):
                        if 'path' in template:
                            self.app.template_file_path = template['path']
                            print(f"🔍 LISTENER: Updated app-level template file path to '{template['path']}'")
                        else:
                            # Try to get the path from the template manager
                            if hasattr(self.app, 'template_manager'):
                                template_info = self.app.template_manager.get_template_by_name(template_name)
                                if template_info and 'path' in template_info:
                                    self.app.template_file_path = template_info['path']
                                    print(f"🔍 LISTENER: Updated app-level template file path from template manager")
                
                # Update gallery selection state
                print(f"🔍 LISTENER: Template selection set to '{template_name}'")
                self._on_template_select(template)
                return True
                
            # If we got here, we couldn't find the template
            print(f"🔍 LISTENER: Could not find template with name '{template_name}'")
            return False
        except Exception as e:
            print(f"🔍 ERROR: Exception while selecting template: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def create_template_gallery(app):
    """Create and return the template gallery widget"""
    gallery = TemplateGallery(app=app)
    gallery.template_selected.connect(lambda template: select_template_from_gallery(app, template))
    gallery.populate_gallery()
    return gallery

def select_template_from_gallery(app, template):
    """Handle template selection from gallery"""
    # Update app state with selected template
    app.selected_template = template
    
    # Update recent templates
    from app.core.project_operations import add_to_recent_templates
    add_to_recent_templates(app, template)
    
    # Show template details in the app UI
    # Status message removed - visual highlight is sufficient

# Add unit test section at the end of the file
if __name__ == "__main__":
    """Unit test section for testing gallery components"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test template list item
    template = {
        "name": "Test Template",
        "description": "This is a test template for verifying the UI",
        "category": "Test",
        "icon": "📄"
    }
    
    # Create a simple test window
    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)
    
    # Add a folder list item
    folder_item = TemplateFolderListItem(window, "Test Folder")
    layout.addWidget(folder_item)
    
    # Add a template list item
    template_item = TemplateListItem(window, template)
    layout.addWidget(template_item)
    
    # Show the window
    window.setGeometry(100, 100, 800, 600)
    window.setWindowTitle("Gallery Component Test")
    window.show()
    
    sys.exit(app.exec_()) 