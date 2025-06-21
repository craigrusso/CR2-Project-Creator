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

# Import for version release date checking
from app.config.app_config import APP_VERSION_NUMBER, APP_BUILD_NUMBER

# Constants
# TRIAL_DAYS = 14 # Old constant
# TRIAL_DURATION_MINUTES_FOR_TESTING = 3  # For testing purposes
# TRIAL_DURATION_SECONDS = TRIAL_DURATION_MINUTES_FOR_TESTING * 60 # For 3-minute testing

# Standard 14-day trial period in seconds
TRIAL_DURATION_SECONDS = 14 * 24 * 60 * 60 

# License validation intervals - Updated for business model
FULL_LICENSE_CHECK_INTERVAL = 30 * 24 * 60 * 60  # 30 days (monthly) for permanent/enterprise
SUBSCRIPTION_CHECK_INTERVAL = 15 * 24 * 60 * 60   # 15 days (bi-monthly) for subscriptions

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
            platform.node(),                    # Computer name
            platform.machine(),                 # Architecture (arm64, x86_64)
            platform.processor(),               # Processor info
            str(uuid.getnode()),                # MAC address
            platform.system(),                  # Operating system
            platform.version()[:50],            # OS version (truncated to avoid too long strings)
        ]
        
        # Add additional platform-specific identifiers
        try:
            if platform.system() == "Darwin":  # macOS
                # Add system boot UUID if available
                import subprocess
                result = subprocess.run(["system_profiler", "SPHardwareDataType"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Extract hardware UUID if present
                    for line in result.stdout.split('\n'):
                        if 'Hardware UUID' in line:
                            uuid_part = line.split(':')[-1].strip()
                            if uuid_part:
                                system_info.append(uuid_part)
                            break
            elif platform.system() == "Windows":
                # Add Windows machine GUID
                try:
                    import subprocess
                    result = subprocess.run(["wmic", "csproduct", "get", "UUID"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            uuid_part = lines[1].strip()
                            if uuid_part and uuid_part != "UUID":
                                system_info.append(uuid_part)
                except:
                    pass
        except Exception:
            # If platform-specific info fails, continue with basic info
            pass
        
        # Create a hash of the system information
        combined_info = "|".join(str(info) for info in system_info if info)
        fingerprint = hashlib.sha256(combined_info.encode('utf-8')).hexdigest()
        
        # Save the machine ID
        self.settings.setValue("license/machine_id", fingerprint)
        return fingerprint

    def _get_machine_name(self):
        """Get a human-readable machine name"""
        try:
            machine_name = platform.node()
            if not machine_name or machine_name.strip() == "":
                # Fallback to a combination of system info
                machine_name = f"{platform.system()}-{platform.machine()}"
            return machine_name
        except Exception:
            return "Unknown-Machine"
        
    def _load_api_key_from_config(self):
        """Load the API key from the config file"""
        try:
            # Try to load from bundled config first
            if hasattr(importlib.resources, 'files'):
                # Python 3.9+
                config_path = importlib.resources.files('app.config') / API_KEY_CONFIG_NAME
                if config_path.exists():
                    config_data = json.loads(config_path.read_text())
                    return config_data.get(API_KEY_FIELD_NAME)
            else:
                # Python 3.8 fallback
                with importlib.resources.open_text('app.config', API_KEY_CONFIG_NAME) as f:
                    config_data = json.load(f)
                    return config_data.get(API_KEY_FIELD_NAME)
        except Exception as e:
            print(f"ERROR: Could not load API key from bundled config: {e}")
        
        # Fallback: try to load from local config file
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', API_KEY_CONFIG_NAME)
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                return config_data.get(API_KEY_FIELD_NAME)
        except Exception as e:
            print(f"ERROR: Could not load API key from local config: {e}")
        
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
                machine_name = self._get_machine_name()
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
                    
                    # Verify email matches the one associated with license in the database
                    license_email = data.get("email", "")
                    if license_email and license_email.lower() != email.lower():
                        return False, f"Email address does not match the one registered with this license. Please try again or contact support at https://www.cr2creative.com/support.html"
                    
                    # Store license information regardless of new/existing
                    self.settings.setValue("license/key", license_key)
                    self.settings.setValue("license/email", license_email or email) # Use response email if available
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
                    error_data = response.json()
                    error_message = error_data.get("message", f"Activation failed (Status: {response.status_code})")
                    
                    # Enhanced error handling for 1-machine-per-license policy
                    if response.status_code == 409:  # Conflict - license already activated
                        if "already activated" in error_message.lower():
                            existing_machine = error_data.get("existingMachine", "another machine")
                            enhanced_message = (
                                f"This license is already activated on {existing_machine}.\n\n"
                                f"Each license can only be used on one machine at a time.\n\n"
                                f"To use this license on this machine:\n"
                                f"1. Deactivate the license on {existing_machine}\n"
                                f"2. Then activate it on this machine\n\n"
                                f"Contact support at https://www.cr2creative.com/support.html if you need help."
                            )
                            return False, enhanced_message
                    elif response.status_code == 400:  # Bad request
                        if "invalid" in error_message.lower() or "not found" in error_message.lower():
                            enhanced_message = (
                                f"License key not found or invalid.\n\n"
                                f"Please check:\n"
                                f"• License key is entered correctly\n"
                                f"• Email matches your purchase receipt\n"
                                f"• License hasn't been refunded or cancelled\n\n"
                                f"Contact support at https://www.cr2creative.com/support.html if you need help."
                            )
                            return False, enhanced_message
                    
                    return False, error_message
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
            
        # --- Added: Check for activation_id, backend now requires it --- 
        if not activation_id:
            # If no activation ID, try to deactivate by machine ID only
            # Some older activations might not have stored activation IDs
            pass
        # --- End Added ---

        try:
            url = f"{self.base_url}/licenses/deactivate"
            payload = {
                "email": email,
                "licenseKey": license_key,
                "machineId": self.machine_id,
            }
            
            # Only include activationId if we have one
            if activation_id:
                payload["activationId"] = activation_id
            # --- End Added ---
            
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
                    error_data = response.json()
                    error_message = error_data.get("message", error_data.get("error", f"Deactivation failed (Status: {response.status_code})"))
                    
                    # Special handling for 400 errors with missing activationId
                    if response.status_code == 400 and "activationId" in error_message:
                        # This might be a legacy activation without stored activationId
                        # Force a license validation to see if deactivation actually worked
                        validation_result = self._validate_license_with_server()
                        if not validation_result:
                            # License is now invalid, so deactivation probably worked
                            # Clear local data and treat as success
                            self.settings.remove("license/key")
                            self.settings.remove("license/email")
                            self.settings.remove("license/type")
                            self.settings.remove("license/expiry")
                            self.settings.setValue("license/is_valid", False)
                            self.settings.remove("license/activation_date")
                            self.settings.remove("license/activation_id")
                            self.settings.remove("license/first_name")
                            self.settings.remove("license/last_name")
                            self.settings.remove("license/company")
                            self.settings.sync()
                            return True, "License deactivated successfully (legacy activation)"
                        else:
                            # License is still valid, so deactivation failed
                            return False, f"Deactivation failed: {error_message}"
                    
                except json.JSONDecodeError:
                    error_message = f"Deactivation failed (Status: {response.status_code}) - Non-JSON response: {response.text}"
                return False, error_message

            data = response.json()
            message = data.get("message", "") # Get message for checking
            is_explicit_success = data.get("status") == "success"
            is_already_inactive = "not found" in message.lower() # Check if backend says it's not found
            is_deactivation_successful = "deactivation successful" in message.lower() # Check for successful deactivation message
            
            # --- Updated: Clear local data if successful OR if backend says 'not found' OR if deactivation successful --- 
            if is_explicit_success or is_already_inactive or is_deactivation_successful:
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
                
                # Force settings to sync immediately
                self.settings.sync()
                
                # Force a server validation check to ensure state is synchronized
                self._validate_license_with_server()
                
                # FIX: If we get "not found" message, consider it a success because the license is effectively deactivated
                if is_already_inactive:
                    return True, "License deactivated successfully"
                else:
                    return True, message or "License deactivated successfully"
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
        
        # Get the stored email for comparison
        stored_email = self.settings.value("license/email", "")
            
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
            
            # Additional check: verify email matches the one associated with the license
            if is_valid and stored_email:
                license_email = data.get("email", "")
                if license_email and license_email.lower() != stored_email.lower():
                    # print(f"ERROR: Email mismatch during validation. Stored: {stored_email}, Server: {license_email}")
                    self.settings.setValue("license/is_valid", False)
                    return False
            
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

    def _redact_email(self, email):
        """Redact the email address for security purposes"""
        if not email or '@' not in email:
            return "****@****.***"  # Default redacted format
            
        # Split the email into local part and domain
        local_part, domain = email.split('@', 1)
            
        # Redact the local part
        if len(local_part) <= 2:
            redacted_local = local_part[0] + '*' * (len(local_part) - 1) if local_part else '*'
        else:
            redacted_local = local_part[0] + '*' * (len(local_part) - 2) + local_part[-1]
            
        # Redact the domain, but keep the domain extension visible
        domain_parts = domain.split('.')
        if len(domain_parts) > 1:
            domain_name = '.'.join(domain_parts[:-1])
            extension = domain_parts[-1]
            
            if len(domain_name) <= 2:
                redacted_domain = domain_name[0] + '*' * (len(domain_name) - 1) if domain_name else '*'
            else:
                redacted_domain = domain_name[0] + '*' * (len(domain_name) - 2) + domain_name[-1]
                
            redacted_domain = redacted_domain + '.' + extension
        else:
            redacted_domain = '*' * len(domain)
            
        return redacted_local + '@' + redacted_domain

    def should_run_full_license_check(self):
        """Determine if a full license validation should be performed"""
        current_time = time.time()
        last_check = self.settings.value("license/last_full_check", 0, type=float)
        
        license_type = self.settings.value("license/type", "")
        
        # Use different intervals based on license type
        if license_type == LICENSE_TYPE_SUBSCRIPTION:
            interval = SUBSCRIPTION_CHECK_INTERVAL  # More frequent for subscriptions
        else:
            interval = FULL_LICENSE_CHECK_INTERVAL   # Standard interval
        
        return (current_time - last_check) > interval

    def mark_full_license_check_completed(self):
        """Mark that a full license check was completed"""
        self.settings.setValue("license/last_full_check", time.time())

    def get_version_release_date(self):
        """Fetch the release date for the current app version from the server"""
        try:
            # Use the same API that the update checker uses
            from app.utils.utils import load_config
            config = load_config()
            api_url = config.get("api_urls", {}).get("get_public_downloads")
            
            if not api_url:
                print("ERROR: Could not get API URL for version info")
                return None
            
            # Get current platform
            current_platform = platform.system().lower()
            platform_map = {"darwin": "macos", "windows": "windows", "linux": "linux"}
            target_platform = platform_map.get(current_platform)
            
            if not target_platform:
                print(f"ERROR: Unsupported platform: {current_platform}")
                return None
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            versions_data = response.json()
            
            # Find the current version and build
            current_version = APP_VERSION_NUMBER
            current_build = str(APP_BUILD_NUMBER)
            
            for version_info in versions_data:
                if (version_info.get('platform', '').lower() == target_platform and
                    version_info.get('versionNumber') == current_version and
                    str(version_info.get('buildNumber', '')) == current_build):
                    
                    release_date_str = version_info.get('releaseDate')
                    if release_date_str:
                        # Parse the release date - expect ISO format from server
                        try:
                            release_date = datetime.fromisoformat(release_date_str.replace('Z', '+00:00'))
                            return release_date
                        except ValueError:
                            # Try display format as fallback
                            try:
                                release_date = datetime.strptime(release_date_str, "%b %d, %Y")
                                return release_date
                            except ValueError:
                                print(f"ERROR: Could not parse release date: {release_date_str}")
                                return None
            
            print(f"WARNING: Could not find release date for version {current_version} build {current_build}")
            return None
            
        except Exception as e:
            print(f"ERROR: Failed to fetch version release date: {e}")
            return None

    def is_version_allowed_for_permanent_license(self):
        """Check if permanent license can run this version (1 year update window)"""
        if self.settings.value("license/type") != LICENSE_TYPE_PERMANENT:
            return True  # Not a permanent license, allow
        
        activation_date_str = self.settings.value("license/activation_date", "")
        if not activation_date_str:
            print("ERROR: Permanent license missing activation date")
            return False
        
        try:
            # Parse activation date
            if 'T' in activation_date_str:
                activation_date = datetime.fromisoformat(activation_date_str.replace('Z', '+00:00'))
            else:
                activation_date = datetime.fromisoformat(activation_date_str)
                # Make timezone-aware if needed
                if activation_date.tzinfo is None:
                    from datetime import timezone
                    activation_date = activation_date.replace(tzinfo=timezone.utc)
            
            # Get the release date for this version
            version_release_date = self.get_version_release_date()
            if not version_release_date:
                # If we can't get the release date, be conservative but allow offline use
                # Cache a warning flag so we can prompt user to check online later
                self.settings.setValue("license/version_date_check_needed", True)
                return True
            
            # Ensure both dates have timezone info for comparison
            from datetime import timezone
            if activation_date.tzinfo is None:
                activation_date = activation_date.replace(tzinfo=timezone.utc)
            
            if version_release_date.tzinfo is None:
                version_release_date = version_release_date.replace(tzinfo=timezone.utc)
                
            # Permanent licenses get 1 year of updates from activation date
            license_update_expiry = activation_date + timedelta(days=365)
            
            is_allowed = version_release_date <= license_update_expiry
            
            if not is_allowed:
                print(f"INFO: Permanent license expired for this version. "
                      f"License activated: {activation_date.strftime('%Y-%m-%d')}, "
                      f"Version released: {version_release_date.strftime('%Y-%m-%d')}, "
                      f"Update window ended: {license_update_expiry.strftime('%Y-%m-%d')}")
            
            return is_allowed
            
        except Exception as e:
            print(f"ERROR: Could not validate permanent license version access: {e}")
            return False

    def is_subscription_active(self):
        """Check if subscription period is still valid (works until expiry even if cancelled)"""
        if self.settings.value("license/type") != LICENSE_TYPE_SUBSCRIPTION:
            return True  # Not a subscription license
        
        # Check expiry date from server response - user paid for full year, should work until expiry
        expiry_date_str = self.settings.value("license/expiry", "")
        if not expiry_date_str:
            print("WARNING: Subscription license missing expiry date")
            return False
        
        try:
            # Handle different date formats
            expiry_date = None
            
            # Try ISO format first
            if 'T' in expiry_date_str or 'Z' in expiry_date_str:
                expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
            else:
                # Try simple date format
                expiry_date = datetime.fromisoformat(expiry_date_str)
            
            # Get current date with proper timezone handling
            if expiry_date.tzinfo is not None:
                # Expiry date has timezone info, use UTC for current time
                from datetime import timezone
                current_date = datetime.now(timezone.utc)
            else:
                # Expiry date is naive, use local time
                current_date = datetime.now()
                
            is_active = current_date <= expiry_date
            
            if not is_active:
                print(f"INFO: Subscription period ended. "
                      f"Expiry date: {expiry_date.strftime('%Y-%m-%d')}, "
                      f"Current date: {current_date.strftime('%Y-%m-%d')}")
            
            return is_active
            
        except Exception as e:
            print(f"ERROR: Could not validate subscription expiry: {e}")
            return False

    def validate_enterprise_license(self):
        """Validate enterprise license constraints - works like permanent license"""
        if self.settings.value("license/type") != LICENSE_TYPE_ENTERPRISE:
            return True  # Not an enterprise license
        
        # Enterprise licenses work like permanent licenses - machine locked with yearly validation
        # Check if we have an activation date for version validation
        activation_date_str = self.settings.value("license/activation_date", "")
        if not activation_date_str:
            print("WARNING: Enterprise license missing activation date")
            # If no activation date, assume it's valid (for legacy licenses)
            return True
        
        try:
            # Parse activation date
            if 'T' in activation_date_str:
                activation_date = datetime.fromisoformat(activation_date_str.replace('Z', '+00:00'))
            else:
                activation_date = datetime.fromisoformat(activation_date_str)
                # Make timezone-aware if needed
                if activation_date.tzinfo is None:
                    from datetime import timezone
                    activation_date = activation_date.replace(tzinfo=timezone.utc)
            
            # Enterprise licenses expire after 1 year and need renewal
            current_date = datetime.now()
            if activation_date.tzinfo is not None and current_date.tzinfo is None:
                from datetime import timezone
                current_date = datetime.now(timezone.utc)
            elif activation_date.tzinfo is None and current_date.tzinfo is not None:
                current_date = current_date.replace(tzinfo=None)
            
            enterprise_expiry = activation_date + timedelta(days=365)
            is_valid = current_date <= enterprise_expiry
            
            if not is_valid:
                print(f"INFO: Enterprise license expired. "
                      f"Activated: {activation_date.strftime('%Y-%m-%d')}, "
                      f"Expired: {enterprise_expiry.strftime('%Y-%m-%d')}, "
                      f"Current: {current_date.strftime('%Y-%m-%d')}")
            
            return is_valid
            
        except Exception as e:
            print(f"ERROR: Could not validate enterprise license: {e}")
            # If we can't validate, assume valid (for offline enterprise users)
            return True

    def is_valid_license(self, show_dialog=True):
        """
        Check if the current license is valid.
        
        Args:
            show_dialog (bool): Whether to show the license activation dialog if license is invalid
        
        Returns:
            bool: True if license is valid, False otherwise
        """
        if not self.license_key:
            if show_dialog:
                self.show_license_dialog()
            return False
        
        try:
            # First check if license exists locally
            if not self.settings.value("license/is_valid"):
                if show_dialog:
                    self.show_license_dialog()
                return False
            
            # Check trial expiry (this check is redundant since we have license, but keeping for safety)
            # if not self.is_valid_trial():
            #     if show_dialog:
            #         self.show_license_dialog()
            #     return False
            
            # **NEW: Check if full license validation is needed**
            should_validate = self.should_run_full_license_check()
            license_type = self.settings.value("license/type", "")
            
            if should_validate:
                print(f"Running full license validation for {license_type} license")
                
                # Perform server validation
                if not self._validate_license_with_server():
                    if show_dialog:
                        self.show_license_dialog()
                    return False
                
                # Mark validation as completed
                self.mark_full_license_check_completed()
            
            # **NEW: Always check version restrictions for permanent licenses**
            if not self.is_version_allowed_for_permanent_license():
                if show_dialog:
                    self._show_version_expired_dialog()
                return False
            
            # **NEW: Always check subscription expiry**
            if not self.is_subscription_active():
                if show_dialog:
                    self._show_subscription_expired_dialog()
                return False
            
            # **NEW: Validate enterprise constraints**
            if not self.validate_enterprise_license():
                if show_dialog:
                    self._show_enterprise_expired_dialog()
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating license: {e}")
            import traceback
            traceback.print_exc()
            if show_dialog:
                self.show_license_dialog()
            return False

    def _validate_license_with_server(self):
        """Validate license with server and update local settings"""
        try:
            api_key = self._load_api_key_from_config()
            if not api_key:
                print("ERROR: API key not found. Cannot validate license.")
                return False
            
            # Use the actual endpoint structure from existing code
            validation_url = f"{PRODUCTION_URL}/licenses/validate"
            
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key
            }
            
            # Use the existing API payload format
            payload = {
                "licenseKey": self.license_key
            }
            
            response = requests.post(validation_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                validation_data = response.json()
                
                # Handle both current and enhanced response formats
                is_valid = validation_data.get("isValid", False)
                
                if is_valid:
                    # Update license information from server
                    self.settings.setValue("license/is_valid", True)
                    
                    # Handle current response format
                    if "licenseType" in validation_data:
                        self.settings.setValue("license/type", validation_data["licenseType"])
                    elif "license_type" in validation_data:
                        self.settings.setValue("license/type", validation_data["license_type"])
                    
                    if "email" in validation_data:
                        self.settings.setValue("license/email", validation_data["email"])
                    
                    # Handle enhanced response format (for new validation logic)
                    if "expiryDate" in validation_data:
                        self.settings.setValue("license/expiry", validation_data["expiryDate"])
                    elif "expiry_date" in validation_data:
                        self.settings.setValue("license/expiry", validation_data["expiry_date"])
                    
                    if "activationDate" in validation_data:
                        self.settings.setValue("license/activation_date", validation_data["activationDate"])
                    elif "activation_date" in validation_data:
                        self.settings.setValue("license/activation_date", validation_data["activation_date"])
                    
                    # Handle other fields from current API
                    if "firstName" in validation_data:
                        self.settings.setValue("license/first_name", validation_data["firstName"])
                    if "lastName" in validation_data:
                        self.settings.setValue("license/last_name", validation_data["lastName"])
                    if "company" in validation_data:
                        self.settings.setValue("license/company", validation_data["company"])
                    
                    return True
                else:
                    print("License validation failed on server")
                    self.settings.setValue("license/is_valid", False)
                    return False
                    
            elif response.status_code == 404:
                print("License key not found on server")
                self.settings.setValue("license/is_valid", False)
                return False
                
            elif response.status_code == 403:
                # Handle 403 errors - could be cancelled subscription or revoked license
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", "")
                    
                    if "Status: Cancelled" in error_message:
                        license_type = self.settings.value("license/type", "")
                        if license_type == LICENSE_TYPE_SUBSCRIPTION:
                            # Subscription cancelled but user paid for full year - check expiry date
                            print("Subscription cancelled but checking if paid period is still valid")
                            # Keep license valid locally, let expiry date handling take care of it
                            return True
                        else:
                            # Permanent or enterprise license cancelled - block immediately
                            print("Non-subscription license cancelled - blocking access")
                            self.settings.setValue("license/is_valid", False)
                            return False
                    else:
                        # Other 403 errors (revoked, etc.) - block access
                        print(f"License blocked by server: {error_message}")
                        self.settings.setValue("license/is_valid", False)
                        return False
                        
                except json.JSONDecodeError:
                    print(f"License validation failed: {response.text}")
                    self.settings.setValue("license/is_valid", False)
                    return False
                
            else:
                print(f"License validation request failed: {response.status_code} - {response.text}")
                # For other errors, fall back to cached status to allow offline use
                cached_status = self.settings.value("license/is_valid", False, type=bool)
                print(f"Falling back to cached license status: {cached_status}")
                return cached_status
                
        except requests.exceptions.RequestException as e:
            print(f"Network error validating license with server: {e}")
            # Fall back to cached status for network issues
            cached_status = self.settings.value("license/is_valid", False, type=bool)
            print(f"Falling back to cached license status: {cached_status}")
            return cached_status
            
        except Exception as e:
            print(f"Error validating license with server: {e}")
            return False

    def _show_version_expired_dialog(self):
        """Show dialog when permanent license version access has expired"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("License Update Required")
        msg.setText("Your permanent license has expired for this version.")
        msg.setInformativeText("Permanent licenses include 1 year of updates. "
                              "Please purchase a new license or subscription to continue using the latest version.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _show_subscription_expired_dialog(self):
        """Show dialog when subscription period has ended"""
        expiry_date_str = self.settings.value("license/expiry", "")
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Subscription Period Ended")
        msg.setText("Your subscription period has ended.")
        
        if expiry_date_str:
            try:
                expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
                msg.setInformativeText(f"Your subscription period ended on {expiry_date.strftime('%B %d, %Y')}. "
                                     "Please purchase a new subscription to continue using the app.")
            except:
                msg.setInformativeText("Please purchase a new subscription to continue using the app.")
        else:
            msg.setInformativeText("Please purchase a new subscription to continue using the app.")
        
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _show_enterprise_expired_dialog(self):
        """Show dialog when enterprise license has expired"""
        activation_date_str = self.settings.value("license/activation_date", "")
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Enterprise License Expired")
        msg.setText("Your enterprise license has expired.")
        
        if activation_date_str:
            try:
                activation_date = datetime.fromisoformat(activation_date_str.replace('Z', '+00:00'))
                expiry_date = activation_date + timedelta(days=365)
                msg.setInformativeText(f"Your enterprise license expired on {expiry_date.strftime('%B %d, %Y')}. "
                                     "Please contact your administrator to renew the enterprise license.")
            except:
                msg.setInformativeText("Please contact your administrator to renew the enterprise license.")
        else:
            msg.setInformativeText("Please contact your administrator to renew the enterprise license.")
        
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    @property
    def license_key(self):
        """Get the current license key"""
        return self.settings.value("license/key", "")

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
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            trial_expired_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center align this label too
            
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
        
        if result == QDialog.DialogCode.Accepted:
            self.accept() 