#!/usr/bin/env python3
"""
Test script for SVG illustrations
Verifies that SVG generation works correctly and produces valid XML.
"""

import sys
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.color_scheme_pyqt import APP_COLORS
from app.onboarding.svg_generator import SVGGenerator
from app.onboarding.tutorial_illustrations import TutorialIllustrations

def test_svg_generator():
    """Test basic SVG generator functionality"""
    print("Testing SVG Generator...")
    
    try:
        generator = SVGGenerator(APP_COLORS)
        
        # Test basic SVG creation
        svg = generator.create_svg_element()
        svg_string = generator.to_string(svg)
        
        # Verify it's valid XML
        ET.fromstring(svg_string)
        print("✅ Basic SVG generation: PASSED")
        
        # Test adding elements
        generator.add_app_window_frame(svg)
        generator.add_button(svg, 50, 50, 100, 30, "Test Button", highlight=True)
        generator.add_arrow(svg, 100, 100, 150, 150)
        
        svg_string = generator.to_string(svg)
        ET.fromstring(svg_string)
        print("✅ SVG with elements: PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ SVG Generator test failed: {e}")
        return False

def test_tutorial_illustrations():
    """Test tutorial illustrations generation"""
    print("\nTesting Tutorial Illustrations...")
    
    try:
        illustrations = TutorialIllustrations(APP_COLORS)
        
        # Test each slide illustration
        for i in range(6):
            svg_content = illustrations.get_illustration_for_slide(i)
            
            # Verify it's valid XML
            ET.fromstring(svg_content)
            print(f"✅ Slide {i} illustration: PASSED")
        
        # Test individual illustration methods
        methods_to_test = [
            'create_welcome_illustration',
            'create_template_creation_illustration', 
            'create_drag_drop_illustration',
            'create_smart_patterns_illustration',
            'create_project_creation_illustration',
            'create_completion_illustration'
        ]
        
        for method_name in methods_to_test:
            method = getattr(illustrations, method_name)
            svg_content = method()
            ET.fromstring(svg_content)
            print(f"✅ {method_name}: PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Tutorial Illustrations test failed: {e}")
        return False

def test_integration():
    """Test integration with color scheme"""
    print("\nTesting Integration...")
    
    try:
        # Verify APP_COLORS is accessible
        if not APP_COLORS:
            raise ValueError("APP_COLORS is empty or None")
        
        # Test color scheme integration
        generator = SVGGenerator(APP_COLORS)
        illustrations = TutorialIllustrations(APP_COLORS)
        
        # Generate a sample illustration
        svg_content = illustrations.create_welcome_illustration()
        
        # Verify it contains expected elements
        root = ET.fromstring(svg_content)
        
        # Check for SVG namespace
        if root.tag != 'svg':
            raise ValueError("Root element is not SVG")
        
        # Check for basic structure
        rects = root.findall('.//rect')
        if len(rects) == 0:
            raise ValueError("No rectangles found in SVG")
        
        print("✅ Integration test: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def save_sample_svgs():
    """Save sample SVGs for manual inspection"""
    print("\nSaving sample SVGs...")
    
    try:
        illustrations = TutorialIllustrations(APP_COLORS)
        
        # Create output directory
        output_dir = "sample_svgs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate and save each slide
        slide_names = [
            "welcome",
            "template_creation", 
            "drag_drop",
            "smart_patterns",
            "project_creation",
            "completion"
        ]
        
        for i, name in enumerate(slide_names):
            svg_content = illustrations.get_illustration_for_slide(i)
            
            filename = os.path.join(output_dir, f"slide_{i}_{name}.svg")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            print(f"✅ Saved: {filename}")
        
        print(f"\n📁 Sample SVGs saved to: {os.path.abspath(output_dir)}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save sample SVGs: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing SVG Illustration System\n")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    if test_svg_generator():
        tests_passed += 1
    
    if test_tutorial_illustrations():
        tests_passed += 1
    
    if test_integration():
        tests_passed += 1
    
    if save_sample_svgs():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! SVG illustration system is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 