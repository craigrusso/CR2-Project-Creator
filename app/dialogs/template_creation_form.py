#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QLineEdit, QComboBox, QGridLayout,
                           QMessageBox, QFileDialog, QGroupBox)
from PyQt5.QtCore import Qt
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE

class TemplateCreationForm(QDialog):
    """
    Enhanced template creation form that makes the relationship between 
    project types and folder structures clear
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.template_manager = parent.template_manager if hasattr(parent, 'template_manager') else None
        self.template_file_path = ""
        
        self.setWindowTitle("Create New Template")
        self.resize(600, 450)
        
        self.init_ui()
        self.update_structure_preview()
        
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Create a New Project Template")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(header_label)
        
        # Description
        desc_label = QLabel("Create a template to use for future projects. Templates can be based on an existing project file or created from scratch.")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # Form layout
        form_group = QGroupBox("Template Details")
        form_layout = QGridLayout(form_group)
        form_layout.setColumnStretch(1, 1)  # Make the second column stretch
        
        # Template name
        name_label = QLabel("Template Name:")
        self.name_input = QLineEdit()
        form_layout.addWidget(name_label, 0, 0)
        form_layout.addWidget(self.name_input, 0, 1)
        
        # Project Type (formerly Category)
        type_label = QLabel("Project Type:")
        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self.on_project_type_changed)
        
        # Add help text for project type
        type_help = QLabel("Project Type determines the default folder structure")
        type_help.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        
        form_layout.addWidget(type_label, 1, 0)
        form_layout.addWidget(self.type_combo, 1, 1)
        form_layout.addWidget(type_help, 2, 0, 1, 2)
        
        # Optional template file
        file_label = QLabel("Template File (optional):")
        
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)
        
        form_layout.addWidget(file_label, 3, 0)
        form_layout.addLayout(file_layout, 3, 1)
        
        # Add form to main layout
        main_layout.addWidget(form_group)
        
        # Structure preview
        structure_group = QGroupBox("Folder Structure Preview")
        structure_layout = QVBoxLayout(structure_group)
        
        # Structure combobox
        structure_header = QHBoxLayout()
        structure_label = QLabel("Structure:")
        self.structure_combo = QComboBox()
        self.structure_combo.currentIndexChanged.connect(self.update_structure_preview)
        
        edit_structure_btn = QPushButton("Edit Structure")
        edit_structure_btn.clicked.connect(self.edit_structure)
        
        structure_header.addWidget(structure_label)
        structure_header.addWidget(self.structure_combo, 1)  # 1 = stretch factor
        structure_header.addWidget(edit_structure_btn)
        
        structure_layout.addLayout(structure_header)
        
        # Structure preview text
        self.structure_preview = QLabel()
        self.structure_preview.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        self.structure_preview.setWordWrap(True)
        self.structure_preview.setMinimumHeight(100)
        
        structure_layout.addWidget(self.structure_preview)
        
        # Add structure preview to main layout
        main_layout.addWidget(structure_group)
        
        # Explanation of the relationship
        relationship_label = QLabel(
            "<b>Note:</b> Each Project Type is associated with a default folder structure. "
            "You can customize the structure by editing it above."
        )
        relationship_label.setWordWrap(True)
        relationship_label.setStyleSheet("color: #333; font-style: italic;")
        main_layout.addWidget(relationship_label)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create Template")
        create_btn.clicked.connect(self.create_template)
        create_btn.setStyleSheet(BUTTON_STYLE)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        main_layout.addLayout(button_layout)
        
        # Populate dropdown
        self.populate_dropdowns()
        
    def populate_dropdowns(self):
        """Populate project type and structure dropdowns"""
        if not self.template_manager:
            return
            
        # Project types (categories)
        for category in sorted(self.template_manager.get_categories()):
            self.type_combo.addItem(category)
            
        # Default to first item
        if self.type_combo.count() > 0:
            self.type_combo.setCurrentIndex(0)
            
        # Update structure combo
        self.update_structure_combo()
        
    def update_structure_combo(self):
        """Update the structure dropdown based on the selected project type"""
        self.structure_combo.clear()
        
        # Get selected project type
        project_type = self.type_combo.currentText()
        
        # Get associated structure
        if project_type and hasattr(self.template_manager, 'project_type_manager'):
            structure_name = self.template_manager.project_type_manager.get_structure_for_project_type(project_type)
            if structure_name:
                self.structure_combo.addItem(structure_name)
                
        # Add all custom structures
        if hasattr(self.template_manager, 'custom_structures'):
            for name in sorted(self.template_manager.custom_structures.keys()):
                # Skip if already added
                if self.structure_combo.findText(name) == -1:
                    self.structure_combo.addItem(name)
                    
    def on_project_type_changed(self, index):
        """Handle project type change"""
        # Update structure dropdown based on selected project type
        self.update_structure_combo()
        
        # Update preview
        self.update_structure_preview()
        
    def update_structure_preview(self):
        """Update the structure preview"""
        structure_name = self.structure_combo.currentText()
        if not structure_name or not self.template_manager:
            self.structure_preview.setText("No structure selected")
            return
            
        # Get structure
        structure = self.template_manager.get_structure(structure_name)
        
        # Format structure as text
        preview_text = self.format_structure(structure)
        self.structure_preview.setText(preview_text)
        
    def format_structure(self, structure, indent=""):
        """Format structure as text for preview"""
        result = []
        
        for item in structure:
            if isinstance(item, dict):
                # It's a directory with children
                for dir_name, children in item.items():
                    result.append(f"{indent}📁 {dir_name}/")
                    result.append(self.format_structure(children, indent + "  "))
            elif isinstance(item, str):
                # It's a file or empty directory
                if item.endswith('/'):
                    result.append(f"{indent}📁 {item}")
                else:
                    result.append(f"{indent}📄 {item}")
        
        return "\n".join(result)
        
    def browse_file(self):
        """Browse for a template file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template File",
            "",
            "All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai)"
        )
        
        if file_path:
            self.file_input.setText(file_path)
            self.template_file_path = file_path
            
            # If name is empty, use filename as default
            if not self.name_input.text():
                import os
                filename = os.path.basename(file_path)
                name = os.path.splitext(filename)[0]
                self.name_input.setText(name)
                
            # Detect project type from file extension
            self.detect_project_type_from_file(file_path)
            
    def detect_project_type_from_file(self, file_path):
        """Detect project type from file extension"""
        import os
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Map extensions to project types
        type_map = {
            '.prproj': "Video Editing",
            '.aep': "Motion Graphics",
            '.aepx': "Motion Graphics",
            '.psd': "Design",
            '.ai': "Design",
            '.wav': "Audio",
            '.mp3': "Audio",
            '.aup': "Audio"
        }
        
        if ext in type_map:
            project_type = type_map[ext]
            index = self.type_combo.findText(project_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
                
    def edit_structure(self):
        """Edit the selected structure"""
        structure_name = self.structure_combo.currentText()
        if not structure_name:
            QMessageBox.warning(self, "Error", "Please select a structure first")
            return
            
        # Get structure
        structure = self.template_manager.get_structure(structure_name)
        
        # Show enhanced structure editor
        from app.ui.structure_editor_enhanced import show_enhanced_structure_editor
        result = show_enhanced_structure_editor(
            self,
            structure_name=structure_name,
            structure=structure
        )
        
        if result:
            # Refresh dropdowns
            self.update_structure_combo()
            self.update_structure_preview()
            
    def create_template(self):
        """Create the template"""
        # Get form values
        name = self.name_input.text().strip()
        project_type = self.type_combo.currentText()
        structure_name = self.structure_combo.currentText()
        
        # Validate
        if not name:
            QMessageBox.warning(self, "Error", "Template name is required")
            return
            
        if not project_type:
            QMessageBox.warning(self, "Error", "Project type is required")
            return
            
        # Create template
        success = False
        
        if self.template_file_path:
            # Create from file
            success = self.template_manager.import_template_file(
                self.template_file_path,
                name=name,
                category=project_type
            )
        else:
            # Create empty template
            success = self.template_manager.save_template(
                name,
                project_type,
                "",
                structure_name
            )
            
        if success:
            QMessageBox.information(self, "Success", f"Template '{name}' created successfully")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Failed to create template '{name}'")

def show_template_creation_form(parent):
    """Show the enhanced template creation form"""
    dialog = TemplateCreationForm(parent)
    return dialog.exec_() 