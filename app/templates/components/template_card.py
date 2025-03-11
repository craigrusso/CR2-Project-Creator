# template_card.py

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QMimeData
from PyQt5.QtGui import QPixmap, QFont, QDrag
import os
from .utils import SYSTEM_FONT
from .common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED, colors

def template_icon_path(template_name=None):
    """Return the path to the template icon."""
    # Default icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                           "assets", "icons", "template_icon.png")
    
    # Check if template-specific icon exists
    if template_name:
        custom_icon = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 "assets", "icons", "templates", f"{template_name}.png")
        if os.path.exists(custom_icon):
            icon_path = custom_icon
    
    return icon_path

class TemplateCard(QFrame):
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)
    dragStarted = pyqtSignal(str)

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
        
        # Template icon
        self.icon_label = QLabel(self)
        try:
            icon_path = template_icon_path(template_name=self.template_name())
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
        layout.addWidget(self.icon_label, 1, Qt.AlignCenter)
        
        # Template name label
        self.name_label = QLabel(self.template_name(), self)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        font = QFont(SYSTEM_FONT)
        font.setPointSize(10)
        self.name_label.setFont(font)
        self.name_label.setStyleSheet(f"color: {colors['text']};")
        layout.addWidget(self.name_label)
        
        # Template category label
        category = self.template.get("category", self.template.get("type", "Custom"))
        self.category_label = QLabel(str(category), self)
        self.category_label.setAlignment(Qt.AlignCenter)
        font = QFont(SYSTEM_FONT)
        font.setPointSize(8)
        self.category_label.setFont(font)
        self.category_label.setStyleSheet(f"color: {colors['secondary_text']};")
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
            self.clicked.emit(self.template_name())

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
            bg_color = CARD_SELECTED
        elif self.hover:
            bg_color = CARD_HOVER
        else:
            bg_color = CARD_NORMAL

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 6px;
            }}
            QLabel {{
                color: white;
            }}
        """)

class TemplateListItem(QFrame):
    """Template list item widget for displaying a template in list view"""
    
    clicked = pyqtSignal(object)
    doubleClicked = pyqtSignal(object)
    dragStarted = pyqtSignal(str)
    
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