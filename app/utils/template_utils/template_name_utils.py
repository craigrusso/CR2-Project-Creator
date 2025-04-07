#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from datetime import datetime

class TemplateNameGenerator:
    """Utility class for generating and validating template names"""
    
    @staticmethod
    def generate_default_name():
        """Generate a default template name with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"UNTITLED_{timestamp}"
    
    @staticmethod
    def sanitize_name(name):
        """Sanitize a template name"""
        if not name:
            return TemplateNameGenerator.generate_default_name()
        
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # If empty after stripping, generate default
        if not name:
            return TemplateNameGenerator.generate_default_name()
            
        return name
    
    @staticmethod
    def validate_and_fix_name(name):
        """
        Validate a template name and fix it if needed
        
        Returns:
            tuple: (fixed_name, was_modified)
        """
        original_name = name
        fixed_name = TemplateNameGenerator.sanitize_name(name)
        return fixed_name, fixed_name != original_name 