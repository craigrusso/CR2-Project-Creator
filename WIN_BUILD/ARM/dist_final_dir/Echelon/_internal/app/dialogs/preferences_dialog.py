#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog window for application preferences.
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QGridLayout, QTabWidget, QWidget,
                           QLineEdit, QFileDialog, QMessageBox, QCheckBox,
                           QSpinBox, QGroupBox, QDialogButtonBox, QSpacerItem,
                           QSizePolicy, QComboBox)
from PyQt6.QtCore import QSettings

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, GROUPBOX_STYLE, COMBOBOX_STYLE, ACCENT_BUTTON_STYLE
from app.ui.styles.dialog_styles import LABEL_STYLE, LINEEDIT_STYLE, CHECKBOX_STYLE, SPINBOX_STYLE
from app.utils.utils import open_folder
from app.core import config_manager

# Import the logging utilities
from app.utils.logging_utils import (
    get_logger, set_log_level, enable_console_logging, enable_file_logging,
    LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARNING, LOG_LEVEL_ERROR
)

def show_preferences_dialog(parent=None):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Preferences")
    dialog.setMinimumWidth(500)
    base_style = f"background-color: {colors['bg']}; color: {colors['text']};"
    
    # Apply the base style without overriding the CHECKBOX_STYLE which is imported
    dialog.setStyleSheet(base_style)

    main_layout = QVBoxLayout(dialog)
    tabs = QTabWidget()

    # Define improved Tab QSS (using colors dict)
    tab_qss = f'''
        QTabWidget::pane {{
            border-top: 1px solid {colors.get('accent', '#2A82DA')};
            margin-top: -1px;
            background-color: {colors['bg']}; 
        }}
        QTabBar::tab:selected {{
            background-color: {colors.get('primary', '#2A82DA')};
            color: white;
            border: 1px solid {colors.get('accent', '#2A82DA')};
            border-bottom: none; 
            padding: 5px 10px;
            margin-left: -1px; 
            margin-right: -1px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:!selected {{
            background-color: {colors.get('card_bg', '#3C3C3C')};
            color: {colors.get('secondary_text', '#BBBBBB')};
            border: 1px solid {colors.get('border', '#555555')};
            border-bottom: 1px solid {colors.get('border', '#555555')}; 
            padding: 5px 10px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-bottom: 0px;
        }}
        QTabBar::tab:!selected:hover {{
            background-color: {colors.get('hover_bg', '#4D4D4D')};
            color: {colors.get('text', 'white')};
            border: 1px solid {colors.get('accent', '#555555')};
        }}
        QTabBar {{
            qproperty-drawBase: 0; 
            border: none; 
            margin-bottom: -1px; 
        }}
    '''
    tabs.setStyleSheet(tab_qss)

    # --- Storage Location Tab (MODIFIED) ---
    storage_tab = QWidget()
    storage_layout = QGridLayout(storage_tab)
    storage_layout.setColumnStretch(1, 1)  # Make the path column expandable

    row = 0

    # --- ADDED: Data Root Directory ---
    data_root_label = QLabel("Data Root Directory:")
    data_root_label.setStyleSheet(LABEL_STYLE)
    storage_layout.addWidget(data_root_label, row, 0)

    data_root_field = QLineEdit()
    data_root_field.setText(config_manager.get_user_data_root()) # Get path from config_manager
    data_root_field.setReadOnly(True)
    data_root_field.setStyleSheet(LINEEDIT_STYLE)
    # Make the field span columns 1, 2, and 3
    storage_layout.addWidget(data_root_field, row, 1, 1, 3) 

    # --- Button Row --- 
    row += 1 # Move to the next row for the buttons

    # Button layout for Change, Reset, Open
    button_hbox = QHBoxLayout()

    data_root_browse_btn = QPushButton("Change...")
    data_root_browse_btn.setStyleSheet(BUTTON_STYLE)
    def browse_data_root():
        current_path = data_root_field.text()
        new_path = QFileDialog.getExistingDirectory(
            dialog, "Select Data Root Directory", current_path)
        if new_path:
            success = config_manager.set_user_data_root(new_path)
            if success:
                data_root_field.setText(new_path)
                QMessageBox.information(dialog, "Path Changed",
                                        f"Data root path set to:\n{new_path}\n\nPlease restart the application for all changes to take full effect.")
            else:
                 QMessageBox.warning(dialog, "Error Changing Path",
                                     f"Could not set the data root path to:\n{new_path}\n\nPlease ensure the location is valid and writable.")
    data_root_browse_btn.clicked.connect(browse_data_root)
    button_hbox.addWidget(data_root_browse_btn)

    # --- ADDED: Reset Button ---
    data_root_reset_btn = QPushButton("Reset to Default")
    data_root_reset_btn.setStyleSheet(BUTTON_STYLE) # Use the same style
    def reset_data_root():
        reply = QMessageBox.question(dialog, "Confirm Reset",
                                     "Are you sure you want to reset the data root directory to the default location?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            settings = QSettings()
            settings.remove(config_manager.SETTINGS_KEY_USER_DATA_ROOT)
            settings.sync() # Ensure change is saved
            # Force config manager to forget the cached path and get the new default
            new_default_path = config_manager.get_user_data_root(force_reload=True)
            data_root_field.setText(new_default_path)
            QMessageBox.information(dialog, "Path Reset",
                                    f"Data root path reset to default:\n{new_default_path}\n\nPlease restart the application for this change to take full effect.")
    data_root_reset_btn.clicked.connect(reset_data_root)
    button_hbox.addWidget(data_root_reset_btn) # Add to HBox

    data_root_open_btn = QPushButton("Open")
    data_root_open_btn.setStyleSheet(BUTTON_STYLE)
    def open_data_root():
        open_folder(data_root_field.text())
    data_root_open_btn.clicked.connect(open_data_root)
    button_hbox.addWidget(data_root_open_btn)

    # Add the horizontal button layout to the grid
    storage_layout.addLayout(button_hbox, row, 2, 1, 2) # Span across columns 2 and 3

    # Add note about derived paths and restarting
    row += 1
    derived_paths_label = QLabel("Templates, Cache, Settings, Structures, etc., are stored in subdirectories within this Data Root Directory.")
    derived_paths_label.setStyleSheet(f"color: {colors['secondary_text']};")
    derived_paths_label.setWordWrap(True)
    # Make note span all columns
    storage_layout.addWidget(derived_paths_label, row, 0, 1, 4)

    # Adjusted row increment
    row += 1 
    note_label = QLabel("Note: Restart the application for path changes to take full effect.")
    note_label.setStyleSheet(f"color: {colors['secondary_text']}; font-style: italic;")
    # Make note span all columns
    storage_layout.addWidget(note_label, row, 0, 1, 4)

    # Add stretch at the bottom
    row += 1
    storage_layout.setRowStretch(row, 1)

    # Add the tabs to the tab widget
    tabs.addTab(storage_tab, "Storage") # Renamed tab

    # --- Cache Management Tab (MODIFIED) ---
    cache_tab = QWidget()
    cache_layout = QVBoxLayout(cache_tab)

    # Get current cache preferences (Import and use)
    try:
        from app.utils.cache_preferences import CachePreferences
        cache_prefs = CachePreferences()
        cache_prefs_available = True
    except ImportError:
        # print("WARN: CachePreferences module not found.")
        cache_prefs = None
        cache_prefs_available = False

    # Enable file caching group
    caching_group = QGroupBox("File Caching Settings")
    caching_group.setStyleSheet(GROUPBOX_STYLE) # Apply the imported style
    caching_layout = QVBoxLayout(caching_group)

    # Fix for checkbox styling - use direct styling to ensure checkmarks display properly
    checkbox_direct_style = f"""
        QCheckBox {{
            color: {colors['text']};
            spacing: 5px;
        }}
        
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors['border']};
            border-radius: 3px;
            background-color: {colors['card_bg']};
        }}
        
        QCheckBox::indicator:hover {{
            border: 1px solid {colors['accent']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors['accent']};
            border: 1px solid {colors['accent']};
        }}
    """

    # Create checkboxes with text containing Unicode checkmark
    enable_caching_check = QCheckBox("Enable file caching")
    enable_caching_check.setStyleSheet(checkbox_direct_style)
    enable_caching_check.setChecked(cache_prefs.should_cache_files() if cache_prefs_available else True)
    enable_caching_check.setToolTip("Cache files used in templates for better performance")
    enable_caching_check.setEnabled(cache_prefs_available)
    caching_layout.addWidget(enable_caching_check)

    auto_clean_check = QCheckBox("Automatically clean cache periodically")
    auto_clean_check.setStyleSheet(checkbox_direct_style)
    auto_clean_check.setChecked(cache_prefs.should_clean_cache() if cache_prefs_available else True)
    auto_clean_check.setToolTip("Remove old and unused files")
    auto_clean_check.setEnabled(cache_prefs_available)
    caching_layout.addWidget(auto_clean_check)

    params_layout = QGridLayout()
    max_size_label = QLabel("Maximum Cache Size (MB):")
    max_size_label.setStyleSheet(LABEL_STYLE)
    params_layout.addWidget(max_size_label, 0, 0)
    max_size_field = QSpinBox()
    max_size_field.setMinimum(100)
    max_size_field.setMaximum(10000)
    max_size_field.setValue(cache_prefs.get_preference("max_cache_size_mb", 1000) if cache_prefs_available else 1000)
    max_size_field.setSingleStep(100)
    max_size_field.setStyleSheet(SPINBOX_STYLE)
    max_size_field.setEnabled(cache_prefs_available)
    params_layout.addWidget(max_size_field, 0, 1)
    max_age_label = QLabel("Maximum Cache Age (days):")
    max_age_label.setStyleSheet(LABEL_STYLE)
    params_layout.addWidget(max_age_label, 1, 0)
    max_age_field = QSpinBox()
    max_age_field.setMinimum(1)
    max_age_field.setMaximum(365)
    max_age_field.setValue(cache_prefs.get_preference("max_cache_age_days", 30) if cache_prefs_available else 30)
    max_age_field.setSingleStep(1)
    max_age_field.setStyleSheet(SPINBOX_STYLE)
    max_age_field.setEnabled(cache_prefs_available)
    params_layout.addWidget(max_age_field, 1, 1)
    caching_layout.addLayout(params_layout)

    # Cache statistics group
    stats_group = QGroupBox("Cache Statistics")
    stats_group.setStyleSheet(GROUPBOX_STYLE) # Apply the imported style
    stats_layout = QVBoxLayout(stats_group)

    # Get cache statistics using config_manager path
    cache_manager_instance = None
    stats_available = False
    current_cache_path = "N/A" # Default value
    cache_stats = {} # Default value
    # CORRECTED try/except block structure
    try:
        from app.utils.file_cache_manager import FileCacheManager
        current_cache_path = config_manager.get_cache_path()
        cache_manager_instance = FileCacheManager(current_cache_path)
        cache_stats = cache_manager_instance.get_cache_stats()
        stats_available = True # Only set True if all succeed
    except ImportError:
        # print("WARN: FileCacheManager module not found.")
        stats_available = False # Ensure stats_available is False
    except Exception as e_stat:
        print(f"ERROR initializing FileCacheManager or getting stats: {e_stat}")
        stats_available = False # Ensure stats_available is False

    stats_grid = QGridLayout()
    total_files_label = QLabel("Total Files:")
    total_files_label.setStyleSheet(LABEL_STYLE)
    stats_grid.addWidget(total_files_label, 0, 0)
    total_files_value = QLabel(str(cache_stats.get("cached_files", 0)) if stats_available else "N/A")
    total_files_value.setStyleSheet(LABEL_STYLE)
    stats_grid.addWidget(total_files_value, 0, 1)

    total_size_label = QLabel("Total Size:")
    total_size_label.setStyleSheet(LABEL_STYLE)
    stats_grid.addWidget(total_size_label, 1, 0)
    # Check instance exists before calling method
    total_size_str = cache_manager_instance._human_readable_size(cache_stats.get("total_size", 0)) if stats_available and cache_manager_instance else "N/A"
    total_size_value = QLabel(total_size_str)
    total_size_value.setStyleSheet(LABEL_STYLE)
    stats_grid.addWidget(total_size_value, 1, 1)

    current_cache_loc_label = QLabel("Current Cache Location:")
    current_cache_loc_label.setStyleSheet(LABEL_STYLE)
    stats_grid.addWidget(current_cache_loc_label, 2, 0)
    current_cache_loc_value = QLabel(current_cache_path)
    current_cache_loc_value.setStyleSheet(LABEL_STYLE)
    current_cache_loc_value.setWordWrap(True)
    stats_grid.addWidget(current_cache_loc_value, 2, 1)

    cache_open_btn_stats = QPushButton("Open Cache Folder")
    cache_open_btn_stats.setStyleSheet(BUTTON_STYLE)
    cache_open_btn_stats.setEnabled(stats_available)
    def open_cache_stats_location():
        if stats_available and current_cache_path != "N/A" and os.path.exists(current_cache_path):
            open_folder(current_cache_path)
        else:
             QMessageBox.warning(dialog, "Error", "Cache path not available or does not exist.")
    cache_open_btn_stats.clicked.connect(open_cache_stats_location)
    stats_grid.addWidget(cache_open_btn_stats, 3, 0, 1, 2)
    stats_layout.addLayout(stats_grid)

    # Cache maintenance buttons
    maintenance_layout = QHBoxLayout()
    clean_cache_btn = QPushButton("Clean Cache Now")
    clean_cache_btn.setStyleSheet(BUTTON_STYLE)
    clean_cache_btn.setEnabled(stats_available)
    def clean_cache():
        if not cache_manager_instance:
            QMessageBox.warning(dialog, "Error", "Cache manager not available.")
            return
        result = QMessageBox.question(dialog, "Clean Cache",
                                     "Are you sure you want to clean the cache according to the current size/age settings? This will remove old and unused files.")
        if result == QMessageBox.Yes:
            try:
                # --- MODIFIED: Handle dictionary return value --- 
                prune_results = cache_manager_instance.prune_cache(
                    max_age_days=max_age_field.value(),
                    max_size_mb=max_size_field.value()
                )
                # --- END MODIFIED ---

                new_stats = cache_manager_instance.get_cache_stats()
                total_files_value.setText(str(new_stats.get("cached_files", 0)))
                size_str = cache_manager_instance._human_readable_size(new_stats.get("total_size", 0)) if cache_manager_instance else "N/A"
                total_size_value.setText(size_str)
                
                # --- MODIFIED: Use keys from the result dictionary --- 
                files_removed_count = prune_results.get('files_removed', 0)
                space_reclaimed_str = prune_results.get('bytes_removed_human', '0 B')
                QMessageBox.information(dialog, "Cache Cleaned",
                                     f"Cache cleaned successfully.\nFiles removed: {files_removed_count}\nSpace reclaimed: {space_reclaimed_str}")
                # --- END MODIFIED ---
            except Exception as e_clean:
                QMessageBox.warning(dialog, "Error", f"Error cleaning cache: {e_clean}")
    clean_cache_btn.clicked.connect(clean_cache)
    maintenance_layout.addWidget(clean_cache_btn)

    clear_cache_btn = QPushButton("Clear All Cache")
    clear_cache_btn.setStyleSheet(BUTTON_STYLE)
    clear_cache_btn.setEnabled(stats_available)
    def clear_cache():
        if not cache_manager_instance:
            QMessageBox.warning(dialog, "Error", "Cache manager not available.")
            return
        result = QMessageBox.warning(dialog, "Clear Cache",
                                    "ARE YOU SURE you want to clear the entire cache?\nThis will remove ALL cached files and cannot be undone.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if result == QMessageBox.Yes:
            try:
                total_removed = cache_manager_instance.clear_all_caches()
                new_stats = cache_manager_instance.get_cache_stats()
                total_files_value.setText(str(new_stats.get("cached_files", 0)))
                # Check instance exists before calling method
                size_str = cache_manager_instance._human_readable_size(new_stats.get("total_size", 0)) if cache_manager_instance else "N/A"
                total_size_value.setText(size_str)
                QMessageBox.information(dialog, "Cache Cleared", f"All cache files ({total_removed}) have been removed.")
            except Exception as e_clear:
                QMessageBox.warning(dialog, "Error", f"Error clearing cache: {e_clear}")
    clear_cache_btn.clicked.connect(clear_cache)
    maintenance_layout.addWidget(clear_cache_btn)
    stats_layout.addLayout(maintenance_layout)

    # Add the groups to the cache tab
    cache_layout.addWidget(caching_group)
    cache_layout.addWidget(stats_group)
    cache_layout.addStretch()

    # Show warning if modules were missing
    if not cache_prefs_available or not stats_available:
         warning_label = QLabel("Cache management features may be limited as required modules were not found.")
         # Assuming 'warning' color exists in the color scheme
         warning_color = colors.get('warning', colors.get('secondary_text', '#FFA500')) # Fallback color
         warning_label.setStyleSheet(f"color: {warning_color};")
         warning_label.setWordWrap(True)
         cache_layout.addWidget(warning_label)

    # Save function for cache preferences
    def save_cache_preferences():
        if cache_prefs_available and cache_prefs:
            cache_prefs.set_preference("enable_file_caching", enable_caching_check.isChecked())
            cache_prefs.set_preference("auto_clean_cache", auto_clean_check.isChecked())
            cache_prefs.set_preference("max_cache_size_mb", max_size_field.value())
            cache_prefs.set_preference("max_cache_age_days", max_age_field.value())
            cache_prefs.save_preferences()
        else:
            print("DEBUG: Cache preferences save skipped (CachePreferences unavailable).")

    # Add Cache tab to main tabs
    tabs.addTab(cache_tab, "Cache")

    # --- Apply Tab Styling ---
    tabs.setStyleSheet(f"""
        QTabWidget::pane {{ /* The tab widget frame */
            border-top: 1px solid {colors['border']};
            margin-top: -1px; /* Adjust overlap */
        }}

        QTabBar::tab {{ /* Style for unselected tabs */
            background: {colors['card_bg']};
            color: {colors['secondary_text']}; /* Use secondary text for inactive tabs */
            border: 1px solid {colors['border']};
            border-bottom: none; /* Remove bottom border for seamless look */
            padding: 8px 15px;
            margin-right: 2px; /* Spacing between tabs */
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
        }}

        QTabBar::tab:hover {{
            background: {colors['hover_bg']};
            color: {colors['text']}; /* Use primary text color on hover */
        }}

        QTabBar::tab:selected {{ /* Style for selected tab */
            background: {colors['accent']}; /* Use accent blue for selected tab background */
            color: {colors['highlight_text']}; /* Use white text for selected tab */
            border: 1px solid {colors['border']}; /* Keep standard border */
            border-bottom: none; /* Remove bottom border to avoid visual clash with pane */
        }}
        
        QTabBar::tab:!selected {{
             margin-top: 2px; /* Push non-selected tabs down slightly */
        }}
    """)

    # --- Add new Logging tab ---
    logging_tab = QWidget()
    logging_layout = QVBoxLayout(logging_tab)

    # Logging settings group
    logging_group = QGroupBox("Logging Settings")
    logging_group.setStyleSheet(GROUPBOX_STYLE)
    logging_inner_layout = QVBoxLayout(logging_group)

    # Log level selection
    level_layout = QHBoxLayout()
    level_label = QLabel("Log Level:")
    level_label.setStyleSheet(LABEL_STYLE)
    level_layout.addWidget(level_label)
    
    # Create a standard QComboBox
    level_combo = QComboBox()
    level_combo.setStyleSheet(COMBOBOX_STYLE)  # Use the global COMBOBOX_STYLE
    
    # Add items with both the text and user data
    level_options = [
        ("Debug", LOG_LEVEL_DEBUG),
        ("Info", LOG_LEVEL_INFO),
        ("Warning", LOG_LEVEL_WARNING),
        ("Error", LOG_LEVEL_ERROR)
    ]
    
    for text, data in level_options:
        level_combo.addItem(text, data)  # Remove the added triangle symbol
    
    # Set current selected level based on settings
    settings = QSettings()
    current_level_name = settings.value('logging/level', 'INFO')
    level_map = {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3,
    }
    level_combo.setCurrentIndex(level_map.get(current_level_name, 1))  # Default to INFO
    
    level_layout.addWidget(level_combo)
    level_layout.addStretch(1)
    logging_inner_layout.addLayout(level_layout)
    
    # Console logging checkbox
    console_check = QCheckBox("Enable console logging")
    console_check.setStyleSheet(checkbox_direct_style)
    console_check.setChecked(settings.value('logging/console_enabled', True, type=bool))
    console_check.setToolTip("Show log messages in the console")
    logging_inner_layout.addWidget(console_check)
    
    # File logging checkbox
    file_check = QCheckBox("Enable file logging")
    file_check.setStyleSheet(checkbox_direct_style)
    file_check.setChecked(settings.value('logging/file_enabled', True, type=bool))
    file_check.setToolTip("Save log messages to a file")
    logging_inner_layout.addWidget(file_check)
    
    # Log file location and open button
    log_file_layout = QHBoxLayout()
    log_file_label = QLabel("Log File:")
    log_file_label.setStyleSheet(LABEL_STYLE)
    log_file_layout.addWidget(log_file_label)
    
    # Import the function to get log file path
    from app.utils.logging_utils import get_log_file_path
    log_file_path = get_log_file_path()
    
    log_file_field = QLineEdit()
    log_file_field.setText(log_file_path)
    log_file_field.setReadOnly(True)
    log_file_field.setStyleSheet(LINEEDIT_STYLE)
    log_file_layout.addWidget(log_file_field)
    
    log_file_open_btn = QPushButton("Open")
    log_file_open_btn.setStyleSheet(BUTTON_STYLE)
    def open_log_file():
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        open_folder(log_dir)
    log_file_open_btn.clicked.connect(open_log_file)
    log_file_layout.addWidget(log_file_open_btn)
    
    logging_inner_layout.addLayout(log_file_layout)
    
    # Note about log settings
    logging_note_label = QLabel("Note: Log level changes take effect immediately. Use higher levels (Warning, Error) in production for better performance.")
    logging_note_label.setStyleSheet(f"color: {colors['secondary_text']}; font-style: italic;")
    logging_note_label.setWordWrap(True)
    logging_inner_layout.addWidget(logging_note_label)
    
    logging_layout.addWidget(logging_group)
    logging_layout.addStretch(1)
    
    # Add the new logging tab
    tabs.addTab(logging_tab, "Logging")

    # --- Save Preferences Logic --- 
    # (This function is called when OK is clicked)
    def save_preferences():
        # Save cache preferences (non-path related)
        try:
            save_cache_preferences()
        except Exception as e:
            print("DEBUG: Cache preferences save skipped (CachePreferences unavailable).")

        # Save logging preferences
        try:
            # Get the selected log level
            level_index = level_combo.currentIndex()
            level = level_combo.itemData(level_index)
            set_log_level(level)
            
            # Save console and file logging settings
            enable_console_logging(console_check.isChecked())
            enable_file_logging(file_check.isChecked())
        except Exception as e:
            print(f"ERROR: Failed to save logging preferences: {e}")
        
        print("DEBUG: Preferences saved (Cache settings saved, Data Root handled by QSettings).")
        dialog.accept()

    # Add the tabs to the main layout
    main_layout.addWidget(tabs)

    # Add buttons at the bottom
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(save_preferences)
    button_box.rejected.connect(dialog.reject)
    
    # Style the buttons individually for proper styling
    ok_button = button_box.button(QDialogButtonBox.Ok)
    cancel_button = button_box.button(QDialogButtonBox.Cancel)
    
    # Apply the accent button style to OK button
    ok_button.setStyleSheet(ACCENT_BUTTON_STYLE)
    
    # Apply regular button style to Cancel button
    cancel_button.setStyleSheet(BUTTON_STYLE)
    
    main_layout.addWidget(button_box)

    dialog.exec()
