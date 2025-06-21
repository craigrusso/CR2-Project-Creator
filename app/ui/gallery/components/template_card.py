# template_card.py

from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout,QWidget, QWidgetAction, QMenu, QMessageBox, 
    QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QSizePolicy, QApplication,
    QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QMimeData, QSize, QPoint, QRect, QByteArray, QTimer
from PyQt6.QtGui import QPixmap, QFont, QDrag, QPainter, QColor, QBrush, QPen, QIcon, QCursor, QPalette, QAction
# Add SVG module import for better SVG support
from PyQt6.QtSvg import QSvgRenderer
import os
from app.templates.components.utils import SYSTEM_FONT
from app.templates.components.common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED
from app.ui.color_scheme_pyqt import colors
from app.templates.components.menu_actions import ContextMenu
from app.constants import get_resource_path
from PyQt6.QtWidgets import QApplication, QStyle
from app.templates.mime_types import TEMPLATE_NAMES_MIME_TYPE, TEMPLATE_MULTI_DRAG_MIME_TYPE
from app.templates.drag_helpers import setup_drag_mime_data, create_drag_pixmap

def template_icon_path(template_name=None):
    """Return the path to the template icon."""
    # Use our new SVG icon as the default
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), # MODIFIED
                           "assets", "icons", "template_structure_icon.svg")
    
    # Check if template-specific icon exists
    if template_name:
        # First try SVG
        custom_icon_svg = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), # MODIFIED
                                 "assets", "icons", "templates", f"{template_name}.svg")
        if os.path.exists(custom_icon_svg):
            icon_path = custom_icon_svg
        else:
            # Then try PNG
            custom_icon_png = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), # MODIFIED
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
    duplicate_requested = pyqtSignal(str)  # New signal for duplicate action

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
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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
        
        # Icon container (allows for proper alignment)
        self.icon_container = QWidget()
        self.icon_container.setFixedHeight(70)  # Gives enough space for the icon

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Try to load the icon
        icon_size = 64 # Define icon size
        pixmap = None

        # --- IMPROVED ICON LOADING WITH SVG SUPPORT ---
        icon_filename = "template_structure_icon.svg"
        
        # Try different paths to locate the icon
        # 1. First try with the original path
        icon_path = get_resource_path(os.path.join(
            "app", "assets", "icons", "templates", icon_filename))
        print(f"DEBUG (Card Icon Path 1): {icon_path}")
        
        # 2. Try with a direct absolute path
        direct_icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "assets", "icons", "templates", icon_filename)
        print(f"DEBUG (Card Icon Path 2): {direct_icon_path}")
        
        # 3. Try to find the project root and construct path
        current_dir = os.path.dirname(__file__)
        project_root = current_dir
        for _ in range(10):  # Limit directory traversal to avoid infinite loop
            if os.path.exists(os.path.join(project_root, "app")) and os.path.isdir(os.path.join(project_root, "app")):
                break
            parent = os.path.dirname(project_root)
            if parent == project_root:  # Reached filesystem root
                break
            project_root = parent
            
        alt_icon_path = os.path.join(project_root, "app", "assets", "icons", "templates", icon_filename)
        print(f"DEBUG (Card Icon Path 3): {alt_icon_path}")
        print(f"DEBUG (Path exists 1): {os.path.exists(icon_path)}")
        print(f"DEBUG (Path exists 2): {os.path.exists(direct_icon_path)}")
        print(f"DEBUG (Path exists 3): {os.path.exists(alt_icon_path)}")
        
        # Use the first path that exists
        if os.path.exists(icon_path):
            print(f"DEBUG: Using icon path 1")
        elif os.path.exists(direct_icon_path):
            icon_path = direct_icon_path
            print(f"DEBUG: Using icon path 2")
        elif os.path.exists(alt_icon_path):
            icon_path = alt_icon_path
            print(f"DEBUG: Using icon path 3")
        
        if os.path.exists(icon_path):
            # Method 1: Try with QIcon (standard method)
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(QSize(icon_size, icon_size))
            
            # Check if we got a valid pixmap
            if pixmap.isNull():
                print(f"Method 1 (QIcon) failed for: {icon_path}, trying Method 2 (QSvgRenderer)")
                
                # Method 2: Try with QSvgRenderer as fallback
                try:
                    renderer = QSvgRenderer(icon_path)
                    if renderer.isValid():
                        print(f"Successfully loaded SVG with QSvgRenderer: {icon_path}")
                        pixmap = QPixmap(icon_size, icon_size)
                        pixmap.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                    else:
                        print(f"ERROR: QSvgRenderer could not load: {icon_path}")
                except Exception as e:
                    print(f"ERROR: SVG Renderer exception: {str(e)}")
            else:
                print(f"Successfully loaded icon with QIcon: {icon_path}")
        else:
            print(f"ERROR (Card): No icon file found at any path!")
            print(f"Current working directory: {os.getcwd()}")
            
            # List the app/assets/icons/templates directory to see what's there
            try:
                templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                          "assets", "icons", "templates")
                if os.path.exists(templates_dir):
                    print(f"Contents of templates directory ({templates_dir}):")
                    for file in os.listdir(templates_dir):
                        print(f"  - {file}")
                else:
                    print(f"Templates directory not found: {templates_dir}")
                    
                # Try to list app/assets/icons directory
                icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                       "assets", "icons")
                if os.path.exists(icons_dir):
                    print(f"Contents of icons directory ({icons_dir}):")
                    for file in os.listdir(icons_dir):
                        print(f"  - {file}")
                else:
                    print(f"Icons directory not found: {icons_dir}")
            except Exception as e:
                print(f"Error listing directory contents: {str(e)}")
        # --- END IMPROVED ICON LOADING ---
        
        # Set the pixmap if successfully created
        if pixmap and not pixmap.isNull():
            self.icon_label.setPixmap(pixmap)
        else:
            # Create a fallback pixmap with a text label
            fallback_pixmap = QPixmap(icon_size, icon_size)
            fallback_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(fallback_pixmap)
            painter.setPen(QColor(colors['text']))
            painter.setBrush(QColor(colors['secondary_background']))
            painter.drawRect(1, 1, icon_size-2, icon_size-2)
            painter.drawText(QRect(0, 0, icon_size, icon_size), Qt.AlignmentFlag.AlignCenter, "T")
            painter.end()
            
            self.icon_label.setPixmap(fallback_pixmap)
            print("Using fallback text icon")
            
        self.icon_layout = QVBoxLayout(self.icon_container)
        self.icon_layout.setContentsMargins(0, 0, 0, 0)
        self.icon_layout.addWidget(self.icon_label, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_container)
        
        # If the template has no structure, add a warning icon overlay
        if not self.has_structure:
            # Create a warning indicator in the top right corner
            self.warning_indicator = QLabel(self)
            self.warning_indicator.setFixedSize(24, 24)
            self.warning_indicator.setStyleSheet(f"""
                color: {colors['error']};
                background-color: transparent;
                font-weight: bold;
                font-size: 16px;
            """)
            self.warning_indicator.setText("⚠")
            self.warning_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(30)  # Limit height of name label
        font = QFont(SYSTEM_FONT)
        font.setPointSize(10)
        self.name_label.setFont(font)
        self.name_label.setStyleSheet(f"color: {colors['text']}; font-size: 10pt;")
        text_layout.addWidget(self.name_label)
        
        # Template category label (changed from type_label)
        category_str = self.template.get("category") # Read 'category'
        # Display "No Category" if category is missing or empty
        display_category = category_str if category_str else "No Category" 
        self.category_label = QLabel(display_category, self)
        self.category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        if event.button() == Qt.MouseButton.LeftButton:
            # Save mouse press position for potential drag operation
            self.mouse_press_pos = event.pos()
            self.mouse_is_pressed = True
            
            # Get keyboard modifiers for multi-selection
            modifiers = QApplication.keyboardModifiers()
            is_ctrl_or_cmd = bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier))
            is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
            is_modifier_click = is_ctrl_or_cmd or is_shift
            
            # Store initial state for reference in mouseReleaseEvent
            self.initial_selection_state = {
                'selected': self.selected,
                'multi_selected': getattr(self, 'multi_selected', False),
                'is_modifier_click': is_modifier_click,
                'is_ctrl_or_cmd': is_ctrl_or_cmd,
                'is_shift': is_shift
            }
            
            print(f"[DEBUG-SELECTION] MousePressEvent on '{self.template_name()}'")
            print(f"[DEBUG-SELECTION] Modifiers: CTRL/CMD={is_ctrl_or_cmd}, SHIFT={is_shift}")
            print(f"[DEBUG-SELECTION] Initial state: selected={self.selected}, multi_selected={getattr(self, 'multi_selected', False)}")
            
            # Get gallery reference
            gallery = None
            p = self.parent()
            while p is not None:
                if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager'):
                    gallery = p
                    break
                p = p.parent()
            
            if gallery:
                # Check if this item is already multi-selected
                is_already_multi_selected = False
                multi_selection_size = 0
                
                if hasattr(gallery, 'selection_manager'):
                    # Check if this template is part of a multi-selection
                    is_already_multi_selected = gallery.selection_manager.is_multi_selected(self.template)
                    # Get number of selected items
                    multi_selection_size = len(gallery.selection_manager.multi_selected_templates)
                
                # If modifiers are used, handle multi-selection as before
                if is_modifier_click:
                    # For Ctrl/Cmd+click, set the visual selection immediately
                    # but don't trigger the selection event yet (wait for mouseReleaseEvent)
                    if is_ctrl_or_cmd:
                        if not self.selected: 
                            self.set_selected(True)
                            self.multi_selected = True
                            setattr(self, 'multi_selected', True)
                            print("🔍 LISTENER: Setting multi-selection state of '{}' to True".format(self.template_name()))
                            print(f"[DEBUG-SELECTION] Ctrl+click on unselected item - adding visual selection")
                    elif is_shift:
                        # For shift+click, show visual feedback immediately
                        if not self.selected:
                            self.set_selected(True)
                            self.multi_selected = True
                            setattr(self, 'multi_selected', True)
                            print("🔍 LISTENER: Setting multi-selection state of '{}' to True".format(self.template_name()))
                            print(f"[DEBUG-SELECTION] Shift+click - adding visual selection range")
                # KEY FIX: If clicking on an already multi-selected item without modifier keys,
                # and there are multiple items selected, keep the multi-selection.
                # This allows dragging or context menu of already selected items.
                elif is_already_multi_selected and multi_selection_size > 1:
                    # Just set this as primary without clearing multi-selection
                    self.set_selected(True)
                    self.clicking_multi_selected = True
                    print(f"[DEBUG-SELECTION] Clicked on already multi-selected item - preserving multi-selection")
                    
                    # Update the primary selection without clearing multi
                    if hasattr(gallery, 'selection_manager'):
                        gallery.selection_manager.set_primary_selection(self.template, clear_multi=False)
                else:
                    # Normal click on non-selected item or single-selected item
                    # Apply visual feedback immediately
                    if not self.selected:
                        self.set_selected(True)
                        print(f"[DEBUG-SELECTION] Normal click - set visual selection")
                    
                    # If using gallery_events interface, notify directly
                    from app.templates.gallery_events import GalleryEvents
                    GalleryEvents.on_template_select(gallery, self.template)
        
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release after click or drag"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Reset pressed state
            self.mouse_is_pressed = False
            
            # Calculate the drag distance
            drag_occurred = False
            if hasattr(self, 'mouse_press_pos') and self.mouse_press_pos:
                drag_distance = (event.pos() - self.mouse_press_pos).manhattanLength()
                drag_occurred = drag_distance >= QApplication.startDragDistance()
                print(f"[DEBUG-SELECTION] MouseReleaseEvent drag_distance={drag_distance}, threshold={QApplication.startDragDistance()}, drag_occurred={drag_occurred}")
            
            # Get current modifier state - may have changed since mouse press
            current_modifiers = QApplication.keyboardModifiers()
            current_is_ctrl_cmd = bool(current_modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier))
            current_is_shift = bool(current_modifiers & Qt.KeyboardModifier.ShiftModifier)
            current_is_modifier_pressed = current_is_ctrl_cmd or current_is_shift
            
            # DEBUG LOGGING
            print(f"[DEBUG-SELECTION] MouseReleaseEvent on '{self.template_name()}'")
            print(f"[DEBUG-SELECTION] Current modifiers: CTRL/CMD={current_is_ctrl_cmd}, SHIFT={current_is_shift}")
            if hasattr(self, 'initial_selection_state'):
                print(f"[DEBUG-SELECTION] Initial modifiers: modifier_click={self.initial_selection_state['is_modifier_click']}, ctrl_cmd={self.initial_selection_state['is_ctrl_or_cmd']}, shift={self.initial_selection_state['is_shift']}")
            
            # Get gallery reference
            gallery = None
            p = self.parent()
            while p is not None:
                if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager'):
                    gallery = p
                    break
                p = p.parent()
            
            # If no gallery or drag occurred, skip selection logic
            if not gallery:
                print(f"[DEBUG-SELECTION] Skipping selection logic: gallery not found")
                self.mouse_press_pos = None
                super().mouseReleaseEvent(event)
                return
                
            # If drag occurred, we don't want to change selection state
            if drag_occurred:
                print(f"[DEBUG-SELECTION] Drag occurred, preserving selection state")
                self.mouse_press_pos = None
                super().mouseReleaseEvent(event)
                return
                
            # If we clicked on an already multi-selected item (without modifiers), we've already
            # set it as primary in mousePressEvent while preserving multi-selection
            if hasattr(self, 'clicking_multi_selected') and self.clicking_multi_selected:
                print(f"[DEBUG-SELECTION] Release after clicking multi-selected item - selection preserved")
                self.clicking_multi_selected = False
                self.mouse_press_pos = None
                super().mouseReleaseEvent(event)
                return
                
            # NOW is when we actually update the real selection state
            # We use the initial modifier state from mousePressEvent
            if hasattr(self, 'initial_selection_state') and gallery and hasattr(gallery, 'selection_manager'):
                try:
                    # Get the initial state we saved during mouse press
                    was_modifier_click = self.initial_selection_state['is_modifier_click']
                    was_ctrl_cmd_pressed = self.initial_selection_state['is_ctrl_or_cmd']
                    was_shift_pressed = self.initial_selection_state['is_shift']
                    
                    print(f"[DEBUG-SELECTION] Applying selection based on initial state: modifier_click={was_modifier_click}, ctrl_cmd={was_ctrl_cmd_pressed}, shift={was_shift_pressed}")
                    print(f"[DEBUG-SELECTION] Was selected: {self.selected}, Was multi-selected: {getattr(self, 'multi_selected', False)}")
                    
                    # Handle different cases based on the initial mouse press state
                    if not was_modifier_click:
                        # Simple click with no modifiers - select only this item
                        print(f"[DEBUG-SELECTION] Simple click - selecting only this item")
                        gallery.selection_manager.set_primary_selection(self.template, clear_multi=True)
                    elif was_ctrl_cmd_pressed:
                        # Ctrl+click - toggle this item in the selection
                        # If it was previously selected, remove it
                        if hasattr(self, 'multi_selected') and self.multi_selected:
                            print(f"[DEBUG-SELECTION] Ctrl+click on selected item - toggling off")
                            gallery.selection_manager.toggle_multi_selection(self.template)
                        # If it wasn't selected, add it
                        else:
                            print(f"[DEBUG-SELECTION] Ctrl+click on unselected item - adding to selection")
                            gallery.selection_manager.add_to_multi_selection(self.template)
                            gallery.selection_manager.set_primary_selection(self.template, clear_multi=False)
                    elif was_shift_pressed:
                        # Handle shift+click to select range
                        print(f"[DEBUG-SELECTION] Shift+click - handling range selection")
                        if hasattr(gallery.selection_manager, 'multi_selected_templates'):
                            if not gallery.selection_manager.multi_selected_templates:
                                # No existing selection, just select this item
                                gallery.selection_manager.set_primary_selection(self.template, clear_multi=True)
                            else:
                                # Add this to multi-selection
                                gallery.selection_manager.add_to_multi_selection(self.template)
                                gallery.selection_manager.set_primary_selection(self.template, clear_multi=False)
                    
                    # Update visual state to match actual selection state
                    is_primary = gallery.selection_manager.is_selected(self.template)
                    is_multi = gallery.selection_manager.is_multi_selected(self.template)
                    print(f"[DEBUG-SELECTION] Final state: primary={is_primary}, multi={is_multi}")
                    self.set_selected(is_primary)
                    self.set_multi_selected(is_multi)
                except Exception as e:
                    print(f"[ERROR] Error in template_card.mouseReleaseEvent: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Reset press tracking
            self.mouse_press_pos = None
        
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click to open template editor"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit(self.template_name())
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'mouse_is_pressed') and self.mouse_is_pressed and hasattr(self, 'mouse_press_pos') and self.mouse_press_pos and ((event.pos() - self.mouse_press_pos).manhattanLength() > QApplication.startDragDistance()):
            
            print(f"[DEBUG-DRAG] Starting drag operation on '{self.template_name()}'")
            print(f"[DEBUG-DRAG] Mouse press pos: {self.mouse_press_pos}, current pos: {event.pos()}, distance: {(event.pos() - self.mouse_press_pos).manhattanLength()}")
            
            # Find the parent gallery
            gallery = None
            p = self.parent()
            while p is not None:
                # Check for attributes that identify the TemplateGallery instance
                if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager'):
                    gallery = p
                    break
                p = p.parent()

            if not gallery:
                print("[DEBUG-DRAG] ERROR: Could not find gallery parent for drag operation")
                return

            # Store the selection state before drag starts
            primary_template = None
            multi_selected_templates = []
            if hasattr(gallery, 'selection_manager'):
                primary_template = gallery.selection_manager.selected_template
                multi_selected_templates = list(gallery.selection_manager.multi_selected_templates)
                print(f"[DEBUG-DRAG] Stored selection state - Primary: {primary_template.get('name') if primary_template else 'None'}, Multi count: {len(multi_selected_templates)}")

            # Get selection manager to check multi-selection state
            templates_to_drag = []
            if hasattr(gallery, 'selection_manager'):
                selection_manager = gallery.selection_manager
                print(f"[DEBUG-DRAG] Using selection_manager to check multi-selection")
                
                # Check if this item is in the multi-selection
                in_multi_selection = selection_manager.is_multi_selected(self.template)
                multi_selection_count = len(selection_manager.multi_selected_templates)
                
                print(f"[DEBUG-DRAG] Item in multi-selection: {in_multi_selection}")
                print(f"[DEBUG-DRAG] Multi-selection count: {multi_selection_count}")
                
                if in_multi_selection and multi_selection_count > 1:
                    print(f"[DEBUG-DRAG] Should drag multiple items: {multi_selection_count}")
                    templates_to_drag = selection_manager.multi_selected_templates
                    template_names = [t.get('name', 'Unknown') if isinstance(t, dict) else str(t) for t in templates_to_drag]
                    print(f"[DEBUG-DRAG] Templates to drag: {template_names}")
                else:
                    print(f"[DEBUG-DRAG] Should drag single item: {self.template_name()}")
                    templates_to_drag = [self.template]
            else:
                # Fallback to directly checking multi_selected_templates if no selection_manager
                print(f"[DEBUG-DRAG] No selection_manager found, checking multi_selected_templates directly")
                
                if hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
                    # Safely check if this template is in the multi-selection
                    try:
                        is_multi_selected_item = self.template in gallery.multi_selected_templates
                        if is_multi_selected_item and len(gallery.multi_selected_templates) > 1:
                            # Dragging multiple items
                            templates_to_drag = gallery.multi_selected_templates
                            print(f"[DEBUG-DRAG] Multi-selection drag with {len(templates_to_drag)} templates: {[t.get('name') if isinstance(t, dict) else str(t) for t in templates_to_drag]}")
                        else:
                            # Single item (even if in multi-selection)
                            templates_to_drag = [self.template]
                            print(f"[DEBUG-DRAG] Single template drag: {self.template.get('name') if isinstance(self.template, dict) else str(self.template)}")
                    except Exception as e:
                        print(f"[DEBUG-DRAG] Exception checking multi-selection status: {e}")
                        templates_to_drag = [self.template]
                else:
                    # No multi-selection, just drag this template
                    templates_to_drag = [self.template]
                    print(f"[DEBUG-DRAG] No multi-selection found, dragging single template: {self.template.get('name') if isinstance(self.template, dict) else str(self.template)}")

            self.dragging = True
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Setup MIME data with our helper
            print(f"[DEBUG-DRAG] Setting up MIME data for {len(templates_to_drag)} templates")
            template_names = setup_drag_mime_data(templates_to_drag, mime_data)
            drag.setMimeData(mime_data)
            
            # Create a custom drag pixmap with count indicator
            item_count = len(template_names)
            print(f"[DEBUG-DRAG] Creating drag pixmap with {item_count} templates")
            drag_pixmap = create_drag_pixmap(self, item_count=item_count)
            drag.setPixmap(drag_pixmap)
            
            # Set the hotspot to be the mouse position relative to the top-left of the pixmap
            drag.setHotSpot(event.pos() - self.rect().topLeft())

            # Execute the drag operation
            # Use CopyAction initially to prevent clearing selection
            print(f"[DEBUG-DRAG] Executing drag operation")
            result = drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction, Qt.DropAction.CopyAction)
            
            # Reset flags after drag completes
            self.dragging = False
            self.mouse_is_pressed = False
            
            # Restore selection state if it was cleared during drag
            if hasattr(gallery, 'selection_manager'):
                current_primary = gallery.selection_manager.selected_template
                current_multi = gallery.selection_manager.multi_selected_templates
                
                if (not current_primary and primary_template) or (not current_multi and multi_selected_templates):
                    print(f"[DEBUG-DRAG] Restoring selection state after drag")
                    # Only restore if selection was actually cleared
                    gallery.selection_manager.set_selection_state(primary_template, multi_selected_templates)
            
            # Optional: Handle result if needed (e.g., if MoveAction occurred)
            print(f"[DEBUG-DRAG] Drag completed with result: {result}")
            if result == Qt.DropAction.MoveAction:
                print("[DEBUG-DRAG] Drag resulted in MoveAction (Item might be removed by drop target)")

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
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #2C4F76;
                    border: none;
                    border-radius: 6px;
                }}
            """)
            
            # Text colors
            self.name_label.setStyleSheet("color: white; font-weight: bold; background-color: transparent;")
            self.category_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: transparent;")
            self.icon_label.setStyleSheet("color: white; background-color: transparent;")
        else:
            # Update based on hover or default state
            if hasattr(self, 'multi_selected') and self.multi_selected:
                # If not primary selected but is multi-selected
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
            elif self.hover:
                # Hover styling
                self.setStyleSheet(f"""
                    QFrame {{
                        background-color: {CARD_HOVER};
                        border: none;
                        border-radius: 6px;
                    }}
                """)
                
                # Text colors for hover state
                self.name_label.setStyleSheet("color: white; background-color: transparent;")
                self.category_label.setStyleSheet("color: #AAAAAA; background-color: transparent;")
                self.icon_label.setStyleSheet("color: white; background-color: transparent;")
            else:
                # Normal styling
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
        
        # Store current states as properties on the widget
        self.setProperty("is_selected", self.selected)
        self.setProperty("is_multi_selected", getattr(self, 'multi_selected', False))
        self.setProperty("is_hover", self.hover)
        
        # Force immediate style application - fixes delayed style updates
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Temporary highlight style (when template renamed)
        if hasattr(self, 'highlight_animation_active') and self.highlight_animation_active:
            # Highlight styling (bright blue with border)
            print(f"⭐ Applying HIGHLIGHT animation style to {self.template_name()}")
            
            # Card background
            self.setStyleSheet("""
                QFrame {
                    background-color: #3C6EA5;
                    border: none;
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
            
        elif self.hover:
            # Hover styling
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_HOVER};
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
        if (event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace) and self.selected:
            print(f"[DEBUG] Template Card keyPressEvent: Delete/Backspace detected for {self.template_name()}")
            # Find the parent gallery for multi-selection handling
            gallery = None
            p = self.parent()
            print(f"[DEBUG] Template Card parent: {p}")
            parent_iteration = 0
            while p and parent_iteration < 10:  # Limit to prevent infinite loop
                parent_iteration += 1
                print(f"[DEBUG] Template Card searching parent level {parent_iteration}: {p}, has multi_selected_templates: {hasattr(p, 'multi_selected_templates')}")
                if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager'):
                    gallery = p
                    print(f"[DEBUG] Template Card found gallery at parent level {parent_iteration}")
                    break
                p = p.parent()
            
            if gallery:
                print(f"[DEBUG] Template Card found gallery, calling _delete_multi_selected")
                self._delete_multi_selected(gallery)
            else:
                print(f"[DEBUG] Template Card ERROR: Could not find gallery in parent hierarchy")
                # Try alternative approach - find app and trigger deletion through app
                if hasattr(self, 'app') and self.app:
                    print(f"[DEBUG] Template Card attempting deletion through app")
                    if hasattr(self.app, 'template_gallery') and hasattr(self.app.template_gallery, '_on_delete_template'):
                        print(f"[DEBUG] Template Card using app.template_gallery._on_delete_template")
                        self.app.template_gallery._on_delete_template(self.template_name())
            
        super().keyPressEvent(event)
    
    def contextMenuEvent(self, event: QEvent):
        """Create and show a context menu for the template card"""
        from app.templates.gallery_events import GalleryEvents # Ensure import

        # Create a context menu
        # Use our custom ContextMenu class
        context_menu = ContextMenu(self)
        
        # Get template name from the card's own data
        t_name = self.template_name()
        
        # --- Add actions ---
        # Add "Edit" action
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.editRequested.emit(self.template_name()))
        context_menu.addAction(edit_action)
        
        # Find the parent gallery for multi-selection handling and folder operations
        gallery = None
        p = self.parent()
        while p is not None:
            if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager') and hasattr(p, 'current_folder'):
                gallery = p
                break
            if hasattr(p, 'template_gallery'):
                gallery_candidate = p.template_gallery
                if hasattr(gallery_candidate, 'selection_manager') and \
                   hasattr(gallery_candidate, 'template_manager') and \
                   hasattr(gallery_candidate, 'current_folder'):
                    gallery = gallery_candidate
                    break
            p = p.parent()

        if not gallery and self.app and hasattr(self.app, 'template_gallery'): # Fallback to app.template_gallery
            gallery = self.app.template_gallery

        # Determine if multi-selection is active
        has_multi_selection_active = False
        num_selected_for_context_menu = 0
        if gallery and hasattr(gallery, 'selection_manager'):
            multi_selected_items = gallery.selection_manager.multi_selected_templates
            # Check if the current card's template is among the multi-selected items
            # Card's template object: self.template
            # Multi-selected items: list of template dicts
            card_template_name = self.template.get('name') if isinstance(self.template, dict) else None
            is_current_card_in_multi_selection = False
            if card_template_name:
                for item in multi_selected_items:
                    if isinstance(item, dict) and item.get('name') == card_template_name:
                        is_current_card_in_multi_selection = True
                        break
            
            if len(multi_selected_items) > 1 and is_current_card_in_multi_selection:
                num_selected_for_context_menu = len(multi_selected_items)
                has_multi_selection_active = True
        
        # --- Delete Action ---
        delete_action_text = "Delete"
        if has_multi_selection_active:
            delete_action_text = f"Delete {num_selected_for_context_menu} Selected Templates"
        
        delete_callback = None
        if gallery: 
            delete_callback = lambda: GalleryEvents.on_delete_template(gallery)
        else:
            print("[WARNING] TemplateCard context menu: Gallery instance not found for delete action callback.")
            delete_callback = lambda: self.deleteRequested.emit(t_name)
        
        context_menu.addRedDeleteAction(parent=self, callback=delete_callback, text=delete_action_text)
        
        context_menu.addSeparator()
        
        duplicate_action = QAction("Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.duplicate_requested.emit(self.template_name()))
        context_menu.addAction(duplicate_action)
        
        export_action = QAction("Export Template...", self)
        export_action.triggered.connect(self._export_template)
        context_menu.addAction(export_action)
        
        context_menu.addSeparator()

        # --- Move to Folder ---
        if gallery and hasattr(gallery, 'template_manager'):
            move_menu = context_menu.addMenu("Move to...")
            
            # Determine current folder and if template is in any folder
            # directly from the card's own template data.
            card_template_data = self.template # self.template is the dict the card was initialized with
            is_in_any_folder = False
            current_folder_for_this_card = "" 

            if isinstance(card_template_data, dict):
                current_folder_for_this_card = card_template_data.get('parent_folder', "")
                is_in_any_folder = bool(current_folder_for_this_card)
            
            print(f"DEBUG: TemplateCard context menu for '{t_name}': in_folder={is_in_any_folder}, current_card_folder='{current_folder_for_this_card}'")
            
            move_to_root_action = QAction("No Folder", self)
            move_to_root_action.setEnabled(is_in_any_folder)
            
            def move_to_root_handler(): # Renamed to avoid conflict if contextMenuEvent is called rapidly
                print(f"DEBUG: 'No Folder' clicked for '{t_name}' (current_card_folder='{current_folder_for_this_card}')")
                # Use the same multi-selection logic as regular folder moves
                self._move_template_out_of_folder(current_folder_for_this_card) 
            
            move_to_root_action.triggered.connect(move_to_root_handler)
            move_menu.addAction(move_to_root_action)
            
            available_folders = []
            if hasattr(gallery.template_manager, 'get_folders'):
                available_folders = gallery.template_manager.get_folders()
            
            if available_folders:
                move_menu.addSeparator()
                # Determine the folder to exclude from the list (the one this card is in)
                # current_folder_for_this_card is used here
                print(f"DEBUG: TemplateCard 'Move to...' menu: current_card_folder='{current_folder_for_this_card}', gallery.current_folder='{gallery.current_folder}'")

                for folder_name_iter in sorted(available_folders):
                    if folder_name_iter == current_folder_for_this_card:
                        print(f"DEBUG: Skipping folder '{folder_name_iter}' (current folder of this card) in move menu for '{t_name}'")
                        continue

                    folder_action = QAction(folder_name_iter, self)
                    
                    # Use a lambda that captures f_name correctly and handles multi-selection
                    folder_action.triggered.connect(
                        lambda checked=False, target_folder_name=folder_name_iter: 
                            self._move_to_folder_and_hide(target_folder_name)
                    )
                    move_menu.addAction(folder_action)

        context_menu.addSeparator()

        recache_action = QAction("Recache Template Files", self)
        recache_action.triggered.connect(self._recache_template)
        context_menu.addAction(recache_action)
        
        clear_cache_action = QAction("Clear Cache for This Template", self)
        clear_cache_action.triggered.connect(self._clear_template_cache)
        context_menu.addAction(clear_cache_action)
        
        context_menu.exec(event.globalPos())

    def _move_template_out_of_folder(self, current_folder):
        """Move template out of its current folder and hide it for immediate feedback"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Template manager not available")
            return
            
        # Get gallery reference to check multi-selection
        gallery = None
        p = self.parent()
        while p is not None:
            if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager'):
                gallery = p
                break
            p = p.parent()
            
        if not gallery:
            print(f"[ERROR] Cannot move template: invalid gallery reference")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Gallery reference not found")
            return
            
        # Store a reference to the original cursor
        original_cursor = self.cursor()
        self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        
        try:
            selected_templates_for_op = []
            processed_names = set()

            # 1. Add the template from the card that was right-clicked
            if self.template and isinstance(self.template, dict) and 'name' in self.template:
                template_name = self.template.get('name')
                if template_name: # Ensure name is not empty
                    selected_templates_for_op.append(self.template)
                    processed_names.add(template_name)

            # 2. Add other unique templates from the selection manager's multi-select list
            if hasattr(gallery, 'selection_manager') and gallery.selection_manager.multi_selected_templates:
                for t_data in gallery.selection_manager.multi_selected_templates:
                    if t_data and isinstance(t_data, dict) and 'name' in t_data:
                        name = t_data.get('name')
                        if name and name not in processed_names: # Add if valid and not already added
                            selected_templates_for_op.append(t_data)
                            processed_names.add(name)
            
            if not selected_templates_for_op:
                is_self_template_invalid = not (self.template and isinstance(self.template, dict) and self.template.get('name'))
                is_multi_empty_or_only_self = True 
                if hasattr(gallery, 'selection_manager') and gallery.selection_manager.multi_selected_templates:
                    if len(gallery.selection_manager.multi_selected_templates) == 1 and gallery.selection_manager.multi_selected_templates[0] == self.template:
                        pass 
                    elif len(gallery.selection_manager.multi_selected_templates) > 0 : 
                        is_multi_empty_or_only_self = False

                if is_self_template_invalid and is_multi_empty_or_only_self:
                    print(f"[ERROR] No valid templates found for 'move out of folder' operation (self.template invalid and multi-selection did not yield others).")
                    QMessageBox.warning(self, "Move Error", "No valid templates selected for move.")
                    self.setCursor(original_cursor)
                    return

            if not selected_templates_for_op: # Final check
                print("[ERROR] No valid templates found for 'move out of folder' operation after all checks.")
                # It's possible self.template was valid but multi_selected_templates was empty, so list has 1.
                # This path should ideally not be hit if self.template is valid.
                QMessageBox.warning(self, "Move Error", "No templates selected for move (final check).")
                self.setCursor(original_cursor)
                return
                
            template_names_to_move = [t.get('name') for t in selected_templates_for_op if t.get('name')] # Ensure names are valid
            if not template_names_to_move:
                print("[ERROR] No valid template names derived from selected_templates_for_op.")
                QMessageBox.warning(self, "Move Error", "No valid template names to move.")
                self.setCursor(original_cursor)
                return
            
            print(f"Moving {len(template_names_to_move)} templates out of folder '{current_folder}': {template_names_to_move}")
            
            # Move all templates out of folder at once using GalleryEvents directly
            # This ensures multi-selection works properly by calling the move operation once with all templates
            from app.gallery.logic.gallery_events import GalleryEvents
            GalleryEvents.on_move_template_to_folder(gallery, template_names_to_move, None)
            print(f"Moved {len(template_names_to_move)} templates out of folder '{current_folder}' using GalleryEvents")
            
            # Refresh UI for immediate feedback
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Refresh the gallery view with a slight delay to ensure model is updated
            self._refresh_gallery(gallery)

        except Exception as e:
            print(f"[ERROR] Exception during move operation: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error dialog
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Move Operation Failed",
                f"An error occurred while moving template(s): {str(e)}",
                QMessageBox.Ok
            )
        finally:
            # Restore the original cursor
            self.setCursor(original_cursor)

    def _refresh_gallery(self, gallery=None):
        """Helper method to refresh gallery properly after all operations"""
        try:
            # Log more detailed information about the refresh operation
            print(f"🔍 LISTENER: Refreshing gallery with force_refresh=True")
            
            # If gallery was provided, use it directly
            if gallery and hasattr(gallery, 'populate_gallery'):
                print(f"🔍 LISTENER: Refreshing gallery using provided gallery reference")
                # Force a small delay to ensure template manager state is updated
                QTimer.singleShot(100, lambda: gallery.populate_gallery(force_refresh=True))
                return
                
            # Otherwise find parent gallery through hierarchy
            if not hasattr(self, 'parent'):
                print(f"[ERROR] Cannot refresh gallery: self.parent method not available")
                return
                
            p = self.parent()
            if not p:
                print(f"[ERROR] Cannot refresh gallery: parent is None")
                return
            
            # First try list items parent chain
            if p and hasattr(p, 'parent') and p.parent() and hasattr(p.parent(), 'populate_gallery'):
                print(f"🔍 LISTENER: Refreshing gallery through list item parent chain")
                QTimer.singleShot(100, lambda: p.parent().populate_gallery(force_refresh=True))
            # Then try direct parent
            elif p and hasattr(p, 'populate_gallery'):
                print(f"🔍 LISTENER: Refreshing gallery through direct parent")
                QTimer.singleShot(100, lambda: p.populate_gallery(force_refresh=True))
            else:
                print(f"[WARNING] Could not find a gallery to refresh")
                
        except Exception as e:
            print(f"[ERROR] Exception in _refresh_gallery: {e}")
            import traceback
            traceback.print_exc()

    def _move_to_folder_and_hide(self, folder_name):
        """Move template to folder and hide for immediate feedback"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Template manager not available")
            return
            
        # Get gallery reference to check multi-selection
        gallery = None
        p = self.parent()
        while p is not None:
            if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager'):
                gallery = p
                break
            p = p.parent()
            
        if not gallery:
            print(f"[ERROR] Cannot move template: invalid gallery reference")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Gallery reference not found")
            return
            
        # Store a reference to the original cursor
        original_cursor = self.cursor()
        self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        
        try:
            selected_templates_for_op = []
            processed_names = set()

            # 1. Add the template from the card that was right-clicked
            if self.template and isinstance(self.template, dict) and 'name' in self.template:
                template_name = self.template.get('name')
                if template_name: # Ensure name is not empty
                    selected_templates_for_op.append(self.template)
                    processed_names.add(template_name)

            # 2. Add other unique templates from the selection manager's multi-select list
            if hasattr(gallery, 'selection_manager') and gallery.selection_manager.multi_selected_templates:
                for t_data in gallery.selection_manager.multi_selected_templates:
                    if t_data and isinstance(t_data, dict) and 'name' in t_data:
                        name = t_data.get('name')
                        if name and name not in processed_names: # Add if valid and not already added
                            selected_templates_for_op.append(t_data)
                            processed_names.add(name)
            
            if not selected_templates_for_op:
                is_self_template_invalid = not (self.template and isinstance(self.template, dict) and self.template.get('name'))
                is_multi_empty_or_only_self = True 
                if hasattr(gallery, 'selection_manager') and gallery.selection_manager.multi_selected_templates:
                    if len(gallery.selection_manager.multi_selected_templates) == 1 and gallery.selection_manager.multi_selected_templates[0] == self.template:
                        pass 
                    elif len(gallery.selection_manager.multi_selected_templates) > 0 : 
                        is_multi_empty_or_only_self = False

                if is_self_template_invalid and is_multi_empty_or_only_self:
                    print(f"[ERROR] No valid templates found for 'move to folder {folder_name}' operation (self.template invalid and multi-selection did not yield others).")
                    QMessageBox.warning(self, "Move Error", "No valid templates selected for move.")
                    self.setCursor(original_cursor)
                    return

            if not selected_templates_for_op: # Final check
                print(f"[ERROR] No valid templates found for 'move to folder {folder_name}' operation after all checks.")
                QMessageBox.warning(self, "Move Error", "No templates selected for move (final check).")
                self.setCursor(original_cursor)
                return
                
            template_names_to_move = [t.get('name') for t in selected_templates_for_op if t.get('name')]
            if not template_names_to_move:
                print("[ERROR] No valid template names derived from selected_templates_for_op for move to folder.")
                QMessageBox.warning(self, "Move Error", "No valid template names to move.")
                self.setCursor(original_cursor)
                return

            print(f"Moving {len(template_names_to_move)} templates to folder '{folder_name}': {template_names_to_move}")
            
            # Move all templates to folder at once using GalleryEvents directly
            # This ensures multi-selection works properly by calling the move operation once with all templates
            from app.gallery.logic.gallery_events import GalleryEvents
            GalleryEvents.on_move_template_to_folder(gallery, template_names_to_move, folder_name)
            print(f"Moved {len(template_names_to_move)} templates to folder '{folder_name}' using GalleryEvents")
            
            # The success message will now rely on the outcome of the signal-slot mechanism.
            # For immediate feedback, we might need a way for the signal handler to report back, 
            # or assume success if no error is immediately thrown by the emit (which is not robust).
            # For now, let's assume the operation will be handled by the manager.
            # We can refine status reporting later if needed.
            if hasattr(self.app, 'show_status_message'):
                 # Since we don't have immediate feedback on success count from the signal alone,
                 # this message is more general.
                 self.app.show_status_message(f"Requested move of {len(template_names_to_move)} template(s) to '{folder_name}'", "info")

            # Refresh UI for immediate feedback
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Refresh the gallery view with a slight delay to ensure model is updated
            self._refresh_gallery(gallery)
            
        except Exception as e:
            print(f"[ERROR] Exception during move operation: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error dialog
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Move Operation Failed",
                f"An error occurred while moving template(s): {str(e)}",
                QMessageBox.Ok
            )
        finally:
            # Restore the original cursor
            self.setCursor(original_cursor)

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
                if isinstance(gallery.selected_template, dict):
                    print(f"🔍 LISTENER: Current primary selection: {gallery.selected_template.get('name', 'Unknown')}")
                else:
                    print(f"🔍 LISTENER: Current primary selection: {str(gallery.selected_template)}")
            else:
                print(f"🔍 LISTENER: No primary selection")
                
            if hasattr(gallery, 'multi_selected_templates'):
                template_names = []
                for t in gallery.multi_selected_templates:
                    if isinstance(t, dict):
                        template_names.append(t.get('name', 'Unknown'))
                    else:
                        template_names.append(str(t))
                print(f"🔍 LISTENER: Current multi-selection: {template_names}")
            
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
                if isinstance(gallery.selected_template, dict):
                    primary_name = gallery.selected_template.get('name', 'Unknown')
                else:
                    primary_name = str(gallery.selected_template)
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
                        if isinstance(template, dict):
                            print(f"🔍 LISTENER: Adding multi-selected template to delete operation: {template.get('name', 'Unknown')}")
                        else:
                            print(f"🔍 LISTENER: Adding multi-selected template to delete operation: {str(template)}")
            
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
                elif isinstance(template, dict) and hasattr(template, 'get'):
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
                if hasattr(self, 'app') and self.app and hasattr(self.app, 'template_manager'):
                    success_count = 0
                    error_count = 0
                    for name in template_names:
                        try:
                            print(f"🔍 LISTENER: Deleting template '{name}'")
                            if self.app.template_manager.delete_template(name):
                                success_count += 1
                            else:
                                error_count += 1
                                print(f"[ERROR] Template manager failed to delete template '{name}'")
                        except Exception as e:
                            error_count += 1
                            print(f"[ERROR] Exception when deleting template '{name}': {e}")
                            import traceback
                            traceback.print_exc()
                    
                    print(f"🔍 LISTENER: Delete operation completed - Success: {success_count}, Errors: {error_count}")
                else:
                    print("[ERROR] Cannot delete templates: app or template_manager not available")
                
                # Show success message
                if hasattr(self, 'app') and self.app and hasattr(self.app, 'show_status_message'):
                    if len(template_names) == 1:
                        self.app.show_status_message(f"Deleted template '{template_names[0]}'", "success")
                    else:
                        self.app.show_status_message(f"Deleted {len(template_names)} templates", "success")
                
                try:
                    # Refresh gallery to update the view
                    self._refresh_gallery(gallery)
                except Exception as e:
                    print(f"[ERROR] Failed to refresh gallery after delete: {e}")
                    import traceback
                    traceback.print_exc()
        finally:
            # Reset deletion in progress flag
            TemplateCard._deletion_in_progress = False

    def set_multi_selected(self, multi_selected):
        """Set the multi-selection state of the card with immediate visual feedback"""
        prev_state = getattr(self, 'multi_selected', False)
        self.multi_selected = multi_selected
        print(f"🔍 LISTENER: Setting multi-selection state of '{self.template_name()}' to {multi_selected}")
        
        # Set property for stylesheet access
        self.setProperty("is_multi_selected", multi_selected)
        
        # Direct styling for multi-selection state
        if multi_selected:
            if not self.selected:
                # Multi-selected but not primary - mid-blue tone
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
                
                print(f"🔍 LISTENER: Applied multi-selected style to '{self.template_name()}'")
        else:
            # Not multi-selected, update based on primary selection and hover
            if self.selected:
                # Primary selected styling
                self.setStyleSheet(f"""
                    QFrame {{
                        background-color: #2C4F76;
                        border: none;
                        border-radius: 6px;
                    }}
                """)
                
                # Text colors
                self.name_label.setStyleSheet("color: white; font-weight: bold; background-color: transparent;")
                self.category_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: transparent;")
                self.icon_label.setStyleSheet("color: white; background-color: transparent;")
            elif self.hover:
                # Hover styling
                self.setStyleSheet(f"""
                    QFrame {{
                        background-color: {CARD_HOVER};
                        border: none;
                        border-radius: 6px;
                    }}
                """)
                
                # Text colors for hover state
                self.name_label.setStyleSheet("color: white; background-color: transparent;")
                self.category_label.setStyleSheet("color: #AAAAAA; background-color: transparent;")
                self.icon_label.setStyleSheet("color: white; background-color: transparent;")
            else:
                # Default styling
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
        
        # Force style application immediately
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        
        return self.multi_selected

    def _export_template(self):
        """Export this template to a file"""
        from app.core.import_export_manager import export_template
        
        # Call the export_template function with the application and template name
        export_template(self.app, self.template_name())
    
    def _recache_template(self):
        """Recache this template's files"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        template_name = self.template_name()
        
        # Check if template manager has cache_manager
        if not hasattr(self.app.template_manager, 'cache_manager'):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Cache Manager Not Available", 
                "The cache manager is not available. Cannot recache template.",
                QMessageBox.Ok
            )
            return
        
        # Show progress dialog
        from app.templates.cache_manager import RecacheProgressDialog
        
        dialog = RecacheProgressDialog(
            self.app.template_manager.cache_manager,
            [template_name],
            self
        )
        dialog.exec()
    
    def _clear_template_cache(self):
        """Safely clear this template's cache"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        template_name = self.template_name()
        
        # Use the safe_clear_template_cache method to ensure we don't lose important files
        if hasattr(self.app.template_manager, 'safe_clear_template_cache'):
            success = self.app.template_manager.safe_clear_template_cache(template_name)
            
            if success:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, 
                    "Cache Cleared", 
                    f"Cache for template '{template_name}' has been cleared.",
                    QMessageBox.Ok
                )
        else:
            # Fallback to regular clear_template_cache if safe version not available
            if (hasattr(self.app.template_manager, 'file_cache_manager') and 
                hasattr(self.app.template_manager.file_cache_manager, 'clear_template_cache')):
                
                from PyQt6.QtWidgets import QMessageBox
                
                result = QMessageBox.question(
                    self, 
                    "Clear Template Cache", 
                    f"Are you sure you want to clear the cache for template '{template_name}'?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if result == QMessageBox.Yes:
                    success = self.app.template_manager.file_cache_manager.clear_template_cache(template_name)
                    
                    if success:
                        QMessageBox.information(
                            self, 
                            "Cache Cleared", 
                            f"Cache for template '{template_name}' has been cleared.",
                            QMessageBox.Ok
                        )
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, 
                    "Cache Manager Not Available", 
                    "The cache manager is not available. Cannot clear template cache.",
                    QMessageBox.Ok
                )

# Utility function for QIcon cache (Optional but good practice)
icon_cache = {} 