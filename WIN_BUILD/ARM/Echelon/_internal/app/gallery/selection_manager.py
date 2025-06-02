from PyQt6.QtCore import QObject, pyqtSignal

class GallerySelectionManager(QObject):
    '''Manages template selection state for the TemplateGallery.'''
    
    # Signal to indicate that the primary or multi-selection has changed.
    # Emits: primary_selected_template (dict or None), multi_selected_templates (list)
    selection_changed = pyqtSignal(object, list)

    def __init__(self, gallery_widget, parent=None):
        super().__init__(parent)
        self.gallery = gallery_widget  # Reference to the main gallery widget
        self._selected_template = None
        self._multi_selected_templates = []

    @property
    def selected_template(self):
        '''Get the primary selected template'''
        return self._selected_template
        
    @property
    def multi_selected_templates(self):
        '''Get all multi-selected templates (which includes the primary selected template)'''
        return self._multi_selected_templates

    def set_primary_selection(self, template_data, emit_signal=True, clear_multi=True):
        '''Set the primary selected template.
        
        Args:
            template_data: Template data dict or None
            emit_signal: Whether to emit the selection_changed signal
            clear_multi: If True, clear multi-selection; if False, add this to multi-selection
        '''
        try:
            # Only clear multi-selection if requested AND multi-selection exists and differs from new selection
            if clear_multi and self._multi_selected_templates and self._multi_selected_templates != [template_data]:
                # Store old values before making changes (for signal)
                old_multi = self._multi_selected_templates.copy()
                
                # Clear multi-selection and set the new primary
                self._multi_selected_templates = [template_data] if template_data else []
                self._selected_template = template_data # Ensure primary is set here too
                
                print(f"🔍 GALLERY: Selection Manager cleared multi-selection and set primary to {template_data.get('name') if template_data and isinstance(template_data, dict) else template_data}")
            
            else: # This block covers (not clear_multi) OR cases where clear_multi is true but conditions weren't met to clear.
                # Set the primary selected template first
                self._selected_template = template_data

                if template_data and not clear_multi:
                    # Ensure the new primary template is in the multi-selection list
                    if template_data not in self._multi_selected_templates:
                        self._multi_selected_templates.append(template_data)
                        print(f"🔍 GALLERY: Selection Manager added primary {template_data.get('name') if isinstance(template_data, dict) else template_data} to multi-selection list.")
                    else:
                        # If it was already there, that's fine. It's now primary.
                        print(f"🔍 GALLERY: Selection Manager confirmed primary {template_data.get('name') if isinstance(template_data, dict) else template_data} is in multi-selection list.")
                elif not template_data and not clear_multi: # Clearing primary but not clearing multi (e.g. deselecting primary in a multi-select scenario)
                    # This scenario should be handled carefully. If primary is set to None
                    # but multi-selection is preserved, a new primary might be chosen from multi-list later.
                    # For now, just setting primary to None. The multi_selected_templates list remains as is.
                    pass
                elif clear_multi and template_data : # This means conditions for full clear weren't met, but we are setting a new primary with clear_multi=True
                                                     # e.g. multi_selected_templates was empty or already just [template_data]
                    self._multi_selected_templates = [template_data]
                elif clear_multi and not template_data: # Clearing selection entirely
                     self._multi_selected_templates = []


            # Emit the selection changed signal if requested
            if emit_signal:
                # Make a copy of the multi-selection list to avoid external modification
                multi_copy = self._multi_selected_templates.copy() if self._multi_selected_templates else []
                self.selection_changed.emit(self._selected_template, multi_copy)
                print(f"🔍 GALLERY: Selection Manager reported update. Primary: {self._selected_template.get('name') if self._selected_template and isinstance(self._selected_template, dict) else self._selected_template}, Multi: {[t.get('name') if isinstance(t, dict) else str(t) for t in multi_copy]}")
                
            return True
        except Exception as e:
            print(f"[ERROR] Error in set_primary_selection: {e}")
            import traceback
            traceback.print_exc()
            return False

    def add_to_multi_selection(self, template_data, emit_signal=True):
        '''Add a template to the multi-selection list without affecting primary selection.'''
        try:
            if not template_data:
                return False
                
            # If template is not already in multi-selection, add it
            if template_data not in self._multi_selected_templates:
                self._multi_selected_templates.append(template_data)
                
                # Emit signal if requested
                if emit_signal:
                    # Make a copy to avoid external modification
                    multi_copy = self._multi_selected_templates.copy()
                    self.selection_changed.emit(self._selected_template, multi_copy)
                    print(f"🔍 GALLERY: Selection Manager added to multi. Primary: {self._selected_template.get('name') if self._selected_template and isinstance(self._selected_template, dict) else self._selected_template}, Multi: {[t.get('name') if isinstance(t, dict) else str(t) for t in multi_copy]}")
                    
                return True
            return False  # Template already in multi-selection
        except Exception as e:
            print(f"[ERROR] Error in add_to_multi_selection: {e}")
            import traceback
            traceback.print_exc()
            return False

    def toggle_multi_selection(self, template_data, emit_signal=True):
        '''Toggle a template's presence in the multi-selection list.'''
        try:
            if template_data in self._multi_selected_templates:
                # Remove from multi-selection
                self._multi_selected_templates.remove(template_data)
                
                # If we removed the primary selection, update primary
                if self._selected_template == template_data:
                    if self._multi_selected_templates:
                        # Set primary to first item in multi-selection
                        self._selected_template = self._multi_selected_templates[0]
                    else:
                        # No more items in multi-selection, clear primary
                        self._selected_template = None
                
                # Emit signal if requested
                if emit_signal:
                    # Make a copy to avoid external modification
                    multi_copy = self._multi_selected_templates.copy()
                    self.selection_changed.emit(self._selected_template, multi_copy)
                    print(f"🔍 GALLERY: Selection Manager toggled off. Primary: {self._selected_template.get('name') if self._selected_template and isinstance(self._selected_template, dict) else self._selected_template}, Multi: {[t.get('name') if isinstance(t, dict) else str(t) for t in multi_copy]}")
                
                return True
            else:
                # Add to multi-selection
                return self.add_to_multi_selection(template_data, emit_signal)
        except Exception as e:
            print(f"[ERROR] Error in toggle_multi_selection: {e}")
            import traceback
            traceback.print_exc()
            return False

    def clear_selection(self, emit_signal=True):
        '''Clear both primary and multi-selection.'''
        try:
            self._selected_template = None
            self._multi_selected_templates.clear()
            
            # Emit signal if requested
            if emit_signal:
                self.selection_changed.emit(None, [])
                print("🔍 GALLERY: Selection Manager cleared all selections")
                
            return True
        except Exception as e:
            print(f"[ERROR] Error in clear_selection: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def is_selected(self, template_data):
        '''Check if a template is the primary selected template.'''
        return self._selected_template == template_data
        
    def is_multi_selected(self, template_data):
        '''Check if a template is in the multi-selection list.'''
        return template_data in self._multi_selected_templates
        
    def set_selection_state(self, primary_template, multi_selected_templates):
        '''Set both primary selection and multi-selection in one operation.'''
        try:
            self._selected_template = primary_template
            self._multi_selected_templates = list(multi_selected_templates) if multi_selected_templates else []
            
            # Emit signal
            multi_copy = self._multi_selected_templates.copy()
            self.selection_changed.emit(self._selected_template, multi_copy)
            print(f"🔍 GALLERY: Selection Manager state restored. Primary: {self._selected_template.get('name') if self._selected_template and isinstance(self._selected_template, dict) else self._selected_template}, Multi count: {len(multi_copy)}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Error in set_selection_state: {e}")
            import traceback
            traceback.print_exc()
            return False

    def handle_item_interaction(self, template_data, is_ctrl_cmd_modifier, is_shift_modifier=False):
        '''
        Handles user interaction (click) on a template item.
        is_ctrl_cmd_modifier: True if Ctrl (Windows/Linux) or Command (Mac) was pressed.
        is_shift_modifier: True if Shift was pressed (for range selection - basic implementation).
        '''
        try:
            if not isinstance(template_data, dict) or not template_data.get('name'):
                print("[ERROR] SelectionManager: Invalid template data in handle_item_interaction.")
                return

            # Store old state for change detection to see if a signal is needed
            old_primary_name = self._selected_template.get('name') if self._selected_template else None
            old_multi_names = {t.get('name') for t in self._multi_selected_templates if t and t.get('name')}

            # --- Shift-click (Basic: acts like Ctrl/Cmd for adding, or single click if no Ctrl/Cmd) ---
            # Proper range selection would require an anchor item.
            if is_shift_modifier:
                # If Ctrl/Cmd is also pressed with Shift, it's like a normal Ctrl/Cmd click for adding to selection
                if is_ctrl_cmd_modifier:
                    if template_data not in self._multi_selected_templates:
                        self._multi_selected_templates.append(template_data)
                    # The last item clicked in a shift-ctrl-click usually becomes the primary
                    self._selected_template = template_data
                # If Shift is pressed alone (no Ctrl/Cmd)
                # A common OS behavior is to select a range from the last selected item (anchor).
                # Without an anchor, it could act like a single click or add to current selection.
                # For now, let's treat Shift-only like a single click that starts a new selection, making it primary.
                # Or, if we want to extend selection: if primary exists, add this to multi and make it primary.
                else:
                    # Simple Shift-click: if something is primary, add new item to multi and make it primary.
                    # If nothing is primary, acts like a single click.
                    if self._selected_template and self._selected_template != template_data:
                        if self._selected_template not in self._multi_selected_templates: # Add old primary if not there
                            self._multi_selected_templates.append(self._selected_template)
                        if template_data not in self._multi_selected_templates:
                            self._multi_selected_templates.append(template_data)
                        self._selected_template = template_data
                    else: # No primary, or clicking the same primary again with shift
                        self._selected_template = template_data
                        if template_data not in self._multi_selected_templates:
                             self._multi_selected_templates.append(template_data)
                        # If only this item is now intended for selection due to shift alone
                        # and no other modifiers, we might want to clear other multi-selected items.
                        # However, typical shift-click *extends*. Let's assume extension for now.
                        # If you want shift to *replace* multi-selection with just this item, uncomment next line:
                        # self._multi_selected_templates = [template_data]
           
            # --- Ctrl/Cmd-click (without Shift) or Simple Click ---
            elif is_ctrl_cmd_modifier: # Ctrl/Cmd is pressed, Shift is not
                if template_data in self._multi_selected_templates:
                    self._multi_selected_templates.remove(template_data)
                    if self._selected_template == template_data: # If primary was deselected
                        self._selected_template = self._multi_selected_templates[0] if self._multi_selected_templates else None
                else:
                    self._multi_selected_templates.append(template_data)
                    self._selected_template = template_data # Newly ctrl-clicked item becomes primary
            else: # Simple click (no modifiers)
                self._selected_template = template_data
                self._multi_selected_templates = [template_data]

            # --- Post-interaction state normalization ---
            # Ensure primary selection is valid and consistent with multi-selection list
            if self._multi_selected_templates:
                if not self._selected_template or self._selected_template not in self._multi_selected_templates:
                    # If primary is None or not in multi-list, set primary to the last item in multi-list
                    self._selected_template = self._multi_selected_templates[-1]
            else: # If multi_selected_templates is empty, primary must be None
                self._selected_template = None

            # Update app's selected template reference
            if hasattr(self.gallery, 'app') and self.gallery.app:
                self.gallery.app.selected_template = self._selected_template
                # TODO: Update app.template_file_path based on the new primary selection
                # This might involve getting the path from template_data or template_manager

            # Emit signal if a meaningful change occurred in selection state
            new_primary_name = self._selected_template.get('name') if self._selected_template else None
            new_multi_names = {t.get('name') for t in self._multi_selected_templates if t and t.get('name')}

            if old_primary_name != new_primary_name or old_multi_names != new_multi_names:
                self.selection_changed.emit(self._selected_template, list(self._multi_selected_templates))
            
            # print(f"🔍 SEL_MAN: Handled item interaction. Primary: {new_primary_name}. Multi count: {len(new_multi_names)}")
        except Exception as e:
            print(f"Error in GallerySelectionManager.handle_item_interaction: {e}")
            import traceback
            traceback.print_exc()

    def set_selection_state(self, primary_template_data, multi_selected_list, emit_signal=True):
        '''Synchronizes the selection state with an external source (e.g., table view).
        
        Args:
            primary_template_data: The template data (dict) for the primary selection, or None.
            multi_selected_list: A list of template data (dict) for all multi-selected items.
            emit_signal: Whether to emit the selection_changed signal.
        '''
        try:
            old_primary_name = self._selected_template.get('name') if self._selected_template else None
            old_multi_names = {t.get('name') for t in self._multi_selected_templates if t and t.get('name')}

            self._selected_template = primary_template_data
            self._multi_selected_templates = list(multi_selected_list) if multi_selected_list else [] # Ensure it's a new list

            # Ensure consistency: primary must be in multi-list if multi-list is not empty
            if self._selected_template and self._multi_selected_templates:
                if self._selected_template not in self._multi_selected_templates:
                    # This case should ideally be handled by the caller ensuring consistency,
                    # but as a safeguard, add primary to multi if it's missing.
                    # Or, if primary is meant to be exclusive, then multi should be just [primary].
                    # For now, let's assume multi_selected_list is the definitive list of selected items,
                    # and primary_template_data is just a hint for the focused one among them.
                    # So, if primary is not in multi, then current primary is invalid w.r.t. multi_list
                    # Default to the first item in multi_list or None if multi_list is empty.
                    # print(f"[WARN] SelectionManager: Primary '{self._selected_template.get('name')}' not in multi-list. Adjusting.")
                    # self._multi_selected_templates.append(self._selected_template) # Option 1: Add it
                    pass # Option 2: Assume multi_selected_list is correct, primary might be temporarily out of sync or represents focus.
                         # The normalization below will handle it.

            # Re-normalize after direct state setting
            if self._multi_selected_templates:
                if not self._selected_template or self._selected_template not in self._multi_selected_templates:
                    self._selected_template = self._multi_selected_templates[0] # Default to first in multi if primary is inconsistent
            else: # If multi is empty, primary must be empty
                self._selected_template = None

            if hasattr(self.gallery, 'app') and self.gallery.app:
                self.gallery.app.selected_template = self._selected_template

            new_primary_name = self._selected_template.get('name') if self._selected_template else None
            new_multi_names = {t.get('name') for t in self._multi_selected_templates if t and t.get('name')}

            if emit_signal and (old_primary_name != new_primary_name or old_multi_names != new_multi_names):
                self.selection_changed.emit(self._selected_template, list(self._multi_selected_templates))
        except Exception as e:
            print(f"Error in GallerySelectionManager.set_selection_state: {e}")
            import traceback
            traceback.print_exc()

    # More methods will be added here to move logic from TemplateGallery:
    # - handle_item_press(self, template_data, event_modifiers)
    # - handle_table_selection_update(self, ...) 