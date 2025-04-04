# template_folder_card.py

from PyQt5.QtWidgets import QFrame, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QMenu, QAction, QWidget, QApplication, QStyle
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QEvent, QPoint, QRect, QRectF
from PyQt5.QtGui import QFont, QIcon, QPixmap, QCursor, QColor, QFontMetrics, QPainter, QBrush, QPen, QPainterPath, QLinearGradient
from .utils import SYSTEM_FONT
from .common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED
from app.ui.color_scheme_pyqt import colors, MENU_DESTRUCTIVE_ITEM_STYLE, DELETE_TEXT_STYLE
from app.templates.components.menu_actions import ContextMenu
from app.constants import get_resource_path
import os

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

        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumSize(120, 130)  # Increase minimum height for text
        self.setCursor(Qt.PointingHandCursor)

        # Layouts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)  # Increase spacing between icon and text

        # Icon Label (3D macOS-style Folder Icon)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # --- MODIFICATION START: Use System Icon --- 
        # Get the standard system directory icon
        try:
            style = QApplication.style()
            icon = style.standardIcon(QStyle.SP_DirIcon) 
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
        
        self.layout.addWidget(self.icon_label, 0, Qt.AlignCenter)  # Force center alignment

        # Folder Name Label/LineEdit
        self.name_container = QWidget()
        self.name_container.setObjectName("folderNameContainer")
        # Make container background transparent
        self.name_container.setStyleSheet("background-color: transparent;")
        self.name_layout = QHBoxLayout(self.name_container)
        self.name_layout.setContentsMargins(0, 0, 0, 0)
        self.name_layout.setSpacing(0)

        self.name_label = QLabel(self.folder_name)
        self.name_label.setAlignment(Qt.AlignCenter)
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
        self.rename_edit.setAlignment(Qt.AlignCenter)
        self.rename_edit.setStyleSheet(f"color: {colors.get('text', '#FFFFFF')}; background-color: {colors.get('input_bg', '#444444')}; border: 1px solid {colors.get('highlight_bg', '#5A5A5A')}; border-radius: 3px;")
        self.rename_edit.editingFinished.connect(self._finish_rename)
        self.rename_edit.returnPressed.connect(self._finish_rename) # Also finish on Enter
        self.rename_edit.setVisible(False)
        self.name_layout.addWidget(self.rename_edit)

        self.layout.addWidget(self.name_container, 0, Qt.AlignCenter)  # Force center alignment

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
            icon = style.standardIcon(QStyle.SP_DirIcon)
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
        if obj == self.name_label and event.type() == QEvent.MouseButtonDblClick:
            if not self.editing:
                self._start_rename()
                return True
        return super().eventFilter(obj, event)

    def mouseDoubleClickEvent(self, event):
        if not self.editing:
            self.doubleClicked.emit(self.folder_name)

    def dragEnterEvent(self, event):
        """Accept drops if they contain template names."""
        if event.mimeData().hasFormat('application/x-echelon-template-names'):
            event.setDropAction(Qt.MoveAction)
            event.accept()
            # Add visual feedback (e.g., highlight)
            self.setStyleSheet(f"background-color: {colors.get('highlight_bg', '#4A90E2')}; border-radius: 6px; border: 1px solid {colors.get('highlight_border', '#FFFFFF')};")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Remove visual feedback when drag leaves."""
        self._update_styling() # Restore normal style
        event.accept()

    def dropEvent(self, event):
        """Handle the drop event to move templates."""
        if event.mimeData().hasFormat('application/x-echelon-template-names'):
            encoded_data = event.mimeData().data('application/x-echelon-template-names')
            try:
                template_names_str = bytes(encoded_data).decode('utf-8')
                template_names = template_names_str.split('\n')
                template_names = [name for name in template_names if name] # Remove empty strings
                
                print(f"[DEBUG] FolderCard '{self.folder_name}': Dropped {len(template_names)} templates: {template_names}")

                # Call the gallery/app handler to move the templates
                gallery = self._find_gallery()
                # Ensure gallery and template_manager exist
                template_manager = None
                if gallery and hasattr(gallery, 'template_manager'):
                    template_manager = gallery.template_manager
                elif gallery and hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
                    template_manager = gallery.app.template_manager
                
                if template_manager and hasattr(template_manager, 'move_template_to_folder'):
                    success_count = 0
                    for template_name in template_names:
                        try:
                            # Call the move function for each template
                            success = template_manager.move_template_to_folder(template_name, self.folder_name)
                            if success:
                                success_count += 1
                            else:
                                print(f"[WARNING] Failed to move template '{template_name}' to folder '{self.folder_name}'")
                        except Exception as move_error:
                            print(f"[ERROR] Error moving template '{template_name}': {move_error}")

                    if success_count > 0:
                        print(f"Successfully moved {success_count}/{len(template_names)} templates to {self.folder_name}")
                        event.setDropAction(Qt.MoveAction)
                        event.accept()
                        # Refresh the gallery view after move
                        if hasattr(gallery, 'populate_gallery'):
                            gallery.populate_gallery(force_refresh=True)
                    else:
                        print(f"[ERROR] Failed to move any templates.")
                        event.ignore()
                else:
                    print("[ERROR] Could not find template_manager or move_template_to_folder method.")
                    event.ignore()

            except Exception as e:
                print(f"[ERROR] Failed to process drop data: {e}")
                event.ignore()
        else:
            event.ignore()
        
        self._update_styling() # Restore normal style

    def _find_gallery(self):
        """Helper to find the parent TemplateGallery instance."""
        parent = self.parent()
        while parent:
            if isinstance(parent, QWidget) and hasattr(parent, 'multi_selected_templates'): # Check for a known gallery attribute
                return parent
            parent = parent.parent()
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.editing:
            self.click_timer.start()

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
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self._finish_rename()
            elif event.key() == Qt.Key_Escape:
                # Cancel editing
                self.editing = False
                self.rename_edit.hide()
                self.name_label.show()
        # Handle both Delete and Backspace (for Mac) for folder deletion when selected
        elif (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            self._delete_folder()
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
        context_menu.exec_(event.globalPos())
    
    def _delete_folder(self):
        """Delete this folder"""
        if not self.app:
            return
            
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{self.folder_name}'?\n"
            "Templates in this folder will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete folder
            success = self.app.template_manager.delete_folder(self.folder_name)
            
            if success:
                # Refresh the gallery
                if hasattr(self.app, 'template_gallery') and self.app.template_gallery:
                    self.app.template_gallery.populate_gallery(force_refresh=True)
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete folder '{self.folder_name}'.")

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

class TemplateFolderListItem(QFrame):
    """Template folder list item widget for displaying a folder in list view"""
    
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)
    renameRequested = pyqtSignal(str)
    renameDone = pyqtSignal(str, str)  # Signal for when renaming is done (old_name, new_name)
    
    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        self.editing = False
        
        # Setup styling
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(36)  # Fixed height for compact list view
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptDrops(True)  # Accept template drops
        
        # Click handling
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.setInterval(250)
        self.click_timer.timeout.connect(self._handle_single_click)
        self.click_pending = False
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        
        # Folder icon - use the flat style for consistency
        self.icon_label = QLabel()
        self._create_folder_icon(24, 24)  # Create a smaller flat icon for list view
        self.icon_label.setFixedSize(24, 24)
        self.layout.addWidget(self.icon_label)
        
        # Folder name
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(SYSTEM_FONT, 12))
        self.title.setCursor(Qt.IBeamCursor)  # Change cursor to indicate text editability
        self.title.setToolTip("Double-click to rename")
        self.layout.addWidget(self.title, 1)  # Give it stretch factor
        
        # Inline edit field
        self.name_edit = QLineEdit(folder_name)
        self.name_edit.setFont(QFont(SYSTEM_FONT, 12))
        self.name_edit.editingFinished.connect(self._finish_rename)
        self.name_edit.hide()  # Hide by default
        self.layout.addWidget(self.name_edit, 1)  # Same stretch as title
        
        # Set alternating row color property (will be set by parent)
        self.setProperty("row_type", "even")  # Default to even
        
        # Install event filters
        self.installEventFilter(self)
        self.title.installEventFilter(self)
        
        self._update_styling()
    
    def _create_folder_icon(self, width, height):
        """Create a simple flat folder icon for list view (non-3D)"""
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate folder dimensions
        folder_width = width * 0.75
        folder_height = height * 0.65
        x = (width - folder_width) / 2
        y = (height - folder_height) / 2 + (height * 0.05)
        
        # Create folder path
        folder_path = QPainterPath()
        folder_path.addRoundedRect(QRectF(x, y, folder_width, folder_height), 3, 3)
        
        # Add tab to folder
        tab_width = folder_width * 0.4
        tab_height = folder_height * 0.2
        tab_x = x + folder_width * 0.05
        tab_y = y - tab_height * 0.7
        
        # Create tab path
        tab_path = QPainterPath()
        tab_path.addRoundedRect(QRectF(tab_x, tab_y, tab_width, tab_height), 2, 2)
        
        # Folder color - light blue
        folder_color = QColor(100, 150, 240)
        
        # Fill the folder
        painter.fillPath(folder_path, folder_color)
        painter.fillPath(tab_path, folder_color)
        
        # Add outline
        outline_pen = QPen(QColor(80, 120, 200), 1)
        painter.setPen(outline_pen)
        painter.drawPath(folder_path)
        painter.drawPath(tab_path)
        
        painter.end()
        self.icon_label.setPixmap(pixmap)
    
    def _handle_single_click(self):
        """Handle single click event"""
        if not self.editing:
            self.clicked.emit(self.folder_name)
    
    def _update_styling(self):
        """Update the styling based on hover and selection state"""
        # First get the base background color based on row type
        if self.property("row_type") == "odd":
            bg_color = colors["card_bg"]  # Darker for odd rows
        else:
            bg_color = colors["bg"]  # Lighter for even rows
        
        # Base styles
        base_style = f"background-color: {bg_color}; border: none; border-radius: 0px;"
        hover_style = f"background-color: {colors['hover_bg']}; border: none; border-radius: 0px;"
        selected_style = f"background-color: {colors['accent']}; border: none; border-radius: 0px;"
        
        # Text styles
        normal_text = f"color: {colors['text']}; background: transparent;"
        highlight_text = f"color: {colors['highlight_text']}; background: transparent;"
        
        # Icon styles - use colors.get('folder_icon') instead of hardcoded "goldenrod"
        folder_icon_color = colors.get('folder_icon', '#E8BA36')  # Get folder icon color from theme
        normal_icon = f"color: {folder_icon_color}; background: transparent;"
        
        # Apply appropriate styles based on state
        if self.selected:
            # Selected style
            self.setStyleSheet(f"QFrame {{ {selected_style} }}")
            self.icon_label.setStyleSheet(highlight_text)
            self.title.setStyleSheet(highlight_text)
        elif self.hover:
            # Hover style
            self.setStyleSheet(f"QFrame {{ {hover_style} }}")
            self.icon_label.setStyleSheet(normal_icon)
            self.title.setStyleSheet(normal_text)
        else:
            # Normal style with alternating row colors
            self.setStyleSheet(f"QFrame {{ {base_style} }}")
            self.icon_label.setStyleSheet(normal_icon)
            self.title.setStyleSheet(normal_text)
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.hover = True
        self._update_styling()
        
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.hover = False
        self._update_styling()
    
    def eventFilter(self, obj, event):
        """Handle events for this widget and its children"""
        if obj == self.title and event.type() == QEvent.MouseButtonDblClick:
            if not self.editing:
                self._start_rename()
                return True
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton and not self.editing:
            self.click_timer.start()
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click event"""
        if not self.editing:
            self.doubleClicked.emit(self.folder_name)
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/x-template-multi-selection"):
            self.hover = True
            self._update_styling()
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.hover = False
        self._update_styling()
    
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasFormat('application/x-echelon-template-names'):
            encoded_data = event.mimeData().data('application/x-echelon-template-names')
            try:
                template_names_str = bytes(encoded_data).decode('utf-8')
                template_names = template_names_str.split('\n')
                template_names = [name for name in template_names if name] # Remove empty strings
                
                print(f"[DEBUG] FolderListItem '{self.folder_name}': Dropped {len(template_names)} templates: {template_names}")

                # Find the template manager via app reference
                if self.app and hasattr(self.app, 'template_manager'):
                    template_manager = self.app.template_manager
                    
                    success_count = 0
                    for template_name in template_names:
                        try:
                            # Call the move function for each template
                            success = template_manager.move_template_to_folder(template_name, self.folder_name)
                            if success:
                                success_count += 1
                            else:
                                print(f"[WARNING] Failed to move template '{template_name}' to folder '{self.folder_name}'")
                        except Exception as move_error:
                            print(f"[ERROR] Error moving template '{template_name}': {move_error}")

                    if success_count > 0:
                        print(f"Successfully moved {success_count}/{len(template_names)} templates to {self.folder_name}")
                        event.setDropAction(Qt.MoveAction)
                        event.accept()
                        # Refresh the gallery view after move
                        if hasattr(self.app, 'template_gallery'):
                            self.app.template_gallery.populate_gallery(force_refresh=True)
                    else:
                        print(f"[ERROR] Failed to move any templates.")
                        event.ignore()
                else:
                    print("[ERROR] Could not find template_manager method.")
                    event.ignore()

            except Exception as e:
                print(f"[ERROR] Failed to process drop data: {e}")
                event.ignore()
        else:
            # Fallback to check other MIME types
            mime_data = event.mimeData()
            template_names = []
            
            # Check for text format as fallback
            if mime_data.hasText():
                text_data = mime_data.text()
                # Check if this contains multiple templates (newline separated)
                if '\n' in text_data:
                    template_names = text_data.strip().split('\n')
                    print(f"[DEBUG] FolderListItem: Detected newline-separated drop with {len(template_names)} templates")
                else:
                    # Single template drop
                    template_name = text_data
                    template_names = [template_name]
                    print(f"[DEBUG] FolderListItem: Detected single template drop: '{template_name}'")
                
                # Process all templates
                if template_names and self.app and hasattr(self.app, 'template_manager'):
                    success_count = 0
                    for template_name in template_names:
                        if template_name and template_name.strip():  # Skip empty names
                            try:
                                success = self.app.template_manager.move_template_to_folder(template_name, self.folder_name)
                                if success:
                                    success_count += 1
                            except Exception as e:
                                print(f"Error moving template '{template_name}': {e}")
                    
                    # Show success message if available
                    if success_count > 0:
                        print(f"Successfully moved {success_count}/{len(template_names)} templates to '{self.folder_name}'")
                        event.setDropAction(Qt.MoveAction)
                        event.accept()
                        
                        # Refresh the gallery to show the updated contents
                        if hasattr(self.app, 'template_gallery'):
                            self.app.template_gallery.populate_gallery(force_refresh=True)
                        return
            
            event.ignore()
        
        self.hover = False
        self._update_styling()
    
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
            self.title.hide()
            self.name_edit.setText(self.folder_name)
            self.name_edit.show()
            self.name_edit.setFocus()
            self.name_edit.selectAll()
            
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
            new_name = self.name_edit.text().strip()
            
            # Hide edit field, show label
            self.name_edit.hide()
            self.title.show()
            
            # If name is empty or unchanged, do nothing
            if not new_name or new_name == self.folder_name:
                return
                
            # Emit signal with old and new name
            self.renameDone.emit(self.folder_name, new_name)
            
            # Update internal folder name - will be reset by gallery when refreshed
            self.folder_name = new_name
            self.title.setText(new_name)
        except Exception as e:
            print(f"Error in _finish_rename: {e}")
            import traceback
            traceback.print_exc()
    
    def keyPressEvent(self, event):
        """Handle key press events for rename operation"""
        if self.editing:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self._finish_rename()
            elif event.key() == Qt.Key_Escape:
                # Cancel editing
                self.editing = False
                self.name_edit.hide()
                self.title.show()
        # Handle both Delete and Backspace (for Mac) for folder deletion when selected
        elif (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            self._delete_folder()
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
        context_menu.exec_(event.globalPos())
    
    def _delete_folder(self):
        """Delete this folder"""
        if not self.app:
            return
            
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{self.folder_name}'?\n"
            "Templates in this folder will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete folder
            success = self.app.template_manager.delete_folder(self.folder_name)
            
            if success:
                # Refresh the gallery
                if hasattr(self.app, 'template_gallery') and self.app.template_gallery:
                    self.app.template_gallery.populate_gallery(force_refresh=True)
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete folder '{self.folder_name}'.")

    def set_selected(self, selected):
        """Set the selected state of the list item"""
        self.selected = selected
        self._update_styling()