#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import platform
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QFileDialog, QMessageBox,
                           QInputDialog, QMenu, QAction, QApplication, QComboBox, QSizePolicy,
                           QSlider, QButtonGroup, QToolButton)
from PyQt5.QtCore import (Qt, pyqtSignal, QSize, QPoint, QEvent, QMimeData, 
                        QByteArray)
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
    
    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        
        # Setup styling
        self.setFrameShape(QFrame.NoFrame)  # No frame/container around the folder
        self.setFixedSize(180, 180)  # Keep consistent size that fits with gallery width calculation
        self.setCursor(Qt.PointingHandCursor)
        
        # Enable drop functionality
        self.setAcceptDrops(True)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 0)  # Remove bottom padding to pull name closer to icon
        self.layout.setSpacing(0)  # Reduce spacing between elements to minimum
        
        # Icon - Make folder icon larger and more distinct
        self.icon_layout = QHBoxLayout()
        self.icon_layout.setAlignment(Qt.AlignCenter)
        self.icon_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Folder icon - more obvious folder appearance
        self.icon_label = QLabel("📁")  # Using a folder emoji
        self.icon_label.setFont(QFont(SYSTEM_FONT, 64))  # Larger font for better visibility
        self.icon_label.setStyleSheet("color: goldenrod; background: transparent; padding-bottom: 0;")
        self.icon_layout.addWidget(self.icon_label)
        self.layout.addLayout(self.icon_layout)
        
        # Folder name - simpler display directly under the icon
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(SYSTEM_FONT, 12))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: inherit; background: transparent; margin-top: -8px;")  # Negative margin to pull up closer to icon
        self.title.setWordWrap(True)
        self.layout.addWidget(self.title)
        
        # Install event filter for mouse events
        self.installEventFilter(self)
        self._update_styling()
        
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
            return
            
        try:
            # Check if template exists
            template = self.app.template_manager.get_template_by_name(template_name)
            if not template:
                print(f"Template not found: {template_name}")
                return False
                
            # Add template to folder
            result = self.app.template_manager.add_to_folder(self.folder_name, template_name)
            
            if result:
                # Show success message
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Template '{template_name}' added to folder '{self.folder_name}'"
                )
                
                # Refresh the gallery
                if hasattr(self.parent(), 'populate_gallery'):
                    self.parent().populate_gallery()
            
            return result
        except Exception as e:
            print(f"Error adding template to folder: {e}")
            return False
    
    def eventFilter(self, obj, event):
        """Handle mouse events for hover effects"""
        if obj == self:
            if event.type() == QEvent.Enter:
                self._on_hover_enter()
            elif event.type() == QEvent.Leave:
                self._on_hover_leave()
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.clicked.emit(self.folder_name)
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
        """Update card styling based on state"""
        if self.selected:
            bg_color = colors["highlight_bg_transparent"]
            text_color = colors["highlight_text"]
        elif self.hover:
            bg_color = colors["hover_bg_transparent"]
            text_color = colors["text"]
        else:
            bg_color = "transparent"
            text_color = colors["text"]
            
        # Apply styles to specific labels instead of all labels to prevent expanding
        self.title.setStyleSheet(f"color: {text_color}; background: transparent;")
        
        # Only apply background style to the frame
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 8px;
            }}
        """)

class TemplateFolderListItem(QFrame):
    """Template folder list item widget for displaying a folder in list view"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        
        # Setup styling - No frame to make it cleaner like macOS
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(36)  # Slightly shorter like macOS
        self.setCursor(Qt.PointingHandCursor)
        
        # Enable drop functionality
        self.setAcceptDrops(True)
        
        # Layout (horizontal for list view)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 2, 10, 2)  # Reduce vertical padding
        self.layout.setSpacing(8)  # Tighten spacing
        
        # Folder icon - smaller for list view
        self.icon_label = QLabel("📁")
        self.icon_label.setFont(QFont(SYSTEM_FONT, 20))  # Slightly smaller
        self.icon_label.setStyleSheet("color: goldenrod; background: transparent;")
        self.icon_label.setFixedWidth(24)  # Narrower width
        self.layout.addWidget(self.icon_label)
        
        # Folder name - make it white for better readability
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(SYSTEM_FONT, 12))
        self.title.setStyleSheet("color: white; background: transparent;")
        self.layout.addWidget(self.title, 1)  # Give it stretch factor
        
        # Install event filter for mouse events
        self.installEventFilter(self)
        self._update_styling()
    
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
            return
            
        # Get the template
        template = self.app.template_manager.get_template_by_name(template_name)
        if not template:
            return
            
        # Ask for confirmation
        from PyQt5.QtWidgets import QMessageBox
        result = QMessageBox.question(
            self,
            "Move Template",
            f"Move template '{template_name}' to folder '{self.folder_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # Update template and save
            self.app.template_manager.move_template_to_folder(template_name, self.folder_name)
            
            # Refresh the gallery
            if hasattr(self.parent(), 'populate_gallery'):
                self.parent().populate_gallery()
    
    def eventFilter(self, obj, event):
        """Filter events for mouse tracking"""
        if obj is self:
            if event.type() == QEvent.MouseButtonPress:
                self.clicked.emit(self.folder_name)
                return True
            elif event.type() == QEvent.Enter:
                self._on_hover_enter()
                return False
            elif event.type() == QEvent.Leave:
                self._on_hover_leave()
                return False
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
            # Selected item - macOS style highlight (blue bg, white text)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["accent"]};
                    border: none;
                    border-radius: 0px;
                }}
                QLabel {{
                    color: white;
                    background: transparent;
                }}
            """)
        elif self.hover:
            # Hover state - subtle light gray bg like macOS
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(200, 200, 200, 50);
                    border: none;
                    border-radius: 0px;
                }}
                QLabel {{
                    color: white;
                    background: transparent;
                }}
            """)
        else:
            # Normal state - transparent bg like macOS
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                }}
                QLabel {{
                    color: white;
                    background: transparent;
                }}
            """)

class TemplateListItem(QFrame):
    """Template list item widget for displaying a template in list view"""
    
    clicked = pyqtSignal(object)
    
    def __init__(self, parent=None, template=None, app=None):
        super().__init__(parent)
        self.template = template
        self.app = app
        self.selected = False
        self.hover = False
        
        # Configure frame appearance
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        self.setFixedHeight(50)  # Fixed height for list items
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
        self.name_label.setStyleSheet("color: inherit; font-weight: bold; background: transparent;")
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
                self._on_hover_enter()
                return False
            elif event.type() == QEvent.Leave:
                self._on_hover_leave()
                return False
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
        """Update the styling based on current state"""
        if self.selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["selected_bg"]};
                    border: 1px solid {colors["accent"]};
                    border-radius: 4px;
                }}
            """)
        elif self.hover:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["hover_bg"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 4px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["card_bg"]};
                    border: 1px solid {colors["border"]};
                    border-radius: 4px;
                }}
            """)

class TemplateGallery(QWidget):
    """Main widget for displaying and managing templates"""
    
    template_selected = pyqtSignal(dict)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.template_manager = app.template_manager if hasattr(app, 'template_manager') else None
        self.current_folder = None
        self.current_category = "All"
        self.current_search = ""
        self.selected_template = None
        self.template_cards = []
        self.folder_cards = []
        self.view_mode = "icon"  # Default view mode: "icon" or "list"
        self.icon_scale = 100  # Default icon scale (percentage)
        
        # Import necessary modules for drag and drop
        global QApplication, QDrag, QMimeData, QByteArray  
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QDrag
        from PyQt5.QtCore import QMimeData, QByteArray
        
        # Additional imports for new UI elements
        from PyQt5.QtWidgets import QSlider, QButtonGroup, QToolButton, QSizePolicy
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
        
        # Setup widget
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
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
        
        # View controls - add at the beginning of the button area
        self.view_controls = QWidget()
        self.view_controls_layout = QHBoxLayout(self.view_controls)
        self.view_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.view_controls_layout.setSpacing(5)
        
        # Create view toggle buttons
        self.view_toggle_group = QButtonGroup(self)
        
        self.icon_view_btn = QToolButton()
        self.icon_view_btn.setText("Icons")
        self.icon_view_btn.setCheckable(True)
        self.icon_view_btn.setChecked(True)  # Default is icon view
        self.icon_view_btn.clicked.connect(lambda: self._set_view_mode("icon"))
        self.view_toggle_group.addButton(self.icon_view_btn)
        self.view_controls_layout.addWidget(self.icon_view_btn)
        
        self.list_view_btn = QToolButton()
        self.list_view_btn.setText("List")
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.clicked.connect(lambda: self._set_view_mode("list"))
        self.view_toggle_group.addButton(self.list_view_btn)
        self.view_controls_layout.addWidget(self.list_view_btn)
        
        # Add label for folder controls
        folder_label = QLabel("Folder View:")
        folder_label.setStyleSheet(f"color: {colors['text']};")
        self.view_controls_layout.addWidget(folder_label)
        
        # Add slider for icon scaling - macOS style
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(50)   # 50% minimum size
        self.size_slider.setMaximum(150)  # 150% maximum size
        self.size_slider.setValue(100)    # Default 100%
        self.size_slider.setFixedWidth(100)
        # Remove tick marks and style for macOS look
        self.size_slider.setTickPosition(QSlider.NoTicks)
        self.size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #CCCCCC;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #BBBBBB;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #EEEEEE;
            }
        """)
        self.size_slider.valueChanged.connect(self._on_icon_scale_changed)
        # Initially visible since default is icon view
        self.size_slider.setVisible(self.view_mode == "icon")
        self.view_controls_layout.addWidget(self.size_slider)
        
        self.button_layout.addWidget(self.view_controls)
        self.button_layout.addStretch(1)  # Push view controls to the left
        
        # Folder management buttons
        self.add_folder_button = QPushButton("New Folder")
        self.add_folder_button.setStyleSheet(BUTTON_STYLE)
        self.add_folder_button.clicked.connect(self._on_add_folder)
        self.button_layout.addWidget(self.add_folder_button)
        
        self.rename_folder_button = QPushButton("Rename Folder")
        self.rename_folder_button.setStyleSheet(BUTTON_STYLE)
        self.rename_folder_button.clicked.connect(self._on_rename_folder)
        self.rename_folder_button.setEnabled(False)
        self.button_layout.addWidget(self.rename_folder_button)
        
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
        
        # Template gallery
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setFrameShape(QFrame.NoFrame)
        self.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.gallery_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Ensure scroll area fills available space
        self.gallery_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.gallery_widget = QWidget()
        # Update sizePolicy to allow horizontal expansion
        self.gallery_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Remove maximum width restriction to allow full expansion
        # Calculate width based on standard card size and columns
        card_width = 200  # Standard card width with margins
        max_cols = 4      # Maximum columns for templates
        padding = 40      # Extra padding
        # self.gallery_widget.setMaximumWidth(card_width * max_cols + padding)
        
        self.gallery_layout = QGridLayout(self.gallery_widget)
        self.gallery_layout.setContentsMargins(10, 10, 10, 10)
        self.gallery_layout.setSpacing(20)
        # Allow alignment but don't restrict expansion
        self.gallery_layout.setAlignment(Qt.AlignTop)
        
        self.gallery_scroll.setWidget(self.gallery_widget)
        
        self.layout.addWidget(self.gallery_scroll)
        
        # Populate gallery
        self.populate_gallery()
    
    def populate_gallery(self):
        """Populate the template gallery with cards"""
        # Clear existing cards
        self._clear_gallery()
        
        search_text = self.search_box.get().lower() if hasattr(self.search_box, 'get') else ""
        self.current_search = search_text
        
        # Update categories
        self._update_categories()
        
        # If we're viewing the root (no folder selected)
        if self.current_folder is None:
            # Show categories and template folders
            folders = self.template_manager.get_folders()
            
            # Add folder cards
            row, col = 0, 0
            
            # Configure columns based on view mode - only for folders
            if self.view_mode == "icon":
                # Ensure consistent number of columns for folders layout 
                # and match card width calculation from initialization
                max_cols = 4  # Consistent column count, same as for templates
            else:  # list view
                max_cols = 1  # Single column for list view
                
                # Add a container for list view with subtle divider lines
                if folders and not search_text:
                    list_container = QFrame()
                    list_container.setFrameShape(QFrame.NoFrame)
                    list_container.setStyleSheet(f"""
                        QFrame {{
                            background-color: transparent;
                            border: none;
                        }}
                    """)
                    list_layout = QVBoxLayout(list_container)
                    list_layout.setContentsMargins(0, 0, 0, 0)
                    list_layout.setSpacing(0)  # No spacing between items
            
            # Add header for folders section if there are folders
            if folders and not search_text:
                folders_header = QLabel("Folders")
                folders_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
                folders_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0;")
                folders_header.setAlignment(Qt.AlignLeft)  # Ensure alignment is left
                self.gallery_layout.addWidget(folders_header, row, 0, 1, max_cols)
                row += 1

                # If we're in list view, prepare the container
                if self.view_mode == "list":
                    self.gallery_layout.addWidget(list_container, row, 0, 1, max_cols)
                    row += 1  # Move to the next row for additional content
            
            folder_count = 0
            
            for folder in folders:
                # Skip if doesn't match search
                if search_text and search_text not in folder.lower():
                    continue
                    
                if self.view_mode == "icon":
                    # Icon view - use standard folder cards
                    folder_card = TemplateFolderCard(parent=self, folder_name=folder, app=self.app)
                    
                    # Adjust size based on current scale (only for icon view)
                    scale_factor = self.icon_scale / 100.0
                    base_width = 180
                    base_height = 180
                    new_width = int(base_width * scale_factor)
                    new_height = int(base_height * scale_factor)
                    folder_card.setFixedSize(new_width, new_height)
                    
                    # Adjust icon font size
                    icon_font_size = int(64 * scale_factor)
                    folder_card.icon_label.setFont(QFont(SYSTEM_FONT, icon_font_size))
                
                    folder_card.clicked.connect(self._on_folder_select)
                    self.gallery_layout.addWidget(folder_card, row, col)
                    self.folder_cards.append(folder_card)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                else:
                    # List view - create a custom list item for the folder
                    folder_card = TemplateFolderListItem(parent=self, folder_name=folder, app=self.app)
                    folder_card.clicked.connect(self._on_folder_select)
                    
                    # Add list item to the container
                    list_layout.addWidget(folder_card)
                    
                    # Add a separator line after each item (except the last one)
                    folder_count += 1
                    if folder_count < len(folders):
                        separator = QFrame()
                        separator.setFrameShape(QFrame.HLine)
                        separator.setFrameShadow(QFrame.Plain)
                        separator.setStyleSheet(f"""
                            QFrame {{
                                background-color: transparent;
                                border: none;
                                border-top: 1px solid rgba(100, 100, 100, 100);
                                max-height: 1px;
                            }}
                        """)
                        list_layout.addWidget(separator)
                    
                    self.folder_cards.append(folder_card)
            
            # Add spacer between folders and templates
            if folders and not search_text:
                spacer = QLabel("")
                spacer.setFixedHeight(20)
                self.gallery_layout.addWidget(spacer, row, 0, 1, max_cols)
                row += 1
            
            # Add templates section header
            if not search_text:
                templates_header = QLabel("Templates")
                templates_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
                templates_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0;")
                templates_header.setAlignment(Qt.AlignLeft)
                self.gallery_layout.addWidget(templates_header, row, 0, 1, 4)  # Always use 4 columns for templates
                row += 1
            
            # Get templates - filter by category if needed
            templates = self.template_manager.get_all_templates()
            if self.current_category != "All":
                templates = [t for t in templates if self.current_category in t.get('categories', [])]
            
            # Filter by search if needed
            if search_text:
                templates = [t for t in templates if 
                           search_text in t.get('name', '').lower() or 
                           search_text in t.get('description', '').lower() or
                           any(search_text in cat.lower() for cat in t.get('categories', []))]

            # Add template cards - always use icon view for templates (4 column grid)
            col = 0  # Reset column counter
            for template in templates:
                # Skip if it's in a folder
                if template.get('folder'):
                    continue
                
                # Always use icon view for templates
                from app.templates.template_card_pyqt import TemplateCard
                template_card = TemplateCard(parent=self, template=template, app=self.app)
                
                template_card.clicked.connect(lambda t=template: self._on_template_select(t))
                self.gallery_layout.addWidget(template_card, row, col)
                self.template_cards.append(template_card)
                
                col += 1
                if col >= 4:  # Always use 4 columns for templates
                    col = 0
                    row += 1
                
            # Add stretch to push everything to the top
            self.gallery_layout.setRowStretch(row + 1, 1)
        else:
            # Viewing a specific folder - always use icon view for templates in folders
            templates = self.template_manager.get_templates_in_folder(self.current_folder)
            
            # Filter by search if needed
            if search_text:
                templates = [t for t in templates if 
                           search_text in t.get('name', '').lower() or 
                           search_text in t.get('description', '').lower()]
            
            # Always use a 4 column grid for templates
            max_cols = 4
            
            # Add templates from the folder
            row, col = 0, 0
            for template in templates:
                # Always use icon view for templates
                from app.templates.template_card_pyqt import TemplateCard
                template_card = TemplateCard(parent=self, template=template, app=self.app)
                
                template_card.clicked.connect(lambda t=template: self._on_template_select(t))
                self.gallery_layout.addWidget(template_card, row, col)
                self.template_cards.append(template_card)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # Add stretch to push everything to the top
            self.gallery_layout.setRowStretch(row + 1, 1)
        
        # Update folder management UI visibility
        self._update_folder_ui()
        
        # Update button states
        self._update_button_state()

    def _clear_gallery(self):
        """Clear all cards from the gallery"""
        for card in self.template_cards:
            self.gallery_layout.removeWidget(card)
            card.deleteLater()
        self.template_cards = []
        
        for card in self.folder_cards:
            self.gallery_layout.removeWidget(card)
            card.deleteLater()
        self.folder_cards = []

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
        self.template_selected.emit(template)
    
    def _on_add_template(self):
        """Handle add template button click"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Template File")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai)")
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                template_name = os.path.basename(file_path)
                template_name, _ = os.path.splitext(template_name)
                
                # Get additional info from user
                category, ok = QInputDialog.getItem(
                    self,
                    "Template Category",
                    "Select category:",
                    self.template_manager.get_categories(),
                    0,
                    False
                )
                
                if ok and category:
                    # Create template
                    success = self.template_manager.save_template(
                        template_name,
                        category,
                        file_path,
                        "Standard"
                    )
                    
                    if success:
                        QMessageBox.information(self, "Success", f"Template '{template_name}' added successfully.")
                        self.populate_gallery()
                    else:
                        QMessageBox.warning(self, "Error", f"Failed to add template '{template_name}'.")
    
    def _on_edit_template(self):
        """Handle edit template button click"""
        if self.selected_template:
            show_edit_template(self, self.selected_template, self._on_template_edited)
    
    def _on_template_edited(self, template):
        """Handle template edit completion"""
        if template:
            self.template_manager.update_template(template)
            self.populate_gallery()
    
    def _on_delete_template(self):
        """Handle delete template button click"""
        if self.selected_template:
            confirm = QMessageBox.question(
                self, 
                "Confirm Delete", 
                f"Are you sure you want to delete template '{self.selected_template.get('name', 'Unnamed Template')}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                self.template_manager.delete_template(self.selected_template)
                self.selected_template = None
                self.populate_gallery()
    
    def _on_manage_templates(self):
        """Handle manage templates button click"""
        show_manage_templates(self, self.template_manager, self.populate_gallery)
    
    def _on_folder_select(self, folder_name):
        """Handle folder selection"""
        self.current_folder = folder_name
        self.folder_label.setText(f"Current Folder: {folder_name}")
        self.populate_gallery()
        
    def _on_back_to_all(self):
        """Go back to all folders view"""
        self.current_folder = None
        self.populate_gallery()
    
    def _update_folder_ui(self):
        """Update the folder management UI based on current state"""
        if self.current_folder is None:
            # Root view - show only add folder
            self.folder_nav.hide()
            self.folder_label.hide()
            self.add_folder_button.show()
            self.rename_folder_button.hide()
            self.delete_folder_button.hide()
        else:
            # Folder view - show all folder management
            self.folder_nav.show()
            self.folder_label.show()
            self.add_folder_button.show()
            self.rename_folder_button.show()
            self.delete_folder_button.show()
    
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
        """Handle rename folder button click"""
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

    def resizeEvent(self, event):
        """Handle widget resize events to maintain proper layout"""
        super().resizeEvent(event)
        
        # We no longer need to restrict the width since we want it to expand
        # with the window. This method is kept for future customizations.
        pass

    def _on_icon_scale_changed(self, value):
        """Handle icon scale slider changes"""
        self.icon_scale = value
        self._update_card_sizes()
        
    def _update_card_sizes(self):
        """Update card sizes based on icon scale - only for folder cards"""
        # Default sizes for 100% scale
        base_width = 180
        base_height = 180
        
        # Calculate new sizes
        scale_factor = self.icon_scale / 100.0
        new_width = int(base_width * scale_factor)
        new_height = int(base_height * scale_factor)
        
        # Update folder cards only
        for card in self.folder_cards:
            if isinstance(card, TemplateFolderCard):  # Only scale icon view cards
                card.setFixedSize(new_width, new_height)
                # Adjust font size of icon
                icon_font_size = int(64 * scale_factor)
                card.icon_label.setFont(QFont(SYSTEM_FONT, icon_font_size))
            
        # Refresh layout
        self.gallery_layout.update()
        
    def _set_view_mode(self, mode):
        """Switch between icon and list view modes"""
        if mode == self.view_mode:
            return  # No change needed
            
        self.view_mode = mode
        
        # Show/hide slider based on view mode
        # Only show slider in icon view since it doesn't apply to list view
        self.size_slider.setVisible(mode == "icon")
        
        # Setup appropriate view
        self._clear_gallery()
        self.populate_gallery()

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