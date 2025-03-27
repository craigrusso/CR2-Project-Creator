#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
UI Operations for Structure Editor

This module provides utility functions for UI testing and validation.
"""

from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox
from PyQt5.QtCore import QTimer

def test_category_ui_persistence(app, test_category="UI Test Category"):
    """
    Test that template categories are correctly persisted in the UI
    
    Args:
        app: The application instance
        test_category: The category name to test with
        
    Returns:
        dict: Test results with success flag and details
    """
    print(f"\n=== Testing Category UI Persistence with '{test_category}' ===")
    
    results = {'success': False, 'ui_tests': {}}
    
    try:
        # First make sure the test category exists
        if hasattr(app, 'template_manager') and hasattr(app.template_manager, 'project_type_manager'):
            app.template_manager.project_type_manager.create_project_type(test_category, "Video Editing - Standard")
            print(f"Added test category '{test_category}' to project types")
            
            # Force a reload of categories
            app.template_manager.project_type_manager.load_custom_project_types()
        
        # Find all category dropdowns in the application
        category_dropdowns = []
        for widget in QApplication.allWidgets():
            if isinstance(widget, QComboBox):
                # Identify category dropdowns (similar to category_manager.py logic)
                widget_name = widget.objectName().lower()
                is_category_dropdown = False
                
                # Method 1: Check widget name
                if any(term in widget_name for term in ["category", "categories", "type"]):
                    is_category_dropdown = True
                    category_dropdowns.append(widget)
                    print(f"Found category dropdown by name: {widget_name}")
                    
                # Method 2: Check content
                elif widget.count() > 0:
                    items = [widget.itemText(i) for i in range(widget.count())]
                    if "Custom" in items and any(cat in items for cat in ["Audio", "Video", "Photography", "Graphics"]):
                        is_category_dropdown = True
                        category_dropdowns.append(widget)
                        print(f"Found category dropdown by content: {items}")
        
        # Test each dropdown found
        if not category_dropdowns:
            results['ui_tests']['dropdown_search'] = {
                'success': False,
                'error': "No category dropdowns found in the UI"
            }
            print("❌ FAILURE: No category dropdowns found in the UI")
        else:
            results['ui_tests']['dropdown_search'] = {
                'success': True,
                'dropdown_count': len(category_dropdowns)
            }
            print(f"Found {len(category_dropdowns)} category dropdowns in the UI")
            
            # Test each dropdown for our test category
            for i, dropdown in enumerate(category_dropdowns):
                dropdown_name = dropdown.objectName() or f"dropdown_{i}"
                dropdown_items = [dropdown.itemText(j) for j in range(dropdown.count())]
                
                # Check if our test category is in the dropdown
                if test_category in dropdown_items:
                    index = dropdown.findText(test_category)
                    current_index = dropdown.currentIndex()
                    
                    # Try to select the test category
                    dropdown.setCurrentIndex(index)
                    new_index = dropdown.currentIndex()
                    new_text = dropdown.currentText()
                    
                    # Check if the selection worked
                    if new_text == test_category:
                        print(f"✅ SUCCESS: Selected '{test_category}' in dropdown {dropdown_name}")
                        results['ui_tests'][f'dropdown_{i}'] = {
                            'success': True,
                            'name': dropdown_name,
                            'selected': new_text
                        }
                    else:
                        print(f"❌ FAILURE: Could not select '{test_category}' in dropdown {dropdown_name}, got '{new_text}' instead")
                        results['ui_tests'][f'dropdown_{i}'] = {
                            'success': False,
                            'name': dropdown_name,
                            'error': f"Selection failed, got '{new_text}' instead of '{test_category}'"
                        }
                        
                    # Restore previous selection
                    dropdown.setCurrentIndex(current_index)
                else:
                    print(f"❌ FAILURE: Test category '{test_category}' not found in dropdown {dropdown_name}")
                    results['ui_tests'][f'dropdown_{i}'] = {
                        'success': False,
                        'name': dropdown_name,
                        'error': f"Category '{test_category}' not found in dropdown",
                        'available_items': dropdown_items
                    }
        
        # Overall success is true if all tests passed
        results['success'] = all(test.get('success', False) for test in results['ui_tests'].values())
                    
    except Exception as e:
        import traceback
        print(f"❌ ERROR during UI test: {e}")
        traceback.print_exc()
        results['error'] = str(e)
        results['success'] = False
    finally:
        print("=== End of Category UI Persistence Test ===\n")
        
    return results

def show_test_results(results, parent=None):
    """
    Show test results in a message box
    
    Args:
        results: Dictionary of test results
        parent: Parent widget for the message box
    """
    if not results:
        QMessageBox.warning(parent, "Test Results", "No test results available")
        return
        
    # Overall result
    overall = "✅ SUCCESS" if results.get('success', False) else "❌ FAILURE"
    
    # Create a detailed message
    message = f"{overall}: Template Category Tests\n\n"
    
    # Add details for each test
    for test_name, test_result in results.items():
        if isinstance(test_result, dict):
            test_status = "✅ SUCCESS" if test_result.get('success', False) else "❌ FAILURE"
            message += f"{test_name}: {test_status}\n"
            
            # Add error if present
            if 'error' in test_result:
                message += f"  Error: {test_result['error']}\n"
                
            # Add other details
            for key, value in test_result.items():
                if key not in ['success', 'error']:
                    message += f"  {key}: {value}\n"
            
            message += "\n"
    
    # Show the message box
    if results.get('success', False):
        QMessageBox.information(parent, "Test Results", message)
    else:
        QMessageBox.warning(parent, "Test Results", message)

def run_ui_tests(app, parent=None):
    """
    Run UI tests and show results
    
    Args:
        app: The application instance
        parent: Parent widget for message boxes
    """
    # Run the tests
    results = test_category_ui_persistence(app)
    
    # Show results in a message box
    QTimer.singleShot(500, lambda: show_test_results(results, parent)) 