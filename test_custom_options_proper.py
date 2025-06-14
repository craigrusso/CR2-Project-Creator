#!/usr/bin/env python3
"""
Proper test script for custom options widget behavior with animation timing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from app.core.app_module_pyqt import ProjectCreatorApp

def test_custom_options_behavior():
    """Test the custom options widget show/hide behavior with proper timing"""
    
    print("🧪 Starting Proper Custom Options Widget Test")
    
    # Create application
    app = QApplication(sys.argv)
    main_window = ProjectCreatorApp()
    main_window.show()
    
    # Wait for UI to initialize
    QTimer.singleShot(2000, lambda: run_tests(main_window))
    
    return app.exec()

def run_tests(main_window):
    """Run the actual tests with proper timing"""
    print("🔍 Running custom options widget tests with proper animation timing...")
    
    # Test data - template with custom options
    template_with_custom_options = {
        'name': 'Test Template',
        'structure': [{
            'name': 'test_file.txt',
            'type': 'file',
            'user_data': {
                'custom_options': {'${CUSTOM}': ['OPTION1', 'OPTION2', 'OPTION3']},
                'pattern': '${PROJECT_NAME}_${CUSTOM}_${DATE}.txt'
            }
        }]
    }
    
    # Test 1: Select template with custom options
    print("📝 Test 1: Selecting template with custom options")
    main_window.check_template_for_custom_options(template_with_custom_options)
    
    # Wait for slide up animation to complete (250ms + buffer)
    QTimer.singleShot(500, lambda: check_after_slide_up(main_window, template_with_custom_options))

def check_after_slide_up(main_window, template_data):
    """Check widget state after slide up animation completes"""
    if hasattr(main_window, 'custom_options_widget'):
        widget = main_window.custom_options_widget
        print(f"   After slide up - Widget isVisible(): {widget.isVisible()}")
        print(f"   After slide up - Widget is_visible flag: {getattr(widget, 'is_visible', 'N/A')}")
        
        if widget.isVisible():
            print("   ✅ Step 1 SUCCESS: Widget properly opened")
        else:
            print("   ❌ Step 1 FAILURE: Widget did not open")
        
        # Test 2: Click off (deselect template)
        print("📝 Test 2: Deselecting template (clicking off)")
        main_window.check_template_for_custom_options(None)
        
        # Wait for slide down animation to complete (250ms + buffer)
        QTimer.singleShot(500, lambda: check_after_slide_down(main_window, template_data))
    else:
        print("   ❌ Custom options widget not found!")
        QTimer.singleShot(1000, lambda: QApplication.quit())

def check_after_slide_down(main_window, template_data):
    """Check widget state after slide down animation completes"""
    if hasattr(main_window, 'custom_options_widget'):
        widget = main_window.custom_options_widget
        print(f"   After slide down - Widget isVisible(): {widget.isVisible()}")
        print(f"   After slide down - Widget is_visible flag: {getattr(widget, 'is_visible', 'N/A')}")
        
        if not widget.isVisible():
            print("   ✅ Step 2 SUCCESS: Widget properly closed")
        else:
            print("   ❌ Step 2 FAILURE: Widget did not close")
        
        # Test 3: Re-select same template
        print("📝 Test 3: Re-selecting same template")
        main_window.check_template_for_custom_options(template_data)
        
        # Wait for slide up animation to complete again
        QTimer.singleShot(500, lambda: check_final_result(main_window))
    else:
        print("   ❌ Custom options widget not found!")
        QTimer.singleShot(1000, lambda: QApplication.quit())

def check_final_result(main_window):
    """Check final result after re-selecting template"""
    if hasattr(main_window, 'custom_options_widget'):
        widget = main_window.custom_options_widget
        print(f"   After re-selection - Widget isVisible(): {widget.isVisible()}")
        print(f"   After re-selection - Widget is_visible flag: {getattr(widget, 'is_visible', 'N/A')}")
        
        if widget.isVisible():
            print("   ✅ Step 3 SUCCESS: Widget properly reopened after deselection!")
            print("\n🎉 OVERALL TEST RESULT: PASSED")
        else:
            print("   ❌ Step 3 FAILURE: Widget did not reopen after deselection!")
            print("\n💥 OVERALL TEST RESULT: FAILED")
    else:
        print("   ❌ Custom options widget not found!")
        print("\n💥 OVERALL TEST RESULT: FAILED")
    
    # End test
    QTimer.singleShot(2000, lambda: QApplication.quit())

if __name__ == "__main__":
    sys.exit(test_custom_options_behavior()) 