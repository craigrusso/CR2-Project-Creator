#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
from app.constants import DEFAULT_TEMPLATE_CATEGORIES

class TemplateCategoryManager:
    """
    Manages template categories for better organization
    """
    def __init__(self, template_manager):
        self.template_manager = template_manager
    
    def get_all_categories(self):
        """Get all available categories"""
        # Combine default categories with any used in templates
        categories = set(DEFAULT_TEMPLATE_CATEGORIES)
        
        for template in self.template_manager.templates:
            category = template.get("category")
            if category:
                categories.add(category)
        
        return sorted(list(categories))
    
    def create_category(self, category_name):
        """Create a new category"""
        # Categories are just strings, so we don't need to create anything
        # Just make sure it's valid
        if not category_name or category_name in DEFAULT_TEMPLATE_CATEGORIES:
            return False
        
        # The category will be used when a template is assigned to it
        return True
    
    def change_template_category(self, template_name, new_category):
        """Change the category of a template"""
        for template in self.template_manager.templates:
            if template["name"] == template_name:
                old_category = template["category"]
                template["category"] = new_category
                
                # Save the template file
                filename = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                file_path = os.path.join(self.template_manager.paths["templates_dir"], f"{filename}.json")
                
                try:
                    with open(file_path, 'w') as f:
                        json.dump(template, f, indent=2)
                    return True
                except Exception as e:
                    # Restore old category on error
                    template["category"] = old_category
                    print(f"Error changing template category: {e}")
                    return False
        
        return False
