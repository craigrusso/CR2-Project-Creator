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
        """Create and show the context menu"""
        print(f"DEBUG: create_context_menu called with position {position}")
        
        if not self.tree_widget:
            print("DEBUG: create_context_menu - no tree widget available")
            return
        
        # Get the item at the click position
        item = self.tree_widget.itemAt(position)
        selected_items = self.tree_widget.selectedItems() if self.tree_widget else []
        
        # Ensure we have items to work with
        if not selected_items:
            if item:
                selected_items = [item]
                self.tree_widget.setCurrentItem(item)
            else:
                print("DEBUG: create_context_menu - no items to show menu for")
                return
        
        print(f"DEBUG: Selected items count: {len(selected_items)}")
        
        # Create the menu
        try:
            from PyQt6.QtWidgets import QMenu
            menu = QMenu(self.tree_widget)
            
            # Build menu content
            self._build_menu_content(menu, selected_items)
            
            # Show the menu
            global_pos = self.tree_widget.mapToGlobal(position)
            print(f"DEBUG: Executing context menu at global position {global_pos}")
            
            # Execute the menu and handle the result
            action = menu.exec(global_pos)
            print(f"DEBUG: Menu action completed: {action}")
            
        except Exception as e:
            print(f"ERROR: Exception in create_context_menu: {e}")
            import traceback
            traceback.print_exc()
            return

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
        """Build the context menu content based on selected items"""
        print(f"DEBUG: Building context menu for {len(selected_items)} selected items")
        
        # Filter items by type
        file_items = []
        folder_items = []
        
        for item in selected_items:
            try:
                item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                item_type = item_data.get('type', 'unknown')
                if item_type == 'file':
                    file_items.append(item)
                elif item_type == 'folder':
                    folder_items.append(item)
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error getting item data for menu: {e}")
                continue
        
        # Add basic actions
        add_file_action = menu.addAction("Add File")
        add_file_action.triggered.connect(self._add_file_handler)
        
        add_folder_action = menu.addAction("Add Folder")
        add_folder_action.triggered.connect(self._add_folder_handler)
        
        if selected_items:
            menu.addSeparator()
            
            # Delete action - store items reference safely
            delete_text = f"Delete {len(selected_items)} items" if len(selected_items) > 1 else "Delete"
            delete_action = menu.addAction(delete_text)
            delete_action.triggered.connect(lambda checked=False, items=selected_items[:]: self._delete_selected_items(items))
        
        # Add file-specific operations
        if file_items:
            self._add_file_operations(menu, file_items)

    def _add_file_handler(self):
        """Handle add file action"""
        try:
            if self.editor and hasattr(self.editor, 'add_file'):
                self.editor.add_file()
        except Exception as e:
            print(f"DEBUG: Error in add file handler: {e}")

    def _add_folder_handler(self):
        """Handle add folder action"""
        try:
            if self.editor and hasattr(self.editor, 'add_folder'):
                self.editor.add_folder()
        except Exception as e:
            print(f"DEBUG: Error in add folder handler: {e}")

    def _add_file_operations(self, menu, file_items):
        """Add file-specific operations to menu"""
        menu.addSeparator()
        
        if len(file_items) == 1:
            # Single file operations
            item = file_items[0]
            try:
                item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                
                # Check current state of the file
                is_using_custom_pattern = (item_data.get('uses_custom_pattern', False) and 
                                         item_data.get('pattern'))
                is_using_project_name = ((item_data.get('rename_flag', False) or 
                                        item_data.get('uses_project_name', False)) and 
                                       not is_using_custom_pattern)
                
                if is_using_custom_pattern:
                    # File has custom pattern - offer to clear it
                    clear_action = menu.addAction("Remove Custom Pattern")
                    clear_action.triggered.connect(lambda checked=False, target_item=item: self._clear_custom_pattern(target_item))
                    
                    menu.addSeparator()
                    
                    # Options to switch to project name modes
                    replace_action = menu.addAction("Replace with Project Name")
                    replace_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'replace'))
                    
                    prepend_action = menu.addAction("Prepend Project Name")
                    prepend_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'prepend'))
                    
                    append_action = menu.addAction("Append Project Name")
                    append_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'append'))
                    
                elif is_using_project_name:
                    # File uses project name - offer to change mode or clear
                    current_mode = item_data.get('project_name_mode', 'replace')
                    
                    revert_action = menu.addAction("Revert to Original Name")
                    revert_action.triggered.connect(lambda checked=False, target_item=item: self._revert_to_original(target_item))
                    
                    menu.addSeparator()
                    
                    # Project name mode options (only show different modes)
                    if current_mode != 'replace':
                        replace_action = menu.addAction("Replace with Project Name")
                        replace_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'replace'))
                    
                    if current_mode != 'prepend':
                        prepend_action = menu.addAction("Prepend Project Name")
                        prepend_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'prepend'))
                    
                    if current_mode != 'append':
                        append_action = menu.addAction("Append Project Name")
                        append_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'append'))
                    
                else:
                    # File uses original name - offer project name options
                    replace_action = menu.addAction("Replace with Project Name")
                    replace_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'replace'))
                    
                    prepend_action = menu.addAction("Prepend Project Name")
                    prepend_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'prepend'))
                    
                    append_action = menu.addAction("Append Project Name")
                    append_action.triggered.connect(lambda checked=False, target_item=item: self._switch_to_project_name_mode(target_item, 'append'))
                
                menu.addSeparator()
                
                # Custom pattern option
                pattern_action = menu.addAction("Custom Naming Pattern...")
                pattern_action.triggered.connect(lambda checked=False, target_item=item: self._configure_custom_patterns(target_item))
                
                # Versioning options
                date_action = menu.addAction("Date Sequences...")
                date_action.triggered.connect(lambda checked=False, target_item=item: self._configure_date_sequences(target_item))
                
            except Exception as e:
                print(f"DEBUG: Error processing single file menu: {e}")
                
        else:
            # Multiple files - bulk operations
            menu.addSeparator()
            
            # Make a copy of the file items list to avoid reference issues
            file_items_copy = file_items[:]
            
            # Bulk clear operations
            clear_patterns_action = menu.addAction("Clear All Custom Patterns")
            clear_patterns_action.triggered.connect(lambda checked=False, items=file_items_copy: self._bulk_clear_custom_patterns(items))
            
            revert_bulk_action = menu.addAction("Revert All to Original Names")
            revert_bulk_action.triggered.connect(lambda checked=False, items=file_items_copy: self._bulk_revert_to_original(items))
            
            menu.addSeparator()
            
            # Bulk project name operations
            prepend_bulk_action = menu.addAction("Prepend Project Name to All")
            prepend_bulk_action.triggered.connect(lambda checked=False, items=file_items_copy: self._bulk_set_project_name_mode(items, 'prepend'))
            
            append_bulk_action = menu.addAction("Append Project Name to All")
            append_bulk_action.triggered.connect(lambda checked=False, items=file_items_copy: self._bulk_set_project_name_mode(items, 'append'))
            
            replace_bulk_action = menu.addAction("Replace All with Project Name")
            replace_bulk_action.triggered.connect(lambda checked=False, items=file_items_copy: self._bulk_set_project_name_mode(items, 'replace'))



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

    def _add_folder_context_actions(self, menu, folder_item):
        """Add folder-specific context menu actions"""
        menu.addSeparator()
        
        # Expand/collapse actions for folders
        expand_action = menu.addAction("Expand")
        expand_action.triggered.connect(lambda: self.tree_widget.expandItem(folder_item) if self.tree_widget else None)
        
        collapse_action = menu.addAction("Collapse")
        collapse_action.triggered.connect(lambda: self.tree_widget.collapseItem(folder_item) if self.tree_widget else None)

    def _delete_selected_items(self, selected_items):
        """Delete the selected items"""
        if not selected_items:
            return
        
        # Confirm deletion
        from PyQt6.QtWidgets import QMessageBox
        item_count = len(selected_items)
        if item_count == 1:
            message = f"Are you sure you want to delete '{selected_items[0].text(0)}'?"
        else:
            message = f"Are you sure you want to delete {item_count} items?"
        
        reply = QMessageBox.question(None, "Confirm Deletion", message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                try:
                    parent = item.parent()
                    if parent:
                        parent.removeChild(item)
                    else:
                        index = self.tree_widget.indexOfTopLevelItem(item)
                        if index >= 0:
                            self.tree_widget.takeTopLevelItem(index)
                except (RuntimeError, AttributeError) as e:
                    print(f"DEBUG: Error deleting item: {e}")
                    continue

    def _bulk_set_project_name_mode(self, items, mode):
        """Set project name mode for multiple items - delegates to editor"""
        print(f"DEBUG: _bulk_set_project_name_mode called with {len(items)} items, mode: {mode}")
        
        # Try multiple delegation paths
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, '_set_project_name_mode'):
            # Delegate to file_operations module
            for item in items:
                try:
                    print(f"DEBUG: Calling file_operations._set_project_name_mode for item: {item.text(0)}")
                    self.editor.file_operations._set_project_name_mode(item, mode)
                except (RuntimeError, AttributeError) as e:
                    print(f"DEBUG: Error setting project name mode via file_operations: {e}")
                    continue
        elif self.editor and hasattr(self.editor, '_set_project_name_mode'):
            # Direct delegation to editor
            for item in items:
                try:
                    print(f"DEBUG: Calling editor._set_project_name_mode for item: {item.text(0)}")
                    self.editor._set_project_name_mode(item, mode)
                except (RuntimeError, AttributeError) as e:
                    print(f"DEBUG: Error setting project name mode via editor: {e}")
                    continue
        else:
            print(f"DEBUG: No suitable method found for setting project name mode. Editor: {self.editor}")
            if self.editor:
                print(f"DEBUG: Editor attributes: {[attr for attr in dir(self.editor) if not attr.startswith('_')]}")
                if hasattr(self.editor, 'file_operations'):
                    print(f"DEBUG: File operations attributes: {[attr for attr in dir(self.editor.file_operations) if not attr.startswith('_')]}")

    def _bulk_revert_to_original(self, items):
        """Revert items to original names - delegates to editor"""
        print(f"DEBUG: _bulk_revert_to_original called with {len(items)} items")
        
        # Try multiple delegation paths
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, '_revert_to_original_name'):
            # Delegate to file_operations module
            for item in items:
                try:
                    print(f"DEBUG: Calling file_operations._revert_to_original_name for item: {item.text(0)}")
                    self.editor.file_operations._revert_to_original_name(item)
                except (RuntimeError, AttributeError) as e:
                    print(f"DEBUG: Error reverting to original name via file_operations: {e}")
                    continue
        elif self.editor and hasattr(self.editor, '_revert_to_original_name'):
            # Direct delegation to editor
            for item in items:
                try:
                    print(f"DEBUG: Calling editor._revert_to_original_name for item: {item.text(0)}")
                    self.editor._revert_to_original_name(item)
                except (RuntimeError, AttributeError) as e:
                    print(f"DEBUG: Error reverting to original name via editor: {e}")
                    continue
        else:
            # Fallback: try to use _toggle_project_name_for_file to revert
            if self.editor and hasattr(self.editor, '_toggle_project_name_for_file'):
                for item in items:
                    try:
                        # Check if item is currently using project name
                        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                        if item_data.get('rename_flag') or item_data.get('uses_project_name'):
                            print(f"DEBUG: Using _toggle_project_name_for_file to revert item: {item.text(0)}")
                            self.editor._toggle_project_name_for_file(item)
                    except (RuntimeError, AttributeError) as e:
                        print(f"DEBUG: Error reverting via toggle method: {e}")
                        continue
            else:
                print(f"DEBUG: No suitable method found for reverting to original names. Editor: {self.editor}")

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
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, '_apply_pattern_to_item'):
            # Delegate to file_operations module (preferred)
            self.editor.file_operations._apply_pattern_to_item(item, pattern_data)
        elif self.editor and hasattr(self.editor, '_apply_pattern_to_item'):
            # Fallback to direct editor method
            self.editor._apply_pattern_to_item(item, pattern_data)
        else:
            print(f"DEBUG: No suitable method found for applying pattern to item")

    def _apply_date_sequence_to_item(self, item, date_data):
        """Apply date sequence to item - delegates to editor"""
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, '_apply_date_sequence_to_item'):
            # Delegate to file_operations module (preferred)
            self.editor.file_operations._apply_date_sequence_to_item(item, date_data)
        elif self.editor and hasattr(self.editor, '_apply_date_sequence_to_item'):
            # Fallback to direct editor method
            self.editor._apply_date_sequence_to_item(item, date_data)
        else:
            print(f"DEBUG: No suitable method found for applying date sequence to item") 

    def _switch_to_project_name_mode(self, item, mode):
        """Switch a file from any current mode to project name mode"""
        print(f"DEBUG: Switching item to project name mode: {mode}")
        
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, 'item_operations'):
            # Use the enhanced method from ItemOperations
            result = self.editor.file_operations.item_operations.switch_from_pattern_to_project_name(item, mode)
            if result:
                print(f"DEBUG: Successfully switched to {mode} mode")
            else:
                print(f"DEBUG: Failed to switch to {mode} mode")
        else:
            print(f"DEBUG: No suitable method found for switching to project name mode")

    def _clear_custom_pattern(self, item):
        """Clear custom pattern from a file and revert to original name"""
        print(f"DEBUG: Clearing custom pattern from item: {item.text(0)}")
        
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, 'item_operations'):
            # Use the reset method to completely clear everything
            self.editor.file_operations.item_operations.reset_item_to_original(item)
            print(f"DEBUG: Successfully cleared custom pattern")
        else:
            print(f"DEBUG: No suitable method found for clearing custom pattern")

    def _revert_to_original(self, item):
        """Revert a file to its original name"""
        print(f"DEBUG: Reverting item to original name: {item.text(0)}")
        
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, 'item_operations'):
            self.editor.file_operations.item_operations.reset_item_to_original(item)
            print(f"DEBUG: Successfully reverted to original name")
        else:
            print(f"DEBUG: No suitable method found for reverting to original")

    def _bulk_clear_custom_patterns(self, items):
        """Clear custom patterns from multiple items"""
        print(f"DEBUG: Clearing custom patterns from {len(items)} items")
        
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, 'item_operations'):
            for item in items:
                try:
                    item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                    if item_data.get('uses_custom_pattern', False):
                        self.editor.file_operations.item_operations.reset_item_to_original(item)
                        print(f"DEBUG: Cleared custom pattern from: {item.text(0)}")
                except (RuntimeError, AttributeError) as e:
                    print(f"DEBUG: Error clearing custom pattern: {e}")
                    continue
        else:
            print(f"DEBUG: No suitable method found for bulk clearing custom patterns") 