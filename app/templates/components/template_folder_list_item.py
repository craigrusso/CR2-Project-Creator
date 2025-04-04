from app.constants import get_resource_path

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
        \"\"\"Accept drops if they contain template names.\"\"\"
        if event.mimeData().hasFormat('application/x-echelon-template-names'):
            event.setDropAction(Qt.MoveAction)
            event.accept()
            self.setStyleSheet(f\"background-color: {colors.get('highlight_bg', '#4A90E2')}; border: 1px solid {colors.get('highlight_border', '#FFFFFF')}; border-radius: 3px;\")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        \"\"\"Remove visual feedback when drag leaves.\"\"\"
        self._update_styling() # Restore normal style
        event.accept()

    def dropEvent(self, event):
        \"\"\"Handle the drop event to move templates.\"\"\"
        if event.mimeData().hasFormat('application/x-echelon-template-names'):
            encoded_data = event.mimeData().data('application/x-echelon-template-names')
            try:
                template_names_str = bytes(encoded_data).decode('utf-8')
                template_names = template_names_str.split('\n')
                template_names = [name for name in template_names if name]
                
                print(f\"[DEBUG] FolderListItem '{self.folder_name}': Dropped {len(template_names)} templates: {template_names}\")

                gallery = self._find_gallery()
                if gallery and hasattr(gallery, 'app') and gallery.app and hasattr(gallery.app, 'move_templates_to_folder'):
                    # Use the app-level function (assuming it exists)
                    success = gallery.app.move_templates_to_folder(template_names, self.folder_name)
                    if success:
                         print(f\"Successfully moved templates to {self.folder_name}\")
                         event.setDropAction(Qt.MoveAction)
                         event.accept()
                         if hasattr(gallery, 'populate_gallery'):
                             gallery.populate_gallery(force_refresh=True)
                    else:
                         print(\"[ERROR] Failed to move templates via app method.\")
                         event.ignore()
                else:
                     print(\"[ERROR] Could not find gallery or app method to move templates.\")
                     event.ignore()

            except Exception as e:
                print(f\"[ERROR] Failed to process drop data: {e}\")
                event.ignore()
        else:
            event.ignore()
        
        self._update_styling() # Restore normal style

    def _find_gallery(self):
        \"\"\"Helper to find the parent TemplateGallery instance.\"\"\"
        parent = self.parent()
        while parent:
            if isinstance(parent, QWidget) and hasattr(parent, 'multi_selected_templates'):
                return parent
            if hasattr(parent, 'parent') and callable(parent.parent):
                 parent = parent.parent()
            else:
                 parent = None
        print(\"Warning: Could not find gallery parent for FolderListItem\")
        return None
    # --- End Drag and Drop --- 