#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QFont

from app.ui.color_scheme_pyqt import colors, get_color

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
        self.layout.addWidget(self.title)
        
        # Create the edit widget but don't add it to layout yet
        self.name_edit = QLineEdit(folder_name)
        self.name_edit.setFont(QFont(SYSTEM_FONT, 12))
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.setStyleSheet("color: white; background: rgba(60, 60, 60, 0.8); border: 1px solid gray; border-radius: 3px;")
        self.name_edit.editingFinished.connect(self._finish_rename)
        self.name_edit.hide()  # Hide by default
        self.layout.addWidget(self.name_edit)
        
        # Click timer for differentiating single from double click
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.setInterval(250)  # 250ms to differentiate single from double click
        self.click_timer.timeout.connect(self._handle_single_click)
        self.click_pending = False
        
        # Install event filter for mouse events
        self.installEventFilter(self)
        self.title.installEventFilter(self)
        self._update_styling()
    
    def _handle_single_click(self):
        """Handle single click after timer expires"""
        if self.click_pending:
            self.click_pending = False
            self.clicked.emit(self.folder_name)
            
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            # Start timer to wait for possible double click
            self.click_pending = True
            self.click_timer.start()
            event.accept()
            
    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        if event.button() == Qt.LeftButton:
            # Cancel any pending single click
            self.click_pending = False
            self.click_timer.stop()
            
            # Emit double click
            self.doubleClicked.emit(self.folder_name)
            event.accept()
            
    def _update_styling(self):
        """Update styling based on state"""
        if self.selected:
            # Selected style
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["accent"]};
                    border: 1px solid {colors["accent"]};
                    border-radius: 5px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent; padding-bottom: 0;")
            self.title.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent; margin-top: -8px;")
        elif self.hover:
            # Hover style
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["hover_bg"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent; padding-bottom: 0;")
            self.title.setStyleSheet(f"color: {colors['text']}; background: transparent; margin-top: -8px;")
        else:
            # Default style
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["card_bg"]};
                    border: 1px solid {colors["card_bg"]};
                    border-radius: 5px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent; padding-bottom: 0;")
            self.title.setStyleSheet(f"color: {colors['text']}; background: transparent; margin-top: -8px;")
            
    def _start_rename(self):
        """Start renaming the folder"""
        self.rename_mode = True
        self.title.hide()
        self.rename_field.setText(self.folder_name)
        self.rename_field.show()
        self.rename_field.setFocus()
        self.rename_field.selectAll()
        
    def enterEvent(self, event):
        """Handle mouse enter - update hover state"""
        self.hover = True
        self._update_styling()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave - update hover state"""
        self.hover = False
        self._update_styling()
        super().leaveEvent(event)
    
    def _finish_rename(self):
        """Finish inline renaming and apply the change"""
        if not self.editing:
            return
            
        self.editing = False
        new_name = self.name_edit.text().strip()
        
        # Hide edit field, show label
        self.name_edit.hide()
        self.title.show()
        
        # If name is empty or unchanged, do nothing
        if not new_name or new_name == self.folder_name:
            return
            
        # Emit signal with old and new name
        self.renameDone.emit(self.folder_name, new_name)

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
    
    def eventFilter(self, obj, event):
        """Filter events for mouse hover and clicks"""
        if obj is self:
            if event.type() == QEvent.Enter:
                self.hover = True
                self._update_styling()
                return True
            elif event.type() == QEvent.Leave:
                self.hover = False
                self._update_styling()
                return True
        elif obj is self.title and event.type() == QEvent.MouseButtonPress:
            # When clicking directly on the title, start inline editing
            self._start_rename()
            return True  # Stop event propagation
                
        return super().eventFilter(obj, event)
    
    def set_selected(self, selected):
        """Set this item as selected"""
        self.selected = selected
        self._update_styling()
    
    def enterEvent(self, event):
        """Handle mouse enter - update hover state"""
        self.hover = True
        self._update_styling()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave - update hover state"""
        self.hover = False
        self._update_styling()
        super().leaveEvent(event)
        
    def set_row_type(self, row_type):
        """Set whether this is an odd or even row for styling"""
        self.setProperty("row_type", row_type)
        self._update_styling()
        
    def _update_styling(self):
        """Update the styling based on current state"""
        if self.selected:
            # Selected style (blue background, white text)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["accent"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            self.icon_label.setStyleSheet("color: white; background: transparent;")
            self.title.setStyleSheet("color: white; background: transparent;")
        elif self.hover:
            # Hover style (slightly lighter background)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["highlight_bg"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent;")
            self.title.setStyleSheet("color: white; background: transparent;")
        else:
            # Normal style - use alternating row colors for list
            if self.property("row_type") == "odd":
                bg_color = colors["hover_bg"]  # Darker for odd rows - using hover_bg as it's darker
            else:
                bg_color = colors["card_bg"]  # Lighter for even rows
                
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent;")
            self.title.setStyleSheet("color: white; background: transparent;")
    
    def mousePressEvent(self, event):
        """Handle mouse press directly"""
        if event.button() == Qt.LeftButton:
            # Handle clicks on the title separately
            if self.title.geometry().contains(event.pos()):
                self.renameRequested.emit(self.folder_name)
                event.accept()
            else:
                # Start timer to wait for possible double click
                self.click_pending = True
                self.click_timer.start()
                event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click directly"""
        if event.button() == Qt.LeftButton:
            # Cancel any pending single click
            self.click_pending = False
            self.click_timer.stop()
            
            # Only emit double click if not clicking on title
            if not self.title.geometry().contains(event.pos()):
                self.doubleClicked.emit(self.folder_name)
                event.accept()
    
    def _start_rename(self):
        """Start inline renaming of folder"""
        # Check if this is a default folder that cannot be renamed
        if self.folder_name in ["General", "Development", "Business"]:
            if hasattr(self.app, "show_message"):
                self.app.show_message(f"'{self.folder_name}' is a default folder and cannot be renamed.")
            else:
                QMessageBox.warning(None, "Error", f"'{self.folder_name}' is a default folder and cannot be renamed.")
            return
            
        # Switch to edit mode
        self.editing = True
        
        # Hide label, show edit field
        self.title.hide()
        self.name_edit.setText(self.folder_name)
        self.name_edit.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()
    
    def _finish_rename(self):
        """Finish inline renaming and apply the change"""
        if not self.editing:
            return
            
        self.editing = False
        new_name = self.name_edit.text().strip()
        
        # Hide edit field, show label
        self.name_edit.hide()
        self.title.show()
        
        # If name is empty or unchanged, do nothing
        if not new_name or new_name == self.folder_name:
            return
            
        # Emit signal with old and new name
        self.renameDone.emit(self.folder_name, new_name)
    
    def keyPressEvent(self, event):
        """Handle escape key to cancel editing"""
        if self.editing and event.key() == Qt.Key_Escape:
            self.editing = False
            self.name_edit.hide()
            self.title.show()
        else:
            super().keyPressEvent(event)
