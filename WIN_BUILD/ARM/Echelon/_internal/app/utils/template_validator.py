#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from datetime import datetime

class TemplateValidator:
    """Utility class for validating and fixing template data"""
    
    @staticmethod
    def generate_default_name():
        """Generate a default template name with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"UNTITLED_{timestamp}"
    
    @staticmethod
    def validate_and_fix_template(template_data):
        """
        Validate and fix template data, ensuring all required fields are present
        and properly formatted.
        
        Args:
            template_data (dict): The template data to validate
            
        Returns:
            tuple: (is_valid, fixed_template, messages)
                - is_valid (bool): Whether the template is valid
                - fixed_template (dict): The fixed template data
                - messages (list): List of validation messages
        """
        # print("DEBUG: Starting template validation")
        messages = []
        is_valid = True
        
        # Work with a copy of the template data
        template = template_data.copy() if template_data else {}
        
        # print(f"DEBUG: Initial template data: {template}")
        
        # Handle empty or missing name
        if not template.get("name"):
            # print("DEBUG: Template name is empty or missing, generating default name")
            template["name"] = TemplateValidator.generate_default_name()
            messages.append(f"Generated default name: {template['name']}")
            # print(f"DEBUG: Generated name: {template['name']}")
        
        # Validate required fields
        required_fields = ["path", "type"]
        for field in required_fields:
            if field not in template:
                # print(f"DEBUG: Missing required field: {field}")
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        # Validate path is not empty
        if template.get("path", "").strip() == "":
            # print("DEBUG: Template path is empty")
            messages.append("Template path cannot be empty")
            is_valid = False
        
        # Add default values for optional fields
        if "description" not in template:
            template["description"] = ""
            
        if "category" not in template:
            template["category"] = "General"
            
        # Add timestamps
        if "created" not in template:
            template["created"] = datetime.now().isoformat()
            
        template["modified"] = datetime.now().isoformat()
        
        # print(f"DEBUG: Validation complete - is_valid={is_valid}, messages={messages}")
        # print(f"DEBUG: Final template data: {template}")
        
        return is_valid, template, messages 