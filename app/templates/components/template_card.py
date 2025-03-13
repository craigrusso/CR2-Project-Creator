# template_card.py

from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QMenu, QAction, QMessageBox, 
    QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QMimeData, QSize, QPoint, QRect
from PyQt5.QtGui import QPixmap, QFont, QDrag, QPainter, QColor, QBrush, QPen, QIcon, QCursor
import os
from .utils import SYSTEM_FONT
from .common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED, colors
from app.ui.color_scheme_pyqt import MENU_DESTRUCTIVE_ITEM_STYLE, DELETE_TEXT_STYLE
from app.templates.components.menu_actions import ContextMenu

def template_icon_path(template_name=None):
    """Return the path to the template icon."""
    # Use our new SVG icon as the default
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                           "assets", "icons", "template_structure_icon.svg")
    
    # Check if template-specific icon exists
    if template_name:
        # First try SVG
        custom_icon_svg = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 "assets", "icons", "templates", f"{template_name}.svg")
        if os.path.exists(custom_icon_svg):
            icon_path = custom_icon_svg
        else:
            # Then try PNG
            custom_icon_png = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    "assets", "icons", "templates", f"{template_name}.png")
            if os.path.exists(custom_icon_png):
                icon_path = custom_icon_png
    
    return icon_path

class TemplateCard(QFrame):
    clicked = pyqtSignal(object)
    doubleClicked = pyqtSignal(str)
    dragStarted = pyqtSignal(str)
    editRequested = pyqtSignal(str)  # New signal for edit action
    deleteRequested = pyqtSignal(str)  # New signal for delete action
    moveToFolderRequested = pyqtSignal(str, str)  # template_name, folder_name

    def __init__(self, parent=None, template=None, app=None):
        super().__init__(parent)
        self.template = template or {}  # Use empty dict if template is None
        self.app = app
        self.hover = False
        self.selected = False
        self.setAcceptDrops(False)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(140, 140)
        self.setStyleSheet(f"background-color: {CARD_NORMAL}; border-radius: 6px;")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Icon container with fixed height to maintain consistent positioning
        icon_container = QWidget()
        icon_container.setFixedHeight(70)  # Fixed height for icon area
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        # Template icon
        self.icon_label = QLabel()
        try:
            icon_path = template_icon_path(template_name=self.template_name())
            if icon_path.endswith('.svg'):
                # Handle SVG files using QPixmap and QSvgRenderer
                from PyQt5.QtSvg import QSvgRenderer
                from PyQt5.QtCore import QByteArray, QSize
                
                # Create a renderer for the SVG
                with open(icon_path, 'r') as f:
                    svg_content = f.read()
                
                renderer = QSvgRenderer(QByteArray(svg_content.encode()))
                if renderer.isValid():
                    # Create a pixmap to render to
                    pixmap = QPixmap(64, 64)
                    pixmap.fill(Qt.transparent)  # Make the background transparent
                    
                    # Paint the SVG on the pixmap
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    self.icon_label.setPixmap(pixmap)
                else:
                    # Fallback to text
                    self.icon_label.setText("📄")
                    font = QFont(SYSTEM_FONT)
                    font.setPointSize(24)
                    self.icon_label.setFont(font)
            else:
                # Handle PNG or fallback
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.icon_label.setPixmap(pixmap)
                else:
                    # If pixmap is null, use text as a fallback
                    self.icon_label.setText("📄")
                    font = QFont(SYSTEM_FONT)
                    font.setPointSize(24)
                    self.icon_label.setFont(font)
        except Exception as e:
            print(f"ERROR: Failed to load template icon: {e}")
            # Use text as a fallback
            self.icon_label.setText("📄")
            font = QFont(SYSTEM_FONT)
            font.setPointSize(24)
            self.icon_label.setFont(font)
        
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.icon_label, 1, Qt.AlignCenter)
        layout.addWidget(icon_container)
        
        # Text container with fixed height
        text_container = QWidget()
        text_container.setFixedHeight(50)  # Fixed height for text area
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        # Template name label
        self.name_label = QLabel(self.template_name(), self)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(30)  # Limit height of name label
        font = QFont(SYSTEM_FONT)
        font.setPointSize(10)
        self.name_label.setFont(font)
        self.name_label.setStyleSheet(f"color: {colors['text']};")
        text_layout.addWidget(self.name_label)
        
        # Template category label
        category = self.template.get("category", self.template.get("type", "Custom"))
        self.category_label = QLabel(str(category), self)
        self.category_label.setAlignment(Qt.AlignCenter)
        font = QFont(SYSTEM_FONT)
        font.setPointSize(8)
        self.category_label.setFont(font)
        self.category_label.setStyleSheet(f"color: {colors['secondary_text']};")
        text_layout.addWidget(self.category_label)
        
        layout.addWidget(text_container)
        
        # Initial styling
        self._update_styling()

    def template_name(self):
        """Get the template name, handling different formats of template data."""
        if not self.template:
            return "Unnamed Template"
            
        # Handle different ways the name might be stored
        if isinstance(self.template, dict):
            return self.template.get("name", "Unnamed Template")
        elif isinstance(self.template, str):
            return self.template
        else:
            return str(self.template)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.template)

    def mouseDoubleClickEvent(self, event):
        """Handle double click to open template editor"""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.template_name())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            mime_data = QMimeData()
            mime_data.setText(self.template_name())

            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.setPixmap(QPixmap(self.grab()))
            drag.exec_(Qt.MoveAction)
            event.accept()

    def enterEvent(self, event):
        self.hover = True
        self._update_styling()

    def leaveEvent(self, event):
        self.hover = False
        self._update_styling()

    def set_selected(self, selected):
        self.selected = selected
        self._update_styling()

    def _update_styling(self):
        if self.selected:
            # Only style the container with a border, let children inherit the background
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['highlight_bg']};
                    border: 2px solid {colors['accent']};
                    border-radius: 6px;
                }}
                QLabel {{
                    color: {colors['highlight_text']};
                    background-color: transparent;
                    border: none;
                }}
            """)
            
            # Set text color but no borders on child elements
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet("color: white; background-color: transparent; border: none;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet("color: white; background-color: transparent; border: none; font-weight: bold;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet("color: white; background-color: transparent; border: none;")
                
        elif self.hover:
            # Hover styling - clean with no individual element borders
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['hover_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 6px;
                }}
                QLabel {{
                    color: {colors['text']};
                    background-color: transparent;
                    border: none;
                }}
            """)
            
            # Reset label styles for hover state without borders
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet("color: white; background-color: transparent; border: none;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet("color: white; background-color: transparent; border: none;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet("color: #AAAAAA; background-color: transparent; border: none;")
                
        else:
            # Default styling - clean with no borders on individual elements
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['card_bg']};
                    border-radius: 6px;
                }}
                QLabel {{
                    color: {colors['text']};
                    background-color: transparent;
                    border: none;
                }}
            """)
            
            # Reset label styles without borders
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet("color: white; background-color: transparent; border: none;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet("color: white; background-color: transparent; border: none;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet("color: #AAAAAA; background-color: transparent; border: none;")

    def keyPressEvent(self, event):
        """Handle key press events for template operations"""
        # Handle both Delete and Backspace (for Mac) for template deletion when selected
        if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            self.deleteRequested.emit(self.template_name())
        super().keyPressEvent(event)
    
    def contextMenuEvent(self, event):
        """Show context menu when right-clicked"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        # Create context menu using our custom class
        context_menu = ContextMenu(self)
        
        # Add "Edit" action
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.editRequested.emit(self.template_name()))
        context_menu.addAction(edit_action)
        
        # Add "Delete" action using our helper method for red styling
        context_menu.addRedDeleteAction(
            parent=self,
            callback=lambda: self.deleteRequested.emit(self.template_name())
        )
        
        # Add separator
        context_menu.addSeparator()
        
        # Add move actions
        move_to_menu = ContextMenu(context_menu)
        move_to_menu.setTitle("Move to...")
        
        # Find current folder of this template
        current_folder = None
        template_manager = self.app.template_manager
        if hasattr(template_manager, 'folders'):
            for folder_name, templates in template_manager.folders.items():
                if self.template_name() in templates:
                    current_folder = folder_name
                    break
        
        # Add "Move to Root" option if template is in a folder
        if current_folder:
            move_to_root_action = QAction("Root (No Folder)", self)
            move_to_root_action.triggered.connect(lambda: self._move_template_out_of_folder(current_folder))
            move_to_menu.addAction(move_to_root_action)
            
            move_to_menu.addSeparator()
        
        # Add all folders except current one
        if hasattr(template_manager, 'folders'):
            folders = sorted(list(template_manager.folders.keys()))
            for folder_name in folders:
                # Skip the current folder
                if folder_name == current_folder:
                    continue
                    
                folder_action = QAction(folder_name, self)
                folder_action.triggered.connect(lambda checked=False, f=folder_name: 
                                               self._move_to_folder_and_hide(f))
                move_to_menu.addAction(folder_action)
        
        # Only add the Move To menu if it has items
        if not move_to_menu.isEmpty():
            context_menu.addMenu(move_to_menu)
        
        # Show the menu
        context_menu.exec_(event.globalPos())
    
    def _move_template_out_of_folder(self, current_folder):
        """Move template out of its current folder and hide it for immediate feedback"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        template_name = self.template_name()
        template_manager = self.app.template_manager
        
        # Remove template from the current folder
        if hasattr(template_manager, 'folders') and current_folder in template_manager.folders:
            if template_name in template_manager.folders[current_folder]:
                template_manager.folders[current_folder].remove(template_name)
                
                # Save folders
                if hasattr(template_manager, 'save_folders'):
                    template_manager.save_folders()
                    
                    # Hide this card immediately for visual feedback
                    self.hide()
                    
                    # Refresh gallery if possible
                    parent = self.parent()
                    # List items may be in a different hierarchy
                    if hasattr(parent, 'parent') and hasattr(parent.parent(), 'populate_gallery'):
                        parent.parent().populate_gallery(force_refresh=True)
                    elif hasattr(parent, 'populate_gallery'):
                        parent.populate_gallery(force_refresh=True)
                    
                    # Show status message
                    if hasattr(self.app, 'show_status_message'):
                        self.app.show_status_message(f"Template '{template_name}' moved to root", "info")

    def _move_to_folder_and_hide(self, folder_name):
        """Move template to folder and hide it immediately for better visual feedback"""
        template_name = self.template_name()
        
        # Emit the signal to actually move the template
        self.moveToFolderRequested.emit(template_name, folder_name)
        
        # Hide this card immediately for visual feedback
        self.hide()
        
        # Show status message if possible
        if hasattr(self.app, 'show_status_message'):
            self.app.show_status_message(f"Template '{template_name}' moved to folder '{folder_name}'", "info")

class TemplateListItem(QFrame):
    """Template list item widget for displaying a template in list view"""
    
    clicked = pyqtSignal(object)
    doubleClicked = pyqtSignal(object)
    dragStarted = pyqtSignal(str)
    editRequested = pyqtSignal(str)  # New signal for edit action
    deleteRequested = pyqtSignal(str)  # New signal for delete action
    moveToFolderRequested = pyqtSignal(str, str)  # template_name, folder_name

    def __init__(self, parent=None, template=None, app=None):
        super().__init__(parent)
        self.template = template or {}  # Use empty dict if template is None
        self.app = app
        self.hover = False
        self.selected = False
        self.setAcceptDrops(False)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)  # Fixed height for list view items
        
        # Set alternating row color property (will be set by parent)
        self.setProperty("row_type", "even")  # Default to even
        
        # Main layout - horizontal for list view
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)
        
        # Template icon (smaller for list view)
        self.icon_label = QLabel()
        try:
            icon_path = template_icon_path(template_name=self.template_name())
            if icon_path.endswith('.svg'):
                # Handle SVG files using QPixmap and QSvgRenderer
                from PyQt5.QtSvg import QSvgRenderer
                from PyQt5.QtCore import QByteArray, QSize
                
                # Create a renderer for the SVG
                with open(icon_path, 'r') as f:
                    svg_content = f.read()
                
                renderer = QSvgRenderer(QByteArray(svg_content.encode()))
                if renderer.isValid():
                    # Create a pixmap to render to
                    pixmap = QPixmap(24, 24)
                    pixmap.fill(Qt.transparent)  # Make the background transparent
                    
                    # Paint the SVG on the pixmap
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    self.icon_label.setPixmap(pixmap)
                else:
                    # Fallback to text
                    self.icon_label.setText("📄")
                    font = QFont(SYSTEM_FONT)
                    font.setPointSize(14)
                    self.icon_label.setFont(font)
            else:
                # Handle PNG or fallback
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.icon_label.setPixmap(pixmap)
                else:
                    # If pixmap is null, use text as a fallback
                    self.icon_label.setText("📄")
                    font = QFont(SYSTEM_FONT)
                    font.setPointSize(14)
                    self.icon_label.setFont(font)
        except Exception as e:
            print(f"ERROR: Failed to load template icon: {e}")
            # Use text as a fallback
            self.icon_label.setText("📄")
            font = QFont(SYSTEM_FONT)
            font.setPointSize(14)
            self.icon_label.setFont(font)
        
        self.icon_label.setFixedSize(24, 24)
        layout.addWidget(self.icon_label)
        
        # Template name label
        self.name_label = QLabel(self.template_name())
        font = QFont(SYSTEM_FONT)
        font.setPointSize(12)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label, 1)
        
        # Template category label
        category = self.template.get("category", self.template.get("type", "Custom"))
        self.category_label = QLabel(str(category))
        font = QFont(SYSTEM_FONT)
        font.setPointSize(10)
        self.category_label.setFont(font)
        self.category_label.setFixedWidth(120)  # Fixed width for consistent layout
        layout.addWidget(self.category_label)
        
        # Initial styling
        self._update_styling()
    
    def template_name(self):
        """Get the template name, handling different formats of template data."""
        if not self.template:
            return "Unnamed Template"
            
        # Handle different ways the name might be stored
        if isinstance(self.template, dict):
            return self.template.get("name", "Unnamed Template")
        elif isinstance(self.template, str):
            return self.template
        else:
            return str(self.template)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.template)
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.template)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            mime_data = QMimeData()
            mime_data.setText(self.template_name())
            
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.setPixmap(QPixmap(self.grab()))
            drag.exec_(Qt.MoveAction)
            event.accept()
    
    def enterEvent(self, event):
        self.hover = True
        self._update_styling()
    
    def leaveEvent(self, event):
        self.hover = False
        self._update_styling()
    
    def set_selected(self, selected):
        self.selected = selected
        self._update_styling()
    
    def _update_styling(self):
        # First get the base background color based on row type
        if self.property("row_type") == "odd":
            bg_color = colors["card_bg"]  # Darker for odd rows
        else:
            bg_color = colors["bg"]  # Lighter for even rows
                
        if self.selected:
            # Selected style
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["accent"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            self.name_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent; font-weight: bold;")
            self.category_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            self.icon_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
        elif self.hover:
            # Hover style
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["hover_bg"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            self.name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            self.icon_label.setStyleSheet("background: transparent;")
        else:
            # Normal style - use alternating row colors
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            self.name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            self.icon_label.setStyleSheet("background: transparent;")

    def keyPressEvent(self, event):
        """Handle key press events for template operations"""
        # Handle both Delete and Backspace (for Mac) for template deletion when selected
        if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            self.deleteRequested.emit(self.template_name())
        super().keyPressEvent(event)
    
    def contextMenuEvent(self, event):
        """Show context menu when right-clicked"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        # Create context menu using our custom class
        context_menu = ContextMenu(self)
        
        # Add "Edit" action
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.editRequested.emit(self.template_name()))
        context_menu.addAction(edit_action)
        
        # Add "Delete" action using our helper method for red styling
        context_menu.addRedDeleteAction(
            parent=self,
            callback=lambda: self.deleteRequested.emit(self.template_name())
        )
        
        # Add separator
        context_menu.addSeparator()
        
        # Add move actions
        move_to_menu = ContextMenu(context_menu)
        move_to_menu.setTitle("Move to...")
        
        # Find current folder of this template
        current_folder = None
        template_manager = self.app.template_manager
        if hasattr(template_manager, 'folders'):
            for folder_name, templates in template_manager.folders.items():
                if self.template_name() in templates:
                    current_folder = folder_name
                    break
        
        # Add "Move to Root" option if template is in a folder
        if current_folder:
            move_to_root_action = QAction("Root (No Folder)", self)
            move_to_root_action.triggered.connect(lambda: self._move_template_out_of_folder(current_folder))
            move_to_menu.addAction(move_to_root_action)
            
            move_to_menu.addSeparator()
        
        # Add all folders except current one
        if hasattr(template_manager, 'folders'):
            folders = sorted(list(template_manager.folders.keys()))
            for folder_name in folders:
                # Skip the current folder
                if folder_name == current_folder:
                    continue
                    
                folder_action = QAction(folder_name, self)
                folder_action.triggered.connect(lambda checked=False, f=folder_name: 
                                               self._move_to_folder_and_hide(f))
                move_to_menu.addAction(folder_action)
        
        # Only add the Move To menu if it has items
        if not move_to_menu.isEmpty():
            context_menu.addMenu(move_to_menu)
        
        # Show the menu
        context_menu.exec_(event.globalPos())
    
    def _move_template_out_of_folder(self, current_folder):
        """Move template out of its current folder and hide it for immediate feedback"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        template_name = self.template_name()
        template_manager = self.app.template_manager
        
        # Remove template from the current folder
        if hasattr(template_manager, 'folders') and current_folder in template_manager.folders:
            if template_name in template_manager.folders[current_folder]:
                template_manager.folders[current_folder].remove(template_name)
                
                # Save folders
                if hasattr(template_manager, 'save_folders'):
                    template_manager.save_folders()
                    
                    # Hide this card immediately for visual feedback
                    self.hide()
                    
                    # Refresh gallery if possible
                    parent = self.parent()
                    # List items may be in a different hierarchy
                    if hasattr(parent, 'parent') and hasattr(parent.parent(), 'populate_gallery'):
                        parent.parent().populate_gallery(force_refresh=True)
                    elif hasattr(parent, 'populate_gallery'):
                        parent.populate_gallery(force_refresh=True)
                    
                    # Show status message
                    if hasattr(self.app, 'show_status_message'):
                        self.app.show_status_message(f"Template '{template_name}' moved to root", "info")

    def _move_to_folder_and_hide(self, folder_name):
        """Move template to folder and hide it immediately for better visual feedback"""
        template_name = self.template_name()
        
        # Emit the signal to actually move the template
        self.moveToFolderRequested.emit(template_name, folder_name)
        
        # Hide this card immediately for visual feedback
        self.hide()
        
        # Show status message if possible
        if hasattr(self.app, 'show_status_message'):
            self.app.show_status_message(f"Template '{template_name}' moved to folder '{folder_name}'", "info")