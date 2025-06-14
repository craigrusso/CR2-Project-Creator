#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Context Menu Operations Module
Handles context menu creation and management for tree items
"""

from PyQt6.QtWidgets import QMenu, QDialog, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor


class ContextMenuOperations:
    """Handles context menu creation and management"""
    
    def __init__(self, tree_widget=None, editor=None):
        """Initialize context menu operations handler"""
        self.tree_widget = tree_widget
        self.editor = editor
        self.current_context_item = None
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        print(f"DEBUG: ContextMenuOperations.set_tree_widget called with: {tree_widget}")
        self.tree_widget = tree_widget
        print(f"DEBUG: ContextMenuOperations tree_widget set to: {self.tree_widget}")
        
    def set_editor(self, editor):
        """Set the editor reference"""
        print(f"DEBUG: ContextMenuOperations.set_editor called with: {editor}")
        self.editor = editor

    def create_context_menu(self, position):
        """Create and show context menu"""
        print(f"DEBUG: create_context_menu called with position {position}")
        
        if not self.tree_widget:
            print("DEBUG: create_context_menu - no tree widget available")
            return
        
        # Check if tree_widget is still valid (not deleted)
        try:
            # Try to access the tree widget to verify it's still valid
            if not hasattr(self.tree_widget, 'itemAt'):
                print("DEBUG: create_context_menu - tree widget is invalid")
                return
        except (RuntimeError, AttributeError):
            print("DEBUG: create_context_menu - tree widget has been deleted")
            return
        
        print("DEBUG: create_context_menu - tree widget available, creating context menu")
        
        # Get selected items and item at position
        try:
            selected_items = self.tree_widget.selectedItems()
            item_at_position = self.tree_widget.itemAt(position)
            
            # If clicked item is not in selection, select just that item
            if item_at_position and item_at_position not in selected_items:
                self.tree_widget.setCurrentItem(item_at_position)
                selected_items = [item_at_position]
            
            # Use the clicked item or first selected item as context
            self.current_context_item = item_at_position or (selected_items[0] if selected_items else None)
            
        except (RuntimeError, AttributeError):
            print("DEBUG: create_context_menu - error getting items")
            return
        
        print(f"DEBUG: Selected items count: {len(selected_items)}")
        
        # Create menu with error handling
        try:
            menu = QMenu(self.tree_widget)
        except (RuntimeError, AttributeError):
            print("DEBUG: Failed to create menu - tree widget invalid")
            return
        
        # Style the menu
        self._style_context_menu(menu)
        
        # Build menu content
        self._build_menu_content(menu, selected_items)
        
        # Show menu if it has actions
        if not menu.isEmpty():
            try:
                if self.tree_widget and hasattr(self.tree_widget, 'mapToGlobal'):
                    global_pos = self.tree_widget.mapToGlobal(position)
                    print(f"DEBUG: Executing context menu at global position {global_pos}")
                    menu.exec(global_pos)
                else:
                    print("DEBUG: Tree widget invalid during menu execution")
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error executing context menu: {e}")
            finally:
                # Always clean up the menu
                try:
                    menu.deleteLater()
                except:
                    pass
        else:
            print("DEBUG: Context menu is empty, not showing")
            try:
                menu.deleteLater()
            except:
                pass

    def _style_context_menu(self, menu):
        """Apply styling to the context menu"""
        try:
            from app.ui.color_scheme_pyqt import APP_COLORS
            colors = APP_COLORS
            
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 5px 15px;
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: {colors['highlight_bg']};
                    color: {colors['highlight_text']};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {colors['border']};
                    margin: 5px 2px;
                }}
            """)
        except ImportError:
            # Fallback if color scheme not available
            pass

    def _build_menu_content(self, menu, selected_items):
        """Build the content of the context menu"""
        # Add basic actions first
        add_file_action = menu.addAction("Add File")
        add_file_action.triggered.connect(lambda: self.editor.add_file() if hasattr(self.editor, 'add_file') else None)
        
        add_folder_action = menu.addAction("Add Folder")
        add_folder_action.triggered.connect(lambda: self.editor.add_folder() if hasattr(self.editor, 'add_folder') else None)
        
        if selected_items:
            try:
                menu.addSeparator()
                
                # Multi-selection vs single selection actions
                if len(selected_items) == 1:
                    item = selected_items[0]
                    # Single item actions
                    rename_action = menu.addAction("Rename")
                    rename_action.triggered.connect(lambda: self.tree_widget.editItem(item, 0) if self.tree_widget else None)
                
                # Delete action (works for single or multiple)
                delete_text = f"Delete {len(selected_items)} items" if len(selected_items) > 1 else "Delete"
                delete_action = menu.addAction(delete_text)
                delete_action.triggered.connect(lambda: self._delete_selected_items(selected_items))
                
                # Categorize selected items
                file_items, folder_items = self._categorize_items(selected_items)
                
                # Handle folder-specific actions
                if folder_items and len(selected_items) == 1:
                    menu.addSeparator()
                    self._add_folder_context_actions(menu, folder_items[0])
                
                # Handle file-specific actions
                if file_items:
                    self._add_file_context_actions(menu, file_items)
                    
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error building context menu for items: {e}")

    def _categorize_items(self, selected_items):
        """Categorize selected items into files and folders"""
        file_items = []
        folder_items = []
        
        for item in selected_items:
            try:
                item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                if isinstance(item_data, dict):
                    if item_data.get('type') == 'file':
                        file_items.append(item)
                    elif item_data.get('type') == 'folder':
                        folder_items.append(item)
            except (RuntimeError, AttributeError):
                continue
                
        return file_items, folder_items

    def _add_file_context_actions(self, menu, file_items):
        """Add file-specific context menu actions"""
        menu.addSeparator()
        
        if len(file_items) == 1:
            # Single file - original actions
            item_data = file_items[0].data(0, Qt.ItemDataRole.UserRole) or {}
            action_text = "Revert to Original Name" if item_data.get('rename_flag') or item_data.get('uses_project_name') else "Use Project Name"
            use_project_name_action = menu.addAction(action_text)
            use_project_name_action.triggered.connect(lambda: self.editor._toggle_project_name_for_file(file_items[0]) if hasattr(self.editor, '_toggle_project_name_for_file') else None)
            
            # Versioning menu for single file
            versioning_menu = menu.addMenu("Versioning")
            date_action = versioning_menu.addAction("Date Sequences...")
            date_action.triggered.connect(lambda: self._configure_date_sequences(file_items[0]))
            
            patterns_action = menu.addAction("Custom Naming Patterns...")
            patterns_action.triggered.connect(lambda: self._configure_custom_patterns(file_items[0]))
        else:
            # Multiple files - bulk operations
            bulk_menu = menu.addMenu(f"Bulk Operations ({len(file_items)} files)")
            
            # Bulk project name operations
            prepend_bulk_action = bulk_menu.addAction("Prepend Project Name to All")
            prepend_bulk_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'prepend'))
            
            append_bulk_action = bulk_menu.addAction("Append Project Name to All")
            append_bulk_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'append'))
            
            replace_bulk_action = bulk_menu.addAction("Replace All with Project Name")
            replace_bulk_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'replace'))
            
            bulk_menu.addSeparator()
            
            revert_bulk_action = bulk_menu.addAction("Revert All to Original Names")
            revert_bulk_action.triggered.connect(lambda: self._bulk_revert_to_original(file_items))
        
        # Project name mode actions (available for single or multiple)
        menu.addSeparator()
        project_menu = menu.addMenu("Project Name")
        
        prepend_action = project_menu.addAction("Prepend Project Name")
        prepend_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'prepend'))
        
        append_action = project_menu.addAction("Append Project Name")
        append_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'append'))
        
        replace_action = project_menu.addAction("Replace with Project Name")
        replace_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'replace'))

    def _add_folder_context_actions(self, menu, folder_item):
        """Add folder-specific context menu actions"""
        # Add folder-specific actions
        expand_action = menu.addAction("Expand All")
        expand_action.triggered.connect(lambda: self.tree_widget.expandItem(folder_item) if self.tree_widget else None)
        
        collapse_action = menu.addAction("Collapse All")
        collapse_action.triggered.connect(lambda: self.tree_widget.collapseItem(folder_item) if self.tree_widget else None)

    def _delete_selected_items(self, items):
        """Delete selected items - delegates to editor"""
        if self.editor and hasattr(self.editor, 'delete_selected'):
            self.editor.delete_selected()
        elif self.tree_widget:
            # Fallback: remove items directly from tree
            for item in items:
                try:
                    parent = item.parent()
                    if parent:
                        parent.removeChild(item)
                    else:
                        index = self.tree_widget.indexOfTopLevelItem(item)
                        if index >= 0:
                            self.tree_widget.takeTopLevelItem(index)
                except (RuntimeError, AttributeError):
                    continue

    def _bulk_set_project_name_mode(self, items, mode):
        """Set project name mode for multiple items - delegates to editor"""
        if self.editor and hasattr(self.editor, '_set_project_name_mode'):
            for item in items:
                try:
                    self.editor._set_project_name_mode(item, mode)
                except (RuntimeError, AttributeError):
                    continue

    def _bulk_revert_to_original(self, items):
        """Revert items to original names - delegates to editor"""
        if self.editor and hasattr(self.editor, '_revert_to_original_name'):
            for item in items:
                try:
                    self.editor._revert_to_original_name(item)
                except (RuntimeError, AttributeError):
                    continue

    def _configure_custom_patterns(self, item):
        """Configure custom naming patterns for file"""
        from ..file_operations import CustomPatternsDialog
        
        dialog = CustomPatternsDialog(self.tree_widget, item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_data = dialog.get_pattern_data()
            self._apply_pattern_to_item(item, pattern_data)
            
            # Clear any pending events to prevent unwanted context menu triggers
            self._clear_pending_events()

    def _configure_date_sequences(self, item):
        """Configure date sequences for file versioning"""
        from ..dialogs.date_sequence_dialog import DateSequenceDialog
        
        dialog = DateSequenceDialog(self.tree_widget, item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            date_data = dialog.get_date_data()
            self._apply_date_sequence_to_item(item, date_data)
            
            # Clear any pending events to prevent unwanted context menu triggers
            self._clear_pending_events()

    def _clear_pending_events(self):
        """Clear pending events to prevent unwanted context menu triggers"""
        if self.tree_widget:
            # Temporarily disable context menu to prevent spurious triggers
            original_policy = self.tree_widget.contextMenuPolicy()
            self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            
            # Also disable the structure editor's context menu if available
            if self.editor and hasattr(self.editor, '_disable_context_menu_temporarily'):
                self.editor._disable_context_menu_temporarily()
            
            # Process any pending events to clear the event queue
            QApplication.processEvents()
            
            # Use a timer to restore context menu after a short delay
            QTimer.singleShot(100, lambda: self._restore_context_menu(original_policy))
            
            # Ensure focus is properly managed
            self.tree_widget.clearFocus()
            self.tree_widget.setFocus()

    def _restore_context_menu(self, original_policy):
        """Restore the context menu policy after a delay"""
        if self.tree_widget:
            self.tree_widget.setContextMenuPolicy(original_policy)
            print("DEBUG: Context menu policy restored after dialog")

    def _apply_pattern_to_item(self, item, pattern_data):
        """Apply custom pattern to item - delegates to editor"""
        if self.editor and hasattr(self.editor, '_apply_pattern_to_item'):
            self.editor._apply_pattern_to_item(item, pattern_data)
        elif self.editor and hasattr(self.editor, 'file_operations'):
            # Try to delegate to file operations
            if hasattr(self.editor.file_operations, '_apply_pattern_to_item'):
                self.editor.file_operations._apply_pattern_to_item(item, pattern_data)

    def _apply_date_sequence_to_item(self, item, date_data):
        """Apply date sequence to item - delegates to editor"""
        if self.editor and hasattr(self.editor, '_apply_date_sequence_to_item'):
            self.editor._apply_date_sequence_to_item(item, date_data)
        elif self.editor and hasattr(self.editor, 'file_operations'):
            # Try to delegate to file operations
            if hasattr(self.editor.file_operations, '_apply_date_sequence_to_item'):
                self.editor.file_operations._apply_date_sequence_to_item(item, date_data) 