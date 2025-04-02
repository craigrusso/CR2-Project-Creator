# template_folder_card.py

from PyQt5.QtWidgets import QFrame, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QMenu, QAction
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QEvent
from PyQt5.QtGui import QFont, QIcon, QPixmap, QCursor, QColor
from app.ui.color_scheme_pyqt import colors, MENU_DESTRUCTIVE_ITEM_STYLE, DELETE_TEXT_STYLE
from .utils import SYSTEM_FONT
import os
from app.templates.components.menu_actions import ContextMenu

class TemplateFolderCard(QFrame):
    clicked = pyqtSignal(str)
    doubleClicked = pyqtSignal(str)
    renameRequested = pyqtSignal(str)
    renameDone = pyqtSignal(str, str)

    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        self.editing = False

        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.setInterval(250)
        self.click_timer.timeout.connect(self._handle_single_click)
        self.click_pending = False

        self.setFrameShape(QFrame.NoFrame)
        self.setFixedSize(120, 120)  # This size is for the whole card
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptDrops(True)

        # Layouts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 0)
        self.layout.setSpacing(0)

        # Icon - create with fixed size that can be adjusted
        self.icon_layout = QHBoxLayout()
        self.icon_layout.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel("📁")
        self.icon_label.setFont(QFont(SYSTEM_FONT, 40))
        self.icon_label.setFixedSize(64, 64)  # Default icon size at 100% scale
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_layout.addWidget(self.icon_label)
        self.layout.addLayout(self.icon_layout)

        # Title label
        self.title = QLabel(folder_name)
        self.title.setFont(QFont(SYSTEM_FONT, 12))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.layout.addWidget(self.title)

        # Apply base styling with transparent background
        self.setStyleSheet("background: transparent; border: none;")
        
        # Inline edit field
        self.name_edit = QLineEdit(folder_name)
        self.name_edit.setFont(QFont(SYSTEM_FONT, 12))
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.editingFinished.connect(self._finish_rename)
        self.name_edit.hide()
        self.layout.addWidget(self.name_edit)

        self.installEventFilter(self)
        self.title.installEventFilter(self)

        self._update_styling()

    def _handle_single_click(self):
        if not self.editing:
            self.clicked.emit(self.folder_name)

    def _update_styling(self):
        """Update the styling based on hover and selection state"""
        # Base styles without gradients or complex effects
        base_style = "background-color: transparent; border-radius: 6px;"
        hover_style = f"background-color: {colors['hover_bg']}; border-radius: 6px;"
        selected_style = f"background-color: {colors['accent']}; border-radius: 6px;"
        
        # Text styles
        normal_text = f"color: {colors['text']}; background: transparent;"
        highlight_text = f"color: {colors['highlight_text']}; background: transparent;"
        
        # Apply appropriate styles based on state
        if self.selected:
            # Selected style
            self.setStyleSheet(f"QFrame {{ {selected_style} }}")
            self.icon_label.setStyleSheet(highlight_text)
            self.title.setStyleSheet(highlight_text)
        elif self.hover:
            # Hover style
            self.setStyleSheet(f"QFrame {{ {hover_style} }}")
            self.icon_label.setStyleSheet(normal_text)
            self.title.setStyleSheet(normal_text)
        else:
            # Normal style
            self.setStyleSheet(f"QFrame {{ {base_style} }}")
            self.icon_label.setStyleSheet(normal_text)
            self.title.setStyleSheet(normal_text)

    def resize_icon(self, scale_percent):
        """Resize just the icon based on scale percentage"""
        # Base icon size at 100%
        base_size = 64
        
        # Get available space in the card (accounting for minimal margins all around)
        available_height = self.height() - 5  # Reserve only 5px for title and margins
        available_width = self.width() - 5  # Reserve only 5px for horizontal margins
        max_icon_size = min(available_height, available_width)  # Use the smaller dimension
        
        # Calculate new size based on scale percentage, but cap it to available space
        new_size = min(int(base_size * scale_percent / 100), max_icon_size)
        
        # Update icon size
        self.icon_label.setFixedSize(new_size, new_size)
        
        # Adjust font size based on the actual icon size
        font_scale = new_size / base_size
        font_size = int(40 * font_scale)
        font_size = max(18, min(font_size, 60))  # Keep font size between 18 and 60
        self.icon_label.setFont(QFont(SYSTEM_FONT, font_size))

    def eventFilter(self, obj, event):
        if obj == self.title and event.type() == QEvent.MouseButtonDblClick:
            if not self.editing:
                self._start_rename()
                return True
        return super().eventFilter(obj, event)

    def mouseDoubleClickEvent(self, event):
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
        mime_data = event.mimeData()
        template_names = []
        
        # Check for multi-selection MIME format first
        if mime_data.hasFormat("application/x-template-multi-selection"):
            try:
                # Get JSON data with multi-selected templates
                multi_data = mime_data.data("application/x-template-multi-selection").data()
                import json
                template_names = json.loads(multi_data.decode())
                print(f"[DEBUG] FolderListItem: Processing multi-selection drop with {len(template_names)} templates")
            except Exception as e:
                print(f"Error processing multi-selection drop: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback to text-based format
        elif mime_data.hasText():
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
        if template_names:
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
            if success_count > 0 and hasattr(self.app, 'show_status_message'):
                if success_count == 1:
                    self.app.show_status_message(f"Moved template to '{self.folder_name}'", "success")
                else:
                    self.app.show_status_message(f"Moved {success_count} templates to '{self.folder_name}'", "success")
            
            event.acceptProposedAction()
            self.hover = False
            self._update_styling()
            
            # Refresh the gallery to show the updated contents
            if hasattr(self.app, 'template_gallery') and self.app.template_gallery:
                self.app.template_gallery.populate_gallery(force_refresh=True)
        else:
            event.ignore()

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
        
        # Folder icon
        self.icon_label = QLabel("📁")
        self.icon_label.setFont(QFont(SYSTEM_FONT, 18))
        self.icon_label.setFixedSize(24, 24)  # Fixed size for list view
        self.icon_label.setAlignment(Qt.AlignCenter)
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
        
        # Icon styles
        normal_icon = "color: goldenrod; background: transparent;"
        
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
        mime_data = event.mimeData()
        template_names = []
        
        # Check for multi-selection MIME format first
        if mime_data.hasFormat("application/x-template-multi-selection"):
            try:
                # Get JSON data with multi-selected templates
                multi_data = mime_data.data("application/x-template-multi-selection").data()
                import json
                template_names = json.loads(multi_data.decode())
                print(f"[DEBUG] FolderListItem: Processing multi-selection drop with {len(template_names)} templates")
            except Exception as e:
                print(f"Error processing multi-selection drop: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback to text-based format
        elif mime_data.hasText():
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
        if template_names:
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
            if success_count > 0 and hasattr(self.app, 'show_status_message'):
                if success_count == 1:
                    self.app.show_status_message(f"Moved template to '{self.folder_name}'", "success")
                else:
                    self.app.show_status_message(f"Moved {success_count} templates to '{self.folder_name}'", "success")
            
            event.acceptProposedAction()
            self.hover = False
            self._update_styling()
            
            # Refresh the gallery to show the updated contents
            if hasattr(self.app, 'template_gallery') and self.app.template_gallery:
                self.app.template_gallery.populate_gallery(force_refresh=True)
        else:
            event.ignore()
    
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