#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtCore import QObject, pyqtSignal


class UpdateWorker(QObject):
    """Worker thread for checking updates in the background."""
    update_found = pyqtSignal(dict)       # Emits full version info dict if update found
    check_complete = pyqtSignal(bool, str) # Emits (update_found_bool, error_message_str)
    finished = pyqtSignal()             # Always emits when run completes

    def __init__(self, app_instance, force_check=False):
        super().__init__()
        self.app_instance = app_instance
        self.force_check = force_check
        self._is_running = False

    def run_check(self):
        if self._is_running:
            return
            
        self._is_running = True
        update_info = None
        error_msg_out = ""
        update_found_flag = False
        
        try:
            # Call the existing logic
            update_info = self.app_instance._check_for_updates_logic(force_check=self.force_check)

            if isinstance(update_info, dict):
                # Update was found successfully
                self.update_found.emit(update_info) # Emit data first
                update_found_flag = True
            elif update_info is None:
                # No update found or check skipped, no error
                update_found_flag = False
            # else: Optional handling if _check_for_updates_logic returns specific error codes/strings
                
        except Exception as e:
            # An unexpected error occurred during the check logic call
            error_msg = f"Error during update check worker: {e}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            error_msg_out = error_msg # Set error message for check_complete
            update_found_flag = False
            
        finally:
            # Emit completion status regardless of outcome
            self.check_complete.emit(update_found_flag, error_msg_out)
            self._is_running = False
            self.finished.emit() # Signal thread can be cleaned up 