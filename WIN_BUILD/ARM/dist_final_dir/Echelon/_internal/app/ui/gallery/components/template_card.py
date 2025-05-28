# template_card.py

from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QMenu, QAction, QMessageBox, 
    QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QSizePolicy, QApplication,
    QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QMimeData, QSize, QPoint, QRect, QByteArray, QTimer
from PyQt6.QtGui import QPixmap, QFont, QDrag, QPainter, QColor, QBrush, QPen, QIcon, QCursor, QPalette
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
        icon_size = 64 # Define icon size
        pixmap = None

        # --- MODIFIED: Always use template_structure_icon.svg ---
        icon_filename = "template_structure_icon.svg"
        icon_path = get_resource_path(os.path.join(
            "app", "assets", "icons", "templates", icon_filename)) # Corrected path
        print(f"DEBUG (Card Icon Path): {icon_path}")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(QSize(icon_size, icon_size))
            if pixmap.isNull():
                print(f"ERROR (Card): Failed to load icon pixmap from: {icon_path}")
        else:
            print(f"ERROR (Card): Icon file not found at: {icon_path}")
        # --- END MODIFICATION --- 
        
        # Set the pixmap if successfully created
        if pixmap and not pixmap.isNull():
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("?") # Fallback text
            print("ERROR (Card): Could not set icon pixmap.")
            
        self.icon_label.setAlignment(Qt.AlignmentFlagFlagFlag.AlignCenter)
        icon_layout.addWidget(self.icon_label, 1, Qt.AlignmentFlagFlagFlag.AlignCenter)
        layout.addWidget(icon_container)
        
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
            self.warning_indicator.setAlignment(Qt.AlignmentFlagFlagFlag.AlignCenter)
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
        self.name_label.setAlignment(Qt.AlignmentFlagFlagFlag.AlignCenter)
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
        self.category_label.setAlignment(Qt.AlignmentFlagFlagFlag.AlignCenter)
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
            result = drag.exec_(Qt.CopyAction | Qt.MoveAction, Qt.CopyAction) 
            
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
            if result == Qt.MoveAction:
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
        if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
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
    
    def contextMenuEvent(self, event):
        """Show context menu when right-clicked"""
        if not self.app or not hasattr(self.app, 'template_manager'):
            return
            
        # CRITICAL: First, apply immediate visual selection feedback
        # This ensures the user sees this template as selected before the context menu appears
        self.set_selected(True)
        
        # Create context menu using our custom class
        context_menu = ContextMenu(self)
        
        # Add "Edit" action
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.editRequested.emit(self.template_name()))
        context_menu.addAction(edit_action)
        
        # Find the parent gallery for multi-selection handling
        gallery = None
        p = self.parent()
        while p is not None:
            if hasattr(p, 'selection_manager') and hasattr(p, 'template_manager'):
                gallery = p
                break
            p = p.parent()
        
        # Before showing context menu, ensure this item is selected if it's not already part of selection
        is_in_multi_selection = False
        if gallery and hasattr(gallery, 'selection_manager'):
            try:
                # Use the selection manager's safe methods to check multi-selection
                if hasattr(gallery.selection_manager, 'is_multi_selected'):
                    is_in_multi_selection = gallery.selection_manager.is_multi_selected(self.template)
                # Fallback to direct check if the method doesn't exist
                elif hasattr(gallery, 'multi_selected_templates'):
                    is_in_multi_selection = self.template in gallery.multi_selected_templates
            except Exception as e:
                print(f"Error checking multi-selection: {e}")
        
        # If not already in multi-selection, select it (preserving existing multi-selection)
        if gallery and not is_in_multi_selection:
            # Check if we have modifiers pressed (ctrl/cmd)
            modifiers = QApplication.keyboardModifiers()
            is_modifier_pressed = bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier | Qt.KeyboardModifier.ShiftModifier))
            
            # If no modifiers, set this as primary but preserve multi-selection
            if not is_modifier_pressed:
                # Don't clear multi-selection when right-clicking
                if hasattr(gallery, 'selection_manager'):
                    # Use clear_multi=False to preserve existing multi-selection
                    gallery.selection_manager.set_primary_selection(self.template, emit_signal=True, clear_multi=False)
                    
                    # Always update our own visual state after changing selection
                    is_primary = gallery.selection_manager.is_selected(self.template)
                    is_multi = gallery.selection_manager.is_multi_selected(self.template)
                    self.set_selected(is_primary)
                    self.set_multi_selected(is_multi)
                # Fallback for galleries without selection_manager
                elif hasattr(gallery, 'selected_template'):
                    gallery.selected_template = self.template
                    
                    # Always update our own visual state
                    self.set_selected(True)
        
        # Check if we're in a multi-selection state - using selection_manager if available
        has_multi = False
        if gallery:
            if hasattr(gallery, 'selection_manager') and hasattr(gallery.selection_manager, 'multi_selected_templates'):
                has_multi = bool(gallery.selection_manager.multi_selected_templates) and len(gallery.selection_manager.multi_selected_templates) > 1
            elif hasattr(gallery, 'multi_selected_templates'):
                has_multi = bool(gallery.multi_selected_templates) and len(gallery.multi_selected_templates) > 1
                    
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
        
        # Add duplicate template option
        duplicate_action = QAction("Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.duplicate_requested.emit(self.template_name()))
        context_menu.addAction(duplicate_action)
        
        # Add export template option
        export_action = QAction("Export Template...", self)
        export_action.triggered.connect(lambda: self._export_template())
        context_menu.addAction(export_action)
        
        # Add cache management submenu
        cache_menu = ContextMenu(context_menu)
        cache_menu.setTitle("Cache Management")
        
        # Add cache management actions
        recache_action = QAction("Recache Template", self)
        recache_action.triggered.connect(lambda: self._recache_template())
        cache_menu.addAction(recache_action)
        
        clear_cache_action = QAction("Clear Template Cache", self)
        clear_cache_action.triggered.connect(lambda: self._clear_template_cache())
        cache_menu.addAction(clear_cache_action)
        
        # Add cache management submenu to main menu
        context_menu.addSeparator()
        context_menu.addMenu(cache_menu)
        
        # --- Keep reference to action during exec_ ---
        self._temp_duplicate_action = duplicate_action 
        # --- END ---

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
            move_to_root_action = QAction("No Folder", self)
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
                    
                # Create a properly captured lambda for this folder using a function factory
                def make_action_for_folder(folder):
                    action = QAction(folder, self)
                    action.triggered.connect(lambda checked=False, f=folder: self._move_to_folder_and_hide(f))
                    return action
                
                # Add the folder action to the menu
                move_to_menu.addAction(make_action_for_folder(folder_name))
        
        # Only add the Move To menu if it has items
        if not move_to_menu.isEmpty():
            context_menu.addMenu(move_to_menu)
        
        # Show the menu
        context_menu.exec_(event.globalPos())
        
        # When context menu closes, make sure our selection state reflects reality
        if gallery and hasattr(gallery, 'selection_manager'):
            try:
                is_primary = gallery.selection_manager.is_selected(self.template)
                is_multi = gallery.selection_manager.is_multi_selected(self.template)
                self.set_selected(is_primary)
                self.set_multi_selected(is_multi)
            except Exception as e:
                print(f"[ERROR] Error updating selection visuals after context menu: {e}")

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
        self.setCursor(QCursor(Qt.WaitCursor))
        
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
            
            # Move all templates out of folder
            for template_name in template_names_to_move:
                # EMIT THE SIGNAL first - this helps grid/list view compatibility
                print(f"Emitting moveToFolderRequested signal for '{template_name}' to 'no folder'")
                self.moveToFolderRequested.emit(template_name, "")
            
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
        self.setCursor(QCursor(Qt.WaitCursor))
        
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
            
            # Move all templates to folder
            for template_name in template_names_to_move:
                # EMIT THE SIGNAL first - this helps grid/list view compatibility
                print(f"Emitting moveToFolderRequested signal for '{template_name}' to '{folder_name}'")
                self.moveToFolderRequested.emit(template_name, folder_name)
            
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