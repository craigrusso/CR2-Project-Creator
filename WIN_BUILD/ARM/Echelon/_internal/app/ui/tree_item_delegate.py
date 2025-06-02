#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit
from PyQt6.QtCore import Qt, QEvent

class TreeItemDelegate(QStyledItemDelegate):
    """
    Custom item delegate for tree widgets to ensure proper editing behavior
    Addresses issues with item editing and ensures consistent styling
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None
        self.edit_in_progress = False
        self.current_index = None
    
    def createEditor(self, parent, option, index):
        """
        Create a properly configured editor for the item
        
        Args:
            parent: Parent widget
            option: Style options
            index: Model index
        """
        # Store the current index
        self.current_index = index
        
        # Force the item to be editable
        if not (index.flags() & Qt.ItemFlag.ItemIsEditable):
            print(f"DEBUG: Making item at {index.row()} editable")
            model = index.model()
            if model:
                model.setData(index, True, Qt.ItemFlag.ItemIsEditable)
        
        # Create the line edit
        editor = QLineEdit(parent)
        editor.setStyleSheet("""
            background-color: #3a3a3a;
            color: white;
            border: 1px solid #5c78ad;
            border-radius: 3px;
            padding: 2px 4px;
            min-height: 24px;
        """)
        
        # Set minimum height to ensure visibility
        editor.setMinimumHeight(24)
        
        # Configure for editing
        editor.setFrame(True)
        editor.installEventFilter(self)
        
        # Store reference to the editor
        self.editor = editor
        self.edit_in_progress = True
        
        # Log creation
        print(f"DEBUG: Created editor for item '{index.data()}'")
        
        return editor
    
    def setEditorData(self, editor, index):
        """
        Set the editor's data from the model
        
        Args:
            editor: Editor widget
            index: Model index
        """
        # Get the current text
        value = index.model().data(index, Qt.ItemDataRole.EditRole) or index.model().data(index, Qt.ItemDataRole.DisplayRole)
        if value:
            editor.setText(str(value))
            editor.selectAll()  # Select all text for easy editing
        
        # Log
        print(f"DEBUG: Setting editor data to '{value}'")
    
    def setModelData(self, editor, model, index):
        """
        Update the model with edited data
        
        Args:
            editor: Editor widget
            model: Data model
            index: Model index
        """
        try:
            # Get the text from the editor
            value = editor.text()
            
            # Update the model
            model.setData(index, value, Qt.ItemDataRole.EditRole)
            
            # Get the tree widget item
            tree_widget = editor.parent().parent() if editor.parent() else None
            if tree_widget and hasattr(tree_widget, "itemFromIndex"):
                tree_item = tree_widget.itemFromIndex(index) 
                if tree_item:
                    # Update user data if it exists
                    item_data = tree_item.data(0, Qt.ItemDataRole.UserRole)
                    if isinstance(item_data, dict):
                        item_data['name'] = value
                        tree_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
            
            # Log success
            print(f"DEBUG: Updated item text to '{value}'")
            self.edit_in_progress = False
            
        except Exception as e:
            print(f"ERROR: Failed to update model data: {e}")
            self.edit_in_progress = False
    
    def updateEditorGeometry(self, editor, option, index):
        """
        Ensure the editor has the right size and position
        
        Args:
            editor: Editor widget
            option: Style options
            index: Model index
        """
        # Set the editor geometry to match the item
        editor.setGeometry(option.rect)
    
    def closeEditor(self, editor, hint):
        """
        Handle editor closing
        
        Args:
            editor: Editor widget
            hint: Close hint
        """
        try:
            # Ensure data is committed if editing finished
            if hint == QStyledItemDelegate.SubmitModelCache or hint == QStyledItemDelegate.EditNextItem:
                # Only commit if there are changes
                if self.edit_in_progress:
                    self.commitData.emit(editor)
            
            # Call base implementation to handle the close
            super().closeEditor(editor, hint)
            
            self.editor = None
            self.edit_in_progress = False
            print("DEBUG: Editor closed successfully")
            
        except Exception as e:
            print(f"ERROR: Failed to close editor properly: {e}")
            self.edit_in_progress = False
            # Make sure editor is closed even if there was an error
            super().closeEditor(editor, QStyledItemDelegate.NoHint)
    
    def eventFilter(self, obj, event):
        """
        Handle events for the editor
        
        Args:
            obj: Object receiving the event
            event: Event being processed
        """
        if obj is self.editor:
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                
                # Handle Enter/Return key - commit changes and close editor
                if key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                    # First commit the data
                    self.commitData.emit(obj)
                    
                    # Schedule the closing of the editor to avoid immediate recursion
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self._finishEditing(obj))
                    
                    return True
                
                # Handle Escape key - just close editor without committing
                elif key == Qt.Key.Key_Escape:
                    # Schedule the closing of the editor to avoid immediate recursion
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self._cancelEditing(obj))
                    
                    return True
            
            # Handle focus out - commit changes if not another editor
            elif event.type() == QEvent.Type.FocusOut:
                # Don't close if a popup is active or another editor is being opened
                if not obj.hasFocus():
                    # First commit the data
                    self.commitData.emit(obj)
                    
                    # Schedule the closing of the editor to avoid immediate recursion
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self._finishEditing(obj))
        
        # Let the base class handle other events
        return super().eventFilter(obj, event)

    def _finishEditing(self, editor):
        """Safely finish editing with data committed"""
        if self.edit_in_progress and editor == self.editor:
            try:
                # Call the closeEditor signal via QMetaObject.invokeMethod
                # to properly trigger the signal
                from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
                QMetaObject.invokeMethod(
                    self, 
                    "closeEditor", 
                    Qt.DirectConnection,
                    Q_ARG(object, editor),
                    Q_ARG(int, QStyledItemDelegate.SubmitModelCache)
                )
            except Exception as e:
                print(f"ERROR: Could not invoke closeEditor signal: {e}")
                # Use a more direct approach as fallback
                if hasattr(editor.parent(), "setFocus"):
                    editor.parent().setFocus()
            
            # Clear state
            self.edit_in_progress = False
            self.editor = None
            self.current_index = None

    def _cancelEditing(self, editor):
        """Safely cancel editing without committing data"""
        if self.edit_in_progress and editor == self.editor:
            try:
                # Call the closeEditor signal via QMetaObject.invokeMethod
                from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
                QMetaObject.invokeMethod(
                    self, 
                    "closeEditor", 
                    Qt.DirectConnection,
                    Q_ARG(object, editor),
                    Q_ARG(int, QStyledItemDelegate.RevertModelCache)
                )
            except Exception as e:
                print(f"ERROR: Could not invoke closeEditor signal: {e}")
                # Use a more direct approach as fallback
                if hasattr(editor.parent(), "setFocus"):
                    editor.parent().setFocus()
            
            # Clear state
            self.edit_in_progress = False
            self.editor = None
            self.current_index = None 