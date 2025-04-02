# template_card.py

from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QMenu, QAction, QMessageBox, 
    QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QSizePolicy, QApplication,
    QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QMimeData, QSize, QPoint, QRect, QByteArray, QTimer
from PyQt5.QtGui import QPixmap, QFont, QDrag, QPainter, QColor, QBrush, QPen, QIcon, QCursor
import os
from .utils import SYSTEM_FONT
from .common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED, colors
from app.ui.color_scheme_pyqt import MENU_DESTRUCTIVE_ITEM_STYLE, DELETE_TEXT_STYLE
from app.templates.components.menu_actions import ContextMenu
from app.constants import get_resource_path

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

    # Static variable to track if deletion is in progress
    _deletion_in_progress = False

    def __init__(self, parent=None, template=None, app=None):
        """Initialize the template card"""
        super().__init__(parent)
        self.template = template or {}  # Use empty dict if template is None
        self.app = app
        self.hover = False
        self.selected = False
        self.multi_selected = False
        self.clicking_multi_selected = False
        self.dragging = False
        self.setAcceptDrops(False)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(140, 140)
        
        # Check if template has structure
        self.has_structure = False
        if isinstance(self.template, dict):
            if 'structure' in self.template:
                structure = self.template['structure']
                if isinstance(structure, dict) and 'folders' in structure and structure['folders']:
                    self.has_structure = True
                elif isinstance(structure, list) and structure:
                    self.has_structure = True
        
        # Initial style - will be updated by _update_styling
        self.setStyleSheet(f"background-color: {CARD_NORMAL}; border-radius: 6px;")
        
        # Set property to track if this is a template card (for styling)
        self.setProperty("is_template_card", True)
        
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
        icon_path = get_resource_path(os.path.join(
            "ICONS", "templates", "template_structure_icon.svg")) # Corrected path
        print(f"DEBUG (Card Icon Path): {icon_path}")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path) # Use QIcon for better scaling
            # Get a pixmap from the icon at the desired size
            pixmap = icon.pixmap(64, 64)
            if pixmap.isNull():
                print(f"ERROR: Failed to load icon pixmap from: {icon_path}")
                # Optionally set a default/fallback icon here
            else:
                # No need for scaled() method now, QIcon provides the correct size
                self.icon_label.setPixmap(pixmap)
        else:
            print(f"ERROR: Icon file not found at: {icon_path}")
            # Optionally set a default/fallback icon here
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.icon_label, 1, Qt.AlignCenter)
        layout.addWidget(icon_container)
        
        # If the template has no structure, add a warning icon overlay
        if not self.has_structure:
            # Create a warning indicator in the top right corner
            self.warning_indicator = QLabel(self)
            self.warning_indicator.setFixedSize(24, 24)
            self.warning_indicator.setStyleSheet(f"""
                background-color: {colors['error']};
                color: white;
                border-radius: 12px;
                font-weight: bold;
                border: 1px solid white;
            """)
            self.warning_indicator.setText("!")
            self.warning_indicator.setAlignment(Qt.AlignCenter)
            self.warning_indicator.move(110, 10)  # Position in top right
            
            # Create a tooltip that explains the warning
            self.setToolTip("This template has no folder structure defined")
        
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
        
        # Template category label (changed from type_label)
        category_str = self.template.get("category") # Read 'category'
        # Display "No Category" if category is missing or empty
        display_category = category_str if category_str else "No Category" 
        self.category_label = QLabel(display_category, self)
        self.category_label.setAlignment(Qt.AlignCenter)
        font = QFont(SYSTEM_FONT)
        font.setPointSize(8)
        self.category_label.setFont(font)
        self.category_label.setStyleSheet(f"color: {colors['secondary_text']};")
        text_layout.addWidget(self.category_label) # Add category_label
        
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

    def template_info(self):
        """Get a string representation of the template info."""
        if isinstance(self.template, dict):
            name = self.template.get("name", "")
            
            # Use type instead of category
            type_str = self.template.get("type", "")
            
            if name and type_str:
                return f"{name} ({type_str})"
            elif name:
                return name
            else:
                return "Unnamed Template"
        elif isinstance(self.template, str):
            return self.template
        else:
            return str(self.template)

    def mousePressEvent(self, event):
        """Handle mouse press events for template selection"""
        if event.button() == Qt.LeftButton:
            # Save mouse press position for potential drag operation
            self.mouse_press_pos = event.pos()
            self.mouse_is_pressed = True
            
            # Get keyboard modifiers for multi-selection
            modifiers = QApplication.keyboardModifiers()
            is_ctrl_or_cmd = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
            is_shift = bool(modifiers & Qt.ShiftModifier)
            
            # Get gallery reference for multi-selection
            gallery = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
            
            template_name = self.template.get('name', 'Unknown')
            print(f"🔍 LISTENER: Template card clicked for template: {template_name}")
            print(f"🔍 LISTENER: Modifiers value: {int(modifiers)}, is_multi_select: {is_ctrl_or_cmd or is_shift}")
            
            # Check if this card is already multi-selected
            was_multi_selected = False
            if gallery and hasattr(gallery, 'multi_selected_templates'):
                was_multi_selected = self.template in gallery.multi_selected_templates
                
            # CRITICAL: Track if we're clicking on an already selected item in multi-selection
            # This is key for allowing drag operations on multiple selections
            self.clicking_multi_selected = was_multi_selected and len(gallery.multi_selected_templates) > 1
            if self.clicking_multi_selected:
                print(f"🔍 LISTENER: Clicking on already multi-selected item for potential drag")
            
            # Always ensure the card's state is updated for immediate visual feedback
            self.set_selected(True)
            
            if gallery:
                if is_ctrl_or_cmd:
                    # Control/Command click - toggle multi-selection
                    if hasattr(gallery, 'multi_selected_templates'):
                        was_multi_selected = self.template in gallery.multi_selected_templates
                        
                        if was_multi_selected:
                            # Remove from multi-selection
                            gallery.multi_selected_templates.remove(self.template)
                            print(f"🔍 LISTENER: Removing '{template_name}' from multi-selection")
                        else:
                            # Add to multi-selection
                            gallery.multi_selected_templates.append(self.template)
                            print(f"🔍 LISTENER: Adding '{template_name}' to multi-selection")
                    
                    # Add to primary selection WITHOUT clearing previous selections
                    if hasattr(gallery, 'selected_template'):
                        # Remember previous selection to maintain it in multi-selection
                        prev_selection = gallery.selected_template
                        
                        # Only add previous selection to multi-selection if it's valid and not already there
                        if prev_selection and prev_selection != self.template:
                            if hasattr(gallery, 'multi_selected_templates') and prev_selection not in gallery.multi_selected_templates:
                                gallery.multi_selected_templates.append(prev_selection)
                                print(f"🔍 LISTENER: Adding previous primary selection to multi-selection")
                        
                        # Set new primary selection
                        gallery.selected_template = self.template
                        print(f"🔍 LISTENER: Setting '{template_name}' as primary selection")
                        
                        # Update app-level selected template if available
                        if hasattr(gallery, 'app') and hasattr(gallery.app, 'selected_template'):
                            gallery.app.selected_template = self.template
                    
                    # Mark that we're in multi-selection mode for the update
                    if not hasattr(gallery, 'is_multi_selecting'):
                        gallery.is_multi_selecting = True
                    else:
                        gallery.is_multi_selecting = True
                        
                    # Update styling for all cards EXCEPT don't deselect anything
                    if hasattr(gallery, '_update_template_card_selection'):
                        gallery._update_template_card_selection()
                elif is_shift:
                    # Shift click - select range
                    if hasattr(gallery, 'selected_template') and gallery.selected_template:
                        # Find the index of the last selected template
                        last_selected_index = -1
                        this_index = -1
                        
                        # Traverse the template_cards in gallery to find indexes
                        if hasattr(gallery, 'template_cards'):
                            for i, card in enumerate(gallery.template_cards):
                                if hasattr(card, 'template'):
                                    if card.template == gallery.selected_template:
                                        last_selected_index = i
                                    if card.template == self.template:
                                        this_index = i
                        
                        # If we found both templates, select the range
                        if last_selected_index >= 0 and this_index >= 0:
                            start = min(last_selected_index, this_index)
                            end = max(last_selected_index, this_index)
                            
                            # Initialize multi-selection list if needed
                            if not hasattr(gallery, 'multi_selected_templates'):
                                gallery.multi_selected_templates = []
                            
                            # Clear existing multi-selection
                            gallery.multi_selected_templates.clear()
                            
                            # Add all templates in range to multi-selection
                            for i in range(start, end + 1):
                                if i < len(gallery.template_cards):
                                    card = gallery.template_cards[i]
                                    if hasattr(card, 'template'):
                                        # Skip the primary selection to avoid duplicates
                                        if card.template != gallery.selected_template:
                                            gallery.multi_selected_templates.append(card.template)
                                            
                    # Set this template as the primary selection
                    if hasattr(gallery, 'selected_template'):
                        gallery.selected_template = self.template
                        
                        # Update app-level selected template if available
                        if hasattr(gallery, 'app') and hasattr(gallery.app, 'selected_template'):
                            gallery.app.selected_template = self.template
                    
                    # Mark that we're in multi-selection mode for the update
                    if not hasattr(gallery, 'is_multi_selecting'):
                        gallery.is_multi_selecting = True
                    else:
                        gallery.is_multi_selecting = True
                        
                    # Update all cards' visual state
                    if hasattr(gallery, '_update_template_card_selection'):
                        gallery._update_template_card_selection()
                else:
                    # Standard click - DON'T clear multi-selection yet in case this is start of drag
                    # We'll handle clearing multi-selection in mouseReleaseEvent if this wasn't a drag
                    
                    # If clicking on a multi-selected item, don't clear yet - allow for drag operations
                    if not self.clicking_multi_selected:
                        # Only clear if not clicking on a multi-selected item
                        if hasattr(gallery, 'is_multi_selecting'):
                            gallery.is_multi_selecting = False
                            
                        # Set primary selection without clearing multi-selection yet
                        if hasattr(gallery, 'selected_template'):
                            gallery.selected_template = self.template
                            
                            # Update app-level selected template if available
                            if hasattr(gallery, 'app') and hasattr(gallery.app, 'selected_template'):
                                gallery.app.selected_template = self.template
                                print(f"🔍 LISTENER: Updated app-level selected template to '{template_name}'")
                        
                        # Just visually highlight this card but don't clear others yet
                        self.set_selected(True)
                
                # Emit clicked signal with template data
                self.clicked.emit(self.template)
            else:
                # No gallery found, just emit the clicked signal
                print(f"🔍 LISTENER: No gallery parent found, emitting clicked signal directly")
                self.clicked.emit(self.template)
                
        # Let parent handle other button events
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release after click or drag"""
        if event.button() == Qt.LeftButton:
            # Calculate the drag distance
            drag_occurred = False
            if self.mouse_press_pos:
                drag_distance = (event.pos() - self.mouse_press_pos).manhattanLength()
                drag_occurred = drag_distance >= 5  # Common threshold for drag detection
            
            if not drag_occurred and not self.clicking_multi_selected:
                # Only clear other selections if this was a genuine click (not drag)
                # and not clicking on an already multi-selected item
                
                # Get gallery reference
                gallery = None
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'multi_selected_templates'):
                        gallery = parent
                        break
                    parent = parent.parent()
                
                # Get keyboard modifiers - maintain multi-selection if modifier is still pressed
                modifiers = QApplication.keyboardModifiers()
                is_ctrl_or_cmd = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
                is_shift = bool(modifiers & Qt.ShiftModifier)
                
                # Only clear multi-selection if no modifiers are pressed
                if not is_ctrl_or_cmd and not is_shift and gallery:
                    if hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
                        # Now clear multi-selection since this is a regular click
                        gallery.multi_selected_templates.clear()
                        print(f"🔍 LISTENER: Cleared multi-selection on mouse release")
                    
                    # Update all card styling
                    if hasattr(gallery, '_update_template_card_selection'):
                        gallery._update_template_card_selection()
            
            # Reset state variables
            self.mouse_press_pos = None
            self.clicking_multi_selected = False
        
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click to open template editor"""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.template_name())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            # Get gallery reference to check multi-selection
            gallery = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
            
            # Calculate drag distance to ensure this is a drag, not a click
            if hasattr(self, 'mouse_press_pos'):
                drag_distance = (event.pos() - self.mouse_press_pos).manhattanLength()
                if drag_distance < 5:  # Common threshold for drag detection
                    return  # Not a drag yet
            
            # Prepare mime data for the drag operation
            mime_data = QMimeData()
            
            # Check if we're part of a multi-selection
            is_multi_drag = False
            template_names = []
            
            if gallery and hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
                # Check if this template is either the primary selection or in multi-selection
                is_primary = hasattr(gallery, 'selected_template') and gallery.selected_template == self.template
                is_in_multi = self.template in gallery.multi_selected_templates
                
                if is_primary or is_in_multi or getattr(self, 'clicking_multi_selected', False):
                    # This is a multi-selection drag - include all selected templates
                    is_multi_drag = True
                    
                    # Always include primary selection first if it exists
                    if hasattr(gallery, 'selected_template') and gallery.selected_template:
                        primary_name = gallery.selected_template.get('name', 'Unknown')
                        if primary_name not in template_names:
                            template_names.append(primary_name)
                    
                    # Then add all multi-selected templates
                    for template in gallery.multi_selected_templates:
                        name = template.get('name', 'Unknown')
                        if name not in template_names:
                            template_names.append(name)
                    
                    print(f"🔍 LISTENER: Multi-selection drag with {len(template_names)} templates: {template_names}")
            
            # If not a multi-selection drag, just use this template
            if not is_multi_drag:
                template_names = [self.template_name()]
                print(f"🔍 LISTENER: Single template drag: {template_names[0]}")
            
            # Store data in mime data
            mime_data.setText("\n".join(template_names))
            # Add a custom MIME type to identify multi-template drag
            if is_multi_drag:
                mime_data.setData("application/x-template-multi-drag", QByteArray(str(len(template_names)).encode()))
            
            # Create drag object
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Set appropriate pixmap based on selection count
            if len(template_names) > 1:
                # Create a special pixmap for multi-template drag
                pixmap = QPixmap(self.size())
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setOpacity(0.8)
                painter.drawPixmap(0, 0, self.grab())
                painter.setOpacity(1.0)
                painter.setPen(QPen(QColor(colors["highlight_bg"]), 2))
                painter.setBrush(QBrush(QColor(colors["highlight_bg"]).darker(150)))
                painter.drawRect(QRect(10, 10, 30, 20))
                painter.setPen(QPen(Qt.white))
                painter.setFont(QFont(SYSTEM_FONT, 10, QFont.Bold))
                painter.drawText(QRect(10, 10, 30, 20), Qt.AlignCenter, str(len(template_names)))
                painter.end()
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
            else:
                # Single template drag
                drag.setPixmap(self.grab())
            
            # Execute drag
            drag.exec_(Qt.MoveAction)
            event.accept()

    def enterEvent(self, event):
        self.hover = True
        self._update_styling()

    def leaveEvent(self, event):
        self.hover = False
        self._update_styling()

    def set_selected(self, selected):
        """Set the selection state of the card with immediate visual feedback"""
        # Track previous state for comparison
        prev_state = self.selected
        self.selected = selected
        
        # Set property for stylesheet access
        self.setProperty("is_selected", selected)
        
        # Always explicitly apply styling based on selection state
        if selected:
            # Selected styling - direct application for immediate feedback
            style = f"""
                QFrame {{
                    background-color: {colors['highlight_bg']};
                    border: none;
                    border-radius: 6px;
                }}
            """
            self.setStyleSheet(style)
            
            # Text colors
            self.name_label.setStyleSheet("color: white; font-weight: bold; background-color: transparent;")
            self.category_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: transparent;")
            self.icon_label.setStyleSheet("color: white; background-color: transparent;")
            
            print(f"⭐ Applied SELECTED style to {self.template_name()}")
        else:
            # Update based on hover or default state
            self._update_styling()
        
        # Force style application immediately
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        
        # Debug output to track selection changes
        if prev_state != selected:
            print(f"⭐ TemplateCard selection changed: {prev_state} -> {selected} for {self.template_name()}")
        
        return self.selected

    def _update_styling(self):
        """Update card styling based on selection and hover states"""
        # Initialize multi_selected attribute if it doesn't exist
        if not hasattr(self, 'multi_selected'):
            self.multi_selected = False
            
        # Debug output
        print(f"⭐ TemplateCard._update_styling() for {self.template_name()}, selected={self.selected}, hover={self.hover}")
        
        # Store current states as properties on the widget
        self.setProperty("is_selected", self.selected)
        self.setProperty("is_multi_selected", getattr(self, 'multi_selected', False))
        
        # Temporary highlight style (when template renamed)
        if hasattr(self, 'highlight_animation_active') and self.highlight_animation_active:
            # Highlight styling (bright blue with border)
            print(f"⭐ Applying HIGHLIGHT animation style to {self.template_name()}")
            
            # Card background
            self.setStyleSheet("""
                QFrame {
                    background-color: #3C6EA5;
                    border: 2px solid #4A86E8;
                    border-radius: 6px;
                }
            """)
            
            # Text colors
            self.name_label.setStyleSheet("color: white; font-weight: bold; background-color: transparent;")
            self.category_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: transparent;")
            self.icon_label.setStyleSheet("color: white; background-color: transparent;")
        
        # Priority: multi-selected > selected > hover > normal
        elif getattr(self, 'multi_selected', False):
            # Multi-selected styling
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['highlight_darker']};
                    border: none;
                    border-radius: 6px;
                }}
            """)
            
            # Text colors
            self.name_label.setStyleSheet("color: white; font-weight: bold; background-color: transparent;")
            self.category_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: transparent;")
            self.icon_label.setStyleSheet("color: white; background-color: transparent;")
            
        elif self.selected:
            # Simple, high-contrast selection style for maximum visibility
            print(f"⭐ Applying SELECTED style to {self.template_name()}")
            
            # Card background
            self.setStyleSheet("""
                QFrame {
                    background-color: #2C4F76;
                    border: none;
                    border-radius: 6px;
                }
            """)
            
            # Text colors
            self.name_label.setStyleSheet("color: white; font-weight: bold; background-color: transparent;")
            self.category_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: transparent;")
            self.icon_label.setStyleSheet("color: white; background-color: transparent;")
            
            # Debug - print style that was applied
            print(f"⭐ Template card style: {self.styleSheet()}")
        
        elif self.hover:
            # Hover styling
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['hover_bg']};
                    border: none;
                    border-radius: 6px;
                }}
            """)
            
            # Text colors for hover state
            self.name_label.setStyleSheet("color: white; background-color: transparent;")
            self.category_label.setStyleSheet("color: #AAAAAA; background-color: transparent;")
            self.icon_label.setStyleSheet("color: white; background-color: transparent;")
        
        else:
            # Default unselected styling
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_NORMAL};
                    border: none;
                    border-radius: 6px;
                }}
            """)
            
            # Default text colors
            self.name_label.setStyleSheet("color: white; background-color: transparent;")
            self.category_label.setStyleSheet("color: #AAAAAA; background-color: transparent;")
            self.icon_label.setStyleSheet("color: white; background-color: transparent;")
        
        # Force immediate update
        self.update()
        
    def apply_rename_highlight(self):
        """Apply a highlight animation when template is renamed
        
        This method is called after a template has been renamed to provide
        visual feedback to the user that the rename was successful
        """
        print(f"🔸 TEMPLATE CARD: Applying rename highlight to {self.template_name()}")
        
        # Set highlight animation active flag
        self.highlight_animation_active = True
        
        # Update styling for highlight
        self._update_styling()
        
        # Set a timer to remove the highlight after 2 seconds
        if hasattr(self, 'highlight_timer'):
            # Cancel any existing timer
            if self.highlight_timer.isActive():
                self.highlight_timer.stop()
        else:
            # Create a new timer if it doesn't exist
            self.highlight_timer = QTimer()
            self.highlight_timer.setSingleShot(True)
            self.highlight_timer.timeout.connect(self._remove_highlight)
        
        # Start timer for 2 seconds
        self.highlight_timer.start(2000)  # 2 seconds
        print(f"🔸 TEMPLATE CARD: Started highlight timer for {self.template_name()} (2 seconds)")

    def _remove_highlight(self):
        """Remove the highlight effect after timer expires"""
        print(f"🔸 TEMPLATE CARD: Removing highlight from {self.template_name()}")
        self.highlight_animation_active = False
        self._update_styling()
        print(f"🔸 TEMPLATE CARD: Reset styling for {self.template_name()}")

    def keyPressEvent(self, event):
        """Handle key press events for template operations"""
        # Handle both Delete and Backspace (for Mac) for template deletion when selected
        if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            # Find the parent gallery for multi-selection handling
            gallery = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
            
            # Always use _delete_multi_selected which handles both single and multi-selections properly
            if gallery:
                self._delete_multi_selected(gallery)
            
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
        
        # Find the parent gallery for multi-selection handling
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'multi_selected_templates'):
                gallery = parent
                break
            parent = parent.parent()
        
        # Check if we're in a multi-selection state
        has_multi = (gallery and hasattr(gallery, 'multi_selected_templates') and 
                    gallery.multi_selected_templates and 
                    len(gallery.multi_selected_templates) > 0)
                    
        # Add "Delete" action with appropriate callback based on selection state
        if has_multi:
            delete_text = "Delete Selected Templates"
            delete_callback = lambda: self._delete_multi_selected(gallery)
        else:
            delete_text = "Delete"
            delete_callback = lambda: self.deleteRequested.emit(self.template_name())
            
        context_menu.addRedDeleteAction(
            parent=self,
            callback=delete_callback,
            text=delete_text
        )
        
        # Add separator
        context_menu.addSeparator()
        
        # Add export template option
        export_action = QAction("Export Template...", self)
        export_action.triggered.connect(lambda: self._export_template())
        context_menu.addAction(export_action)
        
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
            
        # Get gallery reference to check multi-selection
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'multi_selected_templates'):
                gallery = parent
                break
            parent = parent.parent()
            
        # Check if we should be handling multiple templates
        is_multi_selection = False
        templates_to_move = []
        
        # Check if we're part of a multi-selection
        if gallery and hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
            # Check if this template is either the primary selection or in multi-selection
            is_primary = hasattr(gallery, 'selected_template') and gallery.selected_template == self.template
            is_in_multi = self.template in gallery.multi_selected_templates
            
            if is_primary or is_in_multi or getattr(self, 'clicking_multi_selected', False):
                # This is a multi-selection operation - include all selected templates
                is_multi_selection = True
                
                # Always include primary selection first if it exists
                if hasattr(gallery, 'selected_template') and gallery.selected_template:
                    primary_template = gallery.selected_template
                    templates_to_move.append(primary_template)
                    print(f"🔍 LISTENER: Adding primary selection to templates to move out of folder")
                
                # Then add all multi-selected templates (avoiding duplicates)
                for template in gallery.multi_selected_templates:
                    if template not in templates_to_move:
                        templates_to_move.append(template)
                        print(f"🔍 LISTENER: Adding multi-selected template to templates to move out of folder")
        
        # If not a multi-selection, just use this template
        if not is_multi_selection:
            templates_to_move = [self.template]
            
        # Count for message
        count = len(templates_to_move)
        print(f"🔍 LISTENER: Moving {count} templates out of folder '{current_folder}'")
        
        template_manager = self.app.template_manager
        
        # Process each template
        template_names = []
        for template in templates_to_move:
            if isinstance(template, dict):
                template_name = template.get('name', 'Unknown')
            else:
                template_name = str(template)
                
            template_names.append(template_name)
            
            # Remove template from the current folder
            if hasattr(template_manager, 'folders') and current_folder in template_manager.folders:
                if template_name in template_manager.folders[current_folder]:
                    template_manager.folders[current_folder].remove(template_name)
        
        # Save changes to folders
        if hasattr(template_manager, 'save_folders'):
            template_manager.save_folders()
        
        # Show status message - BEFORE refreshing gallery to avoid visual jumping
        if hasattr(self.app, 'show_status_message'):
            if count > 1:
                self.app.show_status_message(f"Moved {count} templates to root", "info")
            else:
                self.app.show_status_message(f"Template '{template_names[0]}' moved to root", "info")
        
        # IMPORTANT: Refresh gallery after ALL templates are moved
        # Wait to refresh gallery until the end to ensure all templates are accounted for
        QTimer.singleShot(50, lambda: self._refresh_gallery(gallery))

    def _refresh_gallery(self, gallery=None):
        """Helper method to refresh gallery properly after all operations"""
        # If gallery was provided, use it directly
        if gallery and hasattr(gallery, 'populate_gallery'):
            print(f"🔍 LISTENER: Refreshing gallery using provided gallery reference")
            gallery.populate_gallery(force_refresh=True)
            return
            
        # Otherwise find parent gallery through hierarchy
        parent = self.parent()
        
        # First try list items parent chain
        if hasattr(parent, 'parent') and hasattr(parent.parent(), 'populate_gallery'):
            print(f"🔍 LISTENER: Refreshing gallery through list item parent chain")
            parent.parent().populate_gallery(force_refresh=True)
        # Then try direct parent
        elif hasattr(parent, 'populate_gallery'):
            print(f"🔍 LISTENER: Refreshing gallery through direct parent")
            parent.populate_gallery(force_refresh=True)

    def _move_to_folder_and_hide(self, folder_name):
        """Move template to folder and hide for immediate feedback"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        # Get gallery reference to check multi-selection
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'multi_selected_templates'):
                gallery = parent
                break
            parent = parent.parent()
            
        # Check if we should be handling multiple templates
        is_multi_selection = False
        templates_to_move = []
        
        # Check if we're part of a multi-selection
        if gallery and hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
            # Check if this template is either the primary selection or in multi-selection
            is_primary = hasattr(gallery, 'selected_template') and gallery.selected_template == self.template
            is_in_multi = self.template in gallery.multi_selected_templates
            
            if is_primary or is_in_multi or getattr(self, 'clicking_multi_selected', False):
                # This is a multi-selection operation - include all selected templates
                is_multi_selection = True
                
                # Always include primary selection first if it exists
                if hasattr(gallery, 'selected_template') and gallery.selected_template:
                    primary_template = gallery.selected_template
                    templates_to_move.append(primary_template)
                    print(f"🔍 LISTENER: Adding primary selection to templates to move to folder '{folder_name}'")
                
                # Then add all multi-selected templates (avoiding duplicates)
                for template in gallery.multi_selected_templates:
                    if template not in templates_to_move:
                        templates_to_move.append(template)
                        print(f"🔍 LISTENER: Adding multi-selected template to templates to move to folder '{folder_name}'")
        
        # If not a multi-selection, just use this template
        if not is_multi_selection:
            templates_to_move = [self.template]
            
        # Count for message
        count = len(templates_to_move)
        print(f"🔍 LISTENER: Moving {count} templates to folder '{folder_name}'")
        
        template_manager = self.app.template_manager
        
        # Process each template
        template_names = []
        for template in templates_to_move:
            if isinstance(template, dict):
                template_name = template.get('name', 'Unknown')
            else:
                template_name = str(template)
                
            template_names.append(template_name)
            
            # Move template to folder
            template_manager.move_template_to_folder(template_name, folder_name)
        
        # If we're in list view, we don't hide immediately since the gallery refresh will handle visibility
        # In grid view (TemplateCard), hide this card for immediate feedback
            self.hide()
        
        # Show status message - BEFORE refreshing gallery to avoid visual jumping
        if hasattr(self.app, 'show_status_message'):
            if count > 1:
                self.app.show_status_message(f"Moved {count} templates to folder '{folder_name}'", "info")
            else:
                self.app.show_status_message(f"Template '{template_names[0]}' moved to folder '{folder_name}'", "info")
        
        # IMPORTANT: Refresh gallery after ALL templates are moved
        # Wait to refresh gallery until the end to ensure all templates are accounted for
        QTimer.singleShot(50, lambda: self._refresh_gallery(gallery))

    def _delete_multi_selected(self, gallery):
        """Delete all selected templates"""
        if not gallery:
            return
            
        # Check if deletion is already in progress
        if TemplateCard._deletion_in_progress:
            print(f"🔍 LISTENER: Deletion already in progress, ignoring duplicate request")
            return
            
        # Set deletion in progress flag
        TemplateCard._deletion_in_progress = True
            
        try:
            # Print current selection states
            if hasattr(gallery, 'selected_template') and gallery.selected_template:
                print(f"🔍 LISTENER: Current primary selection: {gallery.selected_template.get('name', 'Unknown')}")
            else:
                print(f"🔍 LISTENER: No primary selection")
                
            if hasattr(gallery, 'multi_selected_templates'):
                print(f"🔍 LISTENER: Current multi-selection: {[t.get('name', 'Unknown') for t in gallery.multi_selected_templates]}")
            
            # First, detect what we're deleting
            has_primary = hasattr(gallery, 'selected_template') and gallery.selected_template is not None
            has_multi = (hasattr(gallery, 'multi_selected_templates') and 
                        gallery.multi_selected_templates and 
                        len(gallery.multi_selected_templates) > 0)
            
            # If nothing to delete, exit
            if not has_primary and not has_multi:
                print(f"🔍 LISTENER: No templates selected for deletion")
                return
            
            # Create a fresh set of templates to delete (using set for deduplication)
            templates_to_delete_set = set()
            templates_to_delete = []
            
            # ALWAYS include the primary selected template FIRST if it exists
            if has_primary:
                primary_name = gallery.selected_template.get('name', 'Unknown')
                templates_to_delete.append(gallery.selected_template)
                templates_to_delete_set.add(id(gallery.selected_template))  # Add object id to set for tracking
                print(f"🔍 LISTENER: Including primary selected template in delete operation: {primary_name}")
            
            # Then add the multi-selected templates
            if has_multi:
                for template in gallery.multi_selected_templates:
                    template_id = id(template)
                    if template_id not in templates_to_delete_set:
                        templates_to_delete.append(template)
                        templates_to_delete_set.add(template_id)
                        print(f"🔍 LISTENER: Adding multi-selected template to delete operation: {template.get('name', 'Unknown')}")
            
            # Verify total count matches expectations
            expected_count = (1 if has_primary else 0) + (len(gallery.multi_selected_templates) if has_multi else 0)
            actual_count = len(templates_to_delete)
            print(f"🔍 LISTENER: Expected {expected_count} templates, found {actual_count} templates after deduplication")
            
            # If no templates to delete, exit
            if not templates_to_delete:
                print(f"🔍 LISTENER: No templates to delete after processing")
                return
            
            # Get template names for display and deletion
            template_names = []
            for template in templates_to_delete:
                if isinstance(template, dict) and 'name' in template:
                    name = template['name']
                elif hasattr(template, 'get'):
                    name = template.get('name', 'Unknown')
                elif isinstance(template, str):
                    name = template
                else:
                    name = str(template)
                    
                if name and name not in template_names:
                    template_names.append(name)
                    print(f"🔍 LISTENER: Template to delete: '{name}'")
            
            # If no valid template names, exit
            if not template_names:
                print(f"🔍 LISTENER: No valid template names found for deletion")
                return
                
            print(f"🔍 LISTENER: Final delete list ({len(template_names)} templates): {template_names}")
            
            # Create confirmation message
            if len(template_names) == 1:
                message = f"Are you sure you want to delete template '{template_names[0]}'?"
            else:
                message = f"Are you sure you want to delete these {len(template_names)} templates?"
            
            # Single confirmation for all templates
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                message,
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Delete all templates in one operation
                if hasattr(self.app, 'template_manager'):
                    for name in template_names:
                        print(f"🔍 LISTENER: Deleting template '{name}'")
                        self.app.template_manager.delete_template(name)
                
                # Show success message
                if hasattr(self.app, 'show_status_message'):
                    if len(template_names) == 1:
                        self.app.show_status_message(f"Deleted template '{template_names[0]}'", "success")
                    else:
                        self.app.show_status_message(f"Deleted {len(template_names)} templates", "success")
                
                # Refresh gallery to update the view
                self._refresh_gallery(gallery)
        finally:
            # Reset deletion in progress flag
            TemplateCard._deletion_in_progress = False

    def set_multi_selected(self, multi_selected):
        """Set the multi-selection state of the card"""
        self.multi_selected = multi_selected
        print(f"🔍 LISTENER: Setting multi-selection state of '{self.template_name()}' to {multi_selected}")
        
        # Update styling based on multi-selection state
        self._update_styling()
        
        # Force immediate update
        self.update()
        
        # Apply direct styling for multi-selection state
        if multi_selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['highlight_darker']};
                    border: none;
                    border-radius: 6px;
                }}
            """)
            print(f"🔍 LISTENER: Applied multi-selected style to '{self.template_name()}'")
        
        return self.multi_selected

    def _export_template(self):
        """Export the template to a package file"""
        template_name = self.template_name()
        if not template_name or not self.app:
            return
            
        # Use the export_template function from import_export_manager
        from app.core.import_export_manager import export_template
        
        # Show dialog to ask if files should be included
        from PyQt5.QtWidgets import QMessageBox
        
        include_files = QMessageBox.question(
            self,
            "Export Template",
            f"Would you like to include files with this template?\n\n"
            f"Including files will allow others to import the template with all its attached assets.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        ) == QMessageBox.Yes
        
        # Export the template
        export_template(self.app, template_name, include_files)

# Utility function for QIcon cache (Optional but good practice)
icon_cache = {}