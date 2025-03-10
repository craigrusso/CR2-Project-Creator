#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMenu, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QMimeData, QByteArray, QEvent
from PyQt5.QtGui import QCursor, QFont, QDrag, QPixmap

from app.ui.color_scheme_pyqt import colors

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

class TemplateCard(QFrame):
    """Template card widget for displaying a file template in the gallery"""
    
    clicked = pyqtSignal(dict)
    context_menu_requested = pyqtSignal(QPoint, dict)
    hover_enter = pyqtSignal(object)
    hover_leave = pyqtSignal(object)
    
    def __init__(self, parent=None, template=None, app=None):
        super().__init__(parent)
        
        self.template = template
        self.app = app
        self.highlighted = False
        self.hover = False
        
        # Apply styles
        self.setObjectName("templateCard")
        self.setMinimumSize(180, 180)
        self.setMaximumSize(220, 220)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Card layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        
        # Template icon
        self.icon_wrapper = QWidget()
        self.icon_layout = QVBoxLayout(self.icon_wrapper)
        self.icon_layout.setContentsMargins(0, 0, 0, 0)
        self.icon_layout.setAlignment(Qt.AlignCenter)
        
        self.icon = QLabel()
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setMinimumSize(80, 80)
        self.icon.setMaximumSize(100, 100)
        self.set_icon()
        self.icon_layout.addWidget(self.icon)
        
        # Template name
        self.name_label = QLabel(template.get('name', 'Unnamed Template') if template else 'Unnamed Template')
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Template description (truncated)
        description = template.get('description', '') if template else ''
        if len(description) > 60:
            description = description[:60] + "..."
        self.desc_label = QLabel(description)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #999; font-size: 12px;")
        
        # Structure indicator
        self.structure_indicator = QLabel(self)
        self.structure_indicator.setText("📂")  # Folder emoji 
        self.structure_indicator.setToolTip("This template has a custom folder structure")
        self.structure_indicator.setStyleSheet("background-color: rgba(0,0,0,0); color: #4CAF50; font-size: 16px; font-weight: bold;")
        self.structure_indicator.setGeometry(self.width() - 30, 10, 20, 20)
        
        # Check if the template has a structure
        if template and template.get('structure_name'):
            self.structure_indicator.setVisible(True)
        else:
            self.structure_indicator.setVisible(False)
        
        # Add to layout
        self.layout.addWidget(self.icon_wrapper)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.desc_label)
        
        # Set up event filter for hover detection
        self.installEventFilter(self)
        
        # Connect mouse events
        self.drag_start_position = None  # Initialize drag start position
        
        # Override mouse events
        self.mousePressEvent = self._on_mouse_press
        self.mouseMoveEvent = self._on_mouse_move
        self.enterEvent = self._on_hover_enter
        self.leaveEvent = self._on_hover_leave
        self.contextMenuEvent = self._on_context_menu
    
    def set_icon(self):
        """Set the icon for the template card"""
        icon = self.template.get("icon", "📄")
        self.icon.setPixmap(QPixmap(icon))
        self.icon.setStyleSheet(f"color: {colors['text']}; background: transparent;")
    
    def _on_mouse_press(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            # Emit clicked signal
            self.clicked.emit(self.template)
    
    def _on_mouse_move(self, event):
        """Handle mouse move event for drag and drop"""
        # Skip if drag start position is not set or left button is not pressed
        if not self.drag_start_position or not (event.buttons() & Qt.LeftButton):
            return
            
        # Compute distance to determine if it's a drag
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
        
        print(f"[DEBUG] TemplateCard: Starting drag for template '{self.template.get('name', '')}'")
        
        # Create a drag object
        drag = QDrag(self)
        
        # Create mime data with template information
        mime_data = QMimeData()
        
        # Add the template name as text for simple drag/drop operations
        template_name = self.template.get('name', '')
        mime_data.setText(template_name)
        print(f"[DEBUG] TemplateCard: Added template name '{template_name}' as text to mime data")
        
        # Also add the complete template as JSON data for more advanced operations
        try:
            import json
            template_json = json.dumps(self.template).encode()
            mime_data.setData("application/json", QByteArray(template_json))
            print(f"[DEBUG] TemplateCard: Added template as JSON to mime data")
        except Exception as e:
            print(f"[DEBUG] TemplateCard: Error adding JSON data: {e}")
        
        # Set the mime data on the drag object
        drag.setMimeData(mime_data)
        
        # Create a pixmap for the drag feedback
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # Execute the drag operation
        print(f"[DEBUG] TemplateCard: Executing drag operation")
        result = drag.exec_(Qt.CopyAction)
        print(f"[DEBUG] TemplateCard: Drag operation completed with result: {result}")
        
        # Reset drag start position
        self.drag_start_position = None
    
    def _on_hover_enter(self, event):
        """Handle hover enter event"""
        if not self.highlighted:
            self.hover = True
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_HOVER};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
    
    def _on_hover_leave(self, event):
        """Handle hover leave event"""
        if not self.highlighted:
            self.hover = False
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_NORMAL};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
    
    def _on_context_menu(self, event):
        """Handle context menu event"""
        if self.app:
            # Create a context menu
            menu = QMenu(self)
            
            # Actions
            edit_action = menu.addAction("Edit Template")
            structure_action = menu.addAction("Edit Structure")
            preview_action = menu.addAction("Preview Structure")
            duplicate_action = menu.addAction("Duplicate Template")
            delete_action = menu.addAction("Delete Template")
            
            # Execute the menu
            action = menu.exec_(self.mapToGlobal(event.pos()))
            
            # Handle selected action
            if action == edit_action:
                # Edit template
                from app.templates.templates import edit_directory_template
                edit_directory_template(self.app, self.template)
            elif action == structure_action:
                # Edit structure
                from app.templates.templates import edit_template_structure
                edit_template_structure(self.app, self.template)
            elif action == preview_action:
                # Preview structure
                from app.templates.templates import apply_structure_to_template
                apply_structure_to_template(self.app, self.template)
            elif action == duplicate_action:
                # Duplicate template
                # Implement duplicating templates
                if self.app and hasattr(self.app, 'template_manager'):
                    try:
                        # Get new name for the duplicated template
                        original_name = self.template.get('name', '')
                        new_name = f"{original_name} (Copy)"
                        
                        # Make sure the new name is unique
                        i = 1
                        while self.app.template_manager.get_template_by_name(new_name):
                            new_name = f"{original_name} (Copy {i})"
                            i += 1
                        
                        # Create duplicate with new name
                        duplicate = self.template.copy()
                        duplicate['name'] = new_name
                        
                        # Add the duplicate to the template manager
                        success = self.app.template_manager.add_template(duplicate)
                        
                        if success:
                            if hasattr(self.app, 'show_status_message'):
                                self.app.show_status_message(f"Duplicated template '{original_name}' as '{new_name}'", "info")
                            
                            # Refresh the gallery to show the new template
                            if hasattr(self.app, 'template_gallery') and hasattr(self.app.template_gallery, 'populate_gallery'):
                                self.app.template_gallery.populate_gallery(force_refresh=True)
                        else:
                            from PyQt5.QtWidgets import QMessageBox
                            QMessageBox.warning(self, "Error", f"Failed to duplicate template '{original_name}'.")
                    except Exception as e:
                        print(f"Error duplicating template: {e}")
                        from PyQt5.QtWidgets import QMessageBox
                        QMessageBox.warning(self, "Error", f"Failed to duplicate template: {e}")
            elif action == delete_action:
                # Delete template
                # Implement deleting templates
                if self.app and hasattr(self.app, 'template_manager'):
                    try:
                        template_name = self.template.get('name', '')
                        
                        # Confirm deletion
                        from PyQt5.QtWidgets import QMessageBox
                        confirm = QMessageBox.question(
                            self,
                            "Confirm Delete",
                            f"Are you sure you want to delete template '{template_name}'?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        
                        if confirm == QMessageBox.Yes:
                            # Delete the template
                            success = self.app.template_manager.delete_template(template_name)
                            
                            if success:
                                if hasattr(self.app, 'show_status_message'):
                                    self.app.show_status_message(f"Deleted template '{template_name}'", "info")
                                
                                # Refresh the gallery to reflect the deletion
                                if hasattr(self.app, 'template_gallery') and hasattr(self.app.template_gallery, 'populate_gallery'):
                                    self.app.template_gallery.populate_gallery(force_refresh=True)
                            else:
                                QMessageBox.warning(self, "Error", f"Failed to delete template '{template_name}'.")
                    except Exception as e:
                        print(f"Error deleting template: {e}")
                        from PyQt5.QtWidgets import QMessageBox
                        QMessageBox.warning(self, "Error", f"Failed to delete template: {e}")
            
            # Emit context menu signal with position and template
            self.context_menu_requested.emit(self.mapToGlobal(event.pos()), self.template)
    
    def set_highlighted(self, highlighted):
        """Set highlighted state"""
        self.highlighted = highlighted
        self._update_styling()

    def set_selected(self, selected):
        """Set selected state (alias for set_highlighted for compatibility)"""
        self.set_highlighted(selected)
    
    def _update_styling(self):
        """Update styling based on selected and hover state"""
        if self.highlighted:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_SELECTED};
                    border: 1px solid {colors["highlight_border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
            self.icon.setStyleSheet(f"color: white; background: transparent;")
            self.name_label.setStyleSheet(f"color: white; background: transparent;")
            self.desc_label.setStyleSheet(f"color: white; background: transparent;")
        elif self.hover:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_HOVER};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
            self.icon.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_NORMAL};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
            self.icon.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")

    def eventFilter(self, obj, event):
        """Event filter for hover detection"""
        if obj == self:
            if event.type() == QEvent.Enter:
                self._on_hover_enter(event)
                return True
            elif event.type() == QEvent.Leave:
                self._on_hover_leave(event)
                return True
            elif event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    # Store position for potential drag start
                    self.drag_start_position = event.pos()
                    # Also handle the click
                    self._on_mouse_press(event)
                    return True
            elif event.type() == QEvent.ContextMenu:
                self._on_context_menu(event)
                return True
        return super().eventFilter(obj, event) 