#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

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
                           QSlider, QButtonGroup, QToolButton, QLineEdit)
from PyQt5.QtCore import (Qt, pyqtSignal, QSize, QPoint, QEvent, QMimeData, 
                        QByteArray, QTimer)
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QCursor, QDrag, QPixmap

from app.ui.color_scheme_pyqt import colors, get_color, BUTTON_STYLE, ACCENT_BUTTON_STYLE, LABEL_STYLE
from app.ui.ui_components_pyqt import ScrollableFrame, CardFrame, ToolTip, SearchBox
from app.templates.template_manager import TemplateManager
from app.templates.template_card_pyqt import TemplateCard, CARD_NORMAL, CARD_HOVER, CARD_SELECTED, get_system_font, SYSTEM_FONT
from app.dialogs.dialog_windows_pyqt import show_edit_template, show_manage_templates

# Constants for styling
BLUE_HIGHLIGHT = colors["highlight_bg"]
CARD_NORMAL = colors["card_bg"]
CARD_HOVER = colors["hover_bg"]
CARD_SELECTED = colors["highlight_bg"]

# Get suitable system font for different platforms
def get_system_font():
    """Return an appropriate system font based on platform"""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "Helvetica Neue"  # Just use Helvetica which is guaranteed to exist
    else:  # Linux and others
        return "Ubuntu,DejaVu Sans,Liberation Sans,Arial"

# System font to use throughout the app
SYSTEM_FONT = get_system_font()

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
        self.icon_label.setFont(QFont(SYSTEM_FONT, 40))  # Smaller font to match smaller card
        self.icon_label.setStyleSheet("color: goldenrod; background: transparent; padding-bottom: 0;")
        self.icon_layout.addWidget(self.icon_label)
        self.layout.addLayout(self.icon_layout)
        
        # Folder name - simpler display directly under the icon
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(SYSTEM_FONT, 12))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: white; background: transparent; margin-top: -8px;")  # Force white color
        self.title.setWordWrap(True)
        self.title.setCursor(Qt.IBeamCursor)  # Change cursor to indicate text editability
        self.title.setToolTip("Click the name to rename")
        self.title.installEventFilter(self)  # Install event filter for the title specifically
        self.layout.addWidget(self.title)
        
        # Create the edit widget but don't add it to layout yet
        self.name_edit = QLineEdit(folder_name)
        self.name_edit.setFont(QFont(SYSTEM_FONT, 12))
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
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Handle when a drag leaves the folder card"""
        # Reset appearance when drag leaves
        self._update_styling()
        event.accept()
    
    def dropEvent(self, event):
        """Handle when a template is dropped on the folder"""
        template_name = None
        
        # First try to get JSON data for complete template info
        if event.mimeData().hasFormat("application/json"):
            data = event.mimeData().data("application/json")
            try:
                template_data = bytes(data).decode()
                template = json.loads(template_data)
                template_name = template.get('name', '')
                if template_name:
                    self._add_template_to_folder(template_name)
                    event.acceptProposedAction()
                    return
            except Exception as e:
                print(f"Error parsing template data: {e}")
        
        # Fallback to text data which should contain the template name
        if event.mimeData().hasText():
            template_name = event.mimeData().text()
            if template_name:
                self._add_template_to_folder(template_name)
                event.acceptProposedAction()
    
    def _add_template_to_folder(self, template_name):
        """Add a template to this folder"""
        if not template_name or not self.app:
            print(f"[DEBUG] Card: Invalid template name or app: {template_name}")
            return
            
        try:
            # Check if template exists
            print(f"[DEBUG] Card: Trying to add template '{template_name}' to folder '{self.folder_name}'")
            template = self.app.template_manager.get_template_by_name(template_name)
            if not template:
                print(f"[DEBUG] Card: Template not found: {template_name}")
                return False
                
            # Move template to folder (this will remove it from other folders)
            print(f"[DEBUG] Card: Moving template to folder")
            result = self.app.template_manager.move_template_to_folder(template_name, self.folder_name)
            
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
            
            return result
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
            
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{self.folder_name}'?\n"
            "Templates in this folder will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete folder
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
        self.icon_label.setFont(QFont(SYSTEM_FONT, 18))
        self.icon_label.setStyleSheet("color: goldenrod; background: transparent;")
        self.layout.addWidget(self.icon_label)
        
        # Folder name
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(SYSTEM_FONT, 12))
        self.title.setStyleSheet("color: white; background: transparent;")
        self.title.setCursor(Qt.IBeamCursor)  # Change cursor to indicate text editability
        self.title.setToolTip("Click the name to rename")
        self.title.installEventFilter(self)  # Install event filter for the title
        self.layout.addWidget(self.title, 1)  # Give it stretch factor
        
        # Create the edit widget but don't add it to layout yet
        self.name_edit = QLineEdit(folder_name)
        self.name_edit.setFont(QFont(SYSTEM_FONT, 12))
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
        """Handle when a drag enters the folder card"""
        # Only accept if it's dragging a template (text or JSON data)
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/json"):
            # Visual feedback for valid drag target - macOS style
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["accent_hover"]};
                    border: none;
                    border-radius: 0px;
                }}
                QLabel {{
                    color: white;
                    background: transparent;
                }}
            """)
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Handle when a drag leaves the folder card"""
        # Reset appearance when drag leaves
        self._update_styling()
        event.accept()
    
    def dropEvent(self, event):
        """Handle when a template is dropped on the folder"""
        template_name = None
        
        # First try to get JSON data for complete template info
        if event.mimeData().hasFormat("application/json"):
            data = event.mimeData().data("application/json")
            try:
                import json
                template_data = json.loads(bytes(data).decode())
                template_name = template_data.get('name')
            except:
                pass
        
        # Fallback to text data
        if not template_name and event.mimeData().hasText():
            template_name = event.mimeData().text()
        
        if template_name:
            self._add_template_to_folder(template_name)
            
        # Reset styling
        self._update_styling()
        event.accept()
    
    def _add_template_to_folder(self, template_name):
        """Add the template to this folder"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            print(f"[DEBUG] ListItem: Invalid app or template_manager")
            return
            
        # Get the template
        print(f"[DEBUG] ListItem: Trying to add template '{template_name}' to folder '{self.folder_name}'")
        template = self.app.template_manager.get_template_by_name(template_name)
        if not template:
            print(f"[DEBUG] ListItem: Template not found: {template_name}")
            return
            
        # Move template to folder (this will remove it from other folders)
        print(f"[DEBUG] ListItem: Moving template to folder")
        result = self.app.template_manager.move_template_to_folder(template_name, self.folder_name)
        
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
            if hasattr(self.parent(), 'populate_gallery'):
                # Force a complete refresh when adding templates to folders
                self.parent().populate_gallery(force_refresh=True)
        else:
            print(f"[DEBUG] ListItem: Failed to move template")
    
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
            
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{self.folder_name}'?\n"
            "Templates in this folder will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete folder
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
    
    def __init__(self, parent=None, template=None, app=None):
        super().__init__(parent)
        self.template = template
        self.app = app
        self.selected = False
        self.hover = False
        self.is_odd_row = False  # Add this attribute to fix list view disappearing
        
        # Configure frame appearance - use clean, borderless macOS style
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(0)
        self.setFixedHeight(40)  # Slightly reduced height for macOS-like compactness
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)
        
        # Template icon
        icon_text = template.get('icon', '📄')
        self.icon_label = QLabel(icon_text)
        self.icon_label.setFont(QFont(SYSTEM_FONT, 20))
        self.icon_label.setStyleSheet(f"color: {colors['accent']}; background: transparent;")
        self.icon_label.setFixedWidth(40)
        self.layout.addWidget(self.icon_label)
        
        # Template name and description
        self.info_layout = QVBoxLayout()
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout.setSpacing(0)
        
        # Template name
        self.name_label = QLabel(template.get('name', 'Unnamed Template'))
        self.name_label.setFont(QFont(SYSTEM_FONT, 12))
        self.name_label.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        self.info_layout.addWidget(self.name_label)
        
        # Template description (truncated)
        description = template.get('description', '')
        if len(description) > 50:
            description = description[:47] + "..."
        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont(SYSTEM_FONT, 9))
        self.desc_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        self.info_layout.addWidget(self.desc_label)
        
        self.layout.addLayout(self.info_layout, 1)  # Give it stretch factor
        
        # Category/Type
        category = template.get('category', 'General')
        self.category_label = QLabel(category)
        self.category_label.setFont(QFont(SYSTEM_FONT, 9))
        self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        self.layout.addWidget(self.category_label)
        
        # Install event filter
        self.installEventFilter(self)
        self._update_styling()
    
    def eventFilter(self, obj, event):
        """Filter events for mouse tracking"""
        if obj is self:
            if event.type() == QEvent.MouseButtonPress:
                self.clicked.emit(self.template)
                return True
            elif event.type() == QEvent.Enter:
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
        return super().eventFilter(obj, event)
    
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

class TemplateGallery(QWidget):
    """Main widget for displaying and managing templates"""
    
    template_selected = pyqtSignal(dict)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.template_manager = app.template_manager if app else None
        
        # UI state tracking
        self.current_category = "All"
        self.current_folder = None
        self.current_search = ""
        self.selected_template = None
        self.selected_folder = None
        self.folder_cards = []
        self.template_cards = []
        self.icon_scale = 100  # Default scale in percentage
        self.folder_view_mode = "grid"  # Default to grid view for folders
        self.template_view_mode = "grid"  # Default to grid view for templates
        self.templates_loaded = False  # Track if templates have been loaded
        
        # Resize handling
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.setInterval(200)  # 200ms debounce
        self.resize_timer.timeout.connect(self._handle_resize_timeout)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # No space between components
        
        # Top bar for search, filter and actions
        self.top_bar = QWidget()
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Category filter
        self.category_layout = QVBoxLayout()
        self.category_label = QLabel("Category:")
        self.category_label.setStyleSheet(LABEL_STYLE)
        self.category_layout.addWidget(self.category_label)
        
        # Replace horizontal scrollable buttons with a dropdown
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px;
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                selection-background-color: {colors['accent']};
                selection-color: {colors['highlight_text']};
                border: 1px solid {colors['border']};
            }}
        """)
        self.category_combo.currentTextChanged.connect(self._on_category_select)
        
        # Populate initial categories
        self._update_categories()
        
        self.category_layout.addWidget(self.category_combo)
        self.top_bar_layout.addLayout(self.category_layout, 1)
        
        # Search box
        self.search_box = SearchBox(self, "Search:", self._on_search)
        self.top_bar_layout.addWidget(self.search_box, 2)
        
        self.layout.addWidget(self.top_bar)
        
        # Action buttons - folders, templates, etc.
        self.action_bar = QWidget()
        self.action_bar_layout = QHBoxLayout(self.action_bar)
        self.action_bar_layout.setContentsMargins(10, 0, 10, 0)
        
        # Folder navigation (shown when in a folder)
        self.folder_nav = QWidget()
        self.folder_nav_layout = QHBoxLayout(self.folder_nav)
        self.folder_nav_layout.setContentsMargins(0, 0, 0, 0)
        
        self.back_button = QPushButton("« Back to All")
        self.back_button.setStyleSheet(BUTTON_STYLE)
        self.back_button.clicked.connect(self._on_back_to_all)
        self.folder_nav_layout.addWidget(self.back_button)
        
        self.folder_label = QLabel("Current Folder: None")
        self.folder_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
        self.folder_nav_layout.addWidget(self.folder_label)
        
        self.folder_nav_layout.addStretch()
        self.folder_nav.setVisible(False)  # Hidden by default
        
        self.action_bar_layout.addWidget(self.folder_nav)
        
        # Template/folder buttons
        self.button_frame = QWidget()
        self.button_layout = QHBoxLayout(self.button_frame)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        
        # We'll move the view controls to the section headers
        
        self.button_layout.addStretch(1)  # Push buttons to the right
        
        # Folder management buttons
        self.add_folder_button = QPushButton("New Folder")
        self.add_folder_button.setStyleSheet(BUTTON_STYLE)
        self.add_folder_button.clicked.connect(self._on_add_folder)
        self.button_layout.addWidget(self.add_folder_button)
        
        # We're removing the rename folder button as requested
        # Keep the variable for compatibility but don't add to layout
        self.rename_folder_button = QPushButton("Rename Folder")
        self.rename_folder_button.setStyleSheet(BUTTON_STYLE)
        self.rename_folder_button.clicked.connect(self._on_rename_folder)
        self.rename_folder_button.setEnabled(False)
        # Don't add to layout: self.button_layout.addWidget(self.rename_folder_button)
        
        self.delete_folder_button = QPushButton("Delete Folder")
        self.delete_folder_button.setStyleSheet(BUTTON_STYLE)
        self.delete_folder_button.clicked.connect(self._on_delete_folder)
        self.delete_folder_button.setEnabled(False)
        self.button_layout.addWidget(self.delete_folder_button)
        
        self.button_layout.addStretch()
        
        # Template buttons
        self.add_button = QPushButton("Add Template")
        self.add_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.add_button.clicked.connect(self._on_add_template)
        self.button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.setStyleSheet(BUTTON_STYLE)
        self.edit_button.clicked.connect(self._on_edit_template)
        self.edit_button.setEnabled(False)
        self.button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet(BUTTON_STYLE)
        self.delete_button.clicked.connect(self._on_delete_template)
        self.delete_button.setEnabled(False)
        self.button_layout.addWidget(self.delete_button)
        
        self.manage_button = QPushButton("Manage All")
        self.manage_button.setStyleSheet(BUTTON_STYLE)
        self.manage_button.clicked.connect(self._on_manage_templates)
        self.button_layout.addWidget(self.manage_button)
        
        self.action_bar_layout.addWidget(self.button_frame)
        self.layout.addWidget(self.action_bar)
        
        # Add a fixed margin frame between action bar and content
        self.margin_frame = QFrame()
        self.margin_frame.setFixedHeight(10)  # Fixed spacing
        self.margin_frame.setStyleSheet("background-color: transparent;")
        self.layout.addWidget(self.margin_frame)
        
        # Template gallery - use a main vertical layout
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setFrameShape(QFrame.NoFrame)
        self.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.gallery_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Ensure scroll area fills available space
        self.gallery_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Main container widget with vertical layout and fixed spacing
        self.gallery_widget = QWidget()
        self.gallery_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.main_layout = QVBoxLayout(self.gallery_widget)
        self.main_layout.setContentsMargins(8, 0, 8, 8)  # Remove top margin
        self.main_layout.setSpacing(10)  # Fixed spacing between sections
        
        # Folders section with its own scroll area
        self.folders_section = QWidget()
        self.folders_section_layout = QVBoxLayout(self.folders_section)
        self.folders_section_layout.setContentsMargins(0, 0, 0, 0)
        self.folders_section_layout.setSpacing(5)
        # Set a maximum width and policy to prevent excessive expansion
        self.folders_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.folders_section.setMaximumWidth(1200)
        
        # Folders header with view controls
        self.folders_header_container = QWidget()
        self.folders_header_container.setFixedHeight(40)  # Fixed height instead of minimum
        self.folders_header_layout = QHBoxLayout(self.folders_header_container)
        self.folders_header_layout.setContentsMargins(10, 5, 10, 5)  # Add some padding
        self.folders_header_layout.setSpacing(10)
        # Add solid background color to header
        self.folders_header_container.setStyleSheet(f"background-color: {colors['card_bg']};")
        
        # Folder title
        self.folders_header = QLabel("Folders")
        self.folders_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        self.folders_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0; background-color: transparent;")
        self.folders_header.setAlignment(Qt.AlignLeft)
        # Set fixed height and prevent vertical expansion
        self.folders_header.setFixedHeight(30)
        # Set a fixed width to prevent expanding
        self.folders_header.setFixedWidth(100)
        self.folders_header.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.folders_header_layout.addWidget(self.folders_header)
        
        # Add spacer to push buttons to the right
        self.folders_header_layout.addStretch(1)
        
        # Folder view controls
        self.folder_view_controls = QWidget()
        self.folder_view_controls_layout = QHBoxLayout(self.folder_view_controls)
        self.folder_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_view_controls_layout.setSpacing(0)
        
        # Add slider for icon size control (moved before the view buttons)
        self.folder_size_control = QWidget()
        self.folder_size_layout = QHBoxLayout(self.folder_size_control)
        self.folder_size_layout.setContentsMargins(0, 0, 10, 0)  # Add padding to the right
        self.folder_size_layout.setSpacing(5)
        
        # Size slider
        self.folder_size_slider = QSlider(Qt.Horizontal)
        self.folder_size_slider.setRange(50, 150)  # 50% to 150% scaling
        self.folder_size_slider.setValue(self.icon_scale)  # Use current scale value
        self.folder_size_slider.setFixedWidth(100)
        self.folder_size_slider.setTickPosition(QSlider.TicksBelow)
        self.folder_size_slider.setTickInterval(25)
        self.folder_size_slider.valueChanged.connect(self._on_icon_scale_changed)
        self.folder_size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #3C3C3C;
                height: 8px;
                background: #2A2A2A;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #909090;
                border: 1px solid #5A5A5A;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #AAAAAA;
            }
        """)
        
        # Add to layout (removed the label)
        self.folder_size_layout.addWidget(self.folder_size_slider)
        
        # Add to folder view controls first (before the view buttons)
        self.folder_view_controls_layout.addWidget(self.folder_size_control)
        
        # Create a horizontal button group for toggling between icon and list views
        self.folder_view_buttons = QWidget()
        self.folder_view_buttons_layout = QHBoxLayout(self.folder_view_buttons)
        self.folder_view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_view_buttons_layout.setSpacing(0)
        
        self.folder_view_toggle_group = QButtonGroup(self)
        
        # Icon view button
        self.folder_icon_view_btn = QToolButton()
        self.folder_icon_view_btn.setCheckable(True)
        self.folder_icon_view_btn.setToolTip("Icon View")
        self.folder_icon_view_btn.setText("Icon")
        self.folder_icon_view_btn.setChecked(self.folder_view_mode == "icon")
        self.folder_icon_view_btn.clicked.connect(lambda: self._set_folder_view_mode("icon"))
        self.folder_icon_view_btn.setFixedSize(65, 24)
        
        # Apply the same styling as the template view buttons
        self.folder_icon_view_btn.setStyleSheet("""
            QToolButton {
                background-color: #2A2A2A;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 3px 8px;
                min-width: 50px;
            }
            QToolButton:checked {
                background-color: #3E3E3E;
                color: white;
                border-color: #585858;
            }
            QToolButton:hover:!checked {
                background-color: #323232;
                border-color: #585858;
            }
        """)
        self.folder_view_toggle_group.addButton(self.folder_icon_view_btn)
        self.folder_view_buttons_layout.addWidget(self.folder_icon_view_btn)
        
        # List view button
        self.folder_list_view_btn = QToolButton()
        self.folder_list_view_btn.setCheckable(True)
        self.folder_list_view_btn.setToolTip("List View")
        self.folder_list_view_btn.setText("List")
        self.folder_list_view_btn.setChecked(self.folder_view_mode == "list")
        self.folder_list_view_btn.clicked.connect(lambda: self._set_folder_view_mode("list"))
        self.folder_list_view_btn.setFixedSize(65, 24)  # Fixed size to prevent layout shifts
        
        # Apply the same styling as the template list view button
        self.folder_list_view_btn.setStyleSheet("""
            QToolButton {
                background-color: #2A2A2A;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: none;
                padding: 3px 8px;
                min-width: 50px;
            }
            QToolButton:checked {
                background-color: #3E3E3E;
                color: white;
                border-color: #585858;
            }
            QToolButton:hover:!checked {
                background-color: #323232;
                border-color: #585858;
            }
        """)
        self.folder_view_toggle_group.addButton(self.folder_list_view_btn)
        self.folder_view_buttons_layout.addWidget(self.folder_list_view_btn)
        
        # Add buttons to controls
        self.folder_view_controls_layout.addWidget(self.folder_view_buttons)
        
        # Make sure folder view controls maintain their size
        self.folder_view_controls.setMinimumWidth(320)  # Increased to accommodate slider
        self.folder_view_controls.setMaximumWidth(320)
        self.folder_view_controls.setFixedHeight(30)
        self.folder_view_controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Add folder view controls to the header layout
        self.folders_header_layout.addWidget(self.folder_view_controls)
        
        # Add header container to section layout
        self.folders_section_layout.addWidget(self.folders_header_container)
        
        # Scrollable area just for folders
        self.folders_scroll = QScrollArea()
        self.folders_scroll.setWidgetResizable(True)
        self.folders_scroll.setFrameShape(QFrame.NoFrame)
        self.folders_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Never allow horizontal scrolling
        self.folders_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Set minimum and maximum height constraints
        self.folders_scroll.setMinimumHeight(150)
        self.folders_scroll.setMaximumHeight(300)  # Limit height to force scrolling
        
        # Container for folder grid - use a flow layout instead of grid
        self.folders_container = QWidget()
        self.folders_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.folders_grid = QGridLayout(self.folders_container)
        self.folders_grid.setContentsMargins(0, 0, 0, 0)
        self.folders_grid.setHorizontalSpacing(6)  # Slightly more horizontal space for better readability
        self.folders_grid.setVerticalSpacing(12)  # More vertical space between rows
        self.folders_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.folders_scroll.setWidget(self.folders_container)
        self.folders_section_layout.addWidget(self.folders_scroll)
        
        # Templates section
        self.templates_section = QWidget()
        self.templates_section_layout = QVBoxLayout(self.templates_section)
        self.templates_section_layout.setContentsMargins(0, 0, 0, 0)
        self.templates_section_layout.setSpacing(5)
        # Set a maximum width and policy to prevent excessive expansion
        self.templates_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.templates_section.setMaximumWidth(1200)
        
        # Templates header with view controls
        self.templates_header_container = QWidget()
        self.templates_header_container.setFixedHeight(40)  # Fixed height instead of minimum
        self.templates_header_layout = QHBoxLayout(self.templates_header_container)
        self.templates_header_layout.setContentsMargins(10, 5, 10, 5)  # Add some padding
        self.templates_header_layout.setSpacing(10)
        # Add solid background color to header
        self.templates_header_container.setStyleSheet(f"background-color: {colors['card_bg']};")
        
        # Template title
        self.templates_header = QLabel("Templates")
        self.templates_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        self.templates_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0; background-color: transparent;")
        self.templates_header.setAlignment(Qt.AlignLeft)
        # Set fixed height and prevent vertical expansion
        self.templates_header.setFixedHeight(30)
        # Set a fixed width to prevent expanding
        self.templates_header.setFixedWidth(120)
        self.templates_header.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.templates_header_layout.addWidget(self.templates_header)
        
        # Add spacer to push buttons to the right
        self.templates_header_layout.addStretch(1)
        
        # Create template view toggle buttons
        self.template_view_toggle_group = QButtonGroup(self)
        
        self.template_view_controls = QWidget()
        self.template_view_controls_layout = QHBoxLayout(self.template_view_controls)
        self.template_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.template_view_controls_layout.setSpacing(0)  # No spacing between buttons for a joined appearance
        self.template_view_controls.setStyleSheet("background-color: transparent;")
        
        # Create a widget to hold just the buttons in a group
        self.template_view_buttons = QWidget()
        self.template_view_buttons_layout = QHBoxLayout(self.template_view_buttons)
        self.template_view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.template_view_buttons_layout.setSpacing(0)  # No spacing between buttons
        
        # Create view buttons that look like a segmented control
        self.template_icon_view_btn = QToolButton()
        self.template_icon_view_btn.setText("Icons")
        self.template_icon_view_btn.setCheckable(True)
        self.template_icon_view_btn.setChecked(True)  # Default is icon view
        self.template_icon_view_btn.clicked.connect(lambda: self._set_template_view_mode("icon"))
        self.template_icon_view_btn.setStyleSheet("""
            QToolButton {
                background-color: #2A2A2A;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 3px 8px;
                min-width: 50px;
            }
            QToolButton:checked {
                background-color: #3E3E3E;
                color: white;
                border-color: #585858;
            }
            QToolButton:hover:!checked {
                background-color: #323232;
                border-color: #585858;
            }
        """)
        self.template_view_toggle_group.addButton(self.template_icon_view_btn)
        self.template_view_buttons_layout.addWidget(self.template_icon_view_btn)
        
        self.template_list_view_btn = QToolButton()
        self.template_list_view_btn.setText("List")
        self.template_list_view_btn.setCheckable(True)
        self.template_list_view_btn.clicked.connect(lambda: self._set_template_view_mode("list"))
        self.template_list_view_btn.setStyleSheet("""
            QToolButton {
                background-color: #2A2A2A;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: none;
                padding: 3px 8px;
                min-width: 50px;
            }
            QToolButton:checked {
                background-color: #3E3E3E;
                color: white;
                border-color: #585858;
            }
            QToolButton:hover:!checked {
                background-color: #323232;
                border-color: #585858;
            }
        """)
        self.template_view_toggle_group.addButton(self.template_list_view_btn)
        self.template_view_buttons_layout.addWidget(self.template_list_view_btn)
        
        # Add the button group to the controls layout
        self.template_view_controls_layout.addWidget(self.template_view_buttons)
        
        # Make sure template view controls maintain their size
        self.template_view_controls.setMinimumWidth(135)  # Increased width to prevent cutoff
        self.template_view_controls.setMaximumWidth(135)
        self.template_view_controls.setFixedHeight(30)  # Fixed height to prevent vertical changes
        self.template_view_controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Also set fixed size for buttons to prevent layout changes
        self.template_icon_view_btn.setFixedSize(65, 24)
        self.template_list_view_btn.setFixedSize(65, 24)
        
        # Add view controls to header layout
        self.templates_header_layout.addWidget(self.template_view_controls)
        
        # Add header container to section layout
        self.templates_section_layout.addWidget(self.templates_header_container)
        
        # Container for templates grid
        self.templates_container = QWidget()
        self.templates_grid = QGridLayout(self.templates_container)
        self.templates_grid.setContentsMargins(0, 0, 0, 0)
        self.templates_grid.setHorizontalSpacing(5)
        self.templates_grid.setVerticalSpacing(5)
        self.templates_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.templates_section_layout.addWidget(self.templates_container)
        
        # Add sections to the main layout
        self.main_layout.addWidget(self.folders_section)
        self.main_layout.addWidget(self.templates_section)
        
        # Set up the main scroll area
        self.gallery_scroll.setWidget(self.gallery_widget)
        self.layout.addWidget(self.gallery_scroll)
        
        # Hide sections by default
        self.folders_section.hide()
        self.templates_section.hide()
        
        # Populate gallery
        self.populate_gallery()
    
    def populate_gallery(self, force_refresh=False):
        """Populate the gallery with templates or folders"""
        try:
            print("Starting populate_gallery")
            # Check if we need to refresh templates data
            if force_refresh or not self.templates_loaded:
                # No need to call refresh if it doesn't exist
                self.templates_loaded = True
                
            # Clear the gallery
            print("Clearing gallery")
            self._clear_gallery()
            
            # Update category controls
            print("Updating categories")
            self._update_categories()
            
            # Update folder UI
            print("Updating folder UI")
            self._update_folder_ui()
            
            print(f"Current folder: {self.current_folder}")
            # Get templates or folders based on current view
            if self.current_folder is None:
                print("Root level - showing folders")
                # Root level - show folders
                QApplication.setOverrideCursor(Qt.WaitCursor)
                try:
                    # Get folder list
                    print("Getting folders")
                    folders = self.template_manager.get_folders()
                    print(f"Folders: {folders}")
                    
                    # Handle either a list of folder names or a dictionary
                    folders_list = []
                    if isinstance(folders, list):
                        folders_list = folders
                    elif isinstance(folders, dict):
                        folders_list = sorted(folders.keys())
                    print(f"Folders list: {folders_list}")
                    
                    # Make sure the folders section is visible if we have folders
                    if folders_list:
                        print("Making folders section visible")
                        self.folders_section.setVisible(True)
                    
                    # Display using either grid or list
                    print(f"Folder view mode: {self.folder_view_mode}")
                    if self.folder_view_mode == "grid" or self.folder_view_mode == "icon":
                        print("Using grid view for folders")
                        # Grid view for folders
                        row, col = 0, 0  # Initialize row and column counters
                        max_cols = 3  # Default number of columns
                        
                        # Calculate available width for better layout
                        available_width = self.folders_container.width()
                        if available_width > 0:
                            # Each folder card is 120px wide plus spacing
                            folder_width = 120 + 15  # Card width + margin
                            max_cols = max(1, (available_width - 30) // folder_width)
                        
                        for folder_name in sorted(folders_list):
                            print(f"Creating folder card for: {folder_name}")
                            folder_card = TemplateFolderCard(self, folder_name, self.app)
                            folder_card.clicked.connect(self._on_folder_select)
                            folder_card.doubleClicked.connect(self._on_folder_enter)
                            folder_card.renameRequested.connect(self._on_rename_folder_requested)
                            folder_card.renameDone.connect(self._on_rename_folder_done)
                            self.folders_grid.addWidget(folder_card, row, col)
                            self.folder_cards.append(folder_card)  # Track cards for cleanup
                            
                            # Update grid position
                            col += 1
                            if col >= max_cols:
                                col = 0
                                row += 1
                    else:
                        print("Using list view for folders")
                        # List view for folders
                        # Create a container for list view
                        list_container = QFrame()
                        list_container.setFrameShape(QFrame.NoFrame)
                        list_container.setStyleSheet("background-color: transparent; border: none;")
                        list_layout = QVBoxLayout(list_container)
                        list_layout.setContentsMargins(0, 0, 0, 0)
                        list_layout.setSpacing(0)  # No spacing between items
                        
                        # Add the list container to the grid
                        self.folders_grid.addWidget(list_container, 0, 0, 1, 1)
                        
                        for i, folder_name in enumerate(sorted(folders_list)):
                            print(f"Creating folder list item for: {folder_name}")
                            folder_item = TemplateFolderListItem(self, folder_name, self.app)
                            # Height is already set in the TemplateFolderListItem class
                            folder_item.clicked.connect(self._on_folder_select)
                            folder_item.doubleClicked.connect(self._on_folder_enter)
                            folder_item.renameRequested.connect(self._on_rename_folder_requested)
                            folder_item.renameDone.connect(self._on_rename_folder_done)
                            
                            # Set alternate row color using property
                            folder_item.setProperty("row_type", "odd" if i % 2 else "even")
                            
                            # Set the background color directly
                            if i % 2:
                                folder_item.setStyleSheet(f"QFrame {{ background-color: {colors['card_bg']}; border: none; }}")
                            else:
                                folder_item.setStyleSheet(f"QFrame {{ background-color: {colors['bg']}; border: none; }}")
                            
                            # Force style update
                            folder_item.style().unpolish(folder_item)
                            folder_item.style().polish(folder_item)
                            
                            list_layout.addWidget(folder_item)
                            self.folder_cards.append(folder_item)  # Track cards for cleanup
                    
                    # Also load templates not in folders for the root view
                    print("Getting all templates")
                    templates = self.template_manager.get_all_templates()
                    print(f"Templates: {len(templates)}")
                    
                    # Use template_manager to get templates not in any folder
                    root_templates = self.template_manager.get_templates_in_folder(None)
                    print(f"Root templates: {len(root_templates)}")
                    
                    # Make templates section visible if we have templates
                    if root_templates:
                        print("Making templates section visible")
                        self.templates_section.setVisible(True)
                        
                    # Now add template cards to the template section
                    print("Displaying templates")
                    self._display_templates(root_templates)
                    
                    # Update folder management UI visibility
                    print("Updating folder UI")
                    self._update_folder_ui()
                finally:
                    QApplication.restoreOverrideCursor()
            else:
                print(f"Showing templates for folder: {self.current_folder}")
                # Viewing a specific folder
                # Get templates in the folder
                templates = self.get_templates_in_folder(self.current_folder)
                print(f"Templates in folder: {len(templates)}")
                
                # Hide the folders section when inside a folder
                self.folders_section.setVisible(False)
                
                # Update the templates header to show we're in a folder
                self.templates_header.setText(f"Templates in '{self.current_folder}'")
                
                # Make templates section visible if we have templates
                if templates:
                    print("Making templates section visible")
                    self.templates_section.setVisible(True)
                    
                # Display templates
                print("Displaying templates")
                self._display_templates(templates)
                
                # Update folder management UI visibility
                print("Updating folder UI")
                self._update_folder_ui()
                
            print("Populate gallery complete")
        except Exception as e:
            print(f"Error populating gallery: {str(e)}")
            import traceback
            traceback.print_exc()

    def _display_templates(self, templates):
        """Display templates in the template section"""
        try:
            print(f"_display_templates called with {len(templates)} templates")
            
            if not templates:
                print("No templates to display")
                return
                
            # Calculate available width for templates
            available_width = self.templates_container.width()
            if available_width <= 0:
                available_width = self.width() - 40  # Use widget width with margin
                
            # Limit to a reasonable maximum width
            available_width = min(available_width, 1200)
            
            # Calculate columns for templates
            template_width = 200 + 10  # Template card width + spacing
            max_cols = max(1, (available_width - 30) // template_width)
            
            row, col = 0, 0  # Reset row and column counters
            
            # Display templates based on view mode
            print(f"Template view mode: {self.template_view_mode}")
            if self.template_view_mode == "grid" or self.template_view_mode == "icon":
                print("Using grid view for templates")
                # Grid view
                for template in templates:
                    try:
                        # Use a safer import approach
                        template_name = template.get('name', 'Unknown')
                        print(f"Creating template card for: {template_name}")
                        
                        # Import here to avoid circular imports, use a try-except block
                        try:
                            from app.templates.template_card_pyqt import TemplateCard
                        except ImportError as e:
                            print(f"Error importing TemplateCard: {e}")
                            # Create a simple placeholder frame instead
                            temp_frame = QFrame()
                            temp_layout = QVBoxLayout(temp_frame)
                            temp_label = QLabel(f"Template: {template_name}")
                            temp_label.setStyleSheet("color: white; background: transparent;")
                            temp_layout.addWidget(temp_label)
                            temp_frame.setStyleSheet("background-color: #333; padding: 10px; border-radius: 5px;")
                            temp_frame.setMinimumSize(150, 100)
                            template_card = temp_frame
                            # Create a mousePressEvent for the frame
                            def mousePressEvent(event, t=template):
                                self._on_template_select(t)
                            template_card.mousePressEvent = mousePressEvent.__get__(template_card, QFrame)
                        else:
                            template_card = TemplateCard(parent=self, template=template, app=self.app)
                            template_card.clicked.connect(lambda t=template: self._on_template_select(t))
                            
                        self.templates_grid.addWidget(template_card, row, col)
                        self.template_cards.append(template_card)
                        
                        # Update grid position
                        col += 1
                        if col >= max_cols:
                            col = 0
                            row += 1
                            
                    except Exception as e:
                        print(f"Error creating template card for {template.get('name', 'Unknown')}: {e}")
            else:
                print("Using list view for templates")
                # List view
                # Create a container for list view
                list_container = QFrame()
                list_container.setFrameShape(QFrame.NoFrame)
                list_container.setStyleSheet("background-color: transparent; border: none;")
                list_layout = QVBoxLayout(list_container)
                list_layout.setContentsMargins(0, 0, 0, 0)
                list_layout.setSpacing(0)  # No spacing between items
                
                # Add the list container to the grid
                self.templates_grid.addWidget(list_container, 0, 0, 1, 1)
                
                for i, template in enumerate(templates):
                    try:
                        template_name = template.get('name', 'Unknown')
                        template_desc = template.get('description', '')
                        print(f"Creating template list item for: {template_name}")
                        
                        # Create a custom list item regardless of whether TemplateListItem is available
                        list_item = QFrame()
                        list_item.setFrameShape(QFrame.NoFrame)
                        list_item.setFixedHeight(36)  # Fixed height for consistent rows
                        if i % 2:
                            list_item.setStyleSheet(f"background-color: {colors['card_bg']}; padding: 4px;")
                        else:
                            list_item.setStyleSheet(f"background-color: {colors['bg']}; padding: 4px;")
                        
                        item_layout = QHBoxLayout(list_item)
                        item_layout.setContentsMargins(8, 2, 8, 2)  # Reduced vertical margins
                        
                        # Icon/Type indicator
                        icon_label = QLabel("📄")
                        icon_label.setFont(QFont(SYSTEM_FONT, 14))  # Smaller font
                        icon_label.setStyleSheet("color: white; background: transparent;")
                        item_layout.addWidget(icon_label)
                        
                        # Name and description
                        text_container = QWidget()
                        text_layout = QHBoxLayout(text_container)  # Use horizontal layout
                        text_layout.setContentsMargins(0, 0, 0, 0)
                        text_layout.setSpacing(8)
                        
                        name_label = QLabel(template_name)
                        name_label.setFont(QFont(SYSTEM_FONT, 11, QFont.Bold))
                        name_label.setStyleSheet("color: white; background: transparent;")
                        text_layout.addWidget(name_label)
                        
                        if template_desc:
                            desc_label = QLabel(template_desc[:60] + ('...' if len(template_desc) > 60 else ''))
                            desc_label.setStyleSheet("color: #AAAAAA; background: transparent;")
                            # Make sure description doesn't push the name off-screen
                            name_label.setMinimumWidth(150)
                            name_label.setMaximumWidth(200)
                            text_layout.addWidget(desc_label, 1)  # Give stretch to description
                        
                        item_layout.addWidget(text_container, 1)  # Give stretch factor
                        
                        # Make the list item clickable
                        def mousePressEvent(event, t=template):
                            self._on_template_select(t)
                        list_item.mousePressEvent = mousePressEvent.__get__(list_item, QFrame)
                        list_item.setCursor(Qt.PointingHandCursor)
                        
                        list_layout.addWidget(list_item)
                        self.template_cards.append(list_item)
                        
                    except Exception as e:
                        print(f"Error creating template list item for {template.get('name', 'Unknown')}: {e}")
                        
            print("Templates displayed successfully")
        except Exception as e:
            print(f"Error in _display_templates: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_gallery(self):
        """Clear all cards from the gallery"""
        # First, delete all folder cards
        for card in self.folder_cards:
            try:
                card.deleteLater()
            except RuntimeError:
                pass
        self.folder_cards = []
        
        # Delete all template cards
        for card in self.template_cards:
            try:
                card.deleteLater()
            except RuntimeError:
                pass
        self.template_cards = []
        
        # Completely remove and recreate the folders container with a new grid layout
        if self.folders_container:
            self.folders_container.deleteLater()
        
        self.folders_container = QWidget()
        self.folders_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.folders_grid = QGridLayout(self.folders_container)
        self.folders_grid.setContentsMargins(0, 0, 0, 0)
        self.folders_grid.setHorizontalSpacing(6)
        self.folders_grid.setVerticalSpacing(12)
        self.folders_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.folders_scroll.setWidget(self.folders_container)
        
        # Completely remove and recreate the templates container with a new grid layout
        if self.templates_container:
            self.templates_container.deleteLater()
        
        self.templates_container = QWidget()
        self.templates_grid = QGridLayout(self.templates_container)
        self.templates_grid.setContentsMargins(0, 0, 0, 0)
        self.templates_grid.setHorizontalSpacing(5)
        self.templates_grid.setVerticalSpacing(5)
        self.templates_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.templates_section_layout.addWidget(self.templates_container)

    def _update_categories(self):
        """Update category dropdown with available categories"""
        # Get unique categories
        templates = self.template_manager.get_all_templates()
        categories = sorted(set(t.get('category', 'General') for t in templates))
        
        # Remember current category
        current_category = self.current_category
        
        # Clear and repopulate the combo box
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        
        # Always add "All" as the first option
        self.category_combo.addItem("All")
        
        # Add categories
        for category in categories:
            self.category_combo.addItem(category)
        
        # Set to current category if it exists, otherwise default to "All"
        index = self.category_combo.findText(current_category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentIndex(0)
            self.current_category = "All"
            
        self.category_combo.blockSignals(False)
    
    def _on_category_select(self, category):
        """Handle category selection"""
        self.current_category = category
        self.populate_gallery()
    
    def _on_search(self, search_text):
        """Handle search box changes"""
        self.populate_gallery()
    
    def _on_template_select(self, template):
        """Handle template selection"""
        try:
            # Update selected card
            for card in self.template_cards:
                # Check if this card's template is the selected one
                if hasattr(card, 'template') and card.template is template:
                    card.set_selected(True)
                    self.selected_template = template
                else:
                    card.set_selected(False)
            
            # Update edit/delete button state
            self._update_button_state()
            
            # Emit signal for template selection
            if template:
                self.template_selected.emit(template)
        except Exception as e:
            print(f"Error in template selection: {str(e)}")
            # Gracefully handle any errors
    
    def _on_add_template(self):
        """Handle add template button click"""
        # Get template name from user
        template_name, ok = QInputDialog.getText(
            self,
            "New Template",
            "Enter template name:"
        )
        
        if not ok or not template_name:
            return
            
        # Get category
        category, ok = QInputDialog.getItem(
            self,
            "Template Category",
            "Select category:",
            self.template_manager.get_categories(),
            0,
            False
        )
        
        if not ok or not category:
            return
        
        # Create an empty template - no file association yet
        success = self.template_manager.save_template(
            template_name,
            category,
            "",  # No file yet - user will add files in the editor
            "Standard"
        )
        
        if not success:
            QMessageBox.warning(self, "Error", f"Failed to create template '{template_name}'.")
            return
            
        # If we're in a folder, add the template to it
        if self.current_folder:
            print(f"Adding new template '{template_name}' to current folder '{self.current_folder}'")
            self.template_manager.add_to_folder(self.current_folder, template_name)
        
        # Get the newly created template
        new_template = self.template_manager.get_template_by_name(template_name)
        
        if not new_template:
            QMessageBox.warning(self, "Error", f"Failed to retrieve template '{template_name}' after creation.")
            self.populate_gallery()
            return
            
        # Open the editor immediately so user can add files and set up structure
        from app.dialogs.dialog_windows_pyqt import show_edit_template
        show_edit_template(self, new_template, self._on_template_edited)
        
        # Refresh the gallery to show the new template
        self.populate_gallery()
    
    def _on_edit_template(self):
        """Handle edit template button click"""
        if self.selected_template:
            show_edit_template(self, self.selected_template, self._on_template_edited)
    
    def _on_template_edited(self, template):
        """Handle template edit completion"""
        if template:
            print(f"DEBUG: Template edited: {template.get('name')}")
            
            # Check if the template has a structure
            if 'structure' in template:
                print(f"DEBUG: Template has structure data")
                structure_name = f"Template_{template.get('name')}"
                print(f"DEBUG: Saving structure as {structure_name}")
                
                # Save the structure first
                self.template_manager.save_custom_structure(structure_name, template.get('structure', []))
                
                # Make sure structure_name is set in the template
                template['structure_name'] = structure_name
            
            # Check if update_template exists, otherwise use save_template as fallback
            if hasattr(self.template_manager, 'update_template'):
                print(f"DEBUG: Using update_template method")
                self.template_manager.update_template(template)
            else:
                # Fallback to save_template if update_template doesn't exist
                print(f"DEBUG: Using save_template fallback")
                template_name = template.get('name', '')
                category = template.get('category', '')
                path = template.get('path', '')
                template_type = template.get('type', 'Standard')
                self.template_manager.save_template(template_name, category, path, template_type)
            
            self.populate_gallery()
    
    def _on_delete_template(self):
        """Handle delete template button click"""
        if self.selected_template:
            template_name = self.selected_template.get('name', 'Unnamed Template')
            
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
    
    def _on_manage_templates(self):
        """Handle manage templates button click"""
        show_manage_templates(self, self.template_manager, self.populate_gallery)
    
    def _on_folder_select(self, folder_name):
        """Handle folder selection - only selects the folder, enabling rename and delete buttons"""
        try:
            # Clear any previously selected template
            self.selected_template = None
            
            # Store the selected folder name
            self.selected_folder = folder_name
            
            # Deselect all folders
            for folder_card in self.folder_cards:
                if folder_card and not sip.isdeleted(folder_card) and hasattr(folder_card, 'set_selected'):
                    folder_card.set_selected(folder_card.folder_name == folder_name)
            
            # Enable rename and delete buttons
            self.rename_folder_button.setEnabled(True)
            self.delete_folder_button.setEnabled(True)
            
            # Update UI to show folder is selected but don't enter it
            self._update_button_state()
        except Exception as e:
            print(f"Error in _on_folder_select: {e}")

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
            self.delete_folder_button.hide()  # Always hide delete button
        else:
            # Folder view - show all folder management except rename and delete
            # (we're using in-place renaming and keyboard/context menu for deletion now)
            self.folder_nav.show()
            self.folder_label.show()
            self.add_folder_button.show()
            # Don't show rename button: self.rename_folder_button.show()
            self.delete_folder_button.hide()  # Always hide delete button
    
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
                
            # Show confirmation dialog
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete folder '{self.selected_folder}'?\n"
                "Templates in this folder will remain available but will be moved to the root.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Delete folder
                self.template_manager.delete_folder(self.selected_folder)
                self.selected_folder = None
                self.populate_gallery()
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
        """Update layout after resize with proper timing"""
        try:
            # Block signals to prevent repainting cascade
            self.blockSignals(True)
            
            # Force recalculation of container widths
            if hasattr(self, 'folders_container') and self.folders_container:
                parent_width = self.width()
                available_width = min(parent_width - 40, 1200)
                
                viewport_width = self.folders_scroll.viewport().width()
                if viewport_width > 0:
                    available_width = viewport_width
                
                # Set the width without triggering layout
                self.folders_container.setMinimumWidth(available_width)
                self.folders_container.setMaximumWidth(available_width)
            
            # Also update templates container width
            if hasattr(self, 'templates_container') and self.templates_container:
                parent_width = self.width()
                available_width = min(parent_width - 40, 1200)
                
                # Set the width without triggering layout
                self.templates_container.setMinimumWidth(available_width)
                self.templates_container.setMaximumWidth(available_width)
        finally:
            # Always unblock signals
            self.blockSignals(False)

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
                    card.icon_label.setFont(QFont(SYSTEM_FONT, icon_font_size))
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
    app.show_status_message(f"Template selected: {template.get('name', 'Unnamed')}")

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