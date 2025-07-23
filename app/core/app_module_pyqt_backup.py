#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Main Application Module - Refactored
Clean, modular architecture with organized managers
"""

import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QTimer

from app.core.main_window import MainWindowBase
from app.core.managers.ui_manager import UIManager
from app.core.managers.menu_manager import MenuManager
from app.core.managers.custom_options_manager import CustomOptionsManager

# Import existing functionality that we'll delegate to
from app.core.project_operations import handle_batch_create
from app.dialogs.dialog_windows_pyqt import show_preferences_dialog, show_batch_results
from app.core.import_export_manager import import_template
from app.utils.utils import save_config, open_folder
from app.constants import APP_VERSION_NUMBER

# --- Worker for background update check ---
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

# ---------------------------------------

class ProjectCreatorApp(MainWindowBase):
    """Main application class - Clean and modular"""
    
    def __init__(self):
        """Initialize the application with managers"""
        super().__init__()
        
        # Initialize managers
        self.ui_manager = UIManager(self)
        self.menu_manager = MenuManager(self)
        self.custom_options_manager = CustomOptionsManager(self)
        
        # Setup UI and connections
        self._setup_application()
        
        print("DEBUG: ProjectCreatorApp initialization complete")
    
    def _setup_application(self):
        """Setup the complete application"""
        # Setup UI
        self.ui_manager.setup_ui()
        
        # Create menu
        self.menu_manager.create_menu()
        
        # Update UI from config
        self.ui_manager.update_ui_from_config()
        
        # Connect signals
        self._connect_signals()
        
        # Update menus
        self.menu_manager.update_recent_projects_menu(self.recent_projects)
        self.menu_manager.update_recent_templates_menu(self.recent_templates)
    
    def _connect_signals(self):
        """Connect UI signals to handlers"""
        # Browse button
        if hasattr(self, 'browse_button'):
            self.browse_button.clicked.connect(self._browse_output_directory)
        
        # Create button
        if hasattr(self, 'create_button'):
            self.create_button.clicked.connect(self.process_batch_projects)
        
        # Template gallery selection
        if hasattr(self, 'template_gallery'):
            # Connect gallery selection to custom options check
            self.template_gallery.template_selected.connect(
                self.custom_options_manager.check_template_for_custom_options
            )
    
    # Essential methods for compatibility
    def _browse_output_directory(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)
            self.config["last_output_dir"] = directory
            save_config(self.config)
    
    def process_batch_projects(self):
        """Process batch project creation"""
        project_names = self.batch_text_edit.toPlainText().strip().split('\n')
        project_names = [name.strip() for name in project_names if name.strip()]
        
        if not project_names:
            QMessageBox.warning(self, "No Projects", "Please enter at least one project name.")
            return
        
        # Get output directory
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "No Output Directory", "Please select an output directory.")
            return
        
        # Handle batch creation
        self.batch_results = handle_batch_create(
            self, project_names, output_dir, self.template_manager, self.project_builder
        )
        
        if self.batch_results:
            show_batch_results(self, self.batch_results)
    
    def get_output_dir(self):
        """Get the current output directory"""
        return self.output_dir_input.text().strip() if hasattr(self, 'output_dir_input') else ""
    
    def get_current_output_dir(self, use_fallbacks=True):
        """Get current output directory with fallbacks"""
        output_dir = self.get_output_dir()
        if not output_dir and use_fallbacks:
            output_dir = os.path.expanduser("~/Desktop")
        return output_dir
    
    def show_status_message(self, message, message_type="info", duration=5000):
        """Show a status message in the status bar"""
        if hasattr(self, 'status_bar'):
            from app.ui.color_scheme_pyqt import colors
            
            if message_type == "error":
                self.status_bar.setStyleSheet(f"color: {colors['error']};")
            elif message_type == "success":
                self.status_bar.setStyleSheet(f"color: {colors['success']};")
            else:
                self.status_bar.setStyleSheet(f"color: {colors['text']};")
            
            self.status_bar.showMessage(message, duration)
            self.status_message_timer.start(duration)
    
    def _reset_status_bar(self):
        """Reset status bar to default state"""
        if hasattr(self, 'status_bar'):
            self.status_bar.clearMessage()
            self.status_bar.setStyleSheet("")
        self.status_message_timer.stop()
    
    def show_error(self, message):
        """Show an error message"""
        self.show_status_message(message, message_type="error")
    
    # Delegate methods to managers
    def check_template_for_custom_options(self, template_data):
        """Delegate to custom options manager"""
        return self.custom_options_manager.check_template_for_custom_options(template_data)
    
    def get_custom_values_from_widget(self):
        """Delegate to custom options manager"""
        return self.custom_options_manager.get_custom_values_from_widget()
    
    def reset_custom_options_widget(self):
        """Delegate to custom options manager"""
        return self.custom_options_manager.reset_custom_options_widget()
    
    def _check_custom_pattern_conflicts(self):
        """Delegate to custom options manager"""
        return self.custom_options_manager.check_custom_pattern_conflicts()
    
    def update_recent_menu(self):
        """Delegate to menu manager"""
        return self.menu_manager.update_recent_projects_menu(self.recent_projects)
    
    def update_recent_templates_menu(self):
        """Delegate to menu manager"""
        return self.menu_manager.update_recent_templates_menu(self.recent_templates)
    
    # Placeholder methods for compatibility (to be implemented as needed)
    def _create_template(self):
        """Create a new template"""
        from app.dialogs.template_creation_form import show_template_creation_form
        show_template_creation_form(self)
    
    def _manage_structures(self):
        """Manage template structures"""
        from app.core.structures_pyqt import manage_structures
        manage_structures(self)
    
    def _import_all(self):
        """Import templates and settings"""
        # Implementation delegated to import_export_manager
        pass
    
    def _export_all(self):
        """Export templates and settings"""
        # Implementation delegated to import_export_manager
        pass
    
    def check_for_updates(self, triggered_manually=False):
        """Check for application updates"""
        # Implementation delegated to update_manager
        pass
    
    def filter_templates(self, search_text):
        """Filter templates in gallery"""
        if hasattr(self, 'template_gallery'):
            self.template_gallery.filter_templates(search_text)
        print("DEBUG: UI setup complete")
        print("DEBUG: Updating UI from config...")
        self._update_ui_from_config()
        print("DEBUG: UI config update complete")
        
        # Connect signals
        self.template_updated.connect(self.trigger_template_updated)
        
        # Update UI elements
        self.update_recent_menu()
        self.update_recent_templates_menu()
        
        # Set up a timer to check for batch results, but don't start it yet
        self.batch_check_timer = QTimer(self)
        self.batch_check_timer.timeout.connect(self.check_batch_results)
        
        # Schedule initial update check
        self._initial_update_check()
        
        # Note: Window will be shown by main.py, not here
        
    def closeEvent(self, event):
        """Handle application close event - clean up resources"""
        # Call parent close event
        super().closeEvent(event)
    
    def _setup_ui(self):
        """Set up the main application UI"""
        print("DEBUG: Creating central widget...")
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        print("DEBUG: Creating menu bar...")
        # Create menu bar
        self.create_menu()
        print("DEBUG: Menu bar created")
        
        print("DEBUG: Creating status bar...")
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_message = QLabel("")
        self.status_bar.addWidget(self.status_message)
        
        # Configure status bar for proper text display
        self.status_bar.setStyleSheet("""
            QStatusBar { 
                padding-left: 8px; 
                min-height: 24px;
            }
            QStatusBar::item {
                border: none;
                padding-left: 8px;
            }
        """)
        print("DEBUG: Status bar created")
        
        print("DEBUG: Setting minimum window size...")
        # Set minimum window size to ensure all elements are visible
        self.setMinimumSize(1000, 600)
        
        print("DEBUG: Creating main splitter...")
        # Add main horizontal splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        print("DEBUG: Main splitter created")
        
        print("DEBUG: Creating left panel (CardFrame)...")
        # Create left panel with project settings
        self.left_panel = CardFrame()
        self.left_layout = self.left_panel.main_layout
        print("DEBUG: Left panel created")
        
        # Project settings header
        self.settings_header = QLabel("Project Settings")
        self.settings_header.setStyleSheet(f"font-weight: bold; font-size: 14px; border: none; color: {colors.get('text_subtle', '#A0A0A0')};")
        self.left_layout.addWidget(self.settings_header)
        
        # Batch project input area - integrated directly into the main UI
        self.batch_projects_header = QLabel("Enter Project Names")
        self.batch_projects_header.setStyleSheet(f"font-weight: bold; font-size: 13px; border: none; color: {colors.get('text_focus', '#FFFFFF')};")
        self.left_layout.addWidget(self.batch_projects_header)
        
        # Instructions for batch projects
        instruction_base_color = colors.get('text', '#CCCCCC') # Brighter base grey
        highlight_color = colors.get('text_focus', '#FFFFFF') # White for "template"

        instruction_html = (
            f"<span style='color: {instruction_base_color};'>Select a <span style='color: {highlight_color}; font-weight: bold;'>template</span> on the right to use for project creation.</span><br>"
            f"<span style='color: {instruction_base_color};'>Enter one project name per line. You can also separate names with commas or semicolons.</span><br>"
            f"<span style='color: {instruction_base_color};'>All projects will be created using the selected <span style='color: {highlight_color}; font-weight: bold;'>template</span> and output location.</span>"
        )
        self.batch_instructions = QLabel(instruction_html)
        self.batch_instructions.setTextFormat(Qt.TextFormat.RichText) # Ensure HTML is rendered
        self.batch_instructions.setWordWrap(True)
        self.batch_instructions.setStyleSheet(
            f"background-color: {colors.get('info_bg_transparent', 'rgba(46, 59, 78, 0.7)')}; "
            f"border: none; " # Outline removed
            f"border-radius: 4px; "
            f"padding: 8px; "
            f"color: {instruction_base_color};" # Base text color set by the HTML span
        )
        self.left_layout.addWidget(self.batch_instructions)
        
        # Create dummy structure_combo property for compatibility
        # This ensures other parts of the code that reference it will still work
        self.structure_combo = QComboBox()
        self.structure_combo.hide()  # Hide it from view
        
        # Create a stretching middle section for the batch text edit
        middle_container = QWidget()
        middle_layout = QVBoxLayout(middle_container)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # Text input area for batch projects - this should expand
        self.batch_text_edit = QTextEdit()
        self.batch_text_edit.setPlaceholderText("Project 1\nProject 2\nProject 3")
        self.batch_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 8px;
                font-family: '{UI_FONT}';
                font-size: 13px;
            }}
        """)
        # Set size policy to make text edit expand
        self.batch_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        middle_layout.addWidget(self.batch_text_edit)
        
        # Add the expandable middle section
        self.left_layout.addWidget(middle_container, 1)  # Use stretch factor of 1
        
        print("DEBUG: Creating AnimatedCustomOptionsWidget...")
        # Add animated custom options widget (initially hidden)
        from app.ui.custom_options_widgets import AnimatedCustomOptionsWidget
        self.custom_options_widget = AnimatedCustomOptionsWidget(self)
        print("DEBUG: AnimatedCustomOptionsWidget created")
        self.custom_options_widget.hide()
        self.left_layout.addWidget(self.custom_options_widget)
        
        # Add versioning options section
        versioning_container = QWidget()
        versioning_layout = QVBoxLayout(versioning_container)
        versioning_layout.setContentsMargins(0, 10, 0, 0)
        
        # Enable versioning checkbox
        self.enable_versioning = QCheckBox("Create sequence variations for each project")
        self.enable_versioning.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                font-weight: bold;
                spacing: 8px;
                padding: 8px 4px;
                min-height: 20px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['card_bg']};
                margin-right: 4px;
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {colors['accent']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
            }}
        """)
        self.enable_versioning.toggled.connect(self._toggle_versioning_options)
        versioning_layout.addWidget(self.enable_versioning)
        
        # Versioning options (initially hidden)
        self.versioning_options = QWidget()
        versioning_options_layout = QVBoxLayout(self.versioning_options)
        versioning_options_layout.setContentsMargins(20, 8, 0, 0)  # Indent options with proper spacing
        versioning_options_layout.setSpacing(8)  # Consistent 8px spacing
        
        # Create a horizontal container for type and position
        type_position_row = QWidget()
        type_position_layout = QHBoxLayout(type_position_row)
        type_position_layout.setContentsMargins(0, 0, 0, 0)
        type_position_layout.setSpacing(16)  # 16px spacing between controls
        
        # Sequence type
        type_container = QWidget()
        type_layout = QVBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(4)  # 4px spacing between label and control
        
        type_label = QLabel("Type:")
        type_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        type_layout.addWidget(type_label)
        
        self.sequence_type = QComboBox()
        self.sequence_type.addItems(["Date Sequences", "Version Numbers", "Sequential Numbers"])
        self.sequence_type.setMinimumWidth(180)  # Minimum width to prevent text cutoff
        self.sequence_type.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.sequence_type.currentTextChanged.connect(self._update_versioning_options)
        
        # Apply consistent styling using the utility function
        self.sequence_type.setStyleSheet(COMBOBOX_STYLE)
        self.sequence_type.setMinimumWidth(180)  # Minimum width to prevent text cutoff
        self.sequence_type.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.sequence_type.currentTextChanged.connect(self._update_versioning_options)
        
        print("DEBUG: Applying hover delegate to sequence_type...")
        # Apply hover delegate for proper hover effects
        from app.ui.custom_delegates import apply_hover_delegate
        apply_hover_delegate(self.sequence_type)
        print("DEBUG: Hover delegate applied to sequence_type")
        
        type_layout.addWidget(self.sequence_type)
        
        type_position_layout.addWidget(type_container)
        
        # Position
        position_container = QWidget()
        position_layout = QVBoxLayout(position_container)
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.setSpacing(4)  # 4px spacing between label and control
        
        position_label = QLabel("Position:")
        position_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        position_layout.addWidget(position_label)
        
        self.name_position = QComboBox()
        self.name_position.addItems(["Suffix", "Prefix"])
        self.name_position.setMinimumWidth(100)  # Minimum width
        self.name_position.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        
        self.name_position.setStyleSheet(COMBOBOX_STYLE)
        
        # Apply hover delegate for proper hover effects
        apply_hover_delegate(self.name_position)
        
        position_layout.addWidget(self.name_position)
        
        type_position_layout.addWidget(position_container)
        
        # Add stretch to keep controls on the left
        type_position_layout.addStretch()
        
        versioning_options_layout.addWidget(type_position_row)
        
        # Create container for all option widgets
        options_container = QWidget()
        options_container_layout = QVBoxLayout(options_container)
        options_container_layout.setContentsMargins(0, 10, 0, 0)
        options_container_layout.setSpacing(0)
        
        # Date options (shown when Date Sequences selected)
        self.date_options = QWidget()
        date_main_layout = QVBoxLayout(self.date_options)
        date_main_layout.setContentsMargins(0, 5, 0, 0)
        date_main_layout.setSpacing(8)
        
        # First row: Start Date and Count
        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.setSpacing(16)  # 16px spacing between controls
        
        # Start Date
        start_date_container = QWidget()
        start_date_layout = QVBoxLayout(start_date_container)
        start_date_layout.setContentsMargins(0, 0, 0, 0)
        start_date_layout.setSpacing(4)  # 4px spacing between label and control
        
        start_date_label = QLabel("Start Date:")
        start_date_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        start_date_layout.addWidget(start_date_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)  # Enable calendar popup
        
        # Apply standardized calendar styling
        def apply_calendar_style():
            calendar = self.start_date.calendarWidget()
            if calendar:
                # Set weekend text format to be dimmer grey
                weekend_format = QTextCharFormat()
                weekend_format.setForeground(QColor('#888888'))  # Dimmer grey for weekends
                calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
                calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
                
                # Set weekday text format to white  
                weekday_format = QTextCharFormat()
                weekday_format.setForeground(QColor(colors['text']))
                for day in [Qt.DayOfWeek.Monday, Qt.DayOfWeek.Tuesday, Qt.DayOfWeek.Wednesday, 
                           Qt.DayOfWeek.Thursday, Qt.DayOfWeek.Friday]:
                    calendar.setWeekdayTextFormat(day, weekday_format)
        
        # Connect to show calendar styling when popup opens
        self.start_date.dateChanged.connect(lambda: QTimer.singleShot(10, apply_calendar_style))
        
        # Apply initial styling
        QTimer.singleShot(100, apply_calendar_style)
        
        self.start_date.setFixedWidth(120)
        self.start_date.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.start_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 4px;
                min-height: 22px;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {colors['border']};
                background-color: {colors['card_bg_alt']};
            }}
            QDateEdit::down-arrow {{
                image: none;
                border: 1px solid {colors['text']};
                width: 3px;
                height: 3px;
                background-color: {colors['text']};
            }}
        """)
        
        start_date_layout.addWidget(self.start_date)
        first_row_layout.addWidget(start_date_container)
        
        # Count
        count_container = QWidget()
        count_layout = QVBoxLayout(count_container)
        count_layout.setContentsMargins(0, 0, 0, 0)
        count_layout.setSpacing(4)  # 4px spacing between label and control
        
        count_label = QLabel("Count:")
        count_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        count_layout.addWidget(count_label)
        
        self.date_count = QSpinBox()
        self.date_count.setRange(1, 1000)
        self.date_count.setValue(5)
        self.date_count.setMinimumWidth(80)
        self.date_count.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.date_count.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 4px;
            }}
        """)
        count_layout.addWidget(self.date_count)
        first_row_layout.addWidget(count_container)
        
        first_row_layout.addStretch()
        date_main_layout.addWidget(first_row)
        
        # Second row: Interval and Days/Weeks/Months
        second_row = QWidget()
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setContentsMargins(0, 0, 0, 0)
        second_row_layout.setSpacing(16)  # 16px spacing between controls
        
        # Interval
        interval_container = QWidget()
        interval_layout = QVBoxLayout(interval_container)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(4)  # 4px spacing between label and control
        
        interval_label = QLabel("Interval:")
        interval_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        interval_layout.addWidget(interval_label)
        
        self.date_interval = QSpinBox()
        self.date_interval.setRange(1, 30)
        self.date_interval.setValue(1)
        self.date_interval.setMinimumWidth(80)
        self.date_interval.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.date_interval.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 4px;
            }}
        """)
        interval_layout.addWidget(self.date_interval)
        second_row_layout.addWidget(interval_container)
        
        # Interval type (Days/Weeks/Months)
        interval_type_container = QWidget()
        interval_type_layout = QVBoxLayout(interval_type_container)
        interval_type_layout.setContentsMargins(0, 0, 0, 0)
        interval_type_layout.setSpacing(4)  # 4px spacing between label and control
        
        interval_type_label = QLabel("Unit:")
        interval_type_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        interval_type_layout.addWidget(interval_type_label)
        
        self.date_interval_type = QComboBox()
        self.date_interval_type.addItems(["Days", "Weeks", "Months"])
        self.date_interval_type.setMinimumWidth(100)
        self.date_interval_type.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.date_interval_type.setStyleSheet(COMBOBOX_STYLE)
        
        # Apply hover delegate for proper hover effects
        apply_hover_delegate(self.date_interval_type)
        
        interval_type_layout.addWidget(self.date_interval_type)
        second_row_layout.addWidget(interval_type_container)
        
        second_row_layout.addStretch()
        date_main_layout.addWidget(second_row)
        
        # Third row: Format
        format_row = QWidget()
        format_row_layout = QVBoxLayout(format_row)
        format_row_layout.setContentsMargins(0, 0, 0, 0)
        format_row_layout.setSpacing(4)  # 4px spacing between label and control
        
        format_label = QLabel("Format:")
        format_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        format_row_layout.addWidget(format_label)
        
        self.date_format = QComboBox()
        self.date_format.addItems([
            "YYYYMMDD (20250115)",
            "YYYY_MM_DD (2025_01_15)",
            "MM_DD_YYYY (01_15_2025)",
            "DD_MM_YYYY (15_01_2025)",
            "YYYY-MM-DD (2025-01-15)",
            "MM-DD-YYYY (01-15-2025)",
            "DD-MM-YYYY (15-01-2025)",
            "YYYY.MM.DD (2025.01.15)",
            "MM.DD.YYYY (01.15.2025)",
            "DD.MM.YYYY (15.01.2025)",
            "YYYY MM DD (2025 01 15)",
            "MM DD YYYY (01 15 2025)",
            "DD MM YYYY (15 01 2025)"
        ])
        self.date_format.setMinimumWidth(240)  # Ensure sufficient width for format examples
        self.date_format.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.date_format.setStyleSheet(COMBOBOX_STYLE)
        
        # Apply hover delegate for proper hover effects
        apply_hover_delegate(self.date_format)
        
        format_row_layout.addWidget(self.date_format)
        date_main_layout.addWidget(format_row)
        
        # Version options (shown when Version Numbers selected)
        self.version_options = QWidget()
        version_main_layout = QHBoxLayout(self.version_options)
        version_main_layout.setContentsMargins(0, 5, 0, 0)
        version_main_layout.setSpacing(15)
        
        # Count
        count_container = QWidget()
        count_layout = QHBoxLayout(count_container)
        count_layout.setContentsMargins(0, 0, 0, 0)
        count_layout.setSpacing(5)
        
        count_label = QLabel("Count:")
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        count_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        count_label.setFixedWidth(60)
        count_layout.addWidget(count_label)
        
        self.version_count = QSpinBox()
        self.version_count.setRange(1, 1000)
        self.version_count.setValue(5)
        self.version_count.setFixedWidth(80)
        self.version_count.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.version_count.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 4px;
            }}
        """)
        count_layout.addWidget(self.version_count)
        version_main_layout.addWidget(count_container)
        
        # Format
        format_container = QWidget()
        format_layout = QHBoxLayout(format_container)
        format_layout.setContentsMargins(0, 0, 0, 0)
        format_layout.setSpacing(5)
        
        format_label = QLabel("Format:")
        format_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        format_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        format_label.setFixedWidth(60)
        format_layout.addWidget(format_label)
        
        self.version_format = QComboBox()
        self.version_format.addItems([
            "V1, V2, V3...",
            "v1, v2, v3...",
            "Ver1, Ver2, Ver3...",
            "Version1, Version2, Version3..."
        ])
        self.version_format.setFixedWidth(180)
        self.version_format.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.version_format.setStyleSheet(COMBOBOX_STYLE)
        
        # Apply hover delegate for proper hover effects
        apply_hover_delegate(self.version_format)
        
        format_layout.addWidget(self.version_format)
        version_main_layout.addWidget(format_container)
        
        version_main_layout.addStretch()
        
        # Number options (shown when Sequential Numbers selected)
        self.number_options = QWidget()
        number_main_layout = QVBoxLayout(self.number_options)
        number_main_layout.setContentsMargins(0, 5, 0, 0)
        number_main_layout.setSpacing(8)
        
        # First row: Start and Count
        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.setSpacing(15)
        
        # Start
        start_container = QWidget()
        start_layout = QHBoxLayout(start_container)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(5)
        
        start_label = QLabel("Start:")
        start_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        start_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        start_label.setFixedWidth(60)
        start_layout.addWidget(start_label)
        
        self.number_start = QSpinBox()
        self.number_start.setRange(1, 999)
        self.number_start.setValue(1)
        self.number_start.setFixedWidth(80)
        self.number_start.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.number_start.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 4px;
            }}
        """)
        start_layout.addWidget(self.number_start)
        first_row_layout.addWidget(start_container)
        
        # Count
        count_container = QWidget()
        count_layout = QHBoxLayout(count_container)
        count_layout.setContentsMargins(0, 0, 0, 0)
        count_layout.setSpacing(5)
        
        count_label = QLabel("Count:")
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        count_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        count_label.setFixedWidth(60)
        count_layout.addWidget(count_label)
        
        self.number_count = QSpinBox()
        self.number_count.setRange(1, 1000)
        self.number_count.setValue(5)
        self.number_count.setFixedWidth(80)
        self.number_count.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.number_count.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 4px;
            }}
        """)
        count_layout.addWidget(self.number_count)
        first_row_layout.addWidget(count_container)
        
        first_row_layout.addStretch()
        number_main_layout.addWidget(first_row)
        
        # Second row: Format
        format_row = QWidget()
        format_row_layout = QHBoxLayout(format_row)
        format_row_layout.setContentsMargins(0, 0, 0, 0)
        format_row_layout.setSpacing(5)
        
        format_label = QLabel("Format:")
        format_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        format_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        format_label.setFixedWidth(60)
        format_row_layout.addWidget(format_label)
        
        self.number_format = QComboBox()
        self.number_format.addItems([
            "No padding (1, 2, 3...)",
            "2 digits (01, 02, 03...)",
            "3 digits (001, 002, 003...)"
        ])
        self.number_format.setCurrentText("3 digits (001, 002, 003...)")
        self.number_format.setFixedWidth(200)
        self.number_format.setMinimumHeight(32)  # Minimum height to prevent arrow cutoff
        self.number_format.setStyleSheet(COMBOBOX_STYLE)
        
        # Apply hover delegate for proper hover effects
        apply_hover_delegate(self.number_format)
        
        format_row_layout.addWidget(self.number_format)
        
        format_row_layout.addStretch()
        number_main_layout.addWidget(format_row)
        
        # Add all option widgets to the options container
        options_container_layout.addWidget(self.date_options)
        options_container_layout.addWidget(self.version_options)
        options_container_layout.addWidget(self.number_options)
        
        # Add options container to main versioning layout
        versioning_layout.addWidget(self.versioning_options)
        versioning_layout.addWidget(options_container)
        
        # Store reference to options container for visibility control
        self.options_container = options_container
        
        # Initially hide versioning options
        self.versioning_options.hide()
        self.options_container.hide()
        self._update_versioning_options()  # Set initial state
        
        # Setup animation for versioning options (after initial hide)
        self._setup_versioning_animation()
        
        self.left_layout.addWidget(versioning_container)
        
        # Create a fixed bottom section for output directory and create button
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 10, 0, 0)  # Add some top margin for separation
        
        # Output directory
        self.output_dir_layout = QHBoxLayout()
        # Make sure components don't wrap to next line by setting some key properties
        self.output_dir_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        # Add margins to the output dir layout to create space on both sides
        self.output_dir_layout.setContentsMargins(10, 0, 10, 0)  # Left, top, right, bottom
        self.output_dir_layout.setSpacing(5)  # Space between elements
        
        self.output_dir_label = QLabel("Output Directory:")
        self.output_dir_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        # Make label match app background and have no border
        self.output_dir_label.setStyleSheet(f"""
            QLabel {{
                background-color: {APP_COLORS['bg']};
                border: none;
                padding-left: 5px;
            }}
        """)
        
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Select output directory...")
        self.output_dir_input.setReadOnly(True)
        # Remove the minimum width setting so it doesn't force wrapping
        # self.output_dir_input.setMinimumWidth(350)
        # Keep border on path field but make its background match main bg and reduce height
        self.output_dir_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {APP_COLORS['bg']};
                color: {APP_COLORS['text']};
                border: 1px solid {APP_COLORS['border']};
                padding: 5px;
                min-height: 22px;
            }}
        """)
        
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(self.get_output_dir)
        # Make sure the browse button doesn't get too large
        self.output_dir_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Custom style for the browse button - match height with input field
        self.output_dir_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #383838;
                color: #CCCCCC;
                border: 1px solid {APP_COLORS['border']};
                padding: 5px 10px;
                border-radius: 3px;
                min-height: 22px;
                margin-right: 5px;
            }}
            QPushButton:hover {{
                background-color: #454545;
                border: 1px solid #2C4F76;
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #2C4F76;
                color: white;
            }}
        """)
        
        # Create a layout that won't wrap components
        self.output_dir_layout.setSpacing(5)
        self.output_dir_layout.addWidget(self.output_dir_label)
        self.output_dir_layout.addWidget(self.output_dir_input, 1)  # Add stretch factor to take more space
        self.output_dir_layout.addWidget(self.output_dir_btn)
        bottom_layout.addLayout(self.output_dir_layout)
        
        # Remove the separator line - just add a small spacing
        bottom_layout.addSpacing(10)
        
        # Batch create project button
        self.batch_create_btn = QPushButton("Create Project(s)")
        self.batch_create_btn.clicked.connect(self.process_batch_projects)
        self.batch_create_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        # Set minimum height for the button to make it more prominent
        self.batch_create_btn.setMinimumHeight(40)
        bottom_layout.addWidget(self.batch_create_btn)
        
        # Add the bottom container to the main layout (fixed size, won't stretch)
        self.left_layout.addWidget(bottom_container, 0)  # Use stretch factor of 0
        
        # Create right panel with template gallery
        self.right_panel = QWidget()
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        print("DEBUG: Creating TemplateGallery...")
        # Create template gallery
        self.template_gallery = TemplateGallery(app=self)
        print("DEBUG: TemplateGallery created successfully")
        self.right_layout.addWidget(self.template_gallery)
        
        # Connect template selection signal to check for custom options
        self.template_gallery.template_selected.connect(self.check_template_for_custom_options)
        
        # Apply theme to template gallery
        apply_dark_theme_to_template_gallery(self.template_gallery)
        
        # Add panels to splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set minimum widths for panels to ensure they're always usable
        self.left_panel.setMinimumWidth(280)
        self.right_panel.setMinimumWidth(450)  # Ensure right panel buttons remain visible
        
        # Initial sizes - make left project area 6% bigger than original
        self.main_splitter.setSizes([424, 876])  # Left side 6% bigger than original 400, right side adjusted
        self.main_splitter.setHandleWidth(6)  # Standard handle width
        
        # Allow panels to be collapsed to their minimum size but not further
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, True)
        
        # Apply initial config
        self._update_ui_from_config()
        
        # Add Update Notification Banner (initially hidden)
        self.update_banner = UpdateNotificationBanner()
        self.main_layout.insertWidget(0, self.update_banner) # Insert at the top
        
    def _update_ui_from_config(self):
        """Update UI elements based on loaded configuration"""
        # Load last output directory if available
        last_output_dir = self.config.get("last_output_dir", "")
        if last_output_dir and hasattr(self, 'output_dir_input'):
            self.output_dir_input.setText(last_output_dir)
            
        # Load other UI elements from config as needed
        # (like structure selection, template location, etc.)
        if hasattr(self, 'structure_combo'):
            # Attempt to set the last used structure if available
            last_structure = self.config.get("last_structure", "Default")
            idx = self.structure_combo.findText(last_structure)
            if idx >= 0:
                self.structure_combo.setCurrentIndex(idx)
        
    def set_app_icon(self):
        """Set the application icon for this window"""
        app_icon = self.get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
            
    def center_window(self):
        """Center the window on the screen"""
        qr = self.frameGeometry()
        screen = QApplication.primaryScreen()
        cp = screen.availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def create_menu(self):
        """Create application menus that are OS-aware (macOS vs Windows)"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New Template action (new)
        new_template_action = QAction("New Template...", self)
        new_template_action.triggered.connect(self._create_template)
        file_menu.addAction(new_template_action)
        
        file_menu.addSeparator()
        
        # Import Template Package action (ZIP import)
        import_template_package_action = QAction("Import Template...", self)
        import_template_package_action.triggered.connect(lambda: import_template(self))
        file_menu.addAction(import_template_package_action)
        
        # Export/Import Settings section
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = QMenu("Export", self)
        
        # Export all settings and templates
        export_all_action = QAction("All Settings and Templates...", self)
        export_all_action.triggered.connect(self._export_all)
        export_menu.addAction(export_all_action)
        
        # Export settings only
        export_settings_action = QAction("Settings Only...", self)
        export_settings_action.triggered.connect(self._export_settings)
        export_menu.addAction(export_settings_action)
        
        # Add export menu to file menu
        file_menu.addMenu(export_menu)
        
        # Import submenu
        import_menu = QMenu("Import", self)
        
        # Import all settings and templates
        import_all_action = QAction("All Settings and Templates...", self)
        import_all_action.triggered.connect(self._import_all)
        import_menu.addAction(import_all_action)
        
        # Import settings only
        import_settings_action = QAction("Settings Only...", self)
        import_settings_action.triggered.connect(self._import_settings)
        import_menu.addAction(import_settings_action)
        
        # Add import menu to file menu
        file_menu.addMenu(import_menu)
        
        file_menu.addSeparator()
        
        # Recent projects menu
        self.recent_menu = QMenu("Recent Projects", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()
        
        # Clear Recent Projects action
        clear_recent_action = QAction("Clear Recent Projects", self)
        clear_recent_action.triggered.connect(lambda: clear_recent_projects(self))
        file_menu.addAction(clear_recent_action)
        
        file_menu.addSeparator()
        
        # Recent templates menu
        self.recent_templates_menu = QMenu("Recent Templates", self)
        file_menu.addMenu(self.recent_templates_menu)
        self.update_recent_templates_menu()
        
        # Clear Recent Templates action
        clear_recent_templates_action = QAction("Clear Recent Templates", self)
        clear_recent_templates_action.triggered.connect(lambda: clear_recent_templates(self))
        file_menu.addAction(clear_recent_templates_action)
        
        # Don't show Exit on macOS as it's handled by the system
        if platform.system() != "Darwin":  # Not macOS
            file_menu.addSeparator()
            
            # Exit action
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Preferences action - use standard macOS naming convention on Mac
        if platform.system() == "Darwin":  # macOS
            preferences_action = QAction("Preferences...", self)
            # Set shortcut for macOS (Command+,)
            preferences_action.setShortcut("Ctrl+,")
        else:
            preferences_action = QAction("Settings...", self)
            # Set shortcut for Windows/Linux
            preferences_action.setShortcut("Ctrl+P") 
            
        preferences_action.triggered.connect(lambda: show_preferences_dialog(self))
        edit_menu.addAction(preferences_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Refresh Template Gallery
        refresh_gallery_action = QAction("Refresh Template Gallery", self)
        refresh_gallery_action.triggered.connect(lambda: self.template_gallery.populate_gallery())
        view_menu.addAction(refresh_gallery_action)
        
        # Help menu
        self.help_menu = menubar.addMenu("Help")
        
        # Comprehensive user guide
        tutorial_action = QAction("User Guide", self)
        tutorial_action.triggered.connect(lambda: show_tutorial(self))
        self.help_menu.addAction(tutorial_action)
        
        # About action
        self.about_action = self.help_menu.addAction("About Echelon")
        self.about_action.triggered.connect(self.show_about_dialog)
        
        # Update Checker action
        self.update_action = self.help_menu.addAction("Check for Updates...")
        self.update_action.triggered.connect(lambda: self.check_for_updates(triggered_manually=True))
        # Add separator before about
        self.help_menu.insertSeparator(self.about_action)
    
    def filter_templates(self, search_text):
        """Filter templates based on search text"""
        # Template gallery handles its own filtering
        pass
        
    def update_recent_templates_gallery(self):
        """Update the recent templates gallery section"""
        # Trigger template gallery to update
        if hasattr(self, 'template_gallery'):
            self.template_gallery.populate_gallery()
        
    def get_output_dir(self):
        """Open file dialog to select output directory"""
        dialog = QFileDialog(self, "Select Output Directory")
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        initial_dir = self.output_dir_input.text() if hasattr(self, 'output_dir_input') else ""
        dialog.setDirectory(initial_dir)

        # Initialize directory to None before the dialog executes
        directory = None
        
        if dialog.exec():
            directory = dialog.selectedFiles()[0]
            # Update the output directory entry
            if hasattr(self, 'output_dir_input'):
                self.output_dir_input.setText(directory)
            
            # Save to config
            self.config["last_output_dir"] = directory
            save_config(self.config)
            
            # Create a security-scoped bookmark for macOS App Store compatibility
            if platform.system() == "Darwin":
                try:
                    from app.utils.security_bookmarks import create_bookmark
                    create_bookmark(directory)
                except ImportError:
                    print("WARNING: Could not import security_bookmarks module.")
                except Exception as e:
                    print(f"ERROR: Failed to create security-scoped bookmark: {e}")
            
        return directory  # Return the selected directory or None if cancelled
    
    def get_current_output_dir(self, use_fallbacks=True):
        """Get the current output directory from the entry field
        
        Args:
            use_fallbacks: If True, will use fallbacks (config, default path, desktop)
                          If False, will only return a directory if explicitly set by user
        
        Returns:
            str: The output directory path, or None if not set and use_fallbacks is False
        """
        # First check if user has explicitly set a directory in the UI
        if hasattr(self, 'output_dir_input') and self.output_dir_input:
            output_dir = self.output_dir_input.text().strip()
            if output_dir:
                # On macOS, use security-scoped bookmarks if available
                if platform.system() == "Darwin":
                    try:
                        from app.utils.security_bookmarks import BookmarkAccessContext
                        # Use a context manager to access the bookmark
                        with BookmarkAccessContext(output_dir):
                            # Ensure the directory exists
                            try:
                                if not os.path.exists(output_dir):
                                    os.makedirs(output_dir, exist_ok=True)
                            except Exception as e:
                                print(f"Warning: Could not create output directory: {e}")
                    except ImportError:
                        print("WARNING: Could not import security_bookmarks module.")
                        # Fall back to regular directory access
                        try:
                            if not os.path.exists(output_dir):
                                os.makedirs(output_dir, exist_ok=True)
                        except Exception as e:
                            print(f"Warning: Could not create output directory: {e}")
                else:
                    # Regular directory access for non-macOS platforms
                    try:
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir, exist_ok=True)
                    except Exception as e:
                        print(f"Warning: Could not create output directory: {e}")
                
                return output_dir
        
        # If no explicit directory and fallbacks are disabled, return None
        if not use_fallbacks:
            return None
            
        # If fallbacks enabled, try using last directory from config
        if hasattr(self, 'config') and 'last_output_dir' in self.config:
            output_dir = self.config['last_output_dir']
            if output_dir and os.path.exists(output_dir):
                return output_dir
                
        # Fall back to default paths if available
        if hasattr(self, 'default_output_path') and self.default_output_path:
            return self.default_output_path
            
        # Last resort - use desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        return desktop_path
        
    def update_recent_menu(self):
        """Update the recent projects menu"""
        # Clear existing items
        self.recent_menu.clear()
        
        # Add recent projects
        if not self.recent_projects:
            no_recent_action = QAction("No Recent Projects", self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
        else:
            # Check if recent_projects is a list or dict
            if isinstance(self.recent_projects, list):
                projects_list = self.recent_projects
            elif isinstance(self.recent_projects, dict):
                # If it's a dict, we'll extract the paths
                projects_list = list(self.recent_projects.values()) if self.recent_projects else []
            else:
                # Default empty list for any other type
                projects_list = []
            
            # Add each recent project
            for project_path in projects_list:
                if isinstance(project_path, str):
                    project_name = os.path.basename(project_path)
                    action = QAction(f"{project_name} ({truncate_path(project_path)})", self)
                    action.triggered.connect(lambda checked=False, p=project_path: open_recent_project(self, p))
                    self.recent_menu.addAction(action)
    
    def update_recent_templates_menu(self):
        """Update the recent templates menu"""
        # Clear existing items
        self.recent_templates_menu.clear()
        
        # Add recent templates
        if not self.recent_templates:
            no_recent_action = QAction("No Recent Templates", self)
            no_recent_action.setEnabled(False)
            self.recent_templates_menu.addAction(no_recent_action)
        else:
            # Check if recent_templates is a list or dict
            if isinstance(self.recent_templates, list):
                templates_list = self.recent_templates
            elif isinstance(self.recent_templates, dict):
                # If it's a dict, we'll extract the paths
                templates_list = list(self.recent_templates.values()) if self.recent_templates else []
            else:
                # Default empty list for any other type
                templates_list = []
            
            # Add each recent template
            for template_path in templates_list:
                if isinstance(template_path, str):
                    template_name = os.path.basename(template_path)
                    action = QAction(f"{template_name} ({truncate_path(template_path)})", self)
                    action.triggered.connect(lambda checked=False, t=template_path: use_recent_template(self, t))
                    self.recent_templates_menu.addAction(action)
    
    def trigger_template_updated(self):
        """Handle template updated signal"""
        # Update UI elements that depend on template data
        pass
    
    def show_status_message(self, message, message_type="info", duration=5000):
        """Show a status message in the status bar"""
        # Stop any existing timer
        self.status_message_timer.stop()
        
        # Set message style based on type
        base_style = """
            QStatusBar { 
                padding-left: 8px; 
                min-height: 24px;
            }
            QStatusBar::item {
                border: none;
                padding-left: 8px;
            }
        """
        
        if message_type == "success":
            style = base_style + f"QStatusBar {{ background-color: {colors['success']}; color: {colors['success_text']}; }}"
        elif message_type == "error":
            style = base_style + f"QStatusBar {{ background-color: {colors['error']}; color: white; }}"
        elif message_type == "warning":
            style = base_style + f"QStatusBar {{ background-color: {colors['warning']}; color: black; }}"
        else:  # info
            style = base_style + f"QStatusBar {{ background-color: {colors['accent']}; color: white; }}"
        
        # Set status bar message and style
        self.status_bar.setStyleSheet(style)
        self.status_bar.showMessage(message)
        
        # Start timer to clear message after duration
        if duration > 0:
            self.status_message_timer.start(duration)
    
    def _reset_status_bar(self):
        """Reset the status bar to its default state"""
        # Stop the timer
        self.status_message_timer.stop()
        
        # Clear message and reset style
        self.status_bar.clearMessage()
        
        # Reset to default style while maintaining proper padding
        base_style = """
            QStatusBar { 
                padding-left: 8px; 
                min-height: 24px;
                background-color: """ + colors['card_bg'] + """; 
                color: """ + colors['text'] + """;
            }
            QStatusBar::item {
                border: none;
                padding-left: 8px;
            }
        """
        self.status_bar.setStyleSheet(base_style)
    
    def handle_update_available(self, version_info):
        """Displays a message box when an update is found."""
        # version_info is the full dict from get_latest_version_info
        new_v_num_str = version_info.get('versionNumber', 'Unknown')
        new_b_num_str = version_info.get('buildNumber', 'N/A') # buildNumber can be None
        new_r_stage_str = version_info.get('releaseStage', 'Unknown')
        
        actual_download_url = "https://www.cr2creative.com/downloads.html"
        release_notes_text = version_info.get('releaseNotes', 'No release notes provided.')
        
        # print(f"DEBUG Update Dialog: Release notes content: '{release_notes_text[:100]}...' if release_notes_text else 'None'")

        # Current version display
        current_display_version_str = f"{APP_VERSION_NUMBER} (Build {CURRENT_BUILD_NUMBER_CONST})"

        # New available version display string as per requirement
        # Example: "Update Available: Echelon Version 1.2.0 (Beta, Build 275)"
        # Or if build number is None/empty: "Echelon Version 1.2.0 (Beta)"
        build_display_part = f", Build {new_b_num_str}" if new_b_num_str and str(new_b_num_str).strip() else ""
        available_version_display_str = f"{new_v_num_str} ({new_r_stage_str}{build_display_part})"

        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QFrame
        
        custom_dialog = QDialog(self)
        custom_dialog.setWindowTitle("Update Available")
        custom_dialog.setMinimumWidth(500)
        
        main_layout = QVBoxLayout(custom_dialog)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        info_container = QFrame()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        
        info_label = QLabel(
            f"<p>An update is available for Echelon!</p>"
            f"<p><b>New Version: {available_version_display_str}</b></p>"
            f"<p>You are currently running: {current_display_version_str}</p>"
            f"<p>Would you like to visit the download page now?</p>"
        )
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        # Add info container to main layout
        main_layout.addWidget(info_container)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"background-color: {colors['border']}; margin: 5px 0px;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Create a text edit for release notes (initially hidden)
        notes_container = QFrame()
        notes_container.setVisible(False)  # Initially hidden
        notes_layout = QVBoxLayout(notes_container)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(8)
        
        # Add title for release notes
        notes_title = QLabel("## Release Notes")
        notes_title.setStyleSheet(f"font-weight: bold; color: {colors['accent']};")
        notes_layout.addWidget(notes_title)
        
        notes_edit = QTextEdit()
        notes_edit.setReadOnly(True)
        notes_edit.setPlainText(release_notes_text if release_notes_text and release_notes_text.strip() and release_notes_text != 'No release notes provided.' else "No release notes available.")
        notes_edit.setMinimumHeight(200)  # Minimum height for notes
        notes_edit.setMaximumHeight(400)  # Maximum height to prevent excessive expansion
        notes_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg_alt']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        notes_layout.addWidget(notes_edit)
        
        # Add notes container to main layout
        main_layout.addWidget(notes_container)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)  # Add top margin
        buttons_layout.setSpacing(10)  # Add spacing between buttons
        
        # Show/Hide Notes button with toggle behavior
        toggle_notes_btn = QPushButton("Show Release Notes")
        toggle_notes_btn.setStyleSheet(ACTION_LINK_STYLE)
        toggle_notes_btn.clicked.connect(lambda: toggle_notes())
        toggle_notes_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        buttons_layout.addWidget(toggle_notes_btn, 1, Qt.AlignmentFlag.AlignLeft)  # Left-aligned with stretch
        
        # No button
        no_button = QPushButton("No")
        no_button.setStyleSheet(BUTTON_STYLE)
        no_button.clicked.connect(custom_dialog.reject)
        no_button.setFixedWidth(80)  # Set fixed width for consistent button size
        buttons_layout.addWidget(no_button, 0, Qt.AlignmentFlag.AlignRight)  # Right-aligned without stretch
        
        # Download button
        download_button = QPushButton("Download")
        download_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        download_button.clicked.connect(lambda: download_clicked())
        download_button.setFixedWidth(100)  # Set fixed width for consistent button size
        buttons_layout.addWidget(download_button, 0, Qt.AlignmentFlag.AlignRight)  # Right-aligned without stretch
        
        main_layout.addLayout(buttons_layout)
        
        # Function to toggle notes visibility
        def toggle_notes():
            current_visibility = notes_container.isVisible()
            
            if not current_visibility:  # Going to show notes
                # First make it visible, then resize the dialog
                notes_container.setVisible(True)
                toggle_notes_btn.setText("Hide Release Notes")
                
                # Resize the dialog to fit the content
                custom_dialog.adjustSize()
            else:  # Going to hide notes
                # First set a fixed height to current compact size, then hide notes
                compact_height = info_container.sizeHint().height() + buttons_layout.sizeHint().height() + 80
                custom_dialog.setFixedHeight(compact_height)
                
                # Now hide the notes
                notes_container.setVisible(False)
                toggle_notes_btn.setText("Show Release Notes")
                
                # Reset the fixed height constraint after a short delay to allow normal resizing again
                QTimer.singleShot(100, lambda: custom_dialog.setFixedHeight(QWIDGETSIZE_MAX))
        
        # Function to handle download button click
        def download_clicked():
            QDesktopServices.openUrl(QUrl(actual_download_url))
            custom_dialog.accept()
        
        # Set download as default button
        download_button.setDefault(True)
        
        # Show the dialog
        custom_dialog.adjustSize()  # Make sure dialog sizes to fit content initially
        return custom_dialog.exec()

    def handle_check_error(self, error_message):
        """Handles errors during the update check (Called by handle_check_complete)."""
        print(f"ERROR: Update check failed: {error_message}")
        # Optionally show a status bar message, but avoid disruptive popups for background errors
        self.show_status_message(f"Update check failed. Check logs.", "error", 5000) # Simpler message

    def handle_check_complete(self, update_was_found, error_message, triggered_manually):
        """Handles the completion of the update check worker."""
        # print(f"DEBUG: Handling check complete. Update Found: {update_was_found}, Error: '{error_message}', Manual: {triggered_manually}")
        if error_message:
            self.handle_check_error(error_message)
        elif not update_was_found:
            if triggered_manually:
                current_version_str = f"{APP_VERSION_NUMBER} (Build {CURRENT_BUILD_NUMBER_CONST})" # Corrected format
                QMessageBox.information(self, "Up to Date", f"You are using the latest version of Echelon ({current_version_str}).")
            else:
                # print("DEBUG: Automatic check completed, no update found.")
                pass 
        
    def _check_for_updates_logic(self, force_check=False):
        """
        Performs the actual update check against the API.
        Returns the version info dictionary if an update is found and suitable, None otherwise.
        Handles internal errors and logs them.
        """
        # print("DEBUG: Running update check logic...")
        settings = QSettings()
        last_check_timestamp = settings.value("update_check/last_checked_timestamp", 0, type=float)
        current_timestamp = time.time()

        if not force_check and (current_timestamp - last_check_timestamp < UPDATE_CHECK_INTERVAL_SECONDS):
            # print(f"DEBUG: Update check skipped. Last checked {int((current_timestamp - last_check_timestamp)/60)} mins ago. Interval: {int(UPDATE_CHECK_INTERVAL_SECONDS/60)} mins.")
            return None

        # print("DEBUG: Proceeding with API check for updates.")
        config = load_config()
        api_url = config.get("api_urls", {}).get("get_public_downloads")

        if not api_url:
            print("ERROR: Update check - API URL for downloads not found in config.")
            settings.setValue("update_check/last_checked_timestamp", current_timestamp)
            return None

        fetched_version_info = None
        try:
            fetched_version_info = get_latest_version_info(api_url)
            settings.setValue("update_check/last_checked_timestamp", current_timestamp)
        except Exception as e:
            print(f"ERROR: Exception during get_latest_version_info call: {e}")
            settings.setValue("update_check/last_checked_timestamp", current_timestamp)
            return None

        if not fetched_version_info:
            # print("DEBUG: No latest version info received from get_latest_version_info.")
            return None

        # --- New comparison logic ---
        available_v_num_str = fetched_version_info.get("versionNumber")
        available_b_num_str = fetched_version_info.get("buildNumber") # This is a string or None
        available_r_stage_str = fetched_version_info.get("releaseStage")

        if not available_v_num_str or not available_r_stage_str: # buildNumber can be null
            print(f"ERROR: Fetched version info is missing versionNumber or releaseStage: {fetched_version_info}")
            return None

        try:
            current_v_num_parsed = parse_version(APP_VERSION_NUMBER)
            available_v_num_parsed = parse_version(available_v_num_str)

            current_b_key = natural_sort_key(str(CURRENT_BUILD_NUMBER_CONST)) # Ensure current build is string for key func
            available_b_key = natural_sort_key(available_b_num_str)
            
            # print(f"DEBUG: Current: v{APP_VERSION_NUMBER} (parsed {current_v_num_parsed}), b{CURRENT_BUILD_NUMBER_CONST} (key {current_b_key}), s{CURRENT_RELEASE_STAGE_CONST}")
            # print(f"DEBUG: Available: v{available_v_num_str} (parsed {available_v_num_parsed}), b{available_b_num_str} (key {available_b_key}), s{available_r_stage_str}")

            # Enhanced version comparison logic
            def get_release_stage_priority(stage):
                """Return priority number for release stage (higher = more stable/newer)"""
                stage_priorities = {
                    "Alpha": 1,
                    "Beta": 2, 
                    "Release Candidate": 3,
                    "RC": 3,  # Alias for Release Candidate
                    "Stable": 4
                }
                return stage_priorities.get(stage, 0)
            
            is_newer = False
            if available_v_num_parsed > current_v_num_parsed:
                is_newer = True
            elif available_v_num_parsed == current_v_num_parsed:
                if available_b_key > current_b_key:
                    is_newer = True
                elif available_b_key == current_b_key:
                    # Same version and build - check release stage hierarchy
                    current_stage_priority = get_release_stage_priority(CURRENT_RELEASE_STAGE_CONST)
                    available_stage_priority = get_release_stage_priority(available_r_stage_str)
                    if available_stage_priority > current_stage_priority:
                        is_newer = True
            
            if not is_newer:
                # print(f"DEBUG: Available version {available_v_num_str} b{available_b_num_str} ({available_r_stage_str}) is not newer than current.")
                return None

            # --- Release Stage Handling ---
            # TODO: Replace USER_UPDATE_CHANNEL_PREFERENCE with actual QSettings value if/when UI setting is implemented
            user_preference = USER_UPDATE_CHANNEL_PREFERENCE 
            
            allowed_stages = []
            if user_preference == "Stable": # Default
                allowed_stages = ["Stable"]
            elif user_preference == "Beta":
                allowed_stages = ["Stable", "Release Candidate", "Beta"]
            elif user_preference == "RC" or user_preference == "Release Candidate":
                allowed_stages = ["Stable", "Release Candidate", "Beta"]
            elif user_preference == "Alpha":
                allowed_stages = ["Stable", "Release Candidate", "Beta", "Alpha"]
            else: # Fallback to stable if preference is unknown
                allowed_stages = ["Stable"]
                print(f"WARN: Unknown USER_UPDATE_CHANNEL_PREFERENCE '{user_preference}'. Defaulting to Stable.")

            if available_r_stage_str not in allowed_stages:
                # print(f"DEBUG: Available version {available_v_num_str} ({available_r_stage_str}) does not meet user preference '{user_preference}' (Allowed: {allowed_stages}).")
                return None
            
            # Promotion path check:
            # If current is Beta and Stable of same version.build is available, it should be offered (if user allows stable).
            # This is naturally handled if get_latest_version_info provides the "best" build and the filtering above allows it.
            # One specific case: if user is on "1.2.0 Beta b50" and "1.2.0 Stable b60" is available,
            # and user preference allows "Stable". `is_newer` will be true. `allowed_stages` will permit. So it works.

            # print(f"INFO: Update found and suitable! Current: {APP_VERSION_NUMBER} b{CURRENT_BUILD_NUMBER_CONST}, Available: {available_v_num_str} b{available_b_num_str} s{available_r_stage_str}")
            return fetched_version_info

        except Exception as e:
            print(f"ERROR: Could not compare versions or handle release stages: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def _initial_update_check(self):
        """Runs the update check shortly after startup in a background thread."""
        # print("DEBUG: Scheduling initial update check.")
        # Delay check slightly to avoid blocking UI startup
        # QTimer.singleShot(5000, lambda: self._check_for_updates_logic(force_check=False)) # Old timer logic
        
        # Create worker and thread for initial check
        self.initial_update_thread = QThread(self) # Keep a reference
        self.initial_update_worker = UpdateWorker(self, force_check=False)
        self.initial_update_worker.moveToThread(self.initial_update_thread)

        # Connect signals
        self.initial_update_worker.update_found.connect(self.handle_update_available)
        self.initial_update_worker.check_complete.connect(lambda update_found, error_msg: self.handle_check_complete(update_found, error_msg, triggered_manually=False))
        self.initial_update_thread.started.connect(self.initial_update_worker.run_check)
        self.initial_update_worker.finished.connect(self.initial_update_thread.quit)
        self.initial_update_worker.finished.connect(self.initial_update_worker.deleteLater)
        self.initial_update_thread.finished.connect(self.initial_update_thread.deleteLater)

        # Start after a short delay
        QTimer.singleShot(5000, self.initial_update_thread.start)

    def check_for_updates(self, triggered_manually=False):
        """Check for application updates, typically triggered manually."""
        if not triggered_manually:
             # print("DEBUG: check_for_updates called without manual trigger flag, ignoring.")
             return # Avoid accidental calls
             
        self.show_status_message("Checking for updates...", "info", 3000) # Show brief status
        
        # Create worker and thread for manual check
        # Store as instance variables to prevent garbage collection before finished
        self.manual_update_thread = QThread(self) 
        self.manual_update_worker = UpdateWorker(self, force_check=True)
        self.manual_update_worker.moveToThread(self.manual_update_thread)

        # Connect signals
        self.manual_update_worker.update_found.connect(self.handle_update_available)
        self.manual_update_worker.check_complete.connect(lambda update_found, error_msg: self.handle_check_complete(update_found, error_msg, triggered_manually=True))
        self.manual_update_thread.started.connect(self.manual_update_worker.run_check)
        self.manual_update_worker.finished.connect(self.manual_update_thread.quit)
        self.manual_update_worker.finished.connect(self.manual_update_worker.deleteLater)
        self.manual_update_thread.finished.connect(self.manual_update_thread.deleteLater)

        self.manual_update_thread.start()
    
    def _update_structure_combo(self):
        """Update the structure dropdown with available structures
        
        Note: The UI element has been removed, but we keep this method for compatibility.
        We still populate the hidden combo box to ensure the structure selection works properly.
        """
        self.structure_combo.clear()
        
        # Add default structures
        self.structure_combo.addItem("Standard")
        self.structure_combo.addItem("Video Editing")
        self.structure_combo.addItem("Motion Graphics")
        self.structure_combo.addItem("Design")
        self.structure_combo.addItem("Audio")
        
        # Add custom structures
        for name in sorted(self.template_manager.custom_structures.keys()):
            self.structure_combo.addItem(name)
            
        # Select the default structure
        self.structure_combo.setCurrentIndex(0)
    
    def _select_template_file(self):
        """This method is no longer needed as templates contain their files"""
        pass  # Keeping the method as a stub for compatibility
    
    def _edit_structure(self):
        """Open structure editor dialog
        
        Note: The UI element for this has been removed. This method is kept
        for compatibility with other parts of the code.
        """
        # Use Standard as the default structure type
        structure_type = "Standard"
        
        # Show structure editor dialog
        from app.dialogs.dialog_windows_pyqt import show_structure_editor
        show_structure_editor(self, structure_type, self._update_structure_combo)
    
    def _preview_structure(self):
        """Preview the selected structure
        
        Note: The UI element for this has been removed. This method is kept
        for compatibility with other parts of the code.
        """
        # Use Standard as the default structure type
        structure_type = "Standard"
        
        # Get structure
        structure = self.template_manager.get_structure(structure_type)
        
        # Show preview dialog
        from app.dialogs.dialog_windows_pyqt import preview_structure
        preview_structure(self, structure)
    
    def _create_custom_structure(self):
        """Create a new custom structure"""
        from app.dialogs.dialog_windows_pyqt import show_structure_editor
        show_structure_editor(self, None, self._update_structure_combo)
    
    def _manage_structures(self):
        """Manage custom structures"""
        # TODO: Implement manage structures dialog
        QMessageBox.information(self, "Not Implemented", "Structure management dialog not yet implemented in PyQt version.")
    
    def check_batch_results(self):
        """
        Check batch results and update UI accordingly
        """
        # Debug print only in development mode
        # print(f"Checking batch results: {self.batch_results}")
        
        if not self.batch_results:
            return
            
        # Store the results locally so we can clear the main attribute
        results = self.batch_results
        
        # Clear the batch results immediately to prevent duplicate dialogs
        self.batch_results = None
        
        # Stop the timer since we're processing the results now
        self.batch_check_timer.stop()
        
        # Don't reset the custom options widget here - let the user continue using the same template
        # The widget will be reset when they select a different template or close the app
            
        # Extract error message if present
        error_message = results.get("error", None)
        
        # Check if any projects were created
        if results.get("successful_count", 0) > 0:
            # Update status
            self.show_status_message(f"Created {results.get('successful_count')} of {results.get('total_count')} projects", 5000)
            
            # If no_structure flag is True AND no projects were created with structure,
            # only show the status message
            if results.get("no_structure", False) and results.get("successful_count") == results.get("total_count"):
                self.show_status_message("Note: Projects created without folder structure", 5000)
            else:
                # Show results dialog - this handles projects with valid structures
                from app.dialogs.dialog_windows_pyqt import show_batch_results
                show_batch_results(self, results)
        else:
            # No projects created successfully
            self.show_error(error_message or "Failed to create any projects")
            
        print(f"Batch results checked: {results}")
    
    def _create_template(self):
        """Create a new template"""
        try:
            # Explicitly get the category update manager instance to ensure it's initialized
            from app.templates.category_update_manager import get_instance as get_category_update_manager
            category_manager = get_category_update_manager(self)
            
            # Force an immediate update of category comboboxes
            if category_manager:
                category_manager.force_immediate_global_update()
            
            # Use the template manager to create a new template
            success = self.template_manager.create_new_template(self)
            if success:
                self._refresh_ui()
                
                # Ensure all comboboxes have hover delegates 
                from app.templates.category_combobox_updater import ensure_all_combos_have_hover_delegates
                ensure_all_combos_have_hover_delegates(self)
        except Exception as e:
            print(f"Error creating template: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_ui(self):
        """Refresh the UI after creating a new template"""
        # Update UI elements that depend on template data
        pass
        
        # Update recent templates gallery
        self.update_recent_templates_gallery()
        
        # Show status message
        self.show_status_message("Template created successfully!", "success", 5000)

    def eventFilter(self, obj, event):
        """Filter for specific events"""
        # Handle hover effects for structure_combo dropdown - no longer needed as the UI has been removed
        # if hasattr(self, 'structure_combo') and self.structure_combo.view() and obj == self.structure_combo.view().viewport():
        #     if event.type() == QEvent.MouseMove:
        #         # Get the item under the mouse
        #         pos = event.pos()
        #         index = self.structure_combo.view().indexAt(pos)
        #         
        #         if index.isValid():
        #             # Set hover style directly
        #             for i in range(self.structure_combo.view().model().rowCount()):
        #                 item_index = self.structure_combo.view().model().index(i, 0)
        #                 rect = self.structure_combo.view().visualRect(item_index)
        #                 
        #                 # Apply style to the item under cursor
        #                 if rect.contains(pos):
        #                     # Force a repaint of the view
        #                     self.structure_combo.view().update(item_index)
                            
        # Pass the event to the parent class
        return super().eventFilter(obj, event) 

    def _setup_versioning_animation(self):
        """Setup animation for versioning options"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        # Create animations for both widgets
        self.versioning_options_animation = QPropertyAnimation(self.versioning_options, b"maximumHeight")
        self.versioning_options_animation.setDuration(250)
        self.versioning_options_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.options_container_animation = QPropertyAnimation(self.options_container, b"maximumHeight")
        self.options_container_animation.setDuration(250)
        self.options_container_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Track animation state
        self._versioning_options_visible = False
    
    def _toggle_versioning_options(self, enabled):
        """Toggle visibility of versioning options with smooth animation"""
        if enabled:
            self._slide_versioning_options_up()
            # Check for conflicts with custom patterns when versioning is enabled
            self._check_custom_pattern_conflicts()
        else:
            self._slide_versioning_options_down()
    
    def _slide_versioning_options_up(self):
        """Animate versioning options sliding up"""
        if self._versioning_options_visible:
            return
            
        self._versioning_options_visible = True
        
        # Disconnect any previous connections to avoid conflicts
        try:
            self.versioning_options_animation.finished.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        try:
            self.options_container_animation.finished.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        
        # Show widgets first and set initial height to 0
        self.versioning_options.show()
        self.options_container.show()
        self.versioning_options.setMaximumHeight(0)
        self.options_container.setMaximumHeight(0)
        
        # Calculate target heights based on content
        # Temporarily remove height constraint to get natural size
        self.versioning_options.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        self.options_container.setMaximumHeight(16777215)
        self.versioning_options.adjustSize()
        self.options_container.adjustSize()
        
        versioning_target_height = self.versioning_options.sizeHint().height()
        options_target_height = self.options_container.sizeHint().height()
        
        # Reset to 0 for animation
        self.versioning_options.setMaximumHeight(0)
        self.options_container.setMaximumHeight(0)
        
        # Start animations
        self.versioning_options_animation.setStartValue(0)
        self.versioning_options_animation.setEndValue(versioning_target_height)
        self.versioning_options_animation.finished.connect(
            lambda: self.versioning_options.setMaximumHeight(16777215)
        )
        self.versioning_options_animation.start()
        
        self.options_container_animation.setStartValue(0)
        self.options_container_animation.setEndValue(options_target_height)
        self.options_container_animation.finished.connect(
            lambda: self.options_container.setMaximumHeight(16777215)
        )
        self.options_container_animation.start()
    
    def _slide_versioning_options_down(self):
        """Animate versioning options sliding down"""
        if not self._versioning_options_visible:
            return
            
        self._versioning_options_visible = False
        
        # Disconnect any previous connections to avoid conflicts
        try:
            self.versioning_options_animation.finished.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        try:
            self.options_container_animation.finished.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        
        # Get current heights
        current_versioning_height = self.versioning_options.height()
        current_options_height = self.options_container.height()
        
        # Animate to height 0, then hide
        self.versioning_options_animation.setStartValue(current_versioning_height)
        self.versioning_options_animation.setEndValue(0)
        self.versioning_options_animation.finished.connect(lambda: self.versioning_options.hide())
        self.versioning_options_animation.start()
        
        self.options_container_animation.setStartValue(current_options_height)
        self.options_container_animation.setEndValue(0)
        self.options_container_animation.finished.connect(lambda: self.options_container.hide())
        self.options_container_animation.start()
    
    def _update_versioning_options(self):
        """Update which versioning options are visible based on sequence type"""
        sequence_type = self.sequence_type.currentText()
        
        # Hide all options first
        self.date_options.hide()
        self.version_options.hide()
        self.number_options.hide()
        
        # Show relevant options
        if sequence_type == "Date Sequences":
            self.date_options.show()
            # Check for conflicts when switching to date sequences
            if self.enable_versioning.isChecked():
                self._check_custom_pattern_conflicts()
        elif sequence_type == "Version Numbers":
            self.version_options.show()
        elif sequence_type == "Sequential Numbers":
            self.number_options.show()
    
    def _generate_sequence_names(self, base_name):
        """Generate sequence names based on current settings"""
        import datetime
        from datetime import timedelta
        
        if not self.enable_versioning.isChecked():
            return [base_name]
        
        sequence_type = self.sequence_type.currentText()
        position = self.name_position.currentText()
        names = []
        
        if sequence_type == "Date Sequences":
            # Generate date sequence
            qdate = self.start_date.date()
            start_date = datetime.date(qdate.year(), qdate.month(), qdate.day())
            count = self.date_count.value()
            interval = self.date_interval.value()
            interval_type = self.date_interval_type.currentText()
            format_text = self.date_format.currentText()
            
            # Extract format
            if "YYYY-MM-DD" in format_text:
                date_format = "%Y-%m-%d"
            elif "YYYYMMDD" in format_text:
                date_format = "%Y%m%d"
            elif "MM-DD-YYYY" in format_text:
                date_format = "%m-%d-%Y"
            elif "DD-MM-YYYY" in format_text:
                date_format = "%d-%m-%Y"
            elif "YYYY_MM_DD" in format_text:
                date_format = "%Y_%m_%d"
            elif "MM_DD_YYYY" in format_text:
                date_format = "%m_%d_%Y"
            elif "DD_MM_YYYY" in format_text:
                date_format = "%d_%m_%Y"
            elif "YYYY.MM.DD" in format_text:
                date_format = "%Y.%m.%d"
            elif "MM.DD.YYYY" in format_text:
                date_format = "%m.%d.%Y"
            elif "DD.MM.YYYY" in format_text:
                date_format = "%d.%m.%Y"
            elif "YYYY MM DD" in format_text:
                date_format = "%Y %m %d"
            elif "MM DD YYYY" in format_text:
                date_format = "%m %d %Y"
            elif "DD MM YYYY" in format_text:
                date_format = "%d %m %Y"
            else:
                date_format = "%Y-%m-%d"
            
            current_date = start_date
            for i in range(count):
                date_str = current_date.strftime(date_format)
                
                if "Suffix" in position:
                    name = f"{base_name}_{date_str}"
                elif "Prefix" in position:
                    name = f"{date_str}_{base_name}"
                else:
                    name = date_str
                
                names.append(name)
                
                # Calculate next date
                if interval_type == "Days":
                    current_date += timedelta(days=interval)
                elif interval_type == "Weeks":
                    current_date += timedelta(weeks=interval)
                elif interval_type == "Months":
                    # Approximate month calculation
                    current_date += timedelta(days=interval * 30)
        
        elif sequence_type == "Version Numbers":
            # Generate version sequence
            count = self.version_count.value()
            format_text = self.version_format.currentText()
            
            for i in range(1, count + 1):
                # Format number based on leading zeros setting
                if hasattr(self, 'version_digits'):
                    leading_zeros = self.version_digits.currentText()
                    format_prefix = format_text
                    
                    if leading_zeros == "NONE":
                        num_str = str(i)
                    elif leading_zeros == "1":
                        num_str = f"{i:02d}"  # 1 leading zero = 2 digits total
                    elif leading_zeros == "2":
                        num_str = f"{i:03d}"  # 2 leading zeros = 3 digits total
                    elif leading_zeros == "3":
                        num_str = f"{i:04d}"  # 3 leading zeros = 4 digits total
                    else:
                        num_str = str(i)
                    
                    version_str = f"{format_prefix}{num_str}"
                else:
                    # Fallback for old format
                    version_str = f"V{i}"
                
                if "Suffix" in position:
                    name = f"{base_name}_{version_str}"
                elif "Prefix" in position:
                    name = f"{version_str}_{base_name}"
                else:
                    name = version_str
                
                names.append(name)
        
        elif sequence_type == "Sequential Numbers":
            # Generate number sequence
            start = self.number_start.value()
            count = self.number_count.value()
            format_text = self.number_format.currentText()
            
            for i in range(count):
                num = start + i
                
                if "3 digits" in format_text:
                    num_str = f"{num:03d}"
                elif "2 digits" in format_text:
                    num_str = f"{num:02d}"
                else:  # no padding
                    num_str = str(num)
                
                if "Suffix" in position:
                    name = f"{base_name}_{num_str}"
                elif "Prefix" in position:
                    name = f"{num_str}_{base_name}"
                else:
                    name = num_str
                
                names.append(name)
        
        return names

    def process_batch_projects(self):
        """Process the entered project names for batch creation"""
        import re
        from app.core.project_operations import handle_batch_create
        
        # Get project names from text area
        text = self.batch_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter at least one project name.")
            return
        
        # Parse project names
        project_names = re.split(r'[\n,;]+', text)
        project_names = [name.strip() for name in project_names if name.strip()]
        
        if not project_names:
            QMessageBox.warning(self, "Warning", "No valid project names found.")
            return
        
        # Check if current template has custom options and show slide-up widget if needed
        if hasattr(self, 'template_gallery') and self.template_gallery:
            # Try to get the selected template using different methods
            current_template = None
            
            # Method 1: Try get_primary_selected_template
            if hasattr(self.template_gallery, 'get_primary_selected_template'):
                current_template = self.template_gallery.get_primary_selected_template()
            
            # Method 2: Try selection_manager
            elif hasattr(self.template_gallery, 'selection_manager') and hasattr(self.template_gallery.selection_manager, 'selected_template'):
                current_template = self.template_gallery.selection_manager.selected_template
            
            # Method 3: Try selected_template attribute
            elif hasattr(self.template_gallery, 'selected_template'):
                current_template = self.template_gallery.selected_template
            
            print(f"DEBUG: Found current_template for batch creation: {current_template.get('name') if current_template else 'None'}")
            
            if current_template:
                self.check_template_for_custom_options(current_template)
                
                # If custom options are required, check if user has made valid selections
                if (hasattr(self, 'custom_options_widget') and 
                    self.custom_options_widget and 
                    self.custom_options_widget.is_visible and 
                    len(self.custom_options_widget.combo_widgets) > 0):
                    
                    # Check if user has made valid selections for all required custom options
                    selected_values = self.custom_options_widget.get_selected_values()
                    has_valid_selections = True
                    
                    # Check each combo widget to ensure a valid selection is made
                    for combo_key, combo_widget in self.custom_options_widget.combo_widgets.items():
                        current_text = combo_widget.currentText()
                        # Check if selection is empty or placeholder text
                        if not current_text or current_text.startswith("Select ") or current_text == "":
                            has_valid_selections = False
                            break
                    
                    if not has_valid_selections:
                        # Custom options are required but user hasn't made selections
                        QMessageBox.information(
                            self, 
                            "Custom Options Required", 
                            "This template requires custom options. Please make your selections below and then try creating projects again."
                        )
                        return
                    
                    print(f"DEBUG: Custom options validated successfully: {selected_values}")
        
        # Generate final list with sequences if enabled
        final_projects = []
        for base_name in project_names:
            sequence_names = self._generate_sequence_names(base_name)
            final_projects.extend(sequence_names)
        
        # Show confirmation only for larger batches
        if len(final_projects) >= 10:
            if QMessageBox.question(
                self, 
                "Confirm Batch Creation", 
                f"You are about to create {len(final_projects)} projects.\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.No:
                return
        
        # Show creating message in status bar
        self.show_status_message(f"Creating {len(final_projects)} projects...", message_type="info")
        
        # Convert list to text for handle_batch_create
        projects_text = "\n".join(final_projects)
        
        # Start batch creation process
        self.batch_results = handle_batch_create(self, projects_text)
        
        # Start result checking timer
        if not hasattr(self, 'batch_check_timer'):
            self.batch_check_timer = QTimer()
            self.batch_check_timer.timeout.connect(self.check_batch_results)
        
        self.batch_check_timer.start(500)  # Check every 500ms
    
    def _handle_enhanced_batch_creation(self, project_names):
        """Handle the project creation from the enhanced dialog"""
        from app.core.project_operations import handle_batch_create
        
        # Show creating message in status bar
        self.show_status_message(f"Creating {len(project_names)} projects...", message_type="info")
        
        # Convert list of project names to a string for handle_batch_create
        projects_text = "\n".join(project_names)
        
        # Start batch creation process
        self.batch_results = handle_batch_create(self, projects_text)
        
        # Start result checking timer
        if not hasattr(self, 'batch_check_timer'):
            self.batch_check_timer = QTimer()
            self.batch_check_timer.timeout.connect(self.check_batch_results)
        
        self.batch_check_timer.start(500)  # Check every 500ms
    
    def check_template_for_custom_options(self, template_data):
        """Check if template requires custom options and show/hide the animated widget"""

        # Track the current template to detect changes
        current_template_name = template_data.get('name') if template_data else None
        previous_template_name = getattr(self, '_current_template_name', None)
        
        # Only reset if we have a genuine template change (not None -> template or template -> None)
        genuine_template_change = (
            previous_template_name and 
            current_template_name and 
            previous_template_name != current_template_name
        )
        
        if genuine_template_change:
            print(f"DEBUG: Genuine template change from '{previous_template_name}' to '{current_template_name}', resetting widget")
            if hasattr(self, 'custom_options_widget') and self.custom_options_widget:
                self.custom_options_widget.combo_widgets.clear()
                # Hide the widget immediately for template changes
                if self.custom_options_widget.is_visible:
                    self.custom_options_widget.slide_down(delay_ms=0)
        
        # Store current template name for next comparison
        self._current_template_name = current_template_name
        
        if not template_data:
            # Hide the widget when no template is selected (clicking off templates)
            if hasattr(self, 'custom_options_widget') and self.custom_options_widget.isVisible():
                self.custom_options_widget.slide_down(delay_ms=0)
            return
        
        # Check if template has custom options
        custom_prompts = self._collect_custom_options_from_template(template_data)
        
        if custom_prompts:

            # Find the preview pattern for the custom options
            preview_pattern = self._find_preview_pattern_from_template(template_data)
            
            # Always update options when showing the widget to ensure fresh content
            print(f"DEBUG: Updating custom options for template")
            self.custom_options_widget.set_custom_options(custom_prompts)
            if preview_pattern:
                self.custom_options_widget.preview_pattern = preview_pattern
                self.custom_options_widget._update_unified_preview()
            
            # Always slide up when template has custom options - let the widget handle its own state
            self.custom_options_widget.slide_up()
        else:
            # Hide the widget with delay to allow for selection stabilization
            if hasattr(self, 'custom_options_widget') and self.custom_options_widget.isVisible():
                self.custom_options_widget.slide_down()  # Use default delay
    
    def _collect_custom_options_from_template(self, template_data):
        """Collect custom options from template data for the slide-up widget"""
        custom_prompts = {}
        print(f"DEBUG: _collect_custom_options_from_template called with template: {template_data.get('name', 'unknown') if template_data else 'None'}")
        
        def collect_from_structure(structure, path=""):
            """Recursively collect custom options from structure"""
            for item in structure:
                if isinstance(item, dict):
                    item_name = item.get('name', '')
                    item_path = f"{path}/{item_name}" if path else item_name
                    
                    # Helper function to recursively search for pattern data
                    def extract_pattern_data(data, depth=0, max_depth=5):
                        """Recursively extract pattern and custom options from nested data"""
                        if depth > max_depth or not isinstance(data, dict):
                            return [], ''
                        
                        found_options = data.get('custom_options', [])
                        found_pattern = data.get('pattern', '')
                        
                        # If we found both, return them
                        if found_options and found_pattern:
                            return found_options, found_pattern
                        
                        # Otherwise, check user_data recursively
                        if 'user_data' in data and isinstance(data['user_data'], dict):
                            nested_options, nested_pattern = extract_pattern_data(data['user_data'], depth + 1, max_depth)
                            if not found_options and nested_options:
                                found_options = nested_options
                            if not found_pattern and nested_pattern:
                                found_pattern = nested_pattern
                        
                        return found_options, found_pattern
                    
                    # Extract pattern data from the item
                    custom_options, pattern = extract_pattern_data(item)
                    print(f"DEBUG: For item '{item_name}', found custom_options: {custom_options}, pattern: {pattern}")
                    
                    # Check for any CUSTOM placeholders in the pattern
                    if custom_options and pattern:
                        import re
                        custom_matches = re.findall(r'\$\{(CUSTOM\d*)\}', pattern)
                        if custom_matches:
                            # Handle both old format (list) and new format (dict)
                            if isinstance(custom_options, dict):
                                # New format - each placeholder has its own options
                                for custom_placeholder in custom_matches:
                                    # Check both direct key and with ${} format
                                    placeholder_keys = [
                                        custom_placeholder,
                                        f"${{{custom_placeholder}}}"
                                    ]
                                    
                                    found_options = None
                                    for key in placeholder_keys:
                                        if key in custom_options:
                                            found_options = custom_options[key]
                                            break
                                    
                                    if found_options:
                                        custom_key = f"{item_path}_{custom_placeholder}"
                                        if custom_key not in custom_prompts:
                                            custom_prompts[custom_key] = {
                                                'item_path': item_path,
                                                'item_name': item_name,
                                                'options': found_options,
                                                'pattern': pattern,
                                                'placeholder': custom_placeholder
                                            }
                            else:
                                # Old format - single list of options, create entries for each placeholder
                                for i, custom_placeholder in enumerate(custom_matches):
                                    custom_key = f"{item_path}_{custom_placeholder}"
                                    if custom_key not in custom_prompts:
                                        # Use different option based on placeholder index
                                        if i < len(custom_options):
                                            option_list = [custom_options[i]]
                                        else:
                                            # If we don't have enough options, use all options for this placeholder
                                            option_list = custom_options
                                        
                                        custom_prompts[custom_key] = {
                                            'item_path': item_path,
                                            'item_name': item_name,
                                            'options': option_list if len(option_list) > 1 else custom_options,
                                            'pattern': pattern,
                                            'placeholder': custom_placeholder
                                        }
                    
                    # Recursively check children
                    children = item.get('children', [])
                    if children:
                        collect_from_structure(children, item_path)
        
        # Collect all custom options needed
        structure = template_data.get('structure', [])
        collect_from_structure(structure)
        print(f"DEBUG: Final custom_prompts collected: {custom_prompts}")
        return custom_prompts
    
    def get_custom_values_from_widget(self):
        """Get custom values from the animated widget"""
        # Always try to get values from the widget, regardless of visibility
        # The widget retains its values even when hidden
        if hasattr(self, 'custom_options_widget') and self.custom_options_widget:
            values = self.custom_options_widget.get_selected_values()
            print(f"DEBUG: Widget combo_widgets keys: {list(self.custom_options_widget.combo_widgets.keys())}")
            print(f"DEBUG: Widget get_selected_values returned: {values}")
            if values:
                print(f"DEBUG: Retrieved custom values from widget: {values}")
                return values
        print(f"DEBUG: No custom values found in widget")
        return {}
    
    def _find_preview_pattern_from_template(self, template_data):
        """Find a preview pattern from template data for the slide-up widget"""
        def find_first_pattern(structure):
            """Recursively find the first pattern with custom options"""
            for item in structure:
                if isinstance(item, dict):
                    # Helper function to recursively search for pattern data
                    def extract_pattern_data(data, depth=0, max_depth=5):
                        """Recursively extract pattern and custom options from nested data"""
                        if depth > max_depth or not isinstance(data, dict):
                            return [], ''
                        
                        found_options = data.get('custom_options', [])
                        found_pattern = data.get('pattern', '')
                        
                        # If we found both, return them
                        if found_options and found_pattern:
                            return found_options, found_pattern
                        
                        # Otherwise, check user_data recursively
                        if 'user_data' in data and isinstance(data['user_data'], dict):
                            nested_options, nested_pattern = extract_pattern_data(data['user_data'], depth + 1, max_depth)
                            if not found_options and nested_options:
                                found_options = nested_options
                            if not found_pattern and nested_pattern:
                                found_pattern = nested_pattern
                        
                        return found_options, found_pattern
                    
                    # Extract pattern data from the item
                    custom_options, pattern = extract_pattern_data(item)
                    
                    # If we found custom options and pattern, return the pattern
                    if custom_options and pattern:
                        return pattern
                    
                    # Recursively check children
                    if 'children' in item and isinstance(item['children'], list):
                        result = find_first_pattern(item['children'])
                        if result:
                            return result
        
        # Check the main structure
        if 'structure' in template_data:
            return find_first_pattern(template_data['structure'])
        
        return ""
    
    def reset_custom_options_widget(self):
        """Reset the custom options widget state after project creation"""
        if hasattr(self, 'custom_options_widget') and self.custom_options_widget:
            print(f"DEBUG: Resetting custom options widget state")
            # Clear the widget's internal state
            self.custom_options_widget.combo_widgets.clear()
            # Hide the widget immediately after project creation
            if self.custom_options_widget.is_visible:
                self.custom_options_widget.slide_down(delay_ms=0)
            print(f"DEBUG: Custom options widget reset complete")
    
    def _check_custom_pattern_conflicts(self):
        """Check for conflicts between custom patterns and sequence creation settings"""
        if not hasattr(self, 'custom_options_widget') or not self.custom_options_widget:
            return
        
        # Only check if custom options widget is visible (meaning there are custom patterns)
        if not self.custom_options_widget.is_visible:
            return
        
        # Check if sequence creation is enabled
        if not self.enable_versioning.isChecked():
            return
        
        sequence_type = self.sequence_type.currentText()
        
        # Check for conflicts with date sequences
        if sequence_type == "Date Sequences":
            # Check if any custom patterns contain ${DATE} or ${PROJECT_NAME}
            conflicts = []
            
            # Get the current template data to check for patterns
            try:
                from app.templates.template_manager_core import TemplateManagerCore
                template_manager = TemplateManagerCore()
                
                # Get currently selected template
                if hasattr(self, 'template_gallery') and self.template_gallery:
                    selected_templates = self.template_gallery.get_selected_templates()
                    if selected_templates:
                        template_name = selected_templates[0]
                        template_data = template_manager.get_template_by_name(template_name)
                        
                        if template_data:
                            # Check for ${DATE} in custom patterns
                            custom_prompts = self._collect_custom_options_from_template(template_data)
                            for key, prompt_data in custom_prompts.items():
                                pattern = prompt_data.get('pattern', '')
                                if '${DATE}' in pattern:
                                    conflicts.append(f"Custom pattern '{pattern}' contains ${{DATE}}")
                                if '${PROJECT_NAME}' in pattern:
                                    conflicts.append(f"Custom pattern '{pattern}' contains ${{PROJECT_NAME}}")
            except Exception as e:
                print(f"DEBUG: Error checking for pattern conflicts: {e}")
                return
            
            # Show warning if conflicts found
            if conflicts:
                from PyQt6.QtWidgets import QMessageBox
                conflict_text = "\n".join(conflicts)
                
                reply = QMessageBox.question(
                    self,
                    "Pattern Conflict Detected",
                    f"The selected template has custom patterns that may conflict with sequence creation:\n\n"
                    f"{conflict_text}\n\n"
                    f"When using 'Date Sequences':\n"
                    f"• Sequence dates will be added to project names\n"
                    f"• Custom ${{DATE}} patterns will use current date\n"
                    f"• Custom ${{PROJECT_NAME}} will include the sequence date\n\n"
                    f"This may result in duplicate dates in filenames.\n\n"
                    f"Do you want to continue with sequence creation?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    # Disable versioning
                    self.enable_versioning.setChecked(False)
                    return

    def _export_all(self):
        """Export all settings and templates"""
        from app.core.import_export_manager import export_package
        export_package(self, include_settings=True, include_templates=True)
    
    def _export_settings(self):
        """Export settings only"""
        from app.core.import_export_manager import export_package
        export_package(self, include_settings=True, include_templates=False)
    
    def _import_all(self):
        """Import all settings and templates"""
        from app.core.import_export_manager import import_package
        import_package(self, import_settings=True, import_templates=True)
    
    def _import_settings(self):
        """Import settings only"""
        from app.core.import_export_manager import import_package
        import_package(self, import_settings=True, import_templates=False)
    
    def show_error(self, message):
        """Show an error message in the status bar"""
        self.show_status_message(message, message_type="error", duration=10000)

    def show_about_dialog(self):
        """Shows the About dialog."""
        show_about(self)

    def notify_gallery_preference_changed(self, preference_key):
        """Notify listeners that a gallery-related preference has changed."""
        self.gallery_preference_changed.emit(preference_key)

# Add a class variable to hold the single instance
ProjectCreatorApp._instance = None