#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
License Manager for CR2 Creative applications
Handles license activation, deactivation, validation, and trial period management
"""

import os
import json
import uuid
import time
import hashlib
import platform
import requests
import sys
import importlib.resources # For accessing bundled data files
from datetime import datetime, timedelta
import socket # Added import
import math # Added for time calculations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFormLayout, QMessageBox, QProgressBar, QHBoxLayout
from PyQt6.QtCore import Qt, QSettings, QTimer

# Import styling constants
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE

# Constants
# TRIAL_DAYS = 14 # Old constant
# TRIAL_DURATION_MINUTES_FOR_TESTING = 3  # For testing purposes
# TRIAL_DURATION_SECONDS = TRIAL_DURATION_MINUTES_FOR_TESTING * 60 # For 3-minute testing

# Standard 14-day trial period in seconds
TRIAL_DURATION_SECONDS = 14 * 24 * 60 * 60 

PRODUCTION_URL = "https://ceeo86y6ze.execute-api.us-west-1.amazonaws.com/prod"  # Updated Prod URL
TESTING_URL = "https://ceeo86y6ze.execute-api.us-west-1.amazonaws.com/test"  # Updated Test URL
API_KEY_CONFIG_NAME = "config.json"
API_KEY_FIELD_NAME = "ECHELON_VALIDATION_API_KEY"

# License types
LICENSE_TYPE_PERMANENT = "permanent"
LICENSE_TYPE_ENTERPRISE = "enterprise"
LICENSE_TYPE_SUBSCRIPTION = "subscription"

class LicenseManager:
    """Manages license activation, deactivation, validation, and trial period"""
    
    def __init__(self, use_production=False):
        """Initialize the license manager"""
        self.settings = QSettings("CR2 Creative", "Echelon")
        self.base_url = PRODUCTION_URL if use_production else TESTING_URL
        self.machine_id = self._get_machine_id()
        self.api_key = self._load_api_key_from_config()
        
        if not self.api_key:
            print("CRITICAL ERROR: Could not load API key for license validation.")
            # Depending on app behavior, you might want to raise an exception
            # or ensure validation always fails.
        
    def _get_machine_id(self):
        """Generate a unique machine ID based on hardware information"""
        # Try to get an existing machine ID first
        machine_id = self.settings.value("license/machine_id", "")
        if machine_id:
            return machine_id
            
        # Generate a new machine ID if one doesn't exist
        system_info = [
            platform.node(),
            platform.machine(),
            platform.processor(),
            str(uuid.getnode())  # MAC address
        ]
        
        # Create a hash of the system information
        fingerprint = hashlib.sha256("".join(system_info).encode()).hexdigest()
        
        # Save the machine ID
        self.settings.setValue("license/machine_id", fingerprint)
        return fingerprint
        
    def _load_api_key_from_config(self):
        """Load the API key from the bundled config.json file."""
        try:
            # Use importlib.resources to safely access the data file
            # Assumes config.json is in the 'app.config' package
            config_content = importlib.resources.read_text('app.config', API_KEY_CONFIG_NAME)
            config_data = json.loads(config_content)
            api_key = config_data.get(API_KEY_FIELD_NAME)
            
            if not api_key:
                print(f"ERROR: Field '{API_KEY_FIELD_NAME}' not found in {API_KEY_CONFIG_NAME}.")
                return None
                
            # print("DEBUG: API key loaded successfully.")
            return api_key
            
        except FileNotFoundError:
            print(f"ERROR: Configuration file '{API_KEY_CONFIG_NAME}' not found in package 'app.config'. Ensure it's included in the build.")
            return None
        except json.JSONDecodeError:
            print(f"ERROR: Failed to parse JSON from '{API_KEY_CONFIG_NAME}'.")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error loading API key from config: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def is_trial_active(self):
        """Check if the trial period is active"""
        # Check if a license is already activated
        if self.is_licensed():
            return False
            
        # Check if trial has been started
        trial_start = self.settings.value("license/trial_start", None)
        if not trial_start:
            # First time running the app, start the trial
            trial_start = datetime.now().isoformat()
            self.settings.setValue("license/trial_start", trial_start)
            # Also store the precise end time for the trial
            trial_end_time = (datetime.now() + timedelta(seconds=TRIAL_DURATION_SECONDS)).isoformat()
            self.settings.setValue("license/trial_end_time", trial_end_time)
            # print(f"DEBUG: Trial started. Start: {trial_start}, End: {trial_end_time}")
            return True
            
        # Calculate if trial is still active
        # Use the stored trial_end_time for consistency
        trial_end_iso = self.settings.value("license/trial_end_time", None)
        if not trial_end_iso:
            # Fallback if trial_end_time was somehow not set (e.g., older version)
            # This will effectively reset the trial for this check, which is safer.
            # print("DEBUG: trial_end_time not found. Resetting trial period for this session.")
            start_date_dt = datetime.now()
            self.settings.setValue("license/trial_start", start_date_dt.isoformat())
            trial_end_dt = start_date_dt + timedelta(seconds=TRIAL_DURATION_SECONDS)
            self.settings.setValue("license/trial_end_time", trial_end_dt.isoformat())
            return True

        try:
            # start_date = datetime.fromisoformat(trial_start) # Original start, for reference
            # end_date = start_date + timedelta(days=TRIAL_DAYS) # Old calculation
            end_date = datetime.fromisoformat(trial_end_iso)
            is_active = datetime.now() <= end_date
            if not is_active:
                # print(f"DEBUG: Trial has expired. Current time: {datetime.now()}, End date: {end_date}")
                return False
            return is_active
        except (ValueError, TypeError) as e:
            # If there's any error parsing the date, reset the trial
            # print(f"DEBUG: Error parsing trial dates ({e}). Resetting trial period.")
            trial_start_dt = datetime.now()
            trial_end_dt = trial_start_dt + timedelta(seconds=TRIAL_DURATION_SECONDS)
            self.settings.setValue("license/trial_start", trial_start_dt.isoformat())
            self.settings.setValue("license/trial_end_time", trial_end_dt.isoformat())
            return True
            
    def get_trial_days_remaining(self):
        """Get the number of days remaining in the trial period.
        For very short trial durations (like minutes for testing),
        this will show 0 days for most of the period.
        The actual expiration is handled by is_trial_active()."""
        if self.is_licensed():
            return 0
            
        trial_start_iso = self.settings.value("license/trial_start", None)
        trial_end_iso = self.settings.value("license/trial_end_time", None)

        if not trial_start_iso or not trial_end_iso:
            # If trial hasn't started or end time is missing, return full theoretical duration in days
            # This is a rough estimate for display if full info isn't available
            return TRIAL_DURATION_SECONDS // (24 * 60 * 60) if TRIAL_DURATION_SECONDS >= (24*60*60) else 0
            
        try:
            # start_date = datetime.fromisoformat(trial_start_iso) # Original start
            # end_date_calc = start_date + timedelta(days=TRIAL_DAYS) # Old calculation
            end_date = datetime.fromisoformat(trial_end_iso)
            
            now = datetime.now()
            if now >= end_date:
                return 0
                
            time_left = end_date - now
            # Calculate remaining days. For periods less than a day, this will be 0.
            # If you want to show "1 day" for any remaining time less than 24hrs but >0,
            # you could use: math.ceil(time_left.total_seconds() / (24 * 60 * 60))
            # For simplicity and consistency with current .days behavior:
            days_left = time_left.days 
            return max(0, days_left)
        except (ValueError, TypeError):
            # Fallback on error, return full theoretical duration in days
            return TRIAL_DURATION_SECONDS // (24 * 60 * 60) if TRIAL_DURATION_SECONDS >= (24*60*60) else 0
            
    def get_trial_time_remaining_parts(self):
        """Get the remaining trial time in parts (days, hours, minutes)."""
        if self.is_licensed():
            return {'days': 0, 'hours': 0, 'minutes': 0}

        trial_start_iso = self.settings.value("license/trial_start", None)
        trial_end_iso = self.settings.value("license/trial_end_time", None)

        if not trial_start_iso or not trial_end_iso:
            # Trial hasn't formally started in settings, return full configured duration
            # This assumes is_trial_active() would be called first to set these.
            # If called before that, give the full potential.
            total_days = math.floor(TRIAL_DURATION_SECONDS / (24 * 60 * 60))
            remaining_seconds_for_hours = TRIAL_DURATION_SECONDS % (24 * 60 * 60)
            total_hours = math.floor(remaining_seconds_for_hours / (60*60))
            # For this initial full duration display, minutes are likely not needed / would be 0
            return {'days': int(total_days), 'hours': int(total_hours), 'minutes': 0}

        try:
            end_date = datetime.fromisoformat(trial_end_iso)
            now = datetime.now()

            if now >= end_date:
                return {'days': 0, 'hours': 0, 'minutes': 0}

            time_left_delta = end_date - now
            total_seconds_left = time_left_delta.total_seconds()

            if total_seconds_left <= 0:
                return {'days': 0, 'hours': 0, 'minutes': 0}

            days = math.floor(total_seconds_left / (24 * 60 * 60))
            remaining_seconds = total_seconds_left % (24 * 60 * 60)
            hours = math.floor(remaining_seconds / (60 * 60))
            remaining_seconds %= (60 * 60)
            minutes = math.floor(remaining_seconds / 60)

            return {'days': int(days), 'hours': int(hours), 'minutes': int(minutes)}

        except (ValueError, TypeError):
            # Error parsing dates, return 0 time left as a fallback
            return {'days': 0, 'hours': 0, 'minutes': 0}
            
    def is_licensed(self):
        """Check if the application is licensed"""
        license_key = self.settings.value("license/key", "")
        license_email = self.settings.value("license/email", "")
        
        if not license_key or not license_email:
            return False
            
        # Validate license with server if online
        try:
            return self.validate_license(license_key)
        except:
            # If offline, use cached license status
            return self.settings.value("license/is_valid", False, type=bool)
            
    def activate_license(self, email, license_key, first_name="", last_name="", company=""):
        """Activate a license with the license server"""
        try:
            # --- Added: Gather additional activation details ---
            try:
                machine_name = socket.gethostname()
            except Exception:
                machine_name = "Unknown" # Fallback if hostname cannot be retrieved
            activation_date = datetime.utcnow().isoformat() + 'Z' # Use UTC time in ISO format
            # Note: Public IP address is best determined by the server receiving the request.
            # --- End Added ---

            url = f"{self.base_url}/licenses/activate"
            payload = {
                "email": email,
                "licenseKey": license_key,
                "machineId": self.machine_id,
                "firstName": first_name,
                "lastName": last_name,
                "company": company,
                # --- Added: Include new details in payload ---
                "machineName": machine_name,
                "activationDate": activation_date 
                # --- End Added ---
            }
            
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            # Check response status FIRST
            if response.status_code == 200:
                # Activation successful (either new or already registered)
                try:
                    data = response.json()
                    # print(f"DEBUG [activate_license]: Successful response data = {data}")
                    
                    # Store license information regardless of new/existing
                    self.settings.setValue("license/key", license_key)
                    self.settings.setValue("license/email", data.get("email", email)) # Use response email if available
                    self.settings.setValue("license/type", data.get("licenseType", ""))
                    # Expiry date might not be returned on 'already registered', keep existing if not present
                    if "expiryDate" in data:
                         self.settings.setValue("license/expiry", data.get("expiryDate"))
                    self.settings.setValue("license/is_valid", True) # Set as valid
                    # Activation date should only be set on first activation, maybe skip update here?
                    # Or update if not present?
                    if not self.settings.contains("license/activation_date"):
                        self.settings.setValue("license/activation_date", datetime.now().isoformat())
                    
                    # --- Added: Store the received activationId ---
                    activation_id = data.get("activationId")
                    if activation_id:
                        self.settings.setValue("license/activation_id", activation_id)
                        # print(f"DEBUG: Stored activation ID: {activation_id}")
                    else:
                        # print("WARNING: activationId not found in successful activation response.")
                        pass
                    # --- End Added ---

                    # Update names/company if provided in response (might not be)
                    self.settings.setValue("license/first_name", data.get("firstName", first_name))
                    self.settings.setValue("license/last_name", data.get("lastName", last_name))
                    self.settings.setValue("license/company", data.get("company", company))

                    # Return success, use the message from the response
                    return True, data.get("message", "License activated successfully.")

                except json.JSONDecodeError as e:
                    # Handle case where 200 OK but response is not valid JSON
                    # print(f"ERROR: Activation request successful (200 OK) but failed to parse JSON response: {e}. Response text: {response.text}")
                    # Still treat as success for licensing, but maybe show a generic message?
                    self.settings.setValue("license/is_valid", True) # Assume valid based on 200 OK
                    self.settings.setValue("license/key", license_key)
                    self.settings.setValue("license/email", email)
                    return True, "License confirmed, but response details were unclear."
                except Exception as e:
                    # Catch other errors during processing of successful response
                    # print(f"ERROR: Unexpected error processing successful (200 OK) activation response: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Fallback: treat as success based on 200 OK
                    self.settings.setValue("license/is_valid", True)
                    self.settings.setValue("license/key", license_key)
                    self.settings.setValue("license/email", email)
                    return True, "License confirmed, but encountered an internal processing error."
            else:
                # Handle non-200 status codes (failures)
                # print(f"ERROR: Activation request failed with status {response.status_code}. Response text: {response.text}")
                try:
                    error_message = response.json().get("message", f"Activation failed (Status: {response.status_code})")
                except json.JSONDecodeError:
                    error_message = f"Activation failed (Status: {response.status_code}) - Non-JSON response: {response.text}"
                return False, error_message

        except requests.RequestException as e:
            # print(f"ERROR: Activation connection error: {str(e)}") # Enhanced logging prefix
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            # print(f"ERROR: Unexpected error during activation request: {str(e)}") # Changed message slightly
            import traceback
            traceback.print_exc()
            return False, f"Error: {str(e)}"
            
    def deactivate_license(self):
        """Deactivate the current license with the license server"""
        email = self.settings.value("license/email", "")
        license_key = self.settings.value("license/key", "")
        # --- Added: Retrieve stored activation ID ---
        activation_id = self.settings.value("license/activation_id", "") # Get the specific ID for this activation
        # --- End Added ---
        
        if not email or not license_key:
            return False, "No license is currently activated"
            
        # --- Added: Check for activation_id, though backend might not require it yet --- 
        if not activation_id:
            # print("WARNING: No activation ID found locally. Sending deactivation without it. Backend might require this in the future.")
            pass
        # --- End Added ---

        try:
            url = f"{self.base_url}/licenses/deactivate"
            payload = {
                "email": email,
                "licenseKey": license_key,
                "machineId": self.machine_id,
                # --- Added: Include activation ID in payload --- 
                "activationId": activation_id # Send the specific activation ID
                # --- End Added ---
            }
            
            # Add headers with API key
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            # Check response status before trying to parse JSON
            if response.status_code != 200:
                # print(f"ERROR: Deactivation request failed with status {response.status_code}. Response text: {response.text}")
                try:
                    error_message = response.json().get("message", f"Deactivation failed (Status: {response.status_code})")
                except json.JSONDecodeError:
                    error_message = f"Deactivation failed (Status: {response.status_code}) - Non-JSON response: {response.text}"
                return False, error_message

            data = response.json()
            message = data.get("message", "") # Get message for checking
            is_explicit_success = data.get("status") == "success"
            is_already_inactive = "not found" in message.lower() # Check if backend says it's not found
            
            # --- Updated: Clear local data if successful OR if backend says 'not found' --- 
            if is_explicit_success or is_already_inactive:
            # --- End Updated ---
                # Clear license information
                self.settings.remove("license/key")
                self.settings.remove("license/email")
                self.settings.remove("license/type")
                self.settings.remove("license/expiry")
                # --- Updated: Explicitly set is_valid to False --- 
                self.settings.setValue("license/is_valid", False) 
                # --- End Updated ---
                self.settings.remove("license/activation_date")
                # --- Added: Remove activation ID on successful deactivation --- 
                self.settings.remove("license/activation_id")
                # --- End Added ---
                self.settings.remove("license/first_name")
                self.settings.remove("license/last_name")
                self.settings.remove("license/company")
                
                # Return True only on explicit success, but pass the message along
                return is_explicit_success, message or "License deactivated successfully"
            else:
                 # Log failure details even if status was 200 but status field wasn't "success" and message didn't say 'not found'
                # print(f"ERROR: Deactivation successful status code (200) but failed status/message in body. Response: {data}")
                return False, message or "License deactivation failed"
        except requests.RequestException as e:
            # print(f"ERROR: Deactivation connection error: {str(e)}") # Enhanced logging prefix
            return False, f"Connection error: {str(e)}"
        except json.JSONDecodeError as e:
             # print(f"ERROR: Failed to parse deactivation response JSON: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}") # Log raw text on JSON error
             return False, "Error parsing server response."
        except Exception as e:
            # print(f"ERROR: Unexpected error during deactivation: {str(e)}") # Enhanced logging prefix
            import traceback
            traceback.print_exc()
            return False, f"Error: {str(e)}"
            
    def validate_license(self, license_key=None):
        """Validate the license with the license server using only the license key."""
        # If no API key was loaded during init, fail validation
        if not self.api_key:
            # print("ERROR: Cannot validate license - API key is missing.")
            return False
            
        # If no key provided, try to get it from settings
        if license_key is None:
            license_key = self.settings.value("license/key", "")
            
        if not license_key:
            # print("DEBUG: validate_license - No license key found.")
            return False
            
        try:
            # Construct the specific validation URL
            url = f"{self.base_url}/licenses/validate"
            payload = {
                "licenseKey": license_key
            }
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key  # Add the API key header
            }

            # print(f"DEBUG: Headers being sent: {headers}")

            # print(f"DEBUG: Validating license key at {url} with payload: {payload}")
            # Note: Do not print headers in production logs if they contain sensitive info
            # print(f"DEBUG: Headers: {headers}") 
            response = requests.post(url, json=payload, headers=headers)
            
            # Log details for specific auth errors
            if response.status_code == 401 or response.status_code == 403:
                 # print(f"ERROR: License validation authentication failed (Status: {response.status_code}). Check API Key. Response text: {response.text}")
                 self.settings.setValue("license/is_valid", False)
                 return False
                 
            # Check for other non-200 status codes before raising exception or parsing JSON
            if response.status_code != 200:
                # print(f"ERROR: License validation request failed with status {response.status_code}. Response text: {response.text}")
                # Attempt to raise specific HTTPError, but log first
                try:
                    response.raise_for_status() 
                except requests.exceptions.HTTPError as http_err:
                    # print(f"DEBUG: HTTPError raised: {http_err}") # Log the specific HTTPError
                    pass
                
                # Fallback to cached status after logging non-200 response
                cached_status = self.settings.value("license/is_valid", False, type=bool)
                # print(f"DEBUG: Falling back to cached license status after non-200 response: {cached_status}")
                return cached_status

            # If status is 200, proceed to parse JSON
            data = response.json()
            # print(f"DEBUG: Validation response received: {data}") # Keep commented unless debugging success case
            
            # Check the 'isValid' field specifically
            is_valid = data.get("isValid", False)
            
            # Store the validation status
            self.settings.setValue("license/is_valid", is_valid)
            
            # Update other license details if valid and present in response
            if is_valid:
                self.settings.setValue("license/type", data.get("licenseType", self.settings.value("license/type", "")))
                self.settings.setValue("license/expiry", data.get("expiryDate", self.settings.value("license/expiry", "")))
                self.settings.setValue("license/email", data.get("email", self.settings.value("license/email", "")))
                self.settings.setValue("license/first_name", data.get("firstName", self.settings.value("license/first_name", "")))
                self.settings.setValue("license/last_name", data.get("lastName", self.settings.value("license/last_name", "")))
                self.settings.setValue("license/company", data.get("company", self.settings.value("license/company", "")))

            # print(f"DEBUG: License validation result: {is_valid}") # Keep commented unless debugging success case
            return is_valid
            
        except requests.exceptions.RequestException as e:
            # ... existing logging ...
            cached_status = self.settings.value("license/is_valid", False, type=bool)
            # print(f"DEBUG: Falling back to cached license status: {cached_status}")
            return cached_status
        except json.JSONDecodeError as e:
            # Log raw text on JSON error
            # print(f"ERROR: Failed to parse validation response JSON: {e}. Status Code: {response.status_code if 'response' in locals() else 'N/A'}. Response text: {response.text if 'response' in locals() else 'N/A'}") 
            self.settings.setValue("license/is_valid", False)
            return False
        except Exception as e:
            # ... existing logging ...
            cached_status = self.settings.value("license/is_valid", False, type=bool)
            # print(f"DEBUG: Falling back to cached license status due to unexpected error: {cached_status}")
            return cached_status
            
    def get_license_info(self):
        """Get information about the current license"""
        if not self.is_licensed():
            return None
            
        return {
            "email": self.settings.value("license/email", ""),
            "key": self.settings.value("license/key", ""),
            "type": self.settings.value("license/type", ""),
            "expiry": self.settings.value("license/expiry", ""),
            "activation_date": self.settings.value("license/activation_date", ""),
            # --- Added: Include activation_id in info --- 
            "activation_id": self.settings.value("license/activation_id", ""), 
            # --- End Added ---
            "first_name": self.settings.value("license/first_name", ""),
            "last_name": self.settings.value("license/last_name", ""),
            "company": self.settings.value("license/company", "")
        }
        
    def clear_license_data(self):
        """Clear all license data (for testing purposes)"""
        keys = [
            "license/key", 
            "license/email", 
            "license/type", 
            "license/expiry", 
            "license/is_valid", 
            "license/activation_date",
            # --- Added: Include activation_id in clear list --- 
            "license/activation_id",
            # --- End Added ---
            "license/trial_start",
            "license/first_name",
            "license/last_name",
            "license/company"
        ]
        
        for key in keys:
            self.settings.remove(key)

class LicenseActivationDialog(QDialog):
    """Dialog for license activation"""
    
    def __init__(self, parent=None, license_manager=None):
        super().__init__(parent)
        self.license_manager = license_manager or LicenseManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        from app.ui.color_scheme_pyqt import colors
        
        self.setWindowTitle("License Activation")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # Form layout for input fields
        form_layout = QFormLayout()
        
        self.email_input = QLineEdit()
        self.email_input.setMinimumWidth(450)
        
        self.license_key_input = QLineEdit()
        self.license_key_input.setMinimumWidth(450)
        
        self.first_name_input = QLineEdit()
        self.first_name_input.setMinimumWidth(450)
        
        self.last_name_input = QLineEdit()
        self.last_name_input.setMinimumWidth(450)
        
        self.company_input = QLineEdit()
        self.company_input.setMinimumWidth(450)
        
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("License Key:", self.license_key_input)
        form_layout.addRow("First Name:", self.first_name_input)
        form_layout.addRow("Last Name:", self.last_name_input)
        form_layout.addRow("Company:", self.company_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        self.activate_button = QPushButton("Activate License")
        self.activate_button.clicked.connect(self.activate_license)
        self.activate_button.setStyleSheet(f"""
            {ACCENT_BUTTON_STYLE}
            QPushButton:hover {{
                 background-color: {colors['accent_hover']};
            }}
        """)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.activate_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def activate_license(self):
        """Handle license activation"""
        email = self.email_input.text().strip()
        license_key = self.license_key_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        company = self.company_input.text().strip()
        
        if not email or not license_key:
            QMessageBox.warning(self, "Activation Error", "Please enter both email and license key.")
            return
            
        # Show progress indicator
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Activating License")
        progress_layout = QVBoxLayout()
        progress_label = QLabel("Contacting license server...")
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate progress
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar)
        progress_dialog.setLayout(progress_layout)
        progress_dialog.show()
        
        # Process events to update UI
        QTimer.singleShot(100, lambda: self._perform_activation(email, license_key, first_name, last_name, company, progress_dialog))
        
    def _perform_activation(self, email, license_key, first_name, last_name, company, progress_dialog):
        """Perform the actual license activation"""
        success, message = self.license_manager.activate_license(email, license_key, first_name, last_name, company)
        progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "Activation Successful", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Activation Failed", message)

class TrialNagDialog(QDialog):
    """Dialog shown when trial period is active or expired"""
    
    def __init__(self, parent=None, license_manager=None, time_parts=None): # Changed days_left to time_parts
        super().__init__(parent)
        self.license_manager = license_manager or LicenseManager()
        # self.days_left = days_left # Old
        self.time_parts = time_parts if time_parts is not None else {'days': 0, 'hours': 0, 'minutes': 0}
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        from app.ui.color_scheme_pyqt import colors
        
        self.setWindowTitle("Trial Period")
        self.setMinimumWidth(600)  # Increased width to match activation dialog
        
        layout = QVBoxLayout()
        layout.addStretch(1) # Add stretch at the top
        
        # Message
        days = self.time_parts.get('days', 0)
        hours = self.time_parts.get('hours', 0)
        minutes = self.time_parts.get('minutes', 0)

        is_trial_time_left = days > 0 or hours > 0 or minutes > 0
        
        if is_trial_time_left:
            time_str_parts = []
            if days > 0:
                time_str_parts.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                time_str_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            # Updated logic: Always add minutes to the list if they are non-zero.
            if minutes > 0:
                time_str_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

            if not time_str_parts:
                # This case should ideally be covered by is_trial_time_left being false
                # or get_trial_time_remaining_parts returning non-zero if seconds are left.
                # If somehow is_trial_time_left is true but all parts are 0 (e.g. <1 min and no seconds part),
                # provide a fallback string.
                time_display_str = "less than a minute"
            elif len(time_str_parts) > 1:
                time_display_str = ", ".join(time_str_parts[:-1]) + " and " + time_str_parts[-1]
            else:
                time_display_str = time_str_parts[0]
            
            # message = f"You are using the trial version of Echelon.\\n\\nYou have {time_display_str} remaining in your trial period." # Old message
            message = f"You are using the trial version of Echelon.\nTime remaining: {time_display_str}."
        else:
            message = "Your trial period has expired.\\n\\nPlease purchase a license to continue using Echelon."
            
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlagFlagFlag.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Activate Button (Always shown)
        self.activate_button = QPushButton("Activate License")
        # Add hover state to existing ACCENT_BUTTON_STYLE
        self.activate_button.setStyleSheet(f"""
            {ACCENT_BUTTON_STYLE}
            QPushButton:hover {{
                 background-color: {colors['accent_hover']}; 
            }}
        """)
        self.activate_button.clicked.connect(self.open_activation_dialog) # Connect to activation dialog method
        button_layout.addWidget(self.activate_button)
        
        # Continue Trial Button (Conditional)
        # if self.days_left > 0: # Old condition
        if is_trial_time_left: # New condition
            # self.continue_button = QPushButton(f"Continue Trial ({self.days_left} days left)") # Old text
            # Construct button text similarly to the message
            btn_time_str_parts = []
            if days > 0:
                btn_time_str_parts.append(f"{days}d")
            if hours > 0:
                btn_time_str_parts.append(f"{hours}h")
            if days == 0 and minutes > 0 : # Only show minutes on button if no days
                btn_time_str_parts.append(f"{minutes}m")
            
            btn_time_display_str = " ".join(btn_time_str_parts)
            if not btn_time_display_str: # e.g. less than a minute if we don't show seconds
                 btn_time_display_str = "<1m" # Or handle as expired if minutes is the finest granuality

            self.continue_button = QPushButton(f"Continue Trial ({btn_time_display_str} left)")
            # Add hover state to existing BUTTON_STYLE
            self.continue_button.setStyleSheet(f"""
                {BUTTON_STYLE}
                QPushButton:hover {{
                    background-color: {colors['hover_bg']};
                    border: 1px solid {colors['accent']};
                }}
            """)
            self.continue_button.clicked.connect(self.accept) # Accept just closes to continue trial
            button_layout.insertWidget(0, self.continue_button) # Place it to the left
        else:
            # If trial expired, show an Exit button instead of Continue Trial
            # We might not need an explicit Exit button if activate/close handles it.
            # Let's adjust the activate button text instead.
            self.activate_button.setText("Activate License")
            # Add an informative label above the button
            trial_expired_label = QLabel("Your trial has expired. Please activate to continue using Echelon.")
            trial_expired_label.setStyleSheet("color: yellow;") # Make it noticeable
            trial_expired_label.setWordWrap(True)
            trial_expired_label.setAlignment(Qt.AlignmentFlagFlagFlag.AlignCenter) # Center align this label too
            
            # The original insertWidget call places trial_expired_label before message_label if not handled carefully.
            # Original logic: layout.insertWidget(layout.count() -1, trial_expired_label)
            # Given message_label is already added, and button_layout is added last,
            # to maintain trial_expired_label (yellow) visually before the main purchase message,
            # we need to ensure correct insertion or ordering if we change how widgets are added.

            # Let's re-evaluate the order of addition for clarity:
            # The current effective order from previous analysis is [trial_expired_label, message_label, button_layout]
            # The code is:
            # 1. `layout.addWidget(message_label)` (This adds the "Please purchase..." message)
            # 2. If expired: `trial_expired_label` is created.
            # 3. `layout.insertWidget(layout.count() -1, trial_expired_label)` -> Inserts yellow label at index 0 if message_label is the only thing in layout.
            #    This means `layout` becomes `[trial_expired_label, message_label]`. This matches screenshot.

            # So, the insertion logic is fine for order. We've already added message_label.
            # The `trial_expired_label` should appear before the `message_label` if that's desired.
            # The screenshot implies yellow text (trial_expired_label) is first.
            # The code `layout.insertWidget(layout.count() - 1, trial_expired_label)` when `layout` contains just `[message_label]` (count=1),
            # means `insertWidget(0, trial_expired_label)`. So the yellow label becomes the first item. This is correct.

            # We need to ensure the trial_expired_label is correctly placed in the layout IF it's created.
            # The current structure adds message_label, then if expired, trial_expired_label is inserted at index 0.
            # This means trial_expired_label will appear above message_label.
            # No change needed to insertion logic itself, just ensuring trial_expired_label uses AlignCenter.
            
            # Original placement logic for trial_expired_label seems correct for the visual order in screenshot
            # (yellow first, then standard message_label).
            # The `insertWidget` call effectively places it before the `message_label` that was added earlier.
            current_widget_count = layout.count()
            if current_widget_count > 0:
                # If message_label (or anything else) is already in layout, insert yellow label before the last one.
                # If message_label is the only item, this inserts at index 0.
                layout.insertWidget(current_widget_count -1, trial_expired_label)
            else: # Should not happen if message_label is always added first
                layout.addWidget(trial_expired_label)

        layout.addLayout(button_layout) # Add the button layout to the main layout
        layout.addStretch(1) # Add stretch at the bottom
        
        self.setLayout(layout)
        
    def open_activation_dialog(self):
        """Opens the separate ActivationDialog."""
        dialog = LicenseActivationDialog(self, self.license_manager)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            self.accept() 