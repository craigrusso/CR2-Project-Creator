# template_folder_card.py

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFrame, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QMenu, QWidget, QApplication, QStyle
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QEvent, QPoint, QRect, QRectF, QMimeData, QByteArray
from PyQt6.QtGui import QFont, QIcon, QPixmap, QCursor, QColor, QFontMetrics, QPainter, QBrush, QPen, QPainterPath, QDrag
from app.templates.components.utils import SYSTEM_FONT
from app.templates.components.common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED
from app.ui.color_scheme_pyqt import colors, MENU_DESTRUCTIVE_ITEM_STYLE, DELETE_TEXT_STYLE
from app.templates.components.menu_actions import ContextMenu # Corrected import
from app.constants import get_resource_path
from app.templates.mime_types import TEMPLATE_NAMES_MIME_TYPE, TEMPLATE_MULTI_DRAG_MIME_TYPE, TEMPLATE_MULTI_SELECTION_MIME_TYPE
import os
import json

class TemplateFolderCard(QFrame):
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)
    renameRequested = pyqtSignal(str)
    renameDone = pyqtSignal(str, str)
    deleteRequested = pyqtSignal(str)

    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        self.editing = False
        self.setAcceptDrops(True)

        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.setInterval(250)
        self.click_timer.timeout.connect(self._handle_single_click)
        self.click_pending = False

        self.setObjectName(f"folder_card_{folder_name}")
        self.setProperty("class", "folder_card")
        
        # Card styles
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMinimumSize(120, 130)  # Increase minimum height for text
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Ensure card can receive keyboard focus

        # Layouts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)  # Increase spacing between icon and text

        # Icon Label (3D macOS-style Folder Icon)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- MODIFICATION START: Use System Icon --- 
        # Get the standard system directory icon
        try:
            style = QApplication.style()
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon) 
            pixmap = icon.pixmap(64, 64) # Initial size
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap)
                self.icon_label.setFixedSize(64, 64)
            else:
                print("ERROR (FolderCard): Failed to get standard system folder icon pixmap.")
                self.icon_label.setText("??") # Fallback
        except Exception as e:
            print(f"ERROR (FolderCard): Exception getting system icon: {e}")
            self.icon_label.setText("SYSERR") # Fallback for exception
        # --- MODIFICATION END ---
        
        self.layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignCenter)  # Force center alignment

        # Folder Name Label/LineEdit
        self.name_container = QWidget()
        self.name_container.setObjectName("folderNameContainer")
        # Make container background transparent
        self.name_container.setStyleSheet("background-color: transparent;")
        self.name_layout = QHBoxLayout(self.name_container)
        self.name_layout.setContentsMargins(0, 0, 0, 0)
        self.name_layout.setSpacing(0)

        self.name_label = QLabel(self.folder_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(SYSTEM_FONT)
        font.setPointSize(10)
        self.name_label.setFont(font)
        # Use text color from main `colors` dictionary
        self.name_label.setStyleSheet(f"color: {colors.get('text', '#FFFFFF')}; background-color: transparent; font-size: 10pt;")
        self.name_label.setWordWrap(True)
        self.name_label.setFixedWidth(100)  # Set fixed width to ensure proper wrapping
        self.name_layout.addWidget(self.name_label)

        self.rename_edit = QLineEdit(self.folder_name)
        self.rename_edit.setFont(font)
        self.rename_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rename_edit.setStyleSheet(f"color: {colors.get('text', '#FFFFFF')}; background-color: {colors.get('input_bg', '#444444')}; border: 1px solid {colors.get('highlight_bg', '#5A5A5A')}; border-radius: 3px;")
        self.rename_edit.editingFinished.connect(self._finish_rename)
        self.rename_edit.returnPressed.connect(self._finish_rename) # Also finish on Enter
        self.rename_edit.setVisible(False)
        self.name_layout.addWidget(self.rename_edit)

        self.layout.addWidget(self.name_container, 0, Qt.AlignmentFlag.AlignCenter)  # Force center alignment

        # Set frame background to transparent
        self.setAutoFillBackground(False)
        # Apply the background color from main app background
        self.setStyleSheet(f"background-color: {colors.get('bg', '#1E1E1E')}; border-radius: 6px;")

        self.installEventFilter(self)
        self.name_label.installEventFilter(self)

        self._update_styling()

    def _handle_single_click(self):
        if not self.editing:
            self.clicked.emit(self.folder_name)

    def _update_styling(self):
        """Update the styling based on hover and selection state"""
        # Get app bg color for normal state to match surrounding
        app_bg = colors.get('bg', '#1E1E1E')
        
        if self.editing:
            # Special style for renaming (maybe just keep border?)
            self.setStyleSheet(f"background-color: {app_bg}; border-radius: 6px; border: 1px solid {colors.get('highlight_bg', '#FFFFFF')};")
        elif self.selected:
            self.setStyleSheet(f"background-color: {CARD_SELECTED}; border-radius: 6px; border: none;")
        elif self.hover:
            self.setStyleSheet(f"background-color: {CARD_HOVER}; border-radius: 6px; border: none;")
        else:
            self.setStyleSheet(f"background-color: {app_bg}; border-radius: 6px; border: none;")
        # Update name label color based on selection too if needed
        text_color = colors.get('highlight_text', '#FFFFFF') if self.selected else colors.get('text', '#DDDDDD')
        self.name_label.setStyleSheet(f"color: {text_color}; background-color: transparent; font-size: 10pt;")

    def resize_icon(self, scale_percent):
        """Resize just the icon based on scale percentage, preserving the macOS Finder behavior"""
        # Base sizes at 100%
        base_icon_size = 64
        base_card_width = 120
        base_card_height = 130
        
        # Calculate new sizes based on scale percentage
        new_icon_size = int(base_icon_size * scale_percent / 100)
        new_card_width = max(int(base_card_width * scale_percent / 100), 80)  # Minimum width of 80px
        new_card_height = max(int(base_card_height * scale_percent / 100), 100)  # Minimum height
        
        # Update card size
        self.setFixedSize(new_card_width, new_card_height)
        
        # --- MODIFICATION START: Use System Icon in resize --- 
        # Get standard system icon at the new size
        try:
            style = QApplication.style()
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            pixmap = icon.pixmap(new_icon_size, new_icon_size)
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap)
            else:
                print(f"ERROR (resize_icon): Failed to get standard system folder icon pixmap at size {new_icon_size}.")
                self.icon_label.setText("??") # Fallback
        except Exception as e:
            print(f"ERROR (resize_icon): Exception getting system icon: {e}")
            self.icon_label.setText("SYSERR") # Fallback for exception
        # --- MODIFICATION END ---
        
        # Set icon container size to prevent clipping
        self.icon_label.setFixedSize(new_icon_size, new_icon_size)
        
        # Update spacing based on scale
        spacing = max(int(8 * scale_percent / 100), 4)  # Minimum spacing of 4px
        self.layout.setSpacing(spacing)
        
        # Set name label width based on card width
        name_width = min(new_card_width - 20, 120)  # Keep some margin, max 120px
        self.name_label.setFixedWidth(name_width)
        
        # Adjust font size only slightly based on scale - don't make it too small
        font_size = max(int(10 * (0.7 + (scale_percent / 300))), 8)  # Min font size 8pt, don't scale too aggressively
        
        # Set a fixed font size
        font = QFont(SYSTEM_FONT)
        font.setPointSize(font_size)
        self.name_label.setFont(font)
        
        # Also ensure text color is preserved
        text_color = colors.get('highlight_text', '#FFFFFF') if self.selected else colors.get('text', '#DDDDDD')
        self.name_label.setStyleSheet(f"color: {text_color}; background-color: transparent; font-size: {font_size}pt;")

    def eventFilter(self, obj, event):
        if obj == self.name_label and event.type() == QEvent.Type.MouseButtonDblClick:
            if not self.editing:
                self._start_rename()
                return True
        return super().eventFilter(obj, event)

    def mouseDoubleClickEvent(self, event):
        if not self.editing:
            self.doubleClicked.emit(self.folder_name)

    def dragEnterEvent(self, event):
        """Accept drag if it contains template data"""
        mime_data = event.mimeData()
        
        # Accept if any of our supported MIME types are present
        if (mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE) or 
            mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE) or
            mime_data.hasFormat(TEMPLATE_MULTI_DRAG_MIME_TYPE) or
            mime_data.hasText()):
                
            # Apply visual feedback with solid border (was dashed)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.get('accent_hover', '#5A5A5A')};
                    border: 2px solid {colors.get('accent', '#FFFFFF')};
                    border-radius: 8px;
                }}
                QLabel {{
                    color: {colors.get('highlight_text', '#FFFFFF')};
                    background-color: transparent;
                }}
            """)
            
            # Accept the drag
            event.acceptProposedAction()
            
            # Log the event
            if mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE):
                try:
                    data = mime_data.data(TEMPLATE_NAMES_MIME_TYPE).data().decode('utf-8')
                    print(f"[DEBUG] DragEnter: Drag entered folder '{self.folder_name}' with TEMPLATE_NAMES_MIME_TYPE: {data}")
                except Exception as e:
                    print(f"[DEBUG] DragEnter: Drag entered folder '{self.folder_name}' with TEMPLATE_NAMES_MIME_TYPE (decode error: {e})")
            elif mime_data.hasText():
                print(f"[DEBUG] DragEnter: Drag entered folder '{self.folder_name}' with text: {mime_data.text()}")
            else:
                print(f"[DEBUG] DragEnter: Drag entered folder '{self.folder_name}' with supported MIME type")
            
        else:
            print(f"[DEBUG] DragEnter: Rejected drag for folder '{self.folder_name}' - invalid mime data")
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Continue accepting the drag"""
        mime_data = event.mimeData()
        
        # Accept if any of our supported MIME types are present
        if (mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE) or 
            mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE) or
            mime_data.hasFormat(TEMPLATE_MULTI_DRAG_MIME_TYPE) or
            mime_data.hasText()):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Reset styling when drag leaves"""
        self._update_styling()
        event.accept()
    
    def dropEvent(self, event):
        """Handle the drop event to move templates."""
        mime_data = event.mimeData()
        
        try:
            # First priority: check for our standardized MIME type
            if mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE):
                template_names_data = mime_data.data(TEMPLATE_NAMES_MIME_TYPE).data().decode('utf-8')
                template_names = template_names_data.strip().split('\n')
                
                print(f"[DEBUG] Drop: Processing {len(template_names)} templates from {TEMPLATE_NAMES_MIME_TYPE}")
                
                # Process the templates
                self._process_template_names(template_names, event)
                return
                
            # Second priority: check for multi-selection data
            elif mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE):
                multi_data = mime_data.data(TEMPLATE_MULTI_SELECTION_MIME_TYPE).data()
                template_names = json.loads(multi_data.decode())
                
                print(f"[DEBUG] Drop: Processing {len(template_names)} templates from {TEMPLATE_MULTI_SELECTION_MIME_TYPE}")
                
                # Process the templates
                self._process_template_names(template_names, event)
                return
                
            # Fallback to plain text
            elif mime_data.hasText():
                text_data = mime_data.text().strip()
                
                # Check if it contains multiple templates (newline-separated)
                if '\n' in text_data:
                    template_names = text_data.split('\n')
                    print(f"[DEBUG] Drop: Processing {len(template_names)} templates from text data (multiple)")
                    
                    # Process the templates
                    self._process_template_names(template_names, event)
                else:
                    # Single template
                    template_name = text_data
                    print(f"[DEBUG] Drop: Processing single template from text data: {template_name}")
                    
                    # Use existing single template processing
                    result = self._add_template_to_folder(template_name)
                    
                    if result:
                        print(f"[DEBUG] Card: Successfully moved template")
                        # Show success message in status bar
                        if hasattr(self.app, 'show_status_message'):
                            self.app.show_status_message(f"Template '{template_name}' added to folder '{self.folder_name}'", "info")
                        
                        # Refresh the gallery
                        gallery = self._find_gallery()
                        if gallery and hasattr(gallery, 'populate_gallery'):
                            gallery.populate_gallery(force_refresh=True)
                        
                        # Accept the drop
                        event.acceptProposedAction()
                        return True
                    else:
                        print(f"[DEBUG] Card: Failed to move template")
            
            # If we get here, we couldn't handle the drop
            event.ignore()
            return False
            
        except Exception as e:
            print(f"[ERROR] Failed to process drop data: {e}")
            import traceback
            traceback.print_exc()
            event.ignore()
            return False
            
        # Always reset styling
        self._update_styling()
        
    def _process_template_names(self, template_names, event):
        """Process a list of template names for the drop event"""
        # Find the template manager
        template_manager = None
        gallery = self._find_gallery()
        
        if gallery and hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
            template_manager = gallery.app.template_manager
        elif self.app and hasattr(self.app, 'template_manager'):
            template_manager = self.app.template_manager
            
        if template_manager and hasattr(template_manager, 'move_template_to_folder'):
            success_count = 0
            # Process only unique template names to avoid duplicate operations
            processed_names = set()
            
            for template_name in template_names:
                if not template_name or not template_name.strip():
                    continue
                    
                # Sanitize the template name
                sanitized_name = template_name.strip()
                
                # Skip if we've already processed this template in this batch
                if sanitized_name in processed_names:
                    print(f"[DEBUG] Skipping duplicate template name: '{sanitized_name}'")
                    continue
                
                processed_names.add(sanitized_name)
                
                try:
                    # Try to find the actual template first to verify it exists
                    template = None
                    if hasattr(template_manager, 'get_template_by_name'):
                        template = template_manager.get_template_by_name(sanitized_name)
                    
                    if template:
                        # If found, use the real template name from the template object
                        real_name = template.get('name', sanitized_name)
                        print(f"[DEBUG] Found template '{real_name}' for drop operation")
                        
                        # Call the move function for the template
                        success = template_manager.move_template_to_folder(real_name, self.folder_name)
                    else:
                        # If not found, try with the provided name anyway (our improved move_template_to_folder will handle it)
                        print(f"[DEBUG] Template lookup failed for '{sanitized_name}', trying move operation directly")
                        success = template_manager.move_template_to_folder(sanitized_name, self.folder_name)
                    
                    if success:
                        success_count += 1
                    else:
                        print(f"[WARNING] Failed to move template '{sanitized_name}' to folder '{self.folder_name}'")
                except Exception as move_error:
                    print(f"[ERROR] Error moving template '{sanitized_name}': {move_error}")
                    import traceback
                    traceback.print_exc()

            if success_count > 0:
                print(f"Successfully moved {success_count}/{len(processed_names)} templates to {self.folder_name}")
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
                
                # Show success message in status bar
                if hasattr(self.app, 'show_status_message'):
                    self.app.show_status_message(f"Added {success_count} templates to folder '{self.folder_name}'", "info")
                
                # Refresh the gallery view after move
                if gallery and hasattr(gallery, 'populate_gallery'):
                    gallery.populate_gallery(force_refresh=True)
            else:
                print(f"No templates were successfully moved.")
        else:
            print("[ERROR] Could not find template_manager or move_template_to_folder method.")
            event.ignore()
            
    def _find_gallery(self):
        """Helper method to find the parent gallery"""
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'populate_gallery'):
                gallery = parent
                break
            parent = parent.parent()
        return gallery

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.editing:
            self.click_timer.start()
            self.setFocus()  # Ensure the card gets focus when clicked

    def _start_rename(self):
        """Start inline renaming of folder"""
        try:
            # Check if this is a default folder that cannot be renamed
            if self.folder_name in ["General", "Development", "Business"]:
                if hasattr(self.app, 'show_status_message'):
                    self.app.show_status_message(f"'{self.folder_name}' is a default folder and cannot be renamed.", "warning")
                else:
                    QMessageBox.warning(None, "Error", f"'{self.folder_name}' is a default folder and cannot be renamed.")
                return
                
            # Switch to edit mode
            self.editing = True
            
            # Hide label, show edit field
            self.name_label.hide()
            self.rename_edit.setText(self.folder_name)
            self.rename_edit.show()
            self.rename_edit.setFocus()
            self.rename_edit.selectAll()
            
            # Emit signal that rename was requested
            self.renameRequested.emit(self.folder_name)
        except Exception as e:
            print(f"Error in _start_rename: {e}")
            import traceback
            traceback.print_exc()
        
    def _finish_rename(self):
        """Finish inline renaming and apply the change"""
        try:
            if not self.editing:
                return
                
            self.editing = False
            new_name = self.rename_edit.text().strip()
            
            # Hide edit field, show label
            self.rename_edit.hide()
            self.name_label.show()
            
            # If name is empty or unchanged, do nothing
            if not new_name or new_name == self.folder_name:
                return
                
            # Emit signal with old and new name
            self.renameDone.emit(self.folder_name, new_name)
            
            # Update internal folder name - will be reset by gallery when refreshed
            self.folder_name = new_name
            self.name_label.setText(new_name)
        except Exception as e:
            print(f"Error in _finish_rename: {e}")
            import traceback
            traceback.print_exc()

    def keyPressEvent(self, event):
        """Handle key press events for rename operation"""
        if self.editing:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self._finish_rename()
            elif event.key() == Qt.Key.Key_Escape:
                # Cancel editing
                self.editing = False
                self.rename_edit.hide()
                self.name_label.show()
        # Handle both Delete and Backspace (for Mac) for folder deletion when selected
        elif (event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace) and self.selected:
            print(f"[DEBUG] Folder Card: Delete/Backspace key pressed for folder '{self.folder_name}'")
            success = self._delete_folder()
            # Only consume the event if the folder was actually deleted
            if success:
                event.accept()
                return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right click"""
        print(f"🔍 LISTENER: Opening context menu for folder '{self.folder_name}'")
        # Create context menu using our custom class
        context_menu = ContextMenu(self)
        
        # Check if we're in a folder view by finding the gallery parent
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'current_folder'):
                gallery = parent
                break
            parent = parent.parent()
            
        # Add navigation options if we're inside a folder
        if gallery and gallery.current_folder:
            print(f"🔍 LISTENER: Context menu includes navigation options for folder '{gallery.current_folder}'")
            # Add "Up a Level" action if in a nested folder
            up_level_action = QAction("Up a Level", self)
            up_level_action.triggered.connect(lambda: gallery._on_back_to_all())
            context_menu.addAction(up_level_action)
            
            # Add "Go to Root" action
            root_action = QAction("Go to Root", self)
            root_action.triggered.connect(lambda: gallery._on_back_to_all())
            context_menu.addAction(root_action)
            
            # Add separator
            context_menu.addSeparator()
        
        # Add rename action
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self._start_rename)
        context_menu.addAction(rename_action)
        
        # Add delete action (unless it's a default folder)
        if self.folder_name not in ["General", "Development", "Business"]:
            # Use our specialized helper method for red Delete text
            context_menu.addRedDeleteAction(
                parent=self, 
                callback=lambda: self._delete_folder()
            )
        
        # Show the menu
        context_menu.exec(event.globalPos())
    
    def _delete_folder(self):
        """Delete this folder"""
        try:
            # First check if this is a default folder
            if self.folder_name in ["General", "Development", "Business"]:
                QMessageBox.warning(self, "Error", f"'{self.folder_name}' is a default folder and cannot be deleted.")
                return False
            
            # Find template_manager either from app or from parent gallery
            template_manager = None
            gallery = None
            
            # Try to get template manager from app first
            if self.app and hasattr(self.app, 'template_manager'):
                template_manager = self.app.template_manager
                
            # If no template manager from app, try to get from parent gallery
            if template_manager is None:
                # Find parent gallery
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'template_manager'):
                        template_manager = parent.template_manager
                        gallery = parent
                        break
                    parent = parent.parent()
                
            # Check if we found a template manager
            if template_manager is None:
                print(f"[ERROR] Could not find template_manager to delete folder '{self.folder_name}'")
                QMessageBox.warning(self, "Error", f"Failed to delete folder '{self.folder_name}' - template manager not found.")
                return False
            
            # Delete folder without confirmation dialog
            print(f"[DEBUG] Deleting folder: '{self.folder_name}'")
            success = template_manager.delete_folder(self.folder_name)
            
            if success:
                print(f"[DEBUG] Successfully deleted folder: '{self.folder_name}'")
                
                # If we found the gallery, use it to update the UI
                if gallery:
                    # Clear selected folder if it's this folder
                    if hasattr(gallery, 'selected_folder') and gallery.selected_folder == self.folder_name:
                        gallery.selected_folder = None
                    
                    # Refresh the gallery
                    if hasattr(gallery, 'populate_gallery'):
                        gallery.populate_gallery(force_refresh=True)
                else:
                    # Try to find gallery if we didn't get it above
                    parent = self.parent()
                    while parent:
                        if hasattr(parent, 'populate_gallery'):
                            # This is likely the gallery
                            if hasattr(parent, 'selected_folder'):
                                parent.selected_folder = None
                            parent.populate_gallery(force_refresh=True)
                            break
                        parent = parent.parent()
                
                # Show status message for success if available
                if hasattr(self.app, 'show_status_message'):
                    self.app.show_status_message(f"Folder '{self.folder_name}' deleted", "info")
                
                return True
            else:
                print(f"[ERROR] Failed to delete folder: '{self.folder_name}'")
                QMessageBox.warning(self, "Error", f"Failed to delete folder '{self.folder_name}'.")
                return False
        except Exception as e:
            print(f"[ERROR] Exception deleting folder '{self.folder_name}': {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to delete folder '{self.folder_name}' due to an exception: {str(e)}")
            return False

    def set_selected(self, selected):
        """Set the selected state of the card"""
        self.selected = selected
        self._update_styling()

    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.hover = True
        self._update_styling()
        
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.hover = False
        self._update_styling() 