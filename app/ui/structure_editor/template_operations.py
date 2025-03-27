#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template Operations for the Structure Editor

This module provides utility functions for testing and validating template operations.
"""

import os
import json
import tempfile
import time

def test_category_persistence(template_manager, test_category="Test Category"):
    """
    Test that template categories are correctly persisted when saving and loading templates.
    
    Args:
        template_manager: The template manager instance to test
        test_category: The category name to test with
        
    Returns:
        dict: Test results with success flag and details
    """
    print(f"\n=== Testing Category Persistence with '{test_category}' ===")
    
    # Generate a unique test template name
    test_time = int(time.time())
    test_template_name = f"Test Template {test_time}"
    
    # Simple test structure
    test_structure = [
        {
            "Root": [
                "File1.txt",
                "File2.txt",
                {
                    "Subfolder": [
                        "File3.txt"
                    ]
                }
            ]
        }
    ]
    
    # Create a template with the test category
    template_data = {
        'name': test_template_name,
        'description': f"Test template created at {test_time}",
        'category': test_category,
        'structure': test_structure,
        'created': time.time(),
        'modified': time.time(),
        'files': []
    }
    
    # Save the test template
    print(f"Saving test template '{test_template_name}' with category '{test_category}'")
    try:
        save_result = template_manager.save_structure(test_template_name, template_data)
        if not save_result:
            return {'success': False, 'error': "Failed to save test template"}
        
        print(f"Template saved successfully")
        
        # Load the template back
        print(f"Loading test template '{test_template_name}'")
        loaded_template = None
        
        # Try different methods to load the template
        if hasattr(template_manager, 'get_template_by_name'):
            loaded_template = template_manager.get_template_by_name(test_template_name)
        elif hasattr(template_manager, 'get_structure'):
            loaded_template = template_manager.get_structure(test_template_name)
            
        if not loaded_template:
            return {'success': False, 'error': "Failed to load test template"}
            
        # Check that the category was preserved
        if isinstance(loaded_template, dict):
            loaded_category = loaded_template.get('category', loaded_template.get('type', None))
            print(f"Loaded template has category: '{loaded_category}'")
            
            if loaded_category == test_category:
                print(f"✅ SUCCESS: Category was correctly persisted")
                return {'success': True, 'template': loaded_template}
            else:
                print(f"❌ FAILURE: Category was not persisted correctly. Expected '{test_category}', got '{loaded_category}'")
                return {'success': False, 'error': f"Category mismatch: expected '{test_category}', got '{loaded_category}'", 'template': loaded_template}
        else:
            print(f"❌ FAILURE: Loaded template is not a dictionary")
            return {'success': False, 'error': "Loaded template is not a dictionary", 'template': loaded_template}
            
    except Exception as e:
        import traceback
        print(f"❌ ERROR during test: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    finally:
        print("=== End of Category Persistence Test ===\n")
        
def run_template_diagnostic_tests(app):
    """
    Run diagnostic tests for the template system
    
    Args:
        app: The application instance
        
    Returns:
        dict: Test results
    """
    results = {}
    
    # Check if app has template_manager
    if not hasattr(app, 'template_manager'):
        return {'success': False, 'error': "App has no template_manager"}
    
    # Test category persistence
    results['category_persistence'] = test_category_persistence(app.template_manager)
    
    # Check template categories consistency
    if hasattr(app.template_manager, 'get_categories'):
        categories = app.template_manager.get_categories()
        results['categories'] = categories
        print(f"Available categories: {categories}")
    
    # Overall success
    results['success'] = all(test.get('success', False) for test in results.values() if isinstance(test, dict))
    
    return results 