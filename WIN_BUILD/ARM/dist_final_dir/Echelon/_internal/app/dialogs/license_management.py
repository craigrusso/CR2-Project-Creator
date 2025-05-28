#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
License Management Dialog
Provides a user interface for managing licenses in the application
"""

import os
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QTabWidget, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings

from app.utils.security.license_manager import (
    LicenseManager, LicenseActivationDialog,
    LICENSE_TYPE_PERMANENT, LICENSE_TYPE_ENTERPRISE, LICENSE_TYPE_SUBSCRIPTION
)

class LicenseManagementDialog(QDialog):
    """Dialog for managing licenses"""
    
    def __init__(self, parent=None, license_manager=None):
        super().__init__(parent)
        self.license_manager = license_manager or LicenseManager()
        self.setup_ui()
        self.load_license_info()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        from app.ui.color_scheme_pyqt import colors
        
        self.setWindowTitle("License Management")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # Create tabs
        self.tab_widget = QTabWidget()
        self.license_info_tab = QWidget()
        self.activation_tab = QWidget()
        
        self.tab_widget.addTab(self.license_info_tab, "License Information")
        self.tab_widget.addTab(self.activation_tab, "License Activation")
        
        # Setup license info tab
        self.setup_license_info_tab()
        
        # Setup activation tab
        self.setup_activation_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def setup_license_info_tab(self):
        """Set up the license information tab"""
        from app.ui.color_scheme_pyqt import colors
        
        layout = QVBoxLayout()
        
        # License status group
        status_group = QGroupBox("License Status")
        status_layout = QFormLayout()  # Use QFormLayout for key-value pairs
        status_layout.setSpacing(10)  # Add spacing between rows
        status_layout.setLabelAlignment(Qt.AlignmentFlagFlagFlag.AlignRight) # Align labels to the right
        
        self.status_label = QLabel("Checking...")
        self.license_type_label = QLabel("--")
        self.expiry_date_label = QLabel("--")
        self.email_label = QLabel("--")
        self.name_label = QLabel("--")
        self.company_label = QLabel("--")
        
        status_layout.addRow("Status:", self.status_label)
        status_layout.addRow("License Type:", self.license_type_label)
        status_layout.addRow("Expiry Date:", self.expiry_date_label)
        status_layout.addRow("Registered Email:", self.email_label)
        status_layout.addRow("Registered Name:", self.name_label)
        status_layout.addRow("Company:", self.company_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Trial information group
        trial_group = QGroupBox("Trial Information")
        trial_layout = QFormLayout()
        trial_layout.setSpacing(10)
        trial_layout.setLabelAlignment(Qt.AlignmentFlagFlagFlag.AlignRight)
        
        self.trial_status_label = QLabel("Checking...")
        self.trial_days_label = QLabel("--")
        
        trial_layout.addRow("Trial Status:", self.trial_status_label)
        trial_layout.addRow("Days Remaining:", self.trial_days_label)
        
        trial_group.setLayout(trial_layout)
        layout.addWidget(trial_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.deactivate_button = QPushButton("Deactivate License")
        self.deactivate_button.clicked.connect(self.deactivate_license)
        self.deactivate_button.setEnabled(False)
        self.deactivate_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 8px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {colors['hover_bg']};
                border: 1px solid {colors['accent']};
            }}
            QPushButton:pressed {{
                background-color: {colors['accent']}; /* Or consider colors['hover_bg'] */
                color: {colors['highlight_text']};
            }}
             QPushButton:disabled {{
                background-color: {colors['card_bg']}; /* Keep background */
                color: {colors['secondary_text']}; /* Dim text */
                border: 1px solid {colors['border']}; /* Keep border */
            }}
        """)
        
        self.purchase_button = QPushButton("Purchase License")
        self.purchase_button.clicked.connect(self.open_purchase_website)
        self.purchase_button.setStyleSheet(f"background-color: {colors['accent']}; color: white; padding: 8px; border-radius: 3px;")
        
        actions_layout.addWidget(self.deactivate_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.purchase_button)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        self.license_info_tab.setLayout(layout)
        
    def setup_activation_tab(self):
        """Set up the license activation tab"""
        from app.ui.color_scheme_pyqt import colors
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions_label = QLabel("Enter your license details to activate the application:")
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)
        
        # Form layout for input fields
        form_group = QGroupBox("License Details")
        form_layout = QFormLayout()
        
        self.activation_email_input = QLabel("Please visit our website to purchase a license.")
        self.activation_key_input = QLabel("Once purchased, you will receive an email with your license key.")
        
        form_layout.addRow("Email:", self.activation_email_input)
        form_layout.addRow("License Key:", self.activation_key_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Activation button
        self.open_activation_dialog_button = QPushButton("Enter License Key")
        self.open_activation_dialog_button.clicked.connect(self.open_activation_dialog)
        self.open_activation_dialog_button.setStyleSheet(f"background-color: {colors['accent']}; color: white; padding: 8px;")
        
        purchase_layout = QHBoxLayout()
        purchase_layout.addStretch()
        purchase_layout.addWidget(self.open_activation_dialog_button)
        purchase_layout.addStretch()
        
        layout.addLayout(purchase_layout)
        
        # License types explanation
        license_types_group = QGroupBox("Available License Types")
        license_types_layout = QVBoxLayout()
        
        permanent_label = QLabel("<b>Permanent License:</b> Use the software indefinitely. Updates available for 1 year from purchase.")
        permanent_label.setWordWrap(True)
        
        enterprise_label = QLabel("<b>Enterprise License:</b> Multiple installations for a single company. Ability to deactivate and reactivate on different machines.")
        enterprise_label.setWordWrap(True)
        
        subscription_label = QLabel("<b>Subscription License:</b> Full access during the subscription period. Includes all updates.")
        subscription_label.setWordWrap(True)
        
        license_types_layout.addWidget(permanent_label)
        license_types_layout.addWidget(enterprise_label)
        license_types_layout.addWidget(subscription_label)
        
        license_types_group.setLayout(license_types_layout)
        layout.addWidget(license_types_group)
        
        layout.addStretch()
        
        self.activation_tab.setLayout(layout)
        
    def load_license_info(self):
        """Load and display license information"""
        # Check if licensed
        if self.license_manager.is_licensed():
            self.status_label.setText("Licensed")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.deactivate_button.setEnabled(True)
            
            # Get license info
            license_info = self.license_manager.get_license_info()
            if license_info:
                # Set license type
                license_type = license_info.get("type", "")
                if license_type == LICENSE_TYPE_PERMANENT:
                    self.license_type_label.setText("Permanent")
                elif license_type == LICENSE_TYPE_ENTERPRISE:
                    self.license_type_label.setText("Enterprise")
                elif license_type == LICENSE_TYPE_SUBSCRIPTION:
                    self.license_type_label.setText("Subscription")
                else:
                    self.license_type_label.setText(license_type.capitalize() if license_type else "Unknown")
                    
                # Set expiry date
                expiry_date = license_info.get("expiry", "")
                self.expiry_date_label.setText(expiry_date if expiry_date else "Perpetual")
                
                # Set email
                email = license_info.get("email", "")
                self.email_label.setText(email)
                
                # Set name
                first_name = license_info.get("first_name", "")
                last_name = license_info.get("last_name", "")
                full_name = f"{first_name} {last_name}".strip()
                self.name_label.setText(full_name if full_name else "--")
                
                # Set company
                company = license_info.get("company", "")
                self.company_label.setText(company if company else "--")
        else:
            self.status_label.setText("Unlicensed")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.deactivate_button.setEnabled(False)
            
            self.license_type_label.setText("--")
            self.expiry_date_label.setText("--")
            self.email_label.setText("--")
            self.name_label.setText("--")
            self.company_label.setText("--")
        
        # Trial information
        days_left = self.license_manager.get_trial_days_remaining()
        if self.license_manager.is_licensed():
            self.trial_status_label.setText("N/A (Licensed)")
            self.trial_days_label.setText("N/A")
        elif days_left > 0:
            self.trial_status_label.setText("Active")
            self.trial_status_label.setStyleSheet("color: green;")
            self.trial_days_label.setText(str(days_left))
        else:
            self.trial_status_label.setText("Expired")
            self.trial_status_label.setStyleSheet("color: red;")
            self.trial_days_label.setText("0")
        
    def deactivate_license(self):
        """Deactivate the current license"""
        confirm = QMessageBox.question(
            self,
            "Confirm Deactivation",
            "Are you sure you want to deactivate this license? "
            "The application will revert to trial mode if the trial period is still active.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            success, message = self.license_manager.deactivate_license()
            
            if success:
                QMessageBox.information(self, "Deactivation Successful", message)
                self.load_license_info()
            else:
                QMessageBox.warning(self, "Deactivation Failed", message)
    
    def open_purchase_website(self):
        """Open the license purchase website"""
        webbrowser.open("https://testing.cr2creative.com/pricing.html")
    
    def open_activation_dialog(self):
        """Open the license activation dialog"""
        dialog = LicenseActivationDialog(self, self.license_manager)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            self.load_license_info() 