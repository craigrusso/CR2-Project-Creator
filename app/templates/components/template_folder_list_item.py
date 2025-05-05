from app.constants import get_resource_path
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QApplication, QStyle, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent, QMimeData, QByteArray
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
import json

from app.ui.color_scheme_pyqt import colors
from app.templates.mime_types import TEMPLATE_NAMES_MIME_TYPE, TEMPLATE_MULTI_DRAG_MIME_TYPE, TEMPLATE_MULTI_SELECTION_MIME_TYPE

class TemplateFolderListItem(QFrame):
    # ... (existing signals)
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)
    renameRequested = pyqtSignal(str)
    renameDone = pyqtSignal(str, str)
    deleteRequested = pyqtSignal(str)

    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.app = app
        self.folder_name = folder_name
        self.hover = False
        self.selected = False
        self.is_renaming = False
        self.setAcceptDrops(True)  # Enable drops
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure list item can receive keyboard focus
        # Increase the fixed height to accommodate the larger icon
        self.setFixedHeight(44)
        
        # Create layout with better vertical centering
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 6, 10, 6)
        self.layout.setSpacing(10)
        
        # Create icon label with larger size (32x32 instead of 24x24)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        
        # Use system folder icon instead of custom drawn icon
        self._create_folder_icon(32, 32)
        
        self.layout.addWidget(self.icon_label)
        
        # Create folder name label
        self.folder_name_label = QLabel(folder_name)
        self.folder_name_label.setStyleSheet(f"color: {colors.get('text', '#FFFFFF')}; background-color: transparent;")
        # Increase font size to better match grid view (was 10)
        self.folder_name_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.layout.addWidget(self.folder_name_label, 1)  # Stretch factor
        
        # Create rename field (hidden by default)
        self.rename_edit = QLineEdit(folder_name)
        # Match the font size of the label
        self.rename_edit.setFont(QFont("Segoe UI", 11))
        self.rename_edit.setStyleSheet(f"color: {colors.get('text', '#FFFFFF')}; background-color: rgba(50, 50, 50, 0.8); border: 1px solid {colors.get('border', '#555555')};")
        self.rename_edit.editingFinished.connect(self._finish_rename)
        self.rename_edit.hide()
        self.layout.addWidget(self.rename_edit, 1)
        
        # Apply initial styling
        self._update_styling()
        
        # Set up event connections
        self.installEventFilter(self)

    def _create_folder_icon(self, width, height):
        """Create a system folder icon for list view that exactly matches the grid view macOS icons"""
        try:
            # Get standard system folder icon
            style = QApplication.style()
            icon = style.standardIcon(QStyle.SP_DirIcon)
            original_pixmap = icon.pixmap(width, height)
            
            if not original_pixmap.isNull():
                # Create a copy of the pixmap that we can modify
                pixmap = QPixmap(original_pixmap)
                
                # Create a mask from non-transparent pixels
                # This ensures we only color the actual folder shape
                mask = pixmap.createMaskFromColor(Qt.transparent, Qt.MaskOutColor)
                
                # Create painter to modify the pixmap
                painter = QPainter(pixmap)
                
                # Get the system macOS folder color from our color scheme
                # Using the exact same color key as used in grid view
                folder_color = QColor(colors.get('macos_folder_icon', '#3897F0'))
                
                # Use CompositionMode_SourceIn to preserve transparency
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), folder_color)
                painter.end()
                
                # Set the icon with our consistent color
                self.icon_label.setPixmap(pixmap)
                
                # Remove any styling that could affect appearance
                self.icon_label.setStyleSheet("background-color: transparent;")
                
                # Set fixed size to match pixmap dimensions
                self.icon_label.setFixedSize(width, height)
            else:
                print(f"ERROR (FolderListItem): Failed to get standard system folder icon pixmap.")
                # Use identical fallback as in the card implementation
                self.icon_label.setText("??")
                self.icon_label.setStyleSheet("background-color: transparent;")
        except Exception as e:
            print(f"ERROR (FolderListItem): Exception getting system icon: {e}")
            # Use identical fallback as in the card implementation
            self.icon_label.setText("SYSERR")
            self.icon_label.setStyleSheet("background-color: transparent;")

    def _update_styling(self):
        """Update styling based on state (hover, selected)"""
        # Get current state
        is_selected = self.selected
        is_hover = self.hover
        
        # Determine base background color based on row type
        if self.property("row_type") == "odd":
            bg_color = colors.get("card_bg", "#252526")
        else:
            bg_color = colors.get("bg", "#1E1E1E")
        
        # Frame styling based on state
        if is_selected:
            # Selected state
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.get('accent', '#2C4F76')};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            
            # Style text but preserve icon
            self.folder_name_label.setStyleSheet(f"color: {colors.get('highlight_text', '#FFFFFF')}; background-color: transparent;")
            
        elif is_hover:
            # Hover state
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.get('hover_bg', '#3E3E3E')};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            
            # Style text but preserve icon
            self.folder_name_label.setStyleSheet(f"color: {colors.get('text', '#FFFFFF')}; background-color: transparent;")
            
        else:
            # Normal state
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            
            # Style text but preserve icon
            self.folder_name_label.setStyleSheet(f"color: {colors.get('text', '#FFFFFF')}; background-color: transparent;")
            
        # Ensure icon label always has transparent background and no styling override
        self.icon_label.setStyleSheet("background-color: transparent;")
        
        # Process events to ensure immediate visual update
        QApplication.processEvents()

    # ... (rest of existing methods)

    # --- Drag and Drop Handling ---
    def dragEnterEvent(self, event):
        """Accept drops if they contain template names."""
        mime_data = event.mimeData()
        
        # Accept if any of our supported MIME types are present
        if (mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE) or 
            mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE) or
            mime_data.hasFormat(TEMPLATE_MULTI_DRAG_MIME_TYPE) or
            mime_data.hasText()):
            
            # Provide visual feedback with solid border
            self.hover = True
            
            # Apply drag enter styling to frame only, not labels
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.get('accent_hover', '#5A5A5A')};
                    border: 2px solid {colors.get('accent', '#FFFFFF')};
                    border-radius: 3px;
                }}
            """)
            
            # Apply text styling separately but preserve icon
            self.folder_name_label.setStyleSheet(f"color: {colors.get('highlight_text', '#FFFFFF')}; background-color: transparent;")
            
            # Ensure the icon label isn't affected
            self.icon_label.setStyleSheet("background-color: transparent;")
            
            # Accept the drag
            event.acceptProposedAction()
            
            # Log the event
            if mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE):
                try:
                    data = mime_data.data(TEMPLATE_NAMES_MIME_TYPE).data().decode('utf-8')
                    print(f"[DEBUG] DragEnter: Drag entered folder list item '{self.folder_name}' with data: {data}")
                except Exception as e:
                    print(f"[DEBUG] DragEnter: Drag entered folder '{self.folder_name}' with TEMPLATE_NAMES_MIME_TYPE (decode error: {e})")
            elif mime_data.hasText():
                print(f"[DEBUG] DragEnter: Drag entered folder list item '{self.folder_name}' with text: {mime_data.text()}")
            else:
                print(f"[DEBUG] DragEnter: Drag entered folder list item '{self.folder_name}'")
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Continue accepting the drag."""
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
        """Remove visual feedback when drag leaves."""
        self.hover = False
        self._update_styling()  # Restore normal style
        event.accept()
        
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to enter the folder, just like grid view"""
        if not self.is_renaming:
            print(f"[DEBUG] ListItem: Double-clicked folder '{self.folder_name}', emitting signal to navigate into folder")
            # Emit the doubleClicked signal to navigate into this folder
            self.doubleClicked.emit(self.folder_name)
            event.accept()
        
    def mousePressEvent(self, event):
        """Set focus to this item when clicked"""
        if event.button() == Qt.LeftButton:
            self.setFocus()
            self.clicked.emit(self.folder_name)
        super().mousePressEvent(event)

    def _finish_rename(self):
        """Finish inline renaming and apply the change"""
        try:
            self.editing = False
            new_name = self.rename_edit.text().strip()
            
            # Hide edit field, show label
            self.rename_edit.hide()
            self.folder_name_label.show()
            
            # If name is empty or unchanged, do nothing
            if not new_name or new_name == self.folder_name:
                return
                
            # Emit signal with old and new name
            self.renameDone.emit(self.folder_name, new_name)
            
            # Update internal folder name - will be reset by gallery when refreshed
            self.folder_name = new_name
            self.folder_name_label.setText(new_name)
        except Exception as e:
            print(f"Error in _finish_rename: {e}")
            import traceback
            traceback.print_exc()

    def dropEvent(self, event):
        """Handle drop event"""
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
                        print(f"[DEBUG] ListItem: Successfully moved template")
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
                        print(f"[DEBUG] ListItem: Failed to move template")
            
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
        self.hover = False
        self._update_styling()
        
    def _process_template_names(self, template_names, event):
        """Process a list of template names for the drop event"""
        # Ensure we have a valid template_manager
        if not self.app or not hasattr(self.app, 'template_manager'):
            print("[ERROR] Could not find template_manager")
            event.ignore()
            return
            
        template_manager = self.app.template_manager
        
        # Process all templates
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
        
        # Show success message if available
        if success_count > 0:
            print(f"Successfully moved {success_count}/{len(processed_names)} templates to '{self.folder_name}'")
            
            # Show success message in status bar
            if hasattr(self.app, 'show_status_message'):
                self.app.show_status_message(f"Added {success_count} templates to folder '{self.folder_name}'", "info")
            
            # Set drop action and accept
            event.setDropAction(Qt.MoveAction)
            event.accept()
            
            # Refresh the gallery to show the updated contents
            gallery = self._find_gallery()
            if gallery and hasattr(gallery, 'populate_gallery'):
                gallery.populate_gallery(force_refresh=True)
        else:
            print(f"[ERROR] Failed to move any templates.")
            event.ignore()
            
    def _find_gallery(self):
        """Helper method to find the parent gallery"""
        if hasattr(self.app, 'template_gallery'):
            return self.app.template_gallery
            
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'populate_gallery'):
                gallery = parent
                break
            parent = parent.parent()
        return gallery
    # --- End Drag and Drop --- 

    def keyPressEvent(self, event):
        """Handle key press events for rename operation and deletion"""
        if self.is_renaming:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # Finish renaming
                self._finish_rename()
            elif event.key() == Qt.Key_Escape:
                # Cancel renaming
                self.is_renaming = False
                # Hide rename field, show original label
                if hasattr(self, 'rename_edit'):
                    self.rename_edit.hide()
                if hasattr(self, 'title'):
                    self.title.show()
        # Handle both Delete and Backspace (for Mac) for folder deletion when selected
        elif (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            print(f"[DEBUG] Folder List Item: Delete/Backspace key pressed for folder '{self.folder_name}'")
            success = self._delete_folder()
            # Consume the event
            event.accept()
            return
        
        super().keyPressEvent(event) 

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