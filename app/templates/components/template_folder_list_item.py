from app.constants import get_resource_path
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent, QMimeData, QByteArray
from PyQt5.QtGui import QFont, QIcon, QPixmap
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
        self.setFixedHeight(40)
        # ... (rest of __init__)

    # ... (existing methods)

    # --- Drag and Drop Handling ---
    def dragEnterEvent(self, event):
        """Accept drops if they contain template names."""
        mime_data = event.mimeData()
        
        # Accept if any of our supported MIME types are present
        if (mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE) or 
            mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE) or
            mime_data.hasFormat(TEMPLATE_MULTI_DRAG_MIME_TYPE) or
            mime_data.hasText()):
            
            # Provide visual feedback with solid border (was dashed)
            self.hover = True
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.get('accent_hover', '#5A5A5A')};
                    border: 2px solid {colors.get('accent', '#FFFFFF')};
                    border-radius: 3px;
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